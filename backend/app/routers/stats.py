from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, and_
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.models import Booking, Room, User
from app.schemas import (
    UtilizationResponse, RoomUtilization,
    HourlyStatsResponse, HourlyBookingStat,
    DailyStatsResponse, DailyBookingStat
)
from app.auth import get_current_admin_user

router = APIRouter(prefix="/stats", tags=["stats"])


def resolve_period(period: str, start_date: Optional[datetime], end_date: Optional[datetime]):
    now = datetime.utcnow()
    if period == "7d":
        start = now - timedelta(days=7)
        end = now
    elif period == "30d":
        start = now - timedelta(days=30)
        end = now
    elif period == "90d":
        start = now - timedelta(days=90)
        end = now
    else:
        start = start_date or (now - timedelta(days=30))
        end = end_date or now
        period = "custom"
    if start > end:
        start, end = end, start
    return period, start, end


@router.get("/utilization", response_model=UtilizationResponse)
def get_room_utilization(
    period: str = Query("30d", pattern="^(7d|30d|90d|custom)$"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    period, start, end = resolve_period(period, start_date, end_date)

    bookings = db.query(Booking).filter(
        and_(
            Booking.start_time >= start,
            Booking.start_time <= end,
        )
    ).all()

    rooms = db.query(Room).all()
    room_map = {r.id: r for r in rooms}

    agg = {}
    for b in bookings:
        stat = agg.setdefault(b.room_id, {
            "total": 0,
            "checked_in": 0,
            "cancelled": 0,
            "booked_minutes": 0,
            "used_minutes": 0,
        })
        duration = int((b.end_time - b.start_time).total_seconds() / 60)
        stat["total"] += 1
        stat["booked_minutes"] += duration
        if b.is_cancelled:
            stat["cancelled"] += 1
        else:
            stat["used_minutes"] += duration
            if b.is_checked_in:
                stat["checked_in"] += 1

    total_minutes = int((end - start).total_seconds() / 60)

    room_stats = []
    for room in rooms:
        s = agg.get(room.id, {"total": 0, "checked_in": 0, "cancelled": 0,
                              "booked_minutes": 0, "used_minutes": 0})
        utilization_rate = round(s["used_minutes"] / total_minutes * 100, 2) if total_minutes > 0 else 0
        check_in_rate = round(s["checked_in"] / s["total"] * 100, 2) if s["total"] > 0 else 0
        cancel_rate = round(s["cancelled"] / s["total"] * 100, 2) if s["total"] > 0 else 0
        room_stats.append(RoomUtilization(
            room_id=room.id,
            room_name=room.name,
            capacity=room.capacity,
            total_bookings=s["total"],
            checked_in_bookings=s["checked_in"],
            cancelled_bookings=s["cancelled"],
            total_booked_minutes=s["booked_minutes"],
            actual_used_minutes=s["used_minutes"],
            utilization_rate=utilization_rate,
            check_in_rate=check_in_rate,
            cancel_rate=cancel_rate,
        ))

    room_stats.sort(key=lambda x: x.utilization_rate, reverse=True)

    total_bookings = sum(s.total_bookings for s in room_stats)
    total_used = sum(s.actual_used_minutes for s in room_stats)
    avg_util = round(sum(s.utilization_rate for s in room_stats) / len(room_stats), 2) if room_stats else 0
    summary = {
        "total_bookings": float(total_bookings),
        "total_used_minutes": float(total_used),
        "average_utilization_rate": avg_util,
        "total_rooms": float(len(room_stats)),
    }

    return UtilizationResponse(
        period=period,
        start_date=start.isoformat(),
        end_date=end.isoformat(),
        rooms=room_stats,
        summary=summary,
    )


@router.get("/hourly", response_model=HourlyStatsResponse)
def get_hourly_stats(
    period: str = Query("30d", pattern="^(7d|30d|90d|custom)$"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    room_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    period, start, end = resolve_period(period, start_date, end_date)

    query = db.query(func.extract("hour", Booking.start_time).label("hour"),
                     func.count(Booking.id).label("count")).filter(
        and_(
            Booking.start_time >= start,
            Booking.start_time <= end,
            Booking.is_cancelled == False,
        )
    )
    if room_id:
        query = query.filter(Booking.room_id == room_id)

    rows = query.group_by(func.extract("hour", Booking.start_time)).all()
    row_map = {int(h): int(c) for h, c in rows}
    hourly = [HourlyBookingStat(hour=h, count=row_map.get(h, 0)) for h in range(0, 24)]

    return HourlyStatsResponse(
        period=period,
        start_date=start.isoformat(),
        end_date=end.isoformat(),
        hourly=hourly,
    )


@router.get("/daily", response_model=DailyStatsResponse)
def get_daily_stats(
    period: str = Query("30d", pattern="^(7d|30d|90d|custom)$"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    room_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    period, start, end = resolve_period(period, start_date, end_date)

    query = db.query(
        func.date(Booking.start_time).label("date"),
        func.count(Booking.id).label("count"),
        func.sum(func.extract("epoch", Booking.end_time - Booking.start_time) / 60).label("total_minutes"),
    ).filter(
        and_(
            Booking.start_time >= start,
            Booking.start_time <= end,
            Booking.is_cancelled == False,
        )
    )
    if room_id:
        query = query.filter(Booking.room_id == room_id)

    rows = query.group_by(func.date(Booking.start_time)).order_by("date").all()
    daily = [DailyBookingStat(
        date=r.date.isoformat() if hasattr(r.date, "isoformat") else str(r.date),
        count=int(r.count or 0),
        total_minutes=int(r.total_minutes or 0),
    ) for r in rows]

    return DailyStatsResponse(
        period=period,
        start_date=start.isoformat(),
        end_date=end.isoformat(),
        daily=daily,
    )
