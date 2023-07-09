FROM python:3.10.11
RUN apt-get update -y


COPY . /app
RUN pip3 install -r /app/requirements.txt

RUN chmod +x /app/start_app.sh

WORKDIR /app

ENTRYPOINT ["/app/start_app.sh"]
