FROM python:3.11.5

WORKDIR /auth_service

COPY ./requirements.txt ./requirements.txt

RUN pip install --upgrade -r ./requirements.txt

COPY . /auth_service

ENV PYTHONPATH=/app
ENV PYTHONPATH=/auth_service:$PYTHONPATH


