FROM python:3.11-slim

WORKDIR /app

# Install dependencies first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# We don't define a CMD or ENTRYPOINT here because docker-compose 
# will specify a different command for each service (API, Worker, Scheduler).
