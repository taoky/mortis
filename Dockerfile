# An example Dockerfile
FROM python:3.13-slim
ADD requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install -r requirements.txt
ADD . /app
