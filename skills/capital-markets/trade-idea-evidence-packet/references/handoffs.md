# Adjacent-Skill Handoffs — trade-idea-evidence-packet

Produces a cited internal trade-idea evidence packet (`packet_id`) and stops. It does not
recommend to any client, distribute, or decide suitability.

## Downstream (route the human/analyst to)
| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `client-rfq-preparation-brief` | Client-specific RFQ context is needed | client id + instrument |
| `pricing-hedging-scenario-calculator` | Pricing/hedging scenarios for the idea are needed | instrument + params |
| `communications-compliance-reviewer` | Communications-surveillance review before any distribution | packet id |

## Upstream (may call this skill)
Sales/trading and desk-research workflows may request an idea evidence packet for internal review.
This skill is interactive (`aws-fsi-scheduled-agent: no`).

## Duplicate-execution prevention
- This skill only **packages internal evidence and surfaces flags**; it never recommends to a
  client, distributes, or decides suitability — those belong to the human and compliance.
- Downstream reuses the `packet_id` packet rather than re-assembling.
