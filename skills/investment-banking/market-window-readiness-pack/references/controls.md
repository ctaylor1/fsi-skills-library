# Controls — market-window-readiness-pack

- **Risk tier:** R2 — analytical/packaging support. **Action mode:** Draft-only; no
  system-of-record change.
- **Human approval:** `external-delivery` — external delivery requires human sign-off; no launch
  decision or market-timing advice is ever made.

## Prohibited (fail closed)
- No **launch decision**, **pricing clearance**, or **market-timing advice** (window open/closed,
  when to price).
- No **assumption of readiness** for a missing attestation; no acceptance of an unjustified N/A.
- No **waiving a gate item**; no change to attestations or config.

## Required output screen (`scripts/validate_output.py`)
- Every gap carries a cited item + checklist version.
- No launch/timing language (regex: cleared to launch/approved the launch/launch now/window is
  open/time the market/should price now/go to market now).
- Suggested disposition is review-only (`ready-for-review` | `gaps-for-review`).
- Standing disclaimer present.

## Segregation of duties
The packager/analyst is not the launch approver; the packet supports, never replaces, banker
judgment and the launch process.

## Data classification, privacy, records
- **Highly Confidential (MNPI / client-confidential).** Enforce information barriers; deal-team
  only.
- Retain packet + citations + checklist version; log read + external-delivery approval.

## Reproducibility
`packet_id` binds output to the exact attestations and checklist version.
