

from smarttypes.model.postgres_base_model import PostgresBaseModel


class TwitterTweets(PostgresBaseModel):
    """"""
    
    @classmethod
    def upsert_from_api_tweet(cls, api_tweet):
        
        import pprint
        print pprint.pprint(api_user.__dict__)
            
        #model_tweet = cls.get_by_id(api_tweet.id)
        #if model_tweet:
            #model_tweet.screen_name = mk_valid_ascii_str(api_tweet.screen_name)
        #else:
            #properties = {
                #'twitter_id':api_tweet.id,
            #}
            #model_tweet = cls(**properties)
        #model_tweet.save()
        #return model_tweet

        


        
        
        
        