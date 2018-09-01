import os
import json
from datetime import datetime
import re
from unidecode import unidecode
import sys
import csv
import tweepy

emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                           "]+", flags=re.UNICODE)

abs_path = os.path.dirname(os.path.realpath(__file__)) + '/'


def show_time_difference(first, second, message):
    first_date = datetime.strptime(
        first,
        '%Y-%m-%d %H:%M:%S'
    )
    second_date = datetime.strptime(
        second,
        '%Y-%m-%d %H:%M:%S'
    )
    date_delta = second_date - first_date
    # print "%d DAYS %d SECONDS" % (date_delta.days, date_delta.seconds)
    if(date_delta.days > 364):
        date_delta_text = "{0:.1f} YEARS".format(date_delta.days/365.00)
    elif(date_delta.days > 30):
        date_delta_text = "{0:.1f} MONTHS".format(date_delta.days/30.00)
    elif(date_delta.days > 0):  # more than a day
        date_delta_text = "%d DAYS" % date_delta.days
    elif(date_delta.seconds > 3599):  # more than an hour
        date_delta_text = "{0:.1f} HOURS".format(date_delta.seconds/3600)
    elif(date_delta.seconds > 59):  # more than a minute
        date_delta_text = "{0:.1f} MINUTES".format(date_delta.seconds/60)
    else:  # more than a second
        date_delta_text = "%d SECONDS" % date_delta.seconds
    print "%s%s" % (message, date_delta_text)


with open(sys.argv[1], 'r') as json_data_file:
    data = json.load(json_data_file)

# Twitter API credentials
CONSUMER_KEY = data["consumer_key"]
CONSUMER_SECRET = data["consumer_secret"]
ACCESS_KEY = data["access_key"]
ACCESS_SECRET = data["access_secret"]

# authorize twitter, initialize tweepy
auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
api = tweepy.API(
    auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True,
    compression=True
)

for file in sys.argv[2:]:
    count = 0
    bots_count = 0
    bots_tweet_num = []
    errors = 0
    errors_tweet_num = []
    file = file.replace("\n", "")
    print "file: %s" % file
    with open(file.replace(".json", '')+'_bots.csv', 'w') as output_file:
        writer = csv.writer(output_file)
        writer.writerow(['text', 'tweet_id', 'author', 'date', 'reason'])

        with open(file, 'r') as json_data_file:
            data = json.load(json_data_file)
            for tweet in data:
                # print "\ttype: %s" % tweet['type']
                if tweet['type'] == "reply" and "replied_tweet_text" in tweet:
                    count += 1
                    print "-------------------------------"
                    print "tweet #%d" % count
                    print "%d bots found -> %s" % (bots_count, bots_tweet_num)
                    print "%d errors -> %s" % (errors, errors_tweet_num)
                    print "text: %s" % unidecode(emoji_pattern.sub(r'', tweet['replied_tweet_text']))  # no emoji nor accents
                    print "author: %s" % tweet['in_reply_to_screen_name']
                    print "date: %s" % tweet['replied_tweet_date']
                    print "link: https://twitter.com/%s/status/%s\n" % (
                        tweet['in_reply_to_screen_name'],
                        tweet['replied_tweet_id']
                    )

                    print "reply: %s" % unidecode(emoji_pattern.sub(r'', tweet['text']))  # no emoji nor accents
                    print "author: %s" % tweet['author']
                    print "date: %s" % tweet['created_at']
                    print "link: https://twitter.com/%s/status/%d" % (
                        tweet['author'],
                        tweet['id']
                    )
                    print "profile: https://twitter.com/%s" % (
                        tweet['author']
                    )
                    print "src: %s" % unidecode(emoji_pattern.sub(r'', tweet['source']))  # no emoji nor accents
                    show_time_difference(
                        tweet['created_at'],
                        tweet['replied_tweet_date'],
                        "replied tweet in: "
                    )
                    print ""
                    try:
                        user = api.get_user(tweet['author'])
                        print tweet['author']
                        print "tweets: %d" % user.statuses_count
                        print "following: %d" % user.friends_count
                        print "followers: %d" % user.followers_count
                        print "description: %s" % unidecode(emoji_pattern.sub(r'', user.description))  # no emoji nor accents
                        # print "joined_on: %s" % user.created_at

                        show_time_difference(
                            str(user.created_at),
                            tweet['replied_tweet_date'],
                            "account age at tweet: "
                        )
                    except tweepy.error.TweepError as e:
                        print "===== ERROR =====\nreason: %s\nresponse: %s" % (
                            e.reason, e.response
                        )
                        errors += 1
                        errors_tweet_num.append('#' + str(count))

                    pressed = raw_input("\nis this bot-generated? ")
                    # print "you entered %s", pressed
                    if(pressed == "y"):
                        reason = raw_input("why? ")
                        writer.writerow([tweet['text'],
                                        tweet['id'],
                                        tweet['author'],
                                        tweet['created_at'],
                                        reason])
                        bots_count += 1
                        bots_tweet_num.append('#' + str(count))
                        print "tweet saved"
