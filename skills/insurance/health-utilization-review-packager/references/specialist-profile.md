# Specialist market, program and product profile

These packages review supplied facts against an explicitly reviewed method and
source profile. They contain no adopted law, clinical criteria, licensed CPT/UB
code set, filed rates, network-adequacy standard or automatic payment authority.

Keep the standard case_id, as_of, context, versioned sources and unresolved_issues
envelope. `data.owner`, `data.market`, `data.program` and `data.product` identify the
actual review. `data.profile` contains the existing workflow profile fields plus
`markets`, `programs`, `products`, `rule_basis` and `limitations`. Each actual scope
value must be explicitly included. A region label alone cannot select legal rules.
Profile validity covers review as_of; individual rule/contract dates must separately
cover the service, event, valuation or observation basis defined by the native method.

Use exact decimal strings for fractional numeric inputs. Integer JSON numbers are
allowed; every JSON floating-point token (including 3.0 and exponent notation),
booleans, infinity and NaN is rejected. A parser may already round a fraction into
an integer-valued float, so its apparent integrality does not prove source fidelity.
Unknown remains null. A supplied source reference, reviewer name or inventory list
does not prove authorization, authenticity, review or exhaustiveness. Affirmative
review and completeness flags require an explicit source statement and locator.

United States health programs need distinct institutional packs, for example fully
insured commercial, self-funded employer plans, Medicare Advantage and Medicaid
managed care; their benefit, review, rate and network requirements are not
interchangeable. Parametric insurance needs the actual policy jurisdiction,
contractual index provider, publication/finality rule, exposure and event scope.
Other markets may use these arithmetic/evidence methods only with a separately
reviewed matching profile; no blanket regional compliance is asserted.

Report proposed terms, observed facts, conditional calculations and human decisions
separately. Do not infer a professional sign-off from valid native output. The
accountable practitioner owns adoption, legal/clinical/actuarial judgment and any
real action. Outputs remain drafts; unresolved upstream issues and unmapped scope
changes prevent dependent calculations and recommendations.
