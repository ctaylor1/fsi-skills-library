"""Portable native calculate entry point."""

from domain import evaluate, validate
from insurance_foundation import main

PRODUCER = "life-annuity-pricing-modeler"

if __name__ == "__main__":
    raise SystemExit(main("calculate", PRODUCER, evaluate, validate))
