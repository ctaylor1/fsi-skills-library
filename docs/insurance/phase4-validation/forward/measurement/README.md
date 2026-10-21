# Forward measurement evaluation

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
