from datetime import datetime, timedelta, date, time
from collections import defaultdict
from api.models import (
    ActivityDefinition, ScheduledActivity, SchedulingSummary,
    FullData, TimeOfDay, FrequencyPeriod
)

START_DATE = date(2026, 6, 15)
END_DATE = date(2026, 9, 15)

TIME_RANGES = {
    TimeOfDay.MORNING: (360, 720),
    TimeOfDay.AFTERNOON: (720, 1020),
    TimeOfDay.EVENING: (1020, 1320),
    TimeOfDay.ANY: (360, 1320),
}


def _date_range():
    for i in range((END_DATE - START_DATE).days + 1):
        yield START_DATE + timedelta(days=i)


def _build_day_availability(schedule) -> dict[str, list[tuple[int, int]]]:
    weekly = {wa.day_of_week: (wa.start_time, wa.end_time) for wa in schedule.weekly_availability}
    overrides = {o.date: o for o in getattr(schedule, 'overrides', [])}
    result = {}
    for d in _date_range():
        ds = d.strftime("%Y-%m-%d")
        weekday = d.weekday()
        day_slots = []
        if ds in overrides:
            ov = overrides[ds]
            if not ov.is_blocked:
                for slot in ov.available_slots:
                    sh, sm = map(int, slot["start"].split(":"))
                    eh, em = map(int, slot["end"].split(":"))
                    day_slots.append((sh * 60 + sm, eh * 60 + em))
        elif weekday in weekly:
            ws, we = weekly[weekday]
            sh, sm = map(int, ws.split(":"))
            eh, em = map(int, we.split(":"))
            day_slots.append((sh * 60 + sm, eh * 60 + em))
        result[ds] = day_slots
    return result


def _intersect_slots(
    a: list[tuple[int, int]], b: list[tuple[int, int]]
) -> list[tuple[int, int]]:
    result = []
    i = j = 0
    while i < len(a) and j < len(b):
        s1, e1 = a[i]
        s2, e2 = b[j]
        start = max(s1, s2)
        end = min(e1, e2)
        if start < end:
            result.append((start, end))
        if e1 < e2:
            i += 1
        else:
            j += 1
    return result


def _subtract_intervals(
    intervals: list[tuple[int, int]], busy: list[tuple[int, int]]
) -> list[tuple[int, int]]:
    if not busy:
        return intervals[:]
    result = []
    for s, e in intervals:
        for bs, be in sorted(busy):
            if bs >= e:
                break
            if be <= s:
                continue
            if bs > s:
                result.append((s, bs))
            s = max(s, be)
            if s >= e:
                break
        else:
            if s < e:
                result.append((s, e))
    return result


def _calculate_instances(activity: ActivityDefinition, total_days: int) -> int:
    if activity.frequency_period == FrequencyPeriod.DAY:
        return int(activity.frequency_times * total_days)
    elif activity.frequency_period == FrequencyPeriod.WEEK:
        return max(1, int(round(activity.frequency_times * total_days / 7.0)))
    elif activity.frequency_period == FrequencyPeriod.MONTH:
        return max(1, int(round(activity.frequency_times * total_days / 30.0)))
    elif activity.frequency_period == FrequencyPeriod.QUARTER:
        return max(1, activity.frequency_times)
    return max(1, activity.frequency_times)


def _find_best_slot(
    candidate_slots: list[tuple[int, int]],
    pref_range: tuple[int, int],
    duration_min: int,
) -> tuple[int, int] | None:
    pref_start, pref_end = pref_range
    best_start = None
    best_dist = float("inf")
    pref_mid = (pref_start + pref_end) // 2
    for slot_start, slot_end in candidate_slots:
        if slot_end - slot_start < duration_min:
            continue
        lo = max(slot_start, pref_start)
        hi = min(slot_end, pref_end) - duration_min
        if hi < lo:
            lo = slot_start
            hi = slot_end - duration_min
            if hi <= lo:
                continue
        cand = lo
        if cand < lo:
            cand = lo
        if cand > hi:
            cand = hi
            if cand < lo:
                continue
        dist = abs(cand - pref_mid)
        if dist < best_dist:
            best_dist = dist
            best_start = cand
    if best_start is None:
        return None
    return best_start, best_start + duration_min


def compute_schedule(data: FullData) -> tuple[list[ScheduledActivity], SchedulingSummary]:
    activities = sorted(data.activities, key=lambda a: (a.priority, a.id))

    eq_name_map = {e.resource_id: e.resource_name for e in data.equipment}

    total_days = (END_DATE - START_DATE).days

    # Pre-build client availability
    client_day_avail = _build_day_availability(data.client_schedule)
    for trip in data.client_schedule.travel_plans:
        ts = datetime.strptime(trip.start_date, "%Y-%m-%d").date()
        te = datetime.strptime(trip.end_date, "%Y-%m-%d").date()
        cur = ts
        while cur <= te:
            client_day_avail[cur.strftime("%Y-%m-%d")] = []
            cur += timedelta(days=1)
    for bd_str in data.client_schedule.blocked_dates:
        client_day_avail[bd_str] = []

    # Pre-build resource availability
    resource_day_avail: dict[str, dict[str, list[tuple[int, int]]]] = {}
    for eq in data.equipment:
        resource_day_avail[f"equipment:{eq.resource_id}"] = _build_day_availability(eq)
    for sp in data.specialists:
        resource_day_avail[f"specialist:{sp.resource_id}"] = _build_day_availability(sp)
    for ah in data.allied_health:
        resource_day_avail[f"allied_health:{ah.resource_id}"] = _build_day_availability(ah)

    schedule: list[ScheduledActivity] = []
    total_requested = 0
    total_placed = 0
    constraint_violations = 0
    backup_used = 0
    placed_by_type = defaultdict(int)
    activity_map = {a.id: a for a in data.activities}

    # Track all booked time per day across all activities
    day_booked: dict[str, list[tuple[int, int]]] = defaultdict(list)

    for activity in activities:
        n_instances = _calculate_instances(activity, total_days)
        total_requested += n_instances

        if n_instances == 0:
            continue

        interval_days = max(1, total_days // n_instances)
        pref_range = TIME_RANGES.get(activity.preferred_time_of_day, TIME_RANGES[TimeOfDay.ANY])
        duration = activity.duration_minutes

        required_resources = []
        for eq_id in activity.requires_equipment:
            required_resources.append(f"equipment:{eq_id}")
        if activity.requires_specialist:
            required_resources.append(f"specialist:{activity.requires_specialist}")
        if activity.requires_allied_health:
            required_resources.append(f"allied_health:{activity.requires_allied_health}")

        placed = 0
        current_date = START_DATE

        for _ in range(n_instances * max(1, total_days // max(1, n_instances)) + total_days + 30):
            if placed >= n_instances:
                break
            if current_date > END_DATE:
                current_date = START_DATE

            ds = current_date.strftime("%Y-%m-%d")

            slots = client_day_avail.get(ds, [])
            if not slots:
                current_date += timedelta(days=1)
                continue

            for rkey in required_resources:
                rslots = resource_day_avail.get(rkey, {}).get(ds, [])
                if not rslots:
                    slots = []
                    break
                slots = _intersect_slots(slots, rslots)
                if not slots:
                    break

            if not slots:
                current_date += timedelta(days=1)
                continue

            booked = day_booked.get(ds, [])
            if booked:
                slots = _subtract_intervals(slots, booked)
            if not slots:
                current_date += timedelta(days=1)
                continue

            result = _find_best_slot(slots, pref_range, duration)
            if result is None:
                current_date += timedelta(days=1)
                continue

            start_m, end_m = result
            start_dt = datetime.combine(current_date, time(start_m // 60, start_m % 60))
            end_dt = start_dt + timedelta(minutes=duration)

            equipment_names = [eq_name_map.get(eq, eq) for eq in activity.requires_equipment]

            scheduled = ScheduledActivity(
                activity_id=activity.id,
                activity_name=activity.name,
                activity_type=activity.type,
                priority=activity.priority,
                start_datetime=start_dt.isoformat(),
                end_datetime=end_dt.isoformat(),
                duration_minutes=duration,
                location=activity.location,
                facilitator=activity.facilitator,
                equipment_used=equipment_names,
                prep=activity.prep,
                metrics=activity.metrics,
                details=activity.details,
                notes="",
            )
            schedule.append(scheduled)
            day_booked[ds].append((start_m, end_m))
            placed += 1
            placed_by_type[activity.type.value] += 1
            current_date += timedelta(days=interval_days)

        # Try backup activities for unmet instances
        if placed < n_instances and activity.backup_activity_ids:
            for backup_id in activity.backup_activity_ids:
                if backup_id in activity_map and placed < n_instances:
                    backup_act = activity_map[backup_id]
                    cur = START_DATE
                    for __ in range((n_instances - placed) * total_days):
                        if placed >= n_instances:
                            break
                        b_ds = cur.strftime("%Y-%m-%d")
                        b_slots = client_day_avail.get(b_ds, [])
                        if not b_slots:
                            cur += timedelta(days=1)
                            continue
                        b_booked = day_booked.get(b_ds, [])
                        if b_booked:
                            b_slots = _subtract_intervals(b_slots, b_booked)
                        if not b_slots:
                            cur += timedelta(days=1)
                            continue
                        b_result = _find_best_slot(
                            b_slots, TIME_RANGES[TimeOfDay.ANY], backup_act.duration_minutes
                        )
                        if b_result:
                            b_sm, b_em = b_result
                            b_sdt = datetime.combine(cur, time(b_sm // 60, b_sm % 60))
                            b_edt = b_sdt + timedelta(minutes=backup_act.duration_minutes)
                            b_eq_names = [eq_name_map.get(eq, eq) for eq in backup_act.requires_equipment]

                            schedule.append(ScheduledActivity(
                                activity_id=backup_act.id,
                                activity_name=backup_act.name + " (backup)",
                                activity_type=backup_act.type,
                                priority=backup_act.priority,
                                start_datetime=b_sdt.isoformat(),
                                end_datetime=b_edt.isoformat(),
                                duration_minutes=backup_act.duration_minutes,
                                location=backup_act.location,
                                facilitator=backup_act.facilitator,
                                equipment_used=b_eq_names,
                                prep=backup_act.prep,
                                metrics=backup_act.metrics,
                                details=backup_act.details,
                                notes=f"Substituted for {activity.name}",
                            ))
                            day_booked[b_ds].append((b_sm, b_em))
                            placed += 1
                            backup_used += 1
                            placed_by_type[backup_act.type.value] += 1
                        cur += timedelta(days=1)

        constraint_violations += (n_instances - placed)
        total_placed += placed

    summary = SchedulingSummary(
        total_activities_placed=total_placed,
        total_activities_requested=total_requested,
        constraint_violations=constraint_violations,
        backup_activities_used=backup_used,
        placed_by_type=dict(placed_by_type),
    )

    return schedule, summary
