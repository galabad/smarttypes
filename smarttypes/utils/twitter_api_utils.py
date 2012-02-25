
import tweepy
from config import *
from smarttypes.utils import email_utils
from smarttypes.model.twitter_session import TwitterSession
from smarttypes.model.twitter_credentials import TwitterCredentials 
from smarttypes.model.twitter_user import TwitterUser
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


def get_signin_w_twitter_url(postgres_handle):
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET, callback=CALLBACK)
    request_token = auth._get_request_token()
    TwitterSession.create(request_token.key, request_token.secret, postgres_handle)
    url = "https://api.twitter.com/oauth/authenticate"  # might want this: '&force_login=true'
    request = tweepy.oauth.OAuthRequest.from_token_and_callback(token=request_token, http_url=url, callback=CALLBACK)
    return request.to_url()


def complete_signin(request_key, verifier, postgres_handle):
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    session = TwitterSession.get_by_request_key(request_key, postgres_handle)
    auth.set_request_token(request_key, session.request_secret)
    auth.get_access_token(verifier)
    # may have signed up already
    credentials = TwitterCredentials.get_by_access_key(auth.access_token.key, postgres_handle)
    if not credentials:
        credentials = TwitterCredentials.create(auth.access_token.key, auth.access_token.secret, postgres_handle)
    session.access_key = credentials.access_key
    if not credentials.twitter_user:
        user = TwitterUser.upsert_from_api_user(credentials.api_handle.me(), postgres_handle)
        credentials.twitter_id = user.id
        credentials.save()
    screen_name = credentials.twitter_user.screen_name
    email_utils.send_email('signup@smarttypes.org', ['timmyt@smarttypes.org'],
                           '%s signed up' % screen_name, 'smarttypes signup!')
    return session.save()
