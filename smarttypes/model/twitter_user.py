

from smarttypes.model.postgres_base_model import PostgresBaseModel
from smarttypes import model
from types import NoneType
from datetime import datetime, timedelta
import numpy, random, heapq
import collections, csv
from copy import copy



class TwitterUser(PostgresBaseModel):
        
    table_name = 'twitter_user'
    table_key = 'id'
    table_columns = [
        'id',
        'twitter_account_created',
        'screen_name',
        'protected',
        
        'time_zone',
        'lang',
        'location_name',
        'description',
        'url',
        
        'following_count',
        'followers_count',
        'statuses_count',
        'favourites_count',
        
        'last_loaded_following_ids',
        'caused_an_error',
    ]
    table_defaults = {
        #'following_ids':[],
    }
    
    MAX_FOLLOWING_COUNT = 1000
    RELOAD_FOLLOWING_THRESHOLD = timedelta(days=7)
    TRY_AGAIN_AFTER_FAILURE_THRESHOLD = timedelta(days=31)

    @property
    def credentials(self):
        return model.twitter_credentials.TwitterCredentials.get_by_twitter_id(self.id)
    
    def get_following_ids_at_certain_time(self, at_this_datetime):
        if not at_this_datetime:
            raise Exception('get_following_ids_at_certain_time needs a specific datetime')
        pre_params = {
            'postfix':at_this_datetime.strftime('%Y_%U'),
            'user_id':'%(user_id)s',
        }
        qry = """
        select * 
        from twitter_user_following_%(postfix)s
        where twitter_user_id = %(user_id)s
        ;
        """ % pre_params
        params = {
            'user_id':self.id
        }
        results = self.postgres_handle.execute_query(qry, params)
        if not results:
            return []
        else:
            return results[0]['following_ids']
        
    @property
    def following_ids(self):
        if not self.last_loaded_following_ids:
            return []
        return self.get_following_ids_at_certain_time(self.last_loaded_following_ids)
    
    @property
    def following(self):
        return self.get_by_ids(self.following_ids)

    @property
    def following_following_ids(self):
        return_ids = set(self.following_ids)
        for following in self.following:
            for following_following_id in following.following_ids:
                return_ids.add(following_following_id)
        return list(return_ids)  
    
    @property
    def following_and_expired(self):
        return_list = []
        for user in self.following:            
            if user.is_expired:
                return_list.append(user)
        return return_list
    
    @property
    def is_expired(self):
        expired = True
        if self.last_loaded_following_ids and \
           (datetime.now() - self.last_loaded_following_ids) < self.RELOAD_FOLLOWING_THRESHOLD:
            expired = False
        return expired and \
               self.following_count <= self.MAX_FOLLOWING_COUNT and \
               not self.caused_an_error and \
               not self.protected
    
    def get_random_followie_id(self, not_in_this_list=[]):
        random_index = random.randrange(0, len(self.following_ids)) 
        random_id = self.following_ids[random_index]
        if random_id in not_in_this_list:
            return self.get_random_followie_id(not_in_this_list)
        else:
            return random_id
        
    def get_someone_in_my_network_to_load(self):
        """
        keep in mind that 'loading' a user means storing all their connections
        we try to load self, the people self follows, and the people self follows follows
        """
        
        #the people self follows
        following_and_expired_list = self.following_and_expired
        if following_and_expired_list:
            return following_and_expired_list[0]
        
        #the people self follows follows
        else:
            tried_to_load_these_ids = []
            for i in range(len(self.following_ids)): #give up at some point (this could be anything)
                random_following_id = self.get_random_followie_id(tried_to_load_these_ids)
                print random_following_id
                random_following = TwitterUser.get_by_id(random_following_id)
                random_following_following_and_expired_list = random_following.following_and_expired
                if random_following_following_and_expired_list:
                    return random_following_following_and_expired_list[0]
                else:
                    tried_to_load_these_ids.append(random_following_id)
                    
    def get_graph_info(self, distance=10, min_followers=35):
        unique_followers = set([self.id])
        unique_followies = set(self.following_ids)
        follower_followies_map = {self.id:set(self.following_ids)}
        for following in self.following:
            if following.followers_count < min_followers:
                continue
            if following.following_ids and following.id not in follower_followies_map:
                unique_followers.add(following.id)
                unique_followies = unique_followies.union(following.following_ids)
                follower_followies_map[following.id] = set(following.following_ids)
                
            for following_following in following.following[:distance]:
                if following_following.followers_count < min_followers:
                    continue
                if following_following.following_ids and following_following.id not in follower_followies_map:
                    unique_followers.add(following_following.id)
                    unique_followies = unique_followies.union(following_following.following_ids)
                    follower_followies_map[following_following.id] = set(following_following.following_ids)
                    
        return follower_followies_map, list(unique_followers), list(unique_followies)

    ##############################################
    ##group related stuff
    ##############################################
    def top_groups(self, num_groups=10):
        from smarttypes.model.twitter_group import TwitterGroup
        return_list = []
        i = 0
        for score, group_id in sorted(self.scores_groups, reverse=True):
            if i <= num_groups and score > .001:
                return_list.append((score, TwitterGroup.get_by_index(group_id)))
            else:
                break
            i += 1
        return return_list
    
    
    
    
    #def group_inferred_following(self, num_users, just_ids=True):
        #from smarttypes.model.twitter_group import TwitterGroup
        #user_score_map = {}
        #for following_group_score, group_index in self.following_groups:
            #for following_user_score, user_id in TwitterGroup.get_by_index(group_index).following:
                #if user_id not in user_score_map:
                    #user_score_map[user_id] = following_group_score * following_user_score
                #else:
                    #user_score_map[user_id] += following_group_score * following_user_score
        
        #return_list = []
        #score_user_list = [(y,x) for x,y in user_score_map.items()]
        #for score, user_id in heapq.nlargest(num_users, score_user_list):
            #add_this = user_id
            #if not just_ids:
                #add_this = TwitterUser.get_by_id(user_id)
            #return_list.append(add_this)
        #return return_list
        
    #def who_to_follow(self, num_users):
        #return_list = []
        #for user_id in self.group_inferred_following(num_users):
            #if user_id not in self.following_ids:
                #return_list.append(TwitterUser.get_by_id(user_id))
        #return return_list
    
    
    ##############################################
    ##state changing methods
    ##############################################    
    def save_following_ids(self, following_ids):
        pre_params = {
            'postfix':datetime.now().strftime('%Y_%U'),
            'user_id':'%(user_id)s',
            'following_ids':'%(following_ids)s',
        }
        insert_sql = """
        insert into twitter_user_following_%(postfix)s (twitter_user_id, following_ids)
        values(%(user_id)s, %(following_ids)s);
        """ % pre_params
        
        update_sql = """
        update twitter_user_following_%(postfix)s 
        set following_ids = %(following_ids)s
        where twitter_user_id = %(user_id)s;
        """ % pre_params
        
        select_sql = """
        select * from twitter_user_following_%(postfix)s
        where twitter_user_id = %(user_id)s;
        """ % {
            'postfix':datetime.now().strftime('%Y_%U'),
            'user_id':'%(user_id)s',
        }
        results = self.postgres_handle.execute_query(select_sql, {'user_id':self.id})
        if len(results):
            use_this_sql = update_sql
        else:
            use_this_sql = insert_sql
        
        params = {
            'user_id':self.id,
            'following_ids':following_ids,
        }
        self.postgres_handle.execute_query(use_this_sql, params, return_results=False)
        self.last_loaded_following_ids = datetime.now()
        self.save()    
        
    ##############################################
    ##class methods
    ##############################################    
    @classmethod
    def by_screen_name(cls, screen_name):
        results = cls.get_by_name_value('screen_name', screen_name)
        if results:
            return results[0]
        else:
            return None
        
    @classmethod
    def mk_following_following_csv(cls, screen_name, file_like, ):
        user = cls.by_screen_name(screen_name)
        properties = copy(cls.table_columns)
        properties[0:0] = ['createddate', 'modifieddate']
        properties.remove('caused_an_error')
        properties.remove('following_ids')
        try:
            writer = csv.writer(file_like)
            writer.writerow(properties + ['following_ids'])
            for following in cls.get_by_ids(user.following_following_ids):
                initial_stuff = [str(following.__dict__.get(x)) for x in properties]
                following_ids_str = '::'.join(following.following_ids)
                writer.writerow(initial_stuff + [following_ids_str])
        finally:
            file_like.close()
        
    @classmethod
    def upsert_from_api_user(cls, api_user):
        if api_user.protected == None:
            api_user.protected = False

        #import pprint
        #print pprint.pprint(api_user.__dict__)
            
        model_user = cls.get_by_id(api_user.id_str)
        if model_user:
            model_user.screen_name = api_user.screen_name
            model_user.protected = api_user.protected
            
            model_user.time_zone = api_user.time_zone
            model_user.lang = api_user.lang
            model_user.location_name = api_user.location
            model_user.description = api_user.description
            model_user.url = api_user.url            
            
            model_user.following_count = api_user.friends_count
            model_user.followers_count = api_user.followers_count
            model_user.statuses_count = api_user.statuses_count
            model_user.favourites_count = api_user.favourites_count
            
        else:
            properties = {
                'id':api_user.id_str,
                'twitter_account_created':api_user.created_at,
                'screen_name':api_user.screen_name,                 
                'protected':api_user.protected,
                
                'time_zone':api_user.time_zone,
                'lang':api_user.lang,
                'location_name':api_user.location, 
                'description':api_user.description, 
                'url':api_user.url,
                
                'following_count':api_user.friends_count,
                'followers_count':api_user.followers_count,
                'statuses_count':api_user.statuses_count,
                'favourites_count':api_user.favourites_count,
            }
            model_user = cls(**properties)
        model_user.save()
        return model_user
        


        
        
        
        