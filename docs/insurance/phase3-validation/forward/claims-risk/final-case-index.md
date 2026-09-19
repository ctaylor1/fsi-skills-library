# Final selected case outputs

Each row explicitly selects original, unchanged-input repaired, or mapping-only ORSA output. The malformed Boolean case has an error payload, not a native artifact.

| Case | Final selection | Outcome | Output |
|---|---|---|---|
| recovery-multi-interest | original | pass | [Output](/tmp/insurance-p3-forward-claims-risk/claim-recovery-case-reviewer/recovery-multi-interest/original/output.json) |
| recovery-net-exceeds-interest | original | pass | [Output](/tmp/insurance-p3-forward-claims-risk/claim-recovery-case-reviewer/recovery-net-exceeds-interest/original/output.json) |
| recovery-unknown-cost | original | pass | [Output](/tmp/insurance-p3-forward-claims-risk/claim-recovery-case-reviewer/recovery-unknown-cost/original/output.json) |
| recovery-boolean-money | original | expected-rejection | [Output](/tmp/insurance-p3-forward-claims-risk/claim-recovery-case-reviewer/recovery-boolean-money/original/output.json) |
| benefit-daily-cap-waiting | repaired | pass | [Output](/tmp/insurance-p3-forward-claims-risk/disability-care-benefit-reviewer/benefit-daily-cap-waiting/repaired/output.json) |
| benefit-conflicting-medical-evidence | repaired | pass | [Output](/tmp/insurance-p3-forward-claims-risk/disability-care-benefit-reviewer/benefit-conflicting-medical-evidence/repaired/output.json) |
| benefit-unsupported-monthly-method | repaired | pass | [Output](/tmp/insurance-p3-forward-claims-risk/disability-care-benefit-reviewer/benefit-unsupported-monthly-method/repaired/output.json) |
| benefit-unknown-offset-inventory | repaired | pass | [Output](/tmp/insurance-p3-forward-claims-risk/disability-care-benefit-reviewer/benefit-unknown-offset-inventory/repaired/output.json) |
| dispute-contrary-evidence-retained | original | pass | [Output](/tmp/insurance-p3-forward-claims-risk/claimant-dispute-packager/dispute-contrary-evidence-retained/original/output.json) |
| dispute-unanswered-reason-elapsed-date | original | pass | [Output](/tmp/insurance-p3-forward-claims-risk/claimant-dispute-packager/dispute-unanswered-reason-elapsed-date/original/output.json) |
| dispute-carrier-capacity | original | pass | [Output](/tmp/insurance-p3-forward-claims-risk/claimant-dispute-packager/dispute-carrier-capacity/original/output.json) |
| siu-innocent-alternative-custody | original | pass | [Output](/tmp/insurance-p3-forward-claims-risk/insurance-siu-investigation-assistant/siu-innocent-alternative-custody/original/output.json) |
| siu-simultaneous-custody-no-alternative | original | pass | [Output](/tmp/insurance-p3-forward-claims-risk/insurance-siu-investigation-assistant/siu-simultaneous-custody-no-alternative/original/output.json) |
| siu-unsupported-covert-method | original | pass | [Output](/tmp/insurance-p3-forward-claims-risk/insurance-siu-investigation-assistant/siu-unsupported-covert-method/original/output.json) |
| exposure-currency-overlapping-perils | original | pass | [Output](/tmp/insurance-p3-forward-claims-risk/insurance-exposure-aggregation-analyzer/exposure-currency-overlapping-perils/original/output.json) |
| exposure-quality-gap-keeps-known-tiv | original | pass | [Output](/tmp/insurance-p3-forward-claims-risk/insurance-exposure-aggregation-analyzer/exposure-quality-gap-keeps-known-tiv/original/output.json) |
| exposure-duplicate-policy-location | original | pass | [Output](/tmp/insurance-p3-forward-claims-risk/insurance-exposure-aggregation-analyzer/exposure-duplicate-policy-location/original/output.json) |
| cat-joint-weighted-occurrences | original | pass | [Output](/tmp/insurance-p3-forward-claims-risk/catastrophe-scenario-analyzer/cat-joint-weighted-occurrences/original/output.json) |
| cat-incomplete-probability-mass | original | pass | [Output](/tmp/insurance-p3-forward-claims-risk/catastrophe-scenario-analyzer/cat-incomplete-probability-mass/original/output.json) |
| cat-event-rate-above-one | original | pass | [Output](/tmp/insurance-p3-forward-claims-risk/catastrophe-scenario-analyzer/cat-event-rate-above-one/original/output.json) |
| cat-probability-not-event-rate | original | pass | [Output](/tmp/insurance-p3-forward-claims-risk/catastrophe-scenario-analyzer/cat-probability-not-event-rate/original/output.json) |
| orsa-negative-stress-surpluses | mapped-original | pass | [Output](/tmp/insurance-p3-forward-claims-risk/insurance-orsa-packager/orsa-negative-stress-surpluses/mapped-original/output.json) |
| orsa-missing-liquidity-open-board-mismatch | mapped-original | pass | [Output](/tmp/insurance-p3-forward-claims-risk/insurance-orsa-packager/orsa-missing-liquidity-open-board-mismatch/mapped-original/output.json) |
| orsa-baseline-does-not-cover-risk | mapped-original | pass | [Output](/tmp/insurance-p3-forward-claims-risk/insurance-orsa-packager/orsa-baseline-does-not-cover-risk/mapped-original/output.json) |
