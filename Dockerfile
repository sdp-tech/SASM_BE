FROM python:3.10
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
# pull official base image
FROM python:3.10-slim-buster as builder
# 의존성 패키지 설치 및 삭제
RUN apt-get update && apt-get install python3 python3-dev build-essential
RUN apt-get install libssl1.1
RUN apt-get install libssl1.1=1.1.1f-1ubuntu2
RUN apt-get install libssl-dev
RUN apt-get install libmysqlclient-dev
RUN pip3 install mysqlclient
RUN mkdir /srv/SASM_BE
ADD . /srv/SASM_BE

WORKDIR /srv/SASM_BE
COPY requirements.txt /srv/SASM_BE/requirements.txt
RUN python3 -m pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . /srv/SASM_BE/
