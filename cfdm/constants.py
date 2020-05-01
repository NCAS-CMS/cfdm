import logging
import sys

import numpy


CONSTANTS = {
    # The value of absolute tolerance for testing numerically tolerant
    # equality.
    'RTOL': sys.float_info.epsilon,
    # The value of relative tolerance for testing numerically tolerant
    # equality.
    'ATOL': sys.float_info.epsilon,
    # The minimal level of seriousness for which log messages are shown. See
    # functions.LOG_SEVERITY_LEVEL().
    'LOG_SEVERITY_LEVEL': logging.getLevelName(logging.getLogger().level),
}


# --------------------------------------------------------------------
# masked
# --------------------------------------------------------------------
'''A constant that allows data values to be masked by direct
assignment. This is consistent with the behaviour of numpy masked
arrays.

For example, masking every element of a field constructs data array
could be done as follows:

>>> f[...] = cfdm.masked

'''
masked = numpy.ma.masked
