# Fresh forward-run usability finding: undocumented exact valuation date

Original frozen request uses an account value dated 2026-09-17 for review on 2026-09-18. All value inputs, request identity and profile fields are present. Native input/calculation/output checks all exit 0, but `results.value_scenario` is null. Finding `scenario_not_evaluable` groups current value, scope, profile and deductions in one message and never identifies the actual date mismatch.

The cause is the exact equality comparison at `scripts/domain.py:128`: `day(c['value_date']) == day(doc['as_of'])`. `references/source-map.md` documents `value_date` without this restriction; `SKILL.md` says 'current value date'. `references/domain-rules.md` does not explain same-day freshness. A normal previous-close snapshot thus cannot produce the requested illustrative value bridge, and the generic finding provides no clear remediation.

Severity: documentation/usability issue, not an observed arithmetic or boundary violation. Recommend documenting the exact same-day requirement and returning an explicit valuation date finding naming snapshot and review dates. Any change to freshness tolerance should require a supplied reviewed policy; do not silently treat previous-day values as current.

Reproduction: run the three native commands recorded in `commands.json` on `input.json`. The original raw-source packet remains unchanged. A distinct `same-day-source.md` supplement and `same-day-input.json` variant result in the correct $41,250 proceeds and $130,000 account balance, while missing assignee consent persists. No production authority or professional acceptance is implied.
