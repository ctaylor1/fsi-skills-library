#!/usr/bin/env python3
"""Portable native input entrypoint for life-annuity-sales-reviewer."""
from domain import evaluate, validate
from insurance_foundation import main

if __name__ == '__main__':
    raise SystemExit(main('input', 'life-annuity-sales-reviewer', evaluate, validate))
