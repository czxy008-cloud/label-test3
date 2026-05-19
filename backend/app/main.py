from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.routers import auth, rooms, bookings

Base.metadata.create_all(bind=engine)

app = FastAPI(title="会议室预约系统 API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(rooms.router)
app.include_router(bookings.router)


@app.get("/")
def root():
    return {"message": "会议室预约系统 API"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
