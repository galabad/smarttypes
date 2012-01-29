
from smarttypes.utils.postgres_web_decorator import postgres_web_decorator
from smarttypes.utils.exceptions import RedirectException
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
        'template_path':'social_map/index.html',
        'root_user':root_user,
        'num_groups':len(TwitterGroup.all_groups(reduction.id)),
    }

@postgres_web_decorator()
def map_data(req, session):
    root_user = TwitterUser.by_screen_name('SmartTypes')
    reduction = TwitterReduction.get_latest_reduction(root_user.id)
    return {
        'content_type':'application/json',
        'json':reduction.get_details()
    }

#todo: return entire page for the search engines
@postgres_web_decorator()
def ajax_group(req, session):
    if 'group_index' in req.params:
        root_user = TwitterUser.by_screen_name('SmartTypes')
        reduction = TwitterReduction.get_latest_reduction(root_user.id)
        group_index = int(req.params['group_index'])
        twitter_group = TwitterGroup.get_by_index(reduction.id, group_index)
    else:
        twitter_group = None
    return {
        'template_path':'social_map/ajax_group.html',
        'twitter_group':twitter_group,
    }




