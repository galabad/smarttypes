
import os
from collections import defaultdict
import numpy as np
from sklearn.cluster import DBSCAN, MeanShift, estimate_bandwidth
import networkx

class GraphReduce(object):

    def __init__(self, reduction_id, follower_followies_map):

        self.reduction_id = reduction_id
        self.follower_followies_map = follower_followies_map
        self.layout_ids = []
        self.id_to_idx_map = {}
        i = 0
        for node_id in follower_followies_map:
            self.layout_ids.append(node_id)
            self.id_to_idx_map[node_id] = i
            i += 1
        self.reduction = []
        self.layout_clusters = []
        print "Running graph_reduce on %s nodes." % len(self.layout_ids)

        ##file paths
        self.graphreduce_dir = os.path.dirname(os.path.abspath(__file__))
        self.graphreduce_io_dir = '%s/io' % self.graphreduce_dir
        if not os.path.exists(self.graphreduce_io_dir):
            os.makedirs(self.graphreduce_io_dir)
        self.reduction_file_name = 'reduction_%s.txt' % self.reduction_id
        self.reduction_file_path = '%s/%s' % (self.graphreduce_io_dir, self.reduction_file_name)
        self.linloglayout_input_file_name = 'linloglayout_input_%s.txt' % self.reduction_id
        self.linloglayout_input_file_path = '%s/%s' % (self.graphreduce_io_dir,
            self.linloglayout_input_file_name)

        #load last reduction if it's there
        if os.path.exists(self.reduction_file_path):
            self.load_reduction_from_file()

    def load_reduction_from_file(self):
        f = open(self.reduction_file_path)
        list_of_coordinates = []
        layout_clusters = []
        for line in f:
            line_pieces = line.split(' ')
            x_value = float(line_pieces[1])
            y_value = float(line_pieces[2])
            list_of_coordinates.append([x_value, y_value])
            layout_clusters.append(int(line_pieces[4]))
        self.reduction = np.array(list_of_coordinates)
        self.n_clusters = len(set(layout_clusters))
        self.layout_clusters = np.array(layout_clusters)

    def normalize_reduction(self):
        x_mean = np.mean(self.reduction[:,0])
        y_mean = np.mean(self.reduction[:,1])
        x_standard_deviation = np.std(self.reduction[:,0])
        y_standard_deviation = np.std(self.reduction[:,1])
        x_floor = x_mean - x_standard_deviation
        y_floor = y_mean - y_standard_deviation
        if x_floor < y_floor:
            print "mean: %s -- standard_deviation: %s" % (x_mean, x_standard_deviation)
            self.reduction -= x_floor
            self.reduction /= x_mean + x_standard_deviation
        else:
            print "mean: %s -- standard_deviation: %s" % (y_mean, y_standard_deviation)
            self.reduction -= y_floor
            self.reduction /= y_mean + y_standard_deviation

    def reduce_with_linloglayout(self):
        input_file = open(self.linloglayout_input_file_path, 'w')
        for node_id in self.layout_ids:
            for following_id in self.follower_followies_map[node_id]:
                input_file.write('%s %s \n' % (node_id, following_id))
        input_file.close()
        #to recompile
        #$ javac -d ../bin LinLogLayout.java
        os.system('cd %s/LinLogLayout; java -cp bin LinLogLayout 2 %s %s;' % (
            self.graphreduce_dir,
            self.linloglayout_input_file_path,
            self.reduction_file_path
        ))
        self.load_reduction_from_file()
        self.normalize_reduction()


