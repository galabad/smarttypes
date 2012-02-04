
from smarttypes.model.postgres_base_model import PostgresBaseModel
from datetime import datetime, timedelta
from smarttypes.utils import time_utils, text_parsing
import re, string, heapq, random, collections, numpy
import networkx

class TwitterGroup(PostgresBaseModel):
        
    table_name = 'twitter_group'
    table_key = 'id'
    table_columns = [
        'reduction_id',
        'index',
        'user_ids',
        'scores',
        'tag_cloud',
    ]    
    table_defaults = {}
    
    def get_members(self):
        return_list = []
        for i in range(len(self.user_ids)):
            user_id = self.user_ids[i]
            score = self.scores[i]
            return_list.append((score, user_id))
        return return_list
    
    def top_users(self, num_users=20, just_ids=False):
        from smarttypes.model.twitter_user import TwitterUser
        return_list = []
        score_user_id_tup_list = self.get_members()
        for score, user_id in heapq.nlargest(num_users, score_user_id_tup_list):
            if score:
                add_this = (score, user_id)
                if not just_ids: add_this = (score, TwitterUser.get_by_id(user_id, self.postgres_handle))
                return_list.append(add_this)
            else:
                break
        return return_list
        

    ##############################################
    ##class methods
    ##############################################
    @classmethod
    def all_groups(cls, reduction_id, postgres_handle):
        return cls.get_by_name_value('reduction_id', reduction_id, postgres_handle)
    
    @classmethod
    def get_by_index(cls, reduction_id, index, postgres_handle):
        qry = """
        select * 
        from twitter_group
        where reduction_id = %(reduction_id)s
            and index = %(index)s;
        """
        params = {'reduction_id':reduction_id, 'index':index}
        results = postgres_handle.execute_query(qry, params)
        if results:
            return cls(postgres_handle=postgres_handle, **results[0])
        else:
            return None
    
    @classmethod
    def create_group(cls, reduction_id, index, user_ids, scores, postgres_handle):
        twitter_group = cls(postgres_handle=postgres_handle)
        twitter_group.reduction_id = reduction_id
        twitter_group.index = index
        twitter_group.user_ids = user_ids
        twitter_group.scores = scores
        twitter_group.save()
        return twitter_group
        
    @classmethod
    def mk_tag_clouds(cls, reduction_id, postgres_handle):
        
        print "starting group_wordcounts loop"
        group_wordcounts = {}
        all_words = set()
        for group in cls.all_groups(reduction_id, postgres_handle):
            group_wordcounts[group.index] = (group, collections.defaultdict(int))
            for score, user in group.top_users(num_users=25):
                if not user.description:
                    continue
                regex = re.compile(r'[%s\s]+' % re.escape(string.punctuation))
                user_words = set()
                user.description = '' if not user.description else user.description
                user.location_name = '' if not user.location_name else user.location_name
                loc_desc = '%s %s' % (user.description.strip(), user.location_name.strip())
                for word in regex.split(loc_desc):
                    word = string.lower(word)
                    if len(word) > 2 and word not in user_words:
                        user_words.add(word)
                        all_words.add(word)
                        group_wordcounts[group.index][1][word] += (1 + (score * 5))
                        
        print "starting avg_wordcounts loop"            
        avg_wordcounts = {} #{word:avg}
        sum_words = []#[(sum,word)]
        for word in all_words:
            group_usage = []
            for group_index in group_wordcounts:
                group_usage.append(group_wordcounts[group_index][1][word])
            avg_wordcounts[word] = numpy.average(group_usage)
            sum_words.append((numpy.sum(group_usage), word))        
        
        print "starting delete stop words loop"
        for group_index in group_wordcounts:
            for word in text_parsing.STOPWORDS:
                if word in group_wordcounts[group_index][1]:
                    del group_wordcounts[group_index][1][word]     
                
        print "starting groups_unique_words loop"
        groups_unique_words = {} #{group_index:[(score, word)]}
        for group_index in group_wordcounts:
            groups_unique_words[group_index] = []
            for word, times_used in group_wordcounts[group_index][1].items():
                if times_used > 2.5:
                    usage_diff = times_used - avg_wordcounts[word]
                    groups_unique_words[group_index].append((usage_diff, word))
        
        print "starting save tag_cloud loop"
        for group_index, unique_scores in groups_unique_words.items():
            group = group_wordcounts[group_index][0]
            group.tag_cloud = [x[1] for x in heapq.nlargest(10, unique_scores)]
            group.save()
        
        return "All done!"
        
        
        