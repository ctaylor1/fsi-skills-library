# Controls — submission-intake-triager

- **Risk tier:** R3 — regulated/control decision support. **Action mode:** Read-only analysis.
- **Human approval:** `required` — a licensed underwriter must adjudicate the routing
  recommendation before any bind, quote, price, decline, issuance, posting, case closure, or
  system-of-record change, and before any follow-up request is sent externally to the broker.

## Prohibited (fail closed)

The skill recommends and evidences only. It must never, in output or action:

- **Bind, quote, price, decline, or issue** coverage, or state/imply that coverage **is**
  bound, quoted, priced, declined, denied, or issued.
- Make or communicate a **binding underwriting decision** — accept/reject the risk, set
  terms, or approve/decline the submission.
- **Close** the submission or suppress it outside the documented deterministic triage logic.
- Draft or assert a **premium / price** number.
- **Tune appetite thresholds** to a broker or insured; use only the versioned appetite config.
- Present an **opaque score** as decisive; findings are explainable and cite evidence.

Every routing band — including `In-appetite` — routes to a **human underwriter**. No band is
an acceptance or a decline.

## Required output screens (`scripts/validate_output.py`)

- `routing_recommendation` is one of the four documented bands and **equals the deterministic
  mapping** from the appetite findings + critical gaps.
- Every `refer` / `out` appetite finding has ≥1 cited evidence row.
- Every reconciliation `mismatch` carries ≥2 cited source values (surfaced, not hidden).
- Follow-up requests exist whenever gaps exist.
- **No prohibited decision/bind/quote/price/decline/issue/closure language** in the narrative,
  notes, finding reasons, or follow-up text (regex screen).
- Standing disclaimer present: "Triage evidence and routing recommendation only; not a bind,
  quote, price, or coverage decision. A licensed underwriter adjudicates …".

A non-compliant packet (e.g., `evals/files/packet_with_decision.json`) **fails closed** with
exit 1.

## Fairness / conduct

- Triage strictly on the approved, documented appetite rules (state, class, capacity, loss
  ratio, catastrophe zone). Do not use protected-class attributes or proxies.
- Describe risk characteristics factually; avoid stigmatizing language about the insured.

## Data classification, privacy, records

- **Highly Confidential (customer/insured NPI/PII).** Minimize insured data to what evidences
  a finding or gap; mask identifiers where display is not required.
- Retain the packet + citations + `config_version` per records policy; log the read and any
  external-delivery approval.

## Reproducibility

`triage_id` binds the output to the exact inputs and **appetite config version**; re-running
with the same inputs and config reproduces the reconciliation, findings, and routing band.
