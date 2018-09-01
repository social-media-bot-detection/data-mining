import os
import json
import sys

total_count = 0
abs_path = os.path.dirname(os.path.realpath(__file__)) + '/'
for file in sys.argv[1:]:
    count = 0
    file = file.replace("\n", "")
    print "file: %s" % file
    with open(file, 'r') as json_data_file:
        data = json.load(json_data_file)
        for tweet in data:
            # print "\ttype: %s" % tweet['type']
            if tweet['type'] == "reply" and "replied_tweet_text" in tweet:
                count += 1
    print "count: %d\n" % count
    total_count += count
print "total: %d" % total_count
