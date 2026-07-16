FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /app/requirements.txt

COPY alembic.ini /app/alembic.ini
COPY migrations /app/migrations
COPY system_under_test /app/system_under_test

RUN chmod +x /app/system_under_test/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/system_under_test/entrypoint.sh"]
