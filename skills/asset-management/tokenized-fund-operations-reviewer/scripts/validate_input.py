from domain import compute
from foundation_contract import cli_input
def validate(doc):
    try: compute(doc); return []
    except (ValueError,TypeError,KeyError,IndexError,AttributeError,ArithmeticError) as exc: return [str(exc)]
if __name__=='__main__': cli_input(validate)
