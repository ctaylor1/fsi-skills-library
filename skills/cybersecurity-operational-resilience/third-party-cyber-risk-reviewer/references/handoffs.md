# Adjacent-Skill Handoffs — third-party-cyber-risk-reviewer

This skill produces a cited **supplier cyber-risk review** (`review_id`) with a suggested
residual tier and stops. It does not adjudicate, onboard, risk-accept, file, or write a
system of record — a human risk owner does, outside this skill.

## Downstream (route the human/reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `third-party-risk-assessor` | The engagement needs enterprise-wide TPRM scope (financial, operational, reputational) beyond cyber | `review_id` + findings |
| `third-party-ai-due-diligence-assistant` | The supplier delivers AI/ML capability needing model/AI-specific due diligence | `review_id` + supplier ref |
| `cyber-incident-response-coordinator` | A supplier incident is active and affecting our data/services now | incident evidence rows |
| `vulnerability-prioritization-assistant` | Supplier-disclosed vulnerabilities need prioritization against our exposure | vulnerability evidence rows |
| `concentration-risk-monitor` | Supplier concentration / substitutability must be assessed for an important service | supplier ref + criticality |
| `operational-resilience-scenario-tester` | The impact of this supplier's failure on an important business service needs testing | supplier ref + service mapping |
| `operational-resilience-reporter` | Findings feed periodic operational-resilience / outsourcing reporting | `review_id` + residual tier |

Other cyber deep-dives (`cloud-security-posture-reviewer`, `identity-access-reviewer`,
`data-loss-prevention-incident-assistant`, `ransomware-readiness-assessor`) may be routed to
when a specific control domain needs specialist review. The **adjudication decision itself**
(approve / reject / risk-accept / onboard / exception) is a **human risk-owner** action and a
GRC/TPRM system-of-record write — not any skill.

## Upstream (may call this skill)

`third-party-risk-assessor` and the procurement / vendor-management intake process may
request a cyber sub-review. A scheduled monitor is **not** used here (this skill is
interactive, `aws-fsi-scheduled-agent: no`).

## Duplicate-execution prevention

- This skill computes and evidences **findings and a suggested tier only**; it must not reach
  a supplier decision, notify the supplier, or write a register — those belong to the human
  risk owner and the downstream skills/systems.
- Downstream skills reuse the `review_id` evidence rather than recomputing findings.
