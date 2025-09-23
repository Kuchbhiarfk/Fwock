FROM python:3.8-slim-buster

# Update apt sources to use Debian archive
RUN sed -i 's/deb.debian.org/archive.debian.org/g' /etc/apt/sources.list \
    && sed -i 's|security.debian.org/debian-security|archive.debian.org/debian-security|g' /etc/apt/sources.list \
    && echo "deb http://archive.debian.org/debian buster main" > /etc/apt/sources.list.d/buster.list \
    && apt-get update && apt-get upgrade -y

RUN apt-get install git -y
COPY requirements.txt /requirements.txt

RUN pip3 install -U pip && pip3 install -U -r requirements.txt
RUN mkdir /fwdbot
WORKDIR /fwdbot
COPY start.sh /start.sh
CMD ["/bin/bash", "/start.sh"]
