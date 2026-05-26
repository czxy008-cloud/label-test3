from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime


class BookingBase(BaseModel):
    room_id: int
    title: str
    start_time: datetime
    end_time: datetime
    attendees: int = 1
    description: Optional[str] = None

    @field_validator('end_time')
    def end_after_start(cls, v, values):
        if 'start_time' in values.data and v <= values.data['start_time']:
            raise ValueError('end_time must be after start_time')
        return v


class BookingCreate(BookingBase):
    pass


class BookingUpdate(BaseModel):
    title: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    attendees: Optional[int] = None
    description: Optional[str] = None


class BookingCancel(BaseModel):
    reason: Optional[str] = None


class BookingCheckIn(BaseModel):
    pass


class BookingResponse(BookingBase):
    id: int
    user_id: int
    is_cancelled: bool
    cancelled_at: Optional[datetime] = None
    cancelled_by: Optional[int] = None
    cancel_reason: Optional[str] = None
    is_checked_in: bool
    checked_in_at: Optional[datetime] = None
    auto_cancelled: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Booking(BookingResponse):
    pass
