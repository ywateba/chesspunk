from fastapi import FastAPI
import uvicorn

from db import models
from db.database import engine, Base
from routers import user_router, player_router, competition_router, match_router

# Create the database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Chess Community API")

# Include Routers
app.include_router(user_router.router)
app.include_router(player_router.router)
app.include_router(competition_router.router)
app.include_router(match_router.router)

def main(host="0.0.0.0", port=8000):
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main(host="localhost", port=8001)
