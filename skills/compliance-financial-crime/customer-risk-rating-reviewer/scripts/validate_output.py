"""Validate the complete native result against a separately retained original input.

Exact reconstruction rejects added narratives and invented evidence. It establishes
reproducibility of supplied assertions, not their truth or institutional authorization.
Usage: python3 scripts/validate_output.py output.json --input original.json
"""
from native_integrity import validate_reconstruction
from calculate_or_transform import compute

def validate(doc, original_input=None):
    errors=[]
    validate_reconstruction(doc,compute,errors,original_input=original_input)
    return errors

def main(argv):
    import argparse,json
    from pathlib import Path
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',nargs='?')
    parser.add_argument('--input',dest='original')
    parser.add_argument('--selftest',action='store_true')
    args=parser.parse_args(argv)
    folder=Path(__file__).resolve().parents[1]/'evals/files'
    if args.selftest:
        output,original=folder/'pack_example.json',folder/'risk_case_example.json'
    else:
        if not args.output or not args.original: parser.error('output and detached --input are required')
        output,original=Path(args.output),Path(args.original)
    try:
        errors=validate(json.loads(output.read_text()),json.loads(original.read_text()))
    except (ValueError,TypeError,KeyError,AttributeError) as exc:
        errors=[str(exc)]
    for error in errors: print('ERROR',error)
    print(f'output validation: {len(errors)} error(s)')
    return int(bool(errors))

if __name__=='__main__':
    import sys
    raise SystemExit(main(sys.argv[1:]))
