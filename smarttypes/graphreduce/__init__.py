
import os
from collections import defaultdict
import numpy as np
from scipy.spatial import distance
from sklearn.cluster import DBSCAN, MeanShift, estimate_bandwidth
import networkx
from networkx.drawing import layout

import ctypes
solver = ctypes.CDLL("/home/timmyt/projects/smarttypes/smarttypes/graphreduce/libcoulomb.so")

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
        self.layout_similarities = None

        self.layout_ids = []
        self.id_to_idx_map = {}
        i = 0
        for node_id in self.G.nodes():
            self.layout_ids.append(node_id)
            self.id_to_idx_map[node_id] = i
            i += 1

        ##linloglayout file paths
        self.linloglayout_dir = '/home/timmyt/projects/smarttypes/smarttypes/graphreduce/LinLogLayout'
        self.input_file_name = 'io/%s_input.txt' % self.reduction_id
        self.output_file_name = 'io/%s_output.txt' % self.reduction_id
        self.pickle_file_name = 'io/%s.pickle' % self.reduction_id
        self.input_file_path = '%s/%s' % (self.linloglayout_dir, self.input_file_name)
        self.output_file_path = '%s/%s' % (self.linloglayout_dir, self.output_file_name)
        self.pickle_file_path = '%s/%s' % (self.linloglayout_dir, self.pickle_file_name)

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

    def normalize_reduction(self, num_of_standard_deviations=1.0):
        r_min = np.min(self.reduction, axis=0)
        min_x = r_min[0]
        min_y = r_min[1]
        if min_x < 0:
            self.reduction[:, 0] += abs(min_x)
        if min_y < 0:
            self.reduction[:, 1] += abs(min_y)
        r_mean = np.mean(self.reduction)
        r_standard_deviation = np.std(self.reduction)
        print "mean: %s -- standard_deviation: %s -- num_of_standard_deviations: %s" % (
            r_mean, r_standard_deviation, num_of_standard_deviations)
        self.reduction /= r_mean + (r_standard_deviation * num_of_standard_deviations)

    def set_reduction_coordinates(self, coordinates):
        self.reduction = []
        for i in range(self.G.number_of_nodes()):
            #id = self.layout_ids[i]
            x_cord = coordinates[i * 3]
            y_cord = coordinates[i * 3 + 1]
            self.reduction.append([x_cord, y_cord])
        self.reduction = np.array(self.reduction)
        self.normalize_reduction()
        self.find_dbscan_clusters()
        #self.find_mean_shift_clusters()

    def reduce_with_fruchterman_reingold(self):
        return_dict = layout.fruchterman_reingold_layout(self.G)
        for id in return_dict:
            self.reduction.append([return_dict[id][0], return_dict[id][1]])
        self.reduction = np.array(self.reduction)
        self.normalize_reduction()

    def reduce_with_exafmm(self):
        n = self.G.number_of_nodes()
        A = networkx.to_numpy_matrix(self.G)
        A = np.asarray(A)

        node_degrees = A.sum(axis=1) + 1
        for i in range(n):
            node_id = self.layout_ids[i]
            node_degree = len(self.G.neighbors(node_id))
            if node_degree != node_degrees[i] - 1:
                raise Exception('This is not good. This should not happen.')

        iterations = 500
        attractive_force_factor = .00005
        repulsive_force_factor = 1
        potential_force_factor = 1

        x = np.random.random(3 * n) * 20  # coordinates
        x[2::3] = 0  # set z to 0 for 2d
        q = (np.ones(n) / node_degrees) * repulsive_force_factor  # charges
        p = np.ones(n) * potential_force_factor  # potential
        f = np.zeros(3 * n)  # force

        print "iterations: %s -- attractive_force_factor: %s -- repulsive_force_factor: %s -- potential_force_factor: %s\n" % (
            iterations, attractive_force_factor, repulsive_force_factor, potential_force_factor)

        cooling_factor = 0
        energy_status_msg = 0
        for i in range(iterations):
            if i % 50 == 0:
                self.set_reduction_coordinates(x)
                print "iteration %s of %s -- energy: %s -- groups: %s -- cooling: %s" % (i,
                    iterations, energy_status_msg if energy_status_msg else '?',
                    self.n_clusters,
                    cooling_factor)
                energy_status_msg = 0

            #start cooling
            if float(i) / iterations > .75:
                cooling_factor = 1 - (float(i) / iterations)
                q = (np.ones(n) / node_degrees) * repulsive_force_factor * cooling_factor

            solver.FMMcalccoulomb(n, x.ctypes.data, q.ctypes.data, p.ctypes.data, f.ctypes.data, 0)

            #hooke_attraction and move
            for j in range(n):
                node_id = self.layout_ids[j]
                node_f = f[3 * j: 3 * j + 2]
                node_x = x[3 * j: 3 * j + 2]

                #hooke_attraction
                for following_id in self.G.neighbors(node_id):
                    following_idx = self.id_to_idx_map[following_id]
                    following_x = x[3 * following_idx: 3 * following_idx + 2]
                    delta_x = following_x - node_x
                    node_f += delta_x * np.log(1 + np.linalg.norm(delta_x)) * attractive_force_factor

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

        print "iteration %s of %s -- energy: %s" % (i, iterations, energy_status_msg)
        self.set_reduction_coordinates(x)

    def reduce_with_linloglayout(self):
        print "reduce_with_linloglayout"
        input_file = open(self.input_file_path, 'w')
        for node_id in self.layout_ids:
            for following_id in self.G.neighbors(node_id):
                input_file.write('%s %s \n' % (node_id, following_id))

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
        for line in f:
            line_pieces = line.split(' ')
            #id = line_pieces[0]
            x_value = float(line_pieces[1])
            y_value = float(line_pieces[2])
            self.reduction.append([x_value, y_value])
        self.reduction = np.array(self.reduction)
        self.normalize_reduction()

    def find_layout_similarities(self):
        self.layout_similarities = distance.squareform(distance.pdist(self.reduction))
        self.layout_similarities = 1 - (self.layout_similarities / np.max(self.layout_similarities))

    def find_dbscan_clusters(self, eps=0.05, min_samples=12):
        self.layout_clusters = []
        self.find_layout_similarities()
        #db = DBSCAN().fit(self.layout_similarities, eps=eps, min_samples=min_samples)
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
