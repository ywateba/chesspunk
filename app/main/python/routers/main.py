from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.db import models
from core.db.database import engine
from routers import auth, competitions, matches, users
from core.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup resources on App Startup (No automatic DB table generation)
    yield

app = FastAPI(title="Chess Community API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(competitions.router)
app.include_router(matches.router)
