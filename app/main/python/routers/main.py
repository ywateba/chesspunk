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

from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from core.rate_limit import limiter
from core.middleware import SecurityHeadersMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from core.logger import setup_logging

setup_logging()

from core.db import models
from core.db.database import engine
from core.db.documents import UserDocument, CompetitionDocument, MatchDocument
from routers import auth, competitions, matches, users, communities
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
Instrumentator().instrument(app).expose(app)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "type": "about:blank"}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "type": "about:blank"}
    )

# Bind Security Layers
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SecurityHeadersMiddleware)

# Connect endpoint routing matrices
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(competitions.router)
app.include_router(matches.router)
app.include_router(communities.router)
