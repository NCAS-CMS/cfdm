import logging
import os
from copy import deepcopy
from functools import total_ordering
from math import isnan
from numbers import Integral
from os import sep as os_sep
from os.path import abspath as os_abspath
from os.path import dirname as os_dirname
from os.path import join

import numpy as np
from dask import config as _config
from dask.base import is_dask_collection
from dask.utils import parse_bytes
from uritools import uricompose, urisplit

from . import __cf_version__, __file__, __version__, core
from .constants import CONSTANTS, ValidLogLevels
from .core import DocstringRewriteMeta
from .core.docstring import (
    _docstring_substitution_definitions as _core_docstring_substitution_definitions,
)
from .docstring import _docstring_substitution_definitions

# --------------------------------------------------------------------
# Merge core and non-core docstring substitution dictionaries without
# overwriting either of them (in the absence of a dictionary union
# operator).
# --------------------------------------------------------------------
_subs = _docstring_substitution_definitions.copy()
_subs.update(_core_docstring_substitution_definitions)
_docstring_substitution_definitions = _subs
del _subs


class DeprecationError(Exception):
    pass


def configuration(
    atol=None,
    rtol=None,
    log_level=None,
    chunksize=None,
):
    """Views and sets constants in the project-wide configuration.

    The full list of global constants that are provided in a
    dictionary to view, and can be set in any combination, are:

    * `atol`
    * `rtol`
    * `log_level`
    * `chunksize`

    These are all constants that apply throughout `cfdm`, except for
    in specific functions only if overridden by the corresponding
    keyword argument to that function.

    The value of `None`, either taken by default or supplied as a
    value, will result in the constant in question not being changed
    from the current value. That is, it will have no effect.

    Note that setting a constant using this function is equivalent to
    setting it by means of a specific function of the same name,
    e.g. via `cfdm.atol`, but in this case multiple constants can be
    set at once.

    .. versionadded:: (cfdm) 1.8.6

    .. seealso:: `atol`, `rtol`, `log_level`, `chunksize`

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

        chunksize: `float` or `Constant`, optional
            The new chunksize in bytes. The default is to not change
            the current behaviour.

            .. versionadded:: (cfdm) 1.11.2.0

    :Returns:

        `Configuration`
            The dictionary-like object containing the names and values
            of the project-wide constants prior to the change, or the
            current names and values if no new values are specified.

    **Examples**

    View full global configuration of constants:

    >>> cfdm.configuration()
    <{{repr}}Configuration: {'atol': 2.220446049250313e-16,
                     'rtol': 2.220446049250313e-16,
                     'log_level': 'WARNING',
                     'chunksize': 134217728}>
    >>> print(cfdm.configuration())
    {'atol': 2.220446049250313e-16,
     'rtol': 2.220446049250313e-16,
     'log_level': 'WARNING',
     'chunksize': 134217728}

    Make a change to one constant and see that it is reflected in the
    configuration:

    >>> cfdm.log_level('DEBUG')
    <{{repr}}Constant: 'WARNING'>
    >>> print(cfdm.configuration())
    {'atol': 2.220446049250313e-16,
     'rtol': 2.220446049250313e-16,
     'log_level': 'DEBUG',
     'chunksize': 134217728}

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
     'log_level': 'DEBUG',
     'chunksize': 134217728}
    >>> print(cfdm.configuration())
    {'atol': 5e-14,
     'rtol': 2.220446049250313e-16,
     'log_level': 'INFO',
     'chunksize': 134217728}

    Set a single constant without using its bespoke function:

    >>> print(cfdm.configuration(rtol=1e-17))
    {'atol': 5e-14,
     'rtol': 2.220446049250313e-16,
     'log_level': 'INFO',
     'chunksize': 134217728}
    >>> cfdm.configuration()
    {'atol': 5e-14,
     'rtol': 1e-17,
     'log_level': 'INFO',
     'chunksize': 134217728}

    Use as a context manager:

    >>> print(cfdm.configuration())
    {'atol': 2.220446049250313e-16,
     'rtol': 2.220446049250313e-16,
     'log_level': 'WARNING',
     'chunksize': 134217728}
    >>> with cfdm.configuration(atol=9, rtol=10):
    ...     print(cfdm.configuration())
    ...
    {'atol': 9.0, 'rtol': 10.0, 'log_level': 'WARNING'}
    >>> print(cfdm.configuration())
    {'atol': 2.220446049250313e-16,
     'rtol': 2.220446049250313e-16,
     'log_level': 'WARNING',
     'chunksize': 134217728}

    """
    return _configuration(
        Configuration,
        new_atol=atol,
        new_rtol=rtol,
        new_log_level=log_level,
        new_chunksize=chunksize,
    )


def _configuration(_Configuration, **kwargs):
    """Internal helper function with logic for `cfdm.configuration`.

    We delegate from the user-facing `cfdm.configuration` for two main
    reasons:

    1) to avoid a name clash there between the keyword arguments and
       the functions which they each call (e.g. `atol` and
       `cfdm.atol`) which would otherwise necessitate aliasing every
       such function name; and

    2) because the user-facing function must have the keywords
       explicitly listed, but the very similar logic applied for each
       keyword can be consolidated by iterating over the full
       dictionary of input kwargs.

    :Parameters:

        _Configuration: class
            The `Configuration` class to be returned.

    :Returns:

        `Configuration`
            The names and values of the project-wide constants prior
            to the change, or the current names and values if no new
            values are specified.

    """
    old = {name.lower(): val for name, val in CONSTANTS.items()}

    # Filter out 'None' kwargs from configuration() defaults. Note that this
    # does not filter out '0' or 'True' values, which is important as the user
    # might be trying to set those, as opposed to None emerging as default.
    kwargs = {name: val for name, val in kwargs.items() if val is not None}

    # Note values are the functions not the keyword arguments of same name:
    reset_mapping = {
        "new_atol": atol,
        "new_rtol": rtol,
        "new_log_level": log_level,
        "new_chunksize": chunksize,
    }

    old_values = {}

    try:
        # Run the corresponding func for all input kwargs
        for setting_alias, new_value in kwargs.items():
            reset_mapping[setting_alias](new_value)
            setting = setting_alias.replace("new_", "", 1)
            old_values[setting_alias] = old[setting]
    except ValueError:
        # Reset any constants that were changed prior to the exception
        for setting_alias, old_value in old_values.items():
            reset_mapping[setting_alias](old_value)

        # Raise the exception
        raise

    return _Configuration(**old)


def LOG_LEVEL(*new_log_level):
    """Alias for `cfdm.log_level`."""
    return log_level(*new_log_level)


def _is_valid_log_level_int(int_log_level):
    """True if the input is a ValidLogLevels Enum integer."""
    try:
        ValidLogLevels(int_log_level)
    except KeyError:  # if verbose int not in Enum int constants
        return False

    return True


def _reset_log_emergence_level(level, logger=None):
    """Re-set minimum level for displayed log messages of a logger.

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

    """
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

    if level == "DISABLE":
        _disable_logging()
    else:
        # First must (re-)enable in case logging previously was
        # disabled:
        _disable_logging(at_level="NOTSET")
        use_logger.setLevel(getattr(logging, level))


def _disable_logging(at_level=None):
    """Disable log messages at and below a given level, else completely.

    This is an overriding level for all loggers.

    If *at_level* is not provided, it defaults under the hood to
    ``'CRITICAL'`` (see
    https://docs.python.org/3/library/logging.html#logging.disable),
    the highest level in the Python logging module (that we do not
    expose or use explicitly to tag any messages).

    Note specifying ``'NOTSET'`` as the input will revert any
    disactivation level previously set with this method, so the logger
    regains its original level.

    """
    if at_level:
        logging.disable(getattr(logging, at_level))
    else:
        logging.disable()


def _get_module_info(module, alternative_name=False, try_except=False):
    """Helper function for processing modules for `environment`.

    .. versionadded:: (cfdm) 1.12.2.0

    """
    import importlib

    if try_except:
        module_name = None
        try:
            importlib.import_module(module)
            module_name = module
        except ImportError:
            if (
                alternative_name
            ):  # where a module has a different (e.g. old) name
                try:
                    importlib.import_module(alternative_name)
                    module_name = alternative_name
                except ImportError:
                    pass

        if not module_name:
            return ("not available", "")
    else:
        module_name = module

    return (
        importlib.import_module(module_name).__version__,
        importlib.util.find_spec(module_name).origin,
    )


def environment(display=True, paths=True):
    """Return the names, versions and paths of all dependencies.

    .. versionadded:: (cfdm) 1.7.0

    :Parameters:

        display: `bool`, optional
            If False then return the description of the environment as
            a string. By default the description is printed.

        paths: `bool`, optional
            If True (the default) then output the locations of each
            package.

    :Returns:

        `None` or `list`
            If *display* is True then the description of the
            environment is printed and `None` is returned. Otherwise
            the description is returned as in a `list`.

    **Examples**

    >>> cfdm.environment()
    Platform: Linux-6.8.0-60-generic-x86_64-with-glibc2.39
    Python: 3.12.8 /home/miniconda3/bin/python
    packaging: 24.2 /home/miniconda3/lib/python3.12/site-packages/packaging/__init__.py
    numpy: 2.2.6 /home/miniconda3/lib/python3.12/site-packages/numpy/__init__.py
    cfdm.core: 1.12.2.0 /home/miniconda3/lib/python3.12/site-packages/cfdm/cfdm/core/__init__.py
    udunits2 library: libudunits2.so.0
    HDF5 library: 1.14.2
    netcdf library: 4.9.4-development
    netCDF4: 1.7.2 /home/miniconda3/lib/python3.12/site-packages/netCDF4/__init__.py
    h5netcdf: 1.3.0 /home/miniconda3/lib/python3.12/site-packages/h5netcdf/__init__.py
    h5py: 3.12.1 /home/miniconda3/lib/python3.12/site-packages/h5py/__init__.py
    zarr: 3.0.8 /home/miniconda3/lib/python3.12/site-packages/zarr/__init__.py
    s3fs: 2024.12.0 /home/miniconda3/lib/python3.12/site-packages/s3fs/__init__.py
    scipy: 1.15.1 /home/miniconda3/lib/python3.12/site-packages/scipy/__init__.py
    dask: 2025.5.1 /home/miniconda3/lib/python3.12/site-packages/dask/__init__.py
    cftime: 1.6.4.post1 /home/miniconda3/lib/python3.12/site-packages/cftime/__init__.py
    cfunits: 3.3.7 /home/miniconda3/lib/python3.12/site-packages/cfunits/__init__.py
    cfdm: 1.12.2.0 /home/miniconda3/lib/python3.12/site-packages/cfdm/cfdm/__init__.py

    >>> cfdm.environment(paths=False)
    Platform: Linux-6.8.0-60-generic-x86_64-with-glibc2.39
    Python: 3.12.8
    packaging: 24.2
    numpy: 2.2.6
    cfdm.core: 1.12.2.0
    udunits2 library: libudunits2.so.0
    HDF5 library: 1.14.2
    netcdf library: 4.9.4-development
    netCDF4: 1.7.2
    h5netcdf: 1.3.0
    h5py: 3.12.1
    zarr: 3.0.8
    s3fs: 2024.12.0
    scipy: 1.15.1
    dask: 2025.5.1
    distributed: 2025.5.1
    cftime: 1.6.4.post1
    cfunits: 3.3.7
    cfdm: 1.12.2.0

    """
    import ctypes

    import netCDF4

    # Get cfdm.core env
    out = core.environment(display=False, paths=paths)

    dependency_version_paths_mapping = {
        "udunits2 library": (ctypes.util.find_library("udunits2"), ""),
        "HDF5 library": (netCDF4.__hdf5libversion__, ""),
        "netcdf library": (netCDF4.__netcdf4libversion__, ""),
        "netCDF4": _get_module_info("netCDF4"),
        "h5netcdf": _get_module_info("h5netcdf"),
        "h5py": _get_module_info("h5py"),
        "zarr": _get_module_info("zarr"),
        "s3fs": _get_module_info("s3fs"),
        "scipy": _get_module_info("scipy"),
        "dask": _get_module_info("dask"),
        "distributed": _get_module_info("distributed"),
        "cftime": _get_module_info("cftime"),
        "cfunits": _get_module_info("cfunits"),
        "cfdm": (__version__, os.path.abspath(__file__)),
    }
    string = "{0}: {1!s}"
    if paths:
        # Include path information, else exclude, when unpacking tuple.
        string += " {2!s}"

    out.extend(
        [
            string.format(dep, *info)
            for dep, info in dependency_version_paths_mapping.items()
        ]
    )

    if display:
        print("\n".join(out))  # pragma: no cover
    else:
        return out


def CF():
    """The version of the CF conventions.

    This indicates which version of the CF conventions are represented
    by this release of the cfdm package, and therefore the version can
    not be changed.

    .. versionadded:: (cfdm) 1.7.0

    :Returns:

        `str`
            The version of the CF conventions represented by this
            release of the cfdm package.

    **Examples**

    >>> CF()
    '1.12'

    """
    return __cf_version__


def abspath(path, uri=None):
    """Return a normalised absolute version of a path.

    .. versionadded:: (cfdm) 1.7.0

    :Parameters:

        path: `str`
            The file or directory path.

        uri: `None` or `bool`, optional
            If True then the returned path will begin with a URI
            scheme component followed by a ``:`` character, such as
            ``file://data/file.nc``, ``https://remote/data/file.nc``,
            etc.). If False then the returned path will not begin with
            a URI scheme component only if the input *path* does. If
            `None` (the default) then the returned path will begin
            with a URI scheme component if the input *path* does.

            .. versionadded:: (cfdm) 1.12.0.0

    :Returns:

        `str`
            The normalised absolutised version of the path.

    **Examples**

    >>> import os
    >>> os.getcwd()
    '/data/archive'

    >>> cfdm.abspath("")
    '/data/archive'
    >>> cfdm.abspath("file.nc")
    '/data/archive/file.nc'
    >>> cfdm.abspath("../file.nc")
    '/data/file.nc'
    >>> cfdm.abspath("file:///file.nc")
    'file:///file.nc'
    >>> cfdm.abspath("file://file.nc")
    'file://file.nc/data/archive'
    >>> cfdm.abspath("file:/file.nc")
    'file:/file.nc'
    >>> cfdm.abspath("http:///file.nc")
    'http:///file.nc'
    >>> cfdm.abspath("http://file.nc")
    'http://file.nc'
    >>> cfdm.abspath("http:/file.nc")
    'http:/file.nc'

    >>> cfdm.abspath("file.nc", uri=True)
    'file:/data/archive/file.nc'
    >>> cfdm.abspath("../file.nc", uri=True)
    'file:/data/file.nc'
    >>> cfdm.abspath("file:///file.nc", uri=True)
    'file:///file.nc'
    >>> cfdm.abspath("file://file.nc", uri=True)
    'file://file.nc/data/archive'
    >>> cfdm.abspath("file:/file.nc", uri=True)
    'file:/file.nc'
    >>> cfdm.abspath("http:///file.nc", uri=True)
    'http:///file.nc'
    >>> cfdm.abspath("http://file.nc", uri=True)
    'http://file.nc'
    >>> cfdm.abspath("http:/file.nc", uri=True)
    'http:/file.nc'

    >>> cfdm.abspath("file.nc", uri=False)
    '/data/archive/file.nc'
    >>> cfdm.abspath("../file.nc", uri=False)
    '/data/file.nc'
    >>> cfdm.abspath("file:///file.nc", uri=False)
    '/file.nc'
    >>> cfdm.abspath("file://file.nc", uri=False)
    '/data/archive'
    >>> cfdm.abspath("file:/file.nc", uri=False)
    '/file.nc'
     >>> cfdm.abspath("http:///file.nc", uri=False)
    ValueError: Can't set uri=False for path='http:///file.nc'

    """
    u = urisplit(path)
    scheme = u.scheme
    path = u.path

    if scheme:
        # Remote or "file"
        if scheme == "file" or path.startswith(os_sep):
            path = os_abspath(path)

        if uri or uri is None:
            path = uricompose(scheme=scheme, authority=u.authority, path=path)
        elif scheme != "file":
            raise ValueError(f"Can't set uri=False for path={u.geturi()!r}")

    else:
        # Local
        path = os_abspath(path)
        if uri:
            path = uricompose(scheme="file", authority=u.authority, path=path)

    fragment = u.fragment
    if fragment is not None:
        # Append a URI fragment. Do this with a string-append, rather
        # than via `uricompose` in case the fragment contains more
        # than one # character.
        path += f"#{fragment}"

    return path


def dirname(path, normalise=False, uri=None, isdir=False, sep=False):
    """Return the directory of a path.

    .. versionadded:: (cfdm) 1.12.0.0

    :Parameters:

        path: `str`
            The name of the path.

        normalise: `bool`, optional
            If True then normalise the path by resolving it to an
            absolute path. If False (the default) then no
            normalisation is done.

        uri: `None` or `bool`, optional
            If True then the returned directory will begin with a URI
            scheme component followed by a ``:`` character, such as
            ``file://data/file.nc``, ``https://remote/data/file.nc``,
            etc.). If False then the returned directory will not begin
            with a URI scheme component. If `None` (the default) then
            the returned directory will begin with a URI scheme
            component if the input *path* does.

        isdir: `bool`, optional
            Set to True if *path* represents a directory, rather than
            a file.

        sep: `bool`, optional
            Set to True to add a trailing path separator to the
            returned directory.

    :Returns:

        `str`
            The directory of the path.

    **Examples**

    >>> import os
    >>> os.getcwd()
    '/data/archive'

    >>> cfdm.dirname("file.nc")
    ''
    >>> cfdm.dirname("file.nc", normalise=True)
    '/data/archive'
    >>> cfdm.dirname("file.nc", normalise=True, uri=True)
    'file:///data/archive
    >>> cfdm.dirname("file.nc", normalise=True, uri=False)
    '/data/archive'
    >>> cfdm.dirname("file.nc", normalise=True, sep=True)
    '/data/archive/'

    >>> cfdm.dirname("model/file.nc"), "model")
    >>> cfdm.dirname("model/file.nc", normalise=True)
    '/data/archive/model'
    >>> cfdm.dirname("model/file.nc", normalise=True, uri=True)
    'file:///data/archive/model'
    >>> cfdm.dirname("model/file.nc", normalise=True, uri=False)
    '/data/archive/model'

    >>> cfdm.dirname("../file.nc")
    '..'
    >>> cfdm.dirname("../file.nc", normalise=True)
    '/data'
    >>> cfdm.dirname("../file.nc", normalise=True, uri=True),
    'file://{/data}'
    >>> cfdm.dirname("../file.nc", normalise=True, uri=False)
    '/data'

    >>> cfdm.dirname("/model/file.nc")
    '/model'
    >>> cfdm.dirname("/model/file.nc", normalise=True)
    '/model'
    >>> cfdm.dirname("/model/file.nc", normalise=True, uri=True)
    'file:///model'
    >>> cfdm.dirname("/model/file.nc", normalise=True, uri=False)
    '/model'

    >>> cfdm.dirname("")
    ''
    >>> cfdm.dirname("", normalise=True)
    '/data/archive'
    >>> cfdm.dirname("", normalise=True, uri=True)
    'file:///data/archive'
    >>> cfdm.dirname("", normalise=True, uri=False)
    '/data/archive'
    >>> cfdm.dirname("https:///data/archive/file.nc")
    'https:///data/archive'
    >>> cfdm.dirname("https:///data/archive/file.nc", normalise=True)
    'https:///data/archive'
    >>> cfdm.dirname("https:///data/archive/file.nc", normalise=True, uri=True)
    'https:///data/archive'
    >>> cfdm.dirname("https:///data/archive/file.nc", normalise=True, uri=False)
    ValueError: Can't set uri=False for path='https:///data/archive/file.nc'

    >>> cfdm.dirname("file:///data/archive/file.nc")
    'file:///data/archive'
    >>> cfdm.dirname("file:///data/archive/file.nc", normalise=True)
    'file:///data/archive'
    >>> cfdm.dirname("file:///data/archive/file.nc", normalise=True, uri=True)
    'file:///data/archive'
    >>> cfdm.dirname("file:///data/archive/file.nc", normalise=True, uri=False)
    '/data/archive'

    >>> cfdm.dirname("file:///data/archive/../file.nc")
    'file:///data/archive/..'
    >>> cfdm.dirname("file:///data/archive/../file.nc", normalise=True)
    'file:///data'
    >>> cfdm.dirname("file:///data/archive/../file.nc", normalise=True, uri=True)
    'file:///data'
    >>> cfdm.dirname("file:///data/archive/../file.nc", normalise=True, uri=False)
    '/data'

    """
    u = urisplit(path)
    scheme = u.scheme
    path = u.path

    authority = u.authority
    if authority is None:
        authority = ""

    if scheme:
        # Remote (or "file:")
        if normalise and (scheme == "file" or path.startswith(os_sep)):
            path = os_abspath(path)

        if not isdir:
            path = os_dirname(path)

        if uri or uri is None:
            path = uricompose(scheme=scheme, authority=authority, path=path)
        elif scheme != "file":
            raise ValueError(f"Can't set uri=False for path={u.geturi()!r}")

    else:
        # Local file
        if not isdir:
            path = os_dirname(path)

        if normalise:
            path = os_abspath(path)

        if uri:
            path = uricompose(scheme="file", authority=authority, path=path)

    fragment = u.fragment
    if fragment is not None:
        # Append a URI fragment. Do this with a string-append, rather
        # than via `uricompose` in case the fragment contains more
        # than one # character.
        path += f"#{fragment}"

    if sep:
        # Append the directory separator
        path = join(path, "")

    return path


def unique_constructs(constructs, ignore_properties=None, copy=True):
    """Return the unique constructs from a sequence.

    .. versionadded:: (cfdm) 1.9.0.0

    :Parameters:

        constructs: sequence of constructs
            The constructs to be compared. The constructs may comprise
            a mixture of types. The sequence can be empty.

        ignore_properties: (sequence of) `str`, optional
            The names of construct properties to be ignored when
            testing for uniqueness. Any of these properties which have
            unequal values on otherwise equal input constructs are
            removed from the returned unique construct.

            .. versionadded:: (cfdm) 1.10.0.3

        copy: `bool`, optional
            If True (the default) then each returned construct is a
            deep copy of an input construct, otherwise they are not
            copies.

            If *ignore_properties* has been set then *copy* is ignored
            and deep copies are always returned, even if
            *ignore_properties* is an empty sequence.

    :Returns:

        Sequence of constructs
            The unique constructs in a sequence of the same type as
            the input *constructs*. If *constructs* was a generator
            then a generator is returned.

    **Examples**

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

    """
    out_type = type(constructs)

    if not constructs:
        # 'constructs' is an empty sequence
        return out_type([])

    # ----------------------------------------------------------------
    # Find the first construct in the sequence and create an iterator
    # for the rest
    # ----------------------------------------------------------------
    try:
        # 'constructs' is a sequence?
        construct0 = constructs[0]
        constructs = (c for c in constructs[1:])
    except TypeError:
        try:
            # 'constructs' is a generator?
            construct0 = next(constructs)
        except StopIteration:
            # 'constructs' is an empty generator
            return (c for c in ())
        else:
            generator_out = True
    else:
        generator_out = False

    if ignore_properties is not None:
        copy = True

    if isinstance(ignore_properties, str):
        ignore_properties = (ignore_properties,)

    if copy:
        construct0 = construct0.copy()

    # Initialise the list of unique constructs
    out = [construct0]

    # ----------------------------------------------------------------
    # Loop round the iterator, adding any new unique constructs to the
    # list
    # ----------------------------------------------------------------
    for construct in constructs:
        equal = False

        for c in out:
            if construct.equals(
                c, ignore_properties=ignore_properties, verbose="DISABLE"
            ):
                equal = True
                if ignore_properties:
                    for prop in ignore_properties:
                        if construct.get_property(
                            prop, None
                        ) != c.get_property(prop, None):
                            c.del_property(prop, None)

                break

        if not equal:
            if copy:
                construct = construct.copy()

            out.append(construct)

    if generator_out:
        return (c for c in out)

    return out_type(out)


@total_ordering
class Constant(metaclass=DocstringRewriteMeta):
    """A container for a constant with context manager support.

    The constant value is accessed via the `value` attribute:

       >>> c = {{package}}.{{class}}(1.2)
       >>> c.value
       1.2

    Conversion to `int`, `float`, `str` and `bool` is with the usual
    built-in functions:

       >>> c = {{package}}.{{class}}(1.2)
       >>> int(c)
       1
       >>> float(c)
       1.2
       >>> str(c)
       '1.2'
       >>> bool(c)
       True

    Augmented arithmetic assignments (``+=``, ``-=``, ``*=``, ``/=``,
    ``//=``) update `{{class}}` objects in-place:

       >>> c = {{package}}.{{class}}(20)
       >>> c.value
       20
       >>> c /= 2
       >>> c
       <{{repr}}{{class}}: 10.0>
       >>> c += c
       <{{repr}}{{class}}: 20.0>

       >>> c = {{package}}.{{class}}('New_')
       >>> c *= 2
       <{{repr}}{{class}}: 'New_New_'>

    Binary arithmetic operations (``+``, ``-``, ``*``, ``/``, ``//``)
    are equivalent to the operation acting on the `Constant` object's
    `value` attribute:

       >>> c = {{package}}.{{class}}(20)
       >>> c.value
       20
       >>> c * c
       400
       >>> c * 3
       60
       >>> 2 - c
       -18

       >>> c = {{package}}.{{class}}('New_')
       >>> c * 2
       'New_New_'

    Care is required when the right hand side operand is a `numpy`
    array


       >>> c * numpy.array([1, 2, 3])
       array([20, 40, 60])
       >>> d = numpy.array([1, 2, 3]) * c
       >>> d
       array([10, 20, 30], dtype=object)
       >>> type(d[0])
       int

    Unary arithmetic operations (``+``, ``-``, `abs`) are equivalent
    to the operation acting on the `{{class}}` object's `value`
    attribute:

       >>> c = {{package}}.{{class}}(-20)
       >>> c.value
       -20
       >>> -c
       20
       >>> abs(c)
       20
       >>> +c
       -20

    Rich comparison operations are equivalent to the operation acting
    on the `{{class}}` object's `value` attribute:

       >>> c = {{package}}.{{class}}(20)
       >>> d = {{package}}.{{class}}(1)
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

       >>> c = {{package}}.{{class}}('new')
       >>> d = {{package}}.{{class}}('old')
       >>> c == d
       False
       >>> c == 'new'
       True
       >>> c != 3
       True
       >>> 3 == c
       False


       >>> c = {{package}}.{{class}}()
       >>> c < numpy.array([10, 20, 30])
       array([False, False,  True])
       >>> numpy.array([10, 20, 30]) >= c
       array([False,  True,  True])

    `{{class}}` instances are hashable.

    **Context manager**

    The `{{class}}` instance can be used as a context manager that
    upon exit executes the function defined by the `_func` attribute,
    with the `value` attribute as an argument. For example, the
    `{{class}}` instance ``c`` would execute ``c._func(c.value)`` upon
    exit.

    .. versionadded:: (cfdm) 1.8.8.0

    """

    __slots__ = ("_func", "value", "_type")

    def __init__(self, value, _func=None):
        """**Initialisation**

        :Parameters:

            value:
                A value for the constant.

            _func: function, optional
                A function that that is executed upon exit from a
                context manager, that takes the *value* parameter as
                its argument.

        """
        self.value = value
        self._func = _func

    def __docstring_substitutions__(self):
        """Defines applicable docstring substitutions.

        Substitutons are considered applicable if they apply to this
        class as well as all of its subclasses.

        These are in addtion to, and take precendence over, docstring
        substitutions defined by the base classes of this class.

        See `_docstring_substitutions` for details.

        .. versionaddedd:: (cfdm) 1.8.8.0

        :Returns:

            `dict`
                The docstring substitutions that have been applied.

        """
        return _docstring_substitution_definitions

    def __docstring_package_depth__(self):
        """Returns the package depth for {{package}} substitutions.

        See `_docstring_package_depth` for details.

        .. versionaddedd:: (cfdm) 1.8.8.0

        """
        return 0

    def __enter__(self):
        """Enter the runtime context."""
        if getattr(self, "_func", None) is None:
            raise AttributeError(
                f"Can't use {self!r} as a context manager because the "
                "'_func' attribute is not defined"
            )

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Exit the runtime context."""
        self._func(self.value)

    def __deepcopy__(self, memo):
        """Called by the `copy.deepcopy` function.

        x.__deepcopy__() <==> copy.deepcopy(x)

        """
        return self.copy()

    def __bool__(self):
        """Truth value testing and the built-in operation `bool`.

        x.__bool__() <==> bool(x)

        """
        return bool(self.value)

    def __float__(self):
        """Called to implement the built-in function `float`.

        x.__float__() <==> float(x)

        """
        return float(self.value)

    def __int__(self):
        """Called to implement the built-in function `int`.

        x.__int__() <==> int(x)

        """
        return int(self.value)

    def __eq__(self, other):
        """The rich comparison operator ``==``.

        x.__eq__(y) <==> x==y

        """
        return self.value == other

    def __lt__(self, other):
        """The rich comparison operator ``<``.

        x.__lt__(y) <==> x<y

        """
        return self.value < other

    def __abs__(self):
        """The unary arithmetic operation ``abs``.

        x.__abs__() <==> abs(x)

        """
        return abs(self.value)

    def __neg__(self):
        """The unary arithmetic operation ``-``.

        x.__neg__() <==> -x

        """
        return -self.value

    def __pos__(self):
        """The unary arithmetic operation ``+``.

        x.__pos__() <==> +x

        """
        return self.value

    def __iadd__(self, other):
        """The augmented arithmetic assignment ``+=``.

        x.__iadd__(y) <==> x+=y

        """
        self.value += other
        return self

    def __ifloordiv__(self, other):
        """The augmented arithmetic assignment ``//=``.

        x.__ifloordiv__(y) <==> x//=y

        """
        self.value //= other
        return self

    def __imul__(self, other):
        """The augmented arithmetic assignment ``*=``.

        x.__imul__(y) <==> x*=y

        """
        self.value *= other
        return self

    def __isub__(self, other):
        """The augmented arithmetic assignment ``-=``.

        x.__isub__(y) <==> x-=y

        """
        self.value -= other
        return self

    def __itruediv__(self, other):
        """The augmented arithmetic assignment ``/=`` (true division).

        x.__itruediv__(y) <==> x/=y

        """
        self.value /= other
        return self

    def __add__(self, other):
        """The binary arithmetic operation ``+``.

        x.__add__(y) <==> x+y

        """
        return self.value + other

    def __floordiv__(self, other):
        """The binary arithmetic operation ``//``.

        x.__floordiv__(y) <==> x//y

        """
        return self.value // other

    def __mul__(self, other):
        """The binary arithmetic operation ``*``.

        x.__mul__(y) <==> x*y

        """
        return self.value * other

    def __sub__(self, other):
        """The binary arithmetic operation ``-``.

        x.__sub__(y) <==> x-y

        """
        return self.value - other

    def __truediv__(self, other):
        """The binary arithmetic operation ``/`` (true division).

        x.__truediv__(y) <==> x/y

        """
        return self.value / other

    def __radd__(self, other):
        """Binary arithmetic operation ``+`` with reflected operands.

        x.__radd__(y) <==> y+x

        """
        return other + self.value

    def __rfloordiv__(self, other):
        """Binary arithmetic operation ``//`` with reflected operands.

        x.__rfloordiv__(y) <==> y//x

        """
        return other // self.value

    def __rmul__(self, other):
        """Binary arithmetic operation ``*`` with reflected operands.

        x.__rmul__(y) <==> y*x

        """
        return other * self.value

    def __rsub__(self, other):
        """Binary arithmetic operation ``-`` with reflected operands.

        x.__rsub__(y) <==> y-x

        """
        return other - self.value

    def __rtruediv__(self, other):
        """The binary arithmetic operation ``/`` (true division) with
        reflected operands.

        x.__rtruediv__(y) <==> y/x

        """
        return other / self.value

    def __hash__(self):
        """Returns the hash value of the Constant."""
        return hash((self.value, getattr(self, "_func", None)))

    def __repr__(self):
        """Called by the `repr` built-in function."""
        return f"<{self.__class__.__name__}: {self.value!r}>"

    def __str__(self):
        """Called by the `str` built-in function."""
        return str(self.value)

    def copy(self):
        """Return a deep copy.

        ``c.copy()`` is equivalent to ``copy.deepcopy(c)``.

        .. versionadded:: (cfdm) 1.8.8.0

        :Returns:

            `{{class}}`
                The deep copy.

        """
        out = type(self)(
            value=deepcopy(self.value), _func=getattr(self, "_func", None)
        )

        if not hasattr(self, "_func"):
            del out._func

        return out


class Configuration(dict, metaclass=DocstringRewriteMeta):
    """Dictionary-like container for the global constants.

    The container has context manager support.

    Initialisation is as for a `dict`, and nearly all of the `dict`
    methods are available with the same behaviours (`clear`,
    `fromkeys`, `get`, `items`, `keys`, `pop`, `popitem`,
    `setdefault`, `update`, `values`):

       >>> c = {{package}}.{{class}}(atol=0.1, rtol=0.2, log_level='INFO')
       >>> c
       <{{repr}}{{class}}: {'atol': 0.1, 'rtol': 0.2, 'log_level': 'INFO'}>
       >>> print(c)
       {'atol': 0.1, 'rtol': 0.2, 'log_level': 'INFO'}
       >>> c.pop('atol')
       0.1
       >>> c
       <{{repr}}{{class}}: {'rtol': 0.2, 'log_level': 'INFO'}>
       >>> c.clear()
       >>> c
       <{{repr}}{{class}}: {}>

    The `copy` method return a deep copy, rather than a shallow one.

    **Context manager**

    The `{{class}}` instance can be used as a context manager that
    upon exit executes the function defined by the `_func` attribute,
    with the class itself as input *kwargs* parameters. For example,
    the `{{class}}` instance ``c`` would execute ``c._func(**c)`` upon
    exit.

    .. versionadded:: (cfdm) 1.8.8.0

    """

    def __new__(cls, *args, **kwargs):
        """Store components."""
        instance = super().__new__(cls)
        instance._func = configuration
        return instance

    def __docstring_substitutions__(self):
        """Defines applicable docstring substitutions.

        Substitutons are considered applicable if they apply to this
        class as well as all of its subclasses.

        These are in addtion to, and take precendence over, docstring
        substitutions defined by the base classes of this class.

        See `_docstring_substitutions` for details.

        .. versionaddedd:: (cfdm) 1.8.8.0

        :Returns:

            `dict`
                The docstring substitutions that have been applied.

        """
        return _docstring_substitution_definitions

    def __docstring_package_depth__(self):
        """Returns the package depth for {{package}} substitutions.

        See `_docstring_package_depth` for details.

        .. versionaddedd:: (cfdm) 1.8.8.0

        """
        return 0

    def __deepcopy__(self, memo):
        """Called by the `copy.deepcopy` function.

        x.__deepcopy__() <==> copy.deepcopy(x)

        """
        return self.copy()

    def __enter__(self):
        """Enter the runtime context."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Exit the runtime context."""
        self._func(**self)

    def __repr__(self):
        """Called by the `repr` built-in function."""
        return f"<{self.__class__.__name__}: {super().__repr__()}>"

    def __str__(self):
        """Called by the `str` built-in function.

        x.__str__() <==> str(x)

        """
        return super().__repr__()

    # ----------------------------------------------------------------
    # Methods
    # ----------------------------------------------------------------
    def copy(self):
        """Return a deep copy.

        ``c.copy()`` is equivalent to ``copy.deepcopy(c)``.

        .. versionadded:: (cfdm) 1.8.8.0

        :Returns:

            `{{class}}`
                The deep copy.

        """
        out = type(self)(**deepcopy(self), _func=getattr(self, "_func", None))

        if not hasattr(self, "_func"):
            del out._func

        return out


class ConstantAccess(metaclass=DocstringRewriteMeta):
    '''Base class to act as a function accessing package-wide constants.

    Subclasses must implement or inherit a method called `_parse` as
    follows:

       def _parse(cls, arg):
          """Parse a new constant value.

       :Parameter:

            cls:
                This class.

            arg:
                The given new constant value.

       :Returns:

                A version of the new constant value suitable for
                insertion into the `CONSTANTS` dictionary.

           """

    '''

    # Define the dictionary that stores the constant values
    _CONSTANTS = CONSTANTS

    # Define the `Constant` object that contains a constant value
    _Constant = Constant

    # Define the key of the _CONSTANTS dictionary that contains the
    # constant value
    _name = None

    def __new__(cls, *arg):
        """Return a `Constant` instance during class creation."""
        old = cls._CONSTANTS[cls._name]
        if arg:
            arg = arg[0]
            try:
                # Check for Constants instance
                arg = arg.value
            except AttributeError:
                pass

            cls._CONSTANTS[cls._name] = cls._parse(cls, arg)

        return cls._Constant(old, _func=cls)

    def __docstring_substitutions__(self):
        """Defines applicable docstring substitutions.

        Substitutons are considered applicable if they apply to this
        class as well as all of its subclasses.

        These are in addtion to, and take precendence over, docstring
        substitutions defined by the base classes of this class.

        See `_docstring_substitutions` for details.

        .. versionaddedd:: (cfdm) 1.8.8.0

        :Returns:

            `dict`
                The docstring substitutions that have been applied.

        """
        return _docstring_substitution_definitions

    def __docstring_package_depth__(self):
        """Returns the package depth for {{package}} substitutions.

        See `_docstring_package_depth` for details.

        .. versionaddedd:: (cfdm) 1.8.8.0

        """
        return 0


class atol(ConstantAccess):
    """The numerical equality tolerance on absolute differences.

    Two real numbers ``x`` and ``y`` are considered equal if
    ``|x-y|<=atol+rtol|y|``, where ``atol`` (the tolerance on absolute
    differences) and ``rtol`` (the tolerance on relative differences)
    are positive, typically very small numbers. The values of ``atol``
    and ``rtol`` are initialised to the system epsilon (the difference
    between 1 and the least value greater than 1 that is representable
    as a float).

    .. versionadded:: (cfdm) 1.7.0

    .. seealso:: `rtol`, `configuration`

    :Parameters:

        arg: `float` or `Constant`, optional
            The new value of relative tolerance. The default is to not
            change the current value.

    :Returns:

        `Constant`
            The value prior to the change, or the current value if no
            new value was specified.

    **Examples**

    >>> {{package}}.{{class}}()
    <{{repr}}Constant: 2.220446049250313e-16>
    >>> print({{package}}.{{class}}())
    2.220446049250313e-16
    >>> str({{package}}.{{class}}())
    '2.220446049250313e-16'
    >>> {{package}}.{{class}}().value
    2.220446049250313e-16
    >>> float({{package}}.{{class}}())
    2.220446049250313e-16

    >>> old = {{package}}.{{class}}(1e-10)
    >>> {{package}}.{{class}}()
    <{{repr}}Constant: 1e-10>
    >>> {{package}}.{{class}}(old)
    <{{repr}}Constant: 1e-10>
    >>> {{package}}.{{class}}()
    <{{repr}}Constant: 2.220446049250313e-16>

    Use as a context manager:

    >>> print({{package}}.{{class}}())
    2.220446049250313e-16
    >>> with {{package}}.{{class}}(1e-5):
    ...     print({{package}}.{{class}}(), {{package}}.{{class}}(2e-30), {{package}}.{{class}}())
    ...
    1e-05 1e-05 2e-30
    >>> print({{package}}.{{class}}())
    2.220446049250313e-16

    """

    _name = "ATOL"

    def _parse(cls, arg):
        """Parse a new constant value.

        .. versionaddedd:: (cfdm) 1.8.8.0

        :Parameters:

            cls:
                This class.

            arg:
                The given new constant value.

        :Returns:

                A version of the new constant value suitable for
                insertion into the `CONSTANTS` dictionary.

        """
        return float(arg)


class rtol(ConstantAccess):
    """The numerical equality tolerance on relative differences.

    Two real numbers ``x`` and ``y`` are considered equal if
    ``|x-y|<=atol+rtol|y|``, where ``atol`` (the tolerance on absolute
    differences) and ``rtol`` (the tolerance on relative differences)
    are positive, typically very small numbers. The values of ``atol``
    and ``rtol`` are initialised to the system epsilon (the difference
    between 1 and the least value greater than 1 that is representable
    as a float).

    .. versionadded:: (cfdm) 1.7.0

    .. seealso:: `atol`, `configuration`

    :Parameters:

        arg: `float` or `Constant`, optional
            The new value of relative tolerance. The default is to not
            change the current value.

    :Returns:

        `Constant`
            The value prior to the change, or the current value if no
            new value was specified.

    **Examples**

    >>> {{package}}.{{class}}()
    <{{repr}}Constant: 2.220446049250313e-16>
    >>> print({{package}}.{{class}}())
    2.220446049250313e-16
    >>> str({{package}}.{{class}}())
    '2.220446049250313e-16'
    >>> {{package}}.{{class}}().value
    2.220446049250313e-16
    >>> float({{package}}.{{class}}())
    2.220446049250313e-16

    >>> old = {{package}}.{{class}}(1e-10)
    >>> {{package}}.{{class}}()
    <{{repr}}Constant: 1e-10>
    >>> {{package}}.{{class}}(old)
    <{{repr}}Constant: 1e-10>
    >>> {{package}}.{{class}}()
    <{{repr}}Constant: 2.220446049250313e-16>

    Use as a context manager:

    >>> print({{package}}.{{class}}())
    2.220446049250313e-16
    >>> with {{package}}.{{class}}(1e-5):
    ...     print({{package}}.{{class}}(), {{package}}.{{class}}(2e-30), {{package}}.{{class}}())
    ...
    1e-05 1e-05 2e-30
    >>> print({{package}}.{{class}}())
    2.220446049250313e-16

    """

    _name = "RTOL"

    def _parse(cls, arg):
        """Parse a new constant value.

        .. versionaddedd:: (cfdm) 1.8.8.0

        :Parameters:

            cls:
                This class.

            arg:
                The given new constant value.

        :Returns:

                A version of the new constant value suitable for insertion
                into the `CONSTANTS` dictionary.

        """
        return float(arg)


class chunksize(ConstantAccess):
    """Set the default chunksize used by `dask` arrays.

    If called without any arguments then the existing chunksize is
    returned.

    .. note:: Setting the chunk size will also change the `dask`
              global configuration value ``'array.chunk-size'``. If
              `chunksize` is used in context manager then the `dask`
              configuration value is only altered within that context.
              Setting the chunk size directly from the `dask`
              configuration API will affect subsequent data creation,
              but will *not* change the value of `chunksize`.

    .. versionaddedd:: (cfdm) 1.11.2.0

    :Parameters:

        arg: number or `str` or `Constant`, optional
            The chunksize in bytes. Any size accepted by
            `dask.utils.parse_bytes` is accepted, for instance
            ``100``, ``'100'``, ``'1e6'``, ``'100 MB'``, ``'100M'``,
            ``'5kB'``, ``'5.4 kB'``, ``'1kiB'``, ``'1e6 kB'``, and
            ``'MB'`` are all valid sizes.

            Note that if *arg* is a `float`, or a string that implies
            a non-integral amount of bytes, then the integer part
            (rounded down) will be used.

            *Parameter example:*
               A chunksize of 2 MiB may be specified as ``'2097152'``
               or ``'2 MiB'``

            *Parameter example:*
               Chunksizes of ``'2678.9'`` and ``'2.6789 KB'`` are both
               equivalent to ``2678``.

    :Returns:

        `Constant`
            The value prior to the change, or the current value if no
            new value was specified.

    **Examples**

    >>> print(cfdm.chunksize())
    134217728
    >>> old = cfdm.chunksize(1000000)
    >>> print(cfdm.chunksize(old))
    1000000
    >>> print(cfdm.chunksize())
    134217728
    >>> with cfdm.chunksize(314159):
    ...     print(cfdm.chunksize())
    ...
    314159
    >>> print(cfdm.chunksize())
    134217728

    """

    _name = "CHUNKSIZE"

    def _parse(cls, arg):
        """Parse a new constant value.

        .. versionaddedd:: (cfdm) 1.11.2.0

        :Parameters:

            cls:
                This class.

            arg:
                The given new constant value.

        :Returns:

                A version of the new constant value suitable for insertion
                into the `CONSTANTS` dictionary.

        """
        _config.set({"array.chunk-size": arg})
        return parse_bytes(arg)


class log_level(ConstantAccess):
    """The minimal level of seriousness of log messages which are shown.

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

        `Constant`
            The value prior to the change, or the current value if no
            new value was specified (or if one was specified but was
            not valid). Note the string name, rather than the
            equivalent integer, will always be returned.

    **Examples**

    >>> {{package}}.{{class}}()
    <{{repr}}Constant: 'WARNING'>
    >>> print({{package}}.{{class}}())
    WARNING
    >>> str({{package}}.{{class}}())
    'WARNING'

    >>> old = {{package}}.{{class}}('INFO')
    >>> {{package}}.{{class}}()
    <{{repr}}Constant: 'WARNING'>
    >>> {{package}}.{{class}}(old)
    <{{repr}}Constant: 'INFO'>
    >>> {{package}}.{{class}}()
    <{{repr}}Constant: 'WARNING'>

    Use as a context manager:

    >>> print({{package}}.{{class}}())
    WARNING
    >>> with {{package}}.{{class}}('DETAIL'):
    ...     print({{package}}.{{class}}(), {{package}}.{{class}}(-1), {{package}}.{{class}}())
    ...
    DETAIL DETAIL DEBUG
    >>> print({{package}}.{{class}}())
    WARNING

    """

    _name = "LOG_LEVEL"

    # Define the valid log levels
    _ValidLogLevels = ValidLogLevels

    # Function that returns a Boolean stating if input is a
    # ValidLogLevels Enum integer
    _is_valid_log_level_int = _is_valid_log_level_int

    # Function that re-sets minimum level for displayed log messages
    # of a logger
    _reset_log_emergence_level = _reset_log_emergence_level

    def _parse(cls, arg):
        """Parse a new constant value.

        It is assumed that the `_is_valid_log_level_int` and
        `_reset_log_emergence_level` are defined within the namespace.

        .. versionaddedd:: (cfdm) 1.8.8.0

        :Parameters:

            cls:
                This class.

            arg:
                The given new constant value.

        :Returns:

                A version of the new constant value suitable for insertion
                into the `CONSTANTS` dictionary.

        """
        # Ensuring it is a valid level specifier to set & use, either
        # a case-insensitive string of valid log level or
        # dis/en-abler, or an integer 0 to 5 corresponding to one of
        # those as converted above:
        if isinstance(arg, str):
            arg = arg.upper()
        elif cls._is_valid_log_level_int(arg):
            # Convert to string ID first
            arg = cls._ValidLogLevels(arg).name

        if not hasattr(cls._ValidLogLevels, arg):
            listed_levels = ", '".join(
                [
                    val.name + "' = " + str(val.value)
                    for val in cls._ValidLogLevels
                ]
            )
            raise ValueError(
                f"Logging level {arg!r} is not one of the valid values "
                f"'{listed_levels}', where either the string or the "
                "corresponding integer is accepted. Value remains as it was."
            )

        # Safe to reset now as guaranteed to be valid:
        cls._reset_log_emergence_level(arg)

        return arg


def ATOL(*new_atol):
    """Alias for `cfdm.atol`."""
    return atol(*new_atol)


def RTOL(*new_rtol):
    """Alias for `cfdm.rtol`."""
    return rtol(*new_rtol)


def is_log_level_debug(logger):
    """Return True if and only if log level is at least DEBUG.

    .. versionadded:: (cfdm) 1.8.9.0

    .. seealso:: `log_level`

    :Parameters:

        logger: `logging.Logger`
           The logger in use.

    :Returns:

        `bool`
            Whether or not the log level is at least DEBUG.

    """
    return logger.parent.level <= logging.DEBUG


def is_log_level_detail(logger):
    """Return True if and only if log level is at least DETAIL.

    .. versionadded:: (cfdm) 1.8.9.0

    .. seealso:: `log_level`

    :Parameters:

        logger: `logging.Logger`
           The logger in use.

    :Returns:

        `bool`
            Whether or not the log level is at least DETAIL.

    """
    return logger.parent.level <= logging.DETAIL


def is_log_level_info(logger):
    """Return True if and only if log level is at least INFO.

    .. versionadded:: (cfdm) 1.8.9.0

    .. seealso:: `log_level`

    :Parameters:

        logger: `logging.Logger`
           The logger in use.

    :Returns:

        `bool`
            Whether or not the log level is at least INFO.

    """
    return logger.parent.level <= logging.INFO


def integer_dtype(n):
    """Return the smallest data type that can store the given integer.

    .. versionadded:: (cfdm) 1.11.0.0

    :Parameters:

        n: integer
           The integer for which a data type is required.

    :Returns:

        `numpy.dtype`
          ``numpy.dtype('int32')`` if *n* is representable by a 32-bit
           integer, otherwise ``numpy.dtype(int)``.

    **Examples**

    >>> np.iinfo('int32')
    iinfo(min=-2147483648, max=2147483647, dtype=int32)

    >>> cfdm.integer_dtype(123)
    dtype('int32')
    >>> cfdm.integer_dtype(-4294967296)
    dtype('int64')

    >>> cfdm.integer_dtype(np.iinfo('int32').max)
    dtype('int32')
    >>> cfdm.integer_dtype(np.iinfo('int32').min)
    dtype('int32')

    >>> cfdm.integer_dtype(np.iinfo('int32').max + 1)
    dtype('int64')
    >>> cfdm.integer_dtype(np.iinfo('int32').min - 1)
    dtype('int64')

    """
    dtype = np.dtype("int32")
    iinfo = np.iinfo(dtype)
    if n > iinfo.max or n < iinfo.min:
        dtype = np.dtype(int)

    return dtype


def _numpy_allclose(a, b, rtol=None, atol=None, verbose=None):
    """Returns True if two broadcastable arrays have equal values to
    within numerical tolerance, False otherwise.

    The tolerance values are positive, typically very small numbers. The
    relative difference (``rtol * abs(b)``) and the absolute difference
    ``atol`` are added together to compare against the absolute difference
    between ``a`` and ``b``.

    .. versionadded:: (cfdm) 1.11.2.0

    :Parameters:

        a, b : array_like
            Input arrays to compare.

        atol : float, optional
            The absolute tolerance for all numerical comparisons, By
            default the value returned by the `atol` function is used.

        rtol : float, optional
            The relative tolerance for all numerical comparisons, By
            default the value returned by the `rtol` function is used.

    :Returns:

        `bool`
            Returns True if the arrays are equal, otherwise False.

    **Examples**

    >>> cfdm._numpy_allclose([1, 2], [1, 2])
    True
    >>> cfdm._numpy_allclose(numpy.array([1, 2]), numpy.array([1, 2]))
    True
    >>> cfdm._numpy_allclose([1, 2], [1, 2, 3])
    False
    >>> cfdm._numpy_allclose([1, 2], [1, 4])
    False

    >>> a = numpy.ma.array([1])
    >>> b = numpy.ma.array([2])
    >>> a[0] = numpy.ma.masked
    >>> b[0] = numpy.ma.masked
    >>> cfdm._numpy_allclose(a, b)
    True

    """
    # TODO: we want to use @_manage_log_level_via_verbosity on this function
    # but we cannot, since importing it to this module would lead to a
    # circular import dependency with the decorators module. Tentative plan
    # is to move the function elsewhere. For now, it is not 'loggified'.

    # THIS IS WHERE SOME NUMPY FUTURE WARNINGS ARE COMING FROM

    a_is_masked = np.ma.isMA(a)
    b_is_masked = np.ma.isMA(b)

    if not (a_is_masked or b_is_masked):
        try:
            return np.allclose(a, b, rtol=rtol, atol=atol)
        except (IndexError, NotImplementedError, TypeError):
            return np.all(a == b)
    else:
        if a_is_masked and b_is_masked:
            if (a.mask != b.mask).any():
                if verbose:
                    print("Different masks (A)")

                return False
        else:
            if np.ma.is_masked(a) or np.ma.is_masked(b):
                if verbose:
                    print("Different masks (B)")

                return False

        try:
            return np.ma.allclose(a, b, rtol=rtol, atol=atol)
        except (IndexError, NotImplementedError, TypeError):
            # To prevent a bug causing some header/coord-only CDL reads or
            # aggregations to error. See also TODO comment below.
            if a.dtype == b.dtype:
                out = np.ma.all(a == b)
            else:
                # TODO: is this most sensible? Or should we attempt dtype
                # conversion and then compare? Probably we should avoid
                # altogether by catching the different dtypes upstream?
                out = False
            if out is np.ma.masked:
                return True
            else:
                return out


def indices_shape(indices, full_shape, keepdims=True):
    """Return the shape of the array subspace implied by indices.

    **Performance**

    Boolean `dask` arrays will be computed, and `dask` arrays with
    unknown size will have their chunk sizes computed.

    .. versionadded:: (cfdm) 1.11.2.0

    .. seealso:: `cfdm.parse_indices`

    :Parameters:

        indices: `tuple`
            The indices to be applied to an array with shape
            *full_shape*.

        full_shape: sequence of `ints`
            The shape of the array to be subspaced.

        keepdims: `bool`, optional
            If True then an integral index is converted to a
            slice. For instance, ``3`` would become ``slice(3, 4)``.

    :Returns:

        `list`
            The shape of the subspace defined by the *indices*.

    **Examples**

    >>> import numpy as np
    >>> import dask.array as da

    >>> cfdm.indices_shape((slice(2, 5), 4), (10, 20))
    [3, 1]
    >>> cfdm.indices_shape(([2, 3, 4], np.arange(1, 6)), (10, 20))
    [3, 5]

    >>> index0 = [False] * 5
    >>> index0[2:5] = [True] * 3
    >>> cfdm.indices_shape((index0, da.arange(1, 6)), (10, 20))
    [3, 5]

    >>> index0 = da.full((5,), False, dtype=bool)
    >>> index0[2:5] = True
    >>> index1 = np.full((6,), False, dtype=bool)
    >>> index1[1:6] = True
    >>> cfdm.indices_shape((index0, index1), (10, 20))
    [3, 5]

    >>> index0 = da.arange(5)
    >>> index0 = index0[index0 < 3]
    >>> cfdm.indices_shape((index0, []), (10, 20))
    [3, 0]

    >>> cfdm.indices_shape((da.from_array(2), np.array(3)), (10, 20))
    [1, 1]
    >>> cfdm.indices_shape((da.from_array([]), np.array(())), (10, 20))
    [0, 0]
    >>> cfdm.indices_shape((slice(1, 5, 3), 3), (10, 20))
    [2, 1]
    >>> cfdm.indices_shape((slice(5, 1, -2), 3), (10, 20))
    [2, 1]
    >>> cfdm.indices_shape((slice(5, 1, 3), 3), (10, 20))
    [0, 1]
    >>> cfdm.indices_shape((slice(1, 5, -3), 3), (10, 20))
    [0, 1]

    >>> cfdm.indices_shape((slice(2, 5), 4), (10, 20), keepdims=False)
    [3]
    >>> cfdm.indices_shape((da.from_array(2), 3), (10, 20), keepdims=False)
    []
    >>> cfdm.indices_shape((2, np.array(3)), (10, 20), keepdims=False)
    []

    """
    shape = []
    #    i = 0
    for index, full_size in zip(indices, full_shape):
        #    for index in indices:
        if index is None:
            shape.append(1)
            continue

        #        full_size = full_shape[i]
        #        i += 1

        if isinstance(index, slice):
            start, stop, step = index.indices(full_size)
            if (stop - start) * step < 0:
                # E.g. 5:1:3 or 1:5:-3
                size = 0
            else:
                size = abs((stop - start) / step)
                int_size = round(size)
                if size > int_size:
                    size = int_size + 1
                else:
                    size = int_size
        elif is_dask_collection(index) or isinstance(index, np.ndarray):
            if index.dtype == bool:
                # Size is the number of True values in the array
                size = int(index.sum())
            else:
                size = index.size
                if isnan(size):
                    index.compute_chunk_sizes()
                    size = index.size

            if not keepdims and not index.ndim:
                # Scalar array
                continue
        elif isinstance(index, list):
            size = len(index)
            if size:
                i = index[0]
                if isinstance(i, bool):
                    # Size is the number of True values in the list
                    size = sum(index)
        else:
            # Index is Integral
            if not keepdims:
                continue

            size = 1

        shape.append(size)

    return shape


def parse_indices(shape, indices, keepdims=True, newaxis=False):
    """Parse indices for array access and assignment.

    .. versionadded:: (cfdm) 1.11.2.0

    :Parameters:

        shape: sequence of `ints`
            The shape of the array.

        indices: `tuple`
            The indices to be applied.

        keepdims: `bool`, optional
            If True then an integral index is converted to a
            slice. For instance, ``3`` would become ``slice(3, 4)``.

        newaxis: `bool`, optional
            If True then allow *indices* to include one or more
            `numpy.newaxis` elements. If False (the default) then
            these elements are not allowed.

    :Returns:

        `list`
            The parsed indices.

    **Examples**

    >>> cfdm.parse_indices((5, 8), ([1, 2, 4, 6],))
    [array([1, 2, 4, 6]), slice(None, None, None)]
    >>> cfdm.parse_indices((5, 8), (Ellipsis, [2, 4, 6]))
    [slice(None, None, None), [2, 4, 6]]
    >>> cfdm.parse_indices((5, 8), (Ellipsis, 4))
    [slice(None, None, None), slice(4, 5, 1)]
    >>> cfdm.parse_indices((5, 8), (Ellipsis, 4), keepdims=False)
    [slice(None, None, None), 4]
    >>> cfdm.parse_indices((5, 8), (slice(-2, 2)))
    [slice(-2, 2, None), slice(None, None, None)]
    >>> cfdm.parse_indices((5, 8), (cfdm.Data([1, 3]),))
    [dask.array<array, shape=(2,), dtype=int64, chunksize=(2,), chunktype=numpy.ndarray>, slice(None, None, None)]

    """
    parsed_indices = []

    if not isinstance(indices, tuple):
        indices = (indices,)

    # Initialise the list of parsed indices as the input indices with
    # any Ellipsis objects expanded
    length = len(indices)
    n = len(shape)
    ndim = n
    for i, index in enumerate(indices):
        if index is Ellipsis:
            m = n - length + 1
            try:
                if indices[i + 1] is np.newaxis:
                    m += 1
            except IndexError:
                pass

            parsed_indices.extend([slice(None)] * m)
            n -= m
        else:
            parsed_indices.append(index)
            if index is np.newaxis:
                ndim += 1
                length += 1
            else:
                n -= 1

        length -= 1

    len_parsed_indices = len(parsed_indices)
    if ndim and len_parsed_indices > ndim:
        raise IndexError(
            f"Invalid indices {indices!r} for array with shape {shape}"
        )

    if len_parsed_indices < ndim:
        parsed_indices.extend([slice(None)] * (ndim - len_parsed_indices))

    if not ndim and parsed_indices:
        raise IndexError(
            "Scalar array can only be indexed with () or Ellipsis"
        )

    for i, (index, size) in enumerate(zip(parsed_indices, shape)):
        if not newaxis and index is np.newaxis:
            raise IndexError(
                f"Invalid indices {indices!r} for array with shape {shape}: "
                "New axis indices are not allowed"
            )

        if keepdims and isinstance(index, Integral):
            # Convert an integral index to a slice
            if index == -1:
                index = slice(-1, None, None)
            else:
                index = slice(index, index + 1, 1)

        elif hasattr(index, "to_dask_array"):
            to_dask_array = index.to_dask_array
            if callable(to_dask_array):
                # Replace index with its Dask array
                index = to_dask_array()

        parsed_indices[i] = index

    return parsed_indices


def _DEPRECATION_ERROR_KWARGS(
    instance,
    method,
    kwargs=None,
    message="",
    version=None,
    removed_at=None,
):
    """Error handling for deprecated kwargs.

    .. versionadded:: (cfdm) 1.12.0.0

    """
    if removed_at:
        removed_at = f" and will be removed at cfdm version {removed_at}"

    if not kwargs:
        kwargs = {}

    for key in kwargs:
        raise DeprecationError(
            f"Keyword {key!r} of method "
            f"'{instance.__class__.__name__}.{method}' has been deprecated "
            f"at cfdm version {version} and is no longer "
            f"available{removed_at}. {message}"
        )


def _DEPRECATION_ERROR_METHOD(
    instance, method, message="", version=None, removed_at=""
):
    """Error handling for deprecated kwargs methods.

    .. versionadded:: (cfdm) 1.12.2.0

    """
    if version is None:
        raise ValueError(
            "Must set 'version' in call to _DEPRECATION_ERROR_METHOD"
        )

    if removed_at:
        removed_at = f" and will be removed at version {removed_at}"

    raise DeprecationError(
        f"{instance.__class__.__name__} method {method!r} has been deprecated "
        f"at version {version} and is no longer available{removed_at}. "
        f"{message}"
    )
