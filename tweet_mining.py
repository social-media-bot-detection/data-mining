import tweepy  # https://github.com/tweepy/tweepy
import sys
import os
import json
from unidecode import unidecode
import csv
import re
import time
import atexit
import requests
from py2neo import Graph, authenticate
from user_monitoring import User
import operator


emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                           "]+", flags=re.UNICODE)
add_user_url = "http://localhost:80/add_user"
add_tweet_url = "http://localhost:80/add_tweet"
reload(sys)
sys.setdefaultencoding('utf8')

num_tweets = {}
errors = 0


def file_exists(file_path):
    return os.path.exists(file_path)


def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if not file_exists(directory):
        os.makedirs(directory)
        if(file_path == 'csv/'):
            with open('csv/all_users_info.csv', 'wb') as f:
                writer = csv.writer(f)
                writer.writerow(["screen_name", "id", "description", "followers", "following", "profile_image_url", "location", "verified", "created_at"])
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


def real_screen_name(screen_name):
    return api.get_user(screen_name).screen_name

def real_user_id(screen_name):
    return api.get_user(screen_name).id_str


def get_user_info(screen_name):
    user = api.get_user(screen_name)
    screen_name = user.screen_name
    id = user.id_str
    description = unidecode(emoji_pattern.sub(r'', user.description))  # no emoji nor accents
    followers = user.followers_count
    following = user.friends_count
    profile_image_url = user.profile_image_url.replace("normal", "200x200")
    location = unidecode(user.location)
    verified = user.verified
    created_at = str(user.created_at)

    print("screen name: %s" % screen_name)
    print("id: %s" % id)
    print("created at: %s" % created_at)
    print("followers: %s" % followers)
    print("following: %s" % following)
    print("image url: %s" % profile_image_url)
    print("location: %s" % location)
    print("verified: %s" % verified)

    target = User(
        screen_name=screen_name, id=id, description=description,
        followers=followers, following=following,
        profile_image_url=profile_image_url, location=location,
        verified=verified, created_at=created_at,
        followed_at=""
    )
    resp = requests.post(add_user_url,
        headers={'Content-Type': 'application/json'},
        data=json.dumps(target.__dict__),
        params={"target": screen_name, "type": ":Origin"}, verify=False)
    print resp.text

    with open('csv/all_users_info.csv', 'a+') as f:
        writer = csv.writer(f)
        writer.writerow([screen_name, id, description, followers, following, profile_image_url, location, verified, created_at])
    pass
    f.close()


class Tweet:
    def __init__(self, id, id_str, created_at, source, retweet_count, favorite_count, retweeted_from, in_reply_to_screen_name, text, entities):
        self.id = id
        self.id_str = id_str
        self.created_at =  created_at
        self.source = source
        self.retweet_count = retweet_count
        self.favorite_count = favorite_count
        self.retweeted_from = retweeted_from
        self.in_reply_to_screen_name = in_reply_to_screen_name
        self.text = text.encode("utf-8")
        self.entities = entities


def get_all_tweets(screen_name):
    # Twitter only allows access to a users most recent 3240 tweets with this method
    print ("getting all tweets from %s into csv file..." % screen_name)

    # initialize a list to hold all the tweepy Tweets
    alltweets = []
    # make initial request for most recent tweets (200 is the maximum allowed count)
    new_tweets = api.user_timeline(screen_name=screen_name, count=200)
    # save most recent tweets
    for tweet in new_tweets:
        if hasattr(tweet, 'retweeted_status'):
            print "RT a tweet from @%s: %s" % (tweet.retweeted_status.user.screen_name.encode('utf-8'), emoji_pattern.sub(r'', tweet.text.encode('utf-8', errors='replace')))
            alltweets.append(Tweet(tweet.id, tweet.id_str, tweet.created_at, tweet.source, tweet.retweet_count, tweet.favorite_count, tweet.retweeted_status.user.screen_name, tweet.in_reply_to_screen_name, emoji_pattern.sub(r'', tweet.text).encode('utf-8', errors='replace'), tweet.entities))
        else:
            alltweets.append(Tweet(tweet.id, tweet.id_str, tweet.created_at, tweet.source, tweet.retweet_count, tweet.favorite_count, " ", tweet.in_reply_to_screen_name, emoji_pattern.sub(r'', tweet.text).encode('utf-8', errors='replace'), tweet.entities))
        if tweet.in_reply_to_screen_name is not None:
            print "replied a tweet to @%s: %s" % (tweet.in_reply_to_screen_name.encode('utf-8'), emoji_pattern.sub(r'', tweet.text.encode('utf-8', errors='replace')))
    # save the id of the oldest tweet less one
    oldest = alltweets[-1].id - 1
    # keep grabbing tweets until there are no tweets left to grab
    while len(new_tweets) > 0:
        # print "getting tweets before %s" % (oldest)

        # all subsiquent requests use the max_id param to prevent duplicates
        new_tweets = api.user_timeline(screen_name=screen_name, count=200, max_id=oldest)
        # save most recent tweets
        for tweet in new_tweets:
            if hasattr(tweet, 'retweeted_status'):
                print "RT a tweet from @%s: %s" % (tweet.retweeted_status.user.screen_name.encode('utf-8'), emoji_pattern.sub(r'', tweet.text).encode('utf-8', errors='replace'))
                alltweets.append(Tweet(tweet.id, tweet.id_str, tweet.created_at, tweet.source, tweet.retweet_count, tweet.favorite_count, tweet.retweeted_status.user.screen_name, tweet.in_reply_to_screen_name, emoji_pattern.sub(r'', tweet.text).encode('utf-8', errors='replace'), tweet.entities))
            else:
                alltweets.append(Tweet(tweet.id, tweet.id_str, tweet.created_at, tweet.source, tweet.retweet_count, tweet.favorite_count, "", tweet.in_reply_to_screen_name, emoji_pattern.sub(r'', tweet.text).encode('utf-8', errors='replace'), tweet.entities))
            if tweet.in_reply_to_screen_name is not None:
                print "replied a tweet to @%s: %s" % (tweet.in_reply_to_screen_name.encode('utf-8'), emoji_pattern.sub(r'', tweet.text).encode('utf-8', errors='replace'))
        # update the id of the oldest tweet less one
        oldest = alltweets[-1].id - 1

        # print "...%s tweets downloaded so far" % (len(alltweets))

    # transform the tweepy tweets into a 2D array that will populate the csv
    outtweets = [[tweet.id_str, tweet.created_at, tweet.retweet_count, tweet.favorite_count, tweet.retweeted_from, tweet.in_reply_to_screen_name, tweet.source, tweet.text] for tweet in alltweets]
    # print dir(tweet.entities)
    hashtags_file = open("txt/"+screen_name+"_hashtags_only.txt", "w")
    for tweet in alltweets:
        has_hashtags = False
        # print " HASHTAGS: "+str(tweet.entities['hashtags'])
        hashtags = tweet.entities['hashtags']
        for hashtag in hashtags:
            has_hashtags = True
            # print ("   #"+hashtag['text'])
            hashtags_file.write(unidecode(hashtag['text'])+" ")
        if has_hashtags:
            hashtags_file.write("\n")
    hashtags_file.close()

    # write the csv
    with open('csv/'+'%s_tweets.csv' % screen_name, 'wb') as f:
        writer = csv.writer(f)
        writer.writerow(["id", "created_at", "retweets", "favorites", "retweeted_from", "in_reply_to", "source", "text"])
        writer.writerows(outtweets)
    pass
    f.close()


def get_tweets_mentioned_in(screen_name):
    search_query = '@%s -filter:retweets' % screen_name
    tweets = api.search(q=search_query)
    for tweet in tweets:
        print "@%s %s: %s\n" % (screen_name.encode('utf-8'), tweet.author.screen_name.encode('utf-8'), emoji_pattern.sub(r'', tweet.text.encode('utf-8')))


output_file_name = ""


def close_file():
    print("===== Exiting Program =====")
    myStreamListener.output.write(']')
    myStreamListener.output.close()


class SavedTweet:
    def __init__(self, id, text, type, author, author_joined_on, created_at, source,
                retweeted_from_screen_name, retweeted_tweet_id, retweeted_tweet_date,
                in_reply_to_screen_name, replied_tweet_id, replied_tweet_date,
                replied_tweet_text, hashtags):
        self.id = id
        self.text = text.encode("utf-8")
        self.type = type
        self.author = author
        self.author_joined_on = author_joined_on
        self.created_at = created_at
        self.source = source
        self.retweeted_from_screen_name = retweeted_from_screen_name
        self.retweeted_tweet_id = retweeted_tweet_id
        self.retweeted_tweet_date = retweeted_tweet_date
        self.in_reply_to_screen_name = in_reply_to_screen_name
        self.replied_tweet_id = replied_tweet_id
        self.replied_tweet_date = replied_tweet_date
        self.replied_tweet_text = replied_tweet_text
        self.hashtags = hashtags


class MyStreamListener(tweepy.StreamListener):
    def __init__(self, api, users):
        print("===== Realtime Streaming =====")
        self.api = api
        self.users = users
        self.counter = 0
        self.first = True
        global output_file_name
        output_file_name = 'json/output.' + time.strftime('%Y%m%d-%H%M%S') + '.json'
        self.output = open(output_file_name, 'w')
        self.output.write('[')
        atexit.register(close_file)

    def on_status(self, status):
        # When a tweet is published it arrives here.
        type = "?"
        retweeted_from_screen_name = ""
        retweeted_tweet_id = "-1"
        retweeted_tweet_date = ""
        in_reply_to_screen_name = ""
        replied_tweet_id = "-1"
        replied_tweet_date = ""
        replied_tweet_text = ""

        self.counter += 1
        if self.counter >= 20000:
            self.output.write(']')
            self.output.close()
            output_file_name = 'json/output.' + time.strftime('%Y%m%d-%H%M%S') + '.json'
            self.output = open(output_file_name, 'w')
            self.output.write('[')
            self.counter = 0
            self.first = True

        global num_tweets
        print "author: " + status.author.screen_name
        print "joined on: " + str(status.author.created_at)
        if hasattr(status, 'retweeted_status'):
            type = "retweet"
            print "RT'ed from @%s, id %s, date %s" % (status.retweeted_status.user.screen_name, status.retweeted_status.id_str, status.retweeted_status.created_at)
            retweeted_from_screen_name = status.retweeted_status.user.screen_name
            retweeted_tweet_id = status.retweeted_status.id_str
            retweeted_tweet_date = str(status.retweeted_status.created_at)
            if retweeted_from_screen_name in num_tweets:
                num_tweets[retweeted_from_screen_name] += 1
            else:
                num_tweets[retweeted_from_screen_name] = 1
        elif status.in_reply_to_screen_name is not None and status.in_reply_to_status_id is not None:
            type = "reply"
            replied_tweet = api.get_status(status.in_reply_to_status_id_str)
            print "replied a tweet to @%s, id %s, date %s -> %s" % (status.in_reply_to_screen_name, status.in_reply_to_status_id_str, replied_tweet.created_at, unidecode(emoji_pattern.sub(r'', replied_tweet.text)))
            in_reply_to_screen_name = status.in_reply_to_screen_name
            replied_tweet_id = status.in_reply_to_status_id_str
            replied_tweet_date = str(replied_tweet.created_at)
            replied_tweet_text = unidecode(emoji_pattern.sub(r'', replied_tweet.text))
            if in_reply_to_screen_name in num_tweets:
                num_tweets[in_reply_to_screen_name] += 1
            else:
                num_tweets[in_reply_to_screen_name] = 1
        else:
            type = "own"
            if status.author.screen_name in num_tweets:
                num_tweets[status.author.screen_name] += 1
            else:
                num_tweets[status.author.screen_name] = 1
        print "src: " + unidecode(emoji_pattern.sub(r'', status.source))
        print "date: " + str(status.created_at)
        print "id: " + str(status.id_str)
        print "text: " + emoji_pattern.sub(r'', status.text).encode('utf-8', errors='replace')  # Console output may not be UTF-8
        hashtags = status.entities['hashtags']
        for hashtag in hashtags:
            print ("   #"+hashtag['text'].encode('utf-8'))
        print "errors: %d" % errors
        print "total_tweets: %d\ntweets_per_user..." % self.counter
        sorted_num_tweets = sorted(num_tweets.items(), key=operator.itemgetter(1), reverse=True)
        for real_username in sorted_num_tweets:
            real_username_string = real_username[0].encode('utf-8')
            # print "\t%s: %d" % (real_username_string, num_tweets[real_username_string])
            if real_username_string in self.users:
                print "\t%s: %d" % (real_username_string, num_tweets[real_username_string])
        tweet = SavedTweet(
            id=status.id_str, text=unidecode(emoji_pattern.sub(r'', status.text)).encode('utf-8', errors='replace'), type=type, author=status.author.screen_name,
            author_joined_on=str(status.author.created_at), created_at=str(status.created_at), source=status.source, retweeted_from_screen_name=retweeted_from_screen_name,
            retweeted_tweet_id=retweeted_tweet_id, retweeted_tweet_date=retweeted_tweet_date, in_reply_to_screen_name=in_reply_to_screen_name,
            replied_tweet_id=replied_tweet_id, replied_tweet_date=replied_tweet_date, replied_tweet_text=replied_tweet_text, hashtags=hashtags
        )
        if self.first:
            self.output.write(json.dumps(tweet.__dict__))
            self.first = False
        else:
            self.output.write(",\n\n" + json.dumps(tweet.__dict__))
        resp = requests.post(add_tweet_url, headers={'Content-Type': 'application/json'}, data=json.dumps(tweet.__dict__), verify=False)
        print resp.text
        print("-"*10)


if __name__ == '__main__':
    # pass in the configuration file
    abs_path = os.path.dirname(os.path.realpath(__file__)) + '/'
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
    # auth.secure = True
    api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True, compression=True)

    # pass in the username(s) of the account(s) you want to analyze
    ensure_dir("csv/")
    ensure_dir("txt/")
    ensure_dir("json/")
    users = sys.argv[2:]
    user_ids = []
    pos = 0
    global errors
    errors = 0
    global num_tweets
    for user in users:
        user_ids.append(real_user_id(user))
        print "===== Examining %s =====" % user
        screen_name = real_screen_name(user)
        num_tweets[screen_name] = 0
        users[pos] = screen_name
        if not file_exists("csv/"+'%s_tweets.csv' % screen_name):
            get_user_info(screen_name)
            get_all_tweets(screen_name)
            get_tweets_mentioned_in(screen_name)
        pos += 1

    # Connect to the stream
    myStreamListener = MyStreamListener(api=api, users=users)
    myStream = tweepy.Stream(auth=api.auth, listener=myStreamListener)
    try:
        myStream.filter(follow=user_ids)
    except tweepy.error.TweepError as e:
        print "===== ERROR =====\nreason: %s\nresponse: %s" % (
            e.reason, e.response
        )
        errors += 1
