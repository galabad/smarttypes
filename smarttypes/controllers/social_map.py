
# from utils.exceptions import RedirectException
# from utils import validation_utils
# from genshi.core import Markup
# from genshi import HTML
from model.twitter_group import TwitterGroup
from model.twitter_user import TwitterUser
from model.twitter_reduction import TwitterReduction
# from model.twitter_credentials import TwitterCredentials
# import numpy as np


def index(req, session, postgres_handle):

    root_user = None
    if 'user_id' in req.params:
        root_user = TwitterUser.get_by_id(req.params['user_id'], postgres_handle)
    if not root_user:
        root_user = TwitterUser.by_screen_name('SmartTypes', postgres_handle)

    reduction = TwitterReduction.get_latest_reduction(root_user.id, postgres_handle)
    if not reduction:
        root_user = TwitterUser.by_screen_name('SmartTypes', postgres_handle)
        reduction = TwitterReduction.get_latest_reduction(root_user.id, postgres_handle)

    return {
        'active_tab': 'social_map',
        'template_path': 'social_map/index.html',
        'root_user': root_user,
        'reduction': reduction,
        'num_groups': len(TwitterGroup.all_groups(reduction.id, postgres_handle)),
        'users_with_a_reduction': TwitterReduction.get_users_with_a_reduction(postgres_handle),
    }


def map_data(req, session, postgres_handle):
    reduction = None
    if 'reduction_id' in req.params:
        try:
            reduction_id = int(req.params['reduction_id'])
        except ValueError:
            reduction_id = 0
        reduction = TwitterReduction.get_by_id(reduction_id, postgres_handle)

    return {
        'content_type': 'application/json',
        'json': reduction.get_details() if reduction else []
    }

#todo: return entire page for the search engines


def ajax_group(req, session, postgres_handle):
    if 'group_index' in req.params and 'reduction_id' in req.params:
        reduction = TwitterReduction.get_by_id(req.params['reduction_id'], postgres_handle)
        group_index = int(req.params['group_index'])
        twitter_group = TwitterGroup.get_by_index(reduction.id, group_index, postgres_handle)
    else:
        twitter_group = None
    return {
        'template_path': 'social_map/ajax_group.html',
        'twitter_group': twitter_group,
    }
