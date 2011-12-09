# this module contains a class to learn a binary<->binary RBM,
# one to learn a bin<->bin RBM with softmax label, and one
# to learn weights in a belief network using the wake-sleep algorithm

# - I didn't attempt any optimization
# - much of the RBM/RBM_with_labels code is redundant -> need cleanup

# author: Pietro Berkes

import scipy

import private
private.import_scipy_common(globals())
random = srandom.random
rrep = private.rrep

class RBM(object):
    """Binary <-> binary RBM class"""

    def __init__(self, I, J):
        """
        I --- number of visible units
        J --- number of hidden units

        Notation as in (Hinton & Salakhutdinov, 2006)
        """

        # dimensionality
        self.I, self.J = I, J
        # weights
        self.w = srandom.randn(I,J)*0.1 # zeros((I,J))
        # biases
        self.bv = srandom.randn(I,)*0.1 # zeros((I,))
        self.bh = srandom.randn(J,)*0.1 # zeros((J,))

    def sample_h(self, v):
        # P(h=1|v,W,b)
        probs = 1./(1. + exp(-self.bh - dot(v, self.w)))
        h = (probs > random(probs.shape)).astype('d')
        return probs, h

    def sample_v(self, h):
        # P(v=1|h,W,b)
        probs = 1./(1. + exp(-self.bv - dot(h, self.w.T)))
        v = (probs > random(probs.shape)).astype('d')
        return probs, v

    def energy(self, v, h):
        return -dot(v, self.bv) - dot(h, self.bh) \
               - (dot(v, self.w)*h).sum(axis=1)

    def ML_update(self, v, epsilon, n_updates=1, decay=0., momentum=0., delta=None):
        """Training by Contrastive Divergence.
        n_updates --- number of Gibbs sampling
        """

        # useful quantities
        N = v.shape[0]
        w, bv, bh = self.w, self.bv, self.bh

        # old gradients for momentum term
        dw, dbv, dbh = delta if delta is not None else (0.,0.,0.)
        
        # first update of the hidden units for the data term
        ph_data, h_data = self.sample_h(v)
        # n updates of both v and h for the model term
        h_model = h_data.copy()
        for i in range(n_updates):
            pv_model, v_model = self.sample_v(h_model)
            ph_model, h_model = self.sample_h(v_model)
        
        # update w
        data_term = dot(v.T, ph_data)
        model_term = dot(v_model.T, ph_model)
        dw = momentum*dw + \
             epsilon*((data_term - model_term)/N - decay*w)
        w += dw
        
        # update bv
        data_term = v.sum(axis=0)
        model_term = v_model.sum(axis=0)
        dbv = momentum*dbv + \
              epsilon*((data_term - model_term)/N)
        bv += dbv

        # update bh
        data_term = ph_data.sum(axis=0)
        model_term = ph_model.sum(axis=0)
        dbh = momentum*dbh + \
              epsilon*((data_term - model_term)/N)
        bh += dbh

        err = ((v-v_model)**2.).sum()
        return (dw, dbv, dbh), float(err)
    
class RBM_with_labels(object):
    """Binary <-> binary RBM class"""

    def __init__(self, I, J, L):
        """
        I --- number of visible units
        J --- number of hidden units
        L --- number of labels

        Notation as in (Hinton & Salakhutdinov, 2006)
        """

        # dimensionality
        self.I, self.J, self.L = I, J, L
        # weights from visible to hidden units
        self.wv = srandom.randn(I,J)*0.1 #  zeros((I,J))
        # weights from labels to hidden units
        self.wl = srandom.randn(L,J)*0.1 #  zeros((L,J))
        # biases
        self.bv = srandom.randn(I,)*0.1 # zeros((I,))
        self.bh = srandom.randn(J,)*0.1 # zeros((J,))
        self.bl= srandom.randn(L,)*0.1 # zeros((J,))

    def sample_h(self, v, l):
        # P(h=1|v,l,W,b)
        a = self.bh + dot(v, self.wv) + dot(l, self.wl)
        probs = 1./(1. + exp(-a))
        h = (probs > random(probs.shape)).astype('d')
        return probs, h

    def sample_vl(self, h):
        # P(v=1|h,W,b), P(l=1|h,W,b)

        L = self.L
        
        # visible units: logistic activation
        probs_v = 1./(1. + exp(-self.bv - dot(h, self.wv.T)))
        v = (probs_v > random(probs_v.shape)).astype('d')
        
        # label units: softmax activation
        exponent = self.bl + dot(h, self.wl.T)
        exponent -= rrep(exponent.max(axis=1), L)
        probs_l = exp(exponent)
        probs_l /= rrep(probs_l.sum(axis=1), L)

        # ?? this should really be a series of draws from multinomials
        l = probs_l.copy() 
        return probs_v, v, probs_l, l

    def energy(self, v, h, l):
        return -dot(v, self.bv) - dot(h, self.bh) - dot(l, self.bl) \
               - (dot(v, self.wv)*h).sum(axis=1) \
               - (dot(l, self.wl)*h).sum(axis=1)

    def ML_update(self, v, l, epsilon, n_updates=1, decay=0., momentum=0., delta=None):
        """Training by Contrastive Divergence.
        l --- observed labels
        n_updates --- number of Gibbs sampling
        """

        # useful quantities
        N = v.shape[0]
        wv, wl, bv, bh, bl = self.wv, self.wl, self.bv, self.bh, self.bl

        # old gradients for momentum term
        dwv, dwl, dbv, dbl, dbh = delta if delta is not None else (0.,0.,0.,0.,0.)
        
        # first update of the hidden units for the data term
        ph_data, h_data = self.sample_h(v, l)
        # n updates of both v and h for the model term
        h_model = h_data.copy()
        for i in range(n_updates):
            pv_model, v_model, pl_model, l_model = self.sample_vl(h_model)
            ph_model, h_model = self.sample_h(v_model, l_model)
        
        # update wv
        data_term = dot(v.T, h_data)
        model_term = dot(v_model.T, h_model)
        dwv = momentum*dwv + \
              epsilon*((data_term - model_term)/N - decay*wv)
        wv += dwv
        
        # update wl
        data_term = dot(l.T, h_data)
        model_term = dot(pl_model.T, h_model)
        dwl = momentum*dwl + \
              epsilon*((data_term - model_term)/N - decay*wl)
        wl += dwl
        
        # update bv
        data_term = v.sum(axis=0)
        model_term = v_model.sum(axis=0)
        dbv = momentum*dbv + \
              epsilon*((data_term - model_term)/N)
        bv += dbv

        # update bl
        data_term = l.sum(axis=0)
        model_term = pl_model.sum(axis=0)
        dbl = momentum*dbl + \
              epsilon*((data_term - model_term)/N)
        bl += dbl

        # update bh
        data_term = ph_data.sum(axis=0)
        model_term = ph_model.sum(axis=0)
        dbh = momentum*dbh + \
              epsilon*((data_term - model_term)/N)
        bh += dbh

        err = ((v-v_model)**2.).sum()
        return (dwv, dwl, dbv, dbl, dbh), float(err)

class Belief_Network_Layer(object):
    """Layer of a belief network"""

    def __init__(self, I, J, rbm = None):
        """
        I --- number of visible units
        J --- number of hidden units
        rbm --- if not None, initialize the weights using this RBM object

        Notation as in (Hinton & Salakhutdinov, 2006)
        """

        # dimensionality
        self.I, self.J = I, J
        
        # init recognition and generation parameters
        if rbm is not None: # init using an RBM object
            # weights
            self.w_rec = rbm.w.copy()
            self.w_gen = rbm.w.copy()
            # biases
            self.bv = rbm.bv.copy()
            self.bh = rbm.bh.copy()
        else:
            # weights
            self.w_rec = self.w_gen = srandom.randn(I,J)*0.1 # zeros((I,J))
            # biases
            self.bv = srandom.randn(I,)*0.1 # zeros((I,))
            self.bh = srandom.randn(J,)*0.1 # zeros((J,))

        self.dw_wake = 0.
        self.dw_sleep = 0.
        self.dbv = self.dbh = 0.

    def sample_h(self, v):
        # P(h=1|v,W,b)
        probs = 1./(1. + exp(-self.bh - dot(v, self.w_rec)))
        h = (probs > random(probs.shape)).astype('d')
        return probs, h

    def sample_v(self, h):
        # P(v=1|h,W,b)
        probs = 1./(1. + exp(-self.bv - dot(h, self.w_gen.T)))
        v = (probs > random(probs.shape)).astype('d')
        return probs, v

    def wake_phase(self, v, epsilon, decay=0., momentum=0.):
        # sample from recognition model
        ph, h = self.sample_h(v)
        # reconstruct input
        pv1, v1 = self.sample_v(h)
        
        # adapt generative weights
        delta = dot((v - pv1).T, h)/v.shape[0]
        self.dw_wake = momentum*self.dw_wake + epsilon*(delta - decay*self.w_gen)
        self.w_gen += self.dw_wake

        # adapt biases
        delta = (v - pv1).mean(axis=0)
        self.dbv = momentum*self.dbv + epsilon*delta
        self.bv += self.dbv
        
        return ph, h

    def sleep_phase(self, h, epsilon, decay=0., momentum=0.):
        # sample from generative model
        pv, v = self.sample_v(h)
        # reconstruct hidden state
        ph1, h1 = self.sample_h(v)
        
        # adapt generative weights
        delta = dot(v.T, (h - ph1))/v.shape[0]
        self.dw_sleep = momentum*self.dw_sleep + epsilon*(delta - decay*self.w_rec)
        self.w_rec += self.dw_sleep

        # adapt biases
        delta = (h - ph1).mean(axis=0)
        self.dbh = momentum*self.dbh + epsilon*delta
        self.bh += self.dbh
        
        return pv, v

