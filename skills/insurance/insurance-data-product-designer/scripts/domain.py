"""Temporal insurance semantic contracts and exact supplied relationship samples."""
from design_support import Review, validate_with
METHOD = 'insurance-temporal-data-contract-v1'


def evaluate(doc):
    r = Review(doc, METHOD); d = r.data
    entities = r.rows('entities', 'entity_id'); fields = r.rows('fields', 'field_id')
    relations = r.rows('relations', 'relation_id', nonempty=False)
    links = r.rows('links', 'link_id', nonempty=False); records = r.rows('records', 'record_id')
    entity_map = {x['entity_id']:x for x in entities}; field_map = {x['field_id']:x for x in fields}; relation_map = {x['relation_id']:x for x in relations}
    valid_on = r.date(d,'valid_on'); known_on = r.date(d,'known_on')
    r.flag(d,'sample_inventory_complete'); r.fields(d,('purpose','owner','grain','retention_rule'))
    for row in entities: r.fields(row,('entity_type','identity_namespace','source_key'))
    for row in fields:
        r.fields(row,('entity_type','definition','unit','source_system','source_field','transformation','owner','classification','access_rule','quality_rule','version'))
        r.flag(row,'purpose_reviewed')
        r.need(isinstance(row.get('required'),bool), 'required-field', 'Field.required must be explicit boolean', row)
    for row in relations:
        r.fields(row,('from_type','to_type','definition'))
        r.need(row.get('cardinality') in {'one-to-one','many-to-one'}, 'cardinality', 'Only exact one-to-one or many-to-one samples supported', row)
    active = {}; sample_rows = []
    for row in records:
        field = field_map.get(row.get('field_id')); entity = entity_map.get(row.get('entity_id'))
        valid = r.need(bool(field) and bool(entity) and field.get('entity_type') == entity.get('entity_type'), 'field-binding', 'Record must bind a field of the same entity type', row)
        a = r.date(row,'valid_from',future=True); b = r.date(row,'valid_to',future=True) if row.get('valid_to') is not None else None
        recorded = r.date(row,'recorded_on')
        valid &= r.need(a is not None and (b is None or a < b), 'valid-interval', 'Valid interval is [from,to), to may be null for open-ended', row)
        r.need('value' in row, 'value', 'Explicit value or null required', row)
        if valid and a and recorded and valid_on and known_on and a <= valid_on and (b is None or valid_on < b) and recorded <= known_on:
            active.setdefault((row['entity_id'],row['field_id']),[]).append(row)
    for entity in entities:
        for field in fields:
            if field['entity_type'] != entity['entity_type']:continue
            matches = active.get((entity['entity_id'],field['field_id']),[])
            valid = len(matches) == 1 and matches[0].get('value') is not None
            if len(matches)>1: r.add('temporal-conflict','Multiple active assertions; do not silently choose latest', entity)
            if field.get('required') and not valid: r.add('required-value','Required field has no unique known active value',field)
            sample_rows.append({'entity_id':entity['entity_id'],'field_id':field['field_id'],'value':matches[0].get('value') if valid and r.scope_valid else None,
                                'record_ids':[x['record_id'] for x in matches],'source_refs':sorted({s for x in matches for s in x['source_refs']})})
    left_seen=set();right_seen=set();join_rows=[]
    for row in links:
        relation=relation_map.get(row.get('relation_id'));left=entity_map.get(row.get('left_entity_id'));right=entity_map.get(row.get('right_entity_id'))
        valid=bool(relation and left and right and left['entity_type']==relation['from_type'] and right['entity_type']==relation['to_type'])
        r.need(valid,'join-binding','Relationship sample has unresolved or incompatible entities',row)
        lk=(row.get('relation_id'),row.get('left_entity_id'));rk=(row.get('relation_id'),row.get('right_entity_id'))
        unique=lk not in left_seen and (not relation or relation.get('cardinality')!='one-to-one' or rk not in right_seen)
        r.need(unique,'join-cardinality','Observed link violates declared relationship cardinality',row)
        left_seen.add(lk);right_seen.add(rk)
        join_rows.append({**row,'relationship_evaluable':valid and unique})
    # An inconsistent contract/source inventory cannot yield a usable resolved sample.
    if not r.clear:
        for row in sample_rows: row['value']=None
    return r.finish({'semantic_contract':fields,'relationship_samples':join_rows,'resolved_sample':sample_rows,
                     'valid_on':d.get('valid_on'),'known_on':d.get('known_on'),'deployment_approved':False,
                     'acord_conformance':'not_assessed','production_identity_resolution':False})


def validate(doc): return validate_with(evaluate,doc)
