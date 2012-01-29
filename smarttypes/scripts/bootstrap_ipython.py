
from datetime import datetime
import numpy as np

import smarttypes, random
from smarttypes.utils.postgres_handle import PostgresHandle
from smarttypes.model.postgres_base_model import PostgresBaseModel
postgres_handle = PostgresHandle(smarttypes.connection_string)
PostgresBaseModel.postgres_handle = postgres_handle

from smarttypes.model.twitter_user import TwitterUser
from smarttypes.model.twitter_group import TwitterGroup
from smarttypes.model.twitter_reduction import TwitterReduction

#model_user = TwitterUser.by_screen_name('SmartTypes')
#api_handle = model_user.credentials.api_handle
#api_user = api_handle.get_user(screen_name='SmartTypes')

root_user = TwitterUser.by_screen_name('SmartTypes')
reduction = TwitterReduction.get_latest_reduction(root_user.id)   
reduction.save_group_info()
postgres_handle.connection.commit()