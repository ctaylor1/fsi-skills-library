# Source Map — beneficial-ownership-verifier

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Corporate registries / certified cap tables / trust & partnership deeds** (approved-source retrieval + document intelligence) | Authoritative ownership and control edges | Read-only |
| 2 | **Entity resolution** | Resolve entities and natural persons; dedupe aliases across the chain | Read-only |
| 3 | **KYC/AML record** | The entity's declared UBOs and prior verification state | Read-only |
| 4 | **Sanctions / PEP reference data** | Owner context for downstream screening (not adjudicated here) | Read-only |
| 5 | Jurisdiction **config pack** (versioned) | Threshold, control-prong rule, document freshness, effective date | Read-only |

The customer's **self-declaration is the object being reconciled**, never a source of truth.
When an authoritative registry filing and the declaration conflict, the registry outranks
the declaration, but the conflict is **surfaced as a gap**, not silently resolved.

## Citation format

`{system}:{ref}@{date}` — e.g. `reg:sos=DE;file=1234567;cap=P-1@2026-02-01`. Every computed
owner cites the ownership edges on its contributing chains; every control-prong person cites
the officer/control record; every gap cites its subject and (where applicable) evidence.

## Freshness / effective dates

- The jurisdiction `config` (threshold, control-prong rule, document-age window,
  `requirements_effective_date`) is a **versioned contract**; the output records the
  `config_version` used so a verification reproduces.
- Supporting documents carry `issued` / `expires`; a document older than `doc_max_age_days`
  or expired before the as-of date raises an `expired_document` gap.
- The as-of date anchors every freshness comparison and is echoed in the output.

## Least-privilege operations (deployment)

- `registry.get(entity_id)` / `docint.extract(doc_id)` → ownership & control edges with source refs.
- `entityres.resolve(node)` → canonical entity/person identity.
- `kyc.declared_ubos(case_id)` → the declaration to reconcile against.
- `config.get('ubo', jurisdiction, version)` → threshold + control-prong + freshness rules.

All read-only, deterministic, durable `verification_id`, below the fixed timeout; page large
ownership graphs as resumable stages. No write, no filing, no case-state change.
