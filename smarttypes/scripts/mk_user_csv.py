
import smarttypes, sys
from smarttypes.model.twitter_user import TwitterUser
from smarttypes.model.twitter_tweet import TwitterTweet
from datetime import datetime, timedelta

from smarttypes.utils.postgres_handle import PostgresHandle
postgres_handle = PostgresHandle(smarttypes.connection_string)

if __name__ == "__main__":

    if not len(sys.argv) > 1:
        raise Exception('Need a twitter handle.')
    else:
        screen_name = sys.argv[1]
        
    #friends
    friends_file = open('/tmp/%s_twitter_friends.csv' % screen_name, 'w')
    TwitterUser.mk_following_following_csv(screen_name, friends_file, postgres_handle)
    
    #tweets_file = open('/tmp/%s_twitter_tweets.csv')
    #TwitterUser.mk_following_tweets_csv(screen_name, tweets_file)
    