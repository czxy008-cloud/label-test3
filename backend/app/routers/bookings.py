from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.models import Booking, Room, User
from app.schemas import BookingCreate, BookingUpdate, BookingResponse, BookingCancel, BookingCheckIn
from app.auth import get_current_active_user, get_current_admin_user

router = APIRouter(prefix="/bookings", tags=["bookings"])


def check_conflict(db: Session, room_id: int, start_time: datetime, end_time: datetime, exclude_booking_id: Optional[int] = None) -> bool:
    query = db.query(Booking).filter(
        Booking.room_id == room_id,
        Booking.is_cancelled == False,
        or_(
            and_(Booking.start_time < end_time, Booking.end_time > start_time)
        )
    )
    if exclude_booking_id:
        query = query.filter(Booking.id != exclude_booking_id)
    conflicting = query.first()
    return conflicting is not None


def validate_time_slot(start_time: datetime, end_time: datetime):
    duration = end_time - start_time
    if duration < timedelta(minutes=30):
        raise HTTPException(status_code=400, detail="Minimum booking duration is 30 minutes")

    if start_time.minute % 30 != 0 or end_time.minute % 30 != 0:
        raise HTTPException(status_code=400, detail="Bookings must start and end at 30-minute intervals")

    if start_time < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Cannot book past time slots")


@router.get("/", response_model=List[BookingResponse])
def get_bookings(
    room_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    include_cancelled: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(Booking)

    if room_id:
        query = query.filter(Booking.room_id == room_id)
    if start_date:
        query = query.filter(Booking.start_time >= start_date)
    if end_date:
        query = query.filter(Booking.end_time <= end_date)
    if not include_cancelled:
        query = query.filter(Booking.is_cancelled == False)

    bookings = query.order_by(Booking.start_time).all()
    return bookings


@router.get("/my", response_model=List[BookingResponse])
def get_my_bookings(
    include_cancelled: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(Booking).filter(Booking.user_id == current_user.id)
    if not include_cancelled:
        query = query.filter(Booking.is_cancelled == False)
    bookings = query.order_by(Booking.start_time.desc()).all()
    return bookings


@router.get("/{booking_id}", response_model=BookingResponse)
def get_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking


@router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
def create_booking(
    booking: BookingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    room = db.query(Room).filter(Room.id == booking.room_id, Room.is_active == True).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found or inactive")

    if booking.attendees > room.capacity:
        raise HTTPException(status_code=400, detail=f"Room capacity is {room.capacity}, cannot accommodate {booking.attendees} attendees")

    validate_time_slot(booking.start_time, booking.end_time)

    if check_conflict(db, booking.room_id, booking.start_time, booking.end_time):
        raise HTTPException(status_code=400, detail="Time slot conflicts with existing booking")

    db_booking = Booking(
        **booking.dict(),
        user_id=current_user.id
    )
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    return db_booking


@router.post("/{booking_id}/cancel", response_model=BookingResponse)
def cancel_booking(
    booking_id: int,
    cancel_data: BookingCancel,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.is_cancelled:
        raise HTTPException(status_code=400, detail="Booking is already cancelled")

    if booking.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="You can only cancel your own bookings")

    booking.is_cancelled = True
    booking.cancelled_at = datetime.utcnow()
    booking.cancelled_by = current_user.id
    booking.cancel_reason = cancel_data.reason

    db.commit()
    db.refresh(booking)
    return booking


@router.put("/{booking_id}", response_model=BookingResponse)
def update_booking(
    booking_id: int,
    booking_update: BookingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.is_cancelled:
        raise HTTPException(status_code=400, detail="Cannot update a cancelled booking")

    if booking.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="You can only update your own bookings")

    update_data = booking_update.dict(exclude_unset=True)

    new_start = update_data.get('start_time', booking.start_time)
    new_end = update_data.get('end_time', booking.end_time)
    new_room_id = update_data.get('room_id', booking.room_id)

    if 'start_time' in update_data or 'end_time' in update_data:
        validate_time_slot(new_start, new_end)

    if 'start_time' in update_data or 'end_time' in update_data or 'room_id' in update_data:
        if check_conflict(db, new_room_id, new_start, new_end, exclude_booking_id=booking_id):
            raise HTTPException(status_code=400, detail="Time slot conflicts with existing booking")

    for key, value in update_data.items():
        setattr(booking, key, value)

    db.commit()
    db.refresh(booking)
    return booking


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    db.delete(booking)
    db.commit()
    return None


@router.get("/conflict/check")
def check_booking_conflict(
    room_id: int,
    start_time: datetime,
    end_time: datetime,
    exclude_booking_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    has_conflict = check_conflict(db, room_id, start_time, end_time, exclude_booking_id)
    return {"has_conflict": has_conflict}


@router.post("/{booking_id}/checkin", response_model=BookingResponse)
def checkin_booking(
    booking_id: int,
    checkin_data: BookingCheckIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.is_cancelled:
        raise HTTPException(status_code=400, detail="Cannot check in to a cancelled booking")

    if booking.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="You can only check in to your own bookings")

    if booking.is_checked_in:
        raise HTTPException(status_code=400, detail="Booking is already checked in")

    now = datetime.utcnow()
    checkin_window_start = booking.start_time - timedelta(minutes=30)
    checkin_window_end = booking.start_time + timedelta(minutes=15)

    if now < checkin_window_start:
        raise HTTPException(
            status_code=400,
            detail=f"Check-in is only available 30 minutes before the booking starts"
        )

    if now > checkin_window_end:
        raise HTTPException(
            status_code=400,
            detail=f"Check-in is only available within 15 minutes after the booking starts"
        )

    booking.is_checked_in = True
    booking.checked_in_at = now

    db.commit()
    db.refresh(booking)
    return booking
