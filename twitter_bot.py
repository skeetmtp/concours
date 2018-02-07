#python twitter_bot.py

from tweepy.streaming import StreamListener
from tweepy import OAuthHandler, API
from tweepy import Stream
import json
import logging
import warnings
from pprint import pprint
import config
import time

warnings.filterwarnings("ignore")


auth_handler = OAuthHandler(config.consumer_key, config.consumer_secret)
auth_handler.set_access_token(config.access_token, config.access_secret)

twitter_client = API(auth_handler)

logging.basicConfig(level=logging.INFO)

AVOID = ["tag", "paypal", "itune", "googleplay", "bitcoin", "iphone", "carte cadeau"]
#MANDATORY = ["rt", "follow"]

last_tweet_time = 0
last_rt_id = 0
rt_ids = dict()


def my_encode(text):
    return str(unicode(text).encode("utf-8"))

class PyStreamListener(StreamListener):
    def on_data(self, data):
	global last_tweet_time
	global last_rt_id
	global rt_ids
        tweet = json.loads(data)
	now = time.time()
        try:
	    #print json.dumps(tweet, indent=4, sort_keys=True)
	    tweet_text = my_encode(tweet['text'])
	    retweet_count = tweet["retweeted_status"]["retweet_count"]
	    users = tweet["entities"]["user_mentions"]
	    orig_id = tweet["retweeted_status"]["id"]
	    created_at = tweet["retweeted_status"]["created_at"]
	    created_at_sec = time.mktime(time.strptime(created_at,"%a %b %d %H:%M:%S +0000 %Y"))
            tweet_age_sec = now - created_at_sec
	    #created_date = datetime.fromtimestamp(created_at)
        except Exception as ex:
	    #print json.dumps(tweet, indent=4, sort_keys=True)
            logging.error(ex)
	    return True
	try:
            publish = True
	    delta_time = now - last_tweet_time
	    if delta_time < (60*10):
               	logging.info("SKIP delta_time {}".format(delta_time))
		return True
            
	    logging.info("reading {0}".format(tweet_text))
	
	    if tweet_age_sec > (60*60*24*30):
               	logging.info("SKIP too old tweet {0} {1}".format(tweet_age_sec, created_at))
		return True

	    if retweet_count<149:
               	logging.info("SKIP retweet_count {0} to low ".format(retweet_count))
		return True

            if tweet.get('lang') and tweet.get('lang') != 'fr':
               	logging.info("SKIP lang != fr")
                return True
            
	    #for word in MANDATORY:
            #    if word not in tweet_text.lower():
            #        logging.info("SKIP missing word \"{}\"".format(word))
	    #	    return True

            for word in AVOID:
                if word in tweet_text.lower():
                    logging.info("SKIP avoid word {}".format(word))
                    return True

	    if orig_id in rt_ids:
                logging.info("SKIP same id {}".format(orig_id))
                return True
            #print json.dumps(tweet, indent=4, sort_keys=True)
	    #publish = False
            if publish:
	        #print json.dumps(tweet, indent=4, sort_keys=True)
                logging.info("RT {0}".format(orig_id))
		rt_ids[orig_id] = True
		last_rt_id = orig_id
                twitter_client.retweet(orig_id)
                logging.info("RT {0} #{1} : {2}".format(orig_id, retweet_count, tweet_text))
		last_tweet_time = time.time()
		for user in users:
		  user_id = user["id"]
                  logging.info("  @ {0} {1}".format(user_id, my_encode(user['screen_name'])))
		  twitter_client.create_friendship(user_id)

        except Exception as ex:
	    #print json.dumps(tweet, indent=4, sort_keys=True)
            logging.error(ex)
	    return True

        return True

    def on_error(self, status):
	logging.error("status : {0}".format(status))


if __name__ == '__main__':
    while True:
	logging.info("------------------ STARTING ---------------")
	try:
	    listener = PyStreamListener()
	    stream = Stream(auth_handler, listener)
	    stream.filter(track=['concours follow rt'])
        except Exception as ex:
            logging.error(ex)
	    pass


