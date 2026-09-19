#!/usr/bin/env python3
"""Adapt the retired paid-model input to the native P&C reserving schema.

Supply metadata explicitly; this adapter never invents valuation date, currency, unit or source.
Usage: python scripts/migrate_paid_triangle.py legacy.json metadata.json
"""
import json,sys
from pathlib import Path

def migrate(legacy, metadata):
    for key in ('valuation_date','currency','unit','source_ref'):
        if not metadata.get(key):
            raise ValueError(f'explicit migration metadata required: {key}')
    triangle=legacy['triangle'];assumptions=legacy['assumptions']
    if assumptions.get('method') != 'volume_weighted_chain_ladder':
        raise ValueError('legacy adapter supports volume_weighted_chain_ladder only')
    origins=triangle['origin_periods'];rows=triangle['cumulative_paid'];ages=triangle['dev_ages']
    if len(origins)!=len(rows) or len(set(map(str,origins)))!=len(origins):
        raise ValueError('origin and row counts must match without duplicate origins')
    normalized={}
    for origin,row in zip(origins,rows):
        if len(row)!=len(ages):
            raise ValueError('row width must equal development ages')
        values=[];missing=False
        for value in row:
            if value is None:missing=True
            elif missing:raise ValueError('internal triangle gaps cannot be compacted')
            else:values.append(value)
        if not values:raise ValueError('empty origin requires data before migration')
        normalized[str(origin)]=values
    output={k:v for k,v in metadata.items() if k!='source_ref'}
    output['dataset_version']=assumptions['config_version']
    output['migration_source']=legacy
    output['segments']=[{'segment_id':triangle['triangle_id'],'line_of_business':triangle.get('claim_type'),
        'triangle_basis':'paid','development_ages':ages,'triangle':normalized,'factor_method':'volume-weighted',
        'tail_factor':assumptions['tail_factor'],'source_ref':metadata['source_ref']}]
    from validate_input import validate
    errors,_=validate(output)
    if errors:raise ValueError('; '.join(errors))
    return output

if __name__=='__main__':
    source,metadata=[json.loads(Path(p).read_text()) for p in sys.argv[1:]]
    print(json.dumps(migrate(source,metadata),indent=2))
