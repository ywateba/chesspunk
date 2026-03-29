"""
Main Router & FastApi Assembly
==============================
Initializes the core FastApi instance, builds the CORS architectures,
and bootstraps dynamic configuration properties (SQL vs NoSQL).
"""

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
    """
    Manage FastAPI startup constraints asynchronously.
    
    Seamlessly triggers native MongoDB collections building Beanie structures
    if the deployment explicitly defines NoSQL parameters. For standard SQL,
    the application passes safely without initialization logic.
    """
    if os.getenv("DB_ENGINE", "SQL") == "NOSQL":
        client = AsyncIOMotorClient(settings.NOSQL_DATABASE_URL)
        await init_beanie(database=client.chesspunk, document_models=[UserDocument, CompetitionDocument, MatchDocument])
    yield

# Instantiate Application
app = FastAPI(title="Chess Community API", lifespan=lifespan)

# Bind Security Layers
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect endpoint routing matrices
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(competitions.router)
app.include_router(matches.router)
