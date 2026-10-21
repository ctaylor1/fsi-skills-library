# Bounded Phase 1 method

The bundled ruleset is canon-ruleset-2026.07: custodian positions/cash, administrator positions, OMS orders, accounting transactions only. Any other mapping needs an explicit reviewed inline ruleset whose version matches the request. Financial numbers are finite decimal strings. Original records are hashed before batch metadata. Conflicting mapped identifiers and unknown codes are rejected; duplicate source identities block computation. Missing position_basis, quantity_unit or lot_id stays null; downstream adapters must obtain required evidence. Output is JSON, not a bundled CSV exporter.

This is an offline draft evidence method, not a production source of record. Read [schema](schema.md) before mapping inputs. Native output is reconstructed from the separately retained input; independent expected results and professional review remain necessary.
