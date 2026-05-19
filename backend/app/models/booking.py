from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    attendees = Column(Integer, default=1)
    description = Column(Text)
    is_cancelled = Column(Boolean, default=False)
    cancelled_at = Column(DateTime)
    cancelled_by = Column(Integer, ForeignKey("users.id"))
    cancel_reason = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    room = relationship("Room", back_populates="bookings")
    user = relationship("User", back_populates="bookings", foreign_keys=[user_id])
    cancelled_by_user = relationship(
        "User",
        back_populates="cancelled_bookings",
        foreign_keys=[cancelled_by]
    )
