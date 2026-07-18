# Domain Rules — call-quality-compliance-reviewer

Explainable rubric **checks** and how the fired set maps to a **suggested QA disposition
band**. Marker sets, the prohibited lexicon, and thresholds are configuration (versioned,
owned by the QA/compliance-standards team), not hard-coded judgments, and never tuned to an
individual agent or customer. The firm's QA standard, the effective product-disclosure
requirements, and applicable conduct rules (e.g., FDCPA for collections, Reg Z/APR for
lending, investment risk disclosure) take precedence over these defaults.

## Check taxonomy

| Check | Severity | Fires when (default config) | Evidence attached |
| ----- | -------- | --------------------------- | ----------------- |
| `recording_consent_disclosure` | critical | Voice channel AND no recording/monitoring notice in the first `disclosure_deadline_turns` agent/IVR turns | Scanned scope (or the notice turn) |
| `identity_authentication` | critical | `requires_authentication` AND (no verification-complete marker, OR an account-specific disclosure precedes it) | The early-disclosure turn or scanned scope |
| `required_disclosures` | critical | A product-required disclosure's markers are absent from agent turns (one finding per missing item) | Scanned scope per disclosure id |
| `prohibited_language` | critical | Any configured prohibited phrase appears in an agent turn (guarantees, absolute promises, improper threats) | The offending turn(s) + matched phrase |
| `fair_treatment_vulnerability` | critical | A vulnerability cue is present (context flag or customer turn) AND no accommodation/referral marker in agent turns | The cue turn(s) or context scope |
| `complaint_acknowledgement` | coaching | A complaint cue is present in customer turns AND no acknowledgement/log/route marker by the agent | The complaint cue turn(s) |
| `commitment_capture` | coaching | The agent made an explicit follow-up commitment (call-back, refund, send) to capture for follow-up | The commitment turn(s) |
| `empathy_courtesy` | coaching | A customer distress cue is present AND no empathy acknowledgement by the agent | The distress cue turn(s) |

Checks are **independent and explainable**; the output reports each that fired with its own
evidence and the rubric item referenced. There is no opaque composite "quality score".

## Disposition mapping (deterministic, documented)

| Suggested band | Rule |
| -------------- | ---- |
| **Meets expectations** | 0 findings fired |
| **Coaching recommended** | ≥1 **coaching** finding fired AND 0 critical findings |
| **Compliance review required** | ≥1 **compliance-critical** finding fired |

The disposition is a **triage suggestion for a human QA lead / compliance reviewer**. It is
not a misconduct or regulatory-breach determination, a pass/fail that drives discipline, or
an instruction to act.

## Hard boundaries (fail closed)

- Never state or imply the agent **committed** misconduct, a **regulatory breach**, or a
  **reportable breach** — describe what the transcript shows factually and attribute
  conclusions to the human reviewer.
- Never decide or recommend a **disciplinary/HR action** (warning, termination, "fail").
- Never **file or recommend filing** a regulatory report; route to the compliance officer.
- Never tune markers/thresholds to the individual, and never use protected-class attributes
  or proxies as a signal.
- Prohibited-language and clustering checks describe **lexical patterns**, not intent.

## Considerations (always include when any finding fired)

An off-transcript IVR disclosure or authentication, a disclosure delivered in writing
(email/SMS), ASR/transcription errors that hide a spoken marker, a partial or redacted
transcript, or a mislabeled `product_context` that changes which disclosures are required.
The scorecard must invite the reviewer to weigh these before dispositioning.
