from __future__ import print_function
from future import standard_library
standard_library.install_aliases()
from builtins import str

import logging
import os
import platform
import sys
import urllib.parse

import netCDF4
import cftime
import numpy
import future

from . import (__version__,
               __cf_version__,
               __file__)

from .constants import CONSTANTS, valid_log_levels, numeric_log_level_map


def ATOL(*atol):
    '''The tolerance on absolute differences when testing for numerically
    tolerant equality.

    Two real numbers ``x`` and ``y`` are considered equal if
    ``abs(x-y) <= atol + rtol*abs(y)``, where atol (the tolerance on
    absolute differences) and rtol (the tolerance on relative
    differences) are positive, typically very small numbers. By
    default both are set to the system epsilon (the difference between
    1 and the least value greater than 1 that is representable as a
    float).

    .. versionadded:: 1.7.0

    .. seealso:: `RTOL`

    :Parameters:

        atol: `float`, optional
            The new value of absolute tolerance. The default is to not
            change the current value.

    :Returns:

        `float`
            The value prior to the change, or the current value if no
            new value was specified.

    **Examples:**

    >>> ATOL()
    2.220446049250313e-16
    >>> old = ATOL(1e-10)
    >>> ATOL()
    1e-10
    >>> ATOL(old)
    1e-10
    >>> ATOL()
    2.220446049250313e-16

    '''
    old = CONSTANTS['ATOL']
    if atol:
        CONSTANTS['ATOL'] = float(atol[0])

    return old

def RTOL(*rtol):
    '''The tolerance on relative differences when testing for numerically
    tolerant equality.

    Two real numbers ``x`` and ``y`` are considered equal if
    ``abs(x-y) <= atol + rtol*abs(y)``, where atol (the tolerance on
    absolute differences) and rtol (the tolerance on relative
    differences) are positive, typically very small numbers. By
    default both are set to the system epsilon (the difference between
    1 and the least value greater than 1 that is representable as a
    float).

    .. versionadded:: 1.7.0

    .. seealso:: `ATOL`

    :Parameters:

        rtol: `float`, optional
            The new value of relative tolerance. The default is to not
            change the current value.

    :Returns:

        `float`
            The value prior to the change, or the current value if no
            new value was specified.

    **Examples:**

    >>> RTOL()
    2.220446049250313e-16
    >>> old = RTOL(1e-10)
    >>> RTOL()
    1e-10
    >>> RTOL(old)
    1e-10
    >>> RTOL()
    2.220446049250313e-16

    '''
    old = CONSTANTS['RTOL']
    if rtol:
        CONSTANTS['RTOL'] = float(rtol[0])

    return old


def LOG_LEVEL(*log_level):
    '''The minimal level of seriousness of log messages which are shown.

    This can be adjusted to filter out potentially-useful log messages
    generated by cfdm at runtime, such that any messages marked
    as having a severity below the level set will not be reported.

    For example, when set to 'WARNING' (or equivalently 1), all messages
    categorised as 'DEBUG' or 'INFO' will be supressed, and only warnings
    will emerge.

    See the dedicated :ref:`section about logging <logging>` for a
    detailed breakdown on the levels and configuration possibilities.

    The default level is 'WARNING' (`1`).

    .. versionadded:: 1.8.4

    :Parameters:

        log_level: `str` ot `int`, optional
            The new value of the minimal log severity level. This can be
            specified either as a string equal (ignoring case) to
            the named set of log levels or identifier 'DISABLE', or
            an integer code corresponding to each of these, namely:

            * 'DISABLE' (`0`);
            * 'WARNING' (`1`);
            * 'INFO' (`2`);
            * 'DETAIL' (`3`);
            * 'DEBUG' (`-1`).

    :Returns:

        `str`
            The value prior to the change, or the current value if no new
            value was specified (or if one was specified but was not valid).
            Note the string name, rather than the equivalent integer, will
            always be returned.

    **Examples:**

    >>> LOG_LEVEL()  # get the current value
    'WARNING'
    >>> LOG_LEVEL('INFO')  # change the value to 'INFO'
    'WARNING'
    >>> LOG_LEVEL()
    'INFO'
    >>> LOG_LEVEL(0)  # set to 'DISABLE' via corresponding integer
    'INFO'
    >>> LOG_LEVEL()
    'DISABLE'
    '''
    old = CONSTANTS['LOG_LEVEL']

    if log_level:
        level = log_level[0]

        if isinstance(level, str):
            level = level.upper()
        elif level in numeric_log_level_map:
            level = numeric_log_level_map[level]  # convert to string ID first

        # Ensuring it is a valid level specifier to set & use, either a
        # case-insensitive string of valid log level or dis/en-abler, or an
        # integer 0 to 5 corresponding to one of those as converted above:
        if level in valid_log_levels:
            CONSTANTS['LOG_LEVEL'] = level
            _reset_log_emergence_level(level)
        else:
            raise ValueError(
                "Logging level '{}' is not one of the valid values '{}', or "
                "a corresponding integer of 0 to {} and (lastly) -1, "
                "respectively. Value remains as it was, at:".format(
                    level, "', '".join(valid_log_levels),
                    len(valid_log_levels) - 2
                )
            )
    return old


def _reset_log_emergence_level(level, logger=None):
    '''Re-set minimum severity level for displayed log messages of a logger.

    This may correspond to a change, otherwise will re-set to the same value
    (which is harmless, & as costly as checking to avoid this in that case).

    The level specified must be a valid logging level string name or
    equivalent integer (see valid_log_levels in LOG_LEVEL
    above), else a ValueError will be raised by the logging module.

    Unless another logger is specified, this will apply to the root logger.

    Important: with an input level of 'DISABLE' (0), this method only
    disables the logging; the responsibility to re-enable it once the need for
    deactivation is over lies with methods that call this.
    '''
    if logger:
        use_logger = logging.getLogger(logger)
    else:  # apply to root, which all other (module) loggers inherit from
        use_logger = logging.getLogger()

    if level in numeric_log_level_map:
        level = numeric_log_level_map[level]  # convert to string ID first

    if level == 'DISABLE':
        _disable_logging()
    else:
        # First must (re-)enable in case logging previously was disabled:
        _disable_logging(at_level='NOTSET')
        use_logger.setLevel(getattr(logging, level))


def _disable_logging(at_level=None):
    '''Disable log messages at and below a given level, else completely.

    This is an overriding level for all loggers.

    If 'at_level' is not provided, it defaults under the hood to 'CRITICAL'
    (see https://docs.python.org/3/library/logging.html#logging.disable),
    the highest level in the Python logging module (that we do not expose
    or use explicitly to tag any messages).

    Note specifying 'NOTSET' as the input will revert any disactivation level
    previously set with this method, so the logger regains its original level.
    '''
    if at_level:
        logging.disable(getattr(logging, at_level))
    else:
        logging.disable()


def environment(display=True, paths=True):
    '''Return the names, versions and paths of all dependencies.

    .. versionadded:: 1.7.0

    :Parameters:

        display: `bool`, optional
            If False then return the description of the environment as
            a string. By default the description is printed.

        paths: `bool`, optional
            If False then do not output the locations of each package.

    :Returns:

        `None` or `list`
            If *display* is True then the description of the
            environment is printed and `None` is returned. Otherwise
            the description is returned as in a `list`.

    **Examples:**

    >>> environment()
    Platform: Linux-4.15.0-72-generic-x86_64-with-debian-stretch-sid
    HDF5 library: 1.10.2
    netcdf library: 4.6.1
    python: 3.7.3 /home/user/anaconda3/bin/python
    python: 3.7.3 /home/user/anaconda3/bin/python
    future: 0.17.1 /home/user/anaconda3/lib/python3.7/site-packages/future/__init__.py
    netCDF4: 1.5.3 /home/user/anaconda3/lib/python3.7/site-packages/netCDF4/__init__.py
    cftime: 1.1.0 /home/user/anaconda3/lib/python3.7/site-packages/cftime/__init__.py
    numpy: 1.16.2 /home/user/anaconda3/lib/python3.7/site-packages/numpy/__init__.py
    cfdm: 1.8.0

    >>> environment(paths=False)
    Platform: Linux-4.15.0-72-generic-x86_64-with-debian-stretch-sid
    HDF5 library: 1.10.2
    netcdf library: 4.6.1
    python: 3.7.3
    future: 0.17.1
    netCDF4: 1.5.3
    cftime: 1.1.0
    numpy: 1.16.2
    cfdm: 1.8.0

    '''
    out = []

    out.append('Platform: ' + str(platform.platform()))
    out.append('HDF5 library: ' + str(netCDF4. __hdf5libversion__))
    out.append('netcdf library: ' + str(netCDF4.__netcdf4libversion__))

    out.append('python: ' + str(platform.python_version()))
    if paths:
        out[-1] += ' ' + str(sys.executable)

    out.append('future: ' + str(future.__version__))
    if paths:
        out[-1] += ' ' + str(os.path.abspath(future.__file__))

    out.append('netCDF4: ' + str(netCDF4.__version__))
    if paths:
        out[-1] += ' ' + str(os.path.abspath(netCDF4.__file__))

    out.append('cftime: ' + str(cftime.__version__))
    if paths:
        out[-1] += ' ' + str(os.path.abspath(cftime.__file__))

    out.append('numpy: ' + str(numpy.__version__))
    if paths:
        out[-1] += ' ' + str(os.path.abspath(numpy.__file__))

    out.append('cfdm: ' + str(__version__))
    if paths:
        out[-1] += ' ' + str(os.path.abspath(__file__))

    if display:
        print('\n'.join(out))
    else:
        return out

def CF():
    '''The version of the CF conventions.

    This indicates which version of the CF conventions are represented
    by this release of the cfdm package, and therefore the version can
    not be changed.

    .. versionadded:: 1.7.0

    :Returns:

        `str`
            The version of the CF conventions represented by this
            release of the cfdm package.

    **Examples:**

    >>> CF()
    '1.8'

    '''
    return __cf_version__

def abspath(filename):
    '''Return a normalised absolute version of a file name.

    If a string containing URL is provided then it is returned
    unchanged.

    :Parameters:

        filename: `str`
            The name of the file.

    :Returns:

        `str`
            The normalized absolutized version of *filename*.

    **Examples:**

    >>> import os
    >>> os.getcwd()
    '/data/archive'
    >>> abspath('file.nc')
    '/data/archive/file.nc'
    >>> abspath('..//archive///file.nc')
    '/data/archive/file.nc'
    >>> abspath('http://data/archive/file.nc')
    'http://data/archive/file.nc'

    '''
    u = urllib.parse.urlparse(filename)
    if u.scheme != '':
        return filename

    return os.path.abspath(filename)

def default_netCDF_fill_values():
    '''The default netCDF fill values for each data type.

    :Returns:

        `dict`
            The default fill values, keyed by `numpy` data type
            strings

    **Examples:**

    >>> default_netCDF_fill_values()
    {'S1': '\x00',
     'i1': -127,
     'u1': 255,
     'i2': -32767,
     'u2': 65535,
     'i4': -2147483647,
     'u4': 4294967295,
     'i8': -9223372036854775806,
     'u8': 18446744073709551614,
     'f4': 9.969209968386869e+36,
     'f8': 9.969209968386869e+36}

    '''
    return netCDF4.default_fillvals
