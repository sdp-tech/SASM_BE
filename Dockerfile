FROM python:3.9
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
# pull official base image
FROM python:3.9-slim-buster as builder
# 의존성 패키지 설치 및 삭제
RUN apt-get update && apt-get upgrade -y
RUN apt-get install libmysqlclient-dev -y
RUN apt-get install mysql-client-core-5.6
RUN apt-get install python3.10-dev -y
RUN apt-get install gcc -y
RUN pip install mysqlclient
RUN mkdir /srv/SASM_BE
ADD . /srv/SASM_BE

WORKDIR /srv/SASM_BE
COPY requirements.txt /srv/SASM_BE/requirements.txt
RUN python3 -m pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . /srv/SASM_BE/
