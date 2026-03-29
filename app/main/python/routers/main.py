from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
import os

from core.db import models
from core.db.database import engine
from core.db.documents import UserDocument, CompetitionDocument, MatchDocument
from routers import auth, competitions, matches, users
from core.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup resources on App Startup securely isolating Mongo vs SQL deployments dynamically
    if os.getenv("DB_ENGINE", "SQL") == "NOSQL":
        client = AsyncIOMotorClient(settings.NOSQL_DATABASE_URL)
        await init_beanie(database=client.chesspunk, document_models=[UserDocument, CompetitionDocument, MatchDocument])
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
