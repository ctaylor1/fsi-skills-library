#!/usr/bin/env python3
"""Validate a native result against detached original input and wrap for internal review."""
import argparse,json
from pathlib import Path
from investment_contract import build_packet
from native_receiver import package_name,native_validate

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--request',required=True);p.add_argument('--native-output',required=True)
    p.add_argument('--producer-package',required=True);p.add_argument('--method',required=True)
    a=p.parse_args()
    try:
        request=json.loads(Path(a.request).read_text());native=json.loads(Path(a.native_output).read_text())
        method=json.loads(Path(a.method).read_text());name=package_name(a.producer_package)
        result=build_packet(request,native,producer=name,method=method,
            native_validator=lambda output,source:native_validate(a.producer_package,output,source))
    except (ValueError,TypeError,KeyError,OSError) as exc:p.exit(1,str(exc)+'\n')
    print(json.dumps(result,indent=2,allow_nan=False))

if __name__=='__main__':main()
