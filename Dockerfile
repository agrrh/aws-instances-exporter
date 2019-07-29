FROM python:3-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip3 install -r requirements.txt

COPY . /app

CMD python3 main.py

ENV PYTHONUNBUFFERED true
ENV PYTHONDONTWRITEBYTECODE true
