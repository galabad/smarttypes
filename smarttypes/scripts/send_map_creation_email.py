
from datetime import datetime
import smarttypes, sys, string
from smarttypes.config import *
from smarttypes.model.twitter_credentials import TwitterCredentials
from smarttypes.model.twitter_user import TwitterUser
from smarttypes.model.twitter_reduction import TwitterReduction

from smarttypes.utils.postgres_handle import PostgresHandle
postgres_handle = PostgresHandle(smarttypes.connection_string)


if __name__ == "__main__":
    
    user_count_list = TwitterReduction.get_user_reduction_counts(postgres_handle)
    for user, count in user_count_list:
        if count == 1:
            creds = TwitterCredentials.get_by_twitter_id(user.id, postgres_handle)
            creds.maybe_send_initial_map_email()
        
        
        
        
        
        