# Adjacent-Skill Handoffs — security-alert-triage-assistant

Security-alert triage is a **draft-and-package** control activity. It sits between the raw
SIEM/SOAR alert queue (upstream) and specialist investigation / incident response (downstream).
It enriches, prioritizes, correlates, and packages analyst-ready context; it never performs the
specialist's work, closes an alert, declares an incident, or takes a response action.

## Upstream (feeds this skill)

The SIEM/SOAR platform produces the raw alert queue. This skill is **interactive** triage
(`aws-fsi-scheduled-agent: no`); a read-only monitor may *populate* a queue but must not triage,
suppress, decide, or act. The batch intake is a de-identified JSON conforming to
[source-map.md](source-map.md).

## Downstream — specialist corroboration / investigation (this skill routes to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `cyber-incident-response-coordinator` | Malware/C2, ransomware-precursor, or any active-compromise indicator (hard boundary → `blocked`) | `case_id` + investigation context + urgency |
| `phishing-and-bec-investigator` | Phishing / business-email-compromise alert class | `case_id` + message/indicator evidence |
| `identity-access-reviewer` | Authentication anomaly, privilege escalation, or brute-force on an identity | `case_id` + identity + signal evidence |
| `vulnerability-prioritization-assistant` | Exploit attempt against a known-exploited-vulnerability nexus | `case_id` + asset + KEV context |
| `cloud-security-posture-reviewer` | Cloud misconfiguration / posture finding | `case_id` + cloud-posture evidence |
| `data-loss-prevention-incident-assistant` | Data-exfiltration / DLP signal | `case_id` + data-movement evidence |
| `third-party-cyber-risk-reviewer` | Alert implicates a third-party/vendor connection | `case_id` + third-party context |

## Downstream — human decision + reporting

The completed draft package is handed to the **human SOC analyst / incident-response process**,
which decides the alert disposition, declares or closes any incident, and authorizes any
containment or remediation. Operational-resilience reporting of a resulting incident is a
separate activity for `operational-resilience-reporter`; this skill never initiates it.

## Duplicate-execution prevention

- This skill **does not** investigate, disposition threat intel, prioritize vulnerabilities,
  review access, confirm cloud posture, declare incidents, or take response actions — those
  belong to the named skills or the human IR process.
- The specialist consumes the triage `case_id` + investigation context rather than re-triaging.
- A `correlated-duplicate` link is resolved by a human, not auto-merged here; an exact duplicate
  is suppressed under `SUP-DUP-01` and linked to its parent, never closed.
