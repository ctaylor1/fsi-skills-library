"""Validate the complete bounded native contract; source data stays detached."""
from foundation_contract import cli_input
from calculate_or_transform import compute

def validate(doc):
    try: compute(doc)
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, ArithmeticError) as exc: return [str(exc)]
    return []

if __name__ == "__main__": cli_input(validate)
