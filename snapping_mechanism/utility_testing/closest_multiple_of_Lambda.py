import struct

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

# n: double type value
# return: n as a Float object as defined in the below class.
def floatObjectConstructor(n):
    """
    CC added exponent
    """
    bitString = double_to_bin(n)
    sign = int(bitString[0],2)
    exponent = int(bitString[1:	12], 2)
    exponent = bitString[1:	12]
    significand = bitString[12:]
    return(Float(sign, exponent, significand))

class Float:
    # sign: integer representation of the sign value of float
    # exponent: integer representation of the exponent of float (not including the offset by 1024)
    # significand: string representation of the 52 explicitly stored significant digits of float
    def __init__(self, sign, exponent, significand):
        """
        CC added exponent
        """
        self.sign = sign
        self.exponent = exponent
        self.significand = significand

    def round(self):
        """
        Round the significand to only include 'integer' component.
        """
        #ToDo
        unbiased_exponent_num = int(self.exponent, 2) - 1023
        exponent = self.exponent

        """
        This is not working right not
        Also, we might need to handle the case where closest multiple is 0 separately
        """

        if unbiased_exponent_num >= 0:
            '''self >= Lambda'''
            # get elements of significand that represent integers
            # (after being multiplied by 2^unbiased_exponent_num)
            significand_subset = self.significand[0:unbiased_exponent_num]

            # check to see if significand needs to be rounded up or down
            if self.significand[unbiased_exponent_num] == '1':
                '''significand needs to be rounded up'''
                # if integer part of significand is all 1s, rounding needs to be reflected
                # in the exponent instead
                if significand_subset == '1' * len(significand_subset):
                    significand = ''.ljust(52, '0')
                    exponent_num = int(exponent, 2) + 1
                    exponent = bin(exponent_num)[2:].ljust(11, '0')
                else:
                    # if integer part of significand not all 1s, just increment significand
                    significand_subset = bin(int(significand_subset, 2) + 1)[2:]
                    significand = significand_subset.ljust(52, '0')
            elif self.significand[unbiased_exponent_num] == '0':
                '''significand needs to be rounded down'''
                significand = significand_subset.ljust(52, '0')
        elif unbiased_exponent_num < 0:
            '''self < Lambda'''
            if unbiased_exponent_num == -1:
                significand = ''.ljust(52, '0')
                exponent = '0'.ljust(11, '1')
            elif unbiased_exponent_num < -1:
                significand = ''.ljust(52, '0')
                exponent = ''.ljust(11, '0')


        return(Float(self.sign, exponent, significand))

    def divide_by_power_of_two(self, power):
        """
        Divide self by 2^n and return result as a new Float object
        """

        """
        CC added exponent
        """
        exponent_num = int(self.exponent, 2) - power
        exponent = bin(exponent_num)[2:].zfill(11) # use [2:] to remove 0b from beginning of binary representation
        return(Float(self.sign, exponent, self.significand))

    def multiply_by_power_of_two(self, power):
        """
        CC added exponent
        """
        exponent_num = int(self.exponent, 2) + power
        exponent = bin(exponent_num)[2:].zfill(11) # use [2:] to remove 0b from beginning of binary representation
        return(Float(self.sign, exponent, self.significand))

    def to_double(self):
        """"""
        return(bin_to_double(str(self.sign) + str(self.exponent) + str(self.significand)))

# n: exponent on lambda; i.e. Lambda = 2^m
# x: Float object
# return: Float object representation of nearest multiple of Lambda to x.
def get_closest_multiple_of_Lambda(x, m):
    a = x.divide_by_power_of_two(m)
    b = a.round()
    c = b.multiply_by_power_of_two(m)
    return(c.to_double())

def test(num, m):
    x = floatObjectConstructor(num)
    ans = get_closest_multiple_of_Lambda(x, m)
    print(ans)
