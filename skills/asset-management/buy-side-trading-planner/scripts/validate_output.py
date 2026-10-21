from calculate_or_transform import compute
from foundation_contract import validate_result,cli_output
def validate(output,original_input=None):return validate_result(output,original_input,compute)
if __name__=="__main__":cli_output(validate)
