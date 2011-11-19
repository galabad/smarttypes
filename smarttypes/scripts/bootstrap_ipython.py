
import tweepy
import smarttypes
from smarttypes.config import *

from smarttypes.utils.postgres_handle import PostgresHandle
from smarttypes.model.postgres_base_model import PostgresBaseModel
postgres_handle = PostgresHandle(smarttypes.connection_string)
PostgresBaseModel.postgres_handle = postgres_handle

from smarttypes.model.twitter_user import TwitterUser
from smarttypes.model.twitter_signup import TwitterCredentials
#from smarttypes.model.twitter_group import TwitterGroup

#me = TwitterUser.by_screen_name('SmartTypes')
#twitter_api_handle = me.credentials.api_handle

#signups = [x.twitter_user for x in TwitterCredentials.get_all()]
#signup_details = [(x.screen_name, x.description) for x in signups]

#python projects/smarttypes/smarttypes/scripts/get_twitter_tweets.py SmartTypes &> me_tweets.txt &

