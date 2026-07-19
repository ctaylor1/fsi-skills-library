# Source Map — dispute-operations-assistant

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | Card-network **rules & bulletins** (current, via `network-rules-change-tracker`) | Reason-code meaning, required evidence, response windows, effective/version | Read-only |
| 2 | Issuer/acquirer **dispute case system** | Case + dispute state (system of record), `case_id`, role, stage | Read-only |
| 3 | **Transaction & authorization data** | Transaction identity, auth record, amounts, MCC, AVS/CVV/3DS results | Read-only |
| 4 | **Customer / merchant evidence** (banking core, OMS/fulfillment, documents) | Proof of delivery/service, receipts, terms, prior history | Read-only |
| 5 | **Response templates & controlled content** | Draft case-response scaffolding (versioned) | Read-only |

## Citation format

`{system}:{ref}@{date/version}` — e.g. `network-rules:visa:10.4@cardnet-2026.2`,
`casesys:case=DC-3001`, `txns:auth=A-8001@2026-06-20`, `evidence:proof_of_delivery:oms/pod-8004`.
Every reason-code basis, deadline, and exhibit in a draft must carry a citation.

## Freshness / effective dates

- The **reason-code catalog + response windows are a versioned contract**. Record the
  `current_rule_version` on every case record; a case citing a superseded version is
  `rule-version-stale` and must be refreshed before drafting (the window and required
  evidence themselves may have changed).
- Read case state fresh (avoid drafting on an already-decided or already-submitted case).
- Deadlines are computed against a stated `processing_date` for reproducibility.

## Least-privilege operations (deployment)

- `rules.get(network, reason_code, version)` → reason-code spec (window + required evidence).
- `cases.read(case_id | queue)`, `cases.find(role, network, status)` — read-only.
- `txns.read(txn_id | auth_id)`, `auth.read(auth_id)` — read-only, bounded.
- `evidence.read(case_id)` → typed exhibits with source refs — read-only.
- `templates.get('dispute-response', version)` — read-only.

No mutation from this skill. Any submission, credit posting, liability decision, or case
closure is a **human-authorized** action performed through the dispute case system via the
approval broker — never by this skill. Cardholder data is masked to last four; full PAN is
never read into the package (PCI DSS scope).
