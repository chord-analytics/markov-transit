import sys
sys.path.append("/usr/src/")
from RouteModel.route import trunclognorm_cdf
from RouteModel.route import fast_trunclognorm_cdf
import numpy as np
bounded = lambda x: max(min(x,1.0),0.0)

def abs_error(x:float, a:float, b:float, mu:float, sigma:float) -> float:
    y1 = bounded(trunclognorm_cdf(x,a,b,mu,sigma))
    y2 = fast_trunclognorm_cdf(x,a,b,mu,sigma)
    return np.abs(y1-y2), y1, y2

def test_random_values(cutoff:float=10**-9):
    for x, a, b, mu, sigma in (np.random.rand(5000,5)):
        error, y1, y2 = abs_error(a+x,a,a+b+x,a+mu,sigma)
        if error > cutoff:
            print(f'error, y1, y2 = {error}, {y1}, {y2}')
            print(f'x, a, b, mu, sigma = {x}, {a}, {b}, {mu}, {sigma}')
        assert error < cutoff

def test_example_values(cutoff:float=10**-9):
    """
    Test examples values generated from the code.
    """
    samples = np.load("sample_lognormal_values.npy")
    for sample in samples:
        error,y1,y2 = abs_error(*sample)
        if error > cutoff:
            print(f'error, y1, y2 = {error}, {y1}, {y2}')
            print(f'x, a, b, mu, sigma = {sample}')
        assert error < cutoff


test_random_values(10**-9)
test_example_values()