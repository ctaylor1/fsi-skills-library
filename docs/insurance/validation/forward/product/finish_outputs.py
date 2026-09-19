from pathlib import Path
import json,sys,subprocess
ROOT=Path('/tmp/insurance-product-forward-20260918')
PYTHON='/tmp/fsi-p0-venv/bin/python'
texts={
'01-paid-reserving':'''# Reserve Analysis Exhibit — DRAFT

## 1. Cover and valuation basis
Synthetic P&C property segment PROP-PAID; paid-loss basis; valuation 2026-09-18; USD thousands; dataset synthetic-reserve-v1.

## 2. Data sources and reconciliation
The triangle is synthetic triangle-v1: 2024 paid 100 at 12 months and 160 at 24 months; 2025 paid 250 at 12 months. Source: claims-datamart:triangle-v1, synthetic-v1. Paid totals reconcile to 410. No live claim-system reconciliation was supplied. Separate practitioner-context-v1 states case outstanding 80 and reviewer-provided ultimate 400 for 2025 on aligned basis/units; these are contextual inputs outside the native paid-triangle schema.

## 3. Development method and factors
Volume-weighted 12-to-24-month factor = 160 / 100 = 1.6. With the expressly supplied tail 1, CDFs are 1.6 at 12 months and 1.0 at 24 months. Only one observed link ratio supports this example. Source: triangle-v1 and synthetic-reserve-v1.

## 4. Indicated ultimate and reserve measures
| Origin | Paid | CDF | Indicated ultimate | Total unpaid | Source |
| --- | ---: | ---: | ---: | ---: | --- |
| 2024 | 160 | 1.0 | 160 | 0 | triangle-v1 |
| 2025 | 250 | 1.6 | 400 | 150 | triangle-v1 |
| Total | 410 | | 560 | 150 | triangle-v1 |

For 2025, method-indicated total unpaid is 400 - 250 = 150. Total unpaid includes case outstanding; it is not itself IBNR. The separate supplied case outstanding 80 would imply reported incurred 250 + 80 = 330 and a residual 400 - 330 = 70 on the expressly aligned contextual basis (practitioner-context-v1). The native paid-triangle engine does not consume case outstanding or independently validate that reconciliation; the 70 is a transparent supplemental calculation for actuarial review. The supplied ultimate 400 coincides with the mechanical indication; the engine makes no reserve selection.

## 5. Severity, frequency, and large-loss analysis
Severity and frequency are unavailable because no claim counts or exposure were supplied. Large-loss analysis is unavailable because no claim-level large-loss schedule was supplied. The native output's zero count/total and false large-loss flag must not be interpreted as evidence that no large losses exist.

## 6. Uncertainty and sensitivity
The native min/max link-ratio sensitivity is 560 to 560 in aggregate because there is only one observed factor. This zero width supplies no evidence of certainty and is not a statistical interval. The JSON key selected_ultimate represents the method-indicated aggregate 560, not a human reserve selection.

## 7. Assumptions and limitations
The supplied tail 1 assumes no further development after 24 months for this illustration. Origin, valuation, currency and basis alignment must be checked by the reviewing actuary. Aggregate triangles do not establish claim-level large-loss completeness. The paid output table uses total unpaid because the supplied template's generic IBNR heading would mislabel this paid-basis measure.

## 8. Actuarial review and approval
Preparing analyst, qualified actuary and independent peer reviewer sign-offs remain pending. No selection, booking or approval has been performed.
''',
'02-mixed-currency-quotes':'''# Property quote comparison — DRAFT

Both quotes are dated 2026-09-18 and use annual payments for 12-month terms. No extra fees are supplied.

| Item | Quote A | Quote B |
| --- | --- | --- |
| Annual premium and total cost | USD 1,000 | CAD 900 |
| Building limit | USD 100,000 | CAD 100,000 |
| Building deductible | USD 1,000 | CAD 1,000 |
| Source | quote:quote-A-v1@2026-09-18 | quote:quote-B-v1@2026-09-18 |

The currencies differ. Without a sourced FX basis, neither a lowest-cost quote nor a monetary spread can be stated; the native fields are null. The equal printed limit and deductible numbers are in different currencies and do not establish equivalent protection. No exclusions or endorsements were listed in the supplied synthetic records; this does not establish wording equivalence. A useful next comparison requires an agreed, dated FX source and confirmation of coverage definitions, exclusions and endorsements. This is a partial comparison.
''',
'03-earned-loss-ratio':'''# Renewal loss-history review — DRAFT

Earned loss ratio is not evaluable from the supplied records. The inclusive review window is 2023-09-19 through 2026-09-18. All three supplied claims fall within it and sum to USD 300,000 incurred (loss-history-v1/rows1-3; loss dates 2024-01-15, 2025-01-15 and 2026-01-15). The USD 100,000 current annual premium is a current policy-term figure, not earned premium for this historical window. Multiplying it by three would not establish a valid denominator. Supply the actual USD earned-premium ledger total for that exact window before calculating incurred divided by earned premium.

The supplied expiring and proposed annual premiums are both USD 100,000; building limit USD 1,000,000, deductible USD 1,000, TIV USD 1,000,000 and the stated form edition are unchanged (pas-expiring-v1 and pas-proposed-v1, as of 2026-09-18). The native review is partial and suggests Review because all three closed claims meet the configured USD 100,000 large-claim threshold. It does not fire a loss-ratio flag.

Reviewer question: Confirm the status and reserve support of the large claims with the claims function, and obtain historical earned-premium records for the stated window. Development, large-loss treatment and credibility would still matter once a valid ratio is available. The observed premium may reflect exposure, scheduled filings or inflation assumptions in other cases; no such change is attributed here. Form changes may reflect bureau or state requirements, and changes in exposure values may be data corrections; the supplied records do not show these changes.
''',
'04-ceded-illustration':'''# Reinsurance layer illustration — DRAFT

Synthetic treaty ****0001, synthetic cedent, calendar 2026, USD. The supplied and reviewed illustration basis is losses occurring; eligibility is a supplied assumption from eligibility-review-v1/row1, not a decision made here.

- Article 1 states a USD 10m per-occurrence layer above USD 5m for eligible 2026 losses (synthetic-treaty:treaty-v1/article-1@2026-01-01).
- Article 2 states an explicit USD 20m annual aggregate (synthetic-treaty:treaty-v1/article-2@2026-01-01).
- Article 3 states one reinstatement restoring erosion pro rata as to amount at 100% of the USD 2m layer premium with no time adjustment (synthetic-treaty:treaty-v1/article-3@2026-01-01).

For the USD 12m synthetic loss dated 2026-07-01 (synthetic-bordereau:loss-bordereau-v1/row1@2026-07-01), the illustrative layer amount is min(12m - 5m, 10m) = 7m. Illustrative ceded recovery is 7m, cumulative ceded 7m, and remaining aggregate 20m - 7m = 13m. The first erosion restores 7m, and the illustrative reinstatement premium is 7m / 10m × 100% × 2m = 1.4m. These are mechanics under the supplied assumptions; no real-claim recoverability, billing or booking decision is made. No structural gap prevents this bounded illustration; source authenticity and professional acceptance have not been established.
'''}
packages={'01-paid-reserving':'reserving-analysis-assistant','02-mixed-currency-quotes':'premium-quote-comparator','03-earned-loss-ratio':'policy-renewal-reviewer','04-ceded-illustration':'reinsurance-treaty-interpreter'}
for name, narrative in texts.items():
    dest=ROOT/'cases'/name
    out=json.loads((dest/'native-output.json').read_text())
    out['narrative']=narrative
    if 'clauses' in out:
        summaries={'A1':'The stated layer pays an illustrative amount above USD 5,000,000 up to a per-occurrence cap of USD 10,000,000 for supplied eligible losses occurring during 2026.','A2':'The stated calendar-year aggregate limit is USD 20,000,000.','A3':'The stated one reinstatement restores erosion pro rata as to amount at 100 percent of the USD 2,000,000 layer premium, with no time adjustment.'}
        for clause in out['clauses']: clause['plain_summary']=summaries[clause['clause_id']]
    sys.path.insert(0,str(ROOT/packages[name]/'scripts'))
    from insurance_contract import build_artifact
    a=out['artifact']
    out['artifact']=build_artifact(out['calculation_inputs'],out,producer=a['producer'],artifact_type=a['artifact_type'],completeness=a['completeness'],evaluability=a['evaluability'],issues=a['unresolved_issues'])
    sys.path.pop(0)
    (dest/'final-output.json').write_text(json.dumps(out,indent=2)+'\n')
    (dest/'practitioner-output.md').write_text(narrative+'\n'+out.get('disclaimer',out.get('standing_note',''))+'\n')
    args=[PYTHON,str(ROOT/packages[name]/'scripts/validate_output.py'),str(dest/'final-output.json')]
    r=subprocess.run(args,text=True,capture_output=True)
    (dest/'final-output-validation.stdout.txt').write_text(r.stdout)
    (dest/'final-output-validation.stderr.txt').write_text(r.stderr)
    log=json.loads((dest/'run-log.json').read_text());log.append({'stage':'final-output-validation','command':args,'exit_code':r.returncode})
    (dest/'run-log.json').write_text(json.dumps(log,indent=2)+'\n')
    print(name,r.returncode,r.stdout)
