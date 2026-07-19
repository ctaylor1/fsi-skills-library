# Domain Rules — security-alert-triage-assistant

Orientation references: NIST SP 800-61 (computer-security incident handling), MITRE ATT&CK for
signal context, CISA Known Exploited Vulnerabilities (KEV) catalog, and the firm's SOC runbook
and operational-resilience standard. The firm's SOC standard and its **approved suppression rule
set + priority config + output template** take precedence and are versioned contracts. This
skill enriches and prioritizes; it makes no security decision and takes no response action.

## Priority scoring (deterministic, documented)

Priority is computed from explainable inputs; the mapping is configuration, not judgement, and
the band is a **triage rank for a human analyst — never a verdict, closure, or response
decision**.

| Input | Contribution (default) |
| ----- | ---------------------- |
| Asset criticality | Critical +4, High +3, Medium +1, Low 0 |
| Identity privilege | Privileged +3, Service +2, Standard 0 |
| Threat-intel severity | known-malicious +4 (also forces escalate + P1), high +3, medium +1, low/none 0 |
| Internet-facing exposure | +2 |
| Known-exploited-vulnerability (KEV) nexus | +3 |
| Signal confidence | high +2, medium +1, low 0 |
| Correlation / velocity (related alerts in window) | +1 per correlated alert, capped +3 |

Bands: **P1 (Critical)** total ≥ 9 or any known-malicious indicator; **P2 (High)** 5–8;
**P3 (Moderate)** ≤ 4. Priority is a triage rank, not a determination.

## Approved suppression rules (the ONLY suppressions permitted)

| Rule ID | Condition | Evidence required |
| ------- | --------- | ----------------- |
| `SUP-DUP-01` | Exact duplicate of an open alert/case (same asset, signature, window; signals ⊆ parent) | Parent `case_id` + matched signal ids |
| `SUP-SCANNER-01` | Source is a firm-authorized vulnerability scanner on the approved allowlist | Scanner id + qualifying signal ids |
| `SUP-MAINT-01` | Activity matches a documented, approved maintenance/change window | Change/maintenance window id + qualifying signal ids |

Any alert **not** matching one of these is **not** suppressible by this skill. Suppression is
logged with the rule id and the approved-rule-set version and is subject to reviewer sampling.
Suppression removes known-benign **noise**; it is **not** a disposition and never applies to a
genuine alert. A **known-malicious threat-intel indicator overrides suppression** and forces
escalation.

## Hard boundaries (fail closed)

- No **alert closure/disposition**, **incident declaration/closure**, or communication of one.
- No **containment / response action** — isolation, account disable/lock, IP/domain/hash block,
  credential reset/rotation, process/session kill, remediation.
- No **suppression** outside the three approved rules above.
- No **system-of-record write** (SIEM/SOAR/ticketing) and no **send/submit** of the package.
- No **threat-intel / vulnerability / cloud-posture / access conclusion** — route to the specialist.
- **Active compromise** indicator ⇒ `package_status = blocked`, urgent route to incident
  response; this skill performs no containment.

## Package status → recommended handling

| Status | Meaning | Recommended handling |
| ------ | ------- | -------------------- |
| `blocked` | Active-compromise hard boundary present | Hold routine triage; hand to incident response immediately |
| `needs-data` | An alert has unresolved enrichment (e.g., asset not in CMDB) | Return for data; never guess to clear an alert |
| `ready-for-analyst` | All alerts triaged, no hard boundary | Present the package for analyst investigation |

The handling is a **recommendation**; the human analyst chooses and records the actual
disposition, incident decision, and any response action.

## Triage package — required contents

Durable `case_id` per alert; batch overview; enrichment (asset/identity/threat-intel/posture)
with citations; affected-asset/identity map; correlation/deduplication links; deterministic
priority with factors; approved-suppression log; analyst-ready investigation context with
advisory next steps; advisory specialist routing; an approval ledger listing every required role
with status; an aggregate sources-and-citations list; and the standing note (draft-only /
no-decision / no-containment limitation).
