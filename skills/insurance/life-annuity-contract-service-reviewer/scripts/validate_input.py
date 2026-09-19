"""Standalone native input entry point."""

from insurance_foundation import main
from domain import evaluate, validate

PRODUCER = "life-annuity-contract-service-reviewer"

if __name__ == "__main__":
    raise SystemExit(main("input", PRODUCER, evaluate, validate))
