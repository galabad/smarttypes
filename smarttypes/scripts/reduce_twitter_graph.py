
from multiprocessing import Process
from smarttypes.graphreduce import GraphReduce
from datetime import datetime
import numpy as np
from collections import defaultdict
import networkx, pickle

import smarttypes, random
from smarttypes.utils.postgres_handle import PostgresHandle

from smarttypes.model.twitter_user import TwitterUser
from smarttypes.model.twitter_group import TwitterGroup
from smarttypes.model.twitter_reduction import TwitterReduction
from smarttypes.model.twitter_credentials import TwitterCredentials


def reduce_graph(screen_name, distance=20, min_followers=60, just_load_from_file=False):
    
    postgres_handle = PostgresHandle(smarttypes.connection_string)
    
    if just_load_from_file:
        print "Loading data from a pickle."
        gr = GraphReduce(screen_name, {}, [])
        f = open(gr.pickle_file_path)
        twitter_reduction, groups = pickle.load(f)
        twitter_reduction.id = None
        twitter_reduction.postgres_handle = postgres_handle
        twitter_reduction.save()
        postgres_handle.connection.commit()
        for group in groups:
            group.id = None
            group.reduction_id = twitter_reduction.id
            group.postgres_handle = postgres_handle
            group.save()
            postgres_handle.connection.commit()
        TwitterGroup.mk_tag_clouds(twitter_reduction.id, postgres_handle)
        postgres_handle.connection.commit()
        print "All done!"
        return 0
    
    ########################
    ##reduce
    ########################
    root_user = TwitterUser.by_screen_name(screen_name, postgres_handle)
    follower_followies_map, followers = root_user.get_graph_info(distance=distance, min_followers=min_followers)
    gr = GraphReduce(screen_name, follower_followies_map, followers)
    gr.reduce_with_linloglayout()
    gr.load_linloglayout_from_file()
    
    ########################
    ##save reduction in db    
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
    gr.find_dbscan_clusters(eps=0.48, min_samples=14)
    
    ########################
    ##save groups in db   
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
    
    ########################
    ##pickle it 
    ########################
    delattr(twitter_reduction, 'postgres_handle')
    for group in groups:
        delattr(group, 'postgres_handle')
    dump_this = (twitter_reduction, groups)
    f = open(gr.pickle_file_path, 'w')
    pickle.dump(dump_this, f)
    

if __name__ == "__main__":
    postgres_handle = PostgresHandle(smarttypes.connection_string)
    for creds in TwitterCredentials.get_all(postgres_handle):
        root_user = creds.root_user
        if root_user:
            distance = int(400 / (root_user.following_count / 100.0))
            reduce_graph(root_user.screen_name, distance=distance, min_followers=60, just_load_from_file=True)        
        
            
            
            