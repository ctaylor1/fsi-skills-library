#!/usr/bin/env python3
"""Portable native output entrypoint for insurance-producer-onboarding-reviewer."""
from domain import evaluate, validate
from insurance_foundation import main

if __name__ == '__main__':
    raise SystemExit(main('output', 'insurance-producer-onboarding-reviewer', evaluate, validate))
