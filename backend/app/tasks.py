from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging
import os

from app.database import SessionLocal
from app.models import Booking

logger = logging.getLogger(__name__)

CHECKIN_TIMEOUT_MINUTES = int(os.getenv("CHECKIN_TIMEOUT_MINUTES", "15"))
TASK_INTERVAL_MINUTES = int(os.getenv("TASK_INTERVAL_MINUTES", "5"))


def cancel_expired_bookings():
    db: Session = SessionLocal()
    try:
        now = datetime.utcnow()
        cutoff_time = now - timedelta(minutes=CHECKIN_TIMEOUT_MINUTES)

        expired_bookings = db.query(Booking).filter(
            Booking.is_cancelled == False,
            Booking.is_checked_in == False,
            Booking.start_time <= cutoff_time,
            Booking.start_time > now - timedelta(hours=24)
        ).all()

        cancelled_count = 0
        for booking in expired_bookings:
            booking.is_cancelled = True
            booking.cancelled_at = now
            booking.auto_cancelled = True
            booking.cancel_reason = f"自动取消：预约开始后{CHECKIN_TIMEOUT_MINUTES}分钟内未签到"
            cancelled_count += 1

        if cancelled_count > 0:
            db.commit()
            logger.info(f"自动取消了 {cancelled_count} 个未签到的预约")

    except Exception as e:
        logger.error(f"自动取消预约任务执行失败: {str(e)}")
        db.rollback()
    finally:
        db.close()


scheduler = BackgroundScheduler()


def start_scheduler():
    if not scheduler.running:
        scheduler.add_job(
            cancel_expired_bookings,
            trigger=IntervalTrigger(minutes=TASK_INTERVAL_MINUTES),
            id="cancel_expired_bookings",
            replace_existing=True
        )
        scheduler.start()
        logger.info(f"定时任务调度器已启动，每 {TASK_INTERVAL_MINUTES} 分钟检查一次未签到预约")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        logger.info("定时任务调度器已停止")
