import sys

import numpy


# --------------------------------------------------------------------
#   A dictionary of useful constants.
#
#   Whilst the dictionary may be modified directly, it is safer to
#   retrieve and set the values with a function where one is
#   provided. This is due to interdependencies between some values.
#
#   :Keys:
#
#        ATOL : float
#	    The value of absolute tolerance for testing numerically
#	    tolerant equality.
#
#        RTOL : float The value of relative tolerance for testing
#	    numerically tolerant equality.
#
#        TEMPDIR : str
#	    The location to store temporary files. By default it is
#	    the default directory used by the :mod:`tempfile` module.
#
# --------------------------------------------------------------------
CONSTANTS = {'RTOL'              : sys.float_info.epsilon,
             'ATOL'              : sys.float_info.epsilon,
             }
masked = numpy.ma.masked
