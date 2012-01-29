from smarttypes.model.postgres_base_model import PostgresBaseModel
from datetime import datetime, timedelta
from smarttypes.utils import time_utils, text_parsing
import re, string, heapq, random, collections, numpy


class TwitterReduction(PostgresBaseModel):
    
    table_name = 'twitter_reduction'
    table_key = 'id'
    table_columns = [
        'root_user_id',
        'user_ids',
        'x_coordinates',
        'y_coordinates',
        'group_indices',
        'group_scores'
    ]    
    table_defaults = {}
    
    def get_user_coordinates(self):
        return_dict = {}
        for i in range(len(self.user_ids)):
            user_id = self.user_ids[i]
            x = self.x_coordinates[i]
            y = self.y_coordinates[i]
            if user_id in return_dict:
                raise Exception('This shouldnt happen.')
            return_dict[user_id] = (x,y)
        return return_dict
    
    def get_groups(self):
        from smarttypes.model.twitter_group import TwitterGroup
        return TwitterGroup.get_by_name_value('reduction_id', self.id)
    
    def get_details(self):
        details = []
        for i in range(len(self.user_ids)):
            user_id = self.user_ids[i]
            x = self.x_coordinates[i]
            y = self.y_coordinates[i]
            group_index = self.group_indices[i]
            if group_index >= 0:
                details.append({
                    'id':user_id,
                    'x':x,
                    'y':y,
                    'group_index':group_index
                })
        return details
    
    def save_group_info(self):
        group_indices = []
        group_scores = []
        groups = self.get_groups()
        for user_id in self.user_ids:
            group_memberships = []
            for group in groups:
                for i in range(len(group.user_ids)):
                    if user_id == group.user_ids[i]:
                        group_memberships.append((group.scores[i], group.index))
            group_index = -1
            group_score = 0
            if group_memberships:
                group_index = sorted(group_memberships)[0][1]
                group_score = sorted(group_memberships)[0][0]
            group_indices.append(group_index)
            group_scores.append(group_score)
        self.group_indices = group_indices
        self.group_scores = group_scores
        self.save()
    
    @classmethod
    def get_latest_reduction(cls, root_user_id):
        qry = """
        select * 
        from twitter_reduction
        where root_user_id = %(root_user_id)s
        order by createddate desc limit 1;
        """
        params = {'root_user_id':root_user_id}
        results = cls.postgres_handle.execute_query(qry, params)
        if results:
            return cls(**results[0])
        else:
            return None
    
    @classmethod
    def create_reduction(cls, root_user_id, user_ids, x_coordinates, y_coordinates):
        twitter_reduction = cls()
        twitter_reduction.root_user_id = root_user_id
        twitter_reduction.user_ids = user_ids
        twitter_reduction.x_coordinates = x_coordinates
        twitter_reduction.y_coordinates = y_coordinates
        twitter_reduction.save()
        return twitter_reduction
    
    
    
    
    