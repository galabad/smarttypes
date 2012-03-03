
# from smarttypes.utils.exceptions import RedirectException
# from smarttypes.utils import validation_utils
# from genshi.core import Markup
# from genshi import HTML
import smarttypes
from smarttypes.model.twitter_group import TwitterGroup
from smarttypes.model.twitter_user import TwitterUser
from smarttypes.model.twitter_reduction import TwitterReduction
# from smarttypes.model.twitter_credentials import TwitterCredentials
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


def next_or_previous_reduction_id(req, session, postgres_handle):

    reduction = None
    if 'reduction_id' in req.params:
        try:
            reduction_id = int(req.params['reduction_id'])
        except ValueError:
            reduction_id = -1
        reduction = TwitterReduction.get_by_id(reduction_id, postgres_handle)

    #prev / next reduction
    new_reduction_id = -1
    if reduction and 'next_or_previous' in req.params:
        if req.params['next_or_previous'] in ['prev_reduction', 'next_reduction']:
            ordered_reduction_list = TwitterReduction.get_ordered_id_list(
                reduction.root_user_id, postgres_handle)
            for i in range(len(ordered_reduction_list)):
                if reduction.id == ordered_reduction_list[i]:
                    current_idx = i
                    break
            if req.params['next_or_previous'] == 'prev_reduction':
                idx = current_idx - 1
            if req.params['next_or_previous'] == 'next_reduction':
                idx = current_idx + 1
            new_reduction_id = ordered_reduction_list[idx]

    return {
        'content_type': 'application/json',
        'json': {
            'reduction_id': new_reduction_id,
            'num_groups': len(TwitterGroup.all_groups(new_reduction_id, postgres_handle))
        }
    }


def map_data(req, session, postgres_handle):
    reduction = None
    if 'reduction_id' in req.params:
        try:
            reduction_id = int(req.params['reduction_id'])
        except ValueError:
            reduction_id = -1
        reduction = TwitterReduction.get_by_id(reduction_id, postgres_handle)

    #details
    reduction_details = []
    if reduction:
        return_all = not smarttypes.config.IS_PROD  # for debugging
        #return_all = False
        reduction_details = reduction.get_details(return_all=return_all)

    return {
        'content_type': 'application/json',
        'json': reduction_details
    }

#todo: return entire page for the search engines

def group_details(req, session, postgres_handle):
    if 'group_index' in req.params and 'reduction_id' in req.params:
        reduction = TwitterReduction.get_by_id(req.params['reduction_id'], postgres_handle)
        group_index = int(req.params['group_index'])
        twitter_group = TwitterGroup.get_by_index(reduction.id, group_index, postgres_handle)
    else:
        twitter_group = None
    return {
        'template_path': 'social_map/group_details.html',
        'twitter_group': twitter_group,
    }

def node_details(req, session, postgres_handle):

    twitter_user, in_links, out_links = None, [], []
    if 'node_id' in req.params and 'reduction_id' in req.params:
        reduction = TwitterReduction.get_by_id(req.params['reduction_id'], postgres_handle)
        twitter_user = TwitterUser.get_by_id(req.params['node_id'], postgres_handle)
        if twitter_user:
            in_links, out_links = reduction.get_in_and_out_links_for_user(req.params['node_id'])
    return {
        'template_path': 'social_map/node_details.html',
        'twitter_user': twitter_user,
        'in_links':in_links,
        'out_links':out_links,
    }
