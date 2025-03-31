FROM python:3.11.5

WORKDIR orders_service/

COPY ./requirements.txt ./requirements.txt

RUN apt-get update && apt-get install -y netcat-openbsd
RUN pip install --upgrade -r ./requirements.txt

COPY . /orders_service

ENV PYTHONPATH=/app
ENV PYTHONPATH=/orders_service:$PYTHONPATH

RUN chmod +x /orders_service/entrypoint.sh

CMD ["/orders_service/entrypoint.sh"]
