from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os

from api.data_generator import generate_all_data
from api.scheduler import compute_schedule
from api.models import ScheduleResponse, SchedulingSummary, FullData, ScheduledActivity

app = FastAPI(title="Elyx Resource Allocator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA = generate_all_data()

schedule, summary = compute_schedule(DATA)

schedule.sort(key=lambda s: (s.start_datetime, s.priority))


@app.get("/api/activities", response_model=list)
def get_activities():
    return [a.model_dump() for a in DATA.activities]


@app.get("/api/equipment", response_model=list)
def get_equipment():
    return [e.model_dump() for e in DATA.equipment]


@app.get("/api/specialists", response_model=list)
def get_specialists():
    return [s.model_dump() for s in DATA.specialists]


@app.get("/api/allied_health", response_model=list)
def get_allied_health():
    return [a.model_dump() for a in DATA.allied_health]


@app.get("/api/client_schedule")
def get_client_schedule():
    return DATA.client_schedule.model_dump()


@app.get("/api/schedule", response_model=ScheduleResponse)
def get_schedule():
    return ScheduleResponse(
        schedule=schedule,
        summary=summary,
        data=DATA,
    )


@app.get("/api/summary")
def get_summary():
    return summary.model_dump()


@app.get("/api/data", response_model=FullData)
def get_data():
    return DATA


# Serve static files from public/
public_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "public")
if os.path.exists(public_dir):
    app.mount("/", StaticFiles(directory=public_dir, html=True), name="public")
