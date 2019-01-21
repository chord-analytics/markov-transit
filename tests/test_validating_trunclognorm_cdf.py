import sys
sys.path.append("/usr/src/")
from RouteModel.route import trunclognorm_cdf
from RouteModel.route import fast_trunclognorm_cdf
import numpy as np
def abs_error(x:float, a:float, b:float, mu:float, sigma:float) -> float:
    return np.abs(trunclognorm_cdf(x,a,b,mu,sigma) - fast_trunclognorm_cdf(x,a,b,mu,sigma))

def test_random_values():
    for x, mu, sigma, a, b in (np.random.rand(1000,5) * 10):
        error = abs_error(x, a, a+b, mu, sigma)
        assert abs_error(x,0,1,mu,sigma) < 10**-10

test_random_values()