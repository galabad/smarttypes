
import tweepy
import smarttypes
from smarttypes.config import *

from smarttypes.utils.postgres_handle import PostgresHandle
from smarttypes.model.postgres_base_model import PostgresBaseModel
postgres_handle = PostgresHandle(smarttypes.connection_string)
PostgresBaseModel.postgres_handle = postgres_handle

from smarttypes.model.twitter_user import TwitterUser
#from smarttypes.model.twitter_group import TwitterGroup

me = TwitterUser.by_screen_name('SmartTypes')
twitter_api_handle = me.credentials.api_handle


