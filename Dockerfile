FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]"

COPY src/ ./src/
COPY data/ ./data/
COPY tests/ ./tests/

RUN pip install --no-cache-dir -e ".[dev]"

CMD ["uvicorn", "graphrag_agent.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
