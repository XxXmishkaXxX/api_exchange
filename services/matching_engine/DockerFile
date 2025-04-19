FROM python:3.11

# Устанавливаем зависимости для Cython и компиляции
RUN apt-get update && apt-get install -y build-essential gcc && apt-get install -y netcat-openbsd

WORKDIR /app

# Копируем зависимости и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем файлы проекта
COPY . .

# Команда запуска контейнера
CMD ["bash", "-c", "./build.sh && ./entrypoint.sh"]
