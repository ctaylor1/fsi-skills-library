# Domain Rules — data-loss-prevention-incident-assistant

Orientation references: NIST SP 800-61 (computer-security incident handling), NIST SP 800-88
(media sanitization / evidence handling context), the firm's data-classification standard and DLP
policy, and applicable breach-notification regimes (e.g., US state breach laws, GLBA safeguards,
HIPAA where PHI is in scope, GDPR/CCPA where configured). The firm's DLP standard and its
**approved suppression rule set + classification config + severity config + output template**
take precedence and are versioned contracts. This skill classifies data and estimates exposure;
it makes no breach determination, decides no notification, and takes no response action.

## Data classification (deterministic taxonomy)

The classification is the **highest-sensitivity** detected data type; the mapping is
configuration, not judgement, and a **recommendation for human confirmation**, not a legal
determination.

| Classification | Detected data types (default) | Regulated? |
| -------------- | ----------------------------- | ---------- |
| `Restricted (PCI/CHD)` | pci, chd, card, pan | Yes |
| `Restricted (PHI)` | phi, health, medical | Yes |
| `Restricted (PII/NPI)` | pii, npi, ssn, account-number, dob | Yes |
| `Confidential (IP/Proprietary)` | source-code, trade-secret, confidential, ip | No |
| `Internal` | internal (or any typed-but-unmapped value) | No |
| `Public` | public | No |

If no data types are present, the event is **unclassified → `needs-data`** (never guessed).
"Regulated" data (any `Restricted` class) leaving the perimeter is the primary signal for human
breach adjudication.

## Severity scoring (deterministic, documented)

Severity is computed from explainable inputs; the mapping is configuration, not judgement, and the
band is a **triage rank for a human reviewer — never a verdict, breach determination, closure, or
response decision**.

| Input | Contribution (default) |
| ----- | ---------------------- |
| Data classification | Restricted (PCI/CHD, PHI, PII/NPI) +4, Confidential (IP) +3, Internal +1, Public 0 |
| Egress completed (data left the perimeter) | +3 |
| Destination trust | external-untrusted +3, personal +2, sanctioned 0, internal 0 |
| Record count | ≥ 10000 +3, ≥ 1000 +2, ≥ 100 +1 |
| Actor privilege | Privileged +2, Service +1, Standard 0 |

Bands: **S1 (Critical)** total ≥ 9 or any `active_exfiltration` indicator; **S2 (High)** 5–8;
**S3 (Moderate)** ≤ 4. Severity is a triage rank, not a determination of loss.

## Approved suppression rules (the ONLY suppressions permitted)

| Rule ID | Condition | Evidence required |
| ------- | --------- | ----------------- |
| `SUP-DUP-01` | Exact duplicate of an open event/case (same actor, DLP rule, window; event ids ⊆ parent) | Parent `case_id` + matched event ids |
| `SUP-SANCTIONED-01` | Destination is on the firm-approved allowlist **and** the data is **not regulated** **and** trust is sanctioned/internal (approved business use) | Destination id + classification |
| `SUP-FP-PATTERN-01` | Matches a documented, approved false-positive pattern for this DLP rule (e.g., synthetic test data, known template) | Pattern id + qualifying event ids |

Any event **not** matching one of these is **not** suppressible by this skill. Suppression is
logged with the rule id and the approved-rule-set version and is subject to reviewer sampling.
Suppression removes known-benign or approved-business **noise**; it is **not** a disposition and
never applies to a genuine incident. An **`active_exfiltration` indicator overrides suppression**
and forces escalation. Regulated data is never suppressed as "approved business use"
(`SUP-SANCTIONED-01` requires non-regulated data by construction).

## Hard boundaries (fail closed)

- No **breach determination**, **notification decision/issuance**, **incident
  disposition/closure**, or communication of one.
- No **containment / response action** — transfer/upload block or quarantine, access revocation,
  account disable/lock, destination block, data/message deletion/recall, credential/token rotation.
- No **suppression** outside the three approved rules above.
- No **system-of-record write** (DLP console / case management / ticketing) and no
  **send/submit/file** of the package or any notification.
- No **identity/access, cloud-posture, third-party, or incident-command conclusion** — route to
  the specialist / IR / privacy-legal owner.
- **`active_exfiltration`** indicator ⇒ `package_status = blocked`, urgent route to incident
  response; this skill performs no containment and makes no breach determination.

## Package status → recommended handling

| Status | Meaning | Recommended handling |
| ------ | ------- | -------------------- |
| `blocked` | Active-exfiltration hard boundary present | Hold routine packaging; hand to incident response and privacy/legal immediately |
| `needs-data` | An event has unresolved enrichment/classification (e.g., no data types) | Return for data; never guess to classify or clear an event |
| `ready-for-review` | All events assessed, no hard boundary | Present the package for privacy/IR review |

The handling is a **recommendation**; the human owner chooses and records the actual breach
determination, notification decision, incident disposition, and any response action.

## Assessment package — required contents

Durable `case_id` per event; batch overview; enrichment (actor/asset/destination/channel) with
citations; deterministic data classification with citations; exposure assessment (egress,
destination trust, magnitude, regulated-data-left-perimeter) with citations; correlation/
deduplication links; deterministic severity with factors; approved-suppression log; evidence
preservation / chain-of-custody references with legal-hold flags and citations; review-ready
assessment context with advisory next steps; advisory escalation routing; an approval ledger
listing every required role with status; an aggregate sources-and-citations list; and the
standing note (draft-only / no-breach-determination / no-containment / no-notification limitation).
