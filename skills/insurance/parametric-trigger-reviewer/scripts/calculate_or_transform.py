from domain import evaluate, validate
from workflow_foundation import main

if __name__ == "__main__":
    raise SystemExit(main('calculate', 'parametric-trigger-reviewer', evaluate, validate))
