# Prompts Used

## Initial System Understanding & Architecture

**Prompt:** "Analyze this assignment: Implement a Resource Allocator that transforms HealthSpan AI recommendations into scheduled tasks while coordinating with equipment, specialists, client schedules, travel plans, and allied health availability. What is the core engineering challenge and propose an architecture."

**Response contained:** Analysis identifying multi-constraint temporal planning as the core challenge, with a proposed architecture using Python FastAPI backend, greedy priority-based scheduler with constraint intersection, and FullCalendar frontend.

## Data Model Design

**Prompt:** "Design Pydantic data models for a health activity scheduling system with activity types (fitness, food, medication, therapy, consultation), resource schedules (equipment, specialists, allied health), client availability with travel plans, and scheduled output."

**Response contained:** Pydantic models with ActivityDefinition, ResourceSchedule (Equipment, Specialist, AlliedHealth subclasses), ClientSchedule with TravelPlan, and ScheduledActivity output model.

## Data Generator

**Prompt:** "Generate realistic health/wellness activities for 3 months covering 100+ activities across fitness, food, medication, therapy, and consultation types. Include realistic frequencies (daily, 3x/week, 1x/week, 1x/month), durations, priorities, resource requirements, equipment needs, and prep instructions. Also generate availabilities for equipment, specialists, and allied health professionals with realistic weekly schedules and random days off."

**Response contained:** 105 activities with realistic names, frequencies, and constraints. 16 equipment items, 8 specialists, 5 allied health professionals each with weekly schedules and random availability overrides. 3 travel plans for the client.

## Constraint-Based Scheduler

**Prompt:** "Write a scheduler that takes activities sorted by priority and places them into available time slots. It must respect: client availability (with travel blocks), equipment availability, specialist availability, and allied health availability. Distribute instances evenly across the 3-month period and avoid double-booking. Handle backup activities when primary cannot be placed."

**Response contained:** Greedy interval-based scheduler that pre-computes day-wise availability for all resources, uses interval intersection and subtraction to find valid slots, and distributes instances evenly using target intervals. Fixed bugs including TIME_RANGES unit mismatch (hours vs minutes) and activity_used_dates guard being too restrictive.

## Frontend Calendar Display

**Prompt:** "Create a single HTML page that displays the generated schedule using FullCalendar.io. Show events color-coded by type (fitness=green, food=yellow, medication=red, therapy=purple, consultation=blue). Include a summary panel showing placement statistics, type breakdown, and top priority activities. Show travel blocks as all-day red events."

**Response contained:** FullCalendar integration with month/week/day views, color-coded events, modal popup with activity details on click, and sidebar panels for statistics, type breakdown, and travel constraints.

## Vercel Deployment Config

**Prompt:** "Configure a Vercel deployment for a Python FastAPI backend with static file frontend serving. Route /api/* to Python serverless function and /* to static files."

**Response contained:** vercel.json with Python runtime for api/index.py and static file serving for public/ directory.
