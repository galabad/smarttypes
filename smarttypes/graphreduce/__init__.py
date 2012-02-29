
import os
from collections import defaultdict
import numpy as np
from sklearn.cluster import DBSCAN, MeanShift, estimate_bandwidth
import networkx

import ctypes

EPS = 1e-6
EPS2 = 0


class GraphReduce(object):

    def __init__(self, reduction_id, initial_follower_followies_map):

        self.reduction_id = reduction_id
        self.initial_follower_followies_map = initial_follower_followies_map
        self.G = self.get_networkx_graph()
        print "Running graph_reduce on %s nodes." % self.G.number_of_nodes()

        self.reduction = []
        self.layout_clusters = []

        self.layout_ids = []
        self.id_to_idx_map = {}
        i = 0
        for node_id in self.G.nodes():
            self.layout_ids.append(node_id)
            self.id_to_idx_map[node_id] = i
            i += 1

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

        #exafmm_solver
        self.exafmm_solver = ctypes.CDLL("%s/libcoulomb.so" % self.graphreduce_dir)

    def get_networkx_graph(self):
        if not '_G' in self.__dict__:
            self._G = networkx.DiGraph()
            edges = []
            for follower, followies in self.initial_follower_followies_map.items():
                for followie in followies:
                    if followie in self.initial_follower_followies_map:
                        edges.append((follower, followie))
            self._G.add_edges_from(edges)
        return self._G

    def load_reduction_from_file(self):
        f = open(self.reduction_file_path)
        list_of_coordinates = []
        for line in f:
            line_pieces = line.split(' ')
            x_value = float(line_pieces[1])
            y_value = float(line_pieces[2])
            list_of_coordinates.append([x_value, y_value])
        self.reduction = np.array(list_of_coordinates)

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
            for following_id in self.G.neighbors(node_id):
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
        self.find_dbscan_clusters()

    def reduce_with_exafmm(self):
        #helper functions specific to this method
        def x_to_reduction(x):
            list_of_coordinates = []
            for i in range(self.G.number_of_nodes()):
                x_cord = x[i * 3]
                y_cord = x[i * 3 + 1]
                list_of_coordinates.append([x_cord, y_cord])
            self.reduction = np.array(list_of_coordinates)

        def reduction_to_x():
            x = []
            for row in self.reduction:
                x.append(row[0])
                x.append(row[1])
                x.append(0)  # exafmm is 3d
            return np.array(x)

        n = self.G.number_of_nodes()
        A = networkx.to_numpy_matrix(self.G)
        A = np.asarray(A)  # adjacency matrix

        #node_degrees and sanity check
        node_degrees = A.sum(axis=0) + 1
        for node_id, in_degree in self.G.in_degree_iter():
            i = self.id_to_idx_map[node_id]
            if in_degree != node_degrees[i] - 1:
                raise Exception('This is not good. This should not happen.')
        #node_degrees /= np.max(node_degrees)

        #params
        iterations = 100
        attractive_force_factor = 1.0
        repulsive_force_factor = 1.0
        potential_force_factor = 0.0

        #coordinates
        self.reduction = []
        if len(self.reduction):
            x = reduction_to_x()
        else:
            x = np.random.random(3 * n) * 100
        x[2::3] = 0  # make sure z is 0 for 2d
        q = np.ones(n) * node_degrees * repulsive_force_factor  # charges
        p = np.ones(n) * potential_force_factor  # potential
        f = np.zeros(3 * n)  # force

        print "attractive_force_factor: %s -- repulsive_force_factor: %s -- potential_force_factor: %s\n" % (
            attractive_force_factor, repulsive_force_factor, potential_force_factor)

        energy_status_msg = 0
        for i in range(iterations):
            #repulsion
            self.exafmm_solver.FMMcalccoulomb(n, x.ctypes.data, q.ctypes.data,
                p.ctypes.data, f.ctypes.data, 0)

            #attraction and move
            attraction_repulsion_diff = []
            for j in range(n):
                node_id = self.layout_ids[j]
                node_f = f[3 * j: 3 * j + 2]
                node_x = x[3 * j: 3 * j + 2]

                #attraction
                attraction_f = np.array([0.0, 0.0])
                for following_id in self.G.neighbors(node_id):
                    following_idx = self.id_to_idx_map[following_id]
                    following_x = x[3 * following_idx: 3 * following_idx + 2]
                    delta_x = following_x - node_x
                    norm_x = np.linalg.norm(delta_x)
                    if norm_x > EPS:
                        attraction_f += delta_x * np.log(1 + norm_x)

                attraction_repulsion_diff.append(np.linalg.norm(attraction_f) - np.linalg.norm(node_f))
                node_f += attraction_f

                #move
                norm_f = np.linalg.norm(node_f)
                energy_status_msg += norm_f
                if norm_f < EPS:
                    delta_x = 0
                else:
                    delta_x = node_f / np.sqrt(norm_f)
                #print node_f, norm_f, delta_x
                x[3 * j: 3 * j + 2] += delta_x

            #clear spent force
            f = np.zeros(3 * n)

            #status msg
            if i % 1 == 0:
                x_to_reduction(x)
                self.normalize_reduction()
                self.find_dbscan_clusters()
                print "iteration %s of %s -- energy: %s -- groups: %s -- cooling: %s -- att-rep-diff: %s" % (
                    i, iterations,
                    energy_status_msg if energy_status_msg else '?',
                    self.n_clusters,
                    cooling_factor,
                    np.median(attraction_repulsion_diff))
                energy_status_msg = 0

        #all done
        x_to_reduction(x)
        self.normalize_reduction()
        self.find_dbscan_clusters()

    def find_dbscan_clusters(self, eps=0.05, min_samples=12):
        self.layout_clusters = []
        db = DBSCAN().fit(self.reduction, eps=eps, min_samples=min_samples)
        labels = db.labels_
        self.n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        tmp_layout_clusters = defaultdict(lambda: [0] * self.n_clusters)
        for i in range(len(labels)):
            id = self.layout_ids[i]
            group_index = int(labels[i])
            if group_index != -1:
                tmp_layout_clusters[id][group_index] = 1
        for id in self.layout_ids:
            self.layout_clusters.append(tmp_layout_clusters[id])
        self.layout_clusters = np.array(self.layout_clusters)

    def find_mean_shift_clusters(self):
        self.layout_clusters = []
        bandwidth = estimate_bandwidth(self.reduction, quantile=0.2, n_samples=500)
        ms = MeanShift(bandwidth=bandwidth, bin_seeding=True)
        ms.fit(self.reduction)
        labels = ms.labels_
        self.n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        tmp_layout_clusters = defaultdict(lambda: [0] * self.n_clusters)
        for i in range(len(labels)):
            id = self.layout_ids[i]
            group_index = int(labels[i])
            if group_index != -1:
                tmp_layout_clusters[id][group_index] = 1
        for id in self.layout_ids:
            self.layout_clusters.append(tmp_layout_clusters[id])
        self.layout_clusters = np.array(self.layout_clusters)
