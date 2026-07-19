# Source Map — enterprise-risk-assessment-builder

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Risk register / GRC system** (system of record) | Risk inventory, categories, owners, inherent ratings, prior assessment | Read-only |
| 2 | **Control library / control-testing (GRC)** | Control design & operating effectiveness, test evidence, attestations | Read-only |
| 3 | **Risk appetite / limits framework** | Appetite bands and limits per category; tolerance thresholds | Read-only |
| 4 | **KRI / indicator store** | Indicator values, thresholds, breach and trend status | Read-only |
| 5 | **Loss / event database (operational risk)** | Loss and near-miss events, net loss, root-cause links | Read-only |
| 6 | **Scenario / stress library** | Severe-but-plausible scenarios and transmission channels | Read-only |
| 7 | **Third-party inventory** | Vendor criticality, resilience, exit-plan status | Read-only |
| 8 | **Finance & operational data** | Exposure, capital, volumes used to size impact | Read-only |
| 9 | **Scoring / appetite config** (versioned contract) | Inherent/residual banding and control-credit mapping | Read-only |

The risk register is the **system of record** for risk state; this skill never writes it.
Appetite bands and the scoring config are **versioned contracts** — the version is recorded on
the assessment (`config_version`, `template_version`) for reproducibility.

## Citation format

`{system}:{ref}@{date/version}` — e.g. `riskreg:R-001@2026-06-30`,
`grc:C-101-test@2026-05`, `kri:KRI-CRE-01@2026-06-30`, `config:erm-scoring@2026.06`.
Every inherent/residual rating, control-effectiveness claim, KRI value, loss event, and
scenario in the draft must carry a citation to an Evidence Register entry.

## Freshness / effective dates

- Read risk, control-test, appetite, and KRI state **fresh** for the assessment period; a
  stale control test does not evidence current operating effectiveness.
- Control credit toward residual risk is taken **only** when the control is tested within the
  assessment window **and** carries an evidence reference. Untested or unevidenced controls
  earn no credit and are flagged in **Limitations & Assumptions** (fail-closed).
- Scoring/appetite/template versions are stamped on every output for review and reproduction.

## Least-privilege operations (deployment)

- `riskreg.read(entity|risk_id)`, `controls.read(control_id)`, `controltests.read(control_id, period)` — read-only.
- `appetite.get(category, version)`, `kri.read(indicator_id)`, `loss.read(event_id)`,
  `scenarios.read(scenario_id)`, `thirdparty.read(vendor_id)` — read-only, bounded.
- `config.get('erm-scoring'|'erm-template', version)` — read-only.
No mutation from this skill. The completed draft is handed to a human; any acceptance,
approval, attestation, or write to the risk register happens **only** via the approval broker
under a named human, outside this skill.
