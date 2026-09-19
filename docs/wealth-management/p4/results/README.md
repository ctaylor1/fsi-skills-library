# Retained P4 evidence

Start with the [validation record](../../P4-VALIDATION.md). This folder retains the actual initial comparison and targeted follow-ups, including failures. Model outputs are synthetic test artifacts, not client-ready advice.

| Experiment | Machine-readable result | Full evidence |
| --- | --- | --- |
| Initial 12 paired cases / 24 runs | [initial.json](initial.json) | [wealth-p4-20260917.zip](wealth-p4-20260917.zip) |
| Planning and IPS correction / 4 runs | [planning-followup.json](planning-followup.json) | [wealth-p4-followup-20260917.zip](wealth-p4-followup-20260917.zip) |
| Review-attribution correction / 2 runs | [attribution-followup.json](attribution-followup.json) | [wealth-p4-attribution-20260917.zip](wealth-p4-attribution-20260917.zip) |

[artifact-index.json](artifact-index.json) records archive, snapshot and experiment hashes and per-run token/time observations. Cached input tokens are a subset of reported input tokens; reasoning tokens are a subset of output tokens. Counts are service-reported usage, not prices or additive counts of unique source text. They exclude supervisor/reviewer work and runtime smoke checks.

Each archive has `manifest.json` at its root. It includes frozen skill/case/rubric content, exact prepared conditions, raw `events.jsonl`, final response wrappers and actual model-created reports/structured files. Per-item semantic grades live in `reviews/`, reviewer explanations in `reviewer-evidence/`, and independent trace/source checks in `audits/`. Generated artifacts are hashed separately; the short final messages are not treated as the complete work product.

Validate directly without extracting:

```sh
python tools/wealth_p4_eval.py validate docs/wealth-management/p4/results/wealth-p4-20260917.zip
python tools/wealth_p4_eval.py summarize docs/wealth-management/p4/results/wealth-p4-20260917.zip --format markdown
```

Artifact validation checks retained bytes, chronology, citations and review coverage. It does not decide financial meaning or authenticate source facts. `complete-reviewed` means all expected responses have attributed item-level reviews, not that they passed.

[software-checks/](software-checks) contains the final package/repository test logs and independent lending replay. Those deterministic checks are separate from model quality.
