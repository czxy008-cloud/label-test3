from sqlalchemy import Column, Integer, String, Boolean, DateTime, ARRAY
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    capacity = Column(Integer, nullable=False)
    description = Column(String(500))
    facilities = Column(ARRAY(String), default=list)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    bookings = relationship("Booking", back_populates="room")
