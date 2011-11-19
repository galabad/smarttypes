import cPickle
from collections import defaultdict
import heapq
from datetime import datetime, timedelta

import smarttypes
from smarttypes.utils.postgres_handle import PostgresHandle
from smarttypes.model.postgres_base_model import PostgresBaseModel
postgres_handle = PostgresHandle(smarttypes.connection_string)
PostgresBaseModel.postgres_handle = postgres_handle

from smarttypes.model.twitter_user import TwitterUser
from smarttypes.model.twitter_group import TwitterGroup
TwitterUser.time_context = datetime(2011,11,1)
TwitterGroup.time_context = datetime(2011,11,1)

f = open('/home/timmyt/Desktop/group_users_map.pkl', 'r')
group_users_map = cPickle.load(f)
#f = open('/home/timmyt/Desktop/user_groups_map.pkl', 'r')
#user_groups_map = cPickle.load(f)

group_top_users = {}
for i in group_users_map:
    group_top_users[i] = [(x[0], TwitterUser.get_by_id(x[1])) for x in heapq.nlargest(10, group_users_map[i])]
    
def show_details(group_index):
    for x in group_top_users[group_index]:
        print x[0], x[1].screen_name, x[1].description[:100]