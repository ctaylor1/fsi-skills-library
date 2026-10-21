# Fund Commentary — Output Template

Controlled draft template for periodic (monthly / quarterly) fund commentary. The drafter
fills every section from **reconciled** sources and the **approved messaging** library. Every
factual or performance statement must carry a source citation in the claim ledger. The
draft is **not for distribution** until the product and compliance sign-off blocks are
completed. `scripts/validate_output.py` checks that all required sections are present, that
figures tie out, that no claim is unsupported, that no prohibited language appears, and that
both approvals are recorded.

---

## Header
- **Fund / share class:** `{fund_name} ({share_class})` · **Currency:** `{currency}`
- **Benchmark:** `{benchmark}`
- **Period:** `{period.type}` — `{period.label}` (`{period.from}` to `{period.to}`)
- **Template version:** `{template_version}` · **Prior commentary:** `{prior_commentary_ref}`

## Required sections (all mandatory)

### 1. performance_summary
Headline return of the fund vs. benchmark and the resulting excess/active return for the
period. Every number ties to `reconciled_performance` (`excess == fund − benchmark`).

### 2. attribution
Decomposition of relative return into effects (allocation, selection, currency, and any
others). Effects tie out: `sum(effects) == total_excess == performance excess`. Name the
primary driver(s); do not assert a driver not present in the attribution source.

### 3. positioning
Material over/underweights and notable changes over the period, each cited to a positioning
source. Must be consistent with the attribution narrative.

### 4. flows
Net subscriptions/redemptions for the period, cited to the flows source.

### 5. market_context
Brief market backdrop for the period, cited to the market-commentary source. Descriptive of
the period only — no forward guarantees.

### 6. outlook
Forward-looking view drawn **only** from the approved messaging library. No performance
promises, guarantees, or target returns. Clearly framed as opinion, not assurance.

### 7. disclosures
All required disclosure IDs for this fund/jurisdiction (e.g. past-performance, benchmark
definition, marketing-communication status). `required_disclosures ⊆ disclosures_present`.

---

## Claim ledger (accompanies the draft)
Each row: `claim_id | section | text | source_refs[] | supported | period_label`. A claim is
release-ready only when `supported == true` with at least one resolvable citation and its
`period_label` matches the commentary period. Any unsupported claim is listed separately and
**removed or resolved** before release — never asserted.

## Tie-out block
- `performance`: `ok` + detail (`excess == fund − benchmark`).
- `attribution`: `ok` + detail (`effects sum == total_excess == performance excess`).

## Sign-off block (required before external delivery)
| Role | Status | Approver | Date | Notes |
| ---- | ------ | -------- | ---- | ----- |
| Product | `approved` | `{name}` | `{yyyy-mm-dd}` | consistency with fund & messaging |
| Compliance | `approved` | `{name}` | `{yyyy-mm-dd}` | disclosures, prohibited-claim screen |

- **delivery_status:** must remain `draft` / `approved-for-delivery`. This skill never sets
  `sent`, `submitted`, `distributed`, `published`, or `filed`.
- **Standing note (verbatim):** "Draft only - not for distribution until product and
  compliance approvals are recorded; this skill does not send, file, or publish."
