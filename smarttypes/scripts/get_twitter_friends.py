
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

def continue_or_exit(api_handle):
    remaining_hits, reset_time = get_rate_limit_status(api_handle)
    if remaining_hits < REMAINING_HITS_THRESHOLD:
        raise Exception("remaining_hits less than threshold")
        
def load_user_and_the_people_they_follow(api_handle, screen_name, postgres_handle):
    print "Attempting to load %s" % screen_name
    continue_or_exit(api_handle)
    
    try:    
        api_user = api_handle.get_user(screen_name=screen_name)
    except TweepError, ex:
        print "Got a TweepError: %s." % ex  
        if str(ex) == "Not found":
            print "Setting caused_an_error for %s " % screen_name
            model_user = TwitterUser.by_screen_name(screen_name, postgres_handle)
            model_user.caused_an_error = datetime.now()
            model_user.save()
            return model_user
    
    model_user = TwitterUser.upsert_from_api_user(api_user, postgres_handle)
    postgres_handle.connection.commit()
    
    if api_user.protected:
        print "\t %s is protected" % screen_name
        return     
    
    if api_user.friends_count > MAX_FOLLOWING_COUNT:
        print "\t %s follows too many people, %s" % (screen_name, api_user.friends_count)
        model_user.save_following_ids([])
        postgres_handle.connection.commit()
        return model_user
    
    print "Loading the people %s follows" % screen_name    
    following_ids = []
    try:
        api_following_list = list(tweepy.Cursor(api_handle.friends, screen_name).items())
    except TweepError, ex:
        print "Got a TweepError: %s." % ex  
        if str(ex) == "Not authorized":
            print "Setting caused_an_error for %s " % screen_name
            model_user.caused_an_error = datetime.now()
            model_user.save()
            postgres_handle.connection.commit()
            return model_user
    
    for api_following in api_following_list:
        if api_following.protected:
            continue 
        model_following = TwitterUser.upsert_from_api_user(api_following, postgres_handle)
        postgres_handle.connection.commit()
        following_ids.append(model_following.id)
    model_user.save_following_ids(following_ids)
    postgres_handle.connection.commit()
    return model_user

def pull_some_users(screen_name):
    postgres_handle = PostgresHandle(smarttypes.connection_string)
    model_user = TwitterUser.by_screen_name(screen_name, postgres_handle)
    if not model_user.credentials:
        raise Exception('%s does not have api credentials!' % screen_name)
    api_handle = model_user.credentials.api_handle
    twitter_user = load_user_and_the_people_they_follow(api_handle, screen_name, postgres_handle)
    load_this_user = twitter_user.get_someone_in_my_network_to_load()
    while load_this_user:
        load_user_and_the_people_they_follow(api_handle, load_this_user.screen_name, postgres_handle)
        load_this_user = twitter_user.get_someone_in_my_network_to_load()
        #load_this_user = None
    print "Finshed loading all related users for %s!" % screen_name

if __name__ == "__main__":
    postgres_handle = PostgresHandle(smarttypes.connection_string)
    for creds in TwitterCredentials.get_all(postgres_handle):
        root_user = creds.root_user
        if root_user:
            p = Process(target=pull_some_users, args=(root_user.screen_name,))
            p.start()
        
            