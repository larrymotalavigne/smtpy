# Setup & Installation

## Prerequisites
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- Docker (optional, for containerized deployment)

## Local Setup
```bash
uv sync
uvicorn main:create_app --reload --factory
```

## Docker
```bash
docker build -t smtpy .
docker run -p 8000:8000 smtpy
```

## Environment Variables
- `SMTPY_DB_PATH`: Path to the SQLite database file (default: `smtpy.db`) 