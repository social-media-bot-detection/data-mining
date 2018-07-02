# data-mining
Collection of files to collect social media data from users.

# About
The purpose of the scripts included here is to gather data from any particular Twitter account regarding their activity and interaction with other users. Among the information gathered is: followers, following, tweet content, frequency and timing, hashtags, mentions and replies.

## tweet_mining.py
This script allows for data mining of any particular user(s) about their profile metadata and their tweets. </br>
</br>
For each user passed in as argument (twitter handle, without _@_), it will save the following information into a file, _all_users_info.csv_: screen name, id, description, followers, following, profile image url, location, profile verification and the account creation date. </br>
Another file will also be created, <_username_>__tweets.csv_, with the following information about each user's tweets: tweet id, tweet date, retweets, favorites, from whom it's retweeted (if so), in reply to (if so), source and of course the tweet's content. </br>
</br>
Then, it will begin to stream in realtime any of the following events (regarding any of the users passed in as arguments):

- Tweets created by the user.
- Tweets which are retweeted by the user.
- Replies to any tweet created by the user.
- Retweets of any tweet created by the user.
- Manual replies, created without pressing a reply button (e.g. “@twitterapi I agree”).

## user_monitoring.py
This script allows for realtime monitoring of new followers for any particular Twitter account. The way this is done is by requesting the Twitter API the latest 100 followers of the user passed in as argument (twitter handle, without _@_), every 60 seconds. For every scan, it compares the list of followers to the ones obtained in the previous scan and finds new ones. For every new follower found, it retrieves the following information: screen name, id, description, followers, following, profile image url,  tweet count, location, account creation date, date on which follow was discovered and profile verification.

# Usage
First thing you have to do is add your own keys to _config_secret.json_, otherwise you can't use the Twitter API. </br>
</br>
All requirements to run these programs have been put together in a Docker image, which can easily be built with the following command:
```
docker build -t <name-of-your-image> .
```
This will take a few minutes. Then, you can run the resulting image with:
```
docker run -ti <name-of-your-image> bash
```
which will get you right into the prompt ```root@<container-id>:/#```. From here on, you can just switch to the _mining_ directory and run the program you prefer:
```
cd mining/
python tweet_mining.py config_secret.json (<username-1> <username-2> <username-3> ...)
python user_monitoring.py config_secret.json <username>
