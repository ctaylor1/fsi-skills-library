# Source map and freshness

Primary contextual sources reviewed 2026-10-04:

- [CMS Medicare NCCI FAQ Library](https://www.cms.gov/medicare/coding-billing/national-correct-coding-initiative-ncci-edits/medicare-ncci-faq-library): coding edits are separate from medical necessity and prior authorization; private payer adoption varies.
- [CMS NCCI for Medicare](https://www.cms.gov/medicare/coding-billing/national-correct-coding-initiative-ncci-edits): quarterly updates and intervening replacement files require exact file control.
- [AMA CPT licensing frequently asked questions](https://www.ama-assn.org/practice-management/cpt/cpt-licensing-frequently-asked-questions-faqs), updated July 14, 2026: establish permitted content use, including applicable AI terms; public availability does not grant rights.

Case hierarchy: supplied authoritative event/replacement/void ledger and current
file manifest; payer-adopted code/edit profile and licensed-use evidence; executed
contract allowance for exact provider/product/service/code/modifier/version/date;
independently supplied benefit allocation; independent net-payment ledger snapshot.
Every layer requires actual source_ref/version/date/locator. The institution must
confirm provenance and rights. No CPT, UB, production codes, clinical criteria,
external claims access or automatic code retrieval is bundled.

Do not treat Medicare edits as universally adopted by commercial or other programs.
Do not select the latest web file merely because it is newest; actual service date,
retroactive replacement status and payer adoption determine the supplied profile.
A current-file flag needs the custodian's source statement and exact file version.
