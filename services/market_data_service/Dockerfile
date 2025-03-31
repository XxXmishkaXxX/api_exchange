FROM python:3.11.5

WORKDIR market_data_service/

COPY ./requirements.txt ./requirements.txt

RUN pip install --upgrade -r ./requirements.txt

COPY . /market_data_service

ENV PYTHONPATH=/app
ENV PYTHONPATH=/market_data_service:$PYTHONPATH