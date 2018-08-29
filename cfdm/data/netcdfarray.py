from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import str
from future.utils import with_metaclass

import abc
import os
import operator
import urllib.parse

import numpy
import netCDF4

#from .array import Array
from . import abstract
from functools import reduce

class NetCDFArray(with_metaclass(abc.ABCMeta, abstract.Array)):
#class NetCDFArray(Array):
    '''An array stored in a netCDF file.
    
**Initialization**

:Parameters:

    file: `str`
        The netCDF file name in normalized, absolute form.

    dtype: `numpy.dtype`
        The numpy data type of the data array.

    ndim: `int`
        Number of dimensions in the data array.

    shape: `tuple`
        The data array's dimension sizes.

    size: `int`
        Number of elements in the data array.

    ncvar: `str`, optional
        The netCDF variable name containing the data array. Must be
        set if *varid* is not set.

    varid: `int`, optional
        The netCDF ID of the variable containing the data array. Must
        be set if *ncvar* is not set. Ignored if *ncvar* is set.

#    ragged: `int`, optional
#        Reduction in logical rank due to ragged array representation.
#
#    gathered: `int`, optional
#        Reduction in logical rank due to compression by gathering.

:Examples:

>>> import netCDF4
>>> import os
>>> nc = netCDF4.Dataset('file.nc', 'r')
>>> v = nc.variable['tas']
>>> a = NetCDFFileArray(file=os.path.abspath('file.nc'), ncvar='tas',
                        dtype=v.dtype, ndim=v.ndim, shape=v.shape,
                        size=v.size)

    '''

    def __init__(self, filename=None, ncvar=None, dtype=None,
                 ndim=None, shape=None, size=None, varid=None):
        '''
        
**Initialization**

:Parameters:

    file: `str`
        The netCDF file name in normalized, absolute form.

    dtype: `numpy.dtype`
        The numpy data type of the data array.

    ndim: `int`
        Number of dimensions in the data array.

    shape: `tuple`
        The data array's dimension sizes.

    size: `int`
        Number of elements in the data array.

'''
        self._nc = None
        
        # By default, close the netCDF file after data array access
        self._close = True

        if filename is not None:
            u = urllib.parse.urlparse(filename)
            if u.scheme == '':
                filename = os.path.abspath(filename)

            self.filename = filename
        #--- End: def
        
        self._ncvar = ncvar
        self._varid = varid
        
        if ndim is not None:
            self._ndim = ndim
        
        if size is not None:
            self._size = size

        if shape is not None:
            self._shape = shape

        if dtype is not None:
            self._dtype = dtype
    #--- End: def
            
    def __getitem__(self, indices):
        '''x.__getitem__(indices) <==> x[indices]

Returns a numpy array that does not share memory with the un-indexed
array on disk.

        '''
        nc = self.open()
        
#        indices = tuple(self.parse_indices(indices))
        
        ncvar = self.ncvar
        if ncvar is not None:
            # Get the variable by name
            array = nc.variables[ncvar][indices]
        else:
            # Get the variable by netCDF ID
            varid = self.varid
            for value in nc.variables.values():
                if value._varid == varid:
                    array = value[indices]
                    break
        #--- End: if

        if not self.ndim:
            # Hmm netCDF4 has a thing for making scalar size 1 , 1d
            array = array.squeeze()

        # ------------------------------------------------------------
        # If approriate, collapse (by concatenation) the outermost
        # (fastest varying) dimension of string valued array into
        # memory. E.g. [['a','b','c']] becomes ['abc']
        # ------------------------------------------------------------
        if array.dtype.kind in ('S', 'U'): # == 'S' and array.ndim > (self.ndim -
                                                 #    getattr(self, 'gathered', 0) -
                                                 #    getattr(self, 'ragged', 0)):
            if array.dtype.kind == 'U':
                array = array.astype('S')
            
            array = netCDF4.chartostring(array)
            shape = array.shape
#            array.resize((array.size,))
            array = numpy.array([x.rstrip() for x in array.flat], dtype='S') #array.dtype)
            array = numpy.reshape(array, shape)
            array = numpy.ma.masked_where(array==b'', array)

#            array.set_fill_value('')
#            strlen = array.shape[-1]
#            
#            new_shape = array.shape[0:-1]
#            new_size  = int(reduce(operator.mul, new_shape, 1))
#            
#            array = numpy.ma.resize(array, (new_size, strlen))
#            
#            array = array.filled(fill_value='')
#            print('array=', array)
#            array = numpy.array([''.join(x).rstrip() for x in array],
#                                dtype='S{0}'.format(strlen))
#            
#            array = array.reshape(new_shape)
#            
#            array = numpy.ma.where(array=='', numpy.ma.masked, array)
        #--- End: if

        if self._close:
            # Close the netCDF file
            self.close()

        return array
    #--- End: def

    def __repr__(self):
        '''

x.__repr__() <==> repr(x)

'''      
        return "<{0}: {1}>".format(self.__class__.__name__, str(self))
    #--- End: def
     
    def __str__(self):
        '''

x.__str__() <==> str(x)

'''      
        name = self.ncvar
        if name is None:
            name = "varid={0}".format(self.varid)
        else:
            name = "variable={0}".format(name)

        return "file={0} {1} shape={2}".format(self.filename, name, self.shape)
    #--- End: def

    @property
    def ndim(self):
         return self._ndim
    
    @property
    def dtype(self):
         return self._dtype
    
    @property
    def size(self):
         return self._size

    @property
    def shape(self):
         return self._shape

    @property
    def ncvar(self):
         return self._ncvar
    
    @property
    def varid(self):
         return self._varid
    
#    @property
#    def isunique(self):
#        '''
#        '''
#        return True

    def close(self):
        '''Close the `netCDF4.Dataset` for the file containing the data.

:Returns:

    `None`

:Examples:

>>> f.close()

        '''
        nc = self._nc
        if nc is None:
            return
        
        nc.close()    
        self._nc = None
    #--- End: def

    @classmethod
    def file_open(cls, filename, mode, fmt=None):
        '''Return an open `netCDF4.Dataset` for a netCDF file.

:Returns:

    out: `netCDF4.Dataset`

:Examples:

>>> nc = f.file_open(filename, 'r')
>>> nc
<netCDF4.Dataset at 0x115a4d0>

>>> nc = f.file_open(filename, 'w')
>>> nc
<netCDF4.Dataset at 0x345c9e7>

        '''
        try:        
            return netCDF4.Dataset(filename, mode, format=fmt)
        except RuntimeError as error:
            raise RuntimeError("{}: {}".format(error, filename))        
    #--- End: def

    def get_array(self):
        '''
        '''
        return self[...]
    
    def open(self):
        '''Return an open `netCDF4.Dataset` for the file containing the array.

:Returns:

    out: `netCDF4.Dataset`

:Examples:

>>> f.open()
<netCDF4.Dataset at 0x115a4d0>

        '''
        nc = self._nc
        if nc is None:
            nc = self.file_open(self.filename, 'r')            
            self._nc = nc
            
        return nc
    #--- End: def

#--- End: class
