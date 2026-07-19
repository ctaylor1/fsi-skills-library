# Adjacent-Skill Handoffs — data-loss-prevention-incident-assistant

DLP incident assessment is a **draft-and-package** control activity. It sits between a DLP/SIEM
alert (upstream) and specialist investigation, incident response, and privacy/legal breach
adjudication (downstream). It enriches, classifies, estimates exposure, preserves evidence
references, and packages review-ready context; it never determines a breach, dispositions an
incident, decides or issues a notification, or takes a response action.

## Upstream (feeds this skill)

The DLP console / SIEM-SOAR produces the raw DLP event, or `security-alert-triage-assistant`
routes a `data-exfil` alert here with a `case_id` and data-movement evidence. This skill is
**interactive** (`aws-fsi-scheduled-agent: no`); a read-only monitor may *populate* a queue but
must not assess, classify, suppress, decide, or act. The batch intake is a de-identified JSON
conforming to [source-map.md](source-map.md).

## Downstream — specialist corroboration / investigation (this skill routes to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `cyber-incident-response-coordinator` | An `active_exfiltration` indicator (hard boundary → `blocked`), or any event needing incident command | `case_id` + assessment context + evidence refs + urgency |
| `phishing-and-bec-investigator` | The loss vector is phishing / business-email-compromise | `case_id` + message/indicator evidence |
| `identity-access-reviewer` | Loss via a compromised or over-privileged identity / entitlement abuse | `case_id` + actor + access evidence |
| `cloud-security-posture-reviewer` | Exposure via a cloud misconfiguration / open storage / external sync | `case_id` + cloud-posture evidence |
| `third-party-cyber-risk-reviewer` | Destination is a third-party / vendor connection | `case_id` + third-party context |
| `operational-resilience-reporter` | A resulting confirmed incident needs regulatory/board reporting (only after human adjudication; never initiated here) | the human owner's adjudicated incident |

## Downstream — human decision + privacy/legal

The completed draft package is handed to the **human privacy / incident-response owner**, which
determines whether a reportable data breach occurred, decides any notification obligation, closes
or dispositions the incident, and authorizes any containment or remediation. **Breach
adjudication and regulatory/customer notification are privacy-officer and legal/compliance
decisions** — this skill provides evidence and an exposure estimate to inform them, and never
performs, drafts, or triggers a notification.

## Duplicate-execution prevention

- This skill **does not** investigate a specialist class, determine a breach, decide a
  notification, declare/close an incident, review access, confirm cloud posture, assess
  third-party risk, or take a response action — those belong to the named skills or the human
  IR/privacy-legal owners.
- The specialist / owner consumes the `case_id` + assessment context + evidence refs rather than
  re-assessing.
- A `correlated-duplicate` link is resolved by a human, not auto-merged here; an exact duplicate
  is suppressed under `SUP-DUP-01` and linked to its parent, never closed.
