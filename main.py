import argparse

from config import setup_and_configure


def main():
    parser = argparse.ArgumentParser(
        description="Prompt versioning and optimization with MLflow and DSPy")
    parser.add_argument(
        "command", choices=["init", "eval", "optimize"],
        help="init: register prompts, eval: baseline evaluation, optimize: run GEPA")
    args = parser.parse_args()

    setup_and_configure()

    # Imported after setup so MLflow autolog is active before DSPy is used
    if args.command == "init":
        from init_prompt import register_prompts
        register_prompts()
    elif args.command == "eval":
        from optimization import evaluate_baseline
        evaluate_baseline()
    else:
        from optimization import optimize
        optimize()


if __name__ == "__main__":
    main()
