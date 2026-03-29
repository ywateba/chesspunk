FROM python:3.10-slim

WORKDIR /app

# Install system dependencies required for PostgreSQL driver
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project code
COPY . .

# Ensure Python can resolve modules correctly
ENV PYTHONPATH=/app/main/python

# Configure the working directory specifically to execution root
WORKDIR /app

# Run Alembic migrations and then start the API locally resolving from --app-dir
CMD ["sh", "-c", "alembic upgrade head && uvicorn routers.main:app --app-dir /app/main/python --host 0.0.0.0 --port 8000"]