#!/usr/bin/env python3
"""Validate mapped investment artifacts and an explicitly installed native receiver."""
import argparse,json
from pathlib import Path
from investment_contract import make_handoff,validate_handoff
from native_receiver import package_name,native_validate

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('packet')
    p.add_argument('--target-package',required=True)
    p.add_argument('--source-package',required=True,help='installed original producer for native reconstruction')
    p.add_argument('--source-request',required=True,help='separately retained original producer request')
    p.add_argument('--build',action='store_true',help='input has source_packet,target_request,mapping,requested_output')
    a=p.parse_args()
    try:
        doc=json.loads(Path(a.packet).read_text());name=package_name(a.target_package)
        source_request=json.loads(Path(a.source_request).read_text())
        source_name=package_name(a.source_package)
        source=doc['source_packet']
        if source['artifact']['producer'] != source_name:
            raise ValueError('source package does not match artifact producer')
        validator=lambda native:native_validate(a.target_package,native)
        source_validator=lambda output,original:native_validate(a.source_package,output,original)
        if a.build:
            result=make_handoff(doc['source_packet'],doc['target_request'],target_skill=name,
                requested_output=doc['requested_output'],mapping=doc['mapping'],receiver_validator=validator,
                source_request=source_request,source_validator=source_validator)
        else:
            errors=validate_handoff(doc,target_skill=name,receiver_validator=validator,
                source_request=source_request,source_validator=source_validator)
            result={'errors':errors,'authority_granted':False}
            if errors:print(json.dumps(result));return 1
    except (ValueError,TypeError,KeyError,OSError) as exc:p.exit(1,str(exc)+'\n')
    print(json.dumps(result,indent=2,allow_nan=False));return 0

if __name__=='__main__':raise SystemExit(main())
