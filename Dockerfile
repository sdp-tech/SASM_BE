FROM python:3.10
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
# pull official base image
FROM python:3.10-slim-buster as builder
# 의존성 패키지 설치 및 삭제
RUN apt-get update && apt-get install python3 python3-dev mariadb-dev build-essential && pip3 install mysqlclient && apt-get remove python3-dev mariadb-dev build-essential
RUN mkdir /srv/SASM_BE
ADD . /srv/SASM_BE

WORKDIR /srv/SASM_BE
COPY requirements.txt /srv/SASM_BE/requirements.txt
RUN python3 -m pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . /srv/SASM_BE/
