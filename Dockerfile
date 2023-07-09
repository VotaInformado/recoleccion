FROM python:3.10.11
RUN apt-get update -y


COPY requirements.txt /
RUN pip3 install -r /requirements.txt
COPY . /app

RUN chmod +x /app/start_app.sh

WORKDIR /app

ENTRYPOINT ["/app/start_app.sh"]
