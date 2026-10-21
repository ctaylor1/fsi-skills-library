# Customer Risk Rating Reviewer — bounded domain rules

- A complete explicit factor catalog, scale, weights, threshold order, freshness limit, override duration and trigger list are required. No approved methodology is bundled.
- Use catalog weights; reject altered input weights, changed scales, out-of-range/non-finite values, duplicate/unknown factors, invalid band thresholds or prohibition-labeled bands.
- Score uses the whole catalog denominator. Missing any scored factor (including one labeled optional), absent/future/stale observation dates withhold `score_pct`, `score_band`, `recomputed_band` and `recommended_band`. There is no supplied missing-factor policy, so denominator reduction is unsupported.
- A policy floor at the maximum factor value is only a supplied policy rule. It cannot establish legal prohibition. PEP and sanctions findings require their own applicable specialist review.
- An override must carry rationale, approver role, source and approval references, approval/expiry dates covering the assessment, and permitted duration. A documented current override explaining the record is reported distinctly and still requires human review; it does not become an authenticated approval.
- A trigger's `assessed: true` needs an `assessment_ref` before it is treated as documented assessment. No trigger is disposed by this skill.
- Outcome precedence: invalid/documented overrides or unassessed triggers → `Escalate-For-Adjudication`; incomplete data → `Remediate-Data-First`; unexplained band difference → `Re-Rate-Recommended`; otherwise `Align-No-Change`. Incomplete data remains visible even when escalation has precedence.

This is arithmetic reproduction and evidence challenge, not methodology validation, independent factor classification, legal prohibition determination, override authorization or customer lifecycle orchestration. All factor definitions and institutional policy applicability are supplied assertions.

All rules apply to the supplied model/profile only. Human reviewers confirm legal applicability and policy authority; version strings and citations alone do not establish them.
