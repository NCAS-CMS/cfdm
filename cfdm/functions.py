import logging
import os
import platform
import sys
import urllib.parse

from copy import deepcopy

from functools import total_ordering

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
    specific functions only if overridden by the corresponding keyword
    argument to that function.

    The value of `None`, either taken by default or supplied as a value,
    will result in the constant in question not being changed from the
    current value. That is, it will have no effect.

    Note that setting a constant using this function is equivalent to setting
    it by means of a specific function of the same name, e.g. via `cfdm.atol`,
    but in this case multiple constants can be set at once.

    .. versionadded:: (cfdm) 1.8.6

    .. seealso:: `atol`, `rtol`, `log_level`

    :Parameters:

        atol: number or `Constant`, optional
            The new value of absolute tolerance. The default is to not
            change the current value.

        rtol: number or `Constant`, optional
            The new value of relative tolerance. The default is to not
            change the current value.

        log_level: `str` or `int` or `Constant`, optional
            The new value of the minimal log severity level. This can
            be specified either as a string equal (ignoring case) to
            the named set of log levels or identifier ``'DISABLE'``,
            or an integer code corresponding to each of these, namely:

            * ``'DISABLE'`` (``0``);
            * ``'WARNING'`` (``1``);
            * ``'INFO'`` (``2``);
            * ``'DETAIL'`` (``3``);
            * ``'DEBUG'`` (``-1``).

    :Returns:

         `Configuration`
            The dictionary-like object containing the names and values
            of the project-wide constants prior to the change, or the
            current names and values if no new values are specified.

    **Examples:**

    View full global configuration of constants:

    >>> cfdm.configuration()
    <Configuration: {'atol': 2.220446049250313e-16,
                     'rtol': 2.220446049250313e-16,
                     'log_level': 'WARNING'}>
    >>> print(cfdm.configuration())
    {'atol': 2.220446049250313e-16,
     'rtol': 2.220446049250313e-16,
     'log_level': 'WARNING'}

    Make a change to one constant and see that it is reflected in the
    configuration:

    >>> cfdm.log_level('DEBUG')
    <Constant: 'WARNING'>
    >>> print(cfdm.configuration())
    {'atol': 2.220446049250313e-16,
     'rtol': 2.220446049250313e-16,
     'log_level': 'DEBUG'}

    Access specific values by key querying, noting the equivalency to
    using its bespoke function:

    >>> cfdm.configuration()['atol']
    2.220446049250313e-16
    >>> cfdm.configuration()['atol'] == cfdm.atol()
    True

    Set multiple constants simultaneously:

    >>> print(cfdm.configuration(atol=5e-14, log_level='INFO'))
    {'atol': 2.220446049250313e-16,
     'rtol': 2.220446049250313e-16,
     'log_level': 'DEBUG'}
    >>> print(cfdm.configuration())
    {'atol': 5e-14, 'rtol': 2.220446049250313e-16, 'log_level': 'INFO'}

    Set a single constant without using its bespoke function:

    >>> print(cfdm.configuration(rtol=1e-17))
    {'atol': 5e-14, 'rtol': 2.220446049250313e-16, 'log_level': 'INFO'}
    >>> cfdm.configuration()
    {'atol': 5e-14, 'rtol': 1e-17, 'log_level': 'INFO'}

    Use as a context manager:

    >>> print(cfdm.configuration())
    {'atol': 2.220446049250313e-16,
     'rtol': 2.220446049250313e-16,
     'log_level': 'WARNING'}
    >>> with cfdm.configuration(atol=9, rtol=10):
    ...     print(cfdm.configuration())
    ...
    {'atol': 9.0, 'rtol': 10.0, 'log_level': 'WARNING'}
    >>> print(cfdm.configuration())
    {'atol': 2.220446049250313e-16,
     'rtol': 2.220446049250313e-16,
     'log_level': 'WARNING'}

    '''
    return _configuration(
        Configuration,
        new_atol=atol,
        new_rtol=rtol,
        new_log_level=log_level
    )


def _configuration(_Configuration, **kwargs):
    '''Internal helper function to provide the logic for `cfdm.configuration`.

    We delegate from the user-facing `cfdm.configuration` for two main reasons:

    1) to avoid a name clash there between the keyword arguments and the
    functions which they each call (e.g. `atol` and `cfdm.atol`) which
    would otherwise necessitate aliasing every such function name; and

    2) because the user-facing function must have the appropriate keywords
    explicitly listed, but the very similar logic applied for each keyword
    can be consolidated by iterating over the full dictionary of input kwargs.

    :Parameters:

        _Configuration: class
            The `Configuration` class to be returned.

    :Returns:

        `Configuration`
            The names and values of the project-wide constants prior
            to the change, or the current names and values if no new
            values are specified.

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

    return _Configuration(**old)


def atol(*arg):
    '''The tolerance on absolute differences when testing for numerically
    tolerant equality.

    Two real numbers ``x`` and ``y`` are considered equal if
    ``abs(x-y) <= atol + rtol*abs(y)``, where ``atol`` (the tolerance
    on absolute differences) and ``rtol`` (the tolerance on relative
    differences) are positive, typically very small numbers. By
    default both are set to the system epsilon (the difference between
    1 and the least value greater than 1 that is representable as a
    float).

    .. versionadded:: (cfdm) 1.7.0

    .. seealso:: `rtol`, `configuration`

    :Parameters:

        atol: `float` or `Constant`, optional
            The new value of absolute tolerance. The default is to not
            change the current value.

    :Returns:

        `Constant`
            The value prior to the change, or the current value if no
            new value was specified.

    **Examples:**

    >>> cfdm.atol()
    <Constant: 2.220446049250313e-16>
    >>> print(cfdm.atol())
    2.220446049250313e-16
    >>> str(cfdm.atol())
    '2.220446049250313e-16'
    >>> cfdm.atol().value
    2.220446049250313e-16
    >>> float(cfdm.atol())
    2.220446049250313e-16

    >>> old = cfdm.atol(1e-10)
    >>> cfdm.atol()
    <Constant: 2.220446049250313e-16>
    >>> cfdm.atol(old)
    <Constant: 1e-10>
    >>> cfdm.atol()
    <Constant: 2.220446049250313e-16>

    Use as a context manager:

    >>> print(cfdm.atol())
    2.220446049250313e-16
     >>> with cfdm.atol(1e-5):
    ...     print(cfdm.atol(), cfdm.atol(2e-30), cfdm.atol())
    ...
    1e-05 1e-05 2e-30
    >>> print(cfdm.atol())
    2.220446049250313e-16

    '''
    old = CONSTANTS['ATOL']
    if arg:
        arg = arg[0]
        try:
            # Check for Constants instance
            arg = arg.value
        except AttributeError:
            pass

        CONSTANTS['ATOL'] = float(arg)

    return Constant(old, _func=atol)


def ATOL(*new_atol):
    '''Alias for `cfdm.atol`.

    '''
    return atol(*new_atol)


def rtol(*arg):
    '''The tolerance on relative differences when testing for numerically
    tolerant equality.

    Two real numbers ``x`` and ``y`` are considered equal if
    ``abs(x-y) <= atol + rtol*abs(y)``, where ``atol`` (the tolerance
    on absolute differences) and ``rtol`` (the tolerance on relative
    differences) are positive, typically very small numbers. By
    default both are set to the system epsilon (the difference between
    1 and the least value greater than 1 that is representable as a
    float).

    .. versionadded:: (cfdm) 1.7.0

    .. seealso:: `atol`, `configuration`

    :Parameters:

        rtol: `float` or `Constant`, optional
            The new value of relative tolerance. The default is to not
            change the current value.

    :Returns:

        `Constant`
            The value prior to the change, or the current value if no
            new value was specified.

    **Examples:**

    >>> cfdm.rtol()
    <Constant: 2.220446049250313e-16>
    >>> print(cfdm.rtol())
    2.220446049250313e-16
    >>> str(cfdm.rtol())
    '2.220446049250313e-16'
    >>> cfdm.rtol().value
    2.220446049250313e-16
    >>> float(cfdm.rtol())
    2.220446049250313e-16

    >>> old = cfdm.rtol(1e-10)
    >>> cfdm.rtol()
    <Constant: 2.220446049250313e-16>
    >>> cfdm.rtol(old)
    <Constant: 1e-10>
    >>> cfdm.rtol()
    <Constant: 2.220446049250313e-16>

    Use as a context manager:

    >>> print(cfdm.rtol())
    2.220446049250313e-16
    >>> with cfdm.rtol(1e-5):
    ...     print(cfdm.rtol(), cfdm.rtol(2e-30), cfdm.rtol())
    ...
    1e-05 1e-05 2e-30
    >>> print(cfdm.rtol())
    2.220446049250313e-16

    '''
    old = CONSTANTS['RTOL']
    if arg:
        arg = arg[0]
        try:
            # Check for Constants instance
            arg = arg.value
        except AttributeError:
            pass

        CONSTANTS['RTOL'] = float(arg)

    return Constant(old, _func=rtol)


def RTOL(*new_rtol):
    '''Alias for `cfdm.rtol`.

    '''
    return rtol(*new_rtol)


def _log_level(constants_dict, arg, _Constant, _func):
    '''Equivalent to log_level, but with dict to modify as an argument.

    This internal function is designed specifically so that a
    different constants_dict can be manipulated with setting or
    reading of the log level, without the constants dictionary
    becoming a user-facing argument. log_level is the only function of
    the pair documented for use.

    Overall, this means that cf-python can import these functions and
    use them such that it can manipulate (its own separate) log_level
    constant.

    Note: relies on the mutability of arguments (here the
    constants_dict).

    :Parameters:

        constants_dict: `dict`

        arg: `tuple`

        _Constant: class
            The `Constant` class to be returned.

        _func: function
            The callback function for setting the log level.

    :Returns:

        `Constant`

    '''
    old = constants_dict['LOG_LEVEL']

    if arg:
        level = arg[0]
        try:
            # Check for Constant instance
            level = level.value
        except AttributeError:
            pass

        # Ensuring it is a valid level specifier to set & use, either
        # a case-insensitive string of valid log level or
        # dis/en-abler, or an integer 0 to 5 corresponding to one of
        # those as converted above:
        ok = True
        if isinstance(level, str):
            level = level.upper()
        elif _is_valid_log_level_int(level):
            level = ValidLogLevels(level).name  # convert to string ID first
        else:
            ok = False

        if not ok or not hasattr(ValidLogLevels, level):
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

    return _Constant(old, _func=_func)


def log_level(*arg):
    '''The minimal level of seriousness of log messages which are shown.

    This can be adjusted to filter out potentially-useful log messages
    generated by cfdm at runtime, such that any messages marked as
    having a severity below the level set will not be reported.

    For example, when set to ``'WARNING'`` (or equivalently ``1``),
    all messages categorised as ``'DEBUG'`` or ``'INFO'`` will be
    suppressed, and only warnings will emerge.

    See https://ncas-cms.github.io/cfdm/tutorial.html#logging for a
    detailed breakdown on the levels and configuration possibilities.

    The default level is ``'WARNING'`` (``1``).

    .. versionadded:: (cfdm) 1.8.4

    .. seealso:: `configuration`

    :Parameters:

         arg: `str` or `int` or `Constant`, optional
            The new value of the minimal log severity level. This can
            be specified either as a string equal (ignoring case) to
            the named set of log levels or identifier ``'DISABLE'``,
            or an integer code corresponding to each of these, namely:

            * ``'DISABLE'`` (``0``);
            * ``'WARNING'`` (``1``);
            * ``'INFO'`` (``2``);
            * ``'DETAIL'`` (``3``);
            * ``'DEBUG'`` (``-1``).

    :Returns:

        `Constant`
            The value prior to the change, or the current value if no
            new value was specified (or if one was specified but was
            not valid). Note the string name, rather than the
            equivalent integer, will always be returned.

    **Examples:**

    >>> cfdm.log_level()
    <Constant: 'WARNING'>
    >>> print(cfdm.log_level())
    WARNING
    >>> str(cfdm.log_level())
    'WARNING'

    >>> old = log_level('INFO')
    >>> cfdm.log_level()
    <Constant: 'WARNING'>
    >>> cfdm.log_level(old)
    <Constant: 'INFO'>
    >>> cfdm.log_level()
    <Constant: 'WARNING'>

    Use as a context manager:

    >>> print(cfdm.log_level())
    WARNING
    >>> with cfdm.log_level('DETAIL'):
    ...     print(cfdm.log_level(), cfdm.log_level(-1), cfdm.log_level())
    ...
    DETAIL DETAIL DEBUG
    >>> print(cfdm.log_level())
    WARNING

    '''
    return _log_level(CONSTANTS, arg, Constant, log_level)


def LOG_LEVEL(*new_log_level):
    '''Alias for `cfdm.log_level`.

    '''
    return log_level(*new_log_level)


def _is_valid_log_level_int(int_log_level):
    '''Return a Boolean stating if input is a ValidLogLevels Enum integer.

    '''
    try:
        ValidLogLevels(int_log_level)
    except ValueError:  # if verbose int not in Enum int constants
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
    try:
        # Check for Constants instance
        level = level.value
    except AttributeError:
        pass

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
        # CRITICAL in 3.7 so in future when support only v>=3.7, can
        # remove
        logging.disable(level=logging.CRITICAL)


def environment(display=True, paths=True):
    '''Return the names, versions and paths of all dependencies.

    .. versionadded:: (cfdm) 1.7.0

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

    >>> cfdm.environment()
    Platform: Linux-4.15.0-72-generic-x86_64-with-debian-stretch-sid
    HDF5 library: 1.10.2
    netcdf library: 4.6.1
    python: 3.7.3 /home/user/anaconda3/bin/python
    netCDF4: 1.5.3 /home/user/anaconda3/lib/python3.7/site-packages/netCDF4/__init__.py
    cftime: 1.2.1 /home/user/anaconda3/lib/python3.7/site-packages/cftime/__init__.py
    numpy: 1.16.2 /home/user/anaconda3/lib/python3.7/site-packages/numpy/__init__.py
    cfdm: 1.8.8.0

    >>> cfdm.environment(paths=False)
    Platform: Linux-4.15.0-72-generic-x86_64-with-debian-stretch-sid
    HDF5 library: 1.10.2
    netcdf library: 4.6.1
    python: 3.7.3
    netCDF4: 1.5.3
    cftime: 1.2.1
    numpy: 1.16.2
    cfdm: 1.8.8.0

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

    out.append('netcdf_flattener: ' + str(netcdf_flattener.__version__))
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

    .. versionadded:: (cfdm) 1.7.0

    :Returns:

        `str`
            The version of the CF conventions represented by this
            release of the cfdm package.

    **Examples:**

    >>> CF()
    '1.9'

    '''
    return __cf_version__


def abspath(filename):
    '''Return a normalised absolute version of a file name.

    If a string containing URL is provided then it is returned
    unchanged.

    .. versionadded:: (cfdm) 1.7.0

    :Parameters:

        filename: `str`
            The name of the file.

    :Returns:

        `str`
            The normalized absolutised version of *filename*.

    **Examples:**

    >>> import os
    >>> os.getcwd()
    '/data/archive'
    >>> cfdm.abspath('file.nc')
    '/data/archive/file.nc'
    >>> cfdm.abspath('..//archive///file.nc')
    '/data/archive/file.nc'
    >>> cfdm.abspath('http://data/archive/file.nc')
    'http://data/archive/file.nc'

    '''
    u = urllib.parse.urlparse(filename)
    if u.scheme != '':
        return filename

    return os.path.abspath(filename)


def unique_constructs(constructs, copy=True):
    '''Return the unique constructs from a sequence.

    .. versionadded:: (cfdm) 1.9.0.0

    :Parameters:

        constructs: sequence of constructs
            The constructs to be compared. The constructs may comprise
            a mixture of types. The sequence can be empty.

        copy: `bool`, optional
            If False then do not copy returned constructs. By default
            they are deep copies.

    :Returns:

        `list`
            The unique constructs. May be an empty list.

    **Examples:**

    >>> f = cfdm.example_field(0)
    >>> g = cfdm.example_field(1)
    >>> f
    <Field: specific_humidity(latitude(5), longitude(8)) 1>
    >>> g
    <Field: air_temperature(atmosphere_hybrid_height_coordinate(1), grid_latitude(10), grid_longitude(9)) K>

    >>> fields = [f, f, g]
    >>> cfdm.unique_constructs(fields)
    [<Field: specific_humidity(latitude(5), longitude(8)) 1>,
     <Field: air_temperature(atmosphere_hybrid_height_coordinate(1), grid_latitude(10), grid_longitude(9)) K>]

    >>> domains = [x.domain for x in fields]
    >>> cfdm.unique_constructs(domains)
    [<Domain: {latitude(5), longitude(8), time(1)}>,
     <Domain: {atmosphere_hybrid_height_coordinate(1), grid_latitude(10), grid_longitude(9), time(1)}>]

    >>> cfdm.unique_constructs(domains + fields + [f.domain])
    [<Domain: {latitude(5), longitude(8), time(1)}>,
     <Domain: {atmosphere_hybrid_height_coordinate(1), grid_latitude(10), grid_longitude(9), time(1)}>,
     <Field: specific_humidity(latitude(5), longitude(8)) 1>,
     <Field: air_temperature(atmosphere_hybrid_height_coordinate(1), grid_latitude(10), grid_longitude(9)) K>]

    >>> cfdm.unique_constructs(x for x in fields)
    [<Field: specific_humidity(latitude(5), longitude(8)) 1>,
     <Field: air_temperature(atmosphere_hybrid_height_coordinate(1), grid_latitude(10), grid_longitude(9)) K>]

    '''
    if not constructs:
        # constructs is an empty sequence
        return []

    try:
        # constructs is a sequence?
        construct0 = constructs[0]
        constructs = (c for c in constructs[1:])
    except TypeError:
        try:
            # constructs is a generator?
            construct0 = next(constructs)
        except StopIteration:
            # constructs is an empty generator
            return []
    # --- End: try

    if copy:
        construct0 = construct0.copy()

    out = [construct0]

    for construct in constructs:
        is_equal = False
        for c in out:
            if construct.equals(c, verbose='DISABLE'):
                is_equal = True
                break
        # --- End: for

        if not is_equal:
            if copy:
                construct = construct.copy()

            out.append(construct)
    # --- End: for

    return out


@total_ordering
class Constant:
    '''A container for a constant with context manager support.

    The constant value is accessed via the `value` attribute:

       >>> c = cfdm.Constant(1.9)
       >>> c.value
       1.9

    Conversion to `int`, `float` and `str` is with the usual built-in
    functions:

       >>> c = cfdm.Constant(1.9)
       >>> int(c)
       1
       >>> float(c)
       1.9
       >>> str(c)
       '1.9'

    Augmented arithmetic assignments (``+=``, ``-=``, ``*=``, ``/=``,
    ``//=``) update `Constant` objects in-place:

       >>> c = cfdm.Constant(20)
       >>> c.value
       20
       >>> c /= 2
       >>> c
       <Constant: 10.0>
       >>> c += c
       <Constant: 20.0>

       >>> c = cfdm.Constant('New_')
       >>> c *= 2
       <Constant: 'New_New_'>

    Binary arithmetic operations (``+``, ``-``, ``*``, ``/``, ``//``)
    are equivalent to the operation acting on the `Constant` object's
    `value` attribute:

       >>> c = cfdm.Constant(20)
       >>> c.value
       20
       >>> c * c
       400
       >>> c * 3
       60
       >>> 2 - c
       -38

       >>> c = cfdm.Constant('New_')
       >>> c * 2
       'New_New_'

    Care is required when the right hand side operand is a `numpy`
    array

       >>> import numpy
       >>> c * numpy.array([1, 2, 3])
       array([20, 40, 60])
       >>> d = numpy.array([1, 2, 3]) * c
       >>> d
       array([10, 20, 30], dtype=object)
       >>> type(d[0])
       int

    Unary arithmetic operations (``+``, ``-``, `abs`) are equivalent
    to the operation acting on the `Constant` object's `value`
    attribute:

       >>> c = cfdm.Constant(-20)
       >>> c.value
       -20
       >>> -c
       20
       >>> abs(c)
       20
       >>> +c
       -20

    Rich comparison operations are equivalent to the operation acting
    on the `Constant` object's `value` attribute:

       >>> c = cfdm.Constant(20)
       >>> d = cfdm.Constant(1)
       >>> c.value
       20
       >>> d.value
       1
       >>> d < c
       True
       >>> c != 20
       False
       >>> 20 == c
       True

       >>> c = cfdm.Constant('new')
       >>> d = cfdm.Constant('old')
       >>> c == d
       False
       >>> c == 'new'
       True
       >>> c != 3
       True
       >>> 3 == c
       False

       >>> import numpy
       >>> c = cfdm.Constant(20)
       >>> c < numpy.array([10, 20, 30])
       array([False, False,  True])
       >>> numpy.array([10, 20, 30]) >= c
       array([False,  True,  True])

    `Constant` instances are hashable.

    **Context manager**

    The `Constant` instance can be used as a context manager that upon
    exit executes the function defined by the `_func` attribute, with
    the `value` attribute as an argument. For example, the `Constant`
    instance ``c`` would execute ``c._func(c.value)`` upon exit.

    .. versionadded:: (cfdm) 1.8.8.0

    '''
    __slots__ = ('_func',  'value', '_type')

    def __init__(self, value, _func=None):
        '''**Initialization**

    :Parameters:

        value:
            A value for the constant.

        _func: function, optional
            A function that that is executed upon exit from a context
            manager, that takes the *value* parameter as its argument.

        '''
        self.value = value
        self._func = _func

    def __enter__(self):
        '''Enter the runtime context.

        '''
        if getattr(self, '_func', None) is None:
            raise AttributeError(
                "Can't use {!r} as a context manager because the '_func' "
                "attribute is not defined".format(self))

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        '''Exit the runtime context.

        '''
        self._func(self.value)

    def __deepcopy__(self, memo):
        '''Called by the `copy.deepcopy` function.

    x.__deepcopy__() <==> copy.deepcopy(x)

        '''
        return self.copy()

    def __float__(self):
        return float(self.value)

    def __int__(self):
        return int(self.value)

    def __eq__(self, other):
        return self.value == other

    def __lt__(self, other):
        return self.value < other

    def __abs__(self):
        return abs(self.value)

    def __neg__(self):
        return -self.value

    def __pos__(self):
        return self.value

    def __iadd__(self, other):
        self.value += other
        return self

    def __ifloordiv__(self, other):
        self.value //= other
        return self

    def __imul__(self, other):
        self.value *= other
        return self

    def __isub__(self, other):
        self.value -= other
        return self

    def __itruediv__(self, other):
        self.value /= other
        return self

    def __add__(self, other):
        return self.value + other

    def __floordiv__(self, other):
        return self.value // other

    def __mul__(self, other):
        return self.value * other

    def __sub__(self, other):
        return self.value - other

    def __truediv__(self, other):
        return self.value / other

    def __radd__(self, other):
        return other + self.value

    def __rfloordiv__(self, other):
        return other // self.value

    def __rmul__(self, other):
        return other * self.value

    def __rsub__(self, other):
        return other - self.value

    def __rtruediv__(self, other):
        return other / self.value

    def __hash__(self):
        return hash((self.value, getattr(self, '_func', None)))

    def __repr__(self):
        '''Called by the `repr` built-in function.

        '''
        return "<{0}: {1!r}>".format(
            self.__class__.__name__, self.value
        )

    def __str__(self):
        '''Called by the `str` built-in function.

        '''
        return str(self.value)

    # ----------------------------------------------------------------
    # Methods
    # ----------------------------------------------------------------
    def copy(self):
        '''Return a deep copy.

    ``c.copy()`` is equivalent to ``copy.deepcopy(c)``.

    .. versionadded:: (cfdm) 1.8.8.0

    :Returns:

        `Constant`
            The deep copy.

        '''
        out = type(self)(value=deepcopy(self.value),
                         _func=getattr(self, '_func', None))

        if not hasattr(self, '_func'):
            del out._func

        return out


class Configuration(dict):
    '''A dictionary-like container for the global constants with context
    manager support.

    Initialization is as for a `dict`, and all of the `dict` methods
    are available with the same behaviours (`clear`, `copy`,
    `fromkeys`, `get`, `items`, `keys`, `pop`, `popitem`,
    `setdefault`, `update`, `values`):

       >>> c = cfdm.Configuration(atol=0.1, rtol=0.2, log_level='INFO')
       >>> c
       <Configuration: {'atol': 0.1, 'rtol': 0.2, 'log_level': 'INFO'}>
       >>> print(c)
       {'atol': 0.1, 'rtol': 0.2, 'log_level': 'INFO'}
       >>> c.pop('atol')
       0.1
       >>> c
       <Configuration: {'rtol': 0.2, 'log_level': 'INFO'}>
       >>> c.clear()
       >>> c
       <Configuration: {}>

    .. versionadded:: (cfdm) 1.8.8.0

    '''
    __slots__ = ('_func',)

    def __new__(cls, *args, **kwargs):
        '''Must override this method in subclasses.

        '''
        instance = super().__new__(cls)
        instance._func = configuration
        return instance

    def __enter__(self):
        '''Enter the runtime context.

        '''
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        '''Exit the runtime context.

        '''
        self._func(**self)

    def __repr__(self):
        '''Called by the `repr` built-in function.

        '''
        return "<{0}: {1}>".format(
            self.__class__.__name__, super().__repr__()
        )

    def __str__(self):
        return super().__repr__()
