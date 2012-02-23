

from model.postgres_base_model import PostgresBaseModel
import tweepy
from config import *
# from smarttypes import model


class TwitterSession(PostgresBaseModel):

    table_name = 'twitter_session'
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
        from smarttypes.model.twitter_credentials import TwitterCredentials
        if not self.access_key:
            return None
        return TwitterCredentials.get_by_access_key(self.access_key, self.postgres_handle)

    @classmethod
    def create(cls, request_key, request_secret, postgres_handle):
        return cls(postgres_handle=postgres_handle,
                   request_key=request_key, request_secret=request_secret).save()

    @classmethod
    def get_by_request_key(cls, request_key, postgres_handle):
        results = cls.get_by_name_value('request_key', request_key, postgres_handle)
        if results:
            return results[0]
        else:
            return None
