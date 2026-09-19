# Handoffs

- `payment-liquidity-and-funding-analyzer`: use scripts/review_corridor.py with separate account openings, obligations, funding transfers, access windows and stress cases. A quote alone does not supply funds.
- `payment-initiation-control-reviewer`: one exact proposed instruction per distinct economic movement and only a supported native jurisdiction adapter. Carry all gaps. BR/IN/CA execution adapters are not implemented by this planner.
- `bank-payment-workflow-designer`: local-method regional review uses scripts/review_regional.py for Pix, UPI or domestic Interac e-Transfer evidence; it never provides a raw network payload.
- `payment-regulatory-applicability-reviewer`: use only the destination's supported regional scope. For unsupported jurisdictions retain the need for local professional review rather than relabeling the request as US/EA/UK.
