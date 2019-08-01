import crlibm
import struct
import math
import random
import numpy as np
import gmpy2

class Snapping_Mechanism:
    """ Implementation of the Snapping Mechanism from Mironov (2012)

    This class presents an implementation of the Snapping Mechanism developed in Mironov (2012)
    (paper found at http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.366.5957&rep=rep1&type=pdf). The mechanism
    and associated proofs are described in section 5.2 of the paper.

    The mechanism was developed in order to avoid vulnerabilities in the Laplace Mechanism due to imprecise
    floating-point calculations. The 'snapping' can be thought of (loosely) as rounding the final output (input + laplace noise) such that
    potential output values are spaced slightly more than lambda apart.

    The mechanism itself is a little different than many others in that it takes the non-private statistic as an argument
    (it could theoretically be rewritten to take the raw data as an argument as well). That is, the noise is a function of
    the non-private statistic (among other things).

    Big thanks to Daniel Alabi and Ira Globus-Harris for their help. Daniel helped point me in the right direction with regards
    to rounding via IEEE representation manipulation. Ira came up with the main idea we eventually used for the IEEE
    manipulation, wrote the first implementation of it, and was very helpful in general with ideas and feedback on various
    piece of the implementation.

    Attributes:
        mechanism_input (numeric): Raw (non-private) value of statistic for which you want a private release
        sensitivity (numeric): Sensitivity of function generating mechanism input
        epsilon (numeric): DP-epsilon
        B (numeric): Suggested bound on the mechanism_input, corresponds to B from Mironov

    Methods:
        get_snapped_noise: Returns epsilon-DP noise in according with snapping mechanism

    Example:
        snap_object = Snapping_Mechanism(50, 0.012, 0.001, 200)
        snapped_noise = snap_object.get_snapped_noise()
    """

    def __init__(self, mechanism_input, sensitivity, epsilon, B):
        self.mechanism_input = mechanism_input
        self.sensitivity = sensitivity
        self.epsilon = epsilon
        self.B = B

    def _double_to_bin(x):
        """
        Converts a numeric variable (int, float, etc.) to its IEEE 64-bit representation.
        Representation consists of sign (length 1), exponent (length 11), and matissa (length 52).

        Parameters:
            x (numeric): Number for which 64-bit representation will be returned

        Return:
            String: 64-bit representation of x
        """
        return(bin(struct.unpack('!Q', struct.pack('!d', x))[0])[2:].zfill(64))

    def _bin_to_double(binary):
        """
        Converts an IEEE 64-bit representation to a 64-bit float (double).
        Representation consists of sign (length 1), exponent (length 11), and matissa (length 52).

        Parameters:
            binary (String): 64-bit representation of x

        Return:
            float64/double: Number corresponding to 64-bit representation
        """
        return(struct.unpack('!d',struct.pack('!Q', int(binary, 2)))[0])

    def _clamp(x, B):
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

    def _get_ieee_representation(binary):
        """
        Get IEEE representation of floating point number from 64-bit binary representation
        """
        sign = binary[0]
        exponent = binary[1:12]
        mantissa = binary[12:]
        return(sign, exponent, mantissa)

    def _get_Lambda(_lambda):
        """
        Gets closest power or two that is >= _lambda

        Parameters:
            _lambda (numeric): argument to laplace noise.

        Return:
            numeric: Smallest power of two that is >= _lambda -- we call this Lambda
            int: m such that Lambda = 2^m
        """
        # get IEEE representation of x
        binary = _double_to_bin(_lambda)
        sign, exponent, mantissa = _get_ieee_representation(binary)

        # return smallest power of two >= x
        if all(bit == '0' for bit in mantissa):
            return(_lambda, int(exponent, 2)-1023)
        else:
            # create mantissa of all zeros and incremented exponent, then use these to create smallest power of two >= x
            zero_mantissa = ''.zfill(len(mantissa))
            exponent_plus_one = bin(int(exponent, base = 2) + 1)[2:].zfill(len(exponent))
            return(bin_to_double(sign + exponent_plus_one + zero_mantissa), int(exponent_plus_one, 2)-1023)

    def _divide_by_power_of_two(sign, exponent, mantissa, power):
        """
        Divide by power of two and return updated exponent
        """
        exponent_num = int(exponent, 2) - power
        exponent = bin(exponent_num)[2:].zfill(11) # use [2:] to remove 0b from beginning of binary representation
        return(sign, exponent, mantissa)

    def _round_to_nearest_int(sign, exponent, mantissa):
        """
        Round the IEEE representation to the nearest integer.
        This proceeds by different cases for when the unbiased exponent >= 0 vs < 0.
        """
        # generate numeric version of unbiased exponent
        unbiased_exponent_num = int(exponent, 2) - 1023

        if unbiased_exponent_num >= 0:
            '''IEEE_rep >= Lambda'''
            # get elements of mantissa that represent integers
            # (after being multiplied by 2^unbiased_exponent_num)
            mantissa_subset = mantissa[0:unbiased_exponent_num]

            # check to see if mantissa needs to be rounded up or down
            if mantissa[unbiased_exponent_num] == '1':
                '''mantissa needs to be rounded up'''
                # if integer part of mantissa is all 1s, rounding needs to be reflected
                # in the exponent instead
                if mantissa_subset == '1' * len(mantissa_subset):
                    mantissa = ''.ljust(52, '0')
                    exponent_num = int(exponent, 2) + 1
                    exponent = bin(exponent_num)[2:].ljust(11, '0')
                else:
                    # if integer part of mantissa not all 1s, just increment mantissa
                    mantissa_subset_inc = bin(int(mantissa_subset, 2) + 1)[2:].zfill(len(mantissa_subset))
                    mantissa = mantissa_subset_inc.ljust(52, '0')
            elif mantissa[unbiased_exponent_num] == '0':
                '''mantissa needs to be rounded down'''
                mantissa = mantissa_subset.ljust(52, '0')
        elif unbiased_exponent_num < 0:
            '''IEEE_rep < Lambda'''
            if unbiased_exponent_num == -1:
                # round IEEE_rep to 1
                mantissa = ''.ljust(52, '0')
                exponent = '0'.ljust(11, '1')
            elif unbiased_exponent_num < -1:
                # round IEEE_rep to 0
                mantissa = ''.ljust(52, '0')
                exponent = ''.ljust(11, '0')

        return(sign, exponent, mantissa)

    def _multiply_by_power_of_two(sign, exponent, mantissa, power):
        """
        Multiply by power of two and return updated exponent
        """
        if exponent == '0'*len(exponent):
            return(sign, exponent, mantissa)
        else:
            exponent_num = int(exponent, 2) + power
            exponent = bin(exponent_num)[2:].zfill(11) # use [2:] to remove 0b from beginning of binary representation
            return(sign, exponent, mantissa)

    def _get_closest_multiple_of_Lambda(x, m):
        """
        Rounds x to the closest multiple of Lambda, resolving ties toward positive infinity

        Parameters:
            x (numeric): Number to be rounded to closest multiple of Lambda
            m (int): Integer such that Lambda = 2^m

        Return:
            numeric: x rounded to nearest multiple of Lambda
        """
        sign, exponent, mantissa = _get_ieee_representation(double_to_bin(x))
        sign_a, exponent_a, mantissa_a = _divide_by_power_of_two(sign, exponent, mantissa, m)
        sign_b, exponent_b, mantissa_b = _round_to_nearest_int(sign_a, exponent_a, mantissa_a)
        sign_c, exponent_c, mantissa_c = _multiply_by_power_of_two(sign_b, exponent_b, mantissa_b, m)
        return(bin_to_double(str(sign_c) + str(exponent_c) + str(mantissa_c)))

    def get_snapped_noise(self):
        """
        Generates noise for Snapping Mechanism
        """
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

        '''
        Scale input and bounds to sensitivity 1

        The results in the paper all rely on the function that calculates the statistic in question having sensitivity 1.
        So, we scale the input and bounds such that the function has sensitivity 1, implement the snapping mechanism, and rescale back to
        the original sensitivity.
        '''
        # scale clamping bound and mechanism input by sensitivity
        mechanism_input_scaled = self.mechanism_input / self.sensitivity
        B_scaled = self.B / self.sensitivity

        '''
        Construct private estimate

        See section 5.2 of Mironov (2012) for the definition of the snapping mechanism implemented below.
        '''
        # instantiate instance of cryptographically secure random class and generate random sign and draw from Unif(0,1)
        secure_random = random.SystemRandom()
        sign = gmpy2.mpfr(secure_random.sample(population = [-1,1], k = 1)[0]) # using mpfr precision here, even though it's an integer, so that the
                                                                               # precision carries through in later steps
        u_star_exponent = bin(-np.random.geometric(p = 0.5) + 1023)[2:]
        u_star_mantissa = ''.join([str(secure_random.sample(population = [0,1], k = 1)[0]) for i in range(52)])
        u_star_sample = bin_to_double('0' + str(u_star_exponent) + str(u_star_mantissa))

        # u_star_sample = gmpy2.mpfr(secure_random.uniform(0,1)) # NOTE: is this sufficient for U* as described in Mironov (2012)?
                                                               #       maybe should just implement as he describes

        '''
        TODO: GK's version creates overwrites epsilon before this step and I can't figure out why.
        '''
        inner_result = _clamp(mechanism_input_scaled, B_scaled) + (sign * 1/self.epsilon * crlibm.log_rn(u_star_sample))

        # NOTE: this Lambda is calculated relative to lambda = 1/epsilon rather than sensitivity/epsilon because we have already
        #       scaled by the sensitivity
        Lambda, m = _get_Lambda(1/self.epsilon)
        inner_result_rounded = _get_closest_multiple_of_Lambda(float(inner_result), m)
        private_estimate = _clamp(self.sensitivity * inner_result_rounded, self.B)
        snapped_noise = private_estimate - self.mechanism_input

        return(snapped_noise)
