<!--
Approved output template for buyer-investor-list-builder.
Required section anchors (checked by scripts/validate_output.py): cover, executive_summary,
fit_criteria, source_index, buyer_list, outreach_waves, conflicts_hold, gaps, approvals,
standing_note. Keep the "## <section_key>:" heading lines; fill under each.
DRAFT ONLY - never send, deliver, or share this list, and never contact a buyer. External
delivery and outreach are human actions gated on recorded approvals.
-->

# Buyer / Investor List - {{project_codename}}  ({{list_id}})

## cover: Mandate header
- List ID: {{list_id}}
- Deal / project: {{project_codename}}  (mandate_id {{mandate_id}})
- Target (masked): {{target_name_masked}}   |   Process: {{process_type}}   |   Deal size: {{deal_size_band}}
- As-of date: {{as_of_date}}   |   Generated: {{generated_as_of}}
- Classification: Highly Confidential - MNPI / client-confidential
- Status: DRAFT - internal review only

## executive_summary: Summary
Concise, source-grounded overview of the universe: how many candidates, the wave split, and
any conflicts holds and gaps. State facts with citations; make NO buyer recommendation, NO
valuation opinion, and NO investment advice. Do NOT describe sending the list or contacting
buyers - those are human actions gated on approvals.

## fit_criteria: Documented fit criteria (deterministic)
Sector fit (strong +3 / moderate +1 / weak 0); size fit (high +3 / medium +2 / low +1);
geographic fit (+2); mandate/thesis fit (+2); precedent activity (+2); relationship (strong
+2 / some +1 / none 0). Waves: wave-1-priority >= 8; wave-2-standard 4-7; wave-3-broaden <= 3.

## source_index: Indexed sources
| doc_id | title | type | date | version | owner | index_ref |
| ------ | ----- | ---- | ---- | ------- | ----- | --------- |
| {{doc_id}} | {{title}} | {{type}} | {{date}} | {{version}} | {{owner}} | {{index_ref}} |

## buyer_list: Candidates (every rationale claim cites an indexed source)
| candidate | type | fit_score | disposition | relationship | rationale (cited) |
| --------- | ---- | --------- | ----------- | ------------ | ----------------- |
| {{name_masked}} | {{buyer_type}} | {{fit_score}} | {{disposition}} | {{relationship}} | {{claim}} [{{citation}}] |

## outreach_waves: Outreach sequencing plan (for a human; no contact is made here)
- Wave 1 (priority): {{wave_1_ids}}
- Wave 2 (standard): {{wave_2_ids}}
- Wave 3 (broaden): {{wave_3_ids}}

## conflicts_hold: Held for conflicts review (excluded from every wave)
| candidate | reason | route |
| --------- | ------ | ----- |
| {{name_masked}} | {{reason}} | conflicts-of-interest-reviewer |

## gaps: Data / sourcing gaps and duplicates
- needs-data (missing scoring fields): {{needs_data_ids}}
- needs-source (no rationale resolves to an indexed source): {{needs_source_ids}}
- duplicates (linked to prior outreach list): {{duplicate_ids}}

## approvals: Approval ledger (external delivery gated)
| role | name (masked) | status | date |
| ---- | ------------- | ------ | ---- |
| deal_lead | {{name_masked}} | {{status}} | {{date}} |
| conflicts_reviewer | {{name_masked}} | {{status}} | {{date}} |

External delivery and buyer outreach are permitted only after BOTH roles are `approved`, and
are performed by a human - this skill never sends, shares, or contacts.

## standing_note: Standing note
Draft buyer/investor list for internal review only; not approved for external delivery; no
buyer has been contacted and no investment recommendation is made.
