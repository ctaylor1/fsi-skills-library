# Domain Rules — subrogation-opportunity-screener

Explainable **recovery signals**, the **referral economics** calculation, and the deterministic
mapping to a **screening band**. Thresholds are configuration (versioned, owned by the recovery /
claims-strategy team), not hard-coded judgments, and are never tuned to an individual claim.
Jurisdiction-specific limitation periods and the firm's recovery standard take precedence over
any default here.

## Recovery signal taxonomy

| Signal | Fires when (default config) | Evidence attached |
| ------ | --------------------------- | ----------------- |
| `third_party_liability_indicated` | `liability.indicated` AND ≥1 responsible party with `liability_pct` ≥ `min_liability_pct` (default 50%) | Qualifying party rows |
| `recovery_above_floor` | `recovery_base` (paid_to_date + recovery_deductible) ≥ `referral_floor` (default 2,500) | Recovery-base breakdown |
| `limitation_window_open` | Diaried `limitation_date` present AND `days_to_limitation` ≥ `limitation_buffer_days` (default 30) | Limitation date + days remaining |
| `supporting_evidence_present` | ≥1 strong evidence item present (`police_report` / `liability_admission` / `expert_report`) | The strong evidence items |
| `recovery_not_waived` | No waiver of subrogation AND `prior_recovery.status == none` (recovery still available) | Waiver flag + prior-recovery status |
| `collectible_responsible_party` | Best responsible party is insured OR has known assets | Party + collectibility flags |
| `positive_expected_recovery` | `net_expected` > `min_expected_net` (default 0) | Recovery economics |

Signals are **additive and independently evidenced**; the output reports each that fired with its
own evidence. There is no opaque composite "recovery score".

## Referral economics (deterministic)

```
recovery_base       = paid_to_date + recovery_deductible
liability_share     = best_qualifying_party.liability_pct / 100        (0 if none qualifies)
collectibility_factor = insured ? collectibility_insured (1.0)
                      : assets_known ? collectibility_assets (0.6)
                      : collectibility_unknown (0.3)
gross_expected      = recovery_base * liability_share * collectibility_factor
net_expected        = gross_expected - recovery_cost_estimate (default 750)
```

`net_expected` is an **estimate for triage economics**, not a promise of recovery.

## Screening band mapping (deterministic, documented)

Let `F` be the set of fired signals and `time_critical = days_to_limitation ≤ limitation_urgent_days`
(default 90; includes past-due). `CORE = {third_party_liability_indicated, recovery_above_floor,
positive_expected_recovery}`.

| Band | Rule |
| ---- | ---- |
| **No-Action** | `recovery_not_waived` did **not** fire (already waived / handled), OR no core/liability signal fired |
| **Review** | `CORE ⊆ F` but a gap remains (evidence, limitation, or collectibility), OR only `third_party_liability_indicated` / `recovery_above_floor` fired |
| **Refer** | `CORE ⊆ F` AND `supporting_evidence_present ∈ F` AND `limitation_window_open ∈ F` |

**Time-critical override:** if the computed band is `No-Action` but `time_critical`, recovery is
available, and liability is indicated, the band is forced up to `Review` so a live limitation
window is never allowed to lapse without a human looking. This mapping is mirrored exactly in
`scripts/calculate_or_transform.py` and `scripts/validate_output.py`.

The band is a **triage suggestion for a licensed recovery specialist**. It is not a subrogation,
liability, or limitation determination and it never triggers a recovery action.

## Hard boundaries (fail closed)

- Never state or imply a third party **is liable / at fault** — describe recorded liability
  indicators and attribute the determination to the human specialist / counsel.
- Never assert a claim **is / is not time-barred** — report the diaried date and days remaining.
- Never **issue/send a demand, file, place a lien, negotiate, release, waive, or close** recovery.
- Never tune floors/factors to the individual claim; use only the versioned config.

## Counter-considerations (always include when band ≠ No-Action)

Comparative/contributory negligence reducing the share; a judgment-proof or under-insured
responsible party; an anti-subrogation rule or made-whole doctrine; jurisdiction-specific
limitation periods (confirm the controlling date with counsel); another party already pursuing
recovery; policy conditions such as a waiver-of-subrogation endorsement. The pack must invite the
specialist to weigh these before pursuing.
