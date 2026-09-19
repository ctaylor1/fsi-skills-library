#!/usr/bin/env python3
"""Portable native calculate entry point."""

from insurance_foundation import main
from domain import evaluate, validate

if __name__ == "__main__":
    raise SystemExit(main("calculate", "claim-financial-evaluation-assistant", evaluate, validate))
