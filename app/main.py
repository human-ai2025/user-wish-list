from flask import Flask, request, render_template, jsonify
import redis
import requests
from flask_caching import Cache  # Import Cache from flask_caching module
from flask import Response
import json

app = Flask(__name__)

app.config.from_object('config.Config')  # Set the configuration variables to the flask application
cache = Cache(app)  # Initialize Cache

# postgresql://username:password@host:port/database
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://hello_flask:hello_flask@db:5432/hello_flask_dev'

from models import db, UserFavs

db.init_app(app)
with app.app_context():
    # To create / use database mentioned in URI
    db.create_all()
    db.session.commit()

red = redis.Redis(host='redis', port=6379, db=0)


@app.route("/")
def main():
    return render_template('index.html')


@app.route("/save", methods=['POST'])
def save():
    username = str(request.form['username']).lower()
    place = str(request.form['place']).lower()
    food = str(request.form['food']).lower()

    # check if data of the username already exists in the redis
    if red.hgetall(username).keys():
        print("hget username:", red.hgetall(username))
        # return a msg to the template, saying the user already exists(from redis)
        return render_template('index.html', user_exists=1, msg='(From Redis)', username=username,
                               place=red.hget(username, "place").decode('utf-8'),
                               food=red.hget(username, "food").decode('utf-8'))

    # if not in redis, then check in db
    elif len(list(red.hgetall(username))) == 0:
        record = UserFavs.query.filter_by(username=username).first()
        print("Records fecthed from db:", record)

        if record:
            red.hset(username, "place", place)
            red.hset(username, "food", food)
            # return a msg to the template, saying the user already exists(from database)
            return render_template('index.html', user_exists=1, msg='(From DataBase)', username=username,
                                   place=record.place, food=record.food)

    # if data of the username doesnot exist anywhere, create a new record in DataBase and store in Redis also
    # create a new record in DataBase
    new_record = UserFavs(username=username, place=place, food=food)
    db.session.add(new_record)
    db.session.commit()

    # store in Redis also
    red.hset(username, "place", place)
    red.hset(username, "food", food)

    # cross-checking if the record insertion was successful into database
    record = UserFavs.query.filter_by(username=username).first()
    print("Records fetched from db after insert:", record)

    # cross-checking if the insertion was successful into redis
    print("key-values from redis after insert:", red.hgetall(username))

    # return a success message upon saving
    return render_template('index.html', saved=1, username=username, place=red.hget(username, "place").decode('utf-8'),
                           food=red.hget(username, "food").decode('utf-8'))


@app.route("/keys", methods=['GET'])
def keys():
    records = UserFavs.query.all()
    names = []
    for record in records:
        names.append(record.username)
    return render_template('index.html', keys=1, usernames=names)


@app.route("/get", methods=['POST'])
def get():
    username = request.form['username']
    print("Username:", username)
    user_data = red.hgetall(username)
    print("GET Redis:", user_data)

    if not user_data:
        record = UserFavs.query.filter_by(username=username).first()
        print("GET Record:", record)
        if not record:
            print("No data in redis or db")
            return render_template('index.html', no_record=1, msg=f"Record not yet defined for {username}")
        red.hset(username, "place", record.place)
        red.hset(username, "food", record.food)
        return render_template('index.html', get=1, msg="(From DataBase)", username=username, place=record.place,
                               food=record.food)
    return render_template('index.html', get=1, msg="(From Redis)", username=username,
                           place=user_data[b'place'].decode('utf-8'), food=user_data[b'food'].decode('utf-8'))



@app.route("/universities/")
@cache.cached(query_string=True)
def get_universities():
    API_URL = "http://universities.hipolabs.com/search?country="
    search = request.args.get('country')
    r = requests.get(f"{API_URL}{search}")
    return jsonify(r.json())



# todo make a acknowledgement.
# todo update redis cache after that.
# todo db update happens -> acknowledgement comes -> clear that key -> Update cache key
# todo cache the db with cached and then try updatig the cache


@app.route("/get_keys")
def get_keys():
    keys_r = {}
    for i, key in enumerate(red.scan_iter()):
        keys_r[i] = key.decode('utf-8')
    print("*"*50)
    print(keys_r)
    print("*" * 50)
    json_object = json.dumps(keys_r, indent=4)
    return json_object