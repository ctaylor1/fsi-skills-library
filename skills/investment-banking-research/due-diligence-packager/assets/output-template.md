<!--
Approved output template for due-diligence-packager.
Required section anchors (checked by scripts/validate_output.py): cover, executive_summary,
source_index, extracted_data, issue_log, open_questions, completeness, model_handoffs,
approvals, standing_note. Keep the "## <section_key>:" heading lines; fill under each.
DRAFT ONLY — never send, submit, or deliver this pack. External delivery is a human action
gated on recorded approvals.
-->

# Due Diligence Pack — {{project_codename}}  ({{pack_id}})

## cover: Deal header
- Pack ID: {{pack_id}}
- Deal / project: {{project_codename}}  (deal_id {{deal_id}})
- Target (masked): {{target_name_masked}}
- As-of date: {{as_of_date}}   |   Generated: {{generated_as_of}}
- Classification: Highly Confidential — MNPI / client-confidential
- Status: DRAFT — internal review only

## executive_summary: Summary
Concise, source-grounded overview of what the data room contains and the headline diligence
findings. State facts with citations; make NO valuation opinion, NO buy/sell recommendation,
and NO investment advice. Note completeness gaps here.

## source_index: Indexed source documents
| doc_id | title | type | date | version | owner | index_ref |
| ------ | ----- | ---- | ---- | ------- | ----- | --------- |
| {{doc_id}} | {{title}} | {{type}} | {{date}} | {{version}} | {{owner}} | {{index_ref}} |

## extracted_data: Key data points (every row cites an indexed source)
| field | value | unit | confidence | citation | source_doc |
| ----- | ----- | ---- | ---------- | -------- | ---------- |
| {{field}} | {{value}} | {{unit}} | {{confidence}} | {{citation}} | {{source_doc}} |

## issue_log: Diligence issues
| issue_id | category | severity | description | status | citation |
| -------- | -------- | -------- | ----------- | ------ | -------- |
| {{issue_id}} | {{category}} | {{severity}} | {{description}} | {{status}} | {{citation}} |

Issue summary: high {{high}} / medium {{medium}} / low {{low}} / total {{total}}.

## open_questions: Open questions & follow-ups
| q_id | topic | question | owner | priority |
| ---- | ----- | -------- | ----- | -------- |
| {{q_id}} | {{topic}} | {{question}} | {{owner}} | {{priority}} |

## completeness: Workstream coverage
- Covered: {{workstreams_covered}} of {{workstreams_total}}
- Missing (reported, not implied covered): {{missing_workstreams}}

## model_handoffs: Structured handoffs to modeling skills
| target_skill | payload_fields | note |
| ------------ | -------------- | ---- |
| {{target_skill}} | {{payload_fields}} | {{note}} |

## approvals: Approval ledger (external delivery gated)
| role | name (masked) | status | date |
| ---- | ------------- | ------ | ---- |
| diligence_lead | {{name_masked}} | {{status}} | {{date}} |
| quality_reviewer | {{name_masked}} | {{status}} | {{date}} |

External delivery is permitted only after BOTH roles are `approved`, and is performed by a
human — this skill never sends or submits.

## standing_note: Standing note
Draft diligence pack for internal review only; not approved for external delivery; no
valuation or investment recommendation is made.
