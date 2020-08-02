FROM python:3.8

ARG SRC_DIR="./apps"
ARG DOCKER_DIR="./docker/responder"
ARG APP_DIR="/apps"

RUN mkdir ${APP_DIR}

ADD "${SRC_DIR}" "${APP_DIR}"

WORKDIR ${APP_DIR}

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    locales \
    ffmpeg \
 && apt-get -y clean \
 && rm -rf /var/lib/apt/lists/*

RUN echo "ja_JP UTF-8" > /etc/locale.gen
RUN locale-gen

RUN pip install --upgrade pip --no-cache-dir
RUN pip install -r requirements.txt --no-cache-dir

EXPOSE 5000

#CMD ["python", "run.py"]
