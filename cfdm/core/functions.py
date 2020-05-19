from __future__ import print_function
from future import standard_library
standard_library.install_aliases()
from builtins import str

import os
import platform
import sys

import netCDF4
import numpy
import future

from . import (__version__,
               __cf_version__,
               __file__)


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
    numpy: 1.16.2 /home/user/anaconda3/lib/python3.7/site-packages/numpy/__init__.py
    cfdm.core: 1.8.0

    >>> environment(paths=False)
    Platform: Linux-4.15.0-72-generic-x86_64-with-debian-stretch-sid
    HDF5 library: 1.10.2
    netcdf library: 4.6.1
    python: 3.7.3
    future: 0.17.1
    netCDF4: 1.5.3
    numpy: 1.16.2
    cfdm.core: 1.8.0

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

    out.append('numpy: ' + str(numpy.__version__))
    if paths:
        out[-1] += ' ' + str(os.path.abspath(numpy.__file__))

    out.append('cfdm.core: ' + str(__version__))
    if paths:
        out[-1] += ' ' + str(os.path.abspath(__file__))

    if display:
        print('\n'.join(out))
    else:
        return out

def CF():
    '''The version of the CF conventions.

    This indicates which version of the CF conventions are represented
    by this release of the cfdm.core package, and therefore the
    version can not be changed.

    .. versionadded:: 1.7.0

    :Returns:

        `str`
            The version of the CF conventions represented by this
            release of the cfdm.core package.

    **Examples:**

    >>> cfdm.core.CF()
    '1.8'

    '''
    return __cf_version__

