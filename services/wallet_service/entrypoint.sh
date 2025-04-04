#!/bin/sh

# Функция ожидания доступности базы данных
wait_for_db() {
  echo "Ожидание доступности БД $1..."
  until nc -z -v -w30 $1 5432
  do
    echo "Ожидание БД $1..."
    sleep 1
  done
}


wait_for_db wallet_db

if [ -z "$(ls -A migrations/versions/ 2>/dev/null)" ]; then
  echo "Миграции не найдены, создаем первую миграцию..."
  alembic revision --autogenerate -m "Initial migration"
fi


alembic upgrade head

exec uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
