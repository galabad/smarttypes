
from graphreduce import reduce_graph, plot_embedding
from datetime import datetime
import numpy as np

import smarttypes, random
from smarttypes.utils.postgres_handle import PostgresHandle
from smarttypes.model.postgres_base_model import PostgresBaseModel
postgres_handle = PostgresHandle(smarttypes.connection_string)
PostgresBaseModel.postgres_handle = postgres_handle

from smarttypes.model.twitter_user import TwitterUser
from smarttypes.model.twitter_group import TwitterGroup
TwitterUser.time_context = datetime(2011,11,1)
TwitterGroup.time_context = datetime(2011,11,1)


if __name__ == "__main__":

    root_user = TwitterUser.by_screen_name('SmartTypes')
    adjacency_matrix, follower_ids, followie_ids = root_user.get_adjacency_matrix(3)
    print 'follower_ids: %s -- followie_ids: %s' % (len(follower_ids), len(followie_ids))
    
    f = open('/home/timmyt/Desktop/adjacency_matrix.npy', 'w')
    np.save(f, adjacency_matrix)
    
    #little test
    def test():
        i = 0
        tmp_followies = []
        random_index = random.randint(0, len(adjacency_matrix) - 1)
        for x in adjacency_matrix[random_index]:
            if x: tmp_followies.append(followie_ids[i])
            i += 1
        assert not set(tmp_followies).difference(TwitterUser.get_by_id(follower_ids[random_index]).following_ids_default)
        print "Passed our little test: following %s users!" % len(tmp_followies)        
    
    results = reduce_graph(adjacency_matrix, follower_ids, out_dim=2, n_neighbors=30, method='standard')
    plot_embedding(results, follower_ids)


