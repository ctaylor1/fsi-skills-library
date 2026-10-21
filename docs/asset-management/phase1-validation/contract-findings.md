# Investment contract source-validation finding and repair

Date: 2026-09-20. Scope: the Phase 1 common investment adapter and native handoff acceptance.

## Observed semantic gap

A read-only, in-memory probe used the real synthetic `fund-fact-sheet-builder`
intake fixture and its actual transform and output validator. The original packet
passed native reconstruction. The probe then added this deliberately false test
field to its native result:

```json
{"fabricated_narrative": "The fund guarantees a 50 percent annual return."}
```

The probe recalculated the workflow envelope's `output_hash` and `artifact_hash`.
Before the repair, the results were:

```text
actual native output validator rejects:
  output differs from original-input reconstruction: fabricated_narrative
validate_packet(packet): []
validate_packet(packet, original_request): []
make_handoff using the actual receiver input validator: accepted
validate_handoff: []
invented source narrative: retained in handoff.source_packet.result
```

The source packet's hashes established internal consistency. Neither standalone
packet validation nor handoff acceptance reran the producer's native output
validator. Supplying the original request only checked its digest and metadata;
it did not establish correspondence between the native result and that request.
The receiver input validator could not detect an invented field in the separate
upstream native result.

## Repair

`validate_packet(packet, request=None, *, native_validator=None,
integrity_only=False)` now requires the detached original request and the actual
producer output validator for source-bound acceptance. It reruns the native
validator and checks that freshly returned review warnings match the packet.
Supplying only the request, only the callback, or neither is an error.

Envelope-only checks require the explicit argument `integrity_only=True` and
cannot be combined with source-bound arguments. Such checks can still accept a
self-consistent rehashed fabrication; that is the declared limit of this mode.
`validate_mapping` uses this mode only for mapping structure, never for source
native acceptance.

`make_handoff` and `validate_handoff` require keyword arguments `source_request`
and `source_validator`. Acceptance reruns producer reconstruction before accepting
the receiver's native input. The source request is passed separately and is not
embedded in the handoff. Callers must bind the callback to the actual producer;
the integration CLI owns installed-package identity checks.

All current registered native adapters represent local review calculations.
`method.origin` must therefore be `local-analysis`. `external-analysis` and
`supplied-system-of-record` require a separately declared engine adapter and are
rejected here. Packet `method_metadata_assurance` must remain
`caller-declared-unverified`: supplied method IDs and versions are not checked
against a package-specific method registry.

## Repaired verification

Command: `python3 -B tools/test_asset_management_contract_phase1.py`

Result: **26 tests passed**. The actual-fixture fabrication regression verifies
that the unaltered packet and handoff pass with the real native validators; the
fabricated packet fails source-bound validation, handoff construction, and fresh
handoff validation even after every transport hash and mapping is rebuilt.
Explicit envelope-only validation remains distinguishable and insufficient.
Separate cases cover missing source arguments, source-input substitution, warning
changes, origin relabeling, and forged method assurance.

This repair establishes correspondence to supplied original inputs. It does not
authenticate those inputs, establish source truth, verify rights, approve an
investment decision, or validate an arbitrary caller-supplied callback. Native
calculations remain bounded by their package-specific methods and limitations.

## Embedded-original disclosure probe

A separate integration probe appended the complete original factsheet intake under
`source_input` to an otherwise valid native factsheet. Before the repair, the actual
native validator returned `[]` even with the detached original supplied. This could
reintroduce restricted original facts excluded from the outward result.

The canonical integrity helper now rejects embedded raw originals unconditionally,
requires separately retained original input, and refuses `attach_source(embed=True)`.
The research regression checks injection and missing-detached-source rejection across
all nine research/service native modes; generation remains detached. This is a native
artifact boundary, not a general data-loss-prevention or source-rights certification.
