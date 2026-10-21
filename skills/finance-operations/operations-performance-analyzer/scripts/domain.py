"""UTC window queue conservation and completed-episode operating measures."""
from decimal import Decimal
from design_support import Review, total, ratio, validate_with
METHOD='complete-episode-window-performance-v1'


def evaluate(doc):
    r=Review(doc,METHOD);d=r.data;rows=r.rows('episodes','episode_id',nonempty=False)
    r.fields(d,('population','definition_version','currency','owner'));r.flag(d,'inventory_complete')
    start=r.moment(d,'window_start');end=r.moment(d,'window_end')
    r.need(start is not None and end is not None and start<end,'window','An observed positive [start,end) UTC window is required')
    target=r.num(d,'sla_hours');opening=r.num(d,'reported_opening',integer=True);closing=r.num(d,'reported_closing',integer=True)
    r.need(d.get('sla_clock')=='elapsed-calendar-hours','sla-clock','Only elapsed calendar-hour SLA illustrations supported')
    capacity=r.num(d,'available_labor_hours');worked=r.num(d,'worked_labor_hours')
    if capacity is not None and worked is not None and worked>capacity:r.add('capacity-break','Reported work exceeds supplied available hours',severity='review')
    counts=dict(opening=0,arrivals=0,completed=0,cancelled=0,closing=0);completed=[];ages=[];durations=[];costs=[];minutes=[]
    for row in rows:
        r.need(row.get('population')==d.get('population') and row.get('definition_version')==d.get('definition_version') and row.get('currency')==d.get('currency'),'cohort','Episode population/definition/currency differs',row)
        created=r.moment(row,'created_at');exit_at=r.moment(row,'exited_at') if row.get('exited_at') is not None else None
        state=row.get('exit_kind');r.need(state in {'completed','cancelled',None},'exit-kind','Exit kind completed/cancelled or null for open',row)
        r.need((state is None)==(row.get('exited_at') is None),'exit-state','Exit timestamp and disposition must both exist or both be null',row)
        r.need(created is not None and (exit_at is None or created<=exit_at),'chronology','Exit cannot precede arrival',row)
        completed_in_window = bool(start and end and exit_at and start <= exit_at < end and state == 'completed')
        cost = r.num(row,'cost') if completed_in_window or row.get('cost') is not None else None
        labor = r.num(row,'human_minutes') if completed_in_window or row.get('human_minutes') is not None else None
        if not (start and end and created) or (exit_at and exit_at<created):continue
        counts['opening']+=int(created<start and (exit_at is None or exit_at>=start))
        counts['arrivals']+=int(start<=created<end)
        if exit_at and start<=exit_at<end:
            if state in {'completed','cancelled'}:counts[state]+=1
            if state=='completed':
                elapsed=Decimal(str((exit_at-created).total_seconds()))/Decimal(3600)
                durations.append(elapsed);costs.append(cost);minutes.append(labor);completed.append({'episode_id':row['episode_id'],'elapsed_hours':elapsed,'within_sla':elapsed<=target if target is not None else None})
        if created<end and (exit_at is None or exit_at>=end):
            counts['closing']+=1;ages.append({'episode_id':row['episode_id'],'age_hours':Decimal(str((end-created).total_seconds()))/Decimal(3600)})
    valid=r.clear
    if valid:
        for key,reported in [('opening',opening),('closing',closing)]:
            if reported!=counts[key]:r.add('inventory-break',key+' control differs from episode snapshot',severity='review')
    sorted_times=sorted(durations);n=len(sorted_times)
    p95=sorted_times[(95*n+99)//100-1] if n and valid else None
    conservation=counts['opening']+counts['arrivals']-counts['completed']-counts['cancelled']-counts['closing'] if valid else None
    return r.finish({'queue_counts':counts if valid else None,'queue_conservation_difference':conservation,
                     'snapshot_reconciled':(opening == counts['opening'] and closing == counts['closing']) if valid else None,
                     'opening_control_difference':Decimal(counts['opening'])-opening if valid else None,
                     'closing_control_difference':Decimal(counts['closing'])-closing if valid else None,
                     'completed_episodes':completed if valid else [],'backlog_ages':ages if valid else [],
                     'mean_elapsed_hours':ratio(total(durations),Decimal(n)) if valid else None,'p95_elapsed_hours_nearest_rank':p95,
                     'sla_fraction':ratio(Decimal(sum(x['within_sla'] is True for x in completed)),Decimal(n)) if valid else None,
                     'cost_per_completed':ratio(total(costs),Decimal(n)) if valid else None,'human_minutes_per_completed':ratio(total(minutes),Decimal(n)) if valid else None,
                     'labor_utilization':ratio(worked,capacity) if valid else None,'causal_improvement_established':False,'staffing_change_authorized':False})


def validate(doc):return validate_with(evaluate,doc)
