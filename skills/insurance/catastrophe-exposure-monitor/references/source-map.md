# Catastrophe source and model provenance

Policy administration supplies exposure, allocated insured limits, TIV and valuation dates. An event feed supplies the dated hazard footprint. A catastrophe-model provider supplies event- and exposure-bound modeled scenarios. Reference/geocode data and versioned risk-owner configuration explain mapping and thresholds. Claims observations may add context but do not replace modeled scenarios or policy exposure.

The local helper does not provide these external integrations, geocoding, model runs or source authentication. Data-coverage declarations are supplied assertions preserved for review. Empty or absent data is conservatively unknown even if a source declares coverage complete.

The three required source roles each supply `source`, `source_ref`, `version` and timezone-aware `as_of`. The footprint version/reference match `event_feed`; exposure snapshot identity matches `policy_admin.version`; each model row matches the cat-model run reference and version. See [domain-rules.md](domain-rules.md) for all bindings and [insurance-contract.md](insurance-contract.md) for content hashes versus authenticity.

[ASOP 38 Catastrophe Modeling and ASOP 56 Modeling](https://www.actuarialstandardsboard.org/standards-of-practice/) provide professional source anchors for appropriate model use. Qualified domain owners must assess intended use, input quality, limitations and uncertainty. The helper's scenario aggregation and alert thresholds are engineering conventions, not regulatory or ASOP certifications. Source reviewed September 18, 2026.
