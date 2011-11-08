

from smarttypes.model.postgres_base_model import PostgresBaseModel
import tweepy
from smarttypes.config import *
from smarttypes import model

class TwitterCredentials(PostgresBaseModel):

    table_name_prefix = 'twitter_credentials'
    table_time_context = ''
    table_key = 'access_key'
    table_columns = [
        'access_key',
        'access_secret',
        'twitter_id',
        'email',
    ]    
    table_defaults = {}
    
    @property
    def auth_handle(self):
        auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
        auth.set_access_token(self.access_key, self.access_secret)
        return auth
    
    @property
    def api_handle(self):
        return tweepy.API(self.auth_handle)
    
    @property
    def twitter_user(self):
        if not self.twitter_id or not model.twitter_user.TwitterUser.get_by_id(self.twitter_id):
            user = model.twitter_user.TwitterUser.upsert_from_api_user(self.api_handle.me())
            self.twitter_id = user.id
            self.save()
            return user
        else:
            return model.twitter_user.TwitterUser.get_by_id(self.twitter_id)

    @classmethod
    def create(cls, access_key, access_secret):
        return cls(access_key=access_key, access_secret=access_secret).save()
    
    @classmethod
    def get_by_access_key(cls, access_key):
        results = cls.get_by_name_value('access_key', access_key)
        if results:
            return results[0]
        else:
            return None
        
    @classmethod
    def get_by_twitter_id(cls, twitter_id):
        results = cls.get_by_name_value('twitter_id', twitter_id)
        if results:
            return results[0]
        else:
            return None        
        
    @classmethod
    def get_all(cls):
        qry = """
        select * 
        from %(table_name)s;
        """
        params = {'table_name':cls.get_table_name()}
        results = cls.postgres_handle.execute_query(qry % params)
        return [cls(**x) for x in results]
        
        
class TwitterSession(PostgresBaseModel):

    table_name_prefix = 'twitter_session'
    table_time_context = ''
    table_key = 'request_key'
    table_columns = [
        'request_key',
        'request_secret',
        'access_key',
    ]    
    table_defaults = {
    }
    
    @property
    def credentials(self):
        if not self.access_key:
            return None
        return TwitterCredentials.get_by_access_key(self.access_key)
    
    @classmethod
    def create(cls, request_key, request_secret):
        return cls(request_key=request_key, request_secret=request_secret).save()

    @classmethod
    def get_by_request_key(cls, request_key):
        results = cls.get_by_name_value('request_key', request_key)
        if results:
            return results[0]
        else:
            return None

        