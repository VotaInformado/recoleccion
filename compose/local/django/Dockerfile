FROM python:3.10

ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt /requirements.txt
RUN pip install --no-cache-dir --upgrade pip
RUN pip -v install --no-cache-dir -r /requirements.txt

COPY ./compose/local/django/entrypoint /entrypoint
RUN sed -i 's/\r//' /entrypoint
RUN chmod +x /entrypoint

COPY ./compose/local/django/start /start
RUN sed -i 's/\r//' /start
RUN chmod +x /start

WORKDIR /app

ENTRYPOINT ["/entrypoint"]
