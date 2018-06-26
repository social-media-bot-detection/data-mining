FROM ubuntu:14.04
RUN echo "creating data-mining image..."
RUN mkdir mining
ADD tweet_mining.py mining/tweet_mining.py
ADD user_monitoring.py mining/user_monitoring.py
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
