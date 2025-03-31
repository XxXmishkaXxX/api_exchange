FROM python:3.11.5

WORKDIR market_data_service/

COPY ./requirements.txt ./requirements.txt

RUN apt-get update && apt-get install -y netcat-openbsd

RUN pip install --upgrade -r ./requirements.txt

COPY . /market_data_service

ENV PYTHONPATH=/app
ENV PYTHONPATH=/market_data_service:$PYTHONPATH

RUN chmod +x /market_data_service/entrypoint.sh

CMD ["/market_data_service/entrypoint.sh"]