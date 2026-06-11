import random
from datetime import datetime, timedelta, date, time
from api.models import (
    ActivityDefinition, ActivityType, FrequencyPeriod, TimeOfDay,
    Equipment, Specialist, AlliedHealth, WeeklyAvailability,
    AvailabilityOverride, TravelPlan, ClientSchedule, FullData, ResourceSchedule
)

random.seed(42)

START_DATE = date(2026, 6, 15)
END_DATE = date(2026, 9, 15)
DAYS = (END_DATE - START_DATE).days

TIME_SLOTS = {
    "morning": (time(6, 0), time(12, 0)),
    "afternoon": (time(12, 0), time(17, 0)),
    "evening": (time(17, 0), time(22, 0)),
}

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

def date_range():
    for i in range(DAYS):
        d = START_DATE + timedelta(days=i)
        yield d


def time_str(t: time) -> str:
    return t.strftime("%H:%M")


def rand_time_between(start: time, end: time, round_to_min: int = 15) -> time:
    start_m = start.hour * 60 + start.minute
    end_m = end.hour * 60 + end.minute
    if end_m <= start_m:
        end_m = start_m + 60
    chosen = random.randint(start_m, end_m - round_to_min)
    chosen = (chosen // round_to_min) * round_to_min
    h, m = divmod(chosen, 60)
    return time(min(h, 23), m)


def generate_activities() -> list[ActivityDefinition]:
    activities = []
    activity_id_counter = {"val": 1}

    def aid():
        aid_val = f"ACT-{activity_id_counter['val']:03d}"
        activity_id_counter["val"] += 1
        return aid_val

    def make(name, atype, freq_t, freq_p, dur, priority, **kw):
        return ActivityDefinition(
            id=aid(), name=name, type=atype,
            frequency_times=freq_t, frequency_period=freq_p,
            duration_minutes=dur, priority=priority, **kw
        )

    # ── FITNESS / EXERCISE (35 activities) ──
    activities.append(make("Morning Jog", ActivityType.FITNESS, 3, FrequencyPeriod.WEEK, 45, 5,
        details="Maintain HR between 130-145 bpm. Route through Riverside Park.",
        facilitator="Self", location="Riverside Park", remote_possible=True,
        prep=["Lay out running clothes", "Fill water bottle", "Check weather"],
        backup_activity_ids=[], skip_adjustments="Replace with 30min brisk walk",
        metrics=["Heart Rate", "Distance (km)", "Pace (min/km)", "Calories"],
        preferred_time_of_day=TimeOfDay.MORNING))

    activities.append(make("Strength Training - Upper Body", ActivityType.FITNESS, 2, FrequencyPeriod.WEEK, 50, 8,
        details="Push/Pull split: bench press 4x8, rows 4x8, overhead press 3x10, pull-ups 3xAMRAP",
        facilitator="Personal Trainer (bi-weekly)", location="Elite Fitness Gym",
        prep=["Pack gym bag", "Prepare pre-workout shake"],
        backup_activity_ids=[], skip_adjustments="Substitute with resistance band workout at home",
        metrics=["Weight (kg)", "Reps", "Sets", "Rest time"],
        requires_equipment=["EQ-DUMBBELL", "EQ-BARBELL"], preferred_time_of_day=TimeOfDay.MORNING))

    activities.append(make("Strength Training - Lower Body", ActivityType.FITNESS, 2, FrequencyPeriod.WEEK, 50, 8,
        details="Squat 4x8, Deadlift 4x6, Leg press 3x12, Calf raises 3x15",
        facilitator="Personal Trainer (bi-weekly)", location="Elite Fitness Gym",
        prep=["Pack gym bag", "Prepare pre-workout shake"],
        backup_activity_ids=[],
        skip_adjustments="Substitute with bodyweight squats and lunges",
        metrics=["Weight (kg)", "Reps", "Sets"],
        requires_equipment=["EQ-BARBELL", "EQ-DUMBBELL"], preferred_time_of_day=TimeOfDay.AFTERNOON))

    activities.append(make("Yoga Flow", ActivityType.FITNESS, 2, FrequencyPeriod.WEEK, 45, 12,
        details="Vinyasa flow focusing on hip mobility and spinal health",
        facilitator="Self (video)", location="Home Studio", remote_possible=True,
        prep=["Roll out yoga mat", "Prepare water", "Dim lights"],
        backup_activity_ids=[], skip_adjustments="15-min stretching routine",
        metrics=["Session duration", "Heart rate variability"],
        requires_equipment=["EQ-YOGA_MAT"], preferred_time_of_day=TimeOfDay.MORNING))

    activities.append(make("Swimming Laps", ActivityType.FITNESS, 1, FrequencyPeriod.WEEK, 45, 18,
        details="20 laps freestyle, 10 laps backstroke, cool-down. Maintain steady pace.",
        facilitator="Self", location="Community Aquatic Center",
        prep=["Pack swim gear", "Towel", "Goggles", "Swim cap"],
        backup_activity_ids=[], skip_adjustments="Replace with 30-min stationary bike",
        metrics=["Laps", "Time", "Stroke count"],
        requires_equipment=[], preferred_time_of_day=TimeOfDay.AFTERNOON))

    activities.append(make("Outdoor Cycling", ActivityType.FITNESS, 2, FrequencyPeriod.WEEK, 60, 15,
        details="30km route through countryside. Maintain cadence 80-90 RPM.",
        facilitator="Self", location="Countryside Bike Trail",
        prep=["Check tire pressure", "Fill water bottles", "Charge bike computer"],
        backup_activity_ids=[], skip_adjustments="Replace with 45-min stationary bike",
        metrics=["Distance", "Average speed", "Elevation gain", "Heart rate"],
        requires_equipment=["EQ-BIKE"], preferred_time_of_day=TimeOfDay.MORNING))

    activities.append(make("HIIT Circuit", ActivityType.FITNESS, 2, FrequencyPeriod.WEEK, 30, 14,
        details="45s work / 15s rest. 8 rounds: burpees, mountain climbers, jump squats, push-ups",
        facilitator="Self", location="Elite Fitness Gym",
        prep=["Fill water bottle", "Set up circuit stations"],
        backup_activity_ids=[], skip_adjustments="Replace with 20-min jump rope session",
        metrics=["Heart rate max", "Recovery HR (1min)", "Rounds completed"],
        requires_equipment=["EQ-JUMP_ROPE"], preferred_time_of_day=TimeOfDay.MORNING))

    activities.append(make("Pilates Reformer", ActivityType.FITNESS, 1, FrequencyPeriod.WEEK, 50, 20,
        details="Full body reformer session focusing on core strength and posture",
        facilitator="Maria Garcia", location="Pilates Body Studio",
        prep=["Wear grip socks", "Arrive 10min early"],
        backup_activity_ids=[], skip_adjustments="Replace with mat Pilates at home",
        metrics=["Form quality", "Core engagement"],
        requires_equipment=[], preferred_time_of_day=TimeOfDay.AFTERNOON))

    activities.append(make("Tai Chi Practice", ActivityType.FITNESS, 2, FrequencyPeriod.WEEK, 40, 22,
        details="Chen style 24-form. Focus on slow, controlled movements and breath work.",
        facilitator="Self (guided video)", location="Botanical Gardens",
        remote_possible=True,
        prep=["Wear comfortable clothing", "Choose quiet spot in garden"],
        backup_activity_ids=[], skip_adjustments="10-min mindful movement routine",
        metrics=["Form completion", "Session calmness (1-10)"],
        preferred_time_of_day=TimeOfDay.MORNING))

    activities.append(make("Eye Exercise Routine", ActivityType.FITNESS, 1, FrequencyPeriod.DAY, 10, 3,
        details="20-20-20 rule practice: every 20min look 20ft away for 20s. Plus palming and eye rolls.",
        facilitator="Self", location="Anywhere", remote_possible=True,
        prep=["Set phone timer reminders"],
        skip_adjustments="None needed - can be done anytime",
        metrics=["Compliance (times completed)", "Eye strain level (1-10)"],
        preferred_time_of_day=TimeOfDay.ANY))

    activities.append(make("Morning Stretch Routine", ActivityType.FITNESS, 1, FrequencyPeriod.DAY, 15, 2,
        details="Full body morning stretch: cat-cow, downward dog, hip circles, shoulder rolls",
        facilitator="Self", location="Home", remote_possible=True,
        prep=["None needed"],
        backup_activity_ids=[], skip_adjustments="5-min quick stretch version",
        metrics=["Flexibility rating (1-10)", "Consistency streak"],
        preferred_time_of_day=TimeOfDay.MORNING))

    activities.append(make("Dance Cardio", ActivityType.FITNESS, 1, FrequencyPeriod.WEEK, 45, 24,
        details="Zumba-inspired dance routine. Moderate to high intensity.",
        facilitator="Instructor - Lisa Wong", location="Dance Fusion Studio",
        prep=["Dance shoes", "Water bottle", "Towel"],
        backup_activity_ids=[], skip_adjustments="Replace with 30-min home dance session",
        metrics=["Calories burned", "Heart rate zones"],
        preferred_time_of_day=TimeOfDay.EVENING))

    activities.append(make("Weekend Trail Hike", ActivityType.FITNESS, 1, FrequencyPeriod.WEEK, 90, 16,
        details="8-10km trail with 300m elevation gain. Vary trails weekly.",
        facilitator="Self", location="Regional Nature Reserve",
        prep=["Pack hiking boots", "Trail snacks", "Water 2L", "Navigation app"],
        backup_activity_ids=[], skip_adjustments="Replace with 60-min power walk",
        metrics=["Distance", "Elevation gain", "Time", "Heart rate"],
        requires_equipment=[], preferred_time_of_day=TimeOfDay.MORNING))

    activities.append(make("Rowing Machine Intervals", ActivityType.FITNESS, 2, FrequencyPeriod.WEEK, 30, 19,
        details="500m sprint / 2min easy row. 6 rounds. Maintain 28-32 SPM on sprints.",
        facilitator="Self", location="Elite Fitness Gym",
        prep=["Fill water bottle", "Set rower damper to 5"],
        backup_activity_ids=[], skip_adjustments="Replace with 20-min battle ropes",
        metrics=["Split time (500m)", "SPM", "Heart rate", "Distance"],
        requires_equipment=["EQ-ROWER"], preferred_time_of_day=TimeOfDay.AFTERNOON))

    activities.append(make("Posture Correction Exercises", ActivityType.FITNESS, 1, FrequencyPeriod.DAY, 15, 6,
        details="Chin tucks, wall angels, doorway stretches, thoracic extensions. 3 sets of 10.",
        facilitator="Self", location="Home", remote_possible=True,
        prep=["Find a wall", "Set timer"],
        skip_adjustments="5-min mini session on busy days",
        metrics=["Posture score (1-10)", "Pain level (1-10)"],
        preferred_time_of_day=TimeOfDay.ANY))

    activities.append(make("Balance Training", ActivityType.FITNESS, 2, FrequencyPeriod.WEEK, 20, 21,
        details="Single leg stands, bosu ball exercises, stability trainer work, heel-to-toe walk",
        facilitator="Self", location="Home", remote_possible=True,
        prep=["Clear open space", "Have chair nearby for support"],
        backup_activity_ids=[], skip_adjustments="5-min balance mini session",
        metrics=["Balance hold time", "Stability rating (1-10)"],
        requires_equipment=["EQ-YOGA_MAT"], preferred_time_of_day=TimeOfDay.MORNING))

    activities.append(make("Resistance Band Full Body", ActivityType.FITNESS, 2, FrequencyPeriod.WEEK, 30, 17,
        details="Band squats, band rows, band press, band pulls, band rotations. 3x15 each.",
        facilitator="Self", location="Home", remote_possible=True,
        prep=["Set up bands with appropriate resistance"],
        backup_activity_ids=[], skip_adjustments="Replace with bodyweight circuit",
        metrics=["Sets completed", "Perceived exertion (1-10)"],
        requires_equipment=["EQ-BANDS"], preferred_time_of_day=TimeOfDay.AFTERNOON))

    activities.append(make("Kettlebell Complex", ActivityType.FITNESS, 2, FrequencyPeriod.WEEK, 30, 20,
        details="KB swings 3x20, goblet squats 3x12, clean-and-press 3x8, Turkish get-ups 3x3",
        facilitator="Self", location="Elite Fitness Gym",
        prep=["Select appropriate kettlebell weights"],
        backup_activity_ids=[], skip_adjustments="Replace with dumbbell circuit",
        metrics=["Weight used", "Reps completed", "Form quality"],
        requires_equipment=["EQ-KETTLEBELL"], preferred_time_of_day=TimeOfDay.AFTERNOON))

    activities.append(make("Bodyweight Circuit", ActivityType.FITNESS, 2, FrequencyPeriod.WEEK, 25, 23,
        details="Push-ups, squats, lunges, planks, burpees, glute bridges. 45/15 intervals.",
        facilitator="Self", location="Home", remote_possible=True,
        prep=["Exercise mat", "Timer app"],
        backup_activity_ids=[], skip_adjustments="10-min express circuit",
        metrics=["Rounds completed", "Heart rate"],
        requires_equipment=["EQ-YOGA_MAT"], preferred_time_of_day=TimeOfDay.MORNING))

    activities.append(make("Sprint Interval Training", ActivityType.FITNESS, 1, FrequencyPeriod.WEEK, 20, 25,
        details="100m sprints x 8 with 90s walking recovery. Full effort on sprints.",
        facilitator="Self", location="High School Track",
        prep=["Sprint shoes", "Dynamic warm-up 10min", "Water"],
        backup_activity_ids=[], skip_adjustments="Replace with stair sprints",
        metrics=["Sprint times", "Heart rate recovery", "Number of sprints"],
        preferred_time_of_day=TimeOfDay.MORNING))

    activities.append(make("Recovery Walk", ActivityType.FITNESS, 1, FrequencyPeriod.DAY, 20, 1,
        details="Easy pace walk. Focus on deep breathing and posture. No headphones.",
        facilitator="Self", location="Neighborhood", remote_possible=True,
        prep=["Comfortable walking shoes"],
        skip_adjustments="Can be shortened to 10min if time constrained",
        metrics=["Steps", "Duration", "Mindfulness rating (1-10)"],
        preferred_time_of_day=TimeOfDay.AFTERNOON))

    activities.append(make("Foam Rolling Recovery", ActivityType.FITNESS, 1, FrequencyPeriod.DAY, 15, 4,
        details="Full body myofascial release: calves, quads, hamstrings, glutes, back, lats",
        facilitator="Self", location="Home", remote_possible=True,
        prep=["Foam roller", "Massage ball"],
        backup_activity_ids=[], skip_adjustments="5-min targeted rolling on tight areas",
        metrics=["Tightness score (1-10) before/after", "Areas rolled"],
        requires_equipment=["EQ-FOAM_ROLLER"], preferred_time_of_day=TimeOfDay.EVENING))

    activities.append(make("Tennis Practice", ActivityType.FITNESS, 1, FrequencyPeriod.WEEK, 60, 26,
        details="Rally practice + serve practice. Focus on consistency and footwork.",
        facilitator="Coach - David Kim", location="City Tennis Club",
        prep=["Tennis racket", "Tennis balls", "Proper shoes", "Water"],
        backup_activity_ids=[], skip_adjustments="Cancel or replace with wall practice",
        metrics=["Rally length", "First serve percentage", "Movement rating"],
        requires_equipment=[], preferred_time_of_day=TimeOfDay.AFTERNOON))

    activities.append(make("Golf Practice", ActivityType.FITNESS, 1, FrequencyPeriod.WEEK, 90, 30,
        details="30min driving range, 30min short game, 30min putting",
        facilitator="Self", location="Green Valley Golf Club",
        prep=["Golf clubs", "Golf balls", "Glove", "Sunscreen"],
        backup_activity_ids=[], skip_adjustments="Replace with 30-min putting practice",
        metrics=["Fairway hits", "Putts per round", "GIR"],
        requires_equipment=[], preferred_time_of_day=TimeOfDay.MORNING))

    activities.append(make("Boxing Training", ActivityType.FITNESS, 1, FrequencyPeriod.WEEK, 45, 28,
        details="Shadow boxing 3rds, heavy bag 3rds, pad work 3rds, conditioning 3rds",
        facilitator="Coach James Johnson", location="Titan Boxing Gym",
        prep=["Hand wraps", "Boxing gloves", "Mouth guard", "Jump rope"],
        backup_activity_ids=[], skip_adjustments="Shadow boxing session at home",
        metrics=["Punch count", "Heart rate zones", "Technique rating"],
        requires_equipment=[], preferred_time_of_day=TimeOfDay.EVENING))

    activities.append(make("Elliptical Cardio", ActivityType.FITNESS, 2, FrequencyPeriod.WEEK, 40, 24,
        details="Interval program: 5min warmup, 30min intervals, 5min cooldown",
        facilitator="Self", location="Elite Fitness Gym",
        prep=["Water bottle", "Podcast or audiobook"],
        backup_activity_ids=[], skip_adjustments="Replace with 30-min outdoor walk",
        metrics=["Distance", "Calories", "Heart rate", "Resistance level"],
        requires_equipment=["EQ-ELLIPTICAL"], preferred_time_of_day=TimeOfDay.AFTERNOON))

    activities.append(make("Jump Rope Cardio", ActivityType.FITNESS, 2, FrequencyPeriod.WEEK, 15, 27,
        details="3min rounds / 30s rest. 4 rounds. Double unders practice. Various footwork patterns.",
        facilitator="Self", location="Home Gym", remote_possible=True,
        prep=["Adjust jump rope length", "Floor mat"],
        backup_activity_ids=[], skip_adjustments="Replace with 10-min high knees",
        metrics=["Skips", "Double unders", "Heart rate"],
        requires_equipment=["EQ-JUMP_ROPE", "EQ-YOGA_MAT"], preferred_time_of_day=TimeOfDay.MORNING))

    activities.append(make("Rock Climbing Session", ActivityType.FITNESS, 1, FrequencyPeriod.WEEK, 60, 31,
        details="Bouldering focus: V3-V5 routes. Work on technique and problem-solving.",
        facilitator="Self", location="The Climbing Wall",
        prep=["Climbing shoes", "Chalk bag", "Arrive early for warmup"],
        backup_activity_ids=[], skip_adjustments="Replace with 30-min hangboard at home",
        metrics=["Routes completed", "Grade achieved", "Attempts per route"],
        requires_equipment=[], preferred_time_of_day=TimeOfDay.EVENING))

    activities.append(make("Aqua Aerobics", ActivityType.FITNESS, 1, FrequencyPeriod.WEEK, 45, 32,
        details="Low impact water workout. Great for recovery and joint mobility.",
        facilitator="Instructor - Karen Mills", location="Community Aquatic Center",
        prep=["Swimsuit", "Water shoes", "Towel"],
        backup_activity_ids=[], skip_adjustments="Replace with 30-min pool walk",
        metrics=["Heart rate", "Perceived exertion"],
        preferred_time_of_day=TimeOfDay.AFTERNOON))

    activities.append(make("Nordic Walking", ActivityType.FITNESS, 2, FrequencyPeriod.WEEK, 50, 28,
        details="Full body walking with poles. 5km route with varied terrain.",
        facilitator="Self", location="Forest Preserve Trails",
        prep=["Nordic walking poles", "Hiking shoes", "Water"],
        backup_activity_ids=[], skip_adjustments="Regular walking without poles",
        metrics=["Distance", "Pace", "Heart rate", "Arm drive quality"],
        requires_equipment=[], preferred_time_of_day=TimeOfDay.MORNING))

    activities.append(make("Core Strengthening", ActivityType.FITNESS, 2, FrequencyPeriod.WEEK, 20, 19,
        details="Planks 3x60s, side planks 3x45s, dead bugs 3x12, bird dogs 3x12, hollow holds 3x30s",
        facilitator="Self", location="Home", remote_possible=True,
        prep=["Exercise mat"],
        backup_activity_ids=[], skip_adjustments="8-min ab express workout",
        metrics=["Hold times", "Form quality", "Core engagement"],
        requires_equipment=["EQ-YOGA_MAT"], preferred_time_of_day=TimeOfDay.MORNING))

    activities.append(make("Hip Mobility Routine", ActivityType.FITNESS, 1, FrequencyPeriod.DAY, 10, 7,
        details="Hip circles, frog pose, lizard pose, pigeon pose, 90-90 stretches",
        facilitator="Self", location="Home", remote_possible=True,
        prep=["Yoga mat or carpeted area"],
        skip_adjustments="5-min hip opener on busy days",
        metrics=["Hip flexibility (1-10)", "Pain/discomfort level"],
        requires_equipment=["EQ-YOGA_MAT"], preferred_time_of_day=TimeOfDay.ANY))

    activities.append(make("Shoulder Mobility Exercises", ActivityType.FITNESS, 1, FrequencyPeriod.DAY, 10, 8,
        details="Band pull-aparts, dislocates, wall slides, external rotations, Y-T-W-L raises",
        facilitator="Self", location="Home", remote_possible=True,
        prep=["Resistance band", "Clear wall space"],
        backup_activity_ids=[], skip_adjustments="5-min shoulder circuit",
        metrics=["Shoulder mobility (1-10)", "Pain level (1-10)"],
        requires_equipment=["EQ-BANDS"], preferred_time_of_day=TimeOfDay.ANY))

    activities.append(make("Neck Stretches", ActivityType.FITNESS, 1, FrequencyPeriod.DAY, 5, 9,
        details="Neck tilts, chin tucks, neck rotations, shoulder shrugs, levator scapulae stretch",
        facilitator="Self", location="Anywhere", remote_possible=True,
        prep=["None needed"],
        backup_activity_ids=[], skip_adjustments="2-min mini session",
        metrics=["Neck tension (1-10)", "Range of motion"],
        preferred_time_of_day=TimeOfDay.ANY))

    # ── FOOD / NUTRITION (20 activities) ──
    activities.append(make("Breakfast Preparation", ActivityType.FOOD, 1, FrequencyPeriod.DAY, 20, 1,
        details="Prepare balanced breakfast with protein, complex carbs, and healthy fats",
        facilitator="Self", location="Home Kitchen",
        prep=["Grocery shopping completed", "Meal prep containers ready"],
        backup_activity_ids=[], skip_adjustments="Quick smoothie if running late",
        metrics=["Meal quality (1-10)", "Time spent", "Macro balance"],
        requires_equipment=["EQ-BLENDER"], preferred_time_of_day=TimeOfDay.MORNING))

    activities.append(make("Lunch Preparation", ActivityType.FOOD, 1, FrequencyPeriod.DAY, 15, 2,
        details="Prepare or assemble healthy lunch. Focus on vegetables and lean protein.",
        facilitator="Self", location="Home Kitchen",
        prep=["Meal prep vegetables on Sunday"],
        backup_activity_ids=[], skip_adjustments="Pre-prepped salad from fridge",
        metrics=["Vegetable servings", "Protein quality"],
        preferred_time_of_day=TimeOfDay.AFTERNOON))

    activities.append(make("Dinner Preparation", ActivityType.FOOD, 1, FrequencyPeriod.DAY, 30, 3,
        details="Cook dinner from scratch. Include 3+ vegetable varieties. Mindful cooking practice.",
        facilitator="Self", location="Home Kitchen",
        prep=["Review recipe", "Prep ingredients", "Clean as you go"],
        backup_activity_ids=[], skip_adjustments="Prep meal from freezer",
        metrics=["Cooking quality (1-10)", "Nutritional balance", "Prep efficiency"],
        requires_equipment=["EQ-BLENDER"], preferred_time_of_day=TimeOfDay.EVENING))

    activities.append(make("Morning Smoothie Prep", ActivityType.FOOD, 1, FrequencyPeriod.DAY, 10, 4,
        details="Green smoothie: spinach, banana, protein powder, almond milk, flax seeds, berries",
        facilitator="Self", location="Home Kitchen",
        prep=["Pre-portion smoothie packs weekly"],
        backup_activity_ids=[], skip_adjustments="Pre-made smoothie pack in freezer",
        metrics=["Ingredients used", "Nutritional density"],
        requires_equipment=["EQ-BLENDER"], preferred_time_of_day=TimeOfDay.MORNING))

    activities.append(make("Meal Prep Sunday", ActivityType.FOOD, 1, FrequencyPeriod.WEEK, 120, 1,
        details="Prepare meals for the week: cook grains, roast vegetables, portion proteins, make sauces",
        facilitator="Self", location="Home Kitchen",
        prep=["Weekly menu plan", "Grocery list", "Container inventory"],
        backup_activity_ids=[], skip_adjustments="Order meal prep delivery service",
        metrics=["Meals prepped", "Time spent", "Cost per meal"],
        requires_equipment=["EQ-BLENDER"], preferred_time_of_day=TimeOfDay.MORNING))

    activities.append(make("Grocery Shopping", ActivityType.FOOD, 1, FrequencyPeriod.WEEK, 60, 6,
        details="Weekly grocery run. Shop perimeter first (produce, meat, dairy). Check pantry before going.",
        facilitator="Self", location="Whole Foods Market",
        prep=["Inventory pantry", "Write list by aisle", "Bring reusable bags"],
        backup_activity_ids=[], skip_adjustments="Delivery order instead",
        metrics=["Budget adherence", "Whole foods percentage", "Time spent"],
        preferred_time_of_day=TimeOfDay.MORNING))

    activities.append(make("Farmers Market Visit", ActivityType.FOOD, 1, FrequencyPeriod.WEEK, 45, 8,
        details="Weekly visit for seasonal produce. Talk to farmers about growing practices.",
        facilitator="Self", location="Downtown Farmers Market",
        prep=["Reusable produce bags", "Cash", "Shopping list"],
        backup_activity_ids=[], skip_adjustments="Order from local CSA box",
        metrics=["Local food percentage", "Seasonal variety", "Money spent locally"],
        preferred_time_of_day=TimeOfDay.MORNING))

    activities.append(make("Fermented Food Preparation", ActivityType.FOOD, 1, FrequencyPeriod.WEEK, 30, 14,
        details="Make sauerkraut or kimchi. Focus on probiotic-rich fermentation.",
        facilitator="Self", location="Home Kitchen",
        prep=["Sterilize jars", "Buy fresh cabbage and seasonings"],
        backup_activity_ids=[], skip_adjustments="Buy fermented foods from store",
        metrics=["Batch size", "Fermentation quality", "Probiotic content"],
        preferred_time_of_day=TimeOfDay.AFTERNOON))

    activities.append(make("Fresh Juice Preparation", ActivityType.FOOD, 1, FrequencyPeriod.DAY, 10, 5,
        details="Fresh vegetable juice: celery, cucumber, ginger, lemon, apple",
        facilitator="Self", location="Home Kitchen",
        prep=["Wash produce", "Set up juicer"],
        backup_activity_ids=[], skip_adjustments="Store-bought cold-pressed juice",
        metrics=["Vegetable servings", "Juice quality"],
        requires_equipment=["EQ-JUICER"], preferred_time_of_day=TimeOfDay.MORNING))

    activities.append(make("Herbal Tea Time", ActivityType.FOOD, 1, FrequencyPeriod.DAY, 5, 3,
        details="Prepare and enjoy herbal tea. Rotate between chamomile, peppermint, ginger, rooibos.",
        facilitator="Self", location="Home",
        prep=["Select tea variety", "Boil water"],
        backup_activity_ids=[], skip_adjustments="Skip or have cold brew tea",
        metrics=["Tea variety", "Mindfulness during tea (1-10)"],
        preferred_time_of_day=TimeOfDay.EVENING))

    activities.append(make("Post-Workout Protein Shake", ActivityType.FOOD, 6, FrequencyPeriod.WEEK, 5, 1,
        details="Within 30min of workout: protein powder, banana, almond milk, creatine",
        facilitator="Self", location="Home Kitchen",
        prep=["Pre-measure protein powder in container"],
        backup_activity_ids=[], skip_adjustments="Ready-to-drink protein shake",
        metrics=["Timing (how soon after workout)", "Protein amount"],
        requires_equipment=["EQ-BLENDER"], preferred_time_of_day=TimeOfDay.ANY))

    activities.append(make("Healthy Snack Prep", ActivityType.FOOD, 3, FrequencyPeriod.WEEK, 15, 9,
        details="Portion nuts, cut vegetables, make energy balls, prepare hummus portions",
        facilitator="Self", location="Home Kitchen",
        prep=["Check snack inventory"],
        backup_activity_ids=[], skip_adjustments="Buy pre-portioned healthy snacks",
        metrics=["Snack variety", "Portion control"],
        preferred_time_of_day=TimeOfDay.AFTERNOON))

    activities.append(make("Bone Broth Preparation", ActivityType.FOOD, 1, FrequencyPeriod.WEEK, 30, 16,
        details="Simmer beef/chicken bones with vegetables and herbs for 24+ hours",
        facilitator="Self", location="Home Kitchen",
        prep=["Buy bones from butcher", "Stock vegetables"],
        backup_activity_ids=[], skip_adjustments="Buy organic bone broth",
        metrics=["Collagen content", "Simmering time"],
        preferred_time_of_day=TimeOfDay.MORNING))

    activities.append(make("Seed Sprouting", ActivityType.FOOD, 2, FrequencyPeriod.WEEK, 10, 17,
        details="Rinse and drain sprouting seeds. Alfalfa, broccoli, mung bean rotation.",
        facilitator="Self", location="Home Kitchen",
        prep=["Sprouting jar with mesh lid", "Organic sprouting seeds"],
        backup_activity_ids=[], skip_adjustments="Buy sprouted seeds",
        metrics=["Sprout quality", "Days to harvest"],
        preferred_time_of_day=TimeOfDay.MORNING))

    activities.append(make("Hydration Check", ActivityType.FOOD, 1, FrequencyPeriod.DAY, 2, 1,
        details="Track water intake. Goal: 2.5L per day. Refill 500ml bottle 5x daily.",
        facilitator="Self", location="Anywhere", remote_possible=True,
        prep=["Fill water bottle morning", "Set hydration reminders"],
        backup_activity_ids=[], skip_adjustments="Drink when remembered",
        metrics=["Total water intake (L)", "Bottle refills", "Urine color"],
        preferred_time_of_day=TimeOfDay.ANY))

    activities.append(make("Mindful Eating Practice", ActivityType.FOOD, 1, FrequencyPeriod.DAY, 20, 2,
        details="Eat one meal per day without screens. Chew 20x per bite. Pause between bites.",
        facilitator="Self", location="Home", remote_possible=True,
        prep=["Set phone aside", "Set table properly"],
        backup_activity_ids=[], skip_adjustments="Practice during snack time",
        metrics=["Meal duration", "Chews per bite", "Satiety awareness (1-10)"],
        preferred_time_of_day=TimeOfDay.ANY))

    activities.append(make("Food Journaling", ActivityType.FOOD, 1, FrequencyPeriod.DAY, 10, 5,
        details="Log meals, energy levels, mood, and digestive response in food tracking app",
        facilitator="Self", location="Home", remote_possible=True,
        prep=["Keep phone or journal handy"],
        backup_activity_ids=[], skip_adjustments="Quick photo log instead",
        metrics=["Days logged", "Food variety score", "Energy-mood correlation"],
        preferred_time_of_day=TimeOfDay.EVENING))

    activities.append(make("Supplement Organization", ActivityType.FOOD, 1, FrequencyPeriod.WEEK, 10, 7,
        details="Fill weekly pill organizer. Check expiration dates. Order refills if needed.",
        facilitator="Self", location="Home",
        prep=["Check supplement inventory"],
        backup_activity_ids=[], skip_adjustments="Use daily pouches from delivery service",
        metrics=["Days organized", "Refills needed"],
        preferred_time_of_day=TimeOfDay.MORNING))

    activities.append(make("New Recipe Exploration", ActivityType.FOOD, 1, FrequencyPeriod.WEEK, 45, 18,
        details="Try one new healthy recipe each week. Focus on global cuisines and new ingredients.",
        facilitator="Self", location="Home Kitchen",
        prep=["Select recipe", "Ensure ingredients available"],
        backup_activity_ids=[], skip_adjustments="Variation on existing recipe",
        metrics=["Recipe success (1-10)", "New ingredients tried", "Family rating"],
        requires_equipment=["EQ-BLENDER"], preferred_time_of_day=TimeOfDay.EVENING))

    activities.append(make("Organic Food Delivery Pickup", ActivityType.FOOD, 1, FrequencyPeriod.WEEK, 15, 10,
        details="Pick up organic produce box from delivery point. Inspect quality and store properly.",
        facilitator="Self", location="Neighborhood Drop-off Point",
        prep=["Bring reusable bags", "Check delivery notification"],
        backup_activity_ids=[], skip_adjustments="Reschedule delivery",
        metrics=["Produce quality", "Seasonal items"],
        preferred_time_of_day=TimeOfDay.AFTERNOON))

    # ── MEDICATION (15 activities) ──
    meds = [
        ("Take Vitamin D (5000 IU)", 1, "Supports immune function, bone health, mood regulation."),
        ("Take Omega-3 (EPA/DHA 2000mg)", 1, "Essential fatty acids. Supports brain, heart, joint health."),
        ("Take Probiotic (50B CFU)", 1, "Multi-strain probiotic for gut health and digestion."),
        ("Take Magnesium Glycinate (400mg)", 1, "Promotes relaxation, muscle recovery, sleep quality."),
        ("Take B-Complex", 1, "Energy metabolism, stress support, neurotransmitter production."),
        ("Take CoQ10 (200mg)", 1, "Mitochondrial support, heart health, cellular energy production."),
        ("Take Collagen Peptides (10g)", 1, "Skin elasticity, joint health, hair and nail strength."),
        ("Take Blood Pressure Medication", 1, "Prescribed by Dr. Reynolds. Take with breakfast."),
        ("Apply Topical Retinoid (0.05%)", 1, "Evening skincare. Anti-aging, cell turnover. Use pea-sized amount."),
        ("Apply Mineral Sunscreen SPF50", 1, "Daily sun protection. Apply to face, neck, hands. Reapply if outdoors."),
        ("Apply CBD Recovery Cream", 2, "Post-workout recovery. Apply to sore muscles and joints."),
        ("Take Allergy Medication (Cetirizine)", 1, "Seasonal allergy management. Non-drowsy formula."),
        ("Take Ashwagandha (600mg)", 1, "Adaptogenic herb for stress management and cortisol balance."),
        ("Take Melatonin (3mg as needed)", 0.5, "Sleep support. Use only when having difficulty falling asleep."),
        ("Medication Inventory Check", 0, "Monthly review of all medications. Check expiry, order refills."),
    ]
    for i, (name, times_per_day, desc) in enumerate(meds):
        freq_t = times_per_day if times_per_day >= 1 else 1
        freq_p = FrequencyPeriod.DAY if times_per_day > 0 else FrequencyPeriod.MONTH
        prio = 1
        if "Melatonin" in name:
            prio = 15
        elif "Inventory" in name:
            prio = 30
        activities.append(make(name, ActivityType.MEDICATION, freq_t, freq_p, 2 if "Apply" not in name and "Sunscreen" not in name and "Inventory" not in name else 5 if "cream" in name.lower() or "retinoid" in name.lower() or "sunscreen" in name.lower() else 10, prio,
            details=desc,
            facilitator="Self", location="Home", remote_possible=True,
            prep=["Have supplements organized in daily container"] if "Inventory" not in name else [],
            backup_activity_ids=[], skip_adjustments="Skip dose if missed (do not double up)",
            metrics=["Dose taken", "Time taken", "Side effects (if any)"],
            preferred_time_of_day=TimeOfDay.MORNING if "melatonin" not in name.lower() and "retinoid" not in name.lower() and "cream" not in name.lower() else TimeOfDay.EVENING))

    # ── THERAPY (15 activities) ──
    activities.append(make("Sauna Session", ActivityType.THERAPY, 3, FrequencyPeriod.WEEK, 30, 10,
        details="15-20min at 80°C. Hydrate before and after. Follow with cool shower.",
        facilitator="Self", location="Elite Fitness Gym Spa",
        prep=["Bring sauna towel", "Fill water bottle 1L", "Shower before"],
        backup_activity_ids=[], skip_adjustments="Replace with warm bath at home",
        metrics=["Session duration", "Sweat volume", "Heart rate increase", "Post-sauna relaxation (1-10)"],
        requires_equipment=["EQ-SAUSA"], preferred_time_of_day=TimeOfDay.EVENING))

    activities.append(make("Ice Bath", ActivityType.THERAPY, 2, FrequencyPeriod.WEEK, 15, 11,
        details="10-12°C for 10-12min. Deep breathing throughout. Cold exposure benefits.",
        facilitator="Self", location="Home Recovery Room",
        prep=["Fill with cold water", "Add ice", "Prepare warm robe nearby", "Set timer"],
        backup_activity_ids=[], skip_adjustments="Cold shower 3min at end of regular shower",
        metrics=["Duration", "Water temperature", "Shivering intensity (1-10)", "Post-bath energy (1-10)"],
        preferred_time_of_day=TimeOfDay.MORNING))

    activities.append(make("Red Light Therapy", ActivityType.THERAPY, 3, FrequencyPeriod.WEEK, 20, 12,
        details="660nm + 850nm. 6-12 inches from panel. 10min front, 10min back.",
        facilitator="Self", location="Home Recovery Room",
        prep=["Set up red light panel", "Wear protective goggles"],
        backup_activity_ids=[], skip_adjustments="Use handheld red light device for shorter session",
        metrics=["Session duration", "Distance from panel", "Notable effects"],
        requires_equipment=["EQ-RED_LIGHT"], preferred_time_of_day=TimeOfDay.MORNING))

    activities.append(make("Compression Therapy", ActivityType.THERAPY, 1, FrequencyPeriod.WEEK, 30, 14,
        details="NormaTec leg recovery system. Recovery mode, medium pressure.",
        facilitator="Self", location="Home",
        prep=["Put on compression boots", "Set device to recovery mode"],
        backup_activity_ids=[], skip_adjustments="Legs-up-the-wall pose 15min",
        metrics=["Recovery feeling (1-10) before/after", "Session program"],
        requires_equipment=["EQ-COMPRESSION"], preferred_time_of_day=TimeOfDay.EVENING))

    activities.append(make("Acupuncture Session", ActivityType.THERAPY, 1, FrequencyPeriod.WEEK, 45, 13,
        details="Full body session. Focus on stress reduction and energy flow (Qi).",
        facilitator="Dr. Michael Brown", location="Wellness Point Acupuncture",
        prep=["Hydrate well", "Avoid caffeine before session", "Wear comfortable clothing"],
        backup_activity_ids=[], skip_adjustments="Reschedule to next available slot",
        metrics=["Energy level (1-10) before/after", "Stress level (1-10) before/after"],
        requires_allied_health="AH-ACUPUNCTURE", preferred_time_of_day=TimeOfDay.AFTERNOON))

    activities.append(make("Sports Massage", ActivityType.THERAPY, 1, FrequencyPeriod.WEEK, 60, 11,
        details="Deep tissue sports massage. Focus on legs, back, and shoulders.",
        facilitator="Lisa Anderson", location="Recovery Room Massage Studio",
        prep=["Hydrate throughout day", "Arrive 10min early", "Communicate problem areas"],
        backup_activity_ids=[], skip_adjustments="Self-massage with foam roller at home",
        metrics=["Tightness level (1-10) before/after", "Range of motion improvement"],
        requires_allied_health="AH-MASSAGE", preferred_time_of_day=TimeOfDay.AFTERNOON))

    activities.append(make("Chiropractic Adjustment", ActivityType.THERAPY, 1, FrequencyPeriod.MONTH, 30, 15,
        details="Full spine adjustment. Focus on lower back and neck alignment.",
        facilitator="Dr. Robert Taylor", location="Spinal Health Chiropractic",
        prep=["Fill out intake form", "Wear comfortable clothing"],
        backup_activity_ids=[], skip_adjustments="Corrective exercises at home",
        metrics=["Pain level (1-10) before/after", "Range of motion improvement"],
        requires_allied_health="AH-CHIROPRACTOR", preferred_time_of_day=TimeOfDay.MORNING))

    activities.append(make("Float Tank Session", ActivityType.THERAPY, 1, FrequencyPeriod.MONTH, 60, 20,
        details="Sensory deprivation float. 10lbs Epsom salts. Focus on meditation and relaxation.",
        facilitator="Self (monitored)", location="Float Haven Studio",
        prep=["Avoid caffeine", "No shaving day of", "Ear plugs provided"],
        backup_activity_ids=[], skip_adjustments="Guided meditation 20min at home",
        metrics=["Relaxation depth (1-10)", "Session insights"],
        preferred_time_of_day=TimeOfDay.EVENING))

    activities.append(make("Cold Plunge (Morning)", ActivityType.THERAPY, 2, FrequencyPeriod.WEEK, 10, 12,
        details="Quick cold exposure: 3-5min at 8-10°C. Wim Hof breathing before.",
        facilitator="Self", location="Home Recovery Room",
        prep=["Set up cold plunge", "Deep breathing preparation"],
        backup_activity_ids=[], skip_adjustments="End regular shower with 2min cold water",
        metrics=["Duration", "Temperature", "Breathing control rating"],
        preferred_time_of_day=TimeOfDay.MORNING))

    activities.append(make("Contrast Therapy", ActivityType.THERAPY, 1, FrequencyPeriod.WEEK, 20, 16,
        details="3min hot / 1min cold. Repeat 4x. End on cold. Hot: 38-40°C, Cold: 10-12°C.",
        facilitator="Self", location="Spa Center",
        prep=["Shower before", "Hydrate", "Bring change of clothes"],
        backup_activity_ids=[], skip_adjustments="Hot-cold shower contrast at home",
        metrics=["Recovery feeling (1-10)", "Temperature tolerance"],
        preferred_time_of_day=TimeOfDay.EVENING))

    activities.append(make("Infrared Sauna", ActivityType.THERAPY, 2, FrequencyPeriod.WEEK, 30, 13,
        details="Full spectrum infrared. 45-60°C. Deep detoxification and relaxation.",
        facilitator="Self", location="Wellness Center",
        prep=["Hydrate 500ml before", "Shower", "Bring electrolyte drink"],
        backup_activity_ids=[], skip_adjustments="Regular sauna session",
        metrics=["Session duration", "Sweat volume", "Post-sauna energy (1-10)"],
        preferred_time_of_day=TimeOfDay.EVENING))

    activities.append(make("Hydrotherapy Pool", ActivityType.THERAPY, 1, FrequencyPeriod.WEEK, 30, 17,
        details="Warm water therapy: gentle movements, stretches, water walking in heated pool",
        facilitator="Self", location="Physical Therapy & Wellness Center",
        prep=["Swimsuit", "Water shoes", "Towel"],
        backup_activity_ids=[], skip_adjustments="Warm bath with Epsom salts at home",
        metrics=["Range of motion", "Pain level (1-10) before/after"],
        preferred_time_of_day=TimeOfDay.AFTERNOON))

    activities.append(make("Sound Bath Meditation", ActivityType.THERAPY, 1, FrequencyPeriod.WEEK, 45, 18,
        details="Singing bowls, gongs, chimes. Lie down and receive sound frequencies.",
        facilitator="Instructor - Zen Sound Studio", location="Sound Healing Sanctuary",
        prep=["Bring yoga mat", "Blanket", "Eye mask", "Dress warmly"],
        backup_activity_ids=[], skip_adjustments="Listen to binaural beats at home",
        metrics=["Relaxation depth (1-10)", "Stress reduction (1-10)"],
        preferred_time_of_day=TimeOfDay.EVENING))

    activities.append(make("Aromatherapy Session", ActivityType.THERAPY, 1, FrequencyPeriod.DAY, 15, 6,
        details="Essential oil diffusion. Rotate: lavender (evening), peppermint (morning), eucalyptus (afternoon).",
        facilitator="Self", location="Home", remote_possible=True,
        prep=["Fill diffuser", "Select oil blend", "Set timer"],
        backup_activity_ids=[], skip_adjustments="Apply essential oil roller blend",
        metrics=["Oil used", "Mood before/after (1-10)", "Sleep quality if evening"],
        preferred_time_of_day=TimeOfDay.EVENING))

    activities.append(make("Cupping Therapy", ActivityType.THERAPY, 1, FrequencyPeriod.MONTH, 30, 22,
        details="Fire cupping or silicone cupping. Focus on back and shoulders.",
        facilitator="Dr. Michael Brown", location="Wellness Point Acupuncture",
        prep=["Hydrate well", "Avoid applying lotions day of"],
        backup_activity_ids=[], skip_adjustments="Self-massage cupping at home",
        metrics=["Pain level (1-10) before/after", "Marking intensity"],
        requires_allied_health="AH-ACUPUNCTURE", preferred_time_of_day=TimeOfDay.AFTERNOON))

    # ── CONSULTATION (20 activities) ──
    activities.append(make("Weekly Personal Training Session", ActivityType.CONSULTATION, 1, FrequencyPeriod.WEEK, 30, 1,
        details="One-on-one session focusing on progressive overload and form correction.",
        facilitator="Alex Thompson - Personal Trainer", location="Elite Fitness Gym",
        prep=["Log previous workouts", "Arrive 5min early for warmup"],
        backup_activity_ids=[], skip_adjustments="Independent training following program",
        metrics=["Strength progress", "Form correction notes", "Next session plan"],
        requires_specialist="SP-TRAINER", preferred_time_of_day=TimeOfDay.MORNING))

    activities.append(make("Monthly Nutritionist Review", ActivityType.CONSULTATION, 1, FrequencyPeriod.MONTH, 45, 5,
        details="Review food logs, body composition, blood work. Adjust meal plan as needed.",
        facilitator="Rachel Patel - Registered Dietitian", location="Virtual (Zoom)", remote_possible=True,
        prep=["Complete 7-day food log", "Recent blood work results", "Body composition scan"],
        backup_activity_ids=[], skip_adjustments="Virtual check-in 15min instead",
        metrics=["Diet adherence (1-10)", "Body composition changes", "Blood work markers"],
        requires_allied_health="AH-DIETITIAN", preferred_time_of_day=TimeOfDay.AFTERNOON))

    activities.append(make("Physiotherapy Session", ActivityType.CONSULTATION, 1, FrequencyPeriod.WEEK, 45, 3,
        details="Rehabilitation exercises, manual therapy, movement assessment. Focus on knee and shoulder.",
        facilitator="Emily Chen - Physiotherapist", location="PhysioFirst Clinic",
        prep=["Wear athletic clothing", "Note any pain points", "Bring previous exercise sheet"],
        backup_activity_ids=[], skip_adjustments="Home exercise program from previous session",
        metrics=["Pain level (1-10)", "Range of motion", "Strength benchmarks"],
        requires_allied_health="AH-PHYSIO", preferred_time_of_day=TimeOfDay.AFTERNOON))

    activities.append(make("Optometrist Checkup", ActivityType.CONSULTATION, 1, FrequencyPeriod.QUARTER, 30, 10,
        details="Comprehensive eye exam, prescription check, eye health screening.",
        facilitator="Dr. Karen Park - Optometrist", location="Vision Care Center",
        prep=["Bring current glasses/contacts", "Insurance card"],
        backup_activity_ids=[], skip_adjustments="Reschedule to next month",
        metrics=["Vision acuity", "Prescription changes", "Eye pressure"],
        preferred_time_of_day=TimeOfDay.MORNING))

    activities.append(make("Dermatologist Follow-up", ActivityType.CONSULTATION, 1, FrequencyPeriod.QUARTER, 30, 10,
        details="Skin cancer screening, mole mapping, skincare routine review.",
        facilitator="Dr. Sarah Lee - Dermatologist", location="ClearSkin Dermatology",
        prep=["List any skin concerns", "Current skincare products list"],
        backup_activity_ids=[], skip_adjustments="Telehealth visit instead",
        metrics=["Skin health score", "Mole changes", "Treatment efficacy"],
        requires_specialist="SP-DERMATOLOGIST", preferred_time_of_day=TimeOfDay.AFTERNOON))

    activities.append(make("Sleep Consultation", ActivityType.CONSULTATION, 1, FrequencyPeriod.MONTH, 45, 8,
        details="Review sleep data, adjust sleep hygiene protocol, discuss interventions.",
        facilitator="Dr. James Wright - Sleep Specialist", location="Virtual (Zoom)", remote_possible=True,
        prep=["7 days of sleep log", "Wearable sleep data export"],
        backup_activity_ids=[], skip_adjustments="Email update to specialist",
        metrics=["Sleep duration", "Sleep quality (1-10)", "HRV trends", "Bedtime consistency"],
        requires_specialist="SP-SLEEP", preferred_time_of_day=TimeOfDay.MORNING))

    activities.append(make("Health Coach Call", ActivityType.CONSULTATION, 1, FrequencyPeriod.WEEK, 30, 2,
        details="Weekly accountability check. Review goals, challenges, and plan for upcoming week.",
        facilitator="Maya Johnson - Health Coach", location="Virtual (Phone)", remote_possible=True,
        prep=["Weekly goal progress", "Top 3 challenges", "Log of completed activities"],
        backup_activity_ids=[], skip_adjustments="Quick text check-in instead",
        metrics=["Goal progress %", "Accountability score (1-10)", "Next week priorities"],
        preferred_time_of_day=TimeOfDay.MORNING))

    activities.append(make("Mental Health Therapy", ActivityType.CONSULTATION, 1, FrequencyPeriod.WEEK, 50, 4,
        details="CBT-based therapy. Focus on stress management, anxiety tools, and emotional regulation.",
        facilitator="Dr. Amanda Torres - Psychologist", location="Virtual (Zoom)", remote_possible=True,
        prep=["Note any key events/feelings since last session", "Practice CBT exercise"],
        backup_activity_ids=[], skip_adjustments="Reschedule within same week",
        metrics=["Mood score (1-10)", "Coping strategy use", "Therapy effectiveness (1-10)"],
        preferred_time_of_day=TimeOfDay.AFTERNOON))

    activities.append(make("Healthspan AI Review", ActivityType.CONSULTATION, 1, FrequencyPeriod.MONTH, 60, 6,
        details="Review AI-generated health insights, biomarker trends, and personalized recommendations.",
        facilitator="Elyx Health AI Specialist", location="Virtual (Video Call)", remote_possible=True,
        prep=["Review previous month's data", "Prepare questions", "Download health report"],
        backup_activity_ids=[], skip_adjustments="Read AI summary report independently",
        metrics=["Biomarker changes", "Recommendation adherence", "Health score trend"],
        preferred_time_of_day=TimeOfDay.MORNING))

    activities.append(make("Blood Work Analysis", ActivityType.CONSULTATION, 1, FrequencyPeriod.QUARTER, 30, 9,
        details="Comprehensive metabolic panel, lipid panel, hormone panel, vitamin levels.",
        facilitator="Lab Technician + Dr. Reynolds review", location="Quest Diagnostics Lab",
        prep=["Fast 10 hours before", "Hydrate with water only", "Bring lab order form"],
        backup_activity_ids=[], skip_adjustments="Reschedule within the month",
        metrics=["All lab values compared to optimal ranges"],
        preferred_time_of_day=TimeOfDay.MORNING))

    activities.append(make("Annual Physical Examination", ActivityType.CONSULTATION, 1, FrequencyPeriod.QUARTER, 45, 7,
        details="Comprehensive physical with primary care physician. Review all systems.",
        facilitator="Dr. Robert Reynolds - Primary Care", location="Reynolds Medical Group",
        prep=["Fast 10 hours", "Medication list", "Family history updates", "Concerns list"],
        backup_activity_ids=[], skip_adjustments="Telehealth check-in with PA",
        metrics=["Vitals", "BMI", "All systems normal/abnormal"],
        requires_specialist="SP-PCP", preferred_time_of_day=TimeOfDay.MORNING))

    activities.append(make("Dental Cleaning & Checkup", ActivityType.CONSULTATION, 1, FrequencyPeriod.QUARTER, 60, 12,
        details="Professional cleaning, oral cancer screening, cavity check, X-rays if needed.",
        facilitator="Dr. Lisa Martinez - Dentist", location="Bright Smile Dental",
        prep=["Brush and floss before", "Insurance card", "List any dental concerns"],
        backup_activity_ids=[], skip_adjustments="Reschedule to next available slot",
        metrics=["Cavities found", "Gum health score", "Cleaning quality"],
        preferred_time_of_day=TimeOfDay.MORNING))

    activities.append(make("Career Coaching Session", ActivityType.CONSULTATION, 1, FrequencyPeriod.MONTH, 45, 14,
        details="Professional development, goal setting, skill gap analysis, networking strategies.",
        facilitator="Mark Williams - Career Coach", location="Virtual (Zoom)", remote_possible=True,
        prep=["Update accomplishment list", "Goal progress review", "Questions"],
        backup_activity_ids=[], skip_adjustments="Self-guided career assessment",
        metrics=["Goal progress %", "New connections made", "Skills developed"],
        preferred_time_of_day=TimeOfDay.AFTERNOON))

    activities.append(make("Financial Wellness Review", ActivityType.CONSULTATION, 1, FrequencyPeriod.MONTH, 30, 15,
        details="Budget review, investment performance check, financial goal tracking.",
        facilitator="Sarah Chen - Financial Advisor", location="Virtual (Zoom)", remote_possible=True,
        prep=["Recent statements", "Budget tracking sheet", "Financial goals update"],
        backup_activity_ids=[], skip_adjustments="Self-review using budgeting app",
        metrics=["Budget adherence %", "Investment return %", "Goal progress"],
        preferred_time_of_day=TimeOfDay.AFTERNOON))

    activities.append(make("Group Fitness Class", ActivityType.CONSULTATION, 2, FrequencyPeriod.WEEK, 45, 11,
        details="Rotating schedule: Monday - Bootcamp, Wednesday - Spin, Friday - Yoga Flow",
        facilitator="Rotating Instructors", location="Elite Fitness Gym",
        prep=["Book spot in advance", "Pack class-specific gear", "Arrive 5min early"],
        backup_activity_ids=[], skip_adjustments="Follow class recording at home",
        metrics=["Class attendance", "Intensity rating (1-10)", "Enjoyment (1-10)"],
        preferred_time_of_day=TimeOfDay.MORNING))

    activities.append(make("Breathwork Practice", ActivityType.CONSULTATION, 2, FrequencyPeriod.DAY, 10, 5,
        details="Box breathing (4-4-4-4) morning + 4-7-8 breathing evening. Wim Hof 3 rounds.",
        facilitator="Self (guided app)", location="Anywhere", remote_possible=True,
        prep=["Set timer", "Find quiet space", "Sit comfortably"],
        backup_activity_ids=[], skip_adjustments="1 round of 3 deep breaths",
        metrics=["HRV before/after", "Oxygen saturation", "Calmness (1-10)"],
        preferred_time_of_day=TimeOfDay.ANY))

    activities.append(make("Gratitude Journaling", ActivityType.CONSULTATION, 1, FrequencyPeriod.DAY, 10, 3,
        details="Write 3 things grateful for, 1 positive experience, 1 affirmation.",
        facilitator="Self", location="Home", remote_possible=True,
        prep=["Journal and pen on nightstand"],
        backup_activity_ids=[], skip_adjustments="Mental gratitude list while falling asleep",
        metrics=["Mood score (1-10)", "Journaling consistency"],
        preferred_time_of_day=TimeOfDay.EVENING))

    activities.append(make("Walking Meditation", ActivityType.CONSULTATION, 2, FrequencyPeriod.WEEK, 30, 6,
        details="Slow, deliberate walking. Focus on each step. 10-step breath cycle.",
        facilitator="Self", location="Peaceful Garden Trail",
        prep=["Find quiet natural setting", "Silent phone"],
        backup_activity_ids=[], skip_adjustments="5-min standing meditation",
        metrics=["Mindfulness depth (1-10)", "Steps taken", "Stress reduction"],
        preferred_time_of_day=TimeOfDay.MORNING))

    activities.append(make("Sleep Hygiene Routine", ActivityType.CONSULTATION, 1, FrequencyPeriod.DAY, 15, 1,
        details="Tidy bedroom, set temperature 18-20°C, blue light blocking, read fiction 20min.",
        facilitator="Self", location="Bedroom", remote_possible=True,
        prep=["No screens 1hr before", "Prepare herbal tea", "Set out sleep clothes"],
        backup_activity_ids=[], skip_adjustments="5-min wind down: 2min box breathing + 3min stretching",
        metrics=["Sleep latency (min)", "Sleep quality (1-10)", "Morning energy (1-10)"],
        preferred_time_of_day=TimeOfDay.EVENING))

    activities.append(make("Biofeedback Training", ActivityType.CONSULTATION, 1, FrequencyPeriod.WEEK, 30, 16,
        details="Heart rate variability training with biofeedback device. Coherent breathing practice.",
        facilitator="Self (with HeartMath device)", location="Home", remote_possible=True,
        prep=["Charge biofeedback device", "Find quiet space", "Connect to app"],
        backup_activity_ids=[], skip_adjustments="HRV app without device",
        metrics=["HRV score", "Coherence ratio", "Session duration"],
        requires_equipment=[], preferred_time_of_day=TimeOfDay.MORNING))

    activities.append(make("Vision Board Review", ActivityType.CONSULTATION, 1, FrequencyPeriod.MONTH, 20, 20,
        details="Review goals, visualize outcomes, update progress photos, adjust quarterly objectives.",
        facilitator="Self", location="Home Office", remote_possible=True,
        prep=["Print progress photos", "Update goal tracking sheet"],
        backup_activity_ids=[], skip_adjustments="5-min goal review in journal",
        metrics=["Goal completion rate", "Visualization quality (1-10)"],
        preferred_time_of_day=TimeOfDay.MORNING))

    # ── Assign backup_activity_ids (post-processing) ──
    # Build a name→id lookup for cross-referencing
    name_to_id = {a.name.lower().strip(): a.id for a in activities}
    def bid(*names):
        """Resolve one or more activity names to IDs, skipping missing."""
        result = []
        for n in names:
            n = n.lower().strip()
            if n in name_to_id:
                result.append(name_to_id[n])
        return result

    # Fitness backups
    act_map = {a.id: a for a in activities}
    for a in activities:
        if a.id == "ACT-001":   # Morning Jog
            a.backup_activity_ids = bid("Recovery Walk")
        elif a.id == "ACT-002":  # Strength Upper
            a.backup_activity_ids = bid("Strength Training - Lower Body", "Bodyweight Circuit")
        elif a.id == "ACT-003":  # Strength Lower
            a.backup_activity_ids = bid("Strength Training - Upper Body", "Resistance Band Full Body")
        elif a.id == "ACT-004":  # Yoga Flow
            a.backup_activity_ids = bid("Tai Chi Practice", "Hip Mobility Routine")
        elif a.id == "ACT-005":  # Swimming
            a.backup_activity_ids = bid("Aqua Aerobics")
        elif a.id == "ACT-006":  # Outdoor Cycling
            a.backup_activity_ids = bid("Elliptical Cardio", "Recovery Walk")
        elif a.id == "ACT-007":  # HIIT Circuit
            a.backup_activity_ids = bid("Jump Rope Cardio", "Bodyweight Circuit")
        elif a.id == "ACT-008":  # Pilates Reformer
            a.backup_activity_ids = bid("Yoga Flow")
        elif a.id == "ACT-009":  # Tai Chi
            a.backup_activity_ids = bid("Yoga Flow", "Walking Meditation")
        elif a.id == "ACT-012":  # Dance Cardio
            a.backup_activity_ids = bid("Bodyweight Circuit", "HIIT Circuit")
        elif a.id == "ACT-013":  # Weekend Hike
            a.backup_activity_ids = bid("Nordic Walking", "Recovery Walk")
        elif a.id == "ACT-014":  # Rowing Machine
            a.backup_activity_ids = bid("Resistance Band Full Body", "Elliptical Cardio")
        elif a.id == "ACT-016":  # Balance Training
            a.backup_activity_ids = bid("Core Strengthening")
        elif a.id == "ACT-017":  # Resistance Band
            a.backup_activity_ids = bid("Bodyweight Circuit")
        elif a.id == "ACT-018":  # Kettlebell
            a.backup_activity_ids = bid("Strength Training - Upper Body", "Strength Training - Lower Body")
        elif a.id == "ACT-019":  # Bodyweight Circuit
            a.backup_activity_ids = bid("Core Strengthening", "Jump Rope Cardio")
        elif a.id == "ACT-020":  # Sprint Interval
            a.backup_activity_ids = bid("HIIT Circuit")
        elif a.id == "ACT-023":  # Tennis
            a.backup_activity_ids = bid("Boxing Training")
        elif a.id == "ACT-024":  # Golf
            a.backup_activity_ids = bid("Weekend Trail Hike")
        elif a.id == "ACT-025":  # Boxing
            a.backup_activity_ids = bid("Tennis Practice")
        elif a.id == "ACT-026":  # Elliptical
            a.backup_activity_ids = bid("Outdoor Cycling", "Recovery Walk")
        elif a.id == "ACT-027":  # Jump Rope
            a.backup_activity_ids = bid("HIIT Circuit", "Sprint Interval Training")
        elif a.id == "ACT-028":  # Rock Climbing
            a.backup_activity_ids = bid("Bodyweight Circuit", "Core Strengthening")
        elif a.id == "ACT-029":  # Aqua Aerobics
            a.backup_activity_ids = bid("Swimming Laps")
        elif a.id == "ACT-030":  # Nordic Walking
            a.backup_activity_ids = bid("Weekend Trail Hike", "Recovery Walk")
        elif a.id == "ACT-031":  # Core Strengthening
            a.backup_activity_ids = bid("Balance Training")
        elif a.id == "ACT-032":  # Hip Mobility
            a.backup_activity_ids = bid("Posture Correction Exercises", "Morning Stretch Routine")
        elif a.id == "ACT-033":  # Shoulder Mobility
            a.backup_activity_ids = bid("Posture Correction Exercises")

        # Food backups
        elif a.id == "ACT-035":  # Breakfast
            a.backup_activity_ids = bid("Morning Smoothie Prep")
        elif a.id == "ACT-036":  # Lunch
            a.backup_activity_ids = bid("Breakfast Preparation", "Dinner Preparation")
        elif a.id == "ACT-037":  # Dinner
            a.backup_activity_ids = bid("Lunch Preparation", "New Recipe Exploration")
        elif a.id == "ACT-038":  # Smoothie
            a.backup_activity_ids = bid("Fresh Juice Preparation")
        elif a.id == "ACT-039":  # Meal Prep
            a.backup_activity_ids = bid("Dinner Preparation")
        elif a.id == "ACT-040":  # Grocery
            a.backup_activity_ids = bid("Organic Food Delivery Pickup")
        elif a.id == "ACT-042":  # Fermented
            a.backup_activity_ids = bid("Healthy Snack Prep")
        elif a.id == "ACT-043":  # Juice
            a.backup_activity_ids = bid("Morning Smoothie Prep")
        elif a.id == "ACT-045":  # Protein Shake
            a.backup_activity_ids = bid("Morning Smoothie Prep")
        elif a.id == "ACT-046":  # Snack Prep
            a.backup_activity_ids = bid("Fermented Food Preparation")
        elif a.id == "ACT-050":  # Mindful Eating
            a.backup_activity_ids = bid("Hydration Check")
        elif a.id == "ACT-051":  # Food Journaling
            a.backup_activity_ids = bid("Mindful Eating Practice")
        elif a.id == "ACT-053":  # New Recipe
            a.backup_activity_ids = bid("Dinner Preparation")

        # Therapy backups
        elif a.id == "ACT-070":  # Sauna
            a.backup_activity_ids = bid("Infrared Sauna")
        elif a.id == "ACT-071":  # Ice Bath
            a.backup_activity_ids = bid("Cold Plunge (Morning)")
        elif a.id == "ACT-072":  # Red Light
            a.backup_activity_ids = bid("Sauna Session")
        elif a.id == "ACT-073":  # Compression
            a.backup_activity_ids = bid("Foam Rolling Recovery")
        elif a.id == "ACT-074":  # Acupuncture
            a.backup_activity_ids = bid("Cupping Therapy")
        elif a.id == "ACT-075":  # Sports Massage
            a.backup_activity_ids = bid("Foam Rolling Recovery")
        elif a.id == "ACT-078":  # Cold Plunge
            a.backup_activity_ids = bid("Ice Bath")
        elif a.id == "ACT-079":  # Contrast
            a.backup_activity_ids = bid("Cold Plunge (Morning)")
        elif a.id == "ACT-080":  # Infrared Sauna
            a.backup_activity_ids = bid("Sauna Session")
        elif a.id == "ACT-081":  # Hydrotherapy
            a.backup_activity_ids = bid("Swimming Laps")
        elif a.id == "ACT-082":  # Sound Bath
            a.backup_activity_ids = bid("Aromatherapy Session")
        elif a.id == "ACT-083":  # Aromatherapy
            a.backup_activity_ids = bid("Herbal Tea Time")
        elif a.id == "ACT-084":  # Cupping
            a.backup_activity_ids = bid("Acupuncture Session")

        # Consultation backups
        elif a.id == "ACT-085":  # Personal Training
            a.backup_activity_ids = bid("Group Fitness Class", "Bodyweight Circuit")
        elif a.id == "ACT-086":  # Nutritionist
            a.backup_activity_ids = bid("Health Coach Call")
        elif a.id == "ACT-087":  # Physiotherapy
            a.backup_activity_ids = bid("Posture Correction Exercises", "Morning Stretch Routine")
        elif a.id == "ACT-089":  # Dermatologist
            a.backup_activity_ids = bid("Healthspan AI Review")
        elif a.id == "ACT-090":  # Sleep
            a.backup_activity_ids = bid("Sleep Hygiene Routine")
        elif a.id == "ACT-091":  # Health Coach
            a.backup_activity_ids = bid("Healthspan AI Review")
        elif a.id == "ACT-092":  # Mental Health
            a.backup_activity_ids = bid("Gratitude Journaling", "Breathwork Practice")
        elif a.id == "ACT-097":  # Career Coaching
            a.backup_activity_ids = bid("Financial Wellness Review")
        elif a.id == "ACT-098":  # Financial
            a.backup_activity_ids = bid("Career Coaching Session")
        elif a.id == "ACT-099":  # Group Fitness
            a.backup_activity_ids = bid("Weekly Personal Training Session")
        elif a.id == "ACT-102":  # Walking Meditation
            a.backup_activity_ids = bid("Breathwork Practice")
        elif a.id == "ACT-104":  # Biofeedback
            a.backup_activity_ids = bid("Breathwork Practice")

    # Ensure we have the right number of activities
    assert len(activities) >= 100, f"Only generated {len(activities)} activities, need 100+"
    return activities


def _generate_resource_availability(schedule, start_date, end_date):
    weekly = schedule.weekly_availability
    overrides = {o.date: o for o in getattr(schedule, 'overrides', [])}
    result = []
    current = start_date
    while current <= end_date:
        ds = current.strftime("%Y-%m-%d")
        if ds in overrides:
            ov = overrides[ds]
            if ov.is_blocked:
                current += timedelta(days=1)
                continue
            for slot in ov.available_slots:
                result.append({
                    "date": ds,
                    "start": f"{ds}T{slot['start']}",
                    "end": f"{ds}T{slot['end']}"
                })
        else:
            dow = current.weekday()
            for wa in weekly:
                if wa.day_of_week == dow:
                    result.append({
                        "date": ds,
                        "start": f"{ds}T{wa.start_time}",
                        "end": f"{ds}T{wa.end_time}"
                    })
        current += timedelta(days=1)
    return result


def generate_resource_schedules(rand: random.Random):
    equipment_schedules = []
    specialist_schedules = []
    allied_health_schedules = []

    base_start = START_DATE

    # ── EQUIPMENT ──
    eq_defs = [
        ("EQ-TREADMILL", "Treadmill", "Cardio Zone"),
        ("EQ-BIKE", "Road Bike", "Bike Storage"),
        ("EQ-ROWER", "Rowing Machine", "Cardio Zone"),
        ("EQ-DUMBBELL", "Dumbbell Set (5-50lbs)", "Free Weights Area"),
        ("EQ-BARBELL", "Olympic Barbell Set", "Free Weights Area"),
        ("EQ-YOGA_MAT", "Yoga Mat", "Studio A"),
        ("EQ-FOAM_ROLLER", "Foam Roller", "Recovery Area"),
        ("EQ-BANDS", "Resistance Band Set", "Studio A"),
        ("EQ-KETTLEBELL", "Kettlebell Set (8-32kg)", "Free Weights Area"),
        ("EQ-JUMP_ROPE", "Speed Jump Rope", "Cardio Zone"),
        ("EQ-SAUSA", "Finnish Sauna", "Spa Area"),
        ("EQ-RED_LIGHT", "Red Light Therapy Panel", "Recovery Area"),
        ("EQ-COMPRESSION", "Compression Recovery Boots", "Recovery Area"),
        ("EQ-ELLIPTICAL", "Elliptical Trainer", "Cardio Zone"),
        ("EQ-BLENDER", "High-Performance Blender", "Kitchen"),
        ("EQ-JUICER", "Cold Press Juicer", "Kitchen"),
    ]

    for eid, ename, loc in eq_defs:
        days_off = rand.sample([d for d in date_range()], rand.randint(5, 12))
        weekly_avail = [
            WeeklyAvailability(day_of_week=d, start_time="06:00", end_time="21:00")
            for d in range(5)
        ]
        weekly_avail.append(WeeklyAvailability(day_of_week=5, start_time="07:00", end_time="20:00"))
        weekly_avail.append(WeeklyAvailability(day_of_week=6, start_time="08:00", end_time="18:00"))

        overrides = [AvailabilityOverride(date=d.strftime("%Y-%m-%d"), is_blocked=True) for d in days_off]

        # Add maintenance days
        maint_dates = []
        for d in date_range():
            if d.strftime("%Y-%m-%d") not in [o.date for o in overrides] and rand.random() < 0.02:
                maint_dates.append(d)
        for d in maint_dates:
            overrides.append(AvailabilityOverride(
                date=d.strftime("%Y-%m-%d"),
                available_slots=[{"start": "08:00", "end": "10:00"}, {"start": "14:00", "end": "21:00"}]
            ))

        equipment_schedules.append(Equipment(
            resource_id=eid,
            resource_name=ename,
            weekly_availability=weekly_avail,
            overrides=overrides,
            location=loc
        ))

    # ── SPECIALISTS ──
    spec_defs = [
        ("SP-TRAINER", "Alex Thompson", "Personal Training", ["06:00", "18:00"]),
        ("SP-YOGA", "Maria Garcia", "Yoga Instruction", ["08:00", "16:00"]),
        ("SP-SWIM", "David Kim", "Swimming Coaching", ["07:00", "19:00"]),
        ("SP-TENNIS", "Sarah Williams", "Tennis Coaching", ["08:00", "17:00"]),
        ("SP-BOXING", "James Johnson", "Boxing Training", ["10:00", "20:00"]),
        ("SP-PCP", "Dr. Robert Reynolds", "Primary Care", ["08:00", "17:00"]),
        ("SP-DERMATOLOGIST", "Dr. Sarah Lee", "Dermatology", ["09:00", "16:00"]),
        ("SP-SLEEP", "Dr. James Wright", "Sleep Medicine", ["09:00", "15:00"]),
    ]

    for sid, sname, spec, hours in spec_defs:
        days_off = []
        for d in date_range():
            if d.weekday() >= 5 and rand.random() < 0.5:
                days_off.append(d)
            elif d.weekday() < 5 and rand.random() < 0.05:
                days_off.append(d)

        weekly_avail = []
        for d in range(5):
            if d < 3:
                weekly_avail.append(WeeklyAvailability(day_of_week=d, start_time=hours[0], end_time=hours[1]))
            elif d == 3 or d == 4:
                late_start = time(rand.randint(9, 11), 0)
                late_end = time(rand.randint(17, 19), 0)
                weekly_avail.append(WeeklyAvailability(
                    day_of_week=d,
                    start_time=late_start.strftime("%H:%M"),
                    end_time=late_end.strftime("%H:%M")
                ))

        overrides = []
        for d in days_off:
            ds = d.strftime("%Y-%m-%d")
            if rand.random() < 0.3:
                overrides.append(AvailabilityOverride(
                    date=ds,
                    available_slots=[{"start": "10:00", "end": "12:00"}, {"start": "14:00", "end": "16:00"}]
                ))
            else:
                overrides.append(AvailabilityOverride(date=ds, is_blocked=True))

        specialist_schedules.append(Specialist(
            resource_id=sid,
            resource_name=sname,
            weekly_availability=weekly_avail,
            overrides=overrides,
            specialty=spec,
            remote_available=(sid != "SP-TENNIS" and sid != "SP-BOXING" and sid != "SP-SWIM")
        ))

    # ── ALLIED HEALTH ──
    ah_defs = [
        ("AH-PHYSIO", "Emily Chen", "Physiotherapy", ["07:00", "18:00"]),
        ("AH-DIETITIAN", "Rachel Patel", "Dietetics", ["08:00", "17:00"]),
        ("AH-ACUPUNCTURE", "Michael Brown", "Acupuncture", ["09:00", "18:00"]),
        ("AH-MASSAGE", "Lisa Anderson", "Massage Therapy", ["09:00", "19:00"]),
        ("AH-CHIROPRACTOR", "Robert Taylor", "Chiropractic", ["08:00", "17:00"]),
    ]

    for aid, aname, prof, hours in ah_defs:
        days_off = []
        for d in date_range():
            if d.weekday() >= 5 and rand.random() < 0.4:
                days_off.append(d)
            elif d.weekday() < 5 and rand.random() < 0.04:
                days_off.append(d)

        weekly_avail = [
            WeeklyAvailability(day_of_week=d, start_time=hours[0], end_time=hours[1])
            for d in range(5)
        ]

        overrides = [
            AvailabilityOverride(date=d.strftime("%Y-%m-%d"), is_blocked=True)
            for d in days_off
        ]

        allied_health_schedules.append(AlliedHealth(
            resource_id=aid,
            resource_name=aname,
            weekly_availability=weekly_avail,
            overrides=overrides,
            profession=prof,
            remote_available=(aid == "AH-DIETITIAN")
        ))

    return equipment_schedules, specialist_schedules, allied_health_schedules


def generate_client_schedule(rand: random.Random) -> ClientSchedule:
    weekly_avail = [
        WeeklyAvailability(day_of_week=d, start_time="07:00", end_time="21:30")
        for d in range(5)
    ]
    weekly_avail.append(WeeklyAvailability(day_of_week=5, start_time="08:00", end_time="20:00"))
    weekly_avail.append(WeeklyAvailability(day_of_week=6, start_time="08:00", end_time="19:00"))

    # 3 travel plans over the 3 months
    travel_plans = [
        TravelPlan(
            id="TRIP-001",
            destination="New York, NY - Business Conference",
            start_date="2026-07-10",
            end_date="2026-07-14",
            purpose="Annual health technology summit. Attend talks and network."
        ),
        TravelPlan(
            id="TRIP-002",
            destination="Aspen, CO - Family Vacation",
            start_date="2026-08-05",
            end_date="2026-08-12",
            purpose="Summer hiking and outdoor activities with family."
        ),
        TravelPlan(
            id="TRIP-003",
            destination="San Diego, CA - Wellness Retreat",
            start_date="2026-09-01",
            end_date="2026-09-05",
            purpose="Wellness retreat focusing on advanced bio-hacking and recovery protocols."
        ),
    ]

    blocked_dates = []
    for trip in travel_plans:
        start = datetime.strptime(trip.start_date, "%Y-%m-%d").date()
        end = datetime.strptime(trip.end_date, "%Y-%m-%d").date()
        current = start
        while current <= end:
            blocked_dates.append(current.strftime("%Y-%m-%d"))
            current += timedelta(days=1)

    return ClientSchedule(
        weekly_availability=weekly_avail,
        travel_plans=travel_plans,
        blocked_dates=blocked_dates
    )


def generate_all_data() -> FullData:
    rand = random.Random(42)
    activities = generate_activities()
    equipment, specialists, allied_health = generate_resource_schedules(rand)
    client_schedule = generate_client_schedule(rand)
    return FullData(
        activities=activities,
        equipment=equipment,
        specialists=specialists,
        allied_health=allied_health,
        client_schedule=client_schedule
    )
