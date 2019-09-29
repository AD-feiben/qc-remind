FROM python:3.7.4

MAINTAINER feiben <feiben.dev@gmail.com>

WORKDIR /app
COPY . /app

RUN pip install -r requirements.txt

CMD ["python", "main.py"]
