
import random, mimetypes, os
from smarttypes.config import *
from smarttypes.utils.postgres_web_decorator import postgres_web_decorator
from smarttypes.utils.exceptions import RedirectException
from smarttypes.utils import twitter_api_utils
from smarttypes.utils import validation_utils 
from genshi.core import Markup
from smarttypes.model.twitter_group import TwitterGroup
from smarttypes.model.twitter_user import TwitterUser
import tweepy


@postgres_web_decorator()
def home(req, credentials):
    return {}

@postgres_web_decorator()
def sign_in(req, credentials):
    raise RedirectException(twitter_api_utils.get_signin_w_twitter_url())

@postgres_web_decorator()
def my_account(req, credentials):
    if 'oauth_token' in req.params and 'oauth_verifier' in req.params:
        session = twitter_api_utils.complete_signin(req.params['oauth_token'], req.params['oauth_verifier'])
        if session:
            return {'cookies':[('session', session.request_key)], 'credentials':session.credentials}
    return {}

@postgres_web_decorator()
def save_email(req, credentials):
    if credentials:
        if validation_utils.is_valid_email(req.params.get('email')) or not req.params.get('email'):
            credentials.email = req.params.get('email')
            credentials.save()
    raise RedirectException('/my_account')

@postgres_web_decorator()
def sign_in(req, credentials):
    raise RedirectException(twitter_api_utils.get_signin_w_twitter_url())

@postgres_web_decorator()
def blog(req, credentials):
    changed_url_map = {
        'blog/graphlab_and_python_vs_complexity':'blog/complexity_probability_social_networks_and_python'
    }
    template_path = "blog/home.html"
    if req.path.find('/',1) > 0: #path looks like '/blog/something'
        request_path = req.path[1:]
        template_path = "%s.html" % changed_url_map.get(request_path, request_path)
    return {
        'template_path':template_path,
        'active_tab':'blog',
    }

@postgres_web_decorator()
def user(req, credentials):    
    if 'user_id' in req.params:
        user_id = int(req.params['user_id'])
        twitter_user = TwitterUser.get_by_id(user_id)
    else:
        screen_name = req.params['screen_name']
        twitter_user = TwitterUser.by_screen_name(screen_name)
    return {
        'twitter_user':twitter_user,
    }

@postgres_web_decorator()
def group(req, credentials):
    if 'group_index' in req.params:
        group_index = int(req.params['group_index'])
        twitter_group = TwitterGroup.get_by_index(group_index)
    else:
        twitter_group = TwitterGroup.get_random_group()
    return {
        'twitter_group':twitter_group,
    }

@postgres_web_decorator()
def about(req, credentials):
    return {}

@postgres_web_decorator()
def contact(req, credentials):
    return {}

@postgres_web_decorator()
def static(req, credentials):
    #apache will handle this in prod
    static_path = os.path.dirname(os.path.dirname(__file__))+req.path
    return {
        'content_type':mimetypes.guess_type(static_path)[0], 
        'return_str':open(static_path).read()
    }




