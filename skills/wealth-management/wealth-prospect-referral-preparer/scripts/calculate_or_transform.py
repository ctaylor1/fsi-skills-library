#!/usr/bin/env python3
"""Local supplied-record workflow only; no external operations."""
from domain import validate, build, validate_output
from wealth_workflow import run_cli

if __name__ == "__main__":
    raise SystemExit(run_cli("compute", validate, build, validate_output, __file__))
