from app.routers.auth import router as auth_router
from app.routers.rooms import router as rooms_router
from app.routers.bookings import router as bookings_router
from app.routers.stats import router as stats_router

auth = auth_router
rooms = rooms_router
bookings = bookings_router
stats = stats_router

__all__ = ["auth", "rooms", "bookings", "stats"]
