FROM python:3.11.5

WORKDIR wallet_service/

COPY ./requirements.txt ./requirements.txt

RUN apt-get update && apt-get install -y netcat-openbsd
RUN pip install --upgrade -r ./requirements.txt

COPY . /wallet_service

ENV PYTHONPATH=/app
ENV PYTHONPATH=/wallet_service:$PYTHONPATH

RUN chmod +x /wallet_service/entrypoint.sh

CMD ["/wallet_service/entrypoint.sh"]
