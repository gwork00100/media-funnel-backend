# ================================
# Blood — Central API (FastAPI)
# ================================

# Use official Python image with Debian base
FROM python:3.11-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    PATH="/root/.cargo/bin:$PATH" \
    BLOOD_NUM_WORKERS=2

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    git \
    libssl-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install Rust (required for some Python packages)
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y

# Set work directory
WORKDIR /app

# Copy dependency file first (for layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose the FastAPI port
EXPOSE 8000

# Healthcheck (optional but helpful)
HEALTHCHECK CMD curl --fail http://localhost:8000/health || exit 1

# Start the app with Uvicorn
# Using '--workers 1' ensures async queue stays event-loop consistent
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
