FROM python:3.13-slim

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
COPY . .

# Expose SMTP port only
EXPOSE 1025

CMD ["python", "main.py"]