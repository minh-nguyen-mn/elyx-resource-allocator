from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, time
from enum import Enum


class ActivityType(str, Enum):
    FITNESS = "fitness"
    FOOD = "food"
    MEDICATION = "medication"
    THERAPY = "therapy"
    CONSULTATION = "consultation"


class TimeOfDay(str, Enum):
    MORNING = "morning"
    AFTERNOON = "afternoon"
    EVENING = "evening"
    ANY = "any"


class FrequencyPeriod(str, Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"


class ActivityDefinition(BaseModel):
    id: str
    name: str
    type: ActivityType
    priority: int = Field(ge=1, le=100)
    frequency_times: int = Field(ge=1)
    frequency_period: FrequencyPeriod
    duration_minutes: int = Field(ge=1, le=240)
    details: str = ""
    facilitator: Optional[str] = None
    facilitator_type: Optional[str] = None
    location: str = ""
    remote_possible: bool = False
    prep: list[str] = Field(default_factory=list)
    backup_activity_ids: list[str] = Field(default_factory=list)
    skip_adjustments: str = ""
    metrics: list[str] = Field(default_factory=list)
    preferred_time_of_day: TimeOfDay = TimeOfDay.ANY
    requires_equipment: list[str] = Field(default_factory=list)
    requires_specialist: Optional[str] = None
    requires_allied_health: Optional[str] = None
    is_all_day: bool = False


class WeeklyAvailability(BaseModel):
    day_of_week: int = Field(ge=0, le=6)
    start_time: str
    end_time: str


class AvailabilityOverride(BaseModel):
    date: str
    available_slots: list[dict] = Field(default_factory=list)
    is_blocked: bool = False


class ResourceSchedule(BaseModel):
    resource_id: str
    resource_name: str
    weekly_availability: list[WeeklyAvailability] = Field(default_factory=list)
    overrides: list[AvailabilityOverride] = Field(default_factory=list)


class Equipment(ResourceSchedule):
    resource_type: str = "equipment"
    location: str = ""


class Specialist(ResourceSchedule):
    resource_type: str = "specialist"
    specialty: str = ""
    remote_available: bool = False


class AlliedHealth(ResourceSchedule):
    resource_type: str = "allied_health"
    profession: str = ""
    remote_available: bool = False


class TravelPlan(BaseModel):
    id: str
    destination: str
    start_date: str
    end_date: str
    purpose: str = ""


class ClientSchedule(BaseModel):
    weekly_availability: list[WeeklyAvailability] = Field(default_factory=list)
    travel_plans: list[TravelPlan] = Field(default_factory=list)
    blocked_dates: list[str] = Field(default_factory=list)


class ScheduledActivity(BaseModel):
    activity_id: str
    activity_name: str
    activity_type: ActivityType
    priority: int
    start_datetime: str
    end_datetime: str
    duration_minutes: int
    location: str
    facilitator: Optional[str] = None
    equipment_used: list[str] = Field(default_factory=list)
    prep: list[str] = Field(default_factory=list)
    metrics: list[str] = Field(default_factory=list)
    details: str = ""
    notes: str = ""
    is_all_day: bool = False


class SkippedActivity(BaseModel):
    activity_id: str
    activity_name: str
    activity_type: ActivityType
    priority: int
    instances_missed: int
    skip_adjustment: str


class SchedulingSummary(BaseModel):
    total_activities_placed: int
    total_activities_requested: int
    constraint_violations: int
    backup_activities_used: int
    placed_by_type: dict[str, int]
    skipped_activities: list[SkippedActivity] = Field(default_factory=list)


class FullData(BaseModel):
    activities: list[ActivityDefinition]
    equipment: list[Equipment]
    specialists: list[Specialist]
    allied_health: list[AlliedHealth]
    client_schedule: ClientSchedule


class ScheduleResponse(BaseModel):
    schedule: list[ScheduledActivity]
    summary: SchedulingSummary
    data: FullData
