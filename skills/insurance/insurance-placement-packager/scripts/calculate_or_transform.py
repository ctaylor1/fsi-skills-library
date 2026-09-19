#!/usr/bin/env python3
"""Portable native calculate entrypoint for insurance-placement-packager."""
from domain import evaluate, validate
from insurance_foundation import main

if __name__ == '__main__':
    raise SystemExit(main('calculate', 'insurance-placement-packager', evaluate, validate))
