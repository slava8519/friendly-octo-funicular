FROM python:3.7
WORKDIR /app
ADD . /app
RUN python -mensurepip
RUN python setup.py develop

EXPOSE 8080
