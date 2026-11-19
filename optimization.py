from typing import Any, Dict

import dspy
from dspy import GEPA
from mlflow.genai import load_prompt

from config import CONFIG
from dataloaders.business_filter import get_scope_description, load_and_prepare_data
from evaluations.business_filter import evaluation_metric, make_metric_with_feedback


class BusinessFilterSignature(dspy.Signature):
    """Determine if a question is within the business scope."""
    outscope: str = dspy.InputField()
    inscope: str = dspy.InputField()
    question: str = dspy.InputField()
    reason: str = dspy.OutputField(
        description="A concise explanation in Vietnamese, clearly referencing specific items from the <Inscope> or <Outscope> sections, detail error matched if existed. Avoid assumptions."
    )
    in_scope: bool = dspy.OutputField(
        description="Whether the question is in scope."
    )


class BusinessFilter(dspy.Module):
    def __init__(self, instructions: str, inscope: str, outscope: str):
        self.lm = dspy.LM(**CONFIG["MODEL_CONFIG"])
        self.teacher_lm = dspy.LM(**CONFIG["TEACHER_MODEL_CONFIG"])
        dspy.configure(lm=self.lm)

        self.inscope = inscope
        self.outscope = outscope

        self.signature = BusinessFilterSignature.with_instructions(
            instructions)
        self.filter = dspy.Predict(self.signature)

    def forward(self, question: str) -> Dict[str, Any]:
        return self.filter(
            inscope=self.inscope,
            outscope=self.outscope,
            question=question
        )


def build_business_filter() -> BusinessFilter:
    """Load the latest registered prompt and the scope text into a program."""
    prompt = load_prompt(f"prompts:/{CONFIG['PROMPT_NAME']}@latest")
    print(f"✅ Loaded prompt version {prompt.version}")
    _, inscope, outscope = get_scope_description(CONFIG["CATEGORY"].lower())
    return BusinessFilter(prompt.template, inscope, outscope)


def evaluate_baseline():
    business_filter = build_business_filter()
    _, eval_set = load_and_prepare_data()

    evaluate = dspy.Evaluate(
        devset=eval_set,
        metric=evaluation_metric,
        lm=dspy.LM(**CONFIG["JUDGE_MODEL_CONFIG"]),
        display_progress=True,
    )
    return evaluate(business_filter)


def optimize():
    business_filter = build_business_filter()
    train_set, eval_set = load_and_prepare_data()

    optimizer = GEPA(
        metric=make_metric_with_feedback(
            business_filter.inscope, business_filter.outscope),
        auto="light",
        num_threads=32,
        track_stats=True,
        reflection_minibatch_size=3,
        reflection_lm=business_filter.teacher_lm
    )
    optimized_program = optimizer.compile(
        business_filter,
        trainset=train_set,
        valset=eval_set,
    )

    out_path = CONFIG['OUTPUT_DIR'] / f"{CONFIG['PROMPT_NAME']}.json"
    optimized_program.save(str(out_path))
    print(f"✅ Optimization completed, saved to {out_path}")
