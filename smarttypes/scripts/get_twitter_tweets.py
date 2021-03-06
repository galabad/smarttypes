
import smarttypes, sys
from smarttypes.config import *

from smarttypes.utils.postgres_handle import PostgresHandle
postgres_handle = PostgresHandle(smarttypes.connection_string)

from smarttypes.model.twitter_user import TwitterUser
from smarttypes.model.twitter_tweet import TwitterTweet
from datetime import datetime, timedelta

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
            
    
        #for k, v in json.items():
            #if k == 'user':
                #user_model = getattr(api.parser.model_factory, 'user')
                #user = user_model.parse(api, v)
                #setattr(status, 'author', user)
                #setattr(status, 'user', user)  # DEPRECIATED
            #elif k == 'created_at':
                #setattr(status, k, parse_datetime(v))
            #elif k == 'source':
                #if '<' in v:
                    #setattr(status, k, parse_html_value(v))
                    #setattr(status, 'source_url', parse_a_href(v))
                #else:
                    #setattr(status, k, v)
                    #setattr(status, 'source_url', None)
            #elif k == 'retweeted_status':
                #setattr(status, k, Status.parse(api, v))
            #else:
                #setattr(status, k, v)
        #return status    
    
    
if __name__ == "__main__":

    if not len(sys.argv) > 1:
        raise Exception('Need a twitter handle.')
    else:
        screen_name = sys.argv[1]
        
    twitter_user = TwitterUser.by_screen_name(screen_name, postgres_handle)
    if not twitter_user.credentials:
        raise Exception('%s does not have api credentials.' % screen_name)
    
    monitor_these_user_ids = twitter_user.following_following_ids[:4900]
    monitor_these_user_ids.append(twitter_user.id)
    print "Num of users to monitor: %s" % len(monitor_these_user_ids)
    listener = Listener(monitor_these_user_ids)
    stream = Stream(twitter_user.credentials.auth_handle, listener, secure=True)

    stream.filter(follow=monitor_these_user_ids)







