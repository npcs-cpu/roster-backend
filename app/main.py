from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.admin import router as admin_router
from app.api.calendar import router as calendar_router
from app.config import settings
from app.db import Base, engine

if settings.auto_create_tables:
    Base.metadata.create_all(bind=engine)

app = FastAPI(title="Roster SaaS API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(admin_router)
app.include_router(calendar_router)