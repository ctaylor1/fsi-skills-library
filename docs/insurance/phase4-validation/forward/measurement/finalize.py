from pathlib import Path
import hashlib,json
P=Path('/tmp/insurance-p4-forward-measurement')
for kind in ['architecture','automation','data','operations']:
 s=(P/(kind+'-draft.md')).read_text();s=s.replace('Native evidence:', 'Replayed native evidence (repairs folder):')
 if kind=='data':
  s=s.replace('its false license_usable_for_stated_purpose flag is misleadingly affected by unrelated projection gaps and must not be read as a license revocation.','the repaired license_usable_for_stated_purpose flag remains true because projection gaps do not change the supplied license scope. The original misleading false flag is retained in the parent folder for audit.')
 if kind=='operations':
  s=s.replace('They are extract-only calculations until Elena reconciles the discrepancy;', 'The repaired output explicitly sets snapshot_reconciled=false. They are extract-only calculations until Elena reconciles the discrepancy;')
  s=s.replace('Despite complete timing and completed-case costs, the current tool suppresses all window aggregates, including queue counts and utilization. Do not fill unknowns with zero to obtain output. The complete-case run uses separately supplied fictional accrual records instead; it does not repair the raw packet invisibly. This is a practical dependency limitation for real queues with unfinished accounting.', 'The original tool suppressed all window aggregates despite complete timing and completed-case costs. The repaired tool now computes the same queue and completed-cohort results while retaining both open episodes\' costs and labor as null. No zero substitution or fabricated accrual is needed. The complete-case supplemental-accrual run remains as a separate evidence case. See operations-unknown-open-cost-output.json in this repairs folder.')
 (P/'repairs'/(kind+'-draft.md')).write_text(s)
(P/'README.md').write_text('''# Forward measurement evaluation

All cases and owners are fictional. Review date 2026-09-20. No external systems, production data, repo edits, or professional approvals were used. The four installed packages were exercised as an independent author using their instructions, references and templates. Cases were newly originated for this brief rather than copied from bundled eval fixtures.

## Read these first

- `repairs/architecture-draft.md`: provider-neutral assisted-intake components, interfaces, scoped measurement and recovery acceptance.
- `repairs/automation-draft.md`: four-case paired measurement, cash versus capacity, negative economics, control evidence and next measurement.
- `repairs/data-draft.md`: six-case licensed enrichment review with four matches, two explicit fallbacks and time-correct outcome assessment.
- `repairs/operations-draft.md`: complete episode window with opening work, arrivals, completion, cancellation, unfinished ages and contradictory tally.
- `FINDINGS.md`: original usability findings, repair replay results, and limitations.

## Evidence and reproduction

`raw-evidence.json` is the original modest fact packet; `raw-profiles.json` supplies explicit owner-reviewed fictional method profiles. Sources include exact IDs, versions, dates, owners and section locators. `supplemental-evidence.json` is a clearly separate new fictional record containing detailed proposed interface contracts, six required control-category observations and accrued open-episode costs. The open-cost probe intentionally leaves those costs unknown.

`initial-run/` retains the original input mappings and all native outputs/validator results. They all returned exit 0 but remained needs-data because of profile nesting and omitted enum/category details. Initial architecture's I1/I2 and recovery elaboration were evaluator design proposals rather than authenticated raw operational facts; the second mapping explicitly source-binds them to the separately labeled proposal in SUP-1. No initial result is represented as substantive success.

Root `*-input.json` and `*-output.json` are the clarified mappings and pre-repair outputs. Root practitioner drafts describe those original outcomes. `repairs/` contains byte-identical copies of the same ten inputs, fresh native outputs after parent-agent repairs, and current practitioner drafts. Original adverse results were not overwritten by repair replay. `repairs/comparison.json` retains before/after results and findings. `commands.json`, `probe-commands.json`, `initial-run/commands.json`, and `repairs/commands.json` retain exact CLI arguments and exits. Each native output is separate from the authored Markdown.

Initial build: `/tmp/fsi-p0-venv/bin/python /tmp/insurance-p4-forward-measurement/build_cases.py`
Initial mapping refinement: `/tmp/fsi-p0-venv/bin/python /tmp/insurance-p4-forward-measurement/refine_contract_mapping.py`
Native run: `/tmp/fsi-p0-venv/bin/python /tmp/insurance-p4-forward-measurement/run_cases.py`
Additional probes: `/tmp/fsi-p0-venv/bin/python /tmp/insurance-p4-forward-measurement/run_probes.py`
Exact-input repair replay: `/tmp/fsi-p0-venv/bin/python /tmp/insurance-p4-forward-measurement/replay_repairs.py`
Independent fact arithmetic and retained-source/authority audit: `/tmp/fsi-p0-venv/bin/python /tmp/insurance-p4-forward-measurement/audit.py`

Do not rerun build/refinement over this retained evaluation directory: their purpose is to document how cases were originated and mapped; copy elsewhere for a fresh run. Package code has changed during the parent task. `package-snapshot/` was captured during that editing period and includes clarified schemas; it is not a pristine pre-repair source archive. Original outputs, inputs and observed failure messages remain authoritative evidence of the original runs.

## Scope

74 independent arithmetic, source-retention and authority checks passed against raw facts and repaired outputs. The final repair replay ran 30 native commands with zero nonzero exits. These checks are bounded diagnostic evidence, not institutional acceptance. No representative population, live license authentication, privacy approval, accessibility review, claim authority or deployment behavior was tested.
''')
(P/'FINDINGS.md').write_text('''# Findings and disposition

## F1 — Documentation did not fully specify the native input contract (resolved in current docs)

The originally read schema profile paragraph (line 7 in all four packages) described required profile fields without specifying data.profile. A top-level profile produced `reviewed rule profile unavailable`, with dependent metrics null. Automation schema's requested_mode row (line 21) only said text/null; its controls rows did not enumerate the six mandatory control IDs. Initial human-assist and two meaningful controls therefore failed semantic completeness. Architecture operation row (line 48) did not state read/proposed-write, so write was rejected as a gap. These are workflow usability failures rather than unsafe arithmetic. Exact original errors and successful validation exits are in initial-run/. Runtime diagnostics and narrowly targeted implementation searches resolved nesting and enums. The parent added explicit documentation.

Schema-only mappings: profile moved to data.profile for every case; human-assist became assist; write became proposed-write. Optional data projection=null explicitly declines projection. These edits were distinct from new fictional evidence: six required tests and full proposed contracts were newly supplied in SUP-1; backlog accruals were also supplied separately, never inferred as zero. This separation prevents a success-shaped record from being mistaken for unchanged source evidence.

## F2 — Open-episode unknown amounts blocked unrelated queue measures (resolved in replay)

operations-unknown-open-cost-input.json has complete timestamps and completed-episode cost/labor. Only E2/E5, still open, lack amounts. Original native output withheld every aggregate. The broad original rule that evidence gaps withhold aggregates allowed this conservatism, but it conflicted operationally with the narrower completed-cohort cost definition and made ordinary incomplete accounting unusable. Replayed identical input now retains those source nulls, returns opening 2, arrivals 3, completed 2, cancelled 1, closing 2; mean 15 hours; nearest-rank p95 24; cost 24; labor 30; utilization .75. There is no invented value.

## F3 — License flag depended on unrelated benchmark/projection sufficiency (resolved in replay)

With an explicitly unreviewed optional projection, observed metrics were already preserved once profile mapping was fixed: 4/6 coverage and $60 reduction. The initial suspicion that projection suppressed observed results was disproved; earlier outputs were confounded by the wrong profile location. However `license_usable_for_stated_purpose` changed to false solely on missing projection inputs (and separately on temporal leakage) despite identical supplied license evidence. Repaired outputs keep the license flag true while withholding the invalid comparison or projection. This scopes the flag correctly; it remains an unauthenticated assertion check.

## F4 — Contradictory independent queue control needed explicit qualification (resolved in replay)

A closing tally of 3 conflicts with extract closing 2. Original output marked needs-review and difference -1 but retained all numeric aggregates, whereas original method prose said inventory/evidence gaps withhold aggregates. This was not silent arithmetic acceptance, but the scope of retained figures was unclear. Replayed output now adds snapshot_reconciled=false, and current draft labels all measures extract-only until Elena reconciles the discrepancy. The parent is clarifying method prose. No staffing action is authorized.

## Arithmetic and evidence outcomes

Architecture: 280+420+160=$860/month; scoped 640ms <=700ms. Imperfect mismatched workload plus unknown quote correctly null fit and total.
Automation: baseline 20 vs candidate 14 human minutes; baseline/candidate errors both 1/4 with different failed cases; candidate nonlabor $3 vs $1. Six thousand eligible annual cases free 600 capacity hours valued at $28,800, yet cash nets are -$18,000 at 0% realization and -$3,600 at 50%; no payback or pilot recommendation. Missing rework timing and failed duplicate replay correctly withhold the dependent case.
Data: 4/6 matches; baseline TP1/TN2/FP1/FN2, augmented TP2/TN2/FP1/FN1. Costs $240 vs $180 = $60 reduction. Both unmatched outcomes are retained. No representative annual projection. D1 future availability correctly blocks the benchmark.
Operations: queue conservation 2+3−2−1=2; completed 24h/6h yields mean 15h and nearest-rank p95 24h; completed cost $24 and labor 30m; unfinished ages 30h/8h; utilization 12/16=.75.

All ten repaired outputs retained byte-equivalent parsed source documents, false action_taken, true human_review_required, approval=not_requested and execution=not_performed. The 74-check audit uses original raw rows for arithmetic, not script outputs as expected values. Narrative review separately checks scope, contrary cases, unknowns and owner boundaries.

## Limitations and process disclosure

These tiny purposive fictional samples do not prove real source truth, production control behavior, representativeness, legal rights or professional acceptance. Source IDs and hashes demonstrate retention, not authenticity. The evaluator read SKILL/references/templates first, and inspected narrow runtime contract locations only after semantic failures. One broad scripts/*.py search unintentionally returned three test_domain.py profile/measurement-scope lines; no bundled fixtures or test datasets were opened or used to originate facts or expected arithmetic. This is a disclosed minor departure from the intended clean documentation-only setup. Exact original failures and derived inputs are retained rather than concealed.

No repository files were changed by this evaluator. Parent-owned repairs were evaluated through the exact-input replay, without adjusting cases to fit the repaired outputs.
''')
files={str(f.relative_to(P)):hashlib.sha256(f.read_bytes()).hexdigest() for f in P.rglob('*') if f.is_file() and f.name!='manifest.json'}
(P/'manifest.json').write_text(json.dumps(files,indent=2)+'\n')
print('Retained',len(files),'files with manifest hashes')
