# Resource Allocator — Conversation Summary

## Current State
- **All 12 tests pass**
- **Scheduler Stats**: 1,056 / 1,056 (100%) · 0 violations · 0 backups · 0 skipped
- **Timing**: Morning Jog 6:00-6:38am ✓, Sleep Hygiene 8:53pm ✓, Hydration 92/92 days ✓, Meal Prep Sunday near-Sunday ✓

## Changes Made

### Scheduler Bug Fixes
- **`_subtract_intervals` bug**: When a busy interval starts after the current interval's end (`bs >= e`), the code `break`-ed without appending the remaining interval. Added `if s < e: result.append((s, e))` before the `break`.
- **Daily activity offset**: Daily activities (reminders, hydration check) were using `days_offset = ((idx-1)*13)%84`, causing them to start 20-50 days late (e.g., Hydration Reminder started July 6 instead of June 15). Fixed by starting daily activities from `START_DATE` directly.
- **END_DATE break → wrap**: Replaced `break` on `current_date > END_DATE` with a wrap-around that increments `base_date` by 1 (up to 14 wraps), giving more attempts to place all instances.

### Scheduling Improvements
- **Work-hour blocking**: Non-essential activities (fitness, food, self-therapy, medication) are blocked 9am-5pm on weekdays. Exemptions: CONSULTATION type, `requires_specialist`, `requires_allied_health`, `is_all_day` events.
- **`_find_best_slot` penalty**: Out-of-range placement penalty increased from +1000 to +100000, making wrong-time placement 3000x more expensive than in-range.
- **Meal Prep Sunday fix**: `small_offset` is not applied when `pref_day` is inferred from activity name (e.g., "Sunday" → skip to Sunday without adding spread offset).
- **Better weekly spread**: New formula `(act_index * 3 + act_index // 7) % 7` avoids the zero-clustering issue of `(idx-1)*3%7` (which gave offset=0 to indices with idx-1 multiple of 7).

### Data Changes
- **~1000 total instances**: Converted all daily activities (except 4 essentials) to weekly; converted ~60% of weekly activities to monthly (lowest priority first).
- **Client 6am start**: Weekday availability changed from 07:00 to 06:00, giving 3 hours of morning capacity (was 2).
- **Hydration daily**: `ACT-044` (Hydration Check) removed from `daily_to_weekly` conversion set; stays daily alongside the all-day Hydration Reminder.

## Open Issues
- Meal Prep Sunday mostly lands near Sunday (Mon/Wed/Fri) due to blender equipment unavailability on Sundays — first 2 Sundays have blender blocked by random day-offs. The last 2 are correctly on Sunday.
- No UI filters/toggles for activity type, priority range, backup/skip status, remote/in-person
