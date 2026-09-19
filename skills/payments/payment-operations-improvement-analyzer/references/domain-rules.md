# Cohorts and constrained benefits

Completion denominators use completed_at inside [start,end). Backlog is the as-at-end
snapshot, including work created before the window. STP rate uses only eligible completed
cases; unknown effort/eligibility never becomes zero. Rework workload and case incidence
answer different questions. Identical duplicate snapshots collapse; conflicting snapshots
are excluded and the inventory marked incomplete.

Gross avoided minutes = selected cases' (handling + rework) × automation fraction.
Oversight/error minutes = cases × (review minutes + error rate × error minutes).
Capacity hours = max(0, gross − oversight/error)/60, capped at supplied available hours.
Capacity value = capacity hours × loaded cost/hour. Assumed cash savings = min(capacity
value × realization fraction, cash reduction cap). Net economic value subtracts period
technology, implementation and expected error costs from assumed cash savings.

These are transparent scenario conventions, not audited savings or financial advice.
Named case selection, team/entity/currency scope and consistent cost period are mandatory.
Opportunities that share cases are alternative scenarios and cannot be added. Negative
net value remains negative. AI controls are evidence requirements for a bounded pilot;
text completeness does not demonstrate model performance, fairness or deployment approval.
