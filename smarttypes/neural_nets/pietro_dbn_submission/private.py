# A few utility functions
# Author: Pietro Berkes

import scipy

import sys
import mdp
import pickle


# ##### import utilities

def import_from(module, names, dict):
    for name in names:
       dict[name] = getattr(module, name, None)

def import_as(module, names_aliases, dict):
    for name, alias in names_aliases:
       dict[alias] = getattr(module, name, None)

def import_scipy_common(dict):
    import_from(scipy, ['sum', 'prod', 'sqrt', 'log', 'eye', 'exp',
                        'diag', 'trace', 'dot', 'outer', 'inv', 'det',
                        'zeros', 'ones', 'newaxis', 'tensordot'], dict)
    import_from(scipy.linalg, ['inv', 'det'], dict)
    import_as(scipy, [('random', 'srandom')], dict)

import_scipy_common(globals())

# alternative curry-by-closure, Alex Martelli, 2001/06/28
# Nick Perkins' latest version of curry-by-closure (from c.l.p, for the
# record) is more general (no named args at all, thus no accidental name
# capture -- except, I think, for args and create_time_kwds...) and
# quite readable, although marginally more verbose, due to good name
# choices for intermediate locals. It also has curry-from-left (for
# positional args) and call-time-dominates (for named args) semantics,
# which may be popular:
def curry(*args, **create_time_kwds):
    func = args[0]
    create_time_args = args[1:]
    def curried_function(*call_time_args, **call_time_kwds):
        args = create_time_args + call_time_args
        kwds = create_time_kwds.copy()
        kwds.update(call_time_kwds)
        return func(*args, **kwds)
    return curried_function
       
def htime(s):
    """
    Returns seconds expressed in (days,hours,min,seconds)
    """
    min, s = divmod(s, 60)
    h, min = divmod(min, 60)
    d, h = divmod(h, 24)
    return int(d), int(h), int(min), s
    
def histogram(series,nbins=100):
    """
    Generate histogram from series.
    Returns an array of histogram bins and bin counts.
    """
    assert len(series.shape) == 1, "Cannot histogram multidimensional arrays!"
    series = scipy.sort(series)
    mx = series[-1]
    mn = series[0]
    # 2.22044604925e-16 is scipy.limits.double_epsilon
    bins = mdp.utils.linspace(mn, mx+2.22044604925e-16)
    n = scipy.searchsorted(series, bins)
    n = scipy.concatenate([n,[len(series)]])
    hist = (n[1:]-n[:-1]) / float(len(series))
    return bins, hist

def kron(a,b):
    """
    kron(a,b) is the Kronecker tensor product of a and b.
    The result is a large matrix formed by taking all possible
    products between the elements of a and those of b.   For
    example, if a is 2 by 3, then KRON(a,b) is
 
       [ a[1,1]*b  a[1,2]*b  a[1,3]*b
         a[2,1]*b  a[2,2]*b  a[2,3]*b ]

    Author: Nils Wagner
    """
    if not a.iscontiguous():
        a = scipy.reshape(a, a.shape)
    if not b.iscontiguous():
        b = scipy.reshape(b, b.shape)
    o = scipy.outerproduct(a,b)
    o.shape = a.shape + b.shape
    return scipy.concatenate(scipy.concatenate(o, axis=1), axis=1)

def aprint(arr, precision=4, suppress_small=1):
     scipy.io.write_array(sys.stdout,arr,precision=precision,\
                          suppress_small=suppress_small)    

def argmax2d(mtx2d):
    """Return the 2d indices to the maximum value of the 2d matrix."""
    h, w = mtx2d.shape
    idx = mtx2d.argmax()
    idx1 = idx/w
    idx2 = idx%w
    return idx1, idx2

# replication functions
def lrep(x, n):
    """Replicate x n-times on a new first dimension"""
    shp = [1]
    shp.extend(x.shape)
    return x.reshape(shp).repeat(n, axis=0)

def rrep(x, n):
    """Replicate x n-times on a new last dimension"""
    shp = x.shape + (1,)
    return x.reshape(shp).repeat(n, axis=-1)

def irep(x, n, dim):
    """Replicate x n-times on a new dimension dim-th dimension"""
    x_shape = x.shape
    shp = x_shape[:dim] + (1,) + x_shape[dim:]
    return x.reshape(shp).repeat(n, axis=dim)
# /replication functions

def sum0_2d(x):
    """Sum a 2D array over axis 0"""
    o = ones(x.shape[0])
    return dot(o, x)

def sum0(x):
    """Sum over axis 0"""
    o = ones(x.shape[0])
    return tensordot(o, x, axes=[0,0])

# faster in the conventional way x.sum(axis=1)
## def sum1(x):
##     """Sum over axis 1"""
##     o = ones(x.shape[1])
##     return tensordot(x, o, axes=[1,0])

def sum1_2d(x):
    """Sum a 2D array over axis 1"""
    o = ones(x.shape[1])
    return dot(x, o)


def gabor(size, alpha, phi, freq, sgm, x0 = None, res = 1, ampl = 1.):
    """Return a 2D array containing a Gabor wavelet.

    size -- (height, width) (pixel)
    alpha -- orientation (rad)
    phi -- phase (rad)
    freq -- frequency (cycles/deg)
    sgm -- (sigma_x, sigma_y) standard deviation along the axis
           of the gaussian ellipse (pixel)
    x0 -- (x,y) coordinates of the center of the wavelet (pixel)
          Default: None, meaning the center of the array
    res -- spatial resolution (deg/pixel)
           Default: 1, so that 'freq' is measured in cycles/pixel
    ampl -- constant multiplying the result
            Default: 1.
    """

    # init
    w, h = size
    if x0 is None: x0 = (w//2, h//2)
    y0, x0 = x0
    
    # some useful quantities
    freq *= res
    sinalpha = scipy.sin(alpha)
    cosalpha = scipy.cos(alpha)
    v0, u0 = freq*cosalpha, freq*sinalpha

    # coordinates
    #x = scipy.mgrid[-x0:w-x0, -y0:h-y0]
    x = scipy.meshgrid(scipy.arange(w)-x0, scipy.arange(h)-y0)
    x = (x[0].T, x[1].T)
    xr = x[0]*cosalpha - x[1]*sinalpha
    yr = x[0]*sinalpha + x[1]*cosalpha

    # gabor
    im = ampl*scipy.exp(-0.5*(xr*xr/(sgm[0]*sgm[0]) + yr*yr/(sgm[1]*sgm[1]))) \
             *scipy.cos(-2.*scipy.pi*(u0*x[0]+v0*x[1]) - phi)

    return im

def fit_gabor(w, size):
    import scipy.optimize
    import scipy.fftpack
    
    # # get approx parameters
    # envelope
    w2 = w*w
    w2 /= w2.sum()
    
    xgrid, ygrid = scipy.meshgrid(range(size), range(size))
    # mean
    x0 = (xgrid*w2).sum()
    y0 = (ygrid*w2).sum()
    # covariance
    xx = ((xgrid-x0)**2. *w2).sum()
    xy = ((xgrid-x0)*(ygrid-y0) *w2).sum()
    yy = ((ygrid-y0)**2. *w2).sum()
    sgm_y, sgm_x = scipy.sqrt(scipy.linalg.eigvals([[xx, xy],[xy, yy]]).real)

    wfft = scipy.fftpack.fft2(w)
    wsft = scipy.fftpack.fftshift(wfft)[:size/2+1,:]

    i,j = argmax2d(abs(wsft))
    phi = -scipy.angle(wsft[i,j])
    i,j = size/2.-i, j-size/2.
    freq = scipy.sqrt(i**2. + j**2.)/size
    alpha = scipy.pi-scipy.arctan2(i, j)

    ampl = abs(w).max()

    # (alpha, phi, freq, sgm_x, sgm_y, x0, y0)
    params0 = [alpha, phi, freq, sgm_x, sgm_y, x0, y0, ampl]
    #print params0
    #res = ((w - gabor((size, size), alpha, 2*scipy.pi-phi, freq,
    #                  (sgm_x, sgm_y), (x0, y0), ampl=ampl))**2.).sum()
    #return scipy.array(params0), res, 1.
        
    def _gabor_diff(params):
        (alpha, phi, freq, sgm_x, sgm_y, x0, y0, ampl) = params
        #print sgm_x, sgm_y
        if min(x0,y0)<0. or max(x0,y0)>size:
            return +1e10
        if min(sgm_x,sgm_y)<0. or max(sgm_x,sgm_y)>2*size:
            return +1e10
        if freq<0. or freq>0.4:
            return +1e10
        if ampl<0.:
            return +1e10
        res = w - gabor((size, size), alpha, phi, freq,
                        (sgm_x, sgm_y), (x0, y0), ampl=ampl)
        return res.ravel()

    min_res = scipy.inf
    min_params = [alpha, phi, freq, sgm_x, sgm_y, x0, y0, ampl]
    min_ier = 0.
    for alpha in scipy.linspace(0., scipy.pi, 10):
    #for alpha in [alpha]:
        #for phi in [phi]:
        for phi in scipy.linspace(0., 2.*scipy.pi, 10):
            params0 = [alpha, phi, freq, sgm_x, sgm_y, x0, y0, ampl]
            params, ier = scipy.optimize.leastsq(_gabor_diff, params0, maxfev=1000)
            residual = (_gabor_diff(params)**2.).sum()
            if residual<min_res:
                print min_res, ' -> ', residual
                min_res = residual
                min_params = params.copy()
                min_ier = ier

    return min_params, min_res, min_ier
       
# ##### file management

def pickle_to(obj, fname):
    fid = open(fname, 'w')
    pickle.dump(obj, fid, 1)
    fid.close()

def pickle_from(fname):
    fid = open(fname, 'r')
    obj = pickle.load(fid)
    fid.close()
    return obj

# copyed and adapted from elsewhere
def assert_array_almost_equal_diff(x, y, digits, err_msg=''):
    x,y = mdp.numx.asarray(x), mdp.numx.asarray(y)
    msg = '\nArrays are not almost equal'
    assert 0 in [len(mdp.numx.shape(x)),len(mdp.numx.shape(y))] \
           or (len(mdp.numx.shape(x))==len(mdp.numx.shape(y)) and \
               mdp.numx.alltrue(mdp.numx.equal(mdp.numx.shape(x),
                                               mdp.numx.shape(y)))),\
               msg + ' (shapes %s, %s mismatch):\n\t' \
               % (mdp.numx.shape(x),mdp.numx.shape(y)) + err_msg
    maxdiff = max(mdp.numx.ravel(abs(x-y)))/\
              max(max(abs(mdp.numx.ravel(x))),max(abs(mdp.numx.ravel(y)))) 
    if mdp.numx.iscomplexobj(x) or mdp.numx.iscomplexobj(y): maxdiff = maxdiff/2
    cond =  maxdiff< 10**(-digits)
    msg = msg+'\n\t Relative maximum difference: %e'%(maxdiff)+'\n\t'+\
          'Array1: '+str(x)+'\n\t'+\
          'Array2: '+str(y)+'\n\t'+\
          'Absolute Difference: '+str(abs(y-x))
    assert cond, msg 

