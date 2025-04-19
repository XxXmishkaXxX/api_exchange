#!/bin/sh

wait_for_service() {
  local name="$1"
  local host="$2"
  local port="$3"

  echo "Ожидание доступности $name ($host:$port)..."
  until nc -z -v -w30 "$host" "$port"
  do
    echo "$name ($host:$port) пока недоступен, ждем..."
    sleep 1
  done
}

wait_for_service "Kafka" "kafka" 9092

exec python main.py
