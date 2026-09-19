"""Portable native output entry point."""

from domain import evaluate, validate
from insurance_foundation import main

PRODUCER = "insurance-experience-study-builder"

if __name__ == "__main__":
    raise SystemExit(main("output", PRODUCER, evaluate, validate))
