
import social_map

import random, mimetypes, os
from smarttypes.config import *
from smarttypes.utils.exceptions import RedirectException
from smarttypes.utils import twitter_api_utils
from smarttypes.utils import validation_utils 
from genshi.core import Markup
from genshi import HTML
from smarttypes.model.twitter_group import TwitterGroup
from smarttypes.model.twitter_user import TwitterUser
from smarttypes.model.twitter_reduction import TwitterReduction
import numpy as np

 
def index(req, session, postgres_handle):
    return {}

 
def sign_in(req, session, postgres_handle):
    raise RedirectException(twitter_api_utils.get_signin_w_twitter_url(postgres_handle))

 
def my_account(req, session, postgres_handle):
    if session:
        return {}
    if 'oauth_token' in req.params and 'oauth_verifier' in req.params:
        session = twitter_api_utils.complete_signin(req.params['oauth_token'], 
                                                    req.params['oauth_verifier'], postgres_handle)
        if session:
            return {'cookies':[('session', session.request_key)], 'session':session}
    return {}

 
def save_email(req, session, postgres_handle):
    if session and session.credentials:
        credentials = session.credentials
        if validation_utils.is_valid_email(req.params.get('email')) or not req.params.get('email'):
            credentials.email = req.params.get('email')
            credentials.save()
    raise RedirectException('/my_account')

 
def blog(req, session, postgres_handle):
    changed_url_map = {
        'blog/graphlab_and_python_vs_complexity':'blog/modeling_complexity_w_python'
    }
    template_path = "blog/index.html"
    if req.path.find('/',1) > 0: #path looks like '/blog/something'
        request_path = req.path[1:]
        template_path = "%s.html" % changed_url_map.get(request_path, request_path)
    return {
        'template_path':template_path,
        'active_tab':'blog',
    }

 
def contact(req, session, postgres_handle):
    return {}

 
def static(req, session, postgres_handle):
    #apache will handle this in prod
    static_path = os.path.dirname(os.path.dirname(__file__))+req.path
    return {
        'content_type':mimetypes.guess_type(static_path)[0], 
        'return_str':open(static_path).read()
    }




