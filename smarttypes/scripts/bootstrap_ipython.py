
import pickle
from datetime import datetime
import numpy as np

import smarttypes, random
from smarttypes.utils.postgres_handle import PostgresHandle
postgres_handle = PostgresHandle(smarttypes.connection_string)

from smarttypes.model.twitter_user import TwitterUser
from smarttypes.model.twitter_group import TwitterGroup
from smarttypes.model.twitter_reduction import TwitterReduction
from smarttypes.model.twitter_credentials import TwitterCredentials

#model_user = TwitterUser.by_screen_name('SmartTypes', postgres_handle)
#api_handle = model_user.credentials.api_handle
#api_user = api_handle.get_user(screen_name='SmartTypes')

