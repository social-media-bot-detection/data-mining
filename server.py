from flask import *
from py2neo import Graph, authenticate, Path
import sys
import json
import os


app = Flask(__name__)


@app.route('/add_user', methods=['POST'])
def add_user():
    if request.method == 'POST':
        print request.get_json()["screen_name"]
        target = request.args.get("target")
        type = request.args.get("type")
        follower = request.get_json()
        screen_name = follower["screen_name"]
        verified = follower["verified"]
        description = follower["description"]
        created_at = follower["created_at"]
        profile_image_url = follower["profile_image_url"]
        followed_at = follower["followed_at"]
        followers = follower["followers"]
        location = follower["location"]
        following = follower["following"]
        id = follower["id"]

        tx = graph.cypher.begin()
        tx.append("OPTIONAL MATCH(n) WHERE n.screen_name={target} RETURN CASE n WHEN null THEN 0 ELSE 1 END as result", target=screen_name)
        target_exists = tx.commit()[0][0][0]
        tx = graph.cypher.begin()
        if(target_exists != 1):
            tx = graph.cypher.begin()
            if type == ":Origin":
                tx.append('''CREATE (user:Origin:User {screen_name:{screen_name},
                    verified:{verified}, description:{description},
                    created_at:{created_at}, profile_image_url:{profile_image_url},
                    followed_at:{followed_at}, followers:{followers},
                    location:{location}, following:{following}, id:{id}})
                    RETURN user''', screen_name=screen_name,
                    verified=verified, description=description,
                    created_at=created_at, profile_image_url=profile_image_url,
                    followed_at=followed_at, followers=followers, location=location,
                    following=following, id=id)
            else:
                tx.append('''CREATE (user:User {screen_name:{screen_name},
                    verified:{verified}, description:{description},
                    created_at:{created_at}, profile_image_url:{profile_image_url},
                    followed_at:{followed_at}, followers:{followers},
                    location:{location}, following:{following}, id:{id}})
                    RETURN user''', screen_name=screen_name,
                    verified=verified, description=description,
                    created_at=created_at, profile_image_url=profile_image_url,
                    followed_at=followed_at, followers=followers, location=location,
                    following=following, id=id)
            origin = tx.commit()[0].one
        else:
            tx.append("MATCH(user) WHERE user.screen_name={screen_name} RETURN user", screen_name=screen_name)
            origin = tx.commit()[0].one

        if type == "":
            tx = graph.cypher.begin()
            print "%s ----> %s" % (screen_name, target)
            tx.append("OPTIONAL MATCH(origin {screen_name:{screen_name}}) -[rel:FOLLOWS]-> (target {screen_name:{target}}) RETURN CASE rel WHEN null THEN 0 ELSE 1 END as result", screen_name=screen_name, target=target)
            relationship_exists = tx.commit()[0][0][0]
            print "relationship: %s" % relationship_exists
            if(relationship_exists != 1):
                print "relationship doesn't exist!"
                tx = graph.cypher.begin()
                tx.append("MATCH(target) where target.screen_name={target} RETURN target", target=target)
                target = tx.commit()[0].one
                follows_relationship = Path(origin, "FOLLOWS", target)
                graph.create(follows_relationship)
        print "user %s saved" % screen_name
        return "\tuser %s added to database" % screen_name


@app.route('/add_tweet', methods=['POST'])
def add_tweet():
    if request.method == 'POST':
        tweet = request.get_json()
        author = tweet["author"]
        content = tweet["text"]
        created_at = tweet["created_at"]
        source = tweet["source"]
        tweet_id = tweet["id"]
        author_joined_on = tweet["author_joined_on"]
        in_reply_to = tweet["in_reply_to_screen_name"]
        replied_tweet_id = tweet["replied_tweet_id"]
        replied_tweet_content = tweet["replied_tweet_text"]
        replied_tweet_date = tweet["replied_tweet_date"]
        print '''author:%s joined:%s reply_to:%s
replied_id:%s replied_content:%s replied_date:%s\n''' % (author,
                author_joined_on, in_reply_to, replied_tweet_id,
                replied_tweet_content, replied_tweet_date)

        if tweet["type"] == "reply":
            tx = graph.cypher.begin()
            print "OPTIONAL MATCH(n) WHERE n.screen_name={origin} RETURN CASE n WHEN null THEN 0 ELSE 1 END as result\n".format(origin=author)
            tx.append("OPTIONAL MATCH(n) WHERE n.screen_name={origin} RETURN CASE n WHEN null THEN 0 ELSE 1 END as result", origin=author)
            author_exists = tx.commit()[0][0][0]
            tx = graph.cypher.begin()
            if(author_exists != 1):
                print '''CREATE (user:User screen_name:{screen_name},
                    created_at:{joined_on})
                    RETURN user\n'''.format(screen_name=author,
                    joined_on=author_joined_on)
                tx.append('''CREATE (user:User {screen_name:{screen_name},
                    created_at:{joined_on}})
                    RETURN user''', screen_name=author,
                    joined_on=author_joined_on)
                origin = tx.commit()[0].one
            else:
                print "MATCH(user) WHERE user.screen_name={screen_name} RETURN user\n".format(screen_name=author)
                tx.append("MATCH(user) WHERE user.screen_name={screen_name} RETURN user", screen_name=author)
                origin = tx.commit()[0].one

            tx = graph.cypher.begin()
            print "MATCH(target) where target.screen_name={target} RETURN target\n".format(target=in_reply_to)
            tx.append("MATCH(target) where target.screen_name={target} RETURN target", target=in_reply_to)
            replied_author = tx.commit()[0].one

            tx = graph.cypher.begin()
            print "OPTIONAL MATCH(n) WHERE n.tweet_id={replied_tweet_id} RETURN CASE n WHEN null THEN 0 ELSE 1 END as result\n".format(replied_tweet_id=replied_tweet_id)
            tx.append("OPTIONAL MATCH(n) WHERE n.tweet_id={replied_tweet_id} RETURN CASE n WHEN null THEN 0 ELSE 1 END as result", replied_tweet_id=replied_tweet_id)
            replied_tweet_exists = tx.commit()[0][0][0]
            print "replied_tweet_exists: %s" % replied_tweet_exists
            tx = graph.cypher.begin()
            if(replied_tweet_exists != 1):
                print '''CREATE (tweet:Tweet author:{in_reply_to},
                    content:{replied_tweet_content}, tweet_id:{replied_tweet_id},
                    created_at:{replied_tweet_date})
                    RETURN tweet\n'''.format(in_reply_to=in_reply_to,
                    replied_tweet_content=replied_tweet_content,
                    replied_tweet_id=replied_tweet_id,
                    replied_tweet_date=replied_tweet_date)
                tx.append('''CREATE (tweet:Tweet {author:{in_reply_to},
                    content:{replied_tweet_content}, tweet_id:{replied_tweet_id},
                    created_at:{replied_tweet_date}})
                    RETURN tweet''', in_reply_to=in_reply_to,
                    replied_tweet_content=replied_tweet_content,
                    replied_tweet_id=replied_tweet_id,
                    replied_tweet_date=replied_tweet_date)
                replied_tweet = tx.commit()[0].one
            else:
                print "MATCH(tweet) WHERE tweet.tweet_id={replied_tweet_id} RETURN tweet\n".format(replied_tweet_id=replied_tweet_id)
                tx.append("MATCH(tweet) WHERE tweet.tweet_id={replied_tweet_id} RETURN tweet", replied_tweet_id=replied_tweet_id)
                replied_tweet = tx.commit()[0].one

            tx = graph.cypher.begin()
            print "OPTIONAL MATCH(n) WHERE n.tweet_id={replied_tweet_id} RETURN CASE n WHEN null THEN 0 ELSE 1 END as result\n".format(replied_tweet_id=replied_tweet_id)
            tx.append("OPTIONAL MATCH(n) WHERE n.tweet_id={tweet_id} RETURN CASE n WHEN null THEN 0 ELSE 1 END as result", tweet_id=tweet_id)
            response_tweet_exists = tx.commit()[0][0][0]
            tx = graph.cypher.begin()
            if(response_tweet_exists != 1):
                print '''CREATE (tweet:Tweet author:{author},
                    content:{content}, tweet_id:{tweet_id},
                    created_at:{created_at}, source:{source})
                    RETURN tweet'''.format(author=author, content=content,
                    tweet_id=tweet_id, created_at=created_at, source=source)
                tx.append('''CREATE (tweet:Tweet {author:{author},
                    content:{content}, tweet_id:{tweet_id},
                    created_at:{created_at}, source:{source}})
                    RETURN tweet''', author=author, content=content,
                    tweet_id=tweet_id, created_at=created_at, source=source)
                response = tx.commit()[0].one
            else:
                print "MATCH(tweet) WHERE tweet.tweet_id={replied_tweet_id} RETURN tweet\n".format(replied_tweet_id=replied_tweet_id)
                tx.append("MATCH(tweet) WHERE tweet.tweet_id={replied_tweet_id} RETURN tweet", replied_tweet_id=replied_tweet_id)
                response = tx.commit()[0].one

            tx = graph.cypher.begin()
            print "OPTIONAL MATCH(user screen_name:{in_reply_to}) -[rel:TWEETS]-> (tweet:Tweet tweet_id:{replied_tweet_id}) RETURN CASE rel WHEN null THEN 0 ELSE 1 END as result\n".format(in_reply_to=in_reply_to, replied_tweet_id=replied_tweet_id)
            tx.append("OPTIONAL MATCH(user {screen_name:{in_reply_to}}) -[rel:TWEETS]-> (tweet:Tweet {tweet_id:{replied_tweet_id}}) RETURN CASE rel WHEN null THEN 0 ELSE 1 END as result",
                in_reply_to=in_reply_to, replied_tweet_id=replied_tweet_id)
            relationship_exists = tx.commit()[0][0][0]
            print "relationship: %s" % relationship_exists
            if(relationship_exists != 1):
                follows_relationship = Path(replied_author, "TWEETS", replied_tweet)
                graph.create(follows_relationship)

            tx = graph.cypher.begin()
            print "OPTIONAL MATCH(user screen_name:{author}) -[rel:TWEETS]-> (tweet:Tweet tweet_id:{tweet_id}) RETURN CASE rel WHEN null THEN 0 ELSE 1 END as result\n".format(author=author, tweet_id=tweet_id)
            tx.append("OPTIONAL MATCH(user {screen_name:{author}}) -[rel:TWEETS]-> (tweet:Tweet {tweet_id:{tweet_id}}) RETURN CASE rel WHEN null THEN 0 ELSE 1 END as result",
                author=author, tweet_id=tweet_id)
            relationship_exists = tx.commit()[0][0][0]
            print "relationship: %s" % relationship_exists
            if(relationship_exists != 1):
                follows_relationship = Path(origin, "TWEETS", response)
                graph.create(follows_relationship)

            tx = graph.cypher.begin()
            print "OPTIONAL MATCH(response tweet_id:{tweet_id}) -[rel:REPLIES]-> (replied tweet_id:{replied_tweet_id}) RETURN CASE rel WHEN null THEN 0 ELSE 1 END as result\n".format(tweet_id=tweet_id, replied_tweet_id=replied_tweet_id)
            tx.append("OPTIONAL MATCH(response {tweet_id:{tweet_id}}) -[rel:REPLIES]-> (replied {tweet_id:{replied_tweet_id}}) RETURN CASE rel WHEN null THEN 0 ELSE 1 END as result",
                tweet_id=tweet_id, replied_tweet_id=replied_tweet_id)
            relationship_exists = tx.commit()[0][0][0]
            print "relationship: %s" % relationship_exists
            if(relationship_exists != 1):
                follows_relationship = Path(response, "REPLIES", replied_tweet)
                graph.create(follows_relationship)
        return "tweet saved"


if __name__ == '__main__':
    # pass in the configuration file
    abs_path = os.path.dirname(os.path.realpath(__file__)) + '/'
    with open(sys.argv[1], 'r') as json_data_file:
        data = json.load(json_data_file)

    psswrd = data["database_psswrd"]
    authenticate("localhost:7474", "neo4j", psswrd)
    graph = Graph("http://localhost:7474/db/data/")
    app.run(host="0.0.0.0", port=80)
