
import replicated_softmax, time, cPickle, random
import smarttypes, numpy, pprint, os, collections, heapq
from datetime import datetime, timedelta

from intro_to_rbm import RBM
from smarttypes.utils.postgres_handle import PostgresHandle
from smarttypes.model.postgres_base_model import PostgresBaseModel
postgres_handle = PostgresHandle(smarttypes.connection_string)
PostgresBaseModel.postgres_handle = postgres_handle

from smarttypes.model.twitter_user import TwitterUser
from smarttypes.model.twitter_group import TwitterGroup
TwitterUser.time_context = datetime(2011,11,1)
TwitterGroup.time_context = datetime(2011,11,1)

def do_deep_learning(adjacency_matrix, features):
    #parameters
    btsz = 1
    epochs = 20
    lr = 0.15    
    
    #we cache the weights
    weights_file = '/home/timmyt/Desktop/weights.pkl'
    weights = None
    if os.path.exists(weights_file):
        f = open(weights_file, 'r')
        weights = cPickle.load(f)
    
    print "Start the training!"
    r = RBM(num_visible=adjacency_matrix.shape[1], num_hidden=features, weights=weights)
    reconstruction_matrix = r.train(adjacency_matrix, max_epochs=epochs)
    #print "reconstruction_matrix shape: %s" % str(reconstruction_matrix.shape)
    
    #cache the weights
    f = open(weights_file, 'w')
    cPickle.dump(r.weights, f)
    f.close()
    
    return reconstruction_matrix

def do_nmf(adjacency_matrix, features):
    from sklearn.decomposition import NMF
    nmf = NMF(features, max_iter=200)
    reconstruction_matrix = nmf.fit_transform(adjacency_matrix)
    print "Reconstruction err: %s" % nmf.reconstruction_err_
    return reconstruction_matrix

    #components_ = nmf.components_
    #reconstruction_err_ = nmf.reconstruction_err_ 

    ##top users for each group
    #group_users_map = collections.defaultdict(list)
    #for i in range(features):
        #for j in range(len(unique_user_ids)):
            #user_id = unique_user_ids[j]
            #group_users_map[i].append((components_[i][j], user_id))
    
    #group_top_users = {}
    #for i in group_users_map:
        #group_top_users[i] = [(x[0], TwitterUser.get_by_id(x[1])) for x in heapq.nlargest(10, group_users_map[i])]
    
    #def show_details(group_index):
        #for x in group_top_users[group_index]:
            #print x[0], x[1].screen_name, x[1].description[:100]


def test_imagination(unique_user_ids, imagined_matrix, threshold=.7):
    i = 0
    results = []
    for x in imagined_matrix:
        j = 0
        imagined_followies = []
        for y in x:
            if y > threshold: imagined_followies.append(unique_user_ids[j])
            j += 1
        real_followies = set(TwitterUser.get_by_id(unique_user_ids[i]).following_ids_default)
        real_followies = real_followies.intersection(unique_user_ids)
        results.append((len(real_followies), len(imagined_followies), len(set(real_followies).difference(imagined_followies))))
        i += 1
    return results


if __name__ == "__main__":

    root_user = TwitterUser.by_screen_name('SmartTypes')
    adjacency_matrix, unique_user_ids = root_user.get_adjacency_matrix(20)
    print 'unique_users: ', len(unique_user_ids)
    
    #little test
    i = 0
    tmp_followies = []
    random_index = random.randint(0, len(adjacency_matrix) - 1)
    for x in adjacency_matrix[random_index]:
        if x: tmp_followies.append(unique_user_ids[i])
        i += 1
    assert not set(tmp_followies).difference(TwitterUser.get_by_id(unique_user_ids[random_index]).following_ids_default)
    print "Passed our little test: following %s users!" % len(tmp_followies)
    
    #features
    #features = len(unique_user_ids) / 4
    features = 2
    print "Features: %s" % features

    reconstruction_matrix = do_nmf(adjacency_matrix, features)
    #imagination_results = test_imagination(unique_user_ids, reconstruction_matrix, .7)

    
##save the top users for each group
##don't include the bias units
#group_users_map = collections.defaultdict(list)
#user_groups_map = collections.defaultdict(list)
#for i in range(len(unique_user_ids)):
    #user_id = unique_user_ids[i]
    #group_weights = r.weights[i+1]
    #user_groups_map[user_id] = list(group_weights[1:])
    #for j in range(features):
        #group_users_map[j].append((group_weights[1+j], user_id))
#f = open('/home/timmyt/Desktop/group_users_map.pkl', 'w')
#cPickle.dump(group_users_map, f)
#f = open('/home/timmyt/Desktop/user_groups_map.pkl', 'w')
#cPickle.dump(user_groups_map, f)

##May be useful
#from sklearn.decomposition import DictionaryLearning
#dlearn = DictionaryLearning(features, max_iter=200)
#dlearn.fit(adjacency_matrix)
#components_ = dlearn.components_
#reconstruction_err_ = dlearn.error_ 

#k-means
#from scikits.learn.cluster import KMeans
#kmeans = KMeans(k=20, init='k-means++', n_init=10, max_iter=300, tol=0.0001, verbose=0, random_state=None, copy_x=True)
#kmeans.fit(adjacency_matrix)

#print "Reconstruction error: %s" % reconstruction_err_








