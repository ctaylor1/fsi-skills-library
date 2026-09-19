# Controls

R2 draft-only support. No contract signature, provider selection, customer commitment, payment initiation, retries, posting, production routing, account change, or delivery to third parties is implemented. Human approval applies before external delivery; the analytical run itself is read-only.

Use de-identified aggregates and contract extracts. Do not include PAN, credentials, personal identities or secrets in model inputs. The source snapshot intentionally retains all supplied evidence; use the institution's access-controlled record store and retention policy. A local request ID and hash are traceability fields, not a persisted case or audit-system integration.

Unresolved evidence and upstream issues remain visible. Source dates must not be in the future; overdue supplied review dates create gaps. An inspected label means the input owner asserts they inspected the evidence; the helper cannot authenticate the review. Missing review_due is not evidence that a source is current indefinitely; establish institution freshness criteria before relying on it. Freeze source versions for reviewed deliverables.

Run input validation before computation, source-bound output validation afterward, then review the narrative for claims not in the computed artifact. The output gate detects changes even if a caller updates the hash. It cannot prove truth if the underlying original source is fraudulent. Regional/policy applicability and supplier diligence remain specialist decisions. Structural/script testing does not replace domain SME or deployment acceptance.
