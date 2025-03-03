FROM python:3.11.5

WORKDIR wallet_service/

COPY ./requirements.txt ./requirements.txt

RUN pip install --upgrade -r ./requirements.txt

COPY . /wallet_service

ENV PYTHONPATH=/app
ENV PYTHONPATH=/wallet_service:$PYTHONPATH