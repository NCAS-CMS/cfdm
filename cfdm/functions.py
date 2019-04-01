from __future__ import print_function
from future import standard_library
standard_library.install_aliases()
from builtins import str

import os
import sys

from platform import platform, python_version

import netCDF4
import cftime
import numpy
import future

from . import (__version__,
               __cf_version__,
               __file__)

from .constants import CONSTANTS


def ATOL(*atol):
    '''The tolerance on absolute differences when testing for numerically
tolerant equality.

Two real numbers ``x`` and ``y`` are considered equal if ``abs(x-y) <=
atol + rtol*abs(y)``, where atol (the tolerance on absolute
differences) and rtol (the tolerance on relative differences) are
positive, typically very small numbers. By default both are set to the
system epsilon (the difference between 1 and the least value greater
than 1 that is representable as a float).

.. versionadded:: 1.7.0

.. seealso:: `cfdm.RTOL`

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
>>> ATOL(old)
1e-10
>>> ATOL()
2.220446049250313e-16

    '''
    old = CONSTANTS['ATOL']
    if atol:
        CONSTANTS['ATOL'] = atol[0]

    return old
#--- End: def

def RTOL(*rtol):    
    '''The tolerance on relative differences when testing for numerically
tolerant equality.

Two real numbers ``x`` and ``y`` are considered equal if ``abs(x-y) <=
atol + rtol*abs(y)``, where atol (the tolerance on absolute
differences) and rtol (the tolerance on relative differences) are
positive, typically very small numbers. By default both are set to the
system epsilon (the difference between 1 and the least value greater
than 1 that is representable as a float).

.. versionadded:: 1.7.0

.. seealso:: `cfdm.ATOL`

:Parameters:

    rtol: `float`, optional
        The new value of relative tolerance. The default is to not
        change the current value.

:Returns:

    `float`
        The value prior to the change, or the current value if no
        new value was specified.

**Examples:**

>>> cfdm.RTOL()
2.220446049250313e-16
>>> old = RTOL(1e-10)
>>> RTOL(old)
1e-10
>>> cfdm.RTOL()
2.220446049250313e-16

    '''
    old = CONSTANTS['RTOL']
    if rtol:
        CONSTANTS['RTOL'] = rtol[0]

    return old
#--- End: def


def environment(display=True):
    '''Return the names, versions and paths of all dependencies.

.. versionadded:: 1.7.0

:Parameters:

    display: `bool`, optional
        If False then return the description of the environment as a
        string. By default the description is printed.

:Returns:

    `None` or `str`
        If *display* is True then the description of the environment
        is printed and `None` is returned. Otherwise the description
        is returned as a string.

**Examples:**

>>> cfdm.environment()
Platform: Linux-4.15.0-43-generic-x86_64-with-debian-stretch-sid
python: 3.6.5 /home/david/anaconda3/bin/python
HDF5 library: 1.10.2
netcdf library: 4.6.1
netCDF4: 1.4.0 /home/user/anaconda3/lib/python3.6/site-packages/netCDF4/__init__.py
cftime: 1.0.0b1 /home/user/anaconda3/lib/python3.6/site-packages/cftime/__init__.py
numpy: 1.14.3 /home/user/anaconda3/lib/python3.6/site-packages/numpy/__init__.py
future: 0.16.0 /home/user/anaconda3/lib/python3.6/site-packages/future/__init__.py
cfdm: 1.7.0 /home/user/cfdm/cfdm/__init__.py

    '''
    out = []
    out.append('Platform: ' + str(platform()))
    out.append('python: ' + str(python_version() + ' ' + str(sys.executable)))

    out.append('HDF5 library: ' + str(netCDF4. __hdf5libversion__))
    out.append('netcdf library: ' + str(netCDF4.__netcdf4libversion__))

    out.append('netCDF4: ' + str(netCDF4.__version__) + ' ' + str(os.path.abspath(netCDF4.__file__)))
    out.append('cftime: ' + str(cftime.__version__) + ' ' + str(os.path.abspath(cftime.__file__)))
    out.append('numpy: ' + str(numpy.__version__) + ' ' + str(os.path.abspath(numpy.__file__)))
    out.append('future: ' + str(future.__version__) + ' ' + str(os.path.abspath(future.__file__)))

    out.append('cfdm: ' + str(__version__) + ' ' + str(os.path.abspath(__file__)))
    
    out = '\n'.join(out)

    if display:
        print(out)
    else:
        return out
#--- End: def

def CF():
    '''The version of the CF conventions.

This indicates which version of the CF conventions are represented by
this release of the cfdm package, and therefore the version can not be
changed.

.. versionadded:: 1.7.0

:Returns:

    `str`
        The version of the CF conventions represented by this release
        of the cfdm package.

**Examples:**

>>> cfdm.CF()
'1.7'

    '''
    return __cf_version__
#--- End: def
