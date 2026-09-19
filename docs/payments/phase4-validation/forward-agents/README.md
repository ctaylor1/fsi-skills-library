# Independent agent-commerce forward evaluation

Evaluator used the public normalized schema, protocol reference and CLI wrappers, plus the documented canonical hash implementation. No package evaluation fixtures, tests, golden answers or implementation domain code were read. All case data is newly authored fictional procurement evidence.

Normal case: USD 1,200 mandate, five payments maximum, USD 500 per-payment limit. Historical settled USD 250 plus pending USD 150 consume USD 400 and two payments. Available budget before proposal is USD 800, with three payments left. Current cart is 2 x USD 120 + USD 20 tax + USD 15 shipping - USD 5 discount = USD 270. Single-use credential limit USD 300, separately bound merchant origin; platform, seller, merchant of record and refund/dispute/payout responsibilities differ explicitly. No purchase or token release occurs.

106 cases and 315 native CLI calls produced 1,082 assertions: 1,079 passed and 3 exposed one common issue. All successful calculations were independently read back through output validation using the separately retained request. Source lineage and modified arithmetic were challenged independently. Standard permission/action/protocol/cryptography flags remained false throughout.

## Observed issue

All three modes accepted an AP2 v0.2 packet declaring agent-to-agent subdelegation depth 1 with explicit institution consent/limit. They returned draft and supplied-evidence-for-human-review with no unresolved condition. The public protocol reference says AP2 v0.2 excludes agent-to-agent delegation and unsupported extensions should remain unresolved. Institution-defined subdelegation was separately exercised and remained an allowed design review, as intended. Reproductions end in `--ap2-subdelegation.json`; original observed outputs end in `--ap2-subdelegation-output.json`. No target implementation was edited by this evaluator.

## Passing coverage

Pending commitments and count headroom; total/per-payment/count breaches; incomplete, unknown, future, cross-currency and cross-intent histories; failed outcomes without/with terminal nonexecution evidence; duplicate economic IDs and new-ID replay of the same checkout; explicit revocation and unknown revocation; execution before review and after intent/review expiry; altered intent/payee/cart binding; unsupported cart items and negative cart totals; missing charges; source-text injection; propagated upstream issues; source-bound output tampering; credential prior-use/domain/maximum/expiry/authentication scope; platform payee/cart/MoR/refund ownership.

Runtime hashes before and after were equal. Concurrent owner edits changed only platform SKILL.md, CHANGELOG.md and references/handoffs.md; these are listed explicitly in summary.json. All artifacts stay isolated in this directory. This is deterministic review of normalized supplied evidence, not protocol interoperability, authenticated trust validation, specialist legal acceptance or deployment authority.

## Correction retest

The implementation owner corrected public-protocol subdelegation handling. The evaluator reran the unchanged original AP2 subdelegation, institution-defined subdelegation and ordinary nondelegated cases in all three modes: 9 cases, 27 native CLI calls, all passed. AP2 v0.2 now preserves protocol-subdelegation-not-implemented as a gap. Institution-defined and ordinary cases remain draft. Original failure artifacts are unchanged; retest evidence and exact input/source hashes are in retest/. All selected source files were unchanged across this retest.
