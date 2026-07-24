# Adjacent-Skill Handoffs — filing-disclosure-change-detector

This skill produces a cited **filing/disclosure change pack** (`job_id` + `finding_id`s) and
stops. It detects and cites *what changed between two versions*. It never decides whether a
change matters (materiality), what it means legally, or what to do about it (investment view)
— those determinations belong to a qualified human and, where a structured deliverable is
wanted, to the adjacent skills below.

## Downstream (route the human/reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `earnings-results-analyzer` | The changes are earnings-related and the user wants a beat/miss, guidance, KPI, and thesis-impact analysis (investment implication) | `job_id` + changed sections/exhibits |
| `research-publication-preparation-assistant` | The changed disclosures should feed a supervisory-reviewed research report skeleton, tables, and a changed-assumption log | `job_id` + findings |
| `earnings-preview-packet-builder` | The user actually wants a forward-looking pre-event brief (consensus, guidance, debate points), not a version diff | issuer + event |
| `company-profile-builder` | The user wants a current company profile / strip page, not a change diff | issuer |
| `due-diligence-packager` | The user wants a full data-room diligence pack (index, issue log, model handoffs), not a two-version comparison | data-room set |
| `market-landscape-researcher` | The "change" is an industry/theme shift rather than one issuer's filing | industry/theme |
| `regulatory-change-impact-analyzer` | The change is to a **law/regulation/standard** (not an issuer filing) and needs obligation-to-control mapping | rule + jurisdiction |

Materiality, legal-significance, and investment-implication **determinations** have no skill
that makes them autonomously — they route to the human review lanes emitted in
`review_routing` (covering analyst, research supervisory analyst, financial-reporting /
disclosure-controls reviewer, legal / contracts reviewer).

## Upstream (may call this skill)

`coverage-meeting-preparer`, `earnings-preview-packet-builder`, and research-workflow skills
may request a change pack as an input. A scheduled monitor is **not** used here (this skill
is interactive, `aws-fsi-scheduled-agent: no`).

## Duplicate-execution prevention

- This skill computes and cites **change findings only**; it must not analyze thesis impact,
  build a profile/model, draft a report, or reach a materiality/legal/investment conclusion
  — those belong to the human and the downstream skills.
- Downstream skills reuse the `job_id` / `finding_id` evidence rather than re-diffing the
  filings.
