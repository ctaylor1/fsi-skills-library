# Native input and output

The common `investment-foundation/1.0` request uses request_id, object_id, as_of, knowledge_cutoff, currency, internal-review audience, versioned sources and optional unresolved_issues. Every row below carries a registered source_ref. No mode/extension selector exists. Collections require unique identities and at most 10,000 rows; recalls and committed_funding may be explicitly empty.

| Collection | Required fields beyond ID/source_ref |
|---|---|
| agreements / agreement_id | version, owner, legal_document_locator, jurisdiction, transaction_type (`repo-cash-borrower` or `securities-lender-noncash`), day_count (`ACT/360` or `ACT/365F`), accrual_method=`simple`, rate_basis (`cash-principal` for repo; `loaned-market-value` for lending), margin_convention (`haircut` or `initial-margin`), margin_value, acceptance_status, effective_from/to |
| trades / trade_id | agreement_id, counterparty_id, security_id, currency, observed_on=as_of, accrual_start/end (end=as_of), maturity_date>=as_of, positive outstanding_quantity, positive cash_principal or loaned_market_value as specified by agreement, signed annual_rate, basis_constant_over_interval=true, rate_effective_from/to covering start through maturity |
| collateral_inventory / collateral_id | custody_account_id, source_position_id, security_id, currency, collateral_type=`security`, nonnegative market_value, observed_on=as_of, explicit eligible_agreement_ids list |
| collateral_allocations / allocation_id | known collateral_id/trade_id unique pair; nonnegative allocated_market_value |
| recalls / recall_id | securities-lender trade_id, requested_on actual date, due_date>=request, positive requested_quantity, nonnegative returned_quantity<=requested, actual returned_on when nonzero; otherwise returned_on null |
| committed_funding / funding_id | available_date>=as_of, nonnegative amount, currency, status=`supplied-committed` to count as projected receipt |

Top-level available_funding_cash is nonnegative, funding_source_ref is registered and funding_as_of equals review date. Haircut is in [0,1); initial margin is >=1. Signed rates are finite decimal fractions, never percentages such as 3.6 for 3.6%. Use exact decimal strings where precision matters. Sources, known dates and audience restrictions are checked.

Outputs retain per-trade requirements, eligible collateral, exact sufficiency, day-count accruals, projected maturity repayments, open recalls and a dated funding path. Bad structure/unsupported method/currency or temporal contradictions fail validation; agreement, coverage and funding gaps remain needs-review drafts. legal_netting_recognized and execution_authorized remain false. Validate against the detached original input.


The custody-account/source-position pair must be unique across collateral IDs. A renamed inventory row cannot create more available collateral. Constant accrual basis is a supplied historical assertion and future projection assumption, not something inferred from the review-date mark; changing basis requires a different approved method.
