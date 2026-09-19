"""Standalone native calculate entry point."""

from insurance_foundation import main
from domain import evaluate, validate

PRODUCER = "reinsurance-program-analyzer"

if __name__ == "__main__":
    raise SystemExit(main("calculate", PRODUCER, evaluate, validate))
