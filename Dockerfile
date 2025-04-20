# Stage 1: builder
FROM python:3.12.3-slim AS builder
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install build dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --prefix /install -r requirements.txt

# Copy project files
COPY . .

# Stage 2: runtime
FROM python:3.12.3-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/install/bin:$PATH"

WORKDIR /app

# Copy installed dependencies and project files from builder
COPY --from=builder /install /install
COPY --from=builder /app /app

# Make sure entrypoint script is executable
RUN chmod +x ./entrypoint.sh

EXPOSE 8000

# Run the entrypoint
ENTRYPOINT ["./entrypoint.sh"] 