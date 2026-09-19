# Catastrophe monitor controls

R2 read-only calculation, with no bundled external feed, scheduler or queue writer. The output is an observation package; it grants no underwriting, claims, reinsurance, capacity or reserving authority.

- Preserve missing, stale and future-source states; partial evidence cannot produce an all-clear.
- Clear a prior key only when its metric is explicitly measured below threshold on a complete current snapshot. Otherwise retain it as unknown. Never interpret disappearance as resolution.
- Use allocated location limit identities and explicit currency/unit/financial basis before summing.
- Require event, peril, footprint, exposure snapshot, model run/version and aligned named scenarios before producing a full-event modeled range; do not add marginal quantiles.
- Validate monetary values, configured thresholds, metric/threshold ratios, priority bands and dedup counts.
- Preserve source evidence, unresolved issues and the content-bound artifact. Recompute against original input when available.

Regex action-language screens supplement these deterministic checks. They do not authenticate source data or enforce external authorization. Content hashes do not certify the scientific adequacy of a catastrophe model. Read [insurance-contract.md](insurance-contract.md).
