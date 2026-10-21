"""Bounded supplied-input review. No source authentication or business action."""
from decimal import Decimal
from foundation_contract import (D,ratio,date_value,exact,validate_common,validate_referenced_sources,require_sources,finish,cli_compute)
from native_integrity import canonical_hash

from portfolio_math import review_candidates
@exact
def analyze(d):
    require_sources(d,[d.get('covariance_source_ref')]+[x.get('source_ref') for x in d['assets']]+[x.get('source_ref') for x in d.get('scenarios',[])])
    if d['universe_type']!='security':raise ValueError('wrong universe type for this professional workflow')
    return review_candidates(d)

SKILL='portfolio-construction-analyzer'
METHOD='long-only-candidate-feasibility'
LIMITS=['Annualized supplied covariance; PSD tolerance1e-30 and analytic volatility rounded12places.', 'No shorting/leverage, nonlinear derivatives, liability optimization or solver; expected returns are assumptions.']
HANDOFFS=['institutional-investment-policy-builder', 'portfolio-rebalancing-planner', 'portfolio-risk-contribution-analyzer']

def validate(doc):
    errors=validate_common(doc)
    if errors:return errors
    errors+=validate_referenced_sources(doc)
    if doc.get('requested_action','review') not in ('review','draft'):errors.append('business execution unsupported')
    if errors:return errors
    try:analyze(doc)
    except (ValueError,TypeError,KeyError,IndexError,ArithmeticError) as exc:errors.append(str(exc))
    return errors

def compute(doc):
    errors=validate(doc)
    if errors:raise ValueError('; '.join(errors))
    results,issues=analyze(doc)
    return finish(doc,SKILL,METHOD,results,issues=issues,limitations=LIMITS,handoffs=HANDOFFS)

if __name__=='__main__':cli_compute(compute)
