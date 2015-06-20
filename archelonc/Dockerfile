FROM ubuntu:trusty
MAINTAINER Carson Gee <x@carsongee.com>

RUN apt-get update
RUN apt-get install python3 python3-dev python-dev python-pip -y
RUN pip install pip --upgrade

# Add, and run as, non-root user.
RUN adduser --disabled-password --gecos "" archelon

ADD . /app
WORKDIR /app

# Install app
RUN pip install -r requirements.txt

RUN chown -R archelon:archelon /app

# All built, now switch user and run
USER archelon
RUN echo "bind '\"\033a\":\". archelon\n\"'" >> ~/.bashrc
RUN touch ~/.bash_history

CMD /bin/bash
