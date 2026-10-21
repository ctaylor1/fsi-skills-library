# Beneficial Ownership Evidence Analysis — bounded domain rules

- The only supported `ownership_test` is `proportional-equity-gte` with `aggregate_across_chains: true`. No universal legal threshold or jurisdiction pack is bundled.
- Multiply equity proportions along each supplied chain and sum paths. Compare the unrounded result to the supplied threshold; output rounding must not create a threshold crossing.
- Root-relevant entities with less than 100% supplied equity coverage produce `incomplete_ownership`. Over-100 totals and cycles are gaps; skipped cyclic paths do not justify a complete assessment.
- A control edge counts only when its target is the root entity and its type is explicitly in `qualifying_control_types`. Other control edges are retained as excluded, with a reason; they do not establish indirect control.
- Document support requires the correct person subject, a configured document type, supplied source reference, known issue/expiry dates, no future issue date, and the supplied freshness limit. A declared document ID belonging to another person does not support the candidate.
- Candidate declaration is checked by person and basis. A control basis does not rescue an unsupported ownership declaration.
- `Escalate` takes precedence for declaration/control/cycle problems; document, coverage and arithmetic gaps give `Remediation-needed`; `Complete-for-review` means only that this bounded supplied graph produced no enumerated gap. It is not a legal determination or onboarding approval.

Supported: a scalar proportional-equity graph with aggregation across chains and a greater-than-or-equal threshold, plus specified direct root-entity control types. Unsupported: trusts/legal arrangements, voting or share-class tests, indirect control/control by other means, exemptions, nominee look-through, CTA filing determinations and independent identity verification. Route unsupported structures to a qualified specialist.

All rules apply to the supplied model/profile only. Human reviewers confirm legal applicability and policy authority; version strings and citations alone do not establish them.
