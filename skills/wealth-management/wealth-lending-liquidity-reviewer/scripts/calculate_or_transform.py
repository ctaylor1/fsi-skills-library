"""Calculate or transform a bounded lending review."""
from domain import validate, build, validate_output
from wealth_workflow import run_cli

if __name__ == '__main__':
    raise SystemExit(run_cli('compute', validate, build, validate_output, __file__))
