# Stage 1: builder
FROM python:3.13.3-slim AS builder
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
FROM python:3.13.3-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy installed dependencies into the system site-packages and bin
COPY --from=builder /install/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /install/bin /usr/local/bin

# Copy project files
COPY --from=builder /app /app

# Convert entrypoint.sh to Unix line endings and make it executable
RUN apt-get update \
    && apt-get install -y --no-install-recommends dos2unix \
    && dos2unix entrypoint.sh \
    && chmod +x entrypoint.sh

EXPOSE 8000

# Run the entrypoint
ENTRYPOINT ["./entrypoint.sh"] 