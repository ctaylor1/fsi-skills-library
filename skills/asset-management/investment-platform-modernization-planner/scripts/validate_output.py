from domain import compute
from foundation_contract import cli_output, validate_result


def validate(output, original_input=None):
    return validate_result(output, original_input, compute)


if __name__ == '__main__':
    cli_output(validate)
