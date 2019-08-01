import numpy as np

def laplace_noise(sensitivity, epsilon):
    _lambda = sensitivity / epsilon
    noise = np.random.laplace(loc = 0, scale = _lambda)
    return(noise)
