FROM python:3.7.4

MAINTAINER feiben <feiben.dev@gmail.com>

WORKDIR /app
COPY . /app

RUN cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && echo 'Asia/Shanghai' >/etc/timezone \
    && pip install -r requirements.txt

CMD ["python", "main.py"]
