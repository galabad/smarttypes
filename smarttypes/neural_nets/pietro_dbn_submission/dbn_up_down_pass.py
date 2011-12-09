# in this file we refine the solution found with dbn_greedy_pass.py
# using the up-down algorithm
# author: Pietro Berkes

import scipy
import scipy.io as sio
import mdp

import time
import private
private.import_scipy_common(globals())

import rbm
reload(rbm)


# the data ends up in a nclasses x ntrain x sizepatch array 'data'

SAVEPATH = '/unsafe/berkes/'
DATAPATH = '/unsafe/berkes/'
tmp = sio.loadmat(DATAPATH+'binaryalphadigs.mat')
NTRAIN = 39
CLASSES = [10, 12, 28] # A, C, S
NCLASSES = len(CLASSES)
I, L = 20*16, 3
N = NTRAIN*NCLASSES

# organize data
data = zeros((NCLASSES, NTRAIN, I))
labels = zeros((NCLASSES, NTRAIN, L))
for k in range(L):
    for m in range(NTRAIN):
        data[k,m,:] = (tmp['dat'][CLASSES[k],m].ravel()).astype('d')
        labels[k,m,k] = 1.

# prepare observations, labels
perm = srandom.permutation(N)
v = data.reshape(N, I)[perm,:]
l = labels.reshape(N, L)[perm,:]

import pylab
def show(frame, sz=(20,16), vmax=None, vmin=None):
    if sz!=None:
        frame = scipy.reshape(frame, sz)
    pylab.clf()
    pylab.imshow(frame,
                 cmap=pylab.cm.gray, interpolation='nearest',
                 vmax=vmax, vmin=vmin, hold=False)
    pylab.draw()


# ##########

NEPOCHS = 300
INITIAL_MOMENTUM = 0.
FINAL_MOMENTUM = 0.
DECAY = 0.0002
EPSILON = 0.2

# load RBMs
(obs_rbm,hid_rbm,pen_rbm,top) = private.pickle_from(SAVEPATH+'res1')

# ### wake-sleep part

# define untied layers
obs = rbm.Belief_Network_Layer(obs_rbm.I,obs_rbm.J,obs_rbm)
hid = rbm.Belief_Network_Layer(hid_rbm.I,hid_rbm.J,hid_rbm)
pen = rbm.Belief_Network_Layer(pen_rbm.I,pen_rbm.J,pen_rbm)

# use this if you want to start from scratch
#obs = rbm.Belief_Network_Layer(obs_rbm.I,obs_rbm.J)
#hid = rbm.Belief_Network_Layer(hid_rbm.I,hid_rbm.J)
#pen = rbm.Belief_Network_Layer(hid_rbm.I,hid_rbm.J)

for n in range(NEPOCHS):
    momentum = FINAL_MOMENTUM if n>5 else INITIAL_MOMENTUM
    if n<100: n_updates = 3
    elif n<200: n_updates = 6
    else: n_updates = 10
    
    pv1, v1 = obs.wake_phase(v, EPSILON, decay=DECAY, momentum=momentum)
    pv1, v1 = hid.wake_phase(v1, EPSILON, decay=DECAY, momentum=momentum)
    pv1, v1 = pen.wake_phase(v1, EPSILON, decay=DECAY, momentum=momentum)

    # ?? todo: combine learning and sampling
    n_updates = 3
    # learning top layer
    delta, errsum = top.ML_update(v1, l, EPSILON, n_updates=n_updates,
                                  decay=DECAY, momentum=momentum)
    # sampling top layer
    for k in range(n_updates):
        ph, h = top.sample_h(v1, l)
        pv1, v1, pl, rl = top.sample_vl(h)
        if k == 0: class_error = (rl.argmax(axis=1) != l.argmax(axis=1)).sum()

    pv0, v0 = pen.sleep_phase(v1, EPSILON, decay=DECAY, momentum=momentum)
    pv0, v0 = hid.sleep_phase(v0, EPSILON, decay=DECAY, momentum=momentum)
    pv0, v0 = obs.sleep_phase(v0, EPSILON, decay=DECAY, momentum=momentum)
    
    # number of classification errors
    print '* ', n, 'class errors:', class_error


# classification

pv1, v1 = obs.sample_h(v)
pv1, v1 = hid.sample_h(v1)
pv1, v1 = pen.sample_h(v1)

rl = zeros((v.shape[0], NCLASSES)) + 1./NCLASSES

# sampling top layer
ph, h = top.sample_h(v1, rl)
pv2, v2, pl, rl = top.sample_vl(h)

# inferred labels
print rl.argmax(axis=1)
# real labels
print l.argmax(axis=1)
# number of errors
print 'errors:', (rl.argmax(axis=1) != l.argmax(axis=1)).sum()
