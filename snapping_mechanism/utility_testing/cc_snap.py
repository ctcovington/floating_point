import crlibm
import struct
import math
import random
import numpy as np

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

def get_smallest_larger_power_of_two(x):
    """
    Gets closest power or two that is >= x

    Parameters:
        x (numeric): A number.

    Return:
        numeric: Smallest power of two that is >= x
    """
    # get IEEE representation of x
    binary = double_to_bin(x)
    sign = binary[0]
    exponent = binary[1:12]
    mantissa = binary[12:]

    # return smallest power of two >= x
    if all(bit == '0' for bit in mantissa):
        return(x)
    else:
        # create mantissa of all zeros and incremented exponent, then use these to create smallest power of two >= x
        zero_mantissa = ''.zfill(len(mantissa))
        exponent_plus_one = bin(int(exponent, base = 2) + 1)[2:].zfill(len(exponent))
        return(bin_to_double(sign + exponent_plus_one + zero_mantissa))

def get_closest_multiple_of_m(x, m):
    """
    NOTE: This is probably not sufficient
    """
    remainder = x % m
    if remainder == 0:
        return x
    else:
        lower_multiple = x - (remainder)
        higher_multiple = x + (m - remainder)
        if remainder < (m - remainder):
            return(lower_multiple)
        else:
            return(higher_multiple)

# def get_closest_multiple_of_Lambda(x, _lambda):
#     """
#     Rounds input to nearest multiple of Lambda (which is smallest power of two >= lambda), with ties resolved towards positive infinity.
#     Works for positive or negative numbers.
#     Uses 64-bit representation of number to adhere to guidelines in Mironov (2012)
#
#     Parameters:
#         x (numeric): Number to be rounded
#         _lambda (numeric): Argument to Laplace distribution
#
#     Return:
#         float64/double: x rounded to nearest multiple of Lambda
#     """
#     # get Lambda
#     Lambda = get_smallest_larger_power_of_two(_lambda)
#
#     # get multiple of lambda that is closest to x
#     x_rounded_to_Lambda = get_closest_multiple_of_m(x, Lambda)
#
#     return(x_rounded_to_Lambda)

def clamp(x, B):
    """
    If abs(x) > abs(B), clamps x towards 0 such that abs(x) = abs(B).

    Parameters:
        x (numeric): Number to be clamped.
        B (numeric): Bounds to which x should be clamped.

    Return:
        numeric: Clamped version of x.
    """
    if (x < -abs(B)):
        return(-abs(B))
    elif (x > abs(B)):
        return(abs(B))
    return(x)

# def add_snapped_laplace_noise(non_private_estimate, _lambda, B):
#     """
#     Add snapped Laplace noise. This is written as a two step process:
#     (1) Generate private estimate as described on pg. 11 of Mironov (2012).
#     (2) Define noise as difference between non-private and private estimates.
#
#     Parameters:
#         non_private_estimate (numeric): Statistic computed non-privately to which we want to add noise.
#         _lambda (numeric): Argument to Laplace distribution.
#                            NOTE: This should be the function sensitivity divided by epsilon?
#         B (numeric): Bounds to which x should be clamped.
#
#     Return:
#         numeric: noise necessary to create differentially-private estimate
#     """
#
#     '''
#     TODO:
#     '''
#     # construct private estimate
#     secure_random = random.SystemRandom() # instantiate instance of cryptographically secure random class
#     sign = secure_random.sample(population = [-1,1], k = 1)[0]
#     u_star_sample = secure_random.uniform(0,1) # NOTE: is this sufficient for U* as described in Mironov (2012)?
#     inner_result = clamp(non_private_estimate, B) + (sign * _lambda * crlibm.log_rn(u_star_sample))
#     Lambda = get_smallest_larger_power_of_two(_lambda)
#     inner_result_rounded = get_closest_multiple_of_m(inner_result, m = Lambda)
#     private_estimate = clamp(inner_result_rounded, B)
#
#     # return noise necessary to create private estimate
#     return(private_estimate - non_private_estimate)

def add_snapped_laplace_noise(non_private_estimate, sensitivity, epsilon, B):
    # scale clamping bound and non_private estimate by sensitivity
    B_scaled = B / sensitivity
    non_private_estimate_scaled = non_private_estimate / sensitivity

    # construct private estimate
    secure_random = random.SystemRandom() # instantiate instance of cryptographically secure random class
    sign = secure_random.sample(population = [-1,1], k = 1)[0]
    u_star_sample = secure_random.uniform(0,1) # NOTE: is this sufficient for U* as described in Mironov (2012)?
    '''
    TODO: GK's version creates overwrites epsilon before this step and I can't figure out why.
    '''
    inner_result = clamp(non_private_estimate_scaled, B_scaled) + (sign * 1/epsilon * crlibm.log_rn(u_star_sample))

    '''
    TODO: working on way to get closest multiple of a power of two via manipulation of the IEEE representations
    '''
    Lambda = get_smallest_larger_power_of_two(x = 1/epsilon)
    inner_result_rounded = get_closest_multiple_of_m(inner_result, m = Lambda)
    private_estimate = clamp(sensitivity * inner_result_rounded, B)

    return(private_estimate)

    # return noise necessary to create private estimate
    # return(private_estimate - non_private_estimate)


def main():
    pass

if __name__ == '__main__':
    main()
