FROM python:3.11.5

WORKDIR orders_service/

COPY ./requirements.txt ./requirements.txt

RUN pip install --upgrade -r ./requirements.txt

COPY . /orders_service

ENV PYTHONPATH=/app
ENV PYTHONPATH=/orders_service:$PYTHONPATH