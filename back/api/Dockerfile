FROM python:3.14-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get clean

# Install uv and Python dependencies first for better caching
COPY ./pyproject.toml ./uv.lock ./
RUN pip install uv
RUN uv sync --frozen

# Ensure the virtual environment is in PATH
ENV PATH="/app/.venv/bin:$PATH"

# Copy the rest of the application code
COPY ./back/api .

# Copy Alembic migration files (from back/ directory)
COPY ./back/alembic.ini ./alembic.ini
COPY ./back/alembic ./alembic

# Expose API port only
EXPOSE 8000

CMD ["uvicorn", "main:create_app", "--host", "0.0.0.0", "--port", "8000", "--factory"]