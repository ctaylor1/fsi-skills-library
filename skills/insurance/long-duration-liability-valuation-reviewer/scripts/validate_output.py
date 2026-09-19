"""Portable native output entry point."""

from domain import evaluate, validate
from insurance_foundation import main

PRODUCER = "long-duration-liability-valuation-reviewer"

if __name__ == "__main__":
    raise SystemExit(main("output", PRODUCER, evaluate, validate))
