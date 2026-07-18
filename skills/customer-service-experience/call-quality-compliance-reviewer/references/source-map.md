# Source Map — call-quality-compliance-reviewer

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | Contact-center **interaction transcript** (record of what was said) | The turns under review (diarized, de-identified) | Read-only |
| 2 | **CRM / case management** | Interaction context: authentication performed in IVR, prior contact, product, flags | Read-only |
| 3 | **Complaint system** | Whether a complaint was already logged/linked for this interaction | Read-only |
| 4 | **Approved-knowledge / product-terms** library | Which disclosures the product/journey requires (owned, effective-dated) | Read-only |
| 5 | Quality/compliance **rubric config** (versioned) | Disclosure/prohibited/auth/vulnerability marker sets and disposition mapping | Read-only |

Never substitute the reviewer's paraphrase for the transcript record. If the transcript and
a CRM note conflict (e.g., CRM says identity was verified in IVR but the agent transcript
shows an early account disclosure), cite both and flag for the human reviewer.

## Citation format

`transcript:int={interaction_id};turn={turn_id}[@ts]` for a specific turn, e.g.
`transcript:int=INT-55231;turn=t6@2026-07-14T09:01:10`. For an **absence** finding (a
required marker not found) the evidence cites the scanned scope, e.g.
`transcript:int=INT-55231;scan=disclosure_mini_miranda;agent_turns=5`.

## Freshness / effective dates

- The rubric (markers, lexicon, disposition mapping) is a **versioned contract**; the output
  records the `config_version` used so a review is reproducible.
- The required-disclosure set is **product- and journey-specific and effective-dated**;
  confirm the effective rubric for the interaction date, not today's.
- Absence-based checks depend on transcript completeness; record whether the transcript is
  full, partial, or excludes an IVR segment.

## Least-privilege operations (deployment)

- `transcript.get(interaction_id)` → diarized, de-identified turns.
- `crm.context(interaction_id)` → product, auth-in-IVR flag, prior-contact, vulnerability flag.
- `complaint.lookup(interaction_id)` → linked complaint status (read-only).
- `knowledge.required_disclosures(product, as_of)` → effective disclosure set.
- `config.get('cqc-rubric', version)` → marker sets, lexicon, disposition mapping.
All read-only, deterministic, durable `review_id`, below the fixed timeout; page long
transcripts as resumable stages.
