FROM python:3.10

RUN apt update && apt install -y npm python3-pip
COPY requirements.txt /apps/
RUN python -m pip install --no-cache-dir -r /apps/requirements.txt

ADD runtime /apps/runtime

ADD scripts /apps/scripts
RUN chmod +x /apps/scripts/*

ADD frontend2 /apps/frontend

RUN mkdir /data
ENV DATA_DIR=/data
ENV VIDEO_SERVICE_PORT=8000
ENV RUNTIME_SERVICE_PORT=8100
ENV MODEL_SERVICE_PORT=8200

WORKDIR /apps/frontend

RUN /apps/scripts/init.sh
ENTRYPOINT ["/apps/scripts/start.sh"]
