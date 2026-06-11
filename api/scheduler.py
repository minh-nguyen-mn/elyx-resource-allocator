from datetime import datetime, timedelta, date, time
from collections import defaultdict
from api.models import (
    ActivityDefinition, ActivityType, ScheduledActivity, SchedulingSummary,
    SkippedActivity, FullData, TimeOfDay, FrequencyPeriod
)

START_DATE = date(2026, 6, 15)
END_DATE = date(2026, 9, 15)

TIME_RANGES = {
    TimeOfDay.MORNING: (360, 720),
    TimeOfDay.AFTERNOON: (720, 1020),
    TimeOfDay.EVENING: (1020, 1320),
    TimeOfDay.ANY: (360, 1320),
}

BUFFER_MINUTES = 5


def _date_range():
    for i in range((END_DATE - START_DATE).days + 1):
        yield START_DATE + timedelta(days=i)


def _build_day_availability(schedule) -> dict[str, list[tuple[int, int]]]:
    weekly: dict[int, list[tuple[int, int]]] = {}
    for wa in schedule.weekly_availability:
        sh, sm = map(int, wa.start_time.split(":"))
        eh, em = map(int, wa.end_time.split(":"))
        weekly.setdefault(wa.day_of_week, []).append((sh * 60 + sm, eh * 60 + em))
    overrides = {o.date: o for o in getattr(schedule, 'overrides', [])}
    result = {}
    for d in _date_range():
        ds = d.strftime("%Y-%m-%d")
        weekday = d.weekday()
        if ds in overrides:
            ov = overrides[ds]
            if not ov.is_blocked:
                day_slots = []
                for slot in ov.available_slots:
                    sh, sm = map(int, slot["start"].split(":"))
                    eh, em = map(int, slot["end"].split(":"))
                    day_slots.append((sh * 60 + sm, eh * 60 + em))
                result[ds] = day_slots
            else:
                result[ds] = []
        elif weekday in weekly:
            result[ds] = weekly[weekday]
        else:
            result[ds] = []
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
                if s < e:
                    result.append((s, e))
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
    pref_mid = (pref_start + pref_end) // 2
    best_start = None
    best_dist = float("inf")

    for slot_start, slot_end in candidate_slots:
        if slot_end - slot_start < duration_min:
            continue

        lo = max(slot_start, pref_start)
        hi = min(slot_end, pref_end) - duration_min

        if hi >= lo:
            cand = min(max(lo, pref_mid - duration_min // 2), hi)
            dist = abs(cand - pref_mid) * 0.2
        else:
            lo = slot_start
            hi = slot_end - duration_min
            if hi <= lo:
                continue
            if slot_end <= pref_start:
                edge_dist = pref_start - slot_end
            elif slot_start >= pref_end:
                edge_dist = slot_start - pref_end
            else:
                edge_dist = 0
            cand = min(max(lo, pref_mid - duration_min // 2), hi)
            dist = abs(cand - pref_mid) * 0.2 + edge_dist * 10 + 100000

        if dist < best_dist:
            best_dist = dist
            best_start = cand

    if best_start is None:
        return None
    return best_start, best_start + duration_min


def _refine_time_preference(name: str, pref_range: tuple[int, int]) -> tuple[int, int]:
    name_lower = name.lower()
    pref_start, pref_end = pref_range

    if 'consultation' in name_lower or 'checkup' in name_lower or 'check-up' in name_lower:
        return pref_range

    if any(kw in name_lower for kw in ['sleep hygiene', 'sleep routine', 'wind down', 'wind-down', 'bedtime', 'bed time']):
        return (pref_end - 120, pref_end)


    if any(kw in name_lower for kw in ['dinner', 'supper']):
        return (pref_start + 60, pref_start + 150)

    if any(kw in name_lower for kw in ['mindful eating', 'mindful']):
        return (pref_start + 105, pref_start + 165)

    if any(kw in name_lower for kw in ['morning', 'breakfast', 'sunrise']):
        return (pref_start, pref_start + 120)

    if 'sunset' in name_lower:
        return (pref_end - 60, pref_end)

    if 'retinoid' in name_lower or name_lower.startswith('cbd') or 'cbd recovery' in name_lower:
        return (pref_start + 150, pref_end)

    return pref_range


def _infer_preferred_day_offset(name: str) -> int | None:
    name_lower = name.lower()
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    for i, day in enumerate(days):
        if day in name_lower:
            return i
    if 'weekend' in name_lower:
        return 5
    return None


def compute_schedule(data: FullData) -> tuple[list[ScheduledActivity], SchedulingSummary]:
    activities = sorted(data.activities, key=lambda a: (a.priority, a.id))

    eq_name_map = {e.resource_id: e.resource_name for e in data.equipment}

    total_days = (END_DATE - START_DATE).days + 1

    client_day_avail = _build_day_availability(data.client_schedule)

    travel_dates = set()
    for trip in data.client_schedule.travel_plans:
        ts = datetime.strptime(trip.start_date, "%Y-%m-%d").date()
        te = datetime.strptime(trip.end_date, "%Y-%m-%d").date()
        cur = ts
        while cur <= te:
            ds = cur.strftime("%Y-%m-%d")
            travel_dates.add(ds)
            client_day_avail[ds] = [(360, 540), (1080, 1320)]
            cur += timedelta(days=1)

    for bd_str in data.client_schedule.blocked_dates:
        if bd_str not in travel_dates:
            client_day_avail[bd_str] = []

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
    skipped_activities: dict[str, SkippedActivity] = {}
    activity_map = {a.id: a for a in data.activities}

    day_booked: dict[str, list[tuple[int, int]]] = defaultdict(list)
    day_event_count: dict[str, int] = defaultdict(int)
    day_short_cursor: dict[str, int] = {}
    activity_date_used: set[tuple[str, str]] = set()
    SHORT_DURATION = 5

    for activity in activities:
        n_instances = _calculate_instances(activity, total_days)
        total_requested += n_instances

        if n_instances == 0:
            continue

        interval_days = max(1, total_days // n_instances)
        pref_range = _refine_time_preference(activity.name, TIME_RANGES.get(activity.preferred_time_of_day, TIME_RANGES[TimeOfDay.ANY]))
        duration = activity.duration_minutes

        requires_fixed_location = bool(
            activity.requires_equipment
            or activity.requires_specialist
            or activity.requires_allied_health
        )

        required_resources = []
        for eq_id in activity.requires_equipment:
            required_resources.append(f"equipment:{eq_id}")
        if activity.requires_specialist:
            required_resources.append(f"specialist:{activity.requires_specialist}")
        if activity.requires_allied_health:
            required_resources.append(f"allied_health:{activity.requires_allied_health}")

        placed = 0
        is_daily = activity.frequency_period == FrequencyPeriod.DAY
        is_weekly = activity.frequency_period == FrequencyPeriod.WEEK
        act_index = int(activity.id.split("-")[1])
        days_offset = ((act_index - 1) * 13) % 84
        pref_day = None
        if is_daily:
            current_date = START_DATE
        elif is_weekly:
            current_date = START_DATE
            pref_day = _infer_preferred_day_offset(activity.name)
            if pref_day is not None:
                days_ahead = (pref_day - current_date.weekday()) % 7
                current_date += timedelta(days=days_ahead)
            else:
                small_offset = (act_index * 3 + act_index // 7) % 7
                current_date += timedelta(days=small_offset)
        else:
            current_date = START_DATE + timedelta(days=days_offset)
            pref_day = _infer_preferred_day_offset(activity.name)
            if pref_day is not None:
                days_ahead = (pref_day - current_date.weekday()) % 7
                if days_ahead > 0:
                    current_date += timedelta(days=days_ahead)
        base_date = current_date

        def _advance_date():
            nonlocal current_date, pref_day_fails
            if pref_day is not None and pref_day_fails < 5:
                pref_day_fails += 1
                da = (pref_day - current_date.weekday()) % 7
                current_date += timedelta(days=da if da > 0 else 7)
            else:
                current_date += timedelta(days=1)

        wrap_count = 0
        pref_day_fails = 0
        for _ in range(n_instances * max(1, total_days // max(1, n_instances)) + total_days + 60):
            if placed >= n_instances:
                break
            if current_date > END_DATE:
                wrap_count += 1
                if wrap_count > 14:
                    break
                if pref_day is not None:
                    da = (pref_day - base_date.weekday()) % 7
                    base_date += timedelta(days=da if da > 0 else 7)
                else:
                    base_date += timedelta(days=1)
                current_date = base_date
                pref_day_fails = 0
                continue

            ds = current_date.strftime("%Y-%m-%d")

            if (activity.id, ds) in activity_date_used:
                _advance_date()
                continue

            slots = client_day_avail.get(ds, [])
            if not slots:
                _advance_date()
                continue

            if (not activity.is_all_day
                    and current_date.weekday() < 5):
                slots = _subtract_intervals(slots, [(480, 1080)])
                if not slots:
                    _advance_date()
                    continue

            # Reserve midday slot from all non-is_all_day activities so Lunch Break gets priority
            if not activity.is_all_day and 'lunch break' not in activity.name.lower():
                slots = _subtract_intervals(slots, [(690, 750)])

            # Lunch Break: always carve out a midday slot regardless of day
            if 'lunch break' in activity.name.lower():
                slots = [(s, e) for s, e in slots if e <= 480 or s >= 1080]
                slots.append((690, 750))
                slots.sort()

            if ds in travel_dates and requires_fixed_location:
                _advance_date()
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
                _advance_date()
                continue

            is_short = duration <= SHORT_DURATION
            stacked = False
            pref_start, pref_end = pref_range

            if is_short and ds in day_short_cursor:
                cursor = day_short_cursor[ds]
                avail_slots = client_day_avail.get(ds, [])
                bkd = day_booked.get(ds, [])
                if bkd:
                    avail_slots = _subtract_intervals(avail_slots, bkd)
                if (cursor >= pref_start and cursor + duration <= pref_end
                        and any(s <= cursor and cursor + duration <= e for s, e in avail_slots)):
                    start_m = cursor
                    end_m = cursor + duration
                    day_short_cursor[ds] = end_m
                    stacked = True

            if not stacked:
                booked = day_booked.get(ds, [])
                if booked:
                    slots = _subtract_intervals(slots, booked)
                if not slots:
                    _advance_date()
                    continue

                result = _find_best_slot(slots, pref_range, duration)
                if result is None:
                    _advance_date()
                    continue

                start_m, end_m = result

            start_dt = datetime.combine(current_date, time(start_m // 60, start_m % 60))
            end_dt = start_dt + timedelta(minutes=duration)

            equipment_names = [eq_name_map.get(eq, eq) for eq in activity.requires_equipment]

            sched = ScheduledActivity(
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
                is_all_day=activity.is_all_day,
            )
            schedule.append(sched)

            buf = 0 if duration <= 2 else BUFFER_MINUTES
            book_start = max(0, start_m - buf)
            book_end = min(1440, end_m + buf)
            day_booked[ds].append((book_start, book_end))
            if not stacked:
                if is_short:
                    day_short_cursor[ds] = end_m
                day_event_count[ds] += 1
            activity_date_used.add((activity.id, ds))
            placed += 1
            placed_by_type[activity.type.value] += 1
            current_date += timedelta(days=interval_days)

        if placed < n_instances and activity.backup_activity_ids:
            for backup_id in activity.backup_activity_ids:
                if backup_id in activity_map and placed < n_instances:
                    backup_act = activity_map[backup_id]
                    cur = START_DATE + timedelta(days=days_offset)
                    for __ in range((n_instances - placed) * total_days):
                        if placed >= n_instances:
                            break
                        b_ds = cur.strftime("%Y-%m-%d")

                        if (backup_id, b_ds) in activity_date_used:
                            cur += timedelta(days=1)
                            continue

                        b_duration = backup_act.duration_minutes
                        b_is_short = b_duration <= SHORT_DURATION

                        b_slots = client_day_avail.get(b_ds, [])
                        if not b_slots:
                            cur += timedelta(days=1)
                            continue

                        if (not backup_act.is_all_day
                                and cur.weekday() < 5):
                            b_slots = _subtract_intervals(b_slots, [(480, 1080)])
                            if not b_slots:
                                cur += timedelta(days=1)
                                continue

                        if not backup_act.is_all_day and 'lunch break' not in backup_act.name.lower():
                            b_slots = _subtract_intervals(b_slots, [(690, 750)])

                        if 'lunch break' in backup_act.name.lower():
                            b_slots = [(s, e) for s, e in b_slots if e <= 480 or s >= 1080]
                            b_slots.append((690, 750))
                            b_slots.sort()

                        b_reqs_fixed = bool(
                            backup_act.requires_equipment
                            or backup_act.requires_specialist
                            or backup_act.requires_allied_health
                        )
                        if b_ds in travel_dates and b_reqs_fixed:
                            cur += timedelta(days=1)
                            continue

                        b_stacked = False
                        b_sm = 0
                        b_em = 0

                        if b_is_short and b_ds in day_short_cursor:
                            cursor = day_short_cursor[b_ds]
                            b_avail = client_day_avail.get(b_ds, [])
                            b_bkd = day_booked.get(b_ds, [])
                            if b_bkd:
                                b_avail = _subtract_intervals(b_avail, b_bkd)
                            if (cursor + b_duration <= 1440
                                    and any(s <= cursor and cursor + b_duration <= e for s, e in b_avail)):
                                b_sm = cursor
                                b_em = cursor + b_duration
                                day_short_cursor[b_ds] = b_em
                                b_stacked = True

                        if not b_stacked:
                            b_booked = day_booked.get(b_ds, [])
                            if b_booked:
                                b_slots = _subtract_intervals(b_slots, b_booked)
                            if not b_slots:
                                cur += timedelta(days=1)
                                continue

                            b_result = _find_best_slot(
                                b_slots, _refine_time_preference(backup_act.name, TIME_RANGES[TimeOfDay.ANY]), b_duration
                            )
                            if not b_result:
                                cur += timedelta(days=1)
                                continue
                            b_sm, b_em = b_result

                        b_sdt = datetime.combine(cur, time(b_sm // 60, b_sm % 60))
                        b_edt = b_sdt + timedelta(minutes=b_duration)
                        b_eq_names = [eq_name_map.get(eq, eq) for eq in backup_act.requires_equipment]

                        schedule.append(ScheduledActivity(
                            activity_id=backup_act.id,
                            activity_name=backup_act.name + " (backup)",
                            activity_type=backup_act.type,
                            priority=backup_act.priority,
                            start_datetime=b_sdt.isoformat(),
                            end_datetime=b_edt.isoformat(),
                            duration_minutes=b_duration,
                            location=backup_act.location,
                            facilitator=backup_act.facilitator,
                            equipment_used=b_eq_names,
                            prep=backup_act.prep,
                            metrics=backup_act.metrics,
                            details=backup_act.details,
                            notes=f"Substituted for {activity.name}",
                            is_all_day=backup_act.is_all_day,
                        ))

                        b_buf = 0 if b_duration <= 2 else BUFFER_MINUTES
                        b_book_start = max(0, b_sm - b_buf)
                        b_book_end = min(1440, b_em + b_buf)
                        day_booked[b_ds].append((b_book_start, b_book_end))
                        if not b_stacked:
                            if b_is_short:
                                day_short_cursor[b_ds] = b_em
                            day_event_count[b_ds] += 1
                        activity_date_used.add((backup_id, b_ds))
                        placed += 1
                        backup_used += 1
                        placed_by_type[backup_act.type.value] += 1
                        cur += timedelta(days=1)

        missed = n_instances - placed
        constraint_violations += missed
        if missed > 0 and activity.skip_adjustments:
            if activity.id not in skipped_activities:
                skipped_activities[activity.id] = SkippedActivity(
                    activity_id=activity.id,
                    activity_name=activity.name,
                    activity_type=activity.type,
                    priority=activity.priority,
                    instances_missed=0,
                    skip_adjustment=activity.skip_adjustments,
                )
            skipped_activities[activity.id].instances_missed += missed

        total_placed += placed

    summary = SchedulingSummary(
        total_activities_placed=total_placed,
        total_activities_requested=total_requested,
        constraint_violations=constraint_violations,
        backup_activities_used=backup_used,
        placed_by_type=dict(placed_by_type),
        skipped_activities=sorted(
            skipped_activities.values(),
            key=lambda s: s.priority,
        ),
    )

    return schedule, summary
