FROM ubuntu:trusty
MAINTAINER Carson Gee <x@carsongee.com>

RUN apt-get update
RUN apt-get install python-dev python-pip -y
RUN pip install pip --upgrade

# Add, and run as, non-root user.
RUN adduser --disabled-password --gecos "" archelon

ADD . /app
WORKDIR /app

# Install app
RUN pip install -r requirements.txt
RUN pip install -r test_requirements.txt


RUN chown -R archelon:archelon /app

# All built, now switch user and run
USER archelon
ENV PORT 8580

EXPOSE $PORT

CMD uwsgi uwsgi.ini
