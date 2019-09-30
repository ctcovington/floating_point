import struct
import numpy as np
import scipy.stats as ss

def double_to_bin(x):
    """
    Converts a numeric variable (int, float, etc.) to its IEEE 64-bit representation.
    Representation consists of sign (length 1), exponent (length 11), and matissa (length 52).

    Parameters:
        x (numeric): Number for which 64-bit representation will be returned

    Return:
        String: 64-bit representation of x
    """
    return(bin(struct.unpack('!Q', struct.pack('!d', x))[0])[2:].zfill(64))

def bin_to_double(binary):
    """
    Converts an IEEE 64-bit representation to a 64-bit float (double).
    Representation consists of sign (length 1), exponent (length 11), and matissa (length 52).

    Parameters:
        binary (String): 64-bit representation of x

    Return:
        float64/double: Number corresponding to 64-bit representation
    """
    return(struct.unpack('!d',struct.pack('!Q', int(binary, 2)))[0])

def get_ieee_representation(binary):
    """
    Get IEEE representation of floating point number from 64-bit binary representation.
    """
    sign = binary[0]
    exponent = binary[1:12]
    mantissa = binary[12:]
    return(sign, exponent, mantissa)

def get_smallest_greater_power_of_two(_lambda):
    """
    Gets closest power of two that is >= _lambda.

    Parameters:
        _lambda (numeric): Argument to laplace noise

    Return:
        numeric: Smallest power of two that is >= _lambda -- we call this Lambda
        int: m such that Lambda = 2^m
    """
    # get IEEE representation of x
    binary = double_to_bin(_lambda)
    sign, exponent, mantissa = get_ieee_representation(binary)

    # return smallest power of two >= x
    if all(bit == '0' for bit in mantissa):
        return(_lambda, int(exponent, 2)-1023)
    else:
        # create mantissa of all zeros and incremented exponent, then use these to create smallest power of two >= x
        zero_mantissa = ''.zfill(len(mantissa))
        exponent_plus_one = bin(int(exponent, base = 2) + 1)[2:].zfill(len(exponent))
        return(bin_to_double(sign + exponent_plus_one + zero_mantissa), int(exponent_plus_one, 2)-1023)

def get_bias(f_D, B, _lambda):
    # make f_D and B nonnegative, but remember sign for return statement
    sign = np.sign(f_D)
    if sign == 0:
        sign = 1
    f_D = abs(f_D)
    B = abs(B)

    Lambda, m = get_smallest_greater_power_of_two(_lambda)

    # laplace params
    loc = -Lambda/2
    scale = _lambda

    # get probability of each bound binding, then the expected bias this contributes
    p_lower = ss.laplace.cdf(x = -B - f_D, loc = loc, scale = scale)
    bias_lower = (-B-f_D)*p_lower

    p_upper = 1 - ss.laplace.cdf(x = B - f_D, loc = loc, scale = scale)
    bias_upper = (B-f_D)*p_upper

    # get expectation of distribution in cases where bounds do not bind
    bias_rest = (1-p_lower-p_upper) * ss.laplace.expect(loc = loc, scale = scale, lb = -B-f_D, ub = B-f_D)

    # return bias
    return(sign*(bias_lower + bias_rest + bias_upper))

def get_max_bias(B, epsilon):
    max_bias = get_bias(f_D = B, B = B, epsilon = epsilon)
    return({-abs(max_bias), abs(max_bias)})