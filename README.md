# Elyx Resource Allocator

A constraint-based scheduler that transforms health recommendations into a personalised, actionable calendar plan — coordinating activities with equipment, specialists, allied health professionals, and travel constraints.

## Architecture

```
Frontend (FullCalendar.js) ←→ FastAPI Backend ←→ Scheduler ←→ Data Generator
                              (Vercel Python)     (Greedy       (105 activities,
                                                   constraint-   3mo resource
                                                   based)        availability)
```

## Key Design Decisions

- **Greedy priority-based scheduling** — Activities sorted by priority; instances evenly distributed using target intervals
- **Constraint intersection** — Places activities only where client + all required resource availability windows overlap
- **Interval subtraction** — Shared busy-time tracking prevents double-booking across all activities
- **Backup fallback** — When primary activity can't be placed, tries backup activities with different resource requirements
- **Pydantic models** — Validation throughout, JSON export for data transparency

## Project Structure

```
├── api/
│   ├── index.py          FastAPI server (Vercel serverless)
│   ├── models.py         Pydantic data models
│   ├── data_generator.py Generates 105 activities + 3mo availability
│   └── scheduler.py      Constraint-based scheduling engine
├── public/
│   └── index.html        FullCalendar frontend
├── data/                 Exported JSON data
│   ├── activities.json
│   ├── equipment.json
│   ├── specialists.json
│   ├── allied_health.json
│   ├── client_schedule.json
│   ├── schedule.json
│   └── summary.json
├── vercel.json           Vercel deployment config
├── requirements.txt
├── prompts.md            Prompts used during development
└── README.md
```

## Running Locally

```bash
pip install -r requirements.txt
python -m uvicorn api.index:app --port 8000
# Open http://localhost:8000
```

## API Endpoints

| Endpoint | Description |
|---|---|
| `GET /api/data` | All generated data (activities, resources, client) |
| `GET /api/schedule` | Computed schedule + summary |
| `GET /api/summary` | Placement statistics only |
| `GET /` | Calendar frontend |

## Scheduling Results

- **105 activities** across 5 types (fitness, food, medication, therapy, consultation)
- **4349 events scheduled** over 92 days (94.6% placement rate)
- **248 constraint violations** where activities couldn't be placed due to resource conflicts
- **16 equipment items**, **8 specialists**, **5 allied health professionals**
- **3 travel plans** covering 18 blocked days

## Data

All generated data is exported to the `data/` directory as JSON for inspection.

## Deployment

Deployed on Vercel. See `vercel.json` for configuration.
