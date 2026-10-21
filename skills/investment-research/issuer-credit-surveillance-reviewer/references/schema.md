# Current schema and legacy migration — 0.4.1

The only live request contract is explicit `schema_version: ir-phase2/1.0`, detailed in [the analytical schema](phase2-schema.md). Results use `ir-analysis/2.0`. All public input, calculation and output entrypoints reject legacy requests/packets with `legacy surveillance migration required`. Missing or unknown schema labels never select a fallback implementation.

## Reviewed migration

Prepare a new original with the common research context and explicit comparable reported `prior` and `current` financial periods. Source each figure and preserve currency, units, accounting basis and consolidation scope. Do not silently convert or infer the legacy period strings, sources, accessibility flags, thresholds or approval records.

For a spread comparison supply the actual prior/current observation timestamps, selected structured market evidence, precise registered source versions/blocks, dated security-to-issuer/currency mapping, and institution-supplied current-age policy. Source publication time is not observation time. Adding the current schema label to a legacy request is insufficient. Missing optional comparison evidence may yield a faithful partial in an otherwise valid new request; it does not authorize an invented mapping or timestamp.

Validate the new request, calculate a new output and reconstruct it with the exact separately retained original. There is no automatic adapter or compatibility bypass. Historical `surveillance_request_example.json` and `surveillance_packet_*.json` are retained as rejection inputs; they are not current success fixtures. Current success/selftest fixtures are `phase2_input.json` and `phase2_valid.json`.

Earlier phase and repair evidence remains historical. Reproduce it only with the exact frozen historical producer/validator snapshot and original input; the current package does not certify those legacy packets. A historical successful result cannot establish eligibility for current research use.
