import os
import platform
import sys
from pickle import dumps, loads

import netCDF4
import numpy

from . import __cf_version__, __file__, __version__


def environment(display=True, paths=True):
    """Return the names, versions and paths of all dependencies.

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

    >>> environment()
    Platform: Linux-4.15.0-72-generic-x86_64-with-debian-stretch-sid
    HDF5 library: 1.10.2
    netcdf library: 4.6.1
    python: 3.7.3 /home/user/anaconda3/bin/python
    netCDF4: 1.5.3 /home/user/anaconda3/lib/python3.7/site-packages/netCDF4/__init__.py
    numpy: 1.16.2 /home/user/anaconda3/lib/python3.7/site-packages/numpy/__init__.py
    cfdm.core: 1.9.0

    >>> environment(paths=False)
    Platform: Linux-4.15.0-72-generic-x86_64-with-debian-stretch-sid
    HDF5 library: 1.10.2
    netcdf library: 4.6.1
    python: 3.7.3
    netCDF4: 1.5.3
    numpy: 1.16.2
    cfdm.core: 1.9.0

    """
    dependency_version_paths_mapping = {
        "Platform": (platform.platform(), ""),
        "HDF5 library": (netCDF4.__hdf5libversion__, ""),
        "netcdf library": (netCDF4.__netcdf4libversion__, ""),
        "Python": (platform.python_version(), sys.executable),
        "netCDF4": (netCDF4.__version__, os.path.abspath(netCDF4.__file__)),
        "numpy": (numpy.__version__, os.path.abspath(numpy.__file__)),
        "cfdm.core": (__version__, os.path.abspath(__file__)),
    }
    string = "{0}: {1!s}"
    if paths:  # include path information, else exclude, when unpacking tuple
        string += " {2!s}"
    out = [
        string.format(dep, *info)
        for dep, info in dependency_version_paths_mapping.items()
    ]

    if display:
        print("\n".join(out))  # pragma: no cover
    else:
        return out


def CF():
    """The version of the CF conventions.

    This indicates which version of the CF conventions are represented
    by this release of the cfdm.core package, and therefore the
    version can not be changed.

    .. versionadded:: (cfdm) 1.7.0

    :Returns:

        `str`
            The version of the CF conventions represented by this
            release of the cfdm.core package.

    **Examples:**

    >>> cfdm.core.CF()
    '1.9'

    """
    return __cf_version__


def deepcopy(x):
    """Use pickle/unpickle to deep copy an object.

    For the types of inputs expected, pickle/unpickle should a) work and
    b) be "not slower, sometimes much faster" than `copy.deepcopy`.

    """
    return loads(dumps(x))
