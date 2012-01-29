
import social_map

import random, mimetypes, os
from smarttypes.config import *
from smarttypes.utils.postgres_web_decorator import postgres_web_decorator
from smarttypes.utils.exceptions import RedirectException
from smarttypes.utils import twitter_api_utils
from smarttypes.utils import validation_utils 
from genshi.core import Markup
from genshi import HTML
from smarttypes.model.twitter_group import TwitterGroup
from smarttypes.model.twitter_user import TwitterUser
from smarttypes.model.twitter_reduction import TwitterReduction
import numpy as np

@postgres_web_decorator()
def index(req, session):
    root_user = TwitterUser.by_screen_name('SmartTypes')
    reduction = TwitterReduction.get_latest_reduction(root_user.id)    
    return {
        'num_groups':len(TwitterGroup.all_groups(reduction.id)),
    }

@postgres_web_decorator()
def sign_in(req, session):
    raise RedirectException(twitter_api_utils.get_signin_w_twitter_url())

@postgres_web_decorator()
def my_account(req, session):
    if 'oauth_token' in req.params and 'oauth_verifier' in req.params:
        session = twitter_api_utils.complete_signin(req.params['oauth_token'], req.params['oauth_verifier'])
        if session:
            return {'cookies':[('session', session.request_key)], 'session':session}
    return {}

@postgres_web_decorator()
def save_email(req, session):
    if session and session.credentials:
        credentials = session.credentials
        if validation_utils.is_valid_email(req.params.get('email')) or not req.params.get('email'):
            credentials.email = req.params.get('email')
            credentials.save()
    raise RedirectException('/my_account')

@postgres_web_decorator()
def blog(req, session):
    changed_url_map = {
        'blog/graphlab_and_python_vs_complexity':'blog/complexity_probability_social_networks_and_python'
    }
    template_path = "blog/index.html"
    if req.path.find('/',1) > 0: #path looks like '/blog/something'
        request_path = req.path[1:]
        template_path = "%s.html" % changed_url_map.get(request_path, request_path)
    return {
        'template_path':template_path,
        'active_tab':'blog',
    }

@postgres_web_decorator()
def contact(req, session):
    return {}

@postgres_web_decorator()
def static(req, session):
    #apache will handle this in prod
    static_path = os.path.dirname(os.path.dirname(__file__))+req.path
    return {
        'content_type':mimetypes.guess_type(static_path)[0], 
        'return_str':open(static_path).read()
    }




