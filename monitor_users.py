import sys
import os
import csv
import json
import tweepy
import atexit
import time
import re
from unidecode import unidecode


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

output_file = None
output_file_name = ""


def file_exists(file_path):
    return os.path.exists(file_path)


def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if not file_exists(directory):
        os.makedirs(directory)


def open_file(screen_name):
    global output_file_name
    global output_file
    output_file_name = 'json/' + screen_name + 'followers.' + time.strftime('%Y%m%d-%H%M%S') + '.json'
    output_file = open(output_file_name, 'w')
    output_file.write('[')


def close_file():
    print("===== Exiting Program =====")
    global output_file
    output_file.write(']')
    output_file.close()


class Follower:
    def __init__(self, screen_name, id, description, followers, following,
                profile_image_url, location, verified, created_at):
        self.screen_name = screen_name
        self.id = id
        self.description = description
        self.followers = followers
        self.following = following
        self.profile_image_url = profile_image_url
        self.location = location
        self.verified = verified
        self.created_at = created_at


def get_all_followers(screen_name):
    num_follower = 0
    global output_file_name
    global output_file
    open_file(screen_name)
    atexit.register(close_file)
    first = True
    for follower in tweepy.Cursor(api.followers, screen_name=screen_name).items():
        num_follower += 1
        if(num_follower >= 20000):
            num_follower = 1
            close_file()
            open_file(screen_name)
        print "#%d %s <- %s" % (num_follower, screen_name, follower.screen_name)
        user = api.get_user(follower.screen_name)
        id = user.id_str
        description = unidecode(emoji_pattern.sub(r'', user.description))  # no emoji nor accents
        followers = user.followers_count
        following = user.friends_count
        profile_image_url = user.profile_image_url.replace("normal", "200x200")
        location = unidecode(user.location)
        verified = user.verified
        created_at = str(user.created_at)

        follower_saved = Follower(
            screen_name=follower.screen_name, id=id, description=description,
            followers=followers, following=following,
            profile_image_url=profile_image_url, location=location,
            verified=verified, created_at=created_at
        )
        if first:
            output_file.write(json.dumps(follower_saved.__dict__))
            first = False
        else:
            output_file.write(",\n\n" + json.dumps(follower_saved.__dict__))


def real_screen_name(screen_name):
    return api.get_user(screen_name).screen_name


def real_user_id(screen_name):
    return api.get_user(screen_name).id_str


if __name__ == '__main__':
    # pass in the username(s) of the account(s) you want to monitor
    ensure_dir("json/")
    users = sys.argv[1:]
    for user in users:
        print "===== Examining %s =====" % user

        screen_name = real_screen_name(user)
        get_all_followers(screen_name)
