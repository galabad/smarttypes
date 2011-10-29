
import tweepy
from smarttypes.config import *
from smarttypes.model.twitter_signup import TwitterSignup
from dateutil import tz
from datetime import datetime

HERE = tz.tzlocal()
UTC = tz.tzutc()

def get_rate_limit_status(api_handle):
    rate_limit_status_dict = api_handle.rate_limit_status()
    remaining_hits = rate_limit_status_dict['remaining_hits']
    reset_time_in_seconds = rate_limit_status_dict['reset_time_in_seconds']
    reset_time_utc = datetime.utcfromtimestamp(reset_time_in_seconds)
    reset_time_utc = reset_time_utc.replace(tzinfo=UTC)
    reset_time = reset_time_utc.astimezone(HERE)
    return remaining_hits, reset_time

def get_signin_w_twitter_url():
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    request_token = auth._get_request_token()
    TwitterSignup.start_signup(request_token.key, request_token.secret)
    url = "https://api.twitter.com/oauth/authenticate" #might want this: '&force_login=true'
    request = tweepy.oauth.OAuthRequest.from_token_and_callback(token=request_token, http_url=url)
    return request.to_url()

def attempt_to_complete_signin(request_key, verifier):
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    twitter_signup = TwitterSignup.get_by_request_key(request_key)
    auth.set_request_token(request_key, twitter_signup.request_secret)
    auth.get_access_token(verifier)
    #they may have signed up already
    if not TwitterSignup.get_by_access_key(auth.access_token.key):
        twitter_signup.access_key = auth.access_token.key
        twitter_signup.access_secret = auth.access_token.secret
        twitter_signup.save()


    
    
    
    
    