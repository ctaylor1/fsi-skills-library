# Domain Rules — regulatory-change-impact-analyzer

Explainable impact **findings** and how they map to a recommended **disposition band**.
Thresholds are configuration (versioned, owned by the compliance change-management function),
not hard-coded judgments. The primary regulatory text and the firm's regulatory-change
standard take precedence over this reference.

## Applicability test (deterministic)

An obligation is **applicable** when BOTH hold:

- **Jurisdiction:** the instrument's jurisdiction is one the firm operates in
  (`instrument.jurisdiction ∈ firm_profile.jurisdictions`).
- **Business line:** the obligation's `applies_to_lines` overlaps the firm's business lines,
  OR the obligation is firm-wide (`applies_to_lines` empty or `["all"]`).

Applicability is a **recommendation with cited basis**, not a decision — a human confirms
scope and any exemption. If nothing is applicable on the data, the disposition is
`Informational` and the analyst must confirm the scoping rationale before the item is
dispositioned (the skill never auto-closes an "out of scope" change).

## Finding taxonomy

| Finding | Raised when | Evidence attached |
| ------- | ----------- | ----------------- |
| `applicable_in_scope` | ≥1 obligation is applicable to the firm | Applicable obligations + type + citation |
| `mapping_gap` | An applicable obligation lacks a required policy or control in the inventory (`require_policy`/`require_control`) | Obligation + what is missing |
| `owner_gap` | An applicable obligation has no named owner (`require_owner`) | Obligation + citation |
| `overdue_or_retroactive` | `effective_date ≤ as_of` (already effective/overdue) OR `effective_date < publication_date` (retroactive) | Instrument dates |
| `short_lead_time` | Future effective date with `lead_days < near_term_days` (default 30) | Instrument dates + lead days |
| `authority_conflict` | An applicable obligation declares a `conflicts_with` entry (another instrument/jurisdiction) | Obligation + both requirements |

Findings are **additive and independent**; each raised finding carries its own evidence.
There is no opaque composite "compliance score".

## Disposition mapping (deterministic, documented)

Let `raised` = the set of raised findings. `escalators = {overdue_or_retroactive, authority_conflict}`.

| Recommended band | Rule |
| ---------------- | ---- |
| **Informational** | No obligation applicable (out of scope on the data — human confirms rationale) |
| **Assess** | Applicable, and 1–2 findings raised with no escalator |
| **Priority** | Applicable AND (any escalator raised, OR ≥ 3 findings raised) |

Disposition is a **triage recommendation for a human adjudicator**. It is not a compliance
determination and it never closes the change, files, or attests.

## Hard boundaries (fail closed)

- Never state or imply the firm **is / is not compliant**, that an obligation is satisfied, or
  that a gap is/creates a violation — describe findings factually and attribute conclusions to
  the human adjudicator.
- Never **decide applicability to close scope**, **close/disposition** the change, **file** or
  **attest**, or **resolve a conflict** — surface and route.
- Never tune thresholds to force a disposition; use only the versioned config.
- `authority_conflict` describes a **conflict to be read by legal**, not a resolved position.

## Adjudication prompts (always include when any obligation is applicable)

Confirm authoritative text and effective date against the primary source; confirm business-line
applicability and exemptions with the owner; for each mapping gap decide whether a new/updated
policy or control is required (route to gap analysis); obtain a legal reading for any conflict;
record the implementation decision, owner, and target date. A human adjudicates disposition and
closure.
