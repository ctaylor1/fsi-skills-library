# Final independent forward review

Used frozen SKILL/schema and fresh synthetic raw facts, without implementation inspection.

Cases passed: 2/3.

Acquisition independent reasoning: purchase195+fees5=200 uses, financed cash120+newdebt80=200. Available opening cash100 is 20 short of the upfront120 leg. Acquiredcash30 arrives after that leg, so positive closing cash10 does not prove the acquisition fundable. Closing debt355 includes old250+new80+assumed25; netdebt345 and shares60. Expected status remains partial until that20 upfront gap is reconciled.

Legitimate update advances the date/cutoff/use snapshot from October18 to October20, uses a new October19 rate source to patch WACC9% to10.5%, and retains the old October17 source without rewriting it. Candidate preparation is explicitly unvalidated until separately run through the real native DCF engine.

Historical-lookahead variant recalculates all supplied hashes consistently, but moves the retained source known-at to October19 while the original snapshot cutoff remains October18. Eligibility now cannot repair that historical impossibility.

These checks cannot authenticate source assertions, independently observe the model store, provide a live concurrency lock or grant model/publication acceptance.

- acquisition-closing-bridge-and-upfront-funding: PASS

- legitimate-snapshot-advance: FAIL

- source-not-known-at-original-cutoff: PASS
