import numpy as np
import scipy.stats as ss

def get_bias(f_D, B, epsilon, Lambda):
    # make f_D and B nonnegative, but remember sign for return statement
    sign = np.sign(f_D)
    f_D = abs(f_D)
    B = abs(B)

    # laplace params
    loc = -Lambda/2
    scale = 1/epsilon

    # get probability of each bound binding, then the expected bias this contributes
    p_lower = ss.laplace.cdf(x = -B - f_D, loc = loc, scale = scale)
    bias_lower = (-B-f_D)*p_lower

    p_upper = 1 - ss.laplace.cdf(x = B - f_D, loc = loc, scale = scale)
    bias_upper = (B-f_D)*p_upper

    # get expectation of distribution in cases where bounds do not bind
    bias_rest = (1-p_lower-p_upper) * ss.laplace.expect(loc = loc, scale = scale, lb = -B-f_D, ub = B-f_D)

    # return bias
    return(sign*(bias_lower + bias_rest + bias_upper))