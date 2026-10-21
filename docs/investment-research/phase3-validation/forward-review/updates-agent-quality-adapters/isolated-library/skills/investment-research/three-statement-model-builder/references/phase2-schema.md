# Phase2 native schema and method

Phase2 mode uses schema_version ir-phase2/1.0 plus the full common evidence context, explicit issuer_type nonfinancial-corporate, accounting_basis, consolidation_scope, fiscal_calendar calendar and model_input containing the original native schema with company_id matching the issuer. forecast_rows are generated from every integrated year: calendar dates, EBIT, depreciation, capex, change in operating noncash working capital, tax rate, NOPAT and UFCF. No flat-margin reconstruction is used. Funding gaps remain unresolved and no new financing engine is supplied.

The paired examples are evals/files/phase2-input.json and phase2-valid.json. The executable field contract is scripts/phase2_domain.py. Run the standard input, calculation and detached-original output commands on these files. Top-level evidence references gate every calculation; no source authentication or approval follows from a passing arithmetic check.
