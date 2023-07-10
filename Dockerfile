FROM python:3.11
RUN apt-get update -y

RUN mkdir -p /root/.ssh
COPY id_ssh /root/.ssh/id_rsa

# git ssh key
RUN chmod 600 /root/.ssh/id_rsa \
    && chmod 700 /root/.ssh/id_rsa \
    && ls -l /root/.ssh \
    && ssh-keyscan github.com >> /root/.ssh/known_hosts

COPY . /app
RUN pip3 install -r /app/requirements.txt

WORKDIR /app

COPY ./compose/prod/django/start /start
RUN sed -i 's/\r//' /start
RUN chmod +x /start

ENTRYPOINT ["/start"]
