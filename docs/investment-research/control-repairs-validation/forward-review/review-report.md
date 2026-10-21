Independent forward credit skill-use review, 2026-10-20

The declared local review is complete. The authored research draft remains PARTIAL and synthetic. Fresh base-case outputs agree with independent rational-number calculations. The new timing, duplicate-ID and future-period controls behave as documented for the exercised cases. Four semantic evidence limitations remain: economic duplicate adjustments with distinct IDs, unreconciled instrument currency/principal, quote security identity not bound to the issuer, and quote source kind not enforced in Phase 2. The draft explicitly rejects these adverse variants. No repository or historical evidence file was changed by this review.

The review used issuer-credit-researcher v0.1.1 and issuer-credit-surveillance-reviewer v0.3.1 after reading their SKILL.md, native/Phase 2 schemas, methods, controls, evidence standard and public script entry points. Fixture intake examples were read only to understand fields. No fixture or golden output supplied the expected results. Every reviewed input was authored from the separate raw facts, with a new synthetic identity. Full packages were copied under packages/ after source-before/source-after digest comparison; package fixtures are retained only as part of that immutable provenance snapshot. All command executions used those copies, not repository paths.

Both snapshots were stable while copied, their source/copy inventories matched exactly, and every declared package-manifest file hash matched. Provenance records retain each source-before, source-after and copied digest, manifest assertion and check. Snapshot identity is fixed to these local versions even if the repository changes afterward. A package manifest digest establishes supplied-byte identity; it authenticates no source, formula applicability or professional acceptance.

34 fresh cases were exercised: 11 issuer and 23 surveillance. Their public input validators and calculation entry points were invoked even for invalid cases to verify controlled errors. Every computed output was checked with its separately retained original, using public validate_output.py --input ORIGINAL. There were 57 independent numerical/boundary checks and eight additional output-integrity probes; all satisfied their stated expectations. In total, 105 public command invocations were retained, including expected failures. Exit code zero is not financial or professional acceptance. The four semantic limitations are observed accepted inputs, not claims that the software detected them.

Public command pattern, resolved into exact argv arrays in each transcript: bundled Python -B packages/SKILL/scripts/validate_input.py CASE/intake.json; calculate_or_transform.py CASE/intake.json; validate_output.py CASE/native-output.json --input CASE/original.json. Command stdout and stderr were retained independently, including invalid-input errors and rejected tampering. Original and intake files were separate, read back byte equal for all 34 cases; every one of the 27 computed outputs matched an independently calculated canonical hash of its detached original. No external API, web access, messaging or live-model action was used.

Expected issuer arithmetic was independently calculated using Python fractions from the raw facts: reported EBITDA 90, gross leverage 585/90=13/2, net leverage 540/90=6, interest coverage 90/15=6; signed adjustment total 9−3=6; adjusted EBITDA 96, gross leverage 585/96=195/32, net leverage 540/96=45/8, coverage 96/15=32/5; FCF 68−24=44; FFO/debt 60/585=4/39. Native output matched each value within absolute tolerance 1e-12. Base debt legally belongs to the actual supplied subject, so no separate-issuer structural flag is appropriate. Changing only the legal issuer to a subsidiary generated that flag. Unknown seniority remains an explicit issue.

Expected surveillance arithmetic was independently calculated on comparable nine-month periods. Prior/current gross leverage is 5 and 13/2; net leverage 9/2 and 6; interest coverage 55/7 and 6; fixed-charge proxy 45/7 and 22/5; liquidity-to-known-maturity 17/15 and 8/9. Their current-minus-prior changes are 3/2, 3/2, −13/7, −71/35 and −11/45 respectively. The spread change 155 − 100 = 55 bps and current quote age 4 hours meet the supplied 8 hour policy. All three alerts are warranted under the supplied thresholds. Financial comparisons use reported EBITDA; the adjusted EBITDA 96 is not silently substituted into surveillance.

The evidence timing control was tested with a quote exactly eight hours old, one second beyond eight hours, zero-age policy with a four-hour-old quote, zero-age policy with observation/source known exactly at cutoff, timezone-equivalent instants, observation one second after cutoff, observation after economic as-of, equal prior/current instants, source publication one second before the current observation, missing observation time, missing explicit policy and date-only source knowledge. Valid boundaries retained 55 bps. Eligible-but-incomparable cases retained financial metrics and removed the spread result and spread alert. Date-only source knowledge withheld the entire projection under the common precision gate. A source timestamp never substituted for an omitted observed_at.

Issuer cases (0 success;1 controlled validation error; no reconstruction was attempted when calculation rejected):

| Case | Intake / calculation / reconstruction | Observed result |
|---|---|---|
| base | 0 / 0 / 0 | Adjusted EBITDA 96; reported gross leverage 6.5 |
| future-reported-period | 1 / 1 / not run | Controlled input/calculation rejection |
| duplicate-adjustment-id | 1 / 1 / not run | Controlled input/calculation rejection |
| duplicate-economic-adjustment-distinct-id | 0 / 0 / 0 | Adjusted EBITDA 105; reported gross leverage 6.5 |
| zero-ebitda | 0 / 0 / 0 | Adjusted EBITDA 6; reported gross leverage None |
| future-source-one-second | 0 / 0 / 0 | Entire analysis projection withheld; partial |
| confidential-on-public-side | 0 / 0 / 0 | Entire analysis projection withheld; partial |
| unknown-accounting-basis | 1 / 1 / not run | Controlled input/calculation rejection |
| instrument-debt-currency-and-principal-mismatch | 0 / 0 / 0 | Adjusted EBITDA 96; reported gross leverage 6.5 |
| wrong-source-subject | 0 / 0 / 0 | Entire analysis projection withheld; partial |
| different-instrument-issuer | 0 / 0 / 0 | Adjusted EBITDA 96; reported gross leverage 6.5 |

Surveillance cases:

| Case | Intake / calculation / reconstruction | Observed result |
|---|---|---|
| base | 0 / 0 / 0 | Spread change 55; 3 alerts |
| missing-observation-time | 0 / 0 / 0 | Spread change None; 2 alerts |
| missing-freshness-policy | 0 / 0 / 0 | Spread change None; 2 alerts |
| stale-one-second-over-8h | 0 / 0 / 0 | Spread change None; 2 alerts |
| exact-8h-boundary | 0 / 0 / 0 | Spread change 55; 3 alerts |
| zero-policy-with-4h-old-current | 0 / 0 / 0 | Spread change None; 2 alerts |
| zero-policy-observed-and-known-at-cutoff | 0 / 0 / 0 | Spread change 55; 3 alerts |
| observation-one-second-after-cutoff | 0 / 0 / 0 | Spread change None; 2 alerts |
| observation-after-economic-asof | 0 / 0 / 0 | Spread change None; 2 alerts |
| source-version-known-before-observation | 0 / 0 / 0 | Spread change None; 2 alerts |
| date-only-source-knowledge | 0 / 0 / 0 | Entire analysis projection withheld; partial |
| unordered-equal-observation-instants | 0 / 0 / 0 | Spread change None; 2 alerts |
| naive-observation-time | 1 / 1 / not run | Controlled input/calculation rejection |
| negative-freshness-policy | 1 / 1 / not run | Controlled input/calculation rejection |
| timezone-equivalent-instant | 0 / 0 / 0 | Spread change 55; 3 alerts |
| spread-basis-mismatch | 0 / 0 / 0 | Spread change None; 2 alerts |
| incomplete-current-maturity-inventory | 0 / 0 / 0 | Spread change 55; 3 alerts |
| future-reported-financial-period | 1 / 1 / not run | Controlled input/calculation rejection |
| incomparable-financial-period-duration | 1 / 1 / not run | Controlled input/calculation rejection |
| zero-interest-expense | 0 / 0 / 0 | Spread change 55; 2 alerts |
| matching-quotes-unbound-security-identity | 0 / 0 / 0 | Spread change 55; 3 alerts |
| quote-citations-wrong-source-kind | 0 / 0 / 0 | Spread change 55; 3 alerts |
| exact-50bps-alert-boundary | 0 / 0 / 0 | Spread change 50; 3 alerts |

The separate eight-probe integrity set added an unchecked narrative field, upgraded source_truth to verified, embedded a source_input and substituted a changed original, for each skill. Each public output validator returned 1, as expected. The two base-case numerical tampering probes changed reported gross leverage 6.5 to 6.4 and spread 55 to 54; both were rejected. These checks establish full-original reconstruction and detached binding for exercised changes; they do not establish textual entailment, source authenticity, economic reasonableness or domain, legal or institutional acceptance.

Economic duplicate adjustment limitation: the same adjustment A copied under A-SECOND-DOCUMENT passed both public input and output validation, increased adjusted EBITDA to 105 and lowered adjusted net leverage to 540/105≈5.142857. This is distinct from repeated adjustment_id, which was rejected. The schema explicitly leaves distinct IDs describing the same economic item for analyst reconciliation. The research draft therefore rejects the second economic use of A rather than relying on the successful reconstruction.

Instrument reconciliation limitation: changing the single instrument to EUR 700 while leaving consolidated financial debt USD 585 produced unchanged native ratios and no currency/principal reconciliation issue. The original scope does not implement a complete instrument-to-financial debt tie-out. The draft uses only the base USD 585 subject instrument, marks priority unresolved and makes no completeness, legal-priority or absence-of-structural-risk conclusion.

Quote identity/source-type limitations: replacing both quote security IDs with UNRELATED-ISSUER-NOTE passed and retained 55 bps / all 3 alerts, because mutual quote-key equality does not establish the security’s issuer. Reclassifying both quote source records from market_data to financial_statement also passed and retained 55 bps / all 3 alerts. A source subject ID matching the research issuer is insufficient to authenticate the exact instrument mapping or source semantics. The draft rejects both variants. Legacy documentation contains stronger source-type/instrument assertions; this observed result applies specifically to the frozen Phase 2 supplied-input path.

No real accounting framework was supplied. The synthetic envelope uses an explicitly described synthetic convention and carries unresolved issues; that is permissible arithmetic for this exercise, not a workaround for unknown production basis. The literal unknown accounting-basis variant rejected. All ratios remain nine-month denominator calculations, without LTM conversion. The maturity-complete flags, source rights, source classifications, timestamps, source versions and public-side permissions are caller assertions. Seniority, guarantees, enforceability, covenants, source filings, OCF/FFO prior comparables, facility draw conditions, liquidity horizon and a governed institutional profile remain unavailable. No complete issuer credit view, rating, valuation, covenant compliance, DSCR, investment recommendation or source truth is established.

Evidence files: raw-supplied-facts.txt; credit-research-draft.md; independent-issuer-expectations.json; independent-surveillance-expectations.json; issuer-independent-checks.json; surveillance-independent-checks.json; additional-output-integrity-probes.json; retention-readback-checks.json; summary.json; provenance/; packages/; cases/; and evidence-manifest.json. The review builders are rerunnable methodology evidence in this scratch directory; snapshot creation intentionally refuses to replace an existing snapshot. Historical golden evidence was never regenerated.
