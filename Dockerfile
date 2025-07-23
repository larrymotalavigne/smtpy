FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get clean

# Install uv and Python dependencies first for better caching
COPY pyproject.toml uv.lock ./
RUN pip install uv
RUN uv sync --frozen

# Copy the rest of the application code
COPY . .

# Expose ports
EXPOSE 8000


CMD ["uvicorn", "main:create_app", "--host", "0.0.0.0", "--port", "8000", "--factory"]
