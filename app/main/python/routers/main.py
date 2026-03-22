from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.db import models
from core.db.database import engine
from routers import auth, competitions, matches, users



# Create the database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Chess Community API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"], # Common React/Vue default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(competitions.router)
app.include_router(matches.router)
