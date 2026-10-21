"""Validate all native fields by reconstruction from a separately retained original."""
from foundation_contract import validate_result, cli_output
from calculate_or_transform import compute

def validate(output, original_input=None):
    return validate_result(output, original_input, compute)

if __name__ == "__main__": cli_output(validate)
