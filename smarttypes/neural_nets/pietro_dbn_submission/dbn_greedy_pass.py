# in this file we train a deep belief network greedily
# on examples of 3 letters
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

def train_RBM(rbm, v, l, nepochs, mom_init, mom_final, decay, epsilon, n_updates=1):
    delta = None
    for n in range(NEPOCHS):
        momentum = mom_final if n>50 else mom_final
        momentum = 0.5
        errsum = 0.
        energysum = 0.
        #
        if l is None:
            delta, errsum = rbm.ML_update(v, epsilon, n_updates=n_updates,
                                          delta=delta, decay=decay, momentum=momentum)
            ph, h = rbm.sample_h(v)
            energysum += rbm.energy(v, ph).sum()
        else:
            delta, errsum = rbm.ML_update(v, l, epsilon, n_updates=n_updates,
                                          delta=delta, decay=decay, momentum=momentum)
            #ph, h = rbm.sample_h(v, l)
            #energysum += rbm.energy(v, ph, l).sum()
        #
        #
        if n%100 == 0:
            print '  * ', n, 'error', errsum/v.shape[0], 'energy', energysum

NEPOCHS = 500
INITIAL_MOMENTUM = 0.5
FINAL_MOMENTUM = 0.9
DECAY = 0.0002
EPSILON = 0.1

# 3 layers
obs = rbm.RBM(I,100)
hid = rbm.RBM(100,100)
pen = rbm.RBM(100,100)
top = rbm.RBM_with_labels(100,100,L)

train_RBM(obs, v, None, NEPOCHS, INITIAL_MOMENTUM, FINAL_MOMENTUM, DECAY, EPSILON)
ph_obs, h_obs = obs.sample_h(v)
train_RBM(hid, ph_obs, None, NEPOCHS, INITIAL_MOMENTUM, FINAL_MOMENTUM, DECAY, EPSILON)
ph_hid, h_hid = hid.sample_h(ph_obs)
train_RBM(pen, ph_hid, None, NEPOCHS, INITIAL_MOMENTUM, FINAL_MOMENTUM, DECAY, EPSILON)
ph_pen, h_pen = pen.sample_h(ph_hid)

train_RBM(top, ph_pen, l, NEPOCHS, INITIAL_MOMENTUM, FINAL_MOMENTUM, DECAY, EPSILON)
ph_top, h_top = top.sample_h(ph_pen, l)

# save results
#private.pickle_to((obs,hid,pen,top), SAVEPATH+'res1')

# reconstruct
pv_top, v_top, pl_top, l_top = top.sample_vl(ph_top)
pv_pen, v_pen = pen.sample_v(pv_top)
pv_hid, v_hid = hid.sample_v(pv_pen)
pv_obs, v_obs = obs.sample_v(pv_hid)

show(v[5,:])
show(pv_obs[5,:])

# generate
gv = zeros((1, I)) + 0.5
ghid, tmp = obs.sample_h(gv)
gpen, tmp = hid.sample_h(ghid)
gh, tmp = pen.sample_h(gpen)

# class to generate
gl = scipy.array([[0.,0.,1.]])

for k in range(2500):
    gph_top, gh_top = top.sample_h(gh, gl)
    pgh, gh, tmp, tmp = top.sample_vl(gh_top)

for k in range(50):
    for k in range(250):
        gph_top, gh_top = top.sample_h(gh, gl)
        pgh, gh, tmp, tmp = top.sample_vl(gh_top)
    gpv_pen, gv_pen = pen.sample_v(gh)
    gpv_hid, gv_hid = hid.sample_v(gv_pen)
    gpv_obs, gv_obs = obs.sample_v(gv_hid)
    show(gpv_obs)

