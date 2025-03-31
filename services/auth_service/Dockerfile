FROM python:3.11.5

WORKDIR /auth_service

COPY ./requirements.txt ./requirements.txt

RUN apt-get update && apt-get install -y netcat-openbsd
RUN pip install --upgrade -r ./requirements.txt

COPY . /auth_service

ENV PYTHONPATH=/app
ENV PYTHONPATH=/auth_service:$PYTHONPATH

RUN chmod +x /auth_service/entrypoint.sh

CMD ["/auth_service/entrypoint.sh"]


