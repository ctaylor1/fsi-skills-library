# Cedar Harbor policy/claim data contract — draft, 20 September 2026

Owen Diaz owns this synthetic historical FNOL-context design. REV-4 v4 supplies the review profile; DICT-2 v2 supplies semantic records. Purpose: reproduce the exact policy form in a draft claim context at a specified loss-valid date and knowledge cutoff, without interpreting coverage.

## Contract proposal

Grain: one assertion per exact namespaced entity, field, validity interval and recording date. Preserve policy `PolicySandbox:CH-20` and claim `ClaimsSandbox:CL-9`; native entity IDs are `policy:CH-20` and `claim:CL-9`. The supplied exact claim-to-policy link is CL-9→CH-20, many-to-one: one policy per claim, potentially many claims per policy. Do not join by person name or infer additional links.

`policy.form_code` means the exact issued form-edition code. Its source is PolicySandbox.form_edition; transformation is identity with edition suffix preserved; unit is a form code. Proposed required-field validation is a unique nonblank edition at the requested dates. Owen owns the field; classification is synthetic; named data and claims sandbox reviewers may inspect it. Synthetic artifacts remain through owner review. Production retention is undecided, not supplied as a number.

Valid intervals are [from,to). A1 is CP-2025, valid 1 January through but excluding 1 June, recorded 2 January. A2 is CP-2026, valid from 1 June with no stated end, recorded 3 June. Querying valid 1 July / known 10 June identifies A2. `data-early.output.json` resolves CP-2026 under its original completeness/review assumptions. At known 20 September, late assertion A3 (recorded 19 September, valid from 1 June, CP-2025) overlaps A2. `data-conflict.output.json` retains both record IDs and returns null, with temporal-conflict and required-value findings. The late assertion is not automatically authoritative.

## Source fidelity correction and current acceptance

The first mapper incorrectly set `purpose_reviewed=true` and `sample_inventory_complete=true` although DICT-2 specifies a purpose and samples without affirming those reviews/completeness. These are retained evaluation failures. `data-source-audited.input.json` corrects both to null; its native output is needs-data and withholds the resolved value. Thus CP-2026 above is a conditional sample illustration, not an accepted semantic contract. The raw sources were not changed to justify the first output.

Owen must confirm purpose review and inventory completeness, adjudicate A2/A3 from issuance evidence, and explain whether correction/supersession history requires a recorded-end or explicit supersession model. The current package deliberately conflicts overlapping assertions; it cannot by itself implement a full correction history. Producer acceptance should cover exact key uniqueness, interval boundaries and overlap; consumer acceptance should cover both knowledge cutoffs and explicitly unresolved claims. Run the mapped receiving package's own validator before a handoff. ACORD conformance, production identity resolution, licensed schema access, privacy review and deployment remain unassessed. No pipeline or system connection was created.
