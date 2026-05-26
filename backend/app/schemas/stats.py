from pydantic import BaseModel
from typing import List, Dict


class RoomUtilization(BaseModel):
    room_id: int
    room_name: str
    capacity: int
    total_bookings: int
    checked_in_bookings: int
    cancelled_bookings: int
    total_booked_minutes: int
    actual_used_minutes: int
    utilization_rate: float
    check_in_rate: float
    cancel_rate: float


class HourlyBookingStat(BaseModel):
    hour: int
    count: int


class DailyBookingStat(BaseModel):
    date: str
    count: int
    total_minutes: int


class UtilizationResponse(BaseModel):
    period: str
    start_date: str
    end_date: str
    rooms: List[RoomUtilization]
    summary: Dict[str, float]


class HourlyStatsResponse(BaseModel):
    period: str
    start_date: str
    end_date: str
    hourly: List[HourlyBookingStat]


class DailyStatsResponse(BaseModel):
    period: str
    start_date: str
    end_date: str
    daily: List[DailyBookingStat]
