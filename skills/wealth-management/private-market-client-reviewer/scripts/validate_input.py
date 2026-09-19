from domain import build, validate, validate_output
from wealth_workflow import run_cli

if __name__ == "__main__":
    raise SystemExit(run_cli('input', validate, build, validate_output, __file__))
