from fastapi import FastAPI
import uvicorn

from db import models
from db.database import engine, Base
from routers import user_router, player_router, competition_router, match_router

# Create the database tables
Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Chess Community API",
    description="API for managing chess community games.",
    version="1.0.0",
    prefix="/"
)

# Include Routers
app.include_router(user_router.router)
app.include_router(player_router.router)
app.include_router(competition_router.router)
app.include_router(match_router.router)

