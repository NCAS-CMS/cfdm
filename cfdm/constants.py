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
    # functions.LOG_LEVEL().
    'LOG_LEVEL': logging.getLevelName(logging.getLogger().level),
}


# --------------------------------------------------------------------
# logging
# --------------------------------------------------------------------
valid_log_levels = [  # order (highest to lowest severity) must be preserved
    'DISABLE',
    'WARNING',
    'INFO',
    'DETAIL',
    'DEBUG',
]
# Map string level identifiers to ints from 0 to len(valid_log_levels):
numeric_log_level_map = dict(enumerate(valid_log_levels))
# We treat 'DEBUG' as a special case so assign to '-1' rather than highest int:
numeric_log_level_map[-1] = numeric_log_level_map.pop(
    len(valid_log_levels) - 1)
# Result for print(numeric_log_level_map) is:
# {0: 'DISABLE', 1: 'WARNING', 2: 'INFO', 3: 'DETAIL', -1: 'DEBUG'}


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
