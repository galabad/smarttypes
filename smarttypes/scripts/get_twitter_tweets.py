
import smarttypes, sys
from smarttypes.config import *

from smarttypes.utils.postgres_handle import PostgresHandle
from smarttypes.model.postgres_base_model import PostgresBaseModel
postgres_handle = PostgresHandle(smarttypes.connection_string)
PostgresBaseModel.postgres_handle = postgres_handle

from smarttypes.model.twitter_user import TwitterUser
from smarttypes.model.twitter_tweet import TwitterTweet

import tweepy
from tweepy.streaming import StreamListener, Stream


class Listener(StreamListener):
    
    def __init__(self, monitor_these_user_ids, api=None):
        StreamListener.__init__(self)
        self.monitor_these_user_ids = monitor_these_user_ids
    
    def on_error(self, status_code):
        print "Error: %s" % status_code
        return False    
    
    def on_status(self, status):
        if status.author.id_str in self.monitor_these_user_ids:
            TwitterTweet.upsert_from_api_tweet(status)
            postgres_handle.connection.commit()
            print "got one"
        return True
            
    
if __name__ == "__main__":

    if not len(sys.argv) > 1:
        args_dict = {'screen_name':'SmartTypes'}
    else:
        args_dict = eval(sys.argv[1])
    screen_name = args_dict['screen_name']
    twitter_user = TwitterUser.by_screen_name(screen_name)
    
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)

    monitor_these_user_ids = twitter_user.following_following_ids[:4900]
    print "Num of users to monitor: %s" % len(monitor_these_user_ids)
    listener = Listener(monitor_these_user_ids)
    stream = Stream(auth,listener,secure=True)

    stream.filter(follow=monitor_these_user_ids)







