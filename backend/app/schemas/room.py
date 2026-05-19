from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class RoomBase(BaseModel):
    name: str
    capacity: int
    description: Optional[str] = None
    facilities: List[str] = []


class RoomCreate(RoomBase):
    pass


class RoomUpdate(BaseModel):
    name: Optional[str] = None
    capacity: Optional[int] = None
    description: Optional[str] = None
    facilities: Optional[List[str]] = None
    is_active: Optional[bool] = None


class RoomResponse(RoomBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Room(RoomResponse):
    pass
