from __future__ import print_function
from future import standard_library
standard_library.install_aliases()
from builtins import zip
from builtins import str
import os
import sys

from collections import Iterable

from itertools   import zip_longest, product
from platform    import system, platform, python_version
from urllib.parse    import urlparse as urlparse_urlparse
from urllib.parse    import urljoin  as urlparse_urljoin

import netCDF4
import numpy
import future

from . import __version__, __cf_version__, __file__

from .constants import CONSTANTS

def _numpy_allclose(a, b, rtol=None, atol=None):
    '''

Returns True if two broadcastable arrays have equal values to within
numerical tolerance, False otherwise.

The tolerance values are positive, typically very small numbers. The
relative difference (``rtol * abs(b)``) and the absolute difference
``atol`` are added together to compare against the absolute difference
between ``a`` and ``b``.

:Parameters:

    a, b : array_like
        Input arrays to compare.

    atol : float, optional
        The absolute tolerance for all numerical comparisons, By
        default the value returned by the `ATOL` function is used.

    rtol : float, optional
        The relative tolerance for all numerical comparisons, By
        default the value returned by the `RTOL` function is used.

:Returns:

    out: `bool`
        Returns True if the arrays are equal, otherwise False.

**Examples**

>>> cf._numpy_allclose([1, 2], [1, 2])
True
>>> cf._numpy_allclose(numpy.array([1, 2]), numpy.array([1, 2]))
True
>>> cf._numpy_allclose([1, 2], [1, 2, 3])
False
>>> cf._numpy_allclose([1, 2], [1, 4])
False

>>> a = numpy.ma.array([1])
>>> b = numpy.ma.array([2])
>>> a[0] = numpy.ma.masked
>>> b[0] = numpy.ma.masked
>>> cf._numpy_allclose(a, b)
True

'''

    # THIS IS WHERE SOME NUMPY FUTURE WARNINGS ARE COMING FROM
    
    a_is_masked = numpy.ma.isMA(a)
    b_is_masked = numpy.ma.isMA(b)
#    print 'a_is_masked   , b_is_masked ', a_is_masked   , b_is_masked    
    if not (a_is_masked or b_is_masked):
        try:            
            return numpy.allclose(a, b, rtol=rtol, atol=atol)
        except (IndexError, NotImplementedError, TypeError):
            return numpy.all(a == b)
    else:
        if a_is_masked and b_is_masked:
            # a and b are both masked arrays
            if (a.mask != b.mask).any():
                return False
        elif not ((a_is_masked and not a.mask.any()) or
                  (b_is_masked and not b.mask.any())):
            return False

        try:
            return numpy.ma.allclose(a, b, rtol=rtol, atol=atol)
        except (IndexError, NotImplementedError, TypeError):
            out = numpy.ma.all(a == b)
            if out is numpy.ma.masked:
                return True
            else:
                return out
#--- End: def

def _numpy_isclose(a, b, rtol=None, atol=None):
    '''Returns a boolean array where two broadcastable arrays are
element-wise equal within a tolerance.

The tolerance values are positive, typically very small numbers. The
relative difference (``rtol * abs(b)``) and the absolute difference
``atol`` are added together to compare against the absolute difference
between ``a`` and ``b``.

:Parameters:

    a, b: array_like
        Input arrays to compare.

    atol: `float`, optional
        The absolute tolerance for all numerical comparisons, By
        default the value returned by the `ATOL` function is used.

    rtol: `float`, optional
        The relative tolerance for all numerical comparisons, By
        default the value returned by the `RTOL` function is used.

:Returns:

    out: `numpy.ndarray`

**Examples**
    '''      
    try:
        return numpy.isclose(a, b, rtol=rtol, atol=atol)
    except (IndexError, NotImplementedError, TypeError):
        return a == b
#--- End: def

#def parse_indices(shape, indices):
#    '''
#
#:Parameters:
#
#    shape: sequence of `ints`
#
#    indices: `tuple` (not a `list`!)
#
#:Returns:
#
#    out: `list`
#
#**Examples**
#
#'''
#    parsed_indices = []
#    roll           = {}
#    flip           = []
#    compressed_indices = []
#
#    if not isinstance(indices, tuple):
#        indices = (indices,)
#
#    # Initialize the list of parsed indices as the input indices with any
#    # Ellipsis objects expanded
#    length = len(indices)
#    n = len(shape)
#    ndim = n
#    for index in indices:
#        if index is Ellipsis:
#            m = n - length + 1
#            parsed_indices.extend([slice(None)] * m)
#            n -= m            
#        else:
#            parsed_indices.append(index)
#            n -= 1
#
#        length -= 1
#    #--- End: for
#    len_parsed_indices = len(parsed_indices)
#
#    if ndim and len_parsed_indices > ndim:
#        raise IndexError("Invalid indices %s for array with shape %s" %
#                         (parsed_indices, shape))
#
#    if len_parsed_indices < ndim:
#        parsed_indices.extend([slice(None)]*(ndim-len_parsed_indices))
#
#    if not ndim and parsed_indices:
#        raise IndexError("Scalar array can only be indexed with () or Ellipsis")
#
#    for i, (index, size) in enumerate(zip(parsed_indices, shape)):
#        is_slice = False
#
#        if isinstance(index, slice):            
#            is_slice = True
#
#        elif isinstance(index, (int, int)):
#            if index < 0: 
#                index += size
#
#            index = slice(index, index+1, 1)
#            is_slice = True
#        else:
#            convert2positve = True
#            if getattr(getattr(index, 'dtype', None), 'kind', None) == 'b':
#                # Convert booleans to non-negative integers. We're
#                # assuming that anything with a dtype attribute also
#                # has a size attribute.
#                if index.size != size:
#                    raise IndexError(
#"Invalid indices {} for array with shape {}".format(parsed_indices, shape))
#                
#                index = numpy.where(index)[0]
#                convert2positve = False
#            #--- End: if
#
#            if not numpy.ndim(index):
#                if index < 0:
#                    index += size
#
#                index = slice(index, index+1, 1)
#                is_slice = True
#            else:
#                len_index = len(index)
#                if len_index == 1:                
#                    index = index[0]
#                    if index < 0:
#                        index += size
#                    
#                    index = slice(index, index+1, 1)
#                    is_slice = True
#                elif len_index:
#                    if convert2positve:
#                        # Convert to non-negative integer numpy array
#                        index = numpy.array(index)
#                        index = numpy.where(index < 0, index+size, index)
#    
#                    steps = index[1:] - index[:-1]
#                    step = steps[0]
#                    if step and not (steps - step).any():
#                        # Replace the numpy array index with a slice
#                        if step > 0:
#                            start, stop = index[0], index[-1]+1
#                        elif step < 0:
#                            start, stop = index[0], index[-1]-1
#                            
#                        if stop < 0:
#                            stop = None
#                                
#                        index = slice(start, stop, step)
#                        is_slice = True
#                else:
#                    raise IndexError(
#                        "Invalid indices {} for array with shape {}".format(
#                            parsed_indices, shape))                
#            #--- End: if
#        #--- End: if
#        
#        parsed_indices[i] = index    
#    #--- End: for
#
#    return parsed_indices
##--- End: def

#def get_subspace(array, indices):
#    '''
#
#:Parameters:
#
#    array : numpy array
#
#    indices : list
#
#Subset the input numpy array with the given indices. Indexing is similar to
#that of a numpy array. The differences to numpy array indexing are:
#
#1. An integer index i takes the i-th element but does not reduce the rank of
#   the output array by one.
#
#2. When more than one dimension's slice is a 1-d boolean array or 1-d sequence
#   of integers then these indices work independently along each dimension
#   (similar to the way vector subscripts work in Fortran).
#
#indices must contain an index for each dimension of the input array.
#'''
#    gg = [i for i, x in enumerate(indices) if not isinstance(x, slice)]
#    len_gg = len(gg)
#
#    if len_gg < 2:
#        # ------------------------------------------------------------
#        # At most one axis has a list-of-integers index so we can do a
#        # normal numpy subspace
#        # ------------------------------------------------------------
#        return array[tuple(indices)]
#
#    else:
#        # ------------------------------------------------------------
#        # At least two axes have list-of-integers indices so we can't
#        # do a normal numpy subspace
#        # ------------------------------------------------------------
#        if numpy.ma.isMA(array):
#            take = numpy.ma.take
#        else:
#            take = numpy.take
#
#        indices = indices[:]
#        for axis in gg:
#            array = take(array, indices[axis], axis=axis)
#            indices[axis] = slice(None)
#        #--- End: for
#
#        if len_gg < len(indices):
#            array = array[tuple(indices)]
#
#        return array
#    #--- End: if
#
##--- End: def

def ATOL(*atol):
    '''The tolerance on absolute differences when testing for numerically
tolerant equality.

Two numbers ``x`` and ``y`` are considered equal if ``abs(x-y) <= atol
+ rtol*abs(y)``, where atol (the tolerance on absolute differences)
and rtol (the tolerance on relative differences) are positive,
typically very small numbers. By default both are set to the system
epsilon (the difference between 1 and the least value greater than 1
that is representable as a float).

.. versionadded:: 1.7

.. seealso:: `cfdm.RTOL`

:Parameters:

    atol: `float`, optional
        The new value of absolute tolerance. The default is to not
        change the current value.

:Returns:

    out: `float`
        The value prior to the change, or the current value if no
        new value was specified.

**Examples**

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

Two numbers ``x`` and ``y`` are considered equal if ``abs(x-y) <= atol
+ rtol*abs(y)``, where atol (the tolerance on absolute differences)
and rtol (the tolerance on relative differences) are positive,
typically very small numbers. By default both are set to the system
epsilon (the difference between 1 and the least value greater than 1
that is representable as a float).

.. versionadded:: 1.7

.. seealso:: `cfdm.ATOL`

:Parameters:

    rtol: `float`, optional
        The new value of relative tolerance. The default is to not
        change the current value.

:Returns:

    out: `float`
        The value prior to the change, or the current value if no
        new value was specified.

**Examples**

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

#def equals(x, y, rtol=None, atol=None, **kwargs): #ignore_data_type=False,
##           ignore_fill_value=False, ignore_type=False,
##           traceback=False):
#    '''True if and only if two objects are logically equal.
#
#If the first argument, *x*, has an :meth:`equals` method then it is
#used, and in this case ``equals(x, y)`` is equivalent to
#``x.equals(y)``. Else if the second argument, *y*, has an
#:meth:`equals` method then it is used, and in this case ``equals(x,
#y)`` is equivalent to ``y.equals(x)``.
#
#:Parameters:
#
#    x, y :
#        The objects to compare for equality.
#
#    atol : float, optional
#        The absolute tolerance for all numerical comparisons, By
#        default the value returned by the `ATOL` function is used.
#
#    rtol : float, optional
#        The relative tolerance for all numerical comparisons, By
#        default the value returned by the `RTOL` function is used.
#
#    ignore_fill_value : bool, optional
#        If True then `Data` arrays with different fill values are
#        considered equal. By default they are considered unequal.
#
#    traceback : bool, optional
#        If True then print a traceback highlighting where the two
#        objects differ.
#
#:Returns:
#
#    out: `bool`
#        Whether or not the two objects are equal.
#
#**Examples**
#
#>>> f
#<CF Field: rainfall_rate(latitude(10), longitude(20)) kg m2 s-1>
#>>> cfdm.equals(f, f)
#True
#
#>>> cfdm.equals(1.0, 1.0)
#True
#>>> cfdm.equals(1.0, 33)
#False
#
#>>> cfdm.equals('a', 'a')
#True
#>>> cfdm.equals('a', 'b')
#False
#
#>>> type(x), x.dtype
#(<type 'numpy.ndarray'>, dtype('int64'))
#>>> y = x.copy()
#>>> cfdm.equals(x, y)
#True
#>>> cfdm.equals(x, x+1)
#False
#
#>>> class A(object):
#...     pass
#...
#>>> a = A()
#>>> b = A()
#>>> cfdm.equals(a, a)
#True
#>>> cfdm.equals(a, b)
#False
#
#    '''
#    eq = getattr(x, 'equals', None)
#
#    if callable(eq):
#        # x has a callable equals method
#        return eq(y, rtol=rtol, atol=atol, **kwargs)
#
#    eq = getattr(y, 'equals', None)
#    if callable(eq):
#        # y has a callable equals method
#        return eq(x, rtol=rtol, atol=atol, **kwargs)
# 
#    if isinstance(x, numpy.ndarray) or isinstance(y, numpy.ndarray):
#        if numpy.shape(x) != numpy.shape(y):
#            return False
#
#        if rtol is None:
#            rtol = RTOL()
#        if atol is None:
#            atol = ATOL()
#                
#        return _numpy_allclose(x, y, rtol=rtol, atol=atol)
#
#    else:
#        return x == y
##--- End: def

#def abspath(filename):
#    '''
#
#Return a normalized absolute version of a file name.
#
#If a string containing URL is provided then it is returned unchanged.
#
#:Parameters:
#
#    filename: `str`
#        The name of the file.
#
#:Returns:
#
#    out: `str`
#        The normalized absolutized version of *filename*.
# 
#**Examples**
#
#>>> import os
#>>> os.getcwd()
#'/data/archive'
#>>> abspath('file.nc')
#'/data/archive/file.nc'
#>>> abspath('..//archive///file.nc')
#'/data/archive/file.nc'
#>>> abspath('http://data/archive/file.nc')
#'http://data/archive/file.nc'
#
#'''
#    u = urlparse_urlparse(filename)
#    if u.scheme != '':
#        return filename
#
#    return os.path.abspath(filename)
##--- End: def

def allclose(x, y, rtol=None, atol=None):
    '''

Returns True if two broadcastable arrays have equal values to within
numerical tolerance, False otherwise.

The tolerance values are positive, typically very small numbers. The
relative difference (``rtol * abs(b)``) and the absolute difference
``atol`` are added together to compare against the absolute difference
between ``a`` and ``b``.

:Parameters:

    x, y: array_like
        Input arrays to compare.

    atol: `float`, optional
        The absolute tolerance for all numerical comparisons, By
        default the value returned by the `ATOL` function is used.

    rtol: `float`, optional
        The relative tolerance for all numerical comparisons, By
        default the value returned by the `RTOL` function is used.

:Returns:

    out: `bool`
        Returns True if the arrays are equal, otherwise False.

**Examples**

'''    
    if rtol is None:
        rtol = RTOL()
    if atol is None:
        atol = ATOL()

    allclose = getattr(x, 'allclose', None)
    if callable(allclose):
        # x has a callable allclose method
       return allclose(y, rtol=rtol, atol=atol)

    allclose = getattr(y, 'allclose', None)
    if callable(allclose):
        # y has a callable allclose method
       return allclose(x, rtol=rtol, atol=atol)

    # x nor y has a callable allclose method
    return _numpy_allclose(x, y, rtol=rtol, atol=atol)
#--- End: def

def environment(display=True):
    '''Return the names, versions and paths of all dependencies.

.. versionadded:: 1.7

:Parameters:

    display: `bool`, optional
        If False then return the description of the environment as a
        string. By default the description is printed.

:Returns:

    out:
        If *display* is True then the description of the environment
        is printed and `None` is returned. Otherwise the description
        is returned as a string.

**Examples:**

>>> cfdm.environment()
Platform: Linux-4.15.0-38-generic-x86_64-with-debian-stretch-sid
python: 2.7.15 /home/user/anaconda2/bin/python
HDF5 library: 1.10.1
netcdf library: 4.6.1
netCDF4: 1.4.0 /home/user/anaconda2/lib/python2.7/site-packages/netCDF4/__init__.pyc
numpy: 1.11.3 /home/user/anaconda2/lib/python2.7/site-packages/numpy/__init__.pyc
future: 0.16.0 /home/user/anaconda2/lib/python2.7/site-packages/future/__init__.pyc
cfdm: 1.7.1 /home/user/cfdm/cfdm/__init__.pyc

    '''
    out = []
    out.append('Platform: ' + str(platform()))
    out.append('python: ' + str(python_version() + ' ' + str(sys.executable)))

    out.append('HDF5 library: ' + str(netCDF4. __hdf5libversion__))
    out.append('netcdf library: ' + str(netCDF4.__netcdf4libversion__))

    out.append('netCDF4: ' + str(netCDF4.__version__) + ' ' + str(os.path.abspath(netCDF4.__file__)))
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
    '''Return the version of the CF conventions.

.. versionadded:: 1.7

:Returns:

    out:`str`
        The version of the CF conventions.

**Examples:**

>>> cfdm.CF()
'1.7'
    '''
    return __cf_version__
#--- End: def
