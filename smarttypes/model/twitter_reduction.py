
from smarttypes.model.postgres_base_model import PostgresBaseModel


class TwitterReduction(PostgresBaseModel):

    table_name = 'twitter_reduction'
    table_key = 'id'
    table_columns = [
        'root_user_id',
        'user_ids',
        'x_coordinates',
        'y_coordinates',
        'group_indices',
        'group_scores',
        'in_links',
        'out_links',
    ]
    table_defaults = {}

    def get_groups(self):
        from smarttypes.model.twitter_group import TwitterGroup
        return TwitterGroup.get_by_name_value('reduction_id', self.id, self.postgres_handle)

    def get_details(self, return_all=False):
        details = []
        for i in range(len(self.user_ids)):
            user_id = self.user_ids[i]
            x = self.x_coordinates[i]
            y = self.y_coordinates[i]
            group_index = self.group_indices[i]
            if group_index >= 0 or return_all:
                details.append({
                    'id': user_id,
                    'x': x,
                    'y': y,
                    'group_index': group_index
                })
        return details

    def get_in_and_out_links_for_user(self, user_id):

        in_links, out_links = [], []
        for i in range(len(self.user_ids)):
            iter_user_id = self.user_ids[i]
            if iter_user_id == user_id:
                in_links_str = self.in_links[i]
                out_links_str = self.out_links[i]
                if in_links_str:
                    in_links = in_links_str.split(self.spliter)
                if out_links_str:
                    out_links = out_links_str.split(self.spliter)
                return in_links, out_links
        return [], []

    def save_group_info(self, postgres_handle):
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
    def get_latest_reduction(cls, root_user_id, postgres_handle):
        qry = """
        select *
        from twitter_reduction
        where root_user_id = %(root_user_id)s
        order by createddate desc limit 1;
        """
        params = {'root_user_id': root_user_id}
        results = postgres_handle.execute_query(qry, params)
        if results:
            return cls(postgres_handle=postgres_handle, **results[0])
        else:
            return None

    @classmethod
    def get_ordered_id_list(cls, root_user_id, postgres_handle):
        qry = """
        select id
        from twitter_reduction
        where root_user_id = %(root_user_id)s
        order by createddate asc;
        """
        return_list = []
        params = {'root_user_id': root_user_id}
        for result in postgres_handle.execute_query(qry, params):
            return_list.append(result['id'])
        return return_list

    @classmethod
    def get_users_with_a_reduction(cls, postgres_handle):
        from smarttypes.model.twitter_user import TwitterUser
        return_users = []
        qry = """
        select distinct root_user_id
        from twitter_reduction
        order by root_user_id;
        """
        for result in postgres_handle.execute_query(qry):
            user = TwitterUser.get_by_id(result['root_user_id'], postgres_handle)
            return_users.append(user)
        return return_users

    @classmethod
    def get_user_reduction_counts(cls, postgres_handle):
        from smarttypes.model.twitter_user import TwitterUser
        return_users = []
        qry = """
        select root_user_id, count(root_user_id) as reduction_count
        from twitter_reduction
        group by root_user_id;
        """
        for result in postgres_handle.execute_query(qry):
            user = TwitterUser.get_by_id(result['root_user_id'], postgres_handle)
            return_users.append((user, result['reduction_count']))
        return return_users

    @classmethod
    def create_reduction(cls, root_user_id, user_ids, 
            x_coordinates, y_coordinates, in_links, out_links, postgres_handle):
        twitter_reduction = cls(postgres_handle=postgres_handle)
        twitter_reduction.root_user_id = root_user_id
        twitter_reduction.user_ids = user_ids
        twitter_reduction.x_coordinates = x_coordinates
        twitter_reduction.y_coordinates = y_coordinates
        twitter_reduction.in_links = in_links
        twitter_reduction.out_links = out_links
        twitter_reduction.save()
        return twitter_reduction
