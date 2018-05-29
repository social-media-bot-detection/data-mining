import tweepy  # https://github.com/tweepy/tweepy
import sys
import os
import json
from unidecode import unidecode
import csv
import re


# Configuration file
abs_path = os.path.dirname(os.path.realpath(__file__)) + '/'
with open("config_secret.json") as json_data_file:
    data = json.load(json_data_file)


# Twitter API credentials
CONSUMER_KEY = data["consumer_key"]
CONSUMER_SECRET = data["consumer_secret"]
ACCESS_KEY = data["access_key"]
ACCESS_SECRET = data["access_secret"]

# authorize twitter, initialize tweepy
auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True, compression=True)

emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                           "]+", flags=re.UNICODE)


def file_exists(file_path):
    return os.path.exists(file_path)


def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if not file_exists(directory):
        os.makedirs(directory)
        if(file_path == 'csv/'):
            with open('csv/all_users_info.csv', 'wb') as f:
                writer = csv.writer(f)
                writer.writerow(["screen_name", "description", "followers", "following", "profile_image_url", "location", "verified", "created_at"])
            pass
            f.close()


def handle_limit(cursor):
    while True:
        try:
            yield cursor.next()
        except tweepy.RateLimitError:
            # time.sleep(15 * 60)  # wait encouraged 15 minutes
            print ("Rate limit reached!")
            break


def get_user_info(screen_name):
    user = api.get_user(screen_name)
    screen_name = user.screen_name
    description = unidecode(emoji_pattern.sub(r'', user.description))  # no emoji nor accents
    followers = user.followers_count
    following = user.friends_count
    profile_image_url = user.profile_image_url.replace("normal", "200x200")
    location = unidecode(user.location)
    verified = user.verified
    created_at = user.created_at

    print("screen name: %s" % screen_name)
    print("created at: %s" % created_at)
    print("followers: %s" % followers)
    print("following: %s" % following)
    print("image url: %s" % profile_image_url)
    print("location: %s" % location)
    print("verified: %s" % verified)

    with open('csv/all_users_info.csv', 'a+') as f:
        writer = csv.writer(f)
        writer.writerow([screen_name, description, followers, following, profile_image_url, location, verified, created_at])
    pass
    f.close()


def get_all_tweets(screen_name):
    # Twitter only allows access to a users most recent 3240 tweets with this method
    print ("getting all tweets from %s into csv file..." % screen_name)

    # initialize a list to hold all the tweepy Tweets
    alltweets = []
    # make initial request for most recent tweets (200 is the maximum allowed count)
    new_tweets = api.user_timeline(screen_name=screen_name, count=200)
    # save most recent tweets
    alltweets.extend(new_tweets)
    # save the id of the oldest tweet less one
    oldest = alltweets[-1].id - 1
    # keep grabbing tweets until there are no tweets left to grab
    while len(new_tweets) > 0:
        # print "getting tweets before %s" % (oldest)

        # all subsiquent requests use the max_id param to prevent duplicates
        new_tweets = api.user_timeline(screen_name=screen_name, count=200, max_id=oldest)
        # save most recent tweets
        alltweets.extend(new_tweets)
        # update the id of the oldest tweet less one
        oldest = alltweets[-1].id - 1

        # print "...%s tweets downloaded so far" % (len(alltweets))

    # transform the tweepy tweets into a 2D array that will populate the csv
    outtweets = [[tweet.id_str, tweet.created_at, tweet.retweet_count, tweet.favorite_count, tweet.text.encode("utf-8")] for tweet in alltweets]
    # print dir(tweet.entities)
    hashtags_file = open("txt/"+screen_name+"_hashtags_only.txt", "w")
    for tweet in alltweets:
        # print " HASHTAGS: "+str(tweet.entities['hashtags'])
        hashtags = tweet.entities['hashtags']
        for hashtag in hashtags:
            print ("   #"+hashtag['text'])
            hashtags_file.write(unidecode(hashtag['text'])+"\n")
    hashtags_file.close()

    # write the csv
    with open('csv/'+'%s_tweets.csv' % screen_name, 'wb') as f:
        writer = csv.writer(f)
        writer.writerow(["id", "created_at", "retweets", "favorites", "text"])
        writer.writerows(outtweets)
    pass
    f.close()


if __name__ == '__main__':
    # pass in the username of the account you want to analyze
    ensure_dir("csv/")
    ensure_dir("txt/")
    screen_name = sys.argv[1]
    if not file_exists("csv/"+'%s_tweets.csv' % screen_name):
        get_user_info(screen_name)
        get_all_tweets(screen_name)
