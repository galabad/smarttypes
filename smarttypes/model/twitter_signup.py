

from smarttypes.model.postgres_base_model import PostgresBaseModel


class TwitterSignup(PostgresBaseModel):

    table_name_prefix = 'twitter_signup'
    table_time_context = ''
    table_key = 'id'
    table_columns = [
        'request_key',
        'request_secret',
        'access_key',
        'access_secret',
        'twitter_id',
        'twitter_username',
        'email',
    ]    
    table_defaults = {
    }
    
    @classmethod
    def start_signup(cls, request_key, request_secret):
        return cls(request_key=request_key, request_secret=request_secret).save()

    @classmethod
    def get_by_request_key(cls, request_key):
        results = cls.get_by_name_value('request_key', request_key)
        if results:
            return results[0]
        else:
            return None

    @classmethod
    def get_by_access_key(cls, access_key):
        results = cls.get_by_name_value('access_key', access_key)
        if results:
            return results[0]
        else:
            return None
        
        
        
        