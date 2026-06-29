# Elyx Resource Allocator — Technical Documentation

## Table of Contents

1. [Problem Statement](#1-problem-statement)
2. [Architecture Overview](#2-architecture-overview)
3. [Data Model](#3-data-model)
4. [Data Generation](#4-data-generation)
5. [Scheduling Algorithms](#5-scheduling-algorithms)
6. [API Layer](#6-api-layer)
7. [Frontend](#7-frontend)
8. [Edge Cases &amp; Handling](#8-edge-cases--handling)
9. [Testing Strategy](#9-testing-strategy)
10. [Performance &amp; Metrics](#10-performance--metrics)
11. [Deployment](#11-deployment)

---

## 1. Problem Statement

**Domain:** Personal health optimisation — a client follows a detailed wellness protocol involving fitness, nutrition, medication, therapy, and consultation activities across a 3-month horizon (Jun 15 – Sep 15, 2026).

**Core Challenge:** Given:
- ~105+ activity definitions (each with priority, frequency, duration, resource requirements)
- 16 equipment items, 8 specialists, 5 allied health professionals (each with their own weekly schedules and random day-off overrides)
- Client availability (weekly windows + 3 travel plans covering 18 blocked days)

…produce a **non-overlapping calendar schedule** that maximises placement rate, respects all temporal and resource constraints, and is realistic enough for daily use.

**Secondary objectives:**
- Time-of-day preferences (morning/afternoon/evening/any) must be respected
- Weekly activities should land on their logical day-of-week
- Short activities should stack (batch together) for efficiency
- Activities must be spread evenly, not crammed
- When primary placement fails, backup activities should substitute
- No double-booking across any combination of activities

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Browser (FullCalendar.js)               │
│         public/index.html  ←→  REST API  ←→  FastAPI        │
└─────────────────────────────────────────────────────────────┘
                          ▲
                          │ HTTP (JSON)
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Backend (api/index.py)             │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌───────────────┐ │
│  │ Data Gen.    │───▶│ Scheduler    │───▶│ JSON Export   │ │
│  │ (determinis- │    │ (greedy      │    │ & API serve   │ │
│  │  tic, seed=42)│    │  constraint) │    │               │ │
│  └──────────────┘    └──────────────┘    └───────────────┘ │
│         │                    │                               │
│         ▼                    ▼                               │
│  ┌──────────────┐    ┌──────────────┐                       │
│  │ Pydantic     │    │ Pydantic     │                       │
│  │ models       │    │ models       │                       │
│  │ (models.py)  │    │ (models.py)  │                       │
│  └──────────────┘    └──────────────┘                       │
└─────────────────────────────────────────────────────────────┘
```

**Data flow:**
1. Server starts → `generate_all_data()` runs (deterministic, seed=42)
2. `compute_schedule(data)` runs immediately, producing placement + summary
3. Both are cached in-memory as module globals
4. API endpoints serve the cached data
5. Frontend fetches `/api/schedule` on load and renders via FullCalendar

**Key design decisions:**
- **No database** — data is generated fresh on each deployment (idempotent due to fixed seed)
- **Serverless-friendly** — stateless after startup, single compute burst, then read-only
- **Pydantic v2** — validation at every boundary (generation → model → API response)

---

## 3. Data Model (`api/models.py`)

### Enums

| Enum | Values |
|---|---|
| `ActivityType` | `fitness`, `food`, `medication`, `therapy`, `consultation` |
| `TimeOfDay` | `morning`, `afternoon`, `evening`, `any` |
| `FrequencyPeriod` | `day`, `week`, `month`, `quarter` |

### Core Entity: `ActivityDefinition`

| Field | Type | Constraints |
|---|---|---|
| `id` | `str` | Pattern `ACT-NNN` |
| `name` | `str` | Human-readable |
| `type` | `ActivityType` | Enum |
| `priority` | `int` | 1–100 (lower = higher priority) |
| `frequency_times` | `int` | ≥1 |
| `frequency_period` | `FrequencyPeriod` | How often |
| `duration_minutes` | `int` | 0–240 |
| `preferred_time_of_day` | `TimeOfDay` | Slot preference |
| `requires_equipment` | `list[str]` | Equipment IDs needed |
| `requires_specialist` | `Optional[str]` | Single specialist ID |
| `requires_allied_health` | `Optional[str]` | Single allied health ID |
| `requires_fixed_location` | `bool` | Can't do while traveling |
| `remote_possible` | `bool` | Can be done anywhere |
| `is_all_day` | `bool` | Display as day-spanning event |
| `backup_activity_ids` | `list[str]` | Fallback activity IDs |
| `skip_adjustments` | `str` | What to do if skipped |
| `prep` | `list[str]` | Preparation steps |
| `metrics` | `list[str]` | Trackable metrics |

### Resource Schedules

All three resource types inherit from `ResourceSchedule`:
- **`Equipment`** — has `location` field
- **`Specialist`** — has `specialty` + `remote_available`
- **`AlliedHealth`** — has `profession` + `remote_available`

Each has:
- `weekly_availability: list[WeeklyAvailability]` — day-of-week + time ranges
- `overrides: list[AvailabilityOverride]` — date-specific overrides (blocked or custom slots)

### Client Schedule: `ClientSchedule`

| Field | Type | Purpose |
|---|---|---|
| `weekly_availability` | `list[WeeklyAvailability]` | Default weekly windows |
| `travel_plans` | `list[TravelPlan]` | Trips with destination + dates |
| `blocked_dates` | `list[str]` | All dates client is unavailable |

### Output Models

| Model | Fields |
|---|---|
| `ScheduledActivity` | Placed instance: time, location, resources used, notes |
| `SkippedActivity` | Missed instance: which dates, how many, skip adjustment |
| `SchedulingSummary` | Aggregated stats: placed, requested, violations, backups, by-type breakdown |
| `ScheduleResponse` | `schedule + summary + data` (full response for frontend) |

---

## 4. Data Generation (`api/data_generator.py`)

### Strategy

All generation is **deterministic** (`random.seed(42)` and `random.Random(42)`). The generator produces **exactly the same data every run**.

### Activities

**105+ activities** are hand-defined across types:

| Type | Count | Examples |
|---|---|---|
| Fitness | ~32 | Morning Jog, Yoga Flow, HIIT Circuit, Swimming Laps, Tennis Practice |
| Food | ~18 | Breakfast Prep, Dinner Prep, Morning Smoothie, Meal Prep Sunday |
| Medication | 15 | Vitamin D, Omega-3, Probiotic, Blood Pressure Med, Retinoid, Sunscreen |
| Therapy | 15 | Sauna, Ice Bath, Red Light Therapy, Acupuncture, Float Tank |
| Consultation | ~20 | Personal Training, Nutritionist, Mental Health Therapy, Sleep Consultation |

Plus **3 all-day reminders** (Hydration, No Caffeine After 2pm, Screen Wind-Down) and **Lunch Break**.

**Post-processing** (lines 998–1035):
1. Backup activity IDs are assigned via name-based cross-referencing (e.g., Morning Jog → Recovery Walk)
2. Frequency adjustments for realistic density: most daily activities converted to weekly, many weekly converted to monthly. Final density target: ~100 sessions/week.
3. Redundant activities removed (ACT-036, ACT-045, ACT-049, ACT-108)

### Resources

- **16 equipment items** — each with 6-day weekly availability + random 5–12 blocked days + 2% maintenance-day partial availability
- **8 specialists** — Mon–Fri full day + Sat half-day + Sun half-day; 4% weekday / 15% weekend random absences; 30% of absences replaced with partial-day availability
- **5 allied health** — same pattern as specialists; 3% weekday / 15% weekend absences
- **Client schedule** — Mon–Fri 06:00–21:30, Sat 08:00–22:00, Sun 08:00–21:00
- **3 travel plans** — New York (Jul 10–14), Aspen (Aug 5–12), San Diego (Sep 1–5) = 18 blocked days total

### Travel Day Handling

During travel: client availability is overridden to morning (06:00–09:00) and evening (18:00–22:00) slots. Only activities that don't require fixed location can be placed. Travel days override weekly availability entirely.

---

## 5. Scheduling Algorithms (`api/scheduler.py`)

### 5.1 Overall Structure

The scheduler is a **greedy priority-based** algorithm:

```python
activities = sorted(data.activities, key=lambda a: (a.priority, a.id))
for activity in activities:
    # distribute instances evenly across horizon
    # for each instance, find the best available slot
    # book it, track busy intervals
```

**Complexity:** O(A × N × D) where A = activity count, N = instances per activity, D = days scanned per instance. In practice ~105 × ~14 × ~93 ≈ 137K iterations.

### 5.2 Availability Building

**`_build_day_availability(schedule) → dict[str, list[tuple[int, int]]]`**

Converts a resource's `weekly_availability + overrides` into a per-date map of minute-interval tuples:

1. For each day in the horizon:
   - If an override exists: use its slots or mark as blocked (empty list)
   - Else if weekday has weekly availability: use those windows
   - Else: empty list

**`_intersect_slots(a, b)`**

Two-pointer intersection of sorted interval lists. Both inputs are `[(start_min, end_min), ...]`. Used to find time windows where **all** required resources are simultaneously available.

Example:
```
A = [(360, 720), (780, 1080)]   # client availability
B = [(420, 660)]                 # equipment availability
result = [(420, 660)]            # intersection
```

**`_subtract_intervals(intervals, busy)`**

Subtracts busy intervals from available intervals. Used to prevent double-booking. Iterates through busy intervals sorted by start time, carving out chunks from available intervals.

```
available = [(360, 1080)]
busy = [(480, 540), (690, 750)]
result = [(360, 480), (540, 690), (750, 1080)]
```

### 5.3 Instance Calculation

**`_calculate_instances(activity, total_days) → int`**

| Period | Formula |
|---|---|
| Day | `freq_times × total_days` |
| Week | `round(freq_times × total_days / 7)` |
| Month | `round(freq_times × total_days / 30)` |
| Quarter | `freq_times` (flat) |

Total requested for current config: **~1,445 instances** across all activities.

### 5.4 Slot Selection

**`_find_best_slot(candidate_slots, pref_range, duration_min) → (start_min, end_min) | None`**

Scoring system with tiered penalty:

1. **Perfect fit** (slot overlaps preferred range): Score = `distance_from_mid × 0.2`
   - Picks the slot where the activity center is closest to the preferred time range midpoint
2. **Near fit** (slot is near preferred range): Score = `distance_from_mid × 0.2 + edge_distance × 10`
3. **Far fit** (slot is far from preferred range): Score = `distance_from_mid × 0.2 + edge_distance × 10 + 100000`

The massive `+100000` penalty means out-of-range slots are used only as absolute last resort. This ensures time-of-day preferences are strongly respected.

### 5.5 Time Preference Refinement

**`_refine_time_preference(name, pref_range) → tuple[int, int]`**

Activity-name-based override of the generic morning/afternoon/evening time ranges:

| Keyword | Adjustment |
|---|---|
| "sleep hygiene", "wind down", "bedtime" | Last 2 hours of evening |
| "dinner", "supper" | First 90 min of evening (shifted by 60 min) |
| "mindful eating" | 105–165 min into the range |
| "morning", "breakfast", "sunrise" | First 2 hours of morning |
| "sunset" | Last hour of evening |
| "retinoid", "cbd" | Last 90 min of evening |
| "consultation", "checkup" | No refinement |

### 5.6 Day-of-Week Alignment

**`_infer_preferred_day_offset(name) → int | None`**

Scans activity name for weekday names. If found, schedules weekly activities on that day. "weekend" maps to Saturday (5).

Examples:
- "Meal Prep Sunday" → Sunday
- "Weekend Trail Hike" → Saturday

### 5.7 Even Distribution (Spread)

Activities are spread across the horizon using:
- **interval_days = max(1, total_days // n_instances)** — even spacing
- **days_offset** — computed from activity index: `((act_index - 1) * 13) % 84`
  - This distributes different activities' start dates across the 84-day window, preventing all activities from starting on day 1
- **Wrap-around logic** — if current_date exceeds END_DATE, resets to base_date + 1 week and tries again (up to 14 wraps)

### 5.8 Work-Hour Blocking & Lunch Reservation

- **9am–5pm (540–1080 min)** blocked on weekdays for all non-all-day activities
- **11:30am–12:30pm (690–750 min)** reserved as midday lunch slot
  - All normal activities: subtract this interval from available slots
  - Lunch Break: carve out this interval specifically
- These represent implicit work/school constraints

### 5.9 Short Activity Stacking

Activities with `duration ≤ 5 minutes` (mostly medications at 2 min) use a **cursor-based stacking** mechanism:

1. After placing a short activity, its end time is recorded in `day_short_cursor[date]`
2. The next short activity on the same day checks if the cursor + its duration fits within the remaining available window
3. If yes, it's stacked directly after (no buffer), without re-running `_find_best_slot`
4. This allows 10–15 short activities to occupy the same 30-minute block

Stacking is **per-day** and resets for each new day. Stacked activities are excluded from double-booking checks in tests.

### 5.10 Backup Activity Fallback

When `placed < n_instances` and `backup_activity_ids` is non-empty:

1. Iterate through backup activities in order
2. For each backup, scan forward from START_DATE trying to place remaining instances
3. Backup receives less strict slot selection (uses `TimeOfDay.ANY` as preference)
4. Backup activities are marked with `"(backup)"` suffix and `notes = "Substituted for {primary}"`
5. Backup placement follows the same constraint intersection logic

### 5.11 Skipped Activity Tracking

After all instances are processed:

1. Compute `missed = n_instances - placed`
2. If `missed > 0` and `skip_adjustments` is non-empty:
   - Compute `intended_dates` using `_compute_intended_dates()`
   - Subtract actually used dates → `missed_dates`
   - Record in `SkippedActivity` with the skip adjustment text

### 5.12 Constraint Intersection (per day, per activity)

For each activity instance on a given date:

```
slots = client_day_avail[date]
if weekday and not all_day:
    slots -= [(480, 1080)]          # work hours
if not all_day and not lunch_break:
    slots -= [(690, 750)]           # lunch reservation
if lunch_break:
    slots = [(690, 750)]            # forced lunch slot
if travel_date and requires_fixed_location:
    skip
for each required resource:
    resource_slots = resource_day_avail[key][date]
    if empty: skip date
    slots = intersect(slots, resource_slots)
    if empty: break
if booked slots exist:
    slots = subtract(slots, booked)
```

---

## 6. API Layer (`api/index.py`)

### Endpoints

| Method | Path | Response | Purpose |
|---|---|---|---|
| GET | `/api/activities` | `list[ActivityDefinition]` | All activity definitions |
| GET | `/api/equipment` | `list[Equipment]` | Equipment schedules |
| GET | `/api/specialists` | `list[Specialist]` | Specialist schedules |
| GET | `/api/allied_health` | `list[AlliedHealth]` | Allied health schedules |
| GET | `/api/client_schedule` | `ClientSchedule` | Client availability |
| GET | `/api/schedule` | `ScheduleResponse` | Full schedule + summary + data |
| GET | `/api/summary` | `SchedulingSummary` | Placement statistics only |
| GET | `/api/data` | `FullData` | All generated input data |
| GET | `/` | `index.html` | Calendar frontend |

### Startup Behaviour

```python
DATA = generate_all_data()                          # deterministic generation
schedule, summary = compute_schedule(DATA)          # compute once
schedule.sort(key=lambda s: (s.start_datetime, s.priority))
```

The schedule is computed **once at import time** and cached. All endpoints read from these module globals. This means:
- First request may have a few seconds of cold-start latency (generation + scheduling)
- All subsequent requests are O(1) / O(n) reads

### CORS

Wide-open CORS (`allow_origins=["*"]`) for development convenience.

---

## 7. Frontend (`public/index.html`)

### Technology

- **FullCalendar 6.1.15** (CDN) — dayGridMonth, timeGridWeek, timeGridDay views
- **Vanilla JavaScript** — no framework
- **CSS custom properties** — theming via `:root` variables
- **No build step** — served directly as static files

### Features

1. **Stats bar** — Placed / Requested / Violations / Backup counts
2. **Sidebar filters** — Type, Priority, Location, Facilitator, Frequency, Duration
3. **Activity list** — Expandable rows with full details (prep, metrics, resources)
4. **Skipped activities panel** — Lists all missed instances with skip adjustments
5. **Travel/Constraints panel** — Shows travel dates on calendar
6. **Type breakdown** — Pie-style bar chart of placement by type
7. **Event color coding:**
   - Fitness = green
   - Food = brown
   - Medication = red
   - Therapy = purple
   - Consultation = navy
   - Travel = gold (displayed as background events)
8. **Modal popups** — Click event → full details; Click travel → trip info; Click skipped → adjust text
9. **Responsive** — 3-column desktop → 2-column tablet → stacked mobile

### Filtering

Filters are **cumulative** (AND logic). Each filter type has "Select All" / "Deselect All" toggles. Filter state is cleared on calendar rebuild.

---

## 8. Edge Cases &amp; Handling

| Edge Case | Handling Strategy | Location |
|---|---|---|
| **Activity with 0 instances** | `_calculate_instances` returns 0; `continue` immediately | `scheduler.py:274` |
| **All-day activities** | Skip work-hour blocking; skip lunch reservation; displayed as day-spanning | `scheduler.py:361-366` |
| **Travel during planning horizon** | Client availability overridden to morning+evening only; fixed-location activities blocked | `scheduler.py:232-241` |
| **Resource unavailable on a date** | Intersection returns empty; date skipped | `scheduler.py:382-388` |
| **Self-referencing backup** | Banned by test (`test_backup_activity_ids_are_valid`) | `test_scheduler.py:39-41` |
| **Circular backup chains** | Not explicitly prevented; backup scan uses sequential dates, no recursion | — |
| **No available slot in preferred range** | `_find_best_slot` penalises out-of-range 100000× but still accepts them if nothing else fits | `scheduler.py:133-145` |
| **Hitting END_DATE with remaining instances** | Wrap-around logic: reset to base_date + 1 week, try again (up to 14 wraps) | `scheduler.py:337-348` |
| **Short activity stacking overflow** | If cursor + duration exceeds available window, falls back to normal `_find_best_slot` | `scheduler.py:399-410` |
| **Lunch Break forced placement** | Carves out (690, 750) as only available slot, regardless of day type | `scheduler.py:373-376` |
| **Preference day not available** | `_advance_date` tries same weekday up to 5 times, then advances daily | `scheduler.py:323-330` |
| **Duration shorter than buffer** | Activities ≤ 2 min get zero buffer (0 min) | `scheduler.py:451` |
| **Blocked date overlaps with travel** | Deduplicated: only travel availability applies | `scheduler.py:243-245` |
| **Backup activity also has resource constraints** | Full constraint intersection applied for backup placement too | `scheduler.py:484-513` |
| **Weekend-only activities** | `_infer_preferred_day_offset("weekend")` returns Saturday; weekly date advance accounts for this | `scheduler.py:307-310` |
| **Activity with no duration specified** | `duration_minutes = 0` (all-day reminders); placed but takes no time slot | `models.py:31` |
| **Priority tie** | Secondary sort by `id` ensures deterministic ordering | `scheduler.py:224` |
| **Very dense days (+20 events)** | Possible with short-activity stacking; buffer prevents overlaps; tests validate no double-booking | `scheduler.py:451-458` |
| **Mismatched backup activity type** | Backup is accepted regardless of type; frontend still uses the backup's own `activity_type` | `scheduler.py:552-556` |
| **Invalid resource reference** | Pytest validates all resource IDs resolve before scheduling | `test_scheduler.py:52-68` |
| **Travel-allowed vs travel-blocked distinction** | `requires_fixed_location` flag used; remote-possible activities can still place during travel | `scheduler.py:378-380` |

---

## 9. Testing Strategy (`api/test_scheduler.py`)

### Test Suite Overview (12 tests, all pass)

#### Data Integrity Tests

| # | Test Name | What It Validates | Failure Condition |
|---|---|---|---|
| 1 | `test_activities_count` | ≥105 activities generated | `len(activities) < 105` |
| 2 | `test_activities_have_valid_types` | All types are valid `ActivityType` enum members | Unknown type string |
| 3 | `test_activities_have_valid_frequencies` | Valid periods, priority 1–100, duration 0–240 | Out-of-range values |
| 4 | `test_backup_activity_ids_are_valid` | All backup refs exist; no self-refs | Missing ID or self-loop |
| 5 | `test_backup_activities_exist` | ≥30% of activities have backups | Fewer than 30% |
| 6 | `test_resource_references_exist` | Equipment/specialist/allied_health refs resolve | Invalid resource ID |
| 7 | `test_travel_plans_block_dates` | Travel within horizon; blocked_dates populated | Outside horizon |

#### Scheduling Correctness Tests

| # | Test Name | What It Validates | Failure Condition |
|---|---|---|---|
| 8 | `test_scheduler_runs` | No exceptions; returns non-None | Crash or None return |
| 9 | `test_scheduler_places_most_activities` | ≥70% placement rate | <70% placed |
| 10 | `test_scheduler_no_double_booking` | No overlapping non-short activities on same day | Overlap found |
| 11 | `test_scheduler_skip_adjustments_recorded` | Every violation has a `SkippedActivity` entry | Violations but no skips |
| 12 | `test_scheduler_respects_client_availability` | Activities are within client availability windows | Outside availability |

### Running Tests

```bash
python -m pytest api/test_scheduler.py -v
```

### Coverage Areas Not Yet Tested

- Short-activity stacking correctness (only excluded from double-booking, not tested for correct placement)
- Backup activity substitution logic (count, not correctness)
- Resource schedule intersection (implicitly tested via placement rate)
- Wrap-around logic boundaries
- `_refine_time_preference` edge cases (activity names matching multiple keywords)
- Per-activity instance count accuracy (not validated individually)

---

## 10. Performance &amp; Metrics

### Current Results (seed=42, 3-month horizon)

| Metric | Value |
|---|---|
| Activities requested | 1,445 |
| Activities placed | 1,384 |
| Placement rate | 95.8% |
| Constraint violations | 61 |
| Backup activities used | 85 |
| Horizon | 93 days (Jun 15 – Sep 15, 2026) |
| Active days | 93 |
| Skipped activities | 10 |

### By Type Breakdown

| Type | Placed |
|---|---|
| fitness | 173 |
| food | 598 |
| medication | 175 |
| consultation | 390 |
| therapy | 48 |

### Skipped Activities (10 total)

| Activity | Skipped Dates |
|---|---|
| Morning Smoothie | 18 blocked dates during travel |
| Herbal Tea Time | 18 blocked dates during travel |
| Lunch Break | 18 blocked dates during travel |
| Annual Physical | Single quarterly instance |
| Sleep Consultation | Monthly instance |
| Float Tank | Monthly instance |
| Cupping Therapy | Monthly instance |
| Sprint Interval | Weekly instance |
| Boxing | Weekly instance |
| Golf | Weekly instance |

### Performance Characteristics

- **Cold start:** ~2–5 seconds (data generation + scheduling + import)
- **Request serving:** <50ms (in-memory reads)
- **Memory:** ~50–100 MB (schedule + data in Python objects)
- **I/O:** None at runtime (all in-memory; JSON files written separately via export)

### Bottlenecks

1. **Nested loops in scheduler** — O(A × N × D) with worst-case backup scanning adding another O(A × N × D) for failing activities
2. **Interval intersection/subtraction** — linear in interval count per date; could be optimised with interval trees for very large numbers of small intervals
3. **Backup placement** — uses sequential day scan starting from START_DATE; no smart distribution

### Scaling Limits

| Parameter | Current | Estimated Max |
|---|---|---|
| Activity count | 105 | ~500 (linear slowdown) |
| Horizon | 93 days | ~365 days (4x) |
| Resources | 29 total | ~200 (intersection cost) |
| Placement rate target | >70% | Depends on constraint density |

---

## 11. Deployment

### Vercel (Current)

Config via `vercel.json`:
```json
{
  "builds": [
    { "src": "api/index.py", "use": "@vercel/python", "config": { "runtime": "python3.12" } },
    { "src": "public/**", "use": "@vercel/static" }
  ],
  "routes": [
    { "src": "/api/(.*)", "dest": "api/index.py" },
    { "src": "/(.*)", "dest": "public/$1" }
  ]
}
```

**Cold start on Vercel:** ~5–10s due to serverless function cold boot + data generation/scheduling at import time.

### Local Development

```bash
pip install -r requirements.txt
python -m uvicorn api.index:app --port 8000
# Open http://localhost:8000
```

### Dependencies

```
fastapi>=0.104.0
uvicorn>=0.24.0
pydantic>=2.5.0
```

Zero other runtime dependencies. Testing requires `pytest`.
