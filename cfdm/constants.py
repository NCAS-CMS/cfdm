import logging
import sys
from enum import Enum

import numpy as np
from dask import config
from dask.utils import parse_bytes

_CHUNKSIZE = "128 MiB"
config.set({"array.chunk-size": _CHUNKSIZE})
"""A dictionary of useful constants.

Whilst the dictionary may be modified directly, it is safer to
retrieve and set the values with the dedicated get-and-set functions.

:Keys:

    ATOL: `float`
      The value of absolute tolerance for testing numerically tolerant
      equality.

    RTOL: `float`
      The value of relative tolerance for testing numerically tolerant
      equality.

    LOG_LEVEL: `str`
      The minimal level of seriousness for which log messages are
      shown.  See `cfdm.log_level`.

    CHUNKSIZE: `int`
      The Dask chunk size (in bytes). See `cfdm.chunksize`.

"""
CONSTANTS = {
    "ATOL": sys.float_info.epsilon,
    "RTOL": sys.float_info.epsilon,
    "LOG_LEVEL": logging.getLevelName(logging.getLogger().level),
    "CHUNKSIZE": parse_bytes(_CHUNKSIZE),
}


# --------------------------------------------------------------------
# logging
# --------------------------------------------------------------------
class ValidLogLevels(Enum):
    """Enumerates all valid log levels for the logging in cfdm."""

    DISABLE = 0
    WARNING = 1
    INFO = 2
    DETAIL = 3
    DEBUG = -1


# --------------------------------------------------------------------
# masked
# --------------------------------------------------------------------
"""A constant that allows data values to be masked by direct
assignment. This is consistent with the behaviour of numpy masked
arrays.

For example, masking every element of a field constructs data array
could be done as follows:

>>> f[...] = cfdm.masked

"""
masked = np.ma.masked
