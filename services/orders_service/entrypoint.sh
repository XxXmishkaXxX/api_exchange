#!/bin/sh

wait_for_service() {
  local name="$1"
  local host="$2"
  local port="$3"

  echo "Ожидание доступности $name ($host:$port)..."
  until nc -z -v -w30 "$host" "$port"
  do
    echo "$name ($host:$port) пока недоступен, ждем..."
    sleep 10
  done
}

wait_for_service "PostgreSQL" "orders_db" 5432

wait_for_service "Kafka" "kafka" 9092

if [ -z "$(ls -A migrations/versions/ 2>/dev/null)" ]; then
  echo "Миграции не найдены, создаем первую миграцию..."
  alembic revision --autogenerate -m "Initial migration"
fi

alembic upgrade head

exec uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload
