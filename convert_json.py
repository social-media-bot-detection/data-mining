import os
import json
# import fileinput
import sys
import csv

count = 0
tweets = {}
tweet_pairs = {}
abs_path = os.path.dirname(os.path.realpath(__file__)) + '/'
# input2 = fileinput.input()
for file in sys.argv[1:]:
    file = file.replace("\n", "")
    print "file: %s" % file
    with open(file, 'r') as json_data_file:
        data = json.load(json_data_file)

        for tweet in data:
            # print "\ttype: %s" % tweet['type']
            count += 1
            if tweet["type"] == "reply":
                print "replied text, %s: %s\n" % (str(tweet["id"]), tweet["text"])
                tweets[str(tweet["id"])] = tweet["text"]
                # tweets[tweet["replied_tweet_id"]] = tweet["replied_tweet_text"]
            elif tweet["type"] == "retweet":
                tweets[tweet["retweeted_tweet_id"]] = tweet["text"].split(":", 1)[1]
                print "retweeted text, %s: %s\n" % (tweet["retweeted_tweet_id"], tweet["text"].split(":", 1)[1][1:])
            elif tweet["type"] == "own":
                tweets[str(tweet["id"])] = tweet["text"]
                print "own text, %s: %s\n" % (str(tweet["id"]), tweet["text"])
replies = 0
print "-----------------------------------"
with open('csv/tweet_pairs.csv', 'wb') as f:
    writer = csv.writer(f)

    for file in sys.argv[1:]:
        file = file.replace("\n", "")
        print "file: %s" % file
        with open(file, 'r') as json_data_file2:
            data = json.load(json_data_file2)

            for tweet in data:
                # print "\ttype: %s" % tweet['type']
                if tweet["type"] == "reply":
                    if tweet["replied_tweet_id"] in tweets:
                        replies += 1
                        print "replied %s -> %s\n" % (tweets[tweet["replied_tweet_id"]], tweet["text"])
                        tweet_pairs[tweets[tweet["replied_tweet_id"]]] = tweet["text"]
                        writer.writerow([tweets[tweet["replied_tweet_id"]], tweet["text"]])
print "count: %d" % count
print "replies: %d" % replies
