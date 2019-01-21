from scipy.stats import truncnorm 
from truncated_normal_stats import truncnormal_cdf
import numpy as np

bounded = lambda x: max(min(x,1.0),0.0)
def abs_error(x:float, a:float, b:float, mu:float, sigma:float) -> float:
    return np.abs(truncnormal_cdf(x,(a-mu)/sigma,(b-mu)/sigma) - bounded(truncnorm.cdf(x,a,b,mu,sigma)))

def test_random_values():
    for x, a, b in (np.random.rand(1000,3) * 3):
        error = abs_error(x,a,a+b,0,1)
        assert error < 10**-9
            
test_random_values()