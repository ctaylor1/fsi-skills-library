# Native evidence schema

Common envelope: schema_version="1.0", request_id, as_of (ISO date), jurisdiction
US|EA|UK, participant, sources [{source_id, reference, as_of, review_due?}],
upstream_issues [{code,message,source_ids?}] and data. Other regions return unsupported.
Source IDs on every native row must resolve to the registry; dated sources in the
future are rejected and overdue source reviews remain gaps. Thresholds and legal
applicability are supplied institutional evidence, not defaults.

Data has three arrays (empty means missing context):

- credentials: unique credential_id, kind network-token|psp-token|wallet|stored-account-reference,
  state active|suspended|deleted|unknown, scope (exact object of nonempty opaque references),
  valid_from/valid_until dates for use, provisioning {identity_review_ref,consent_ref,
  account_binding_ref}, source_ids. A network token requires merchant_ref and
  token_requestor_ref in scope; add device_ref when its actual domain requires it.
- authentications: unique authentication_id, protocol 3ds|fido|bank-app|otp|other,
  result authenticated|failed|unknown, credential_id, valid_from/valid_until dates,
  binding object, source_ids. Authentication validity must cover the analysis date. Populate result
  only from the final provider result. This helper does not validate native 3DS or FIDO.
- requests: unique operation_id, credential_id, action use|provision|update|suspend|delete,
  scope, source_ids. Use requires binding {instruction_id,payer_ref,payee_ref,currency,
  amount}, authentication_id, payment_intent_ref and authentication_applicability_review_ref.
  Binding objects must match exactly (including optional extra fields); amount is
  positive finite decimal. Scope must exactly match the credential's declared domain.
  Lifecycle changes need lifecycle_authority_ref and notification_plan_ref. Update
  also needs update {provider_event_ref,before_reference,after_reference,
  account_linkage_review_ref,consent_status_ref,extends_mandate:false,consent_revoked:false}.
  The update before_reference must match credential_id.

Unknown control references are omitted/null and create gaps. Reference strings are
assertions linked by row source_ids, not trusted review records. Evidence of intent
is independently reviewed by initiation controls; this package never grants authority.
Output operations retain each request ID, scope, source IDs, findings and false
payment/action/SCA determination flags. The envelope retains original input and hash;
output validation recomputes it and checks optional separately supplied input.
