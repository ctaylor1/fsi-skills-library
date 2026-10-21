from legacy_validate_input import *
from legacy_validate_input import validate as legacy_validate
from domain import validate as phase2_validate

def validate(doc):
    return phase2_validate(doc) if isinstance(doc,dict) and doc.get('mode')=='lifecycle' else legacy_validate(doc)

if __name__=='__main__':
    import sys
    from foundation_contract import cli_input
    if '--selftest' in sys.argv[1:]:
        raise SystemExit(main(sys.argv[1:]))
    cli_input(validate)
