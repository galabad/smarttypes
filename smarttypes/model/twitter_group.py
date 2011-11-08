from smarttypes.model.postgres_base_model import PostgresBaseModel
from datetime import datetime, timedelta
from smarttypes.utils import time_utils, text_parsing
import re, string, heapq, random, collections, numpy
#from smarttypes.utils.log_handle import LogHandle
#log_handle = LogHandle('twitter_group.log')

class TwitterGroup(PostgresBaseModel):
        
    table_name_prefix = 'twitter_group'
    table_time_context = '%Y_%U'
    table_key = 'id'
    table_columns = [
        'id',
        'author_id',
        'retweet_count',
        'tweet_text',
    ]    
    table_defaults = {
        #'following_ids':[],
    }
    
    
    def tag_cloud_display(self):
        return ' '.join([x[1] for x in self.tag_cloud])
    
    def top_users(self, num_users=20, just_ids=False):
        from smarttypes.model.twitter_user import TwitterUser
        
        return_list = []
        i = 0
        for score, user_id in sorted(self.scores_users, reverse=True):
            if i <= num_users and score > .001:
                add_this = (score, user_id)
                if not just_ids: add_this = (score, TwitterUser.get_by_id(user_id))
                return_list.append(add_this)
            else:
                break
            i += 1
        return return_list
        

    ##############################################
    ##class methods
    ############################################## 
    @classmethod
    def get_all_groups(cls, count=False):
        results = cls.collection().find()
        if count:
            return results.count()
        else:
            return_list = []
            for result in results:
                return_list.append(cls(**result))
            return return_list
        
    @classmethod
    def get_by_index(cls, group_index):
        return cls(**cls.collection().find_one({'group_index':group_index}))
    
    @classmethod
    def get_random_group(cls):
        num_groups = cls.get_all_groups(count=True)
        random_index = random.randrange(0, num_groups) 
        random_group = cls.get_by_index(random_index)
        if random_group.scores_users:
            return random_group
        else:
            return cls.get_random_group()
    
    @classmethod
    def upsert_group(cls, group_index, scores_users, scores_groups):
        properties = {
            'group_index': group_index,
            'scores_users':scores_users,
            'scores_groups':scores_groups,
        }
        twitter_group = cls(**properties)
        twitter_group.save()


                
            
            
        