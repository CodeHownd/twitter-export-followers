import tweepy
import sqlite3
import datetime
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("api_key", help='the api key from your twitter developer app', type=str)
parser.add_argument("api_secret_key", help='the api secret key from your twitter developer app', type=str)
parser.add_argument("access_token",  help='the access token from your twitter developer app',  type=str)
parser.add_argument("access_token_secret", help='the access token secret from your twitter developer app', type=str)
parser.add_argument("message", help='message that will be DM\'ed to the followers you select', type=str)
parser.add_argument("-v", "--verified", help="sort followers by verified status", action="store_true")
parser.add_argument("-c", "--count", help="sort followers by follower count (descending)", action="store_true")
parser.add_argument("-i", "--includes", help="sort followers by phrase in bio")


args = parser.parse_args()

message = args.message


def get_api(consumer_key, consumer_secret, access_token_key, access_token_secret):
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token_key, access_token_secret)
    api = tweepy.API(auth)
    return api


global api
api = get_api(args.api_key, args.api_secret_key, args.access_token, args.access_token_secret)


def get_followers():
    followers = api.followers()
    for follower in followers:
        user_id = follower._json['id']
        handle = follower._json['screen_name']
        bio = follower._json['description']
        followers_count = follower._json['followers_count']
        verified = follower._json['verified']
        location = follower._json['location']
        conn = sqlite3.connect('followers.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS followers
            (id integer NOT NULL PRIMARY KEY, handle text, bio text,
                  followers integer, verified integer, location text, date_retrieved text, DMd_already integer)''')
        c.execute("INSERT INTO followers VALUES (?,?,?,?,?,?,?,?)", (user_id, handle, bio,
                                                                     followers_count, verified, location,
                                                                     datetime.datetime.now(), 0))
        conn.commit()
        conn.close()


def preview_followers():
    conn = sqlite3.connect('followers.db')
    c = conn.cursor()
    global query
    query = 'SELECT * FROM followers LIMIT 10'
    if args.verified:
        query = 'SELECT * FROM followers ORDER BY followers DESC LIMIT 10'
    elif args.count:
        query = 'SELECT * FROM followers ORDER BY verified DESC LIMIT 10'
    elif args.includes:
        query = f'SELECT * FROM followers WHERE bio LIKE \'%{args.includes}%\' LIMIT 10'
    for row in c.execute(query):
        print(f'handle: {row[1]}, follower count: {row[3]}, is verified: {"yes" if row[4] == 1 else "no"}, location: {row[5]}, bio: {row[2]}')
    conn.commit()
    conn.close()


def test_send():
    conn = sqlite3.connect('followers.db')
    c = conn.cursor()
    c.execute('SELECT * FROM followers ORDER BY followers DESC LIMIT 10')
    for row in c.fetchall():
        api.send_direct_message(row[0], message)
        with conn:
            conn.execute('UPDATE followers SET DMd_already = 1 WHERE id = (?)', (row[0],))
    c.close()
    conn.close()


def send_all():
    conn = sqlite3.connect('followers.db')
    c = conn.cursor()
    c.execute('SELECT * FROM followers WHERE DMd_already = 0 ORDER BY followers DESC')
    for row in c.fetchall():
        api.send_direct_message(row[0], message)
        with conn:
            conn.execute('UPDATE followers SET DMd_already = 1 WHERE id = (?)', (row[0],))
    c.close()
    conn.close()

# get_followers()

# preview_followers()

test_send()
