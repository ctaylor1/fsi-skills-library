# Adjacent-Skill Handoffs — client-rfq-preparation-brief

Produces a cited RFQ preparation brief (`brief_id`) and stops. It does not quote, commit,
execute, or decide suitability.

## Downstream (route the human/trader to)
| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `pricing-hedging-scenario-calculator` | Pricing/hedging scenarios are needed for the instrument | rfq id + instrument |
| `trade-idea-evidence-packet` | A supporting trade-idea evidence packet is needed | client id + instrument |
| `transaction-cost-estimator` | Expected transaction-cost estimate for the order | instrument + size |

## Upstream (may call this skill)
Sales-trading workflows may request an RFQ prep brief before responding. This skill is interactive
(`aws-fsi-scheduled-agent: no`).

## Duplicate-execution prevention
- This skill only **prepares context and surfaces flags**; it never prices, commits, executes, or
  decides suitability — those belong to the sales trader and compliance.
- Downstream reuses the `brief_id` brief rather than re-assembling.
