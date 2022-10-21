FROM nginx:1.19.0-alpine 
# nginx 베이스 이미지 지정

RUN rm /etc/nginx/conf.d/default.conf 
# 기존 설정 파일 지우고
COPY nginx.conf /etc/nginx/conf.d 
# 직접 설정한 nginx.conf 파일로 기존 설정 파일 대체