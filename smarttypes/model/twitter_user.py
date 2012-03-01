

from smarttypes.model.postgres_base_model import PostgresBaseModel
# from smarttypes import model
from types import NoneType
from datetime import datetime, timedelta
import numpy, random, heapq
import collections, csv, sys
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
    RELOAD_FOLLOWING_THRESHOLD = timedelta(days=14)
    TRY_AGAIN_AFTER_FAILURE_THRESHOLD = timedelta(days=31)

    @property
    def credentials(self):
        from smarttypes.model.twitter_credentials import TwitterCredentials
        creds = TwitterCredentials.get_by_twitter_id(self.id, self.postgres_handle)
        if not creds:
            creds = TwitterCredentials.get_by_root_user_id(self.id, self.postgres_handle)
        return creds

    def set_graph_time_context(self, at_this_datetime):
        self._at_this_datetime = at_this_datetime

    def get_graph_time_context(self):
        if not '_at_this_datetime' in self.__dict__:
            return self.last_loaded_following_ids
        else:
            return self._at_this_datetime

    @property
    def following_ids(self):
        if not '_following_ids' in self.__dict__:
            time_context = self.get_graph_time_context()
            if not time_context:
                self._following_ids = []
            else:
                pre_params = {
                    'postfix': time_context.strftime('%Y_%U'),
                    'user_id': '%(user_id)s',
                }
                qry = """
                select *
                from twitter_user_following_%(postfix)s
                where twitter_user_id = %(user_id)s
                ;
                """ % pre_params
                params = {
                    'user_id': self.id
                }
                results = self.postgres_handle.execute_query(qry, params)
                if not results:
                    self._following_ids = []
                else:
                    self._following_ids = results[0]['following_ids']
        return self._following_ids

    @property
    def following(self):
        return self.get_by_ids(self.following_ids, self.postgres_handle)

    @property
    def following_following_ids(self):
        return_ids = set(self.following_ids)
        for following in self.following:
            for following_following_id in following.following_ids:
                return_ids.add(following_following_id)
        return list(return_ids)

    @property
    def following_and_expired_ids(self):
        following_in_db = self.following
        following_in_db_ids = set([x.id for x in following_in_db])
        not_in_db = set(self.following_ids).difference(following_in_db_ids)
        return_list = list(not_in_db)
        for user in following_in_db:
            if user.is_expired:
                return_list.append(user.id)
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

    def get_random_followie_id(self, not_in_this_list=[], attempts=0):
        random_index = random.randrange(0, len(self.following_ids))
        random_id = self.following_ids[random_index]
        if random_id in not_in_this_list and attempts < sys.getrecursionlimit():
            attempts += 1
            return self.get_random_followie_id(not_in_this_list, attempts)
        else:
            return random_id

    def get_id_of_someone_in_my_network_to_load(self):
        #get_id_of_someone_in_my_network_to_load
        """
        'loading' a user means storing all the edges to the people they follow (followies)
        """
        #the people self follows
        following_and_expired_list = self.following_and_expired_ids
        if following_and_expired_list:
            return following_and_expired_list[0]

        #the people self follows follows
        else:
            tried_to_load_these_ids = []
            for i in range(200):  # give up at some point (this could be anything)
                random_following_id = self.get_random_followie_id(tried_to_load_these_ids)
                random_following = TwitterUser.get_by_id(random_following_id, self.postgres_handle)
                random_following_following_and_expired_list = random_following.following_and_expired_ids
                if random_following_following_and_expired_list:
                    return random_following_following_and_expired_list[0]
                else:
                    tried_to_load_these_ids.append(random_following_id)

    def get_graph_info(self, distance=100, min_followers=60):
        unique_followers = set([self.id])
        follower_followies_map = {self.id: set(self.following_ids)}
        for following in self.following:
            if following.followers_count < min_followers:
                continue
            if following.following_ids and following.id not in unique_followers:
                unique_followers.add(following.id)
                follower_followies_map[following.id] = set(following.following_ids)
            for following_following in following.following[:distance]:
                if following_following.followers_count < min_followers:
                    continue
                if following_following.following_ids and following_following.id not in unique_followers:
                    unique_followers.add(following_following.id)
                    follower_followies_map[following_following.id] = set(following_following.following_ids)
        return follower_followies_map

    ##############################################
    ##group related stuff
    ##############################################
    def top_groups(self, num_groups=10):
        from smarttypes.model.twitter_group import TwitterGroup
        return_list = []
        i = 0
        for score, group_id in sorted(self.scores_groups, reverse=True):
            if i <= num_groups and score > .001:
                return_list.append((score, TwitterGroup.get_by_index(group_id, self.postgres_handle)))
            else:
                break
            i += 1
        return return_list

    def save_following_ids(self, following_ids):
        pre_params = {
            'postfix': datetime.now().strftime('%Y_%U'),
            'user_id': '%(user_id)s',
            'following_ids': '%(following_ids)s',
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
            'postfix': datetime.now().strftime('%Y_%U'),
            'user_id': '%(user_id)s',
        }
        results = self.postgres_handle.execute_query(select_sql, {'user_id': self.id})
        if len(results):
            use_this_sql = update_sql
        else:
            use_this_sql = insert_sql

        params = {
            'user_id': self.id,
            'following_ids': following_ids,
        }
        self.postgres_handle.execute_query(use_this_sql, params, return_results=False)
        self.last_loaded_following_ids = datetime.now()
        self.save()

    ##############################################
    ##class methods
    ##############################################
    @classmethod
    def by_screen_name(cls, screen_name, postgres_handle):
        results = cls.get_by_name_value('screen_name', screen_name, postgres_handle)
        if results:
            return results[0]
        else:
            return None

    @classmethod
    def mk_following_following_csv(cls, screen_name, file_like, postgres_handle):
        user = cls.by_screen_name(screen_name, postgres_handle)
        properties = copy(cls.table_columns)
        properties[0:0] = ['createddate', 'modifieddate']
        properties.remove('caused_an_error')
        properties.remove('following_ids')
        try:
            writer = csv.writer(file_like)
            writer.writerow(properties + ['following_ids'])
            for following in cls.get_by_ids(user.following_following_ids, postgres_handle):
                initial_stuff = [str(following.__dict__.get(x)) for x in properties]
                following_ids_str = '::'.join(following.following_ids)
                writer.writerow(initial_stuff + [following_ids_str])
        finally:
            file_like.close()

    @classmethod
    def upsert_from_api_user(cls, api_user, postgres_handle):
        if api_user.protected == None:
            api_user.protected = False

        model_user = cls.get_by_id(api_user.id_str, postgres_handle)
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
                'id': api_user.id_str,
                'twitter_account_created': api_user.created_at,
                'screen_name': api_user.screen_name,
                'protected': api_user.protected,
                'time_zone': api_user.time_zone,
                'lang': api_user.lang,
                'location_name': api_user.location,
                'description': api_user.description,
                'url': api_user.url,
                'following_count': api_user.friends_count,
                'followers_count': api_user.followers_count,
                'statuses_count': api_user.statuses_count,
                'favourites_count': api_user.favourites_count,
            }
            model_user = cls(postgres_handle=postgres_handle, **properties)
        model_user.save()
        return model_user
