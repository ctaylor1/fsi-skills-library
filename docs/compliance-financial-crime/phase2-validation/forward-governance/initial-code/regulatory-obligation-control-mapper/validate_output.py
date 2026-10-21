#!/usr/bin/env python3
from domain import compute
from foundation_contract import cli_output, validate_result
def validate(doc, original_input=None):
    return validate_result(doc, original_input, compute)
if __name__ == "__main__": cli_output(validate)
