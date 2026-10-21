"""Preserve Phase1 native mode and dispatch explicit Phase2 mode."""
from legacy_calculate_or_transform import *
from legacy_calculate_or_transform import compute as legacy_compute
from domain import compute as phase2_compute

def compute(doc):
    return phase2_compute(doc) if isinstance(doc,dict) and doc.get('mode')=='lifecycle' else legacy_compute(doc)

if __name__=='__main__':
    import sys
    from foundation_contract import cli_compute
    if '--selftest' in sys.argv[1:]:
        from legacy_calculate_or_transform import main
        raise SystemExit(main(sys.argv[1:]))
    cli_compute(compute)
