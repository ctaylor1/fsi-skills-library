#!/usr/bin/env python3
"""Portable native output entry point."""

from insurance_foundation import main
from domain import evaluate, validate

if __name__ == "__main__":
    raise SystemExit(main("output", "pc-rate-adequacy-analyzer", evaluate, validate))
