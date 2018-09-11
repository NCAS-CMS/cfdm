from future import standard_library
standard_library.install_aliases()
from builtins import str
#from functools import reduce

import os
#import operator
import urllib.parse

import numpy
import netCDF4

from . import abstract


class NetCDFArray(abstract.Array):
    '''A container for an array stored in a netCDF file.
    
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

:Examples:

>>> import netCDF4
>>> nc = netCDF4.Dataset('file.nc', 'r')
>>> v = nc.variable['tas']
>>> a = NetCDFFileArray(file='file.nc', ncvar='tas', dtype=v.dtype, 
...                     ndim=v.ndim, shape=v.shape, size=v.size)

'''
        self._netcdf = None
        
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
array.

        '''
        netcdf = self.open()
        
#        indices = tuple(self.parse_indices(indices))
        
        ncvar = self.ncvar
        if ncvar is not None:
            # Get the variable by name
            array = netcdf.variables[ncvar][indices]
        else:
            # Get the variable by netCDF ID
            varid = self.varid
            for value in netcdf.variables.values():
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

    # ----------------------------------------------------------------
    # Attributes
    # ----------------------------------------------------------------
    @property
    def netcdf(self):
        netcdf =  self._netcdf
    
    @property
    def dtype(self):
        '''Data-type of the data elements.
         
:Examples:

>>> a.dtype
dtype('float64')
>>> print(type(a.dtype))
<type 'numpy.dtype'>

        '''
        return self._dtype
    #--- End: def
    
    @property
    def ndim(self):
        '''Number of array dimensions
        
:Examples:

>>> a.shape
(73, 96)
>>> a.ndim
2
>>> a.size
7008

>>> a.shape
(1, 1, 1)
>>> a.ndim
3
>>> a.size
1

>>> a.shape
()
>>> a.ndim
0
>>> a.size
1
        '''
        return self._ndim
    #--- End: def
    
    @property
    def shape(self):
        '''Tuple of array dimension sizes.

:Examples:

>>> a.shape
(73, 96)
>>> a.ndim
2
>>> a.size
7008

>>> a.shape
(1, 1, 1)
>>> a.ndim
3
>>> a.size
1

>>> a.shape
()
>>> a.ndim
0
>>> a.size
1
        '''
        return self._shape
    #--- End: def
    
    @property
    def size(self):        
        '''Number of elements in the array.

:Examples:

>>> a.shape
(73, 96)
>>> a.size
7008
>>> a.ndim
2

>>> a.shape
(1, 1, 1)
>>> a.ndim
3
>>> a.size
1

>>> a.shape
()
>>> a.ndim
0
>>> a.size
1

        '''
        return self._size
    #--- End: def
    
    @property
    def ncvar(self):
         return self._ncvar
    
    @property
    def varid(self):
         return self._varid
    
    def close(self):
        '''Close the `netCDF4.Dataset` for the file containing the data.

:Returns:

    out: `netCDF4.Dataset`

:Examples:

>>> a.close()

        '''
        netcdf = self._netcdf
        if netcdf is  None:
            return
        
        netcdf.close()    
        self._netcdf = None
    #--- End: def

#    @classmethod
#    def file_open(cls, filename, mode, fmt=None):
#        '''Return an open `netCDF4.Dataset` for a netCDF file.
#
#:Returns:
#
#    out: `netCDF4.Dataset`
#
#:Examples:
#
#>>> nc = f.file_open(filename, 'r')
#>>> nc
#<netCDF4.Dataset at 0x115a4d0>
#
#>>> nc = f.file_open(filename, 'w')
#>>> nc
#<netCDF4.Dataset at 0x345c9e7>
#
#        '''
#        try:        
#            return netCDF4.Dataset(filename, mode, format=fmt)
#        except RuntimeError as error:
#            raise RuntimeError("{}: {}".format(error, filename))        
#    #--- End: def

    def get_array(self):
        '''Return an independent numpy array containing the data.

:Returns:

    out: `numpy.ndarray`
        An independent numpy array of the data.

:Examples:

>>> n = numpy.asanyarray(a)
>>> isinstance(n, numpy.ndarray)
True
        '''
        return self[...]
    #--- End: def
    
    def open(self):
        '''Return an open `netCDF4.Dataset` for the file containing the array.

The returned dataset is also stored internally.

:Returns:

    out: `netCDF4.Dataset`

:Examples:

>>> a.open()
<netCDF4.Dataset at 0x115a4d0>

        '''
        netcdf = self._netcdf
        if netcdf is None:
            try:        
                netcdf = netCDF4.Dataset(self.filename, 'r')
            except RuntimeError as error:
                raise RuntimeError("{}: {}".format(error, filename))        

#            nc = self.file_open(self.filename, 'r')            
            self._netcdf = netcdf
            
        return netcdf
    #--- End: def

#--- End: class
