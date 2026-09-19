"""Portable native output entry point."""

from domain import evaluate, validate
from insurance_foundation import main

PRODUCER = "reinsurance-underwriting-reviewer"

if __name__ == "__main__":
    raise SystemExit(main("output", PRODUCER, evaluate, validate))
