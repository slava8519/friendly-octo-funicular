FROM ubuntu:trusty
RUN sudo apt-get -y update
RUN sudo apt-get -y upgrade
RUN sudo apt-get install -y sqlite3 libsqlite3-dev

FROM python:3.7
WORKDIR /app
ADD . /app
RUN python -mensurepip
RUN python setup.py develop

EXPOSE 8080