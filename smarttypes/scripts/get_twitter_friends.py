
from multiprocessing import Process
import smarttypes, sys
from smarttypes.config import *
from smarttypes.utils.postgres_handle import PostgresHandle
from smarttypes.model.twitter_user import TwitterUser
from smarttypes.model.twitter_credentials import TwitterCredentials
from smarttypes.utils.twitter_api_utils import get_rate_limit_status
from datetime import datetime, timedelta
import tweepy
from tweepy import TweepError

MAX_FOLLOWING_COUNT = TwitterUser.MAX_FOLLOWING_COUNT
AVG_PEOPLE_RETURNED_PER_QUERY = 80
REMAINING_HITS_THRESHOLD = 20
if (MAX_FOLLOWING_COUNT / AVG_PEOPLE_RETURNED_PER_QUERY) > REMAINING_HITS_THRESHOLD:
    raise Exception("get_twitter_friends script error: the code assumes this wont happen.")

def continue_or_exit(api_handle, put_this_in_the_error_message):
    remaining_hits, reset_time = get_rate_limit_status(api_handle)
    if remaining_hits < REMAINING_HITS_THRESHOLD:
        raise Exception("remaining_hits less than threshold %s" % put_this_in_the_error_message)

    
def load_user_and_the_people_they_follow(api_handle, user_id, postgres_handle, is_root_user=False):
    
    print "Attempting to load user %s." % user_id
    continue_or_exit(api_handle, user_id)
    
    try:    
        api_user = api_handle.get_user(user_id=user_id)
    except TweepError, ex:
        print "Got a TweepError: %s." % ex
        return None
    
    model_user = TwitterUser.upsert_from_api_user(api_user, postgres_handle)
    postgres_handle.connection.commit()
    screen_name = model_user.screen_name
    
    if api_user.protected:
        print "\t %s is protected." % screen_name
        return model_user    
    
    if not is_root_user and api_user.friends_count > MAX_FOLLOWING_COUNT:
        print "\t %s follows too many people, %s." % (screen_name, api_user.friends_count)
        model_user.save_following_ids([])
        postgres_handle.connection.commit()
        return model_user
    
    print "Loading the people %s follows." % screen_name    
    following_ids = []
    api_following_list = []
    try:
        api_following_list = list(tweepy.Cursor(api_handle.friends, screen_name).items())
    except TweepError, ex:
        print "Got a TweepError: %s." % ex  
        if str(ex) == "Not authorized":
            print "\t Setting caused_an_error for %s." % screen_name
            model_user.caused_an_error = datetime.now()
            model_user.save()
            postgres_handle.connection.commit()
            return model_user
    
    for api_following in api_following_list:
        if api_following.protected:
            continue
        following_ids.append(api_following.id_str)
    model_user.save_following_ids(following_ids)
    postgres_handle.connection.commit()
    return model_user

def pull_some_users(user_id):
    postgres_handle = PostgresHandle(smarttypes.connection_string)
    root_user = TwitterUser.get_by_id(user_id, postgres_handle)
    if not root_user:
        raise Exception('User ID: %s not in our DB!' % user_id)
    if not root_user.credentials:
        raise Exception('%s does not have api credentials!' % root_user.screen_name)
    api_handle = root_user.credentials.api_handle
    root_user = load_user_and_the_people_they_follow(api_handle, root_user.id, postgres_handle, is_root_user=True)
    load_this_user_id = root_user.get_id_of_someone_in_my_network_to_load()
    while load_this_user_id:
        load_user_and_the_people_they_follow(api_handle, load_this_user_id, postgres_handle)
        load_this_user_id = root_user.get_id_of_someone_in_my_network_to_load()
        #load_this_user_id = None
    print "Finshed loading all related users for %s!" % root_user.screen_name

if __name__ == "__main__":
    postgres_handle = PostgresHandle(smarttypes.connection_string)
    max_processes = 4
    i = 0
    for creds in TwitterCredentials.get_all(postgres_handle, order_by='last_root_user_api_query'):
        if i >= max_processes:
            break
        root_user = creds.root_user
        if root_user:
            print "Starting a process to load root user: %s" % root_user.screen_name
            creds.last_root_user_api_query = datetime.now()
            creds.save()
            postgres_handle.connection.commit()
            p = Process(target=pull_some_users, args=(root_user.id,))
            p.start()
            i += 1
        
            
            
            
            
            