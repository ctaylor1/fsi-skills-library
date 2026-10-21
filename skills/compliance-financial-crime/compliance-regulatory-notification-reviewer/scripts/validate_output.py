from domain import compute
from foundation_contract import validate_result, cli_output
def validate(doc, original_input=None): return validate_result(doc,original_input,compute)
if __name__=="__main__": cli_output(validate)
