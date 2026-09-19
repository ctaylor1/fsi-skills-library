"""Reconcile material risks, scenario measures and governance into an ORSA draft."""
from insurance_foundation import number
from local_review import Review, shape, text

SKILL = 'insurance-orsa-packager'
METHOD = 'orsa-evidence-reconciliation-v1'


def validate(doc):
    errors = shape(doc, objects=('profile',), lists=('risks', 'scenarios', 'capital_measures', 'liquidity_measures', 'sections', 'governance'), numbers=('available_capital', 'required_capital', 'resources', 'outflows', 'reported_surplus'))
    for row in doc.get('data', {}).get('risks', []) if not errors else []:
        if row.get('material') is not None and not isinstance(row['material'], bool):
            errors.append('risk.material must be boolean or null')
    return errors


def evaluate(doc):
    d, r = doc['data'], Review(doc)
    p = r.profile(METHOD)
    r.check(d.get('risk_inventory_complete') is True and d.get('scenario_inventory_complete') is True and all(k in d for k in ('risks', 'scenarios', 'capital_measures', 'liquidity_measures', 'sections', 'governance')), 'orsa-inventory', 'Supply explicit scoped risk, scenario, capital, liquidity, section and governance inventories.')
    r.check(text(d.get('currency')) and text(d.get('available_capital_basis')) and text(d.get('required_capital_basis')), 'orsa-measurement-basis', 'Preserve separate available and required capital valuation bases and currency.')
    for key in ('available_capital_basis', 'required_capital_basis'):
        r.check(p.get(key) == d.get(key) and text(p.get(key)), 'orsa-approved-basis', 'Capital measurement bases must match the reviewed ORSA profile.', p)
    risk_map, material = {}, set()
    for row in d.get('risks', []):
        rid = row.get('risk_id')
        r.evidence(row, 'risk')
        r.check(text(rid) and rid not in risk_map and isinstance(row.get('material'), bool) and all(text(row.get(k)) for k in ('materiality_basis', 'owner', 'assessment')), 'risk-materiality', 'Each risk needs a unique identity, explicit materiality decision and rationale, owner and substantive supplied assessment.', row)
        risk_map[rid] = row
        if row.get('material') is True:
            material.add(rid)
    r.check(bool(risk_map), 'risk-register-empty', 'A scoped materiality register cannot be inferred from an empty list.')
    scenarios, covered = {}, set()
    valuation = r.date(d.get('valuation_date'), 'scenario-valuation', latest=doc['as_of'])
    for row in d.get('scenarios', []):
        sid, horizon = row.get('scenario_id'), row.get('horizon')
        key = (sid, horizon)
        refs = row.get('risk_ids', [])
        r.evidence(row, 'scenario')
        r.check(text(sid) and text(horizon) and key not in scenarios and text(row.get('owner')) and text(row.get('assessment')) and text(row.get('reviewed_by')), 'scenario-identity', 'Each scenario/horizon needs unique identity, owner, reviewed assumptions and assessment.', row)
        projection = r.date(row.get('projection_date'), 'projection', row=row)
        r.check(projection is not None and valuation is not None and projection >= valuation, 'projection-horizon', 'Prospective scenario projection cannot predate the valuation date.', row)
        r.check(len(refs) == len(set(refs)) and set(refs).issubset(risk_map) and (sid == 'baseline' or bool(refs)), 'scenario-risk-link', 'Stress scenarios must link unique known risk IDs; a baseline alone does not cover material risk.', row)
        scenarios[key] = row
        if sid != 'baseline':
            covered.update(refs)
    r.check(bool(scenarios) and any(k[0] == 'baseline' for k in scenarios), 'baseline-missing', 'Retain an explicit baseline scenario and prospective horizon.')
    for rid in sorted(material - covered):
        r.add('material-risk-uncovered', f'Material risk {rid} has no supplied non-baseline scenario assessment.', risk_map[rid])
    capital, liquidity, reconciliations = {}, {}, []
    for field, registry, first, second in [('capital_measures', capital, 'available_capital', 'required_capital'), ('liquidity_measures', liquidity, 'resources', 'outflows')]:
        for row in d.get(field, []):
            key = (row.get('scenario_id'), row.get('horizon'))
            good = r.bind(row, field)
            good &= r.check(key in scenarios and key not in registry and text(row.get('reviewed_by')), 'scenario-measure-identity', 'Each measure must uniquely match a supplied scenario/horizon and reviewer.', row)
            if field == 'capital_measures':
                for basis in ('available_capital_basis', 'required_capital_basis'):
                    good &= r.check(row.get(basis) == d.get(basis), 'capital-measure-basis', 'Capital table measurement basis differs from approved ORSA scope.', row)
            a, b, reported = number(row.get(first)), number(row.get(second)), number(row.get('reported_surplus'))
            good &= r.check(all(v is not None for v in (a, b, reported)) and (b is None or b >= 0), 'scenario-measure-unknown', 'Scenario measures and reported surplus must be explicit; unknown does not mean zero.', row)
            surplus, difference = (a - b, a - b - reported) if good else (None, None)
            if good and difference:
                r.add('scenario-reconciliation-break', f'{field} for {key}: supplied surplus differs from components by {difference}.', row, block=False, severity='review')
            if good and surplus < 0:
                r.add('scenario-shortfall', f'{field} for {key}: scenario has a negative surplus of {surplus}; record management assessment and feasibility.', row, block=False, severity='review')
            registry[key] = {'scenario_id': key[0], 'horizon': key[1], 'calculated_surplus': surplus, 'reported_surplus': reported, 'difference': difference}
        for key in scenarios.keys() - registry.keys():
            r.add('scenario-measure-missing', f'{field} missing for scenario/horizon {key}; narrative coverage cannot replace reconciled measures.', scenarios[key])
    for key in scenarios:
        reconciliations.append({'scenario_id': key[0], 'horizon': key[1], 'capital': capital.get(key), 'liquidity': liquidity.get(key)})
    required = p.get('required_sections', [])
    r.check(bool(required) and len(required) == len(set(required)), 'section-profile', 'Reviewed jurisdictional ORSA profile must identify its required narrative sections; no assumed universal filing template.', p)
    sections, governance = {}, []
    for row in d.get('sections', []):
        sid = row.get('section_id')
        r.evidence(row, 'section')
        r.date(row.get('evidence_date'), 'section', latest=doc['as_of'], row=row)
        r.check(text(sid) and sid not in sections and text(row.get('owner')) and text(row.get('assessment')), 'section-evidence', 'Narrative sections need unique identity, accountable owner and supplied substantive assessment.', row)
        sections[sid] = row
    for sid in set(required) - sections.keys():
        r.add('section-missing', f'Required profile section {sid} has no supplied narrative evidence.')
    seen_governance = set()
    for row in d.get('governance', []):
        gid = row.get('governance_role')
        r.evidence(row, 'governance')
        r.date(row.get('evidence_date'), 'governance', latest=doc['as_of'], row=row)
        r.check(text(gid) and gid not in seen_governance and text(row.get('owner')) and row.get('decision') in {'reviewed', 'open', 'rejected'}, 'governance-evidence', 'Governance role, owner, decision and dated evidence must be explicit and unique.', row)
        seen_governance.add(gid)
        if row.get('decision') != 'reviewed':
            r.add('governance-open', 'Governance review remains open or rejected; packaging cannot certify approval.', row, block=False, severity='review')
        governance.append(row)
    r.check({'risk-owner', 'capital-owner', 'liquidity-owner', 'governing-body'}.issubset(seen_governance), 'governance-coverage', 'This bounded package needs risk, capital, liquidity and governing-body review evidence; institutional adoption may require more.')
    return r.result({'material_risk_ids': sorted(material), 'uncovered_material_risks': sorted(material - covered),
                     'risk_assessments': list(risk_map.values()), 'scenario_reconciliations': reconciliations,
                     'narrative_evidence': list(sections.values()), 'governance_evidence': governance,
                     'basis': d.get('basis'), 'currency': d.get('currency'),
                     'available_capital_basis': d.get('available_capital_basis'), 'required_capital_basis': d.get('required_capital_basis'),
                     'filing_applicability': 'human-determination-required', 'orsa_approved': False,
                     'external_submission_authorized': False, 'packaging_metric': 'evidence-and-reconciliation; no completion-percentage'})
