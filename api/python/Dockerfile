FROM python:3.11-slim

WORKDIR /app

# Install system dependencies required for PostgreSQL driver
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project code
COPY . .

# Switch to the main directory so imports resolve correctly (e.g. `import models`)
WORKDIR /app/main

# Expose the port and start the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]