#!/usr/bin/env python3
"""Portable native calculate entrypoint for insurance-producer-onboarding-reviewer."""
from domain import evaluate, validate
from insurance_foundation import main

if __name__ == '__main__':
    raise SystemExit(main('calculate', 'insurance-producer-onboarding-reviewer', evaluate, validate))
