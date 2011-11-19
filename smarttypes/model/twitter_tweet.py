

from smarttypes.model.postgres_base_model import PostgresBaseModel


class TwitterTweet(PostgresBaseModel):

    table_name_prefix = 'twitter_tweet'
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
    
    @classmethod
    def upsert_from_api_tweet(cls, api_tweet):
            
        model_tweet = cls.get_by_id(api_tweet.id_str)
        if not model_tweet:
            properties = {
                'id':api_tweet.id_str,
                'author_id':api_tweet.author.id_str,
                'retweet_count':int(str(api_tweet.retweet_count).replace('+', '')),
                'tweet_text':api_tweet.text,
            }
            model_tweet = cls(**properties)
            try:
                model_tweet.save()
            except Exception, ex:
                #was it inserted by another process?
                
                model_tweet = cls.get_by_id(api_tweet.id_str)
                if not model_tweet:
                    raise Exception('Not sure whats happening?')
            
        return model_tweet

        


        
        
        
        