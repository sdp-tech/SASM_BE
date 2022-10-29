# pull official base image
FROM python:3.10-alpine as builder
# 의존성 패키지 설치 및 삭제
RUN apk update && apk add python3 python3-dev mariadb-dev build-base && pip3 install mysqlclient && apk del python3-dev mariadb-dev build-base
RUN apk add --no-cache gcc musl-dev python3-dev
RUN pip install ruamel.yaml.clib
RUN mkdir /home/ubuntu/SASM_BE
WORKDIR /home/ubuntu/SASM_BE
COPY requirements.txt /home/ubuntu/SASM_BE/requirements.txt
RUN python3 -m pip install --upgrade pip
RUN pip install -r requirements.txt
COPY . /home/ubuntu/SASM_BE/
