import sys

import numpy

CONSTANTS = {
    # The value of absolute tolerance for testing numerically tolerant
    # equality.
    'RTOL': sys.float_info.epsilon,
    # The value of relative tolerance for testing numerically tolerant
    # equality.
    'ATOL': sys.float_info.epsilon,
}
masked = numpy.ma.masked
