# Source hierarchy and freshness

ERP invoice, credit-note, supplier-master and payment records are the primary business evidence; bank/PSP lifecycle and statement evidence establish financial outcomes. Supplier account verification, approved remittance mapping and institution payment authority procedures govern enablement. Invoice approval alone is not a payment mandate.

The bundled fixture is synthetic and ERP-neutral. Native document linkage is explicit; actual SAP/Oracle/other ERP schemas, local tax rules and supplier e-invoicing mandates require separately sourced adapters and specialist review.

Record effective/as-of dates, version, owner and review due dates. Current source identity is not authenticated by local scripts. Source dates after the request are rejected; overdue review dates produce gaps. Missing sources produce needs-evidence. Resolve conflicts with source owners instead of selecting the convenient value. Require specialist review before relying on an institution, national or scheme interpretation. Recertification is a package governance date, not a guarantee that mutable rules remain current until then.
