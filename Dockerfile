FROM ubuntu:14.04
RUN echo "creating data-mining image..."
RUN mkdir mining
ADD twitter_mining.py mining/twitter_mining.py
ADD monitor_users.py mining/monitor_users.py
ADD config_secret.json mining/config_secret.json

RUN apt-get update
RUN apt-get -y install software-properties-common
RUN add-apt-repository ppa:jonathonf/python-2.7
RUN apt-get -y install python2.7
RUN apt-get -y install python-pip
RUN pip install --upgrade pip
RUN pip install --ignore-installed tweepy
RUN pip install unidecode
RUN pip install requests[security]
RUN apt-get install nano
