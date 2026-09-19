# Handoffs — investment risk profile

| Route | When | Artifact |
| --- | --- | --- |
| `investment-policy-statement-builder` | Profile facts support an IPS or change | All dimensions, sources and unresolved findings; no inferred rating |
| `portfolio-proposal-comparator` | Supplied proposals need comparison against established profile | Profile artifact and independently documented constraints |
| `investment-recommendation-evidence-reviewer` | A recommendation needs its profile evidence reviewed | artifact_id/input_hash, dimension records and sources |
| `household-financial-planning-assistant` | Goal funding or current planning assumptions need analysis | Goal/horizon and sourced financial inputs |
| `senior-investor-protection-screener` | Capacity/exploitation concerns warrant protection review | Minimal concern evidence; no medical diagnosis or account action |
| Advisor / qualified planning professional | Reconcile contradictions or select the appropriate rating under approved process | Complete profile with unresolved findings |

Reuse the same profile artifact/version in downstream workflows; do not regenerate a questionnaire
or silently change its answer. Downstream skills cannot interpret review-ready as suitability,
professional approval or permission to place a trade or send a client communication.
