# Handoffs

- `wealth-client-discovery-assistant`: unresolved household facts and missing inventory evidence.
- `wealth-onboarding-packager`: normalized scope plus unresolved items for documentation assembly.
- `client-review-preparer`: validated included account values and explicit partial/exclusion flags; adapt to its documented input schema and rerun its validator.
- `investment-risk-profile-reviewer`: liquidity or financial-capacity facts, with sources and exclusions preserved.
- `household-financial-planning-assistant`: only human-reviewed inventory and agreed assumptions; the P1 household planning workflow preserves goal-progress mode.

Pass household ID, engagement, source registry, as-of date, artifact ID, status and unresolved findings with a human-reviewed field mapping. A review-ready artifact is not automatically a valid input to another skill. Stop if the target lacks required facts or approved deployment configuration.
