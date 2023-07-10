# FROM python:3.11

# ENV PYTHONUNBUFFERED 1

# # git ssh key
# RUN --mount=type=secret,id=ssh_private_key \
#     mkdir -p /root/.ssh \
#     && cp /run/secrets/ssh_private_key /root/.ssh/id_rsa \
#     && chmod 600 /root/.ssh/id_rsa \
#     && chmod 700 /root/.ssh/id_rsa \
#     && ls -l /root/.ssh \
#     && ssh-keyscan github.com >> /root/.ssh/known_hosts

# RUN apt-get update \
#   && apt-get install -y git \
#   && apt-get clean

# COPY ./requirements /requirements
# RUN pip -v install --no-cache-dir -r /requirements/base.txt

# COPY ./compose/local/django/start /start
# RUN sed -i 's/\r//' /start
# RUN chmod +x /start

# WORKDIR /app

# # ARG CACHEBUST
# # ENV CACHEBUST=$CACHEBUST
# # RUN echo "CACHEBUST value: $CACHEBUST"

# # RUN pip install --no-cache-dir -r /requirements/extra.txt

# ENTRYPOINT ["/start"]

FROM python:3.10.11
RUN apt-get update -y

# git ssh key
RUN mkdir -p ~/.ssh \
    cp $SSH_PRIVATE_KEY /root/.ssh/id_ssh \
    && chmod 600 /root/.ssh/id_ssh \
    && chmod 700 /root/.ssh \
    && ls -l /root/.ssh \
    && ssh-keyscan github.com >> /root/.ssh/known_hosts


COPY . /app
RUN pip3 install -r /app/requirements.txt

RUN chmod +x /app/start_app.sh

WORKDIR /app

ENTRYPOINT ["/app/start_app.sh"]
