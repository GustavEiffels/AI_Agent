FROM python:3.10-slim-buster

WORKDIR /app

COPY ai_test/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ai_test 디렉토리의 모든 파일을 복사
COPY ai_test/ /app/

RUN mkdir -p /app/src/ai_test && touch /app/src/__init__.py /app/src/ai_test/__init__.py

ENV PYTHONPATH=/app
ENV FASTAPI_HOST=0.0.0.0
ENV FASTAPI_PORT=8000

CMD ["uvicorn", "src.ai_test.main:app", "--host", "0.0.0.0", "--port", "8000"]