import logging
import os
import platform
import sys
import urllib.parse

import netCDF4
import cftime
import numpy
import netcdf_flattener

from . import (__version__,
               __cf_version__,
               __file__)

from .constants import CONSTANTS, ValidLogLevels


def configuration(atol=None, rtol=None, log_level=None):
    '''View or set any number of constants in the project-wide configuration.

    The full list of global constants that are provided in a dictionary to
    view, and can be set in any combination, are:

    * `atol`
    * `rtol`
    * `log_level`

    These are all constants that apply throughout `cfdm`, except for in
    specific functions only if overriden by the corresponding keyword
    argument to that function.

    The value of `None`, either taken by default or supplied as a value,
    will result in the constant in question not being changed from the
    current value. That is, it will have no effect.

    Note that setting a constant using this function is equivalent to setting
    it by means of a specific function of the same name, e.g. via `cfdm.atol`,
    but in this case multiple constants can be set at once.

    .. versionadded:: 1.8.6

    .. seealso:: `atol`, `rtol`, `log_level`

    :Parameters:

        atol: `float`, optional
            The new value of absolute tolerance. The default is to not
            change the current value.

        rtol: `float`, optional
            The new value of relative tolerance. The default is to not
            change the current value.

        log_level: `str` or `int`, optional
            The new value of the minimal log severity level. This can
            be specified either as a string equal (ignoring case) to
            the named set of log levels or identifier 'DISABLE', or an
            integer code corresponding to each of these, namely:

            * ``'DISABLE'`` (``0``);
            * ``'WARNING'`` (``1``);
            * ``'INFO'`` (``2``);
            * ``'DETAIL'`` (``3``);
            * ``'DEBUG'`` (``-1``).

    :Returns:

        `dict`
            The names and values of the project-wide constants prior to the
            change, or the current names and values if no new values are
            specified.

    **Examples:**

    >>> cfdm.configuration()  # view full global configuration of constants
    {'atol': 2.220446049250313e-16,
     'rtol': 2.220446049250313e-16,
     'log_level': 'WARNING'}
    >>> cfdm.log_level('DEBUG')  # make a change to one constant...
    'WARNING'
    >>> cfdm.configuration()  # ...and it is reflected in the configuration
    {'atol': 2.220446049250313e-16,
     'rtol': 2.220446049250313e-16,
     'log_level': 'DEBUG'}

    >>> cfdm.configuration()['atol']  # access specific values by key querying
    2.220446049250313e-16
    >>> cfdm.configuration()['atol'] == cfdm.atol()  # note the equivalency
    True

    >>> cfdm.configuration(atol=5e-14, log_level='INFO')  # set multiple items
    {'atol': 2.220446049250313e-16,
     'rtol': 2.220446049250313e-16,
     'log_level': 'DEBUG'}
    >>> cfdm.configuration()
    {'atol': 5e-14, 'rtol': 2.220446049250313e-16, 'log_level': 'INFO'}

    >>> cfdm.configuration(rtol=1e-17)  # equivalent to setting cfdm.rtol(1e-17)
    {'atol': 5e-14, 'rtol': 2.220446049250313e-16, 'log_level': 'INFO'}
    >>> cfdm.configuration()
    {'atol': 5e-14, 'rtol': 1e-17, 'log_level': 'INFO'}
    '''
    return _configuration(
        new_atol=atol, new_rtol=rtol, new_log_level=log_level)


def _configuration(**kwargs):
    '''Internal helper function to provide the logic for `cfdm.configuration`.

    We delegate from the user-facing `cfdm.configuration` for two main reasons:

    1) to avoid a name clash there between the keyword arguments and the
    functions which they each call (e.g. `atol` and `cfdm.atol`) which
    would otherwise necessitate aliasing every such function name; and

    2) because the user-facing function must have the appropriate keywords
    explicitly listed, but the very similar logic applied for each keyword
    can be consolidated by iterating over the full dictionary of input kwargs.

    '''
    old = {name.lower(): val for name, val in CONSTANTS.items()}
    # Filter out 'None' kwargs from configuration() defaults. Note that this
    # does not filter out '0' or 'True' values, which is important as the user
    # might be trying to set those, as opposed to None emerging as default.
    kwargs = {name: val for name, val in kwargs.items() if val is not None}

    # Note values are the functions not the keyword arguments of same name:
    reset_mapping = {
        'new_atol': atol,
        'new_rtol': rtol,
        'new_log_level': log_level,
    }
    for setting_alias, new_value in kwargs.items():  # for all input kwargs...
        reset_mapping[setting_alias](new_value)  # ...run corresponding func

    return old


def atol(*atol):
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

    .. seealso:: `rtol`

    :Parameters:

        atol: `float`, optional
            The new value of absolute tolerance. The default is to not
            change the current value.

    :Returns:

        `float`
            The value prior to the change, or the current value if no
            new value was specified.

    **Examples:**

    >>> atol()
    2.220446049250313e-16
    >>> old = atol(1e-10)
    >>> atol()
    1e-10
    >>> atol(old)
    1e-10
    >>> atol()
    2.220446049250313e-16

    '''
    old = CONSTANTS['ATOL']
    if atol:
        CONSTANTS['ATOL'] = float(atol[0])

    return old


def ATOL(*new_atol):
    '''Alias for `cfdm.atol`.
    '''
    return atol(*new_atol)


def rtol(*rtol):
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

    .. seealso:: `atol`

    :Parameters:

        rtol: `float`, optional
            The new value of relative tolerance. The default is to not
            change the current value.

    :Returns:

        `float`
            The value prior to the change, or the current value if no
            new value was specified.

    **Examples:**

    >>> rtol()
    2.220446049250313e-16
    >>> old = rtol(1e-10)
    >>> rtol()
    1e-10
    >>> rtol(old)
    1e-10
    >>> rtol()
    2.220446049250313e-16

    '''
    old = CONSTANTS['RTOL']
    if rtol:
        CONSTANTS['RTOL'] = float(rtol[0])

    return old


def RTOL(*new_rtol):
    '''Alias for `cfdm.rtol`.
    '''
    return rtol(*new_rtol)


def _log_level(constants_dict, log_level):
    ''' Equivalent to log_level, but with dict to modify as an argument.

    This internal function is designed specifically so that a different
    constants_dict can be manipulated with setting or reading of the
    log level, without the constants dictionary becoming a user-facing
    argument. log_level is the only function of the pair documented for use.

    Overall, this means that cf-python can import these functions and use
    them such that it can manipulate (its own separate) log_level constant.

    Note: relies on the mutability of arguments (here the constants_dict).
    '''
    old = constants_dict['LOG_LEVEL']

    if log_level:
        level = log_level[0]

        # Ensuring it is a valid level specifier to set & use, either
        # a case-insensitive string of valid log level or
        # dis/en-abler, or an integer 0 to 5 corresponding to one of
        # those as converted above:
        if isinstance(level, str):
            level = level.upper()
        elif _is_valid_log_level_int(level):
            level = ValidLogLevels(level).name  # convert to string ID first

        if not hasattr(ValidLogLevels, level):
            raise ValueError(
                "Logging level {!r} is not one of the valid values '{}', "
                "where either the string or the corrsponding integer is "
                "accepted. Value remains as it was, at '{}'.".format(
                    level, ", '".join([val.name + "' = " + str(val.value)
                                       for val in ValidLogLevels]), old
                )
            )
        # Safe to reset now as guaranteed to be valid:
        constants_dict['LOG_LEVEL'] = level
        _reset_log_emergence_level(level)

    # --- End: if

    return old


def log_level(*log_level):
    '''The minimal level of seriousness of log messages which are shown.

    This can be adjusted to filter out potentially-useful log messages
    generated by cfdm at runtime, such that any messages marked as
    having a severity below the level set will not be reported.

    For example, when set to ``'WARNING'`` (or equivalently ``1``),
    all messages categorised as ``'DEBUG'`` or ``'INFO'`` will be
    supressed, and only warnings will emerge.

    See https://ncas-cms.github.io/cfdm/tutorial.html#logging for a
    detailed breakdown on the levels and configuration possibilities.

    The default level is ``'WARNING'`` (``1``).

    .. versionadded:: 1.8.4

    :Parameters:

        log_level: `str` or `int`, optional
            The new value of the minimal log severity level. This can
            be specified either as a string equal (ignoring case) to
            the named set of log levels or identifier 'DISABLE', or an
            integer code corresponding to each of these, namely:

            * ``'DISABLE'`` (``0``);
            * ``'WARNING'`` (``1``);
            * ``'INFO'`` (``2``);
            * ``'DETAIL'`` (``3``);
            * ``'DEBUG'`` (``-1``).

    :Returns:

        `str`
            The value prior to the change, or the current value if no
            new value was specified (or if one was specified but was
            not valid). Note the string name, rather than the
            equivalent integer, will always be returned.

    **Examples:**

    >>> log_level()  # get the current value
    'WARNING'
    >>> log_level('INFO')  # change the value to 'INFO'
    'WARNING'
    >>> log_level()
    'INFO'
    >>> log_level(0)  # set to 'DISABLE' via corresponding integer
    'INFO'
    >>> log_level()
    'DISABLE'

    '''
    return _log_level(CONSTANTS, log_level)


def LOG_LEVEL(*new_log_level):
    '''Alias for `cfdm.log_level`.
    '''
    return log_level(*new_log_level)


def _is_valid_log_level_int(int_log_level):
    '''Return a Boolean stating if input is a ValidLogLevels Enum integer.'''
    try:
        ValidLogLevels(int_log_level)
    except KeyError:  # if verbose int not in Enum int constants
        return False
    return True


def _reset_log_emergence_level(level, logger=None):
    '''Re-set minimum level for displayed log messages of a logger.

    This may correspond to a change, otherwise will re-set to the same
    value (which is harmless, & as costly as checking to avoid this in
    that case).

    The level specified must be a valid logging level string name or
    equivalent integer (see valid_log_levels in log_level above), else
    a ValueError will be raised by the logging module.

    Unless another logger is specified, this will apply to the root
    logger.

    Important: with an input level of 'DISABLE' (0), this method only
    disables the logging; the responsibility to re-enable it once the
    need for deactivation is over lies with methods that call this.

    '''
    if logger:
        use_logger = logging.getLogger(logger)
    else:  # apply to root, which all other (module) loggers inherit from
        use_logger = logging.getLogger()

    if isinstance(level, int) and _is_valid_log_level_int(level):
        level = ValidLogLevels(level).name  # convert to string ID if valid

    if level == 'DISABLE':
        _disable_logging()
    else:
        # First must (re-)enable in case logging previously was
        # disabled:
        _disable_logging(at_level='NOTSET')
        use_logger.setLevel(getattr(logging, level))


def _disable_logging(at_level=None):
    '''Disable log messages at and below a given level, else completely.

    This is an overriding level for all loggers.

    If *at_level* is not provided, it defaults under the hood to
    ``'CRITICAL'`` (see
    https://docs.python.org/3/library/logging.html#logging.disable),
    the highest level in the Python logging module (that we do not
    expose or use explicitly to tag any messages).

    Note specifying ``'NOTSET'`` as the input will revert any
    disactivation level previously set with this method, so the logger
    regains its original level.

    '''
    if at_level:
        logging.disable(getattr(logging, at_level))
    else:
        # *level* kwarg is required for Python v<=3.6, but defaults to
        # CRITICAL in 3.7 so in future when support only v>=3.7, can remove
        logging.disable(level=logging.CRITICAL)


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
    netCDF4: 1.5.3 /home/user/anaconda3/lib/python3.7/site-packages/netCDF4/__init__.py
    cftime: 1.2.1 /home/user/anaconda3/lib/python3.7/site-packages/cftime/__init__.py
    numpy: 1.16.2 /home/user/anaconda3/lib/python3.7/site-packages/numpy/__init__.py
    cfdm: 1.8.6.0

    >>> environment(paths=False)
    Platform: Linux-4.15.0-72-generic-x86_64-with-debian-stretch-sid
    HDF5 library: 1.10.2
    netcdf library: 4.6.1
    python: 3.7.3
    netCDF4: 1.5.3
    cftime: 1.2.1
    numpy: 1.16.2
    cfdm: 1.8.6.0

    '''
    out = []

    out.append('Platform: ' + str(platform.platform()))
    out.append('HDF5 library: ' + str(netCDF4. __hdf5libversion__))
    out.append('netcdf library: ' + str(netCDF4.__netcdf4libversion__))

    out.append('python: ' + str(platform.python_version()))
    if paths:
        out[-1] += ' ' + str(sys.executable)

    out.append('netCDF4: ' + str(netCDF4.__version__))
    if paths:
        out[-1] += ' ' + str(os.path.abspath(netCDF4.__file__))

    out.append('cftime: ' + str(cftime.__version__))
    if paths:
        out[-1] += ' ' + str(os.path.abspath(cftime.__file__))

    out.append('numpy: ' + str(numpy.__version__))
    if paths:
        out[-1] += ' ' + str(os.path.abspath(numpy.__file__))

    try:
        out.append('netcdf_flattener: ' + str(netcdf_flattener.__version__))
    except AttributeError:
        out.append('netcdf_flattener: unknown version')
    if paths:
        out[-1] += ' ' + str(os.path.abspath(netcdf_flattener.__file__))

    out.append('cfdm: ' + str(__version__))
    if paths:
        out[-1] += ' ' + str(os.path.abspath(__file__))

    if display:
        print('\n'.join(out))  # pragma: no cover
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
