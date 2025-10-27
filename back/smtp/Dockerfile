FROM python:3.14-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get clean

# Install uv and Python dependencies first for better caching
COPY ./pyproject.toml ./uv.lock ./
RUN pip install uv
RUN uv sync --frozen

# Ensure the virtual environment is in PATH and set PYTHONPATH
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app"

# Copy the application code into 'smtp' subdirectory
COPY ./back/smtp ./smtp

# Copy shared 'core' module from API (SMTP depends on core.database, core.utils, core.config)
COPY ./back/api/core ./core

# Expose SMTP port only
EXPOSE 1025

CMD ["python", "smtp/main.py"]