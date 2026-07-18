# Domain Rules — communications-compliance-reviewer

Explainable communications-compliance **findings** and how they map to a **recommended review
disposition**. Thresholds, the prohibited-claim library, and disclosure requirements are
configuration (versioned, owned by the communications-compliance team), not hard-coded
judgments. Rule citations are **orientation labels**; the firm's Written Supervisory
Procedures (WSPs), the current FINRA/SEC rule text, and any configured jurisdiction pack take
precedence. This skill surfaces findings for a **registered principal** to adjudicate — it
never approves, files, or closes a review.

## Communication classification (FINRA Rule 2210(a))

| Class | Fires when (default config) | Supervision expectation |
| ----- | --------------------------- | ----------------------- |
| **Retail communication** | Distributed/available to **more than 25 retail investors** within the window (default 30 days), or retail with an unknown count (conservative default) | Registered-principal **pre-approval before first use** |
| **Correspondence** | Retail, **25 or fewer** retail investors within the window | Supervisory **review** per WSPs |
| **Institutional communication** | Audience is institutional only | Supervisory **review**; retail-only disclosures not required |
| **Internal** | Internal-only communication | Records retention + escalation review; public-comm content standards N/A |

## Finding taxonomy

| Finding | Fires when | Rule (orientation) | Severity |
| ------- | ---------- | ------------------ | -------- |
| `prohibited_claim` | Guarantee, 'risk-free'/'no-risk'/'riskless', 'cannot-lose', promissory, or assured-return language (public comms) | 2210(d)(1) | high |
| `performance_prediction` | Predicts/projects future performance without permitted-projection basis | 2210(d)(1)(F) | high |
| `fair_and_balanced` | Benefits/returns described with no corresponding risk disclosure (one-sided) | 2210(d)(1)(A) | medium |
| `missing_required_disclosure` | A required disclosure for the class/channel is absent (member name; past-performance disclaimer when performance is discussed; BrokerCheck reference on retail website/social; testimonial disclosures) | 2210(d) / 2210(d)(8) | medium |
| `supervision_gap` | Retail communication with **no principal pre-approval**; or correspondence/institutional/internal with **no review** on record | 2210(b)(1) / 3110 | high (retail) / medium (other) |
| `off_channel` | Business communication on an **unapproved (off-channel)** medium not captured for retention | SEC 17a-4 / FINRA 4511 | high |
| `retention_gap` | Communication not recorded as archived in an approved retention system | SEC 17a-4 / FINRA 4511 | medium |
| `escalation_needed` | Language indicating possible MNPI misuse / market abuse, or a customer complaint | 3110 / 4513 / 4530 | high |

Findings are **additive and independent**; each fired finding is reported with its own cited
evidence. There is no opaque composite "compliance score".

## Disposition mapping (deterministic, documented)

| Recommended band | Rule |
| ---------------- | ---- |
| **Escalate** | Any **high**-severity finding fired |
| **Remediate** | One or more **medium** findings, no high |
| **Advisory** | Only **low**-severity findings |
| **No-exceptions** | No findings fired |

The disposition is a **recommendation for a registered principal**. It is not a supervisory
approval, a filing, or a review closure. **No-exceptions does not mean approved** — principal
review is still mandatory before any use.

## Hard boundaries (fail closed)

- Never **approve** a communication, mark it cleared/fit for use, or grant principal approval.
- Never **file** a communication (e.g., with FINRA) or state that it was filed.
- Never **close** or dispose of the review, or state that no further review is needed.
- Never characterize conduct as a **confirmed violation** — describe the finding factually and
  attribute the decision to the registered principal.
- Never tune classification thresholds or the claim library to a specific author/campaign; use
  only the versioned config.

## Notes and edge cases

- `%`, "return", and performance terms trigger the past-performance disclosure requirement even
  when the number looks small — the principal weighs materiality.
- Prohibited-claim and prediction scans are conservative keyword matches; a hit is a **finding
  to review**, not a determination. False positives are expected and are the reviewer's to
  clear.
- Institutional and internal communications skip retail-only disclosure checks but remain
  subject to content standards (no false/misleading claims), supervision, retention, and
  escalation.
