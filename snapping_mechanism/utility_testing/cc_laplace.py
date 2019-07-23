import numpy as np

def add_laplace_noise(non_private_estimate, sensitivity, epsilon):
    _lambda = sensitivity / epsilon
    private_estimate = non_private_estimate + np.random.laplace(loc = 0, scale = _lambda)
    return(private_estimate)
