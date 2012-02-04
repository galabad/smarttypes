
from smarttypes.graphreduce import GraphReduce
from datetime import datetime
import numpy as np
from collections import defaultdict
import networkx

import smarttypes, random
from smarttypes.utils.postgres_handle import PostgresHandle
postgres_handle = PostgresHandle(smarttypes.connection_string)

from smarttypes.model.twitter_user import TwitterUser
from smarttypes.model.twitter_group import TwitterGroup
from smarttypes.model.twitter_reduction import TwitterReduction


if __name__ == "__main__":

    ########################
    ##reduce
    ########################
    #follower_followies_map, followers = {}, []
    #root_user = TwitterUser.by_screen_name('edchedch', postgres_handle)
    root_user = TwitterUser.by_screen_name('SmartTypes', postgres_handle)
    follower_followies_map, followers = root_user.get_graph_info(20,60)
    gr = GraphReduce(follower_followies_map, followers)
    gr.reduce_with_linloglayout()
    gr.load_linloglayout_from_file()
    
    ########################
    ##save reduction    
    ########################
    root_user_id = root_user.id
    user_ids = []
    x_coordinates = []
    y_coordinates = []
    for i in range(len(gr.linloglayout_ids)):
        user_ids.append(gr.linloglayout_ids[i])
        x_coordinates.append(gr.linloglayout_reduction[i][0])
        y_coordinates.append(gr.linloglayout_reduction[i][1])
    twitter_reduction = TwitterReduction.create_reduction(root_user_id, user_ids, x_coordinates, y_coordinates, postgres_handle)
    postgres_handle.connection.commit()
    
    ########################
    ##create groups    
    ########################
    #gr.find_kmeans_clusters(n_clusters=30)
    gr.find_dbscan_clusters(eps=0.48, min_samples=14)
    
    ########################
    ##save groups    
    ########################
    groups = []
    for i in range(gr.n_clusters):
        user_ids = []
        for j in range(len(gr.linloglayout_ids)):
            if gr.linloglayout_clusters[j][i] > 0:
                user_ids.append(gr.linloglayout_ids[j])
        #run pagerank to get the scores
        group_graph = networkx.DiGraph()
        group_edges = []
        for user_id in user_ids:
            if user_id in follower_followies_map:
                for following_id in set(user_ids).intersection(follower_followies_map[user_id]):
                    group_edges.append((user_id, following_id))
        print len(user_ids), len(group_edges)
        if not group_edges:
            continue
        group_graph.add_edges_from(group_edges)
        pagerank = networkx.pagerank(group_graph, max_iter=500)
        scores = []
        for user_id in user_ids:
            scores.append(pagerank.get(user_id, 0))
        groups.append(TwitterGroup.create_group(twitter_reduction.id, i, user_ids, scores, postgres_handle))
    postgres_handle.connection.commit()
    
    twitter_reduction.save_group_info(postgres_handle)
    postgres_handle.connection.commit()
        
    ########################
    ##mk_tag_clouds 
    ########################
    TwitterGroup.mk_tag_clouds(twitter_reduction.id, postgres_handle)
    postgres_handle.connection.commit()
    
    
        
        
        
        