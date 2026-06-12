import pytest
from datetime import date, timedelta
from api.data_generator import generate_all_data, generate_activities, START_DATE, END_DATE
from api.scheduler import compute_schedule
from api.models import ActivityType, FrequencyPeriod, FullData


def test_activities_count():
    activities = generate_activities()
    assert len(activities) >= 100, f"Expected 100+ activities, got {len(activities)}"
    assert len(activities) >= 105, f"Expected 105+ activities, got {len(activities)}"


def test_activities_have_valid_types():
    activities = generate_activities()
    valid_types = {t.value for t in ActivityType}
    for a in activities:
        assert a.type.value in valid_types, f"Activity {a.id} has invalid type {a.type}"


def test_activities_have_valid_frequencies():
    activities = generate_activities()
    valid_periods = {p.value for p in FrequencyPeriod}
    for a in activities:
        assert a.frequency_period.value in valid_periods, f"Activity {a.id} has invalid period {a.frequency_period}"
        assert a.frequency_times >= 0, f"Activity {a.id} has frequency_times < 0"
        assert 1 <= a.priority <= 100, f"Activity {a.id} has priority out of range: {a.priority}"
        assert 0 <= a.duration_minutes <= 240, f"Activity {a.id} has duration out of range: {a.duration_minutes}"


def test_backup_activity_ids_are_valid():
    activities = generate_activities()
    all_ids = {a.id for a in activities}
    for a in activities:
        for bid in a.backup_activity_ids:
            assert bid in all_ids, (
                f"Activity {a.id} references non-existent backup {bid}"
            )
        assert a.id not in a.backup_activity_ids, (
            f"Activity {a.id} references itself as backup"
        )


def test_backup_activities_exist():
    activities = generate_activities()
    activities_with_backups = [a for a in activities if a.backup_activity_ids]
    assert len(activities_with_backups) > 0, "No activities have backup_activity_ids assigned"
    pct = len(activities_with_backups) / len(activities) * 100
    assert pct >= 30, f"Only {pct:.1f}% of activities have backups, expected >= 30%"


def test_resource_references_exist():
    data = generate_all_data()
    eq_ids = {e.resource_id for e in data.equipment}
    sp_ids = {s.resource_id for s in data.specialists}
    ah_ids = {a.resource_id for a in data.allied_health}

    for a in data.activities:
        for eq in a.requires_equipment:
            assert eq in eq_ids, f"Activity {a.id} requires unknown equipment {eq}"
        if a.requires_specialist:
            assert a.requires_specialist in sp_ids, (
                f"Activity {a.id} requires unknown specialist {a.requires_specialist}"
            )
        if a.requires_allied_health:
            assert a.requires_allied_health in ah_ids, (
                f"Activity {a.id} requires unknown allied health {a.requires_allied_health}"
            )


def test_travel_plans_block_dates():
    data = generate_all_data()
    total_blocked = 0
    for trip in data.client_schedule.travel_plans:
        start = date.fromisoformat(trip.start_date)
        end = date.fromisoformat(trip.end_date)
        days = (end - start).days + 1
        total_blocked += days
        assert start >= START_DATE, f"Travel {trip.id} starts before planning horizon"
        assert end <= END_DATE, f"Travel {trip.id} ends after planning horizon"
    assert total_blocked > 0, "No travel days configured"
    assert data.client_schedule.blocked_dates, "No blocked dates recorded"


def test_scheduler_runs():
    data = generate_all_data()
    schedule, summary = compute_schedule(data)
    assert schedule is not None
    assert summary is not None


def test_scheduler_places_most_activities():
    data = generate_all_data()
    schedule, summary = compute_schedule(data)
    rate = summary.total_activities_placed / max(summary.total_activities_requested, 1) * 100
    assert rate >= 70, f"Placement rate {rate:.1f}% is unexpectedly low"


def test_scheduler_no_double_booking():
    data = generate_all_data()
    schedule, summary = compute_schedule(data)
    sorted_sched = sorted(schedule, key=lambda s: (s.start_datetime, s.end_datetime))
    for i in range(len(sorted_sched) - 1):
        a = sorted_sched[i]
        b = sorted_sched[i + 1]
        if a.start_datetime[:10] != b.start_datetime[:10]:
            continue
        a_start = a.start_datetime
        a_end = a.end_datetime
        b_start = b.start_datetime
        b_end = b.end_datetime
        both_short = a.duration_minutes <= 5 and b.duration_minutes <= 5
        if both_short:
            continue
        assert a_end <= b_start or b_end <= a_start, (
            f"Double-booked: {a.activity_name} ({a_start}-{a_end}) "
            f"and {b.activity_name} ({b_start}-{b_end})"
        )


def test_scheduler_skip_adjustments_recorded():
    data = generate_all_data()
    schedule, summary = compute_schedule(data)
    if summary.constraint_violations > 0:
        assert len(summary.skipped_activities) > 0, (
            f"Found {summary.constraint_violations} violations but no skipped_activities recorded"
        )
        for sa in summary.skipped_activities:
            assert sa.skip_adjustment, f"Skipped activity {sa.activity_name} has empty skip_adjustment"
            assert sa.instances_missed > 0, f"Skipped activity {sa.activity_name} has 0 instances_missed"


def test_scheduler_respects_client_availability():
    data = generate_all_data()
    schedule, summary = compute_schedule(data)
    client_avail = {}
    for d in range((END_DATE - START_DATE).days + 1):
        cd = START_DATE + timedelta(days=d)
        ds = cd.strftime("%Y-%m-%d")
        weekday = cd.weekday()
        slots = []
        for wa in data.client_schedule.weekly_availability:
            if wa.day_of_week == weekday:
                sh, sm = map(int, wa.start_time.split(":"))
                eh, em = map(int, wa.end_time.split(":"))
                slots.append((sh * 60 + sm, eh * 60 + em))
        if slots:
            client_avail[ds] = slots

    for s in schedule:
        dt = date.fromisoformat(s.start_datetime[:10])
        ds = dt.strftime("%Y-%m-%d")
        act = next((a for a in data.activities if a.id == s.activity_id), None)
        if ds in data.client_schedule.blocked_dates and act:
            requires_fixed = bool(act.requires_fixed_location or not act.remote_possible or act.requires_equipment or act.requires_specialist or act.requires_allied_health)
            if requires_fixed:
                pytest.fail(f"Activity {s.activity_name} requires fixed location but placed on travel date {ds}")
        if ds in client_avail:
            s_start = s.start_datetime
            sh, sm = int(s_start[11:13]), int(s_start[14:16])
            start_m = sh * 60 + sm
            end_m = start_m + s.duration_minutes
            within = any(avail_start <= start_m and end_m <= avail_end for avail_start, avail_end in client_avail[ds])
            if not within:
                travel_override_dates = set()
                for trip in data.client_schedule.travel_plans:
                    ts = date.fromisoformat(trip.start_date)
                    te = date.fromisoformat(trip.end_date)
                    cur = ts
                    while cur <= te:
                        travel_override_dates.add(cur.strftime("%Y-%m-%d"))
                        cur += timedelta(days=1)
                if ds not in travel_override_dates:
                    pytest.fail(f"Activity {s.activity_name} at {s_start} is outside client availability on {ds}")
