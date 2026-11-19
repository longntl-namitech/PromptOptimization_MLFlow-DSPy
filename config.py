import os
import sys
from pathlib import Path

import mlflow
import mlflow.exceptions
from dotenv import load_dotenv

load_dotenv()

CONFIG = {
    'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
    'MLFLOW_URI': os.getenv('MLFLOW_TRACKING_URI', 'http://127.0.0.1:5000'),
    'EXPERIMENT_NAME': "Business_Filter_Optimization",
    'CREATE_VISUALIZATIONS': True,
    'USE_CACHING': True  # Cache judge evaluations to save API calls
}

CONFIG["DATA_PATH"] = "data/BOT_FAQS.json"
CONFIG["SCOPE_PATH"] = "data/business_filter.xlsx"
CONFIG["CATEGORY"] = "PaymentAccount"
CONFIG["PROMPT_NAME"] = 'business_filter_payment_account'
CONFIG["OUTPUT_DIR"] = Path(f'{CONFIG["PROMPT_NAME"]}_results')
CONFIG["EVAL_SAMPLE_RATE"] = 0.1  # 10% for evaluation


CONFIG["MODEL_CONFIG"] = {
    "model": "openai/gpt-4o-mini",
    "temperature": 0,
    "max_tokens": 16000
}

CONFIG["TEACHER_MODEL_CONFIG"] = {
    "model": "openai/gpt-5-mini",
    "temperature": 1,
    "max_tokens": 64000
}

CONFIG["JUDGE_MODEL_CONFIG"] = {
    "model": "openai/gpt-4.1-mini",
    "temperature": 0,
    "max_tokens": 32000
}


def setup_and_configure():
    """Validate the environment and point MLflow at the experiment."""
    CONFIG['OUTPUT_DIR'].mkdir(exist_ok=True)

    if not CONFIG['OPENAI_API_KEY']:
        print("❌ OPENAI_API_KEY not found in environment")
        print("   Please set your OpenAI API key in .env file or environment")
        sys.exit(1)

    print(f"   Model: {CONFIG['MODEL_CONFIG']['model']}")
    print(f"   Teacher: {CONFIG['TEACHER_MODEL_CONFIG']['model']}")
    print(f"   Judge: {CONFIG['JUDGE_MODEL_CONFIG']['model']}")
    print(f"   MLflow: {CONFIG['MLFLOW_URI']}")
    print(f"   Output: {CONFIG['OUTPUT_DIR']}")

    mlflow.set_tracking_uri(CONFIG['MLFLOW_URI'])
    mlflow.dspy.autolog(
        log_compiles=True,    # Track optimization process
        log_evals=True,       # Track evaluation results
        log_traces_from_compile=True  # Track program traces during optimization
    )
    mlflow.autolog()

    try:
        mlflow.search_experiments()
    except Exception as e:
        print(f"❌ MLflow connection failed: {e}")
        print("   Please ensure MLflow server is running:")
        print("   mlflow server --host 127.0.0.1 --port 5000")
        sys.exit(1)

    try:
        mlflow.create_experiment(CONFIG['EXPERIMENT_NAME'])
    except mlflow.exceptions.MlflowException:
        pass  # experiment already exists

    experiment = mlflow.set_experiment(CONFIG['EXPERIMENT_NAME'])
    print(
        f"🧪 Experiment: {experiment.name} "
        f"({CONFIG['MLFLOW_URI']}/#/experiments/{experiment.experiment_id})"
    )
    return CONFIG
