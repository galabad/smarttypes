# test module, to be used with py.test
# author: Pietro Berkes

import rbm

import mdp
import scipy
import private
private.import_scipy_common(globals())

from private import import_from, assert_array_almost_equal_diff
import numpy
import_from(numpy.testing, ['assert_array_equal',
                            'assert_array_almost_equal',
                            'assert_almost_equal'], globals())


def test_rbm_sample_h():
    I, J = 2, 4

    bm = rbm.RBM(I,J)
    bm.w[0,:] = [1,0,1,0]
    bm.w[1,:] = [0,1,0,1]
    bm.w *= 2e4
    bm.bv *= 0
    bm.bh *= 0

    # test 1
    v = scipy.array([[0,0],[1,0],[0,1],[1,1.]])
    h = []
    for n in range(100):
        prob, sample = bm.sample_h(v)
        h.append(sample)

    # check inferred probabilities
    expected_probs = scipy.array([[0.5, 0.5, 0.5, 0.5],
                                  [1.0, 0.5, 1.0, 0.5],
                                  [0.5, 1.0, 0.5, 1.0],
                                  [1.0, 1.0, 1.0, 1.0]])
    assert_array_almost_equal(prob, expected_probs, 8)

    # check sampled units
    h = scipy.array(h)
    for n in range(4):
        distr = h[:,n,:].mean(axis=0)
        assert_array_almost_equal(distr, expected_probs[n,:], 1)

    # test 2, with bias
    bm.bh -= 1e4
    h = []
    for n in range(100):
        prob, sample = bm.sample_h(v)
        h.append(sample)

    # check inferred probabilities
    expected_probs = scipy.array([[0., 0., 0., 0.],
                                  [1.0, 0., 1.0, 0.],
                                  [0., 1.0, 0., 1.0],
                                  [1.0, 1.0, 1.0, 1.0]])
    assert_array_almost_equal(prob, expected_probs, 8)

    # check sampled units
    h = scipy.array(h)
    for n in range(4):
        distr = h[:,n,:].mean(axis=0)
        assert_array_almost_equal(distr, expected_probs[n,:], 1)

def test_rbm_sample_v():
    I, J = 4, 2

    bm = rbm.RBM(I,J)
    bm.w[:,0] = [1,0,1,0]
    bm.w[:,1] = [0,1,0,1]
    bm.w *= 2e4
    bm.bv *= 0
    bm.bh *= 0

    # test 1
    h = scipy.array([[0,0],[1,0],[0,1],[1,1.]])
    v = []
    for n in range(100):
        prob, sample = bm.sample_v(h)
        v.append(sample)

    # check inferred probabilities
    expected_probs = scipy.array([[0.5, 0.5, 0.5, 0.5],
                                  [1.0, 0.5, 1.0, 0.5],
                                  [0.5, 1.0, 0.5, 1.0],
                                  [1.0, 1.0, 1.0, 1.0]])
    assert_array_almost_equal(prob, expected_probs, 8)

    # check sampled units
    v = scipy.array(v)
    for n in range(4):
        distr = v[:,n,:].mean(axis=0)
        assert_array_almost_equal(distr, expected_probs[n,:], 1)

    # test 2, with bias
    bm.bv -= 1e4
    v = []
    for n in range(100):
        prob, sample = bm.sample_v(h)
        v.append(sample)

    # check inferred probabilities
    expected_probs = scipy.array([[0., 0., 0., 0.],
                                  [1.0, 0., 1.0, 0.],
                                  [0., 1.0, 0., 1.0],
                                  [1.0, 1.0, 1.0, 1.0]])
    assert_array_almost_equal(prob, expected_probs, 8)

    # check sampled units
    v = scipy.array(v)
    for n in range(4):
        distr = v[:,n,:].mean(axis=0)
        assert_array_almost_equal(distr, expected_probs[n,:], 1)

def test_rbm_stability():
    I, J = 8, 2

    bm = rbm.RBM(I,J)
    bm.w = mdp.utils.random_rot(max(I,J), dtype='d')[:I, :J]
    bm.bv = srandom.randn(I)
    bm.bh = srandom.randn(J)

    real_w = bm.w.copy()
    real_bv = bm.bv.copy()
    real_bh = bm.bh.copy()

    # Gibbs sample until you reach the equilibrium distribution
    N = 1e4
    v = srandom.randint(0,2,(N,I)).astype('d')
    for k in range(100):
        p, h = bm.sample_h(v)
        p, v = bm.sample_v(h)

    # see that w remains stable
    delta = (0.,0.,0.)
    for k in range(100):
        delta, err = bm.ML_update(v, 0.1, n_updates=1, delta=delta)

    assert_array_almost_equal(real_w, bm.w, 1)
    assert_array_almost_equal(real_bv, bm.bv, 1)
    assert_array_almost_equal(real_bh, bm.bh, 1)
    
def test_rbm_learning():
    I, J = 4, 2
    bm = rbm.RBM(I,J)
    bm.w = mdp.utils.random_rot(max(I,J), dtype='d')[:I, :J]

    # the observations consist of two disjunct patterns that never appear together
    N=10000
    v = zeros((N,I))
    for n in range(N):
        r = srandom.random()
        if r>0.666: v[n,:] = [0,1,0,1]
        elif r>0.333: v[n,:] = [1,0,1,0]

    delta = (0.,0.,0.)
    for k in range(1500):
        mom = 0.9 if k>5 else 0.5
        delta, err = bm.ML_update(v, 0.3, n_updates=1, delta=delta, momentum=mom)
        if err/N<0.1: break
        #print '-------', err

    assert err/N<0.1

def test_labelled_rbm_learning():
    I, J, L = 4, 4, 2
    bm = rbm.RBM_with_labels(I,J,L)
    bm.wv = srandom.randn(I,J)
    bm.wl = srandom.randn(L,J)

    N=2500
    v = zeros((2*N,I))
    l = zeros((2*N,L))
    for n in range(N):
        r = srandom.random()
        if r>0.666:
            v[n,:] = [0,1,0,0]
            l[n,:] = [1,0]
        elif r>0.333:
            v[n,:] = [1,0,0,0]
            l[n,:] = [1,0]
    for n in range(N):
        r = srandom.random()
        if r>0.666:
            v[N+n,:] = [0,0,0,1]
            l[N+n,:] = [0,1]
        elif r>0.333:
            v[N+n,:] = [0,0,1,0]
            l[N+n,:] = [0,1]


    delta = None
    for k in range(1500):
        mom = 0.9 if k>100 else 0.5
        delta, err = bm.ML_update(v, l, 0.1, n_updates=1, delta=delta, decay=0., momentum=mom)
        if err/(2*N)<0.1: break
        #print '-------', k, err/(2*N)

    assert err/(2*N)<0.1
