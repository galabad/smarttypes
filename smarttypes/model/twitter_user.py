

from smarttypes.model.postgres_base_model import PostgresBaseModel

from types import NoneType
from datetime import datetime, timedelta
import numpy, random, heapq
import collections



class TwitterUser(PostgresBaseModel):
        
    table_name_prefix = 'twitter_user'
    table_time_context = '%Y_%U'
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
        
        'following_ids',
        'following_count',
        'followers_count',
        'statuses_count',
        'favourites_count',
        'caused_an_error',
    ]
    table_defaults = {
        #'following_ids':[],
    }
    
    MAX_FOLLOWING_COUNT = 1000
    TRY_AGAIN_AFTER_FAILURE_THRESHOLD = timedelta(days=31)

    @property
    def following_ids_default(self):
        if not self.following_ids:
            return []
        else:
            return self.following_ids
    
    @property
    def following(self):
        return self.get_by_ids(self.following_ids)

    @property
    def following_following_ids(self):
        return_ids = set()
        for following in self.following:
            return_ids.add(following.id)
            for following_following_id in following.following_ids_default:
                return_ids.add(following_following_id)
        return list(return_ids)  
    
    @property
    def following_and_expired(self):
        return_list = []
        for user in self.following:            
            if user.should_we_query_this_user:
                return_list.append(user)
        return return_list
    
    @property
    def should_we_query_this_user(self):
        return type(self.following_ids) == NoneType and \
               self.following_count <= self.MAX_FOLLOWING_COUNT and \
               not self.caused_an_error and \
               not self.protected
    
    def get_random_followie_id(self, not_in_this_list=[]):
        random_index = random.randrange(0, len(self.following_ids_default)) 
        random_id = self.following_ids_default[random_index]
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
            for i in range(len(self.following_ids_default)): #give up at some point (this could be anything)
                random_following_id = self.get_random_followie_id(tried_to_load_these_ids)
                print random_following_id
                random_following = TwitterUser.get_by_id(random_following_id)
                random_following_following_and_expired_list = random_following.following_and_expired
                if random_following_following_and_expired_list:
                    return random_following_following_and_expired_list[0]
                else:
                    tried_to_load_these_ids.append(random_following_id)
        

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
            #if user_id not in self.following_ids_default:
                #return_list.append(TwitterUser.get_by_id(user_id))
        #return return_list
    
    
    ##############################################
    ##state changing methods
    ##############################################    
    def save_following_ids(self, following_ids):
        self.following_ids = list(set(following_ids))
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
        


        
        
        
        