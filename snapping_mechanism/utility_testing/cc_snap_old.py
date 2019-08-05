import crlibm
import struct
import math
import random
import numpy as np
import gmpy2

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


# def get_smallest_larger_power_of_two(x):
#     """
#     Gets closest power or two that is >= x
#
#     Parameters:
#         x (numeric): A number.
#
#     Return:
#         numeric: Smallest power of two that is >= x
#     """
#     # get IEEE representation of x
#     binary = double_to_bin(x)
#     sign = binary[0]
#     exponent = binary[1:12]
#     mantissa = binary[12:]
#
#     # return smallest power of two >= x
#     if all(bit == '0' for bit in mantissa):
#         return(x)
#     else:
#         # create mantissa of all zeros and incremented exponent, then use these to create smallest power of two >= x
#         zero_mantissa = ''.zfill(len(mantissa))
#         exponent_plus_one = bin(int(exponent, base = 2) + 1)[2:].zfill(len(exponent))
#         return(bin_to_double(sign + exponent_plus_one + zero_mantissa))

# def get_closest_multiple_of_m(x, m):
#     """
#     NOTE: This is probably not sufficient
#     """
#     remainder = x % m
#     if remainder == 0:
#         return x
#     else:
#         lower_multiple = x - (remainder)
#         higher_multiple = x + (m - remainder)
#         if remainder < (m - remainder):
#             return(lower_multiple)
#         else:
#             return(higher_multiple)

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

def add_snapped_laplace_noise(mechanism_input, sensitivity, epsilon, B):
    # scale clamping bound and mechanism input by sensitivity
    B_scaled = B / sensitivity
    mechanism_input_scaled = mechanism_input / sensitivity

    # set bits of numerical precision for the elements for which we need exact rounding
    # NOTE: Exact rounding, described in section 1.1 of http://www.ens-lyon.fr/LIP/Pub/Rapports/RR/RR2005/RR2005-37.pdf,
    #       is an alternative to accurate-faithful calculations (which is what most mathemematical libraries are).
    #       If the real-valued number falls between two floating point numbers, cccurate-faithful calculations
    #       return one of those two floating point numbers and usually returns the one that is closer to the
    #       real number. Exact rounding always returns the floating point number that is closer.
    # NOTE: I don't actually know what precision is needed for exact rounding.
    #       I chose 118 because this is the number of bits necessary for exact rounding of the log (see section
    #       2.1 at http://www.ens-lyon.fr/LIP/Pub/Rapports/RR/RR2005/RR2005-37.pdf), but I should clarify this
    #       with someone who might know better
    gmpy2.get_context().precision = 118

    # construct private estimate
    secure_random = random.SystemRandom() # instantiate instance of cryptographically secure random class
    sign = gmpy2.mpfr(secure_random.sample(population = [-1,1], k = 1)[0])
    u_star_sample = gmpy2.mpfr(secure_random.uniform(0,1)) # NOTE: is this sufficient for U* as described in Mironov (2012)?
                                                           #       maybe should just implement as he describes
    '''
    TODO: GK's version creates overwrites epsilon before this step and I can't figure out why.
    '''
    inner_result = clamp(mechanism_input_scaled, B_scaled) + (sign * 1/epsilon * crlibm.log_rn(u_star_sample))

    '''
    TODO: working on way to get closest multiple of a power of two via manipulation of the IEEE representations
    '''
    Lambda = get_smallest_larger_power_of_two(x = 1/epsilon)
    inner_result_rounded = get_closest_multiple_of_m(inner_result, m = Lambda)
    private_estimate = clamp(sensitivity * inner_result_rounded, B)

    return(float(private_estimate))

def main():
    pass

if __name__ == '__main__':
    main()
