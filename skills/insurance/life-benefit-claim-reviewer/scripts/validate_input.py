"""Standalone native input entry point."""

from insurance_foundation import main
from domain import evaluate, validate

PRODUCER = "life-benefit-claim-reviewer"

if __name__ == "__main__":
    raise SystemExit(main("input", PRODUCER, evaluate, validate))
