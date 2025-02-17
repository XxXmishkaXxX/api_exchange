FROM python:3.11.5

WORKDIR /app

COPY ./requirements.txt ./requirements.txt

RUN pip install --upgrade -r ./requirements.txt

COPY . /app
