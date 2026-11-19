from mlflow.genai import register_prompt

business_filter_base_prompt = """You are a system scope validation assistant. Your task is to determine whether the user's question falls within the defined system boundaries. Follow these steps strictly:

1. Analyze the user's question to clearly identify the user's intent.
2. Strictly compare this intent against the <Inscope> and <Outscope> categories.
3. Return your judgment in a JSON object with the exact format below. Do not add any extra text.
"""

PROMPTS = {
    "business_filter_card": business_filter_base_prompt,
    "business_filter_payment_account": business_filter_base_prompt
}


def register_prompts():
    """Register every prompt in PROMPTS to the MLflow prompt registry."""
    print("📚 Registering prompt to MLflow...")
    registered = 0

    for prompt_name, template in PROMPTS.items():
        try:
            prompt_version = register_prompt(
                name=prompt_name,
                template=template,
                commit_message=prompt_name
            )
            registered += 1
            print(f"✅ Registered v{prompt_version.version}: {prompt_name}")
        except Exception as e:
            print(f"❌ Failed to register {prompt_name}: {e}")

    print(f"✅ Registered {registered} prompts")
