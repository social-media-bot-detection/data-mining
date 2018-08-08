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
            tx.append('''CREATE (user:User {screen_name:{screen_name},
                verified:{verified}, description:{description},
                created_at:{created_at}, profile_image_url:{profile_image_url},
                followed_at:{followed_at}, followers:{followers},
                location:{location}, following:{following}, id:{id}})
                RETURN user''', screen_name=screen_name, verified=verified,
                description=description, created_at=created_at,
                profile_image_url=profile_image_url,
                followed_at=followed_at, followers=followers, location=location,
                following=following, id=id)
            origin = tx.commit()[0].one
        else:
            tx.append("MATCH(user) WHERE user.screen_name={screen_name} RETURN user", screen_name=screen_name)
            origin = tx.commit()[0].one

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
        print "follower %s saved" % screen_name
        return "\tfollower %s added to database" % screen_name


if __name__ == '__main__':
    # pass in the configuration file
    abs_path = os.path.dirname(os.path.realpath(__file__)) + '/'
    with open(sys.argv[1], 'r') as json_data_file:
        data = json.load(json_data_file)

    psswrd = data["database_psswrd"]
    authenticate("localhost:7474", "neo4j", psswrd)
    graph = Graph("http://localhost:7474/db/data/")
    app.run(host="0.0.0.0", port=80)
