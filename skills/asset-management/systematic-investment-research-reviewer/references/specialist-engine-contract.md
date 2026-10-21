# Specialist engine challenge contract

`investment-specialist-engine/1.0` implements a supplied-result challenge, not an
engine connector, method certification or legal acceptance. The complete request
hash binds the engine input, object, valuation and knowledge dates, currency,
purpose, engine/method/model versions, expected metric identities/units and source
references. Inventory metric IDs must identify the relevant instrument, scenario,
measure and basis without collapsing distinct financial grains.

A complete result repeats those pins and context, reports the request hash,
versioned source, actual observed date, status and unresolved issues, and supplies
all expected metrics. An independent benchmark repeats the request hash and carries
its own identity, version, method, distinct source, observation date, exact values
and nonnegative tolerances. Decimal strings or integers preserve comparison precision;
binary floating point results are rejected. Changing inputs, versions, units or
coverage invalidates the challenge. Breaches and inherited engine issues withhold
dependent values. Missing, failed or unsupported engines never silently use a
simplified local method.

The acceptance reference and independence designation are supplied evidence. They
cannot authenticate institutional acceptance, benchmark independence or source truth.
The deploying institution must verify licenses, method applicability, controls,
calendars, valuation basis and independent benchmark design. No result confers
execution authority. A financial reviewer must assess whether the chosen metric
inventory is complete for the actual book; matching a supplied inventory cannot
prove that no material instrument or scenario was omitted.
