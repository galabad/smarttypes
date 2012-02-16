
import os
from collections import defaultdict
import numpy as np

#import pylab as pl
#import matplotlib
#from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
#from matplotlib.figure import Figure
#from matplotlib.axis import Axis

from sklearn.cluster import KMeans
from sklearn.neighbors import NearestNeighbors
from scipy.spatial import distance
from sklearn.cluster import DBSCAN

import networkx

class GraphReduce(object):
    
    def __init__(self, reduction_id, follower_followies_map, followers):
        self.reduction_id = reduction_id
        self.follower_followies_map = follower_followies_map
        self.followers = followers

        print "running GraphReduce on %s nodes." % len(self.followers)
        
        self.linloglayout_dir = '/home/timmyt/projects/smarttypes/smarttypes/graphreduce/LinLogLayout'
        self.input_file_name = 'io/%s_input.txt' % self.reduction_id
        self.output_file_name = 'io/%s_output.txt' % self.reduction_id
        self.pickle_file_name = 'io/%s.pickle' % self.reduction_id
        self.input_file_path = '%s/%s' % (self.linloglayout_dir, self.input_file_name)
        self.output_file_path = '%s/%s' % (self.linloglayout_dir, self.output_file_name)
        self.pickle_file_path = '%s/%s' % (self.linloglayout_dir, self.pickle_file_name)
        
        self.adjancey_matrix = None
        self.linloglayout_ids = None
        self.linloglayout_reduction = None
        self.linloglayout_clusters = None
        self.linloglayout_cluster_centers = None
        self.linloglayout_similarities = None
        
    def reduce_with_linloglayout(self):
        
        print "reduce_with_linloglayout"
        input_file = open(self.input_file_path, 'w')
        for follower, followies in self.follower_followies_map.items():
            for followie in followies:
                if followie in self.follower_followies_map:
                    input_file.write('%s %s \n' % (follower, followie))
        input_file.close()
        
        #to recompile
        #$javac -d ../bin LinLogLayout.java
        os.system('cd %s; java -cp bin LinLogLayout 2 %s %s;' % (
            self.linloglayout_dir,
            self.input_file_name,
            self.output_file_name
        ))    
    
    def load_linloglayout_from_file(self):
        
        print "load_linloglayout_from_file"
        f = open(self.output_file_path)
        self.linloglayout_reduction = []
        self.linloglayout_ids = []
        for line in f:
            line_pieces = line.split(' ')
            id = line_pieces[0]
            if id in self.linloglayout_ids:
                raise Exception('This shouldnt happen.')
            self.linloglayout_ids.append(id)
            x_value = float(line_pieces[1])
            y_value = float(line_pieces[2])
            self.linloglayout_reduction.append([x_value, y_value])
        self.linloglayout_reduction = np.array(self.linloglayout_reduction)
        self.linloglayout_reduction = self.linloglayout_reduction + abs(np.min(self.linloglayout_reduction)) + 20
        self.linloglayout_reduction = (self.linloglayout_reduction / np.max(self.linloglayout_reduction))
    
    def find_kmeans_clusters(self, n_clusters=20):
        self.n_clusters = n_clusters
        k_means = KMeans(init='k-means++', k=self.n_clusters)
        k_means.fit(self.linloglayout_reduction)
        self.linloglayout_cluster_centers = k_means.cluster_centers_
        neigh = NearestNeighbors(n_neighbors=len(self.linloglayout_ids))
        neigh.fit(self.linloglayout_reduction) 
        neigh_results = neigh.kneighbors(self.linloglayout_cluster_centers)
        #neigh_results is a 2-tuple, first data structure is distances, second is the label index
        tmp_linloglayout_clusters = defaultdict(list)
        for i in range(self.n_clusters):
            neigh_scores = 1 - (neigh_results[0][i] / np.max(neigh_results[0][i]))
            zoom = .95
            neigh_scores = (neigh_scores >= zoom) * neigh_scores
            neigh_scores = (neigh_scores-zoom) * 1/(1-zoom)
            for j in range(len(self.linloglayout_ids)):
                id_idx = neigh_results[1][i][j]
                id_score = neigh_scores[j]
                tmp_linloglayout_clusters[self.linloglayout_ids[id_idx]].append(id_score)
        self.linloglayout_clusters = []
        for id in self.linloglayout_ids:
            self.linloglayout_clusters.append(tmp_linloglayout_clusters[id])
        self.linloglayout_clusters = np.array(self.linloglayout_clusters)
                
    def find_linloglayout_similarities(self):
        self.linloglayout_similarities = distance.squareform(distance.pdist(self.linloglayout_reduction))
        self.linloglayout_similarities = 1 - (self.linloglayout_similarities / np.max(self.linloglayout_similarities))
        
    def find_dbscan_clusters(self, eps=0.65, min_samples=15):
        
        self.find_linloglayout_similarities()
        db = DBSCAN().fit(self.linloglayout_similarities, eps=eps, min_samples=min_samples)
        core_samples = db.core_sample_indices_
        labels = db.labels_
        self.n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        
        tmp_linloglayout_clusters = defaultdict(lambda: [0] * self.n_clusters)
        for i in range(len(labels)):
            id = self.linloglayout_ids[i]
            group_index = int(labels[i])
            if group_index != -1:
                tmp_linloglayout_clusters[id][group_index] = 1
        self.linloglayout_clusters = []
        for id in self.linloglayout_ids:
            self.linloglayout_clusters.append(tmp_linloglayout_clusters[id])
        self.linloglayout_clusters = np.array(self.linloglayout_clusters)
        
        
    #def plot_linloglayout(self, width_inchs=6, height_inchs=6):
        #fig = Figure(figsize=(width_inchs,height_inchs), dpi=100, frameon=False)
        #canvas = FigureCanvas(fig)
        ##add_axes takes [left, bottom, width, height]
        #ax = fig.add_axes([0, 0, 1, 1])
        #ax.axis('off')
        #ax.xaxis.set_visible(False)
        #ax.yaxis.set_visible(False)
    
        ##plot cluster centers if we have em
        #if self.linloglayout_cluster_centers != None:
            #for i in range(len(self.linloglayout_cluster_centers)):
                #ax.plot(self.linloglayout_cluster_centers[i][0], self.linloglayout_cluster_centers[i][1], 'o', 
                        #markersize=30, color='#E8E8E8', gid='cluster_%s' % str(i))        
        
        ##plot the nodes
        #for i in range(len(self.linloglayout_ids)):
            #max_group_score = max(self.linloglayout_clusters[i])
            #if max_group_score > 0:
                #max_group_idx = None
                #for j in range(len(self.linloglayout_clusters[i])):
                    #if self.linloglayout_clusters[i][j] == max_group_score:
                        #max_group_idx = j
                #ax.plot(self.linloglayout_reduction[i][0], self.linloglayout_reduction[i][1], 'o', 
                        #color=pl.cm.gray_r(max_group_idx * (300/self.n_clusters)), gid='node_%s_%s' % (max_group_idx, self.linloglayout_ids[i]))
        
        ##canvas.print_svg('../static/images/smarttypes_graph.svg', bbox_inches="tight", pad_inches=0)
        ##canvas.print_figure('../static/images/smarttypes_graph.png', bbox_inches="tight", pad_inches=0)
        
        