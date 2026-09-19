#!/usr/bin/env python3
"""Portable native input entry point."""

from insurance_foundation import main
from domain import evaluate, validate

if __name__ == "__main__":
    raise SystemExit(main("input", "claim-financial-evaluation-assistant", evaluate, validate))
