FROM python:3.11.0-slim-buster
LABEL maintainer="job-seeker"

ENV PYTHONUNBUFFERED 1


WORKDIR app/

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

