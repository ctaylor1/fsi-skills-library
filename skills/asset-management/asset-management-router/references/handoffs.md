# Native workflow handoffs

A route plan identifies candidates and gaps. It does not hand the original request to
a receiver, run any package, transform data or establish schema compatibility. Use
[the contract](handoff-contract.md) for a separately requested and scoped handoff.

1. Resolve the canonical producer and receiver packages, selected native modes and
   installation inventory. Read their actual input/output contracts. A planned
   capability cannot receive an executable native handoff merely because it has a name.
2. Retain the producer's detached original native input and validate its calculated
   output against that input. Do not substitute a recomputed narrative or omit upstream
   source gaps. Keep subject identity, economic date and knowledge cutoff explicit.
3. Prepare the workflow request with context, source-use assertions, identity/date
   pointers, method identity/version/origin, native input and unresolved issues. Invoke
   `scripts/build_artifact.py --request REQUEST --native-output OUTPUT
   --producer-package PACKAGE --method METHOD`. This calls the producer's validator;
   an envelope does not relax that contract.
4. Prepare a real receiver-native request. Document each exact source-pointer copy or
   additional sourced input, bind the complete target request and source artifact
   hashes, record review basis and explicit context changes. Computed conversions need
   separately validated methods. Do not invent a holding, return, cash flow, legal term
   or missing classification to make the receiver accept the request.
5. Build with `scripts/validate_handoff.py BUNDLE --target-package RECEIVER --source-package PRODUCER --source-request ORIGINAL_REQUEST --build`,
   where BUNDLE contains `source_packet`, `target_request`, `mapping` and
   `requested_output`. Validate the resulting packet with the same command without
   `--build`. Both the producer's source-bound output validator and receiver's native input validator are executed. Keep ORIGINAL_REQUEST detached; envelope hashes alone cannot establish native validity.
6. Preserve all inherited issues even when the receiver accepts its native input.
   Report what was validated, what remains unavailable and which practitioner owns
   follow-up. Receiver acceptance is not investment approval or execution authority.

For attribution to commentary, use actual reconciled supplied figures and preserve
method limitations; performance measurement is not created by narrative assembly.
For exposures to mandate review, reconcile NAV, preserve UNKNOWN dimensions and map
rule applicability explicitly; do not silently drop positions. For liquidity to cash
forecasting, distinguish liquidation assumptions from settled, usable cash and known
dated flows. These are mapping requirements, not preimplemented adapters.

All workflow packets are internal-review evidence. External investor reports, RFP
submissions or other audience projections require their own authorized review. No
sender/receiver path, reviewer string, successful hash check or stored packet grants
permission to trade, deliver, post, file or close an unresolved issue.
