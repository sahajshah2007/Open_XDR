FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for postgres client (psycopg2)
RUN apt-get update && apt-get install -y libpq-dev gcc netcat-traditional && rm -rf /var/lib/apt/lists/*

COPY requirements.lock .
RUN pip install --no-cache-dir -r requirements.lock

COPY . .

# Make the start script executable
RUN chmod +x start.sh

CMD ["./start.sh"]
