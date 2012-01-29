
from smarttypes.graphreduce import GraphReduce
from datetime import datetime
import numpy as np
from collections import defaultdict
import networkx

import smarttypes, random
from smarttypes.utils.postgres_handle import PostgresHandle
from smarttypes.model.postgres_base_model import PostgresBaseModel
postgres_handle = PostgresHandle(smarttypes.connection_string)
PostgresBaseModel.postgres_handle = postgres_handle

from smarttypes.model.twitter_user import TwitterUser
from smarttypes.model.twitter_group import TwitterGroup
from smarttypes.model.twitter_reduction import TwitterReduction


if __name__ == "__main__":

    ########################
    ##reduce
    ########################
    #follower_followies_map, followers, followies = {}, [], []
    #root_user = TwitterUser.by_screen_name('edchedch')
    root_user = TwitterUser.by_screen_name('SmartTypes')
    follower_followies_map, followers, followies = root_user.get_graph_info(200)
    gr = GraphReduce(follower_followies_map, followers, followies)
    #gr.reduce_with_linloglayout()
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
    twitter_reduction = TwitterReduction.create_reduction(root_user_id, user_ids, x_coordinates, y_coordinates)
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
        group_graph.add_edges_from(group_edges)
        pagerank = networkx.pagerank(group_graph, max_iter=500)
        scores = []
        for user_id in user_ids:
            scores.append(pagerank.get(user_id, 0))
        groups.append(TwitterGroup.create_group(twitter_reduction.id, i, user_ids, scores))
    postgres_handle.connection.commit()
        
    ########################
    ##mk_tag_clouds 
    ########################
    #root_user = TwitterUser.by_screen_name('SmartTypes')
    #twitter_reduction = TwitterReduction.get_latest_reduction(root_user.id)
    TwitterGroup.mk_tag_clouds(twitter_reduction.id)
    postgres_handle.connection.commit()
    
    #results = defaultdict(list)
    #for i in range(len(gr.linloglayout_ids)):
        #user = TwitterUser.get_by_id(gr.linloglayout_ids[i])
        #for j in range(n_clusters):
            #score = gr.linloglayout_clusters[i][j]
            #results[j].append((score, user.location_name, user.description))
    #import heapq
    #heapq.nlargest(num_users, score_user_list)
        
        
        
        