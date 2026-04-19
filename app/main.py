from fastapi import FastAPI

from app.api.admin import router as admin_router
from app.api.calendar import router as calendar_router
from app.db import Base, engine


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Roster SaaS API", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(admin_router)
app.include_router(calendar_router)
