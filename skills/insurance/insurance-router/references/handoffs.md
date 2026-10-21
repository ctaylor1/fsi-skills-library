# Handoff contracts

The router selects work; it does not execute a pipeline or translate arbitrary
native schemas. Read the receiver's source map and run its actual input validator.
An envelope, upstream review flag or producer-side validation cannot replace this.

For claims, keep receipt identifiers, policy/version, claim identifiers, product,
coverage and cause of loss distinct. A normalized `auto_physical_damage` label is
not automatically the target's `auto_collision` or liability classification. Use
an explicit, reviewed mapping from supplied facts and preserve unmapped values.
Missing required receiver data produces a blocked handoff, not invented defaults.

For financial work, preserve currency, units, paid/reported/case reserve basis,
gross/ceded/net and valuation/as-of periods. A paid triangle cannot become a
reported triangle merely by changing a label. Policy and treaty contract versions
and legally operative periods must accompany evidence.

Use the shared make_handoff function to retain upstream artifact/issue lineage.
Use `python scripts/validate_handoff.py PACKET.json --skills-root /trusted/skills`
for a local installed target. The packet must contain the actual target's native
input in `target_input`; the wrapper calls that package's validate_input script.
This checks syntax/declared semantics, not professional adequacy, source trust,
access permission or execution approval. Review identity mapping and minimum
necessary disclosure before handing off records between represented parties.

No automatic adapters or connectors are claimed. The Phase 1 integration tests
exercise a supplied native claims-triage record with retained intake evidence;
unsupported transformations remain explicitly manual and receiver-validated.

Later-phase capability names in the route registry are planning records. They are
not callable dependencies. Existing cross-domain destinations likewise need a
deployment inventory and native-schema validation before use.

## Phase 4 portable review handoffs

New design/measurement packages use workflow-evidence/1.0. See
[the portable contract](workflow-contract.md). The handoff validator dispatches
that format and the unchanged legacy insurance format separately. New receivers
may retain validated legacy insurance artifacts; legacy receivers need an explicit
field adapter and companion evidence packet. Neither routing nor a valid common
envelope proves source-to-field fidelity or source access.
