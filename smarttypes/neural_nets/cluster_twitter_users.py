
import replicated_softmax, time, cPickle, random
import smarttypes, numpy, pprint, os, collections
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

root_user = TwitterUser.by_screen_name('SmartTypes')
adjacency_matrix, unique_user_ids = root_user.get_adjacency_matrix(20)
print 'unique_users: ', len(unique_user_ids)

##do svd first
#X = np.random.normal(size=(10000, 2000))
#from scikits.learn.utils.extmath import fast_svd
#fast_svd(X, 60)

#little test
i = 0
tmp_followies = []
random_index = random.randint(0, len(adjacency_matrix) - 1)
for x in adjacency_matrix[random_index]:
    if x: tmp_followies.append(unique_user_ids[i])
    i += 1
assert not set(tmp_followies).difference(TwitterUser.get_by_id(unique_user_ids[random_index]).following_ids_default)
print "Passed our little test: following %s users!" % len(tmp_followies)

#parameters
btsz = 1
features = len(unique_user_ids) / 5
print "Features: %s" % features
epochs = 400
lr = 0.15

#http://metaoptimize.com/qa/questions/4040/how-to-increase-the-capacity-of-auto-encoders
#You should not be afraid of having a (very) large hidden layer size, 
#if you can constrain the hidden activations or the weights somehow 
#(simple tricks: L1/L2 penalty on the weights, L1 penalty on the activations, 
#or the kinds of things that Lee et al, 2007 do).

#neg_visible_activations = np.dot(pos_hidden_states, self.weights.T)
#neg_visible_probs = self._logistic(neg_visible_activations)

#reconstruction_matrix -- neg_visible_probs
#users following topics -- pos_hidden_probs
#topics following users -- self._logistic(self.weights)

#train
print "Start the training!"
weights_file = '/home/timmyt/Desktop/weights.pkl'
weights = None
if os.path.exists(weights_file):
    f = open(weights_file, 'r')
    weights = cPickle.load(f)
r = RBM(num_visible=adjacency_matrix.shape[1], num_hidden=features, weights=weights)
reconstruction_matrix = r.train(adjacency_matrix, max_epochs=epochs)
print "reconstruction_matrix shape: %s" % str(reconstruction_matrix.shape)
f = open(weights_file, 'w')
cPickle.dump(r.weights, f)
f.close()

def test_imagination(imagined_matrix, threshold=.7):
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

imagination_results = test_imagination(reconstruction_matrix)

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












