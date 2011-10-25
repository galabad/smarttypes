
import sys, site
site.addsitedir('/home/timmyt/.virtualenvs/smarttypes/lib/python2.6/site-packages')
sys.path.insert(0, '/home/timmyt/projects/smarttypes')

import tweepy
import smarttypes
from smarttypes.config import *

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
twitter_api_handle = tweepy.API(auth)

from smarttypes.utils.postgres_handle import PostgresHandle
from smarttypes.model.postgres_base_model import PostgresBaseModel
postgres_handle = PostgresHandle(smarttypes.connection_string)
PostgresBaseModel.postgres_handle = postgres_handle

from smarttypes.model.twitter_user import TwitterUser
#from smarttypes.model.twitter_group import TwitterGroup

me = TwitterUser.by_screen_name('SmartTypes')



