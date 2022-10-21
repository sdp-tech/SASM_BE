FROM python:3
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
# 의존성 패키지 설치 및 삭제
RUN apk add --no-cache mariadb-connector-c-dev
RUN apk update && apk add python3 python3-dev mariadb-dev build-base && pip3 install mysqlclient && apk del python3-dev mariadb-dev build-base
RUN mkdir /srv/SASM_BE
ADD . /srv/SASM_BE

WORKDIR /srv/SASM_BE
COPY requirements.txt /srv/SASM_BE/requirements.txt
RUN python3 -m pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . /srv/SASM_BE/