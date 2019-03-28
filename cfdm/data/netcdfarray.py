from future import standard_library
standard_library.install_aliases()
from builtins import (str, super)


import os
import urllib.parse

import numpy
import netCDF4

from . import abstract


class NetCDFArray(abstract.Array):
    '''An underlying array stored in a netCDF file.
    
.. versionadded:: 1.7.0

    '''
    def __init__(self, filename=None, ncvar=None, varid=None,
                 dtype=None, ndim=None, shape=None, size=None):
        '''**Initialization**

:Parameters:

    filename: `str`
        The name of the netCDF file containing the array.

    ncvar: `str`, optional
        The name of the netCDF variable containing the array. Required
        unless *varid* is set.

    varid: `int`, optional
        The UNIDATA netCDF interface ID of the variable containing the
        array. Required if *ncvar* is not set, ignored if *ncvar* is
        set.

    dtype: `numpy.dtype`
        The data type of the array.

    shape: `tuple`
        The array dimension sizes.

    size: `int`
        Number of elements in the array.

    ndim: `int`
        The number of array dimensions.

**Examples:**

>>> import netCDF4
>>> nc = netCDF4.Dataset('file.nc', 'r')
>>> v = nc.variable['tas']
>>> a = NetCDFFileArray(filename='file.nc', ncvar='tas', dtype=v.dtype, 
...                     ndim=v.ndim, shape=v.shape, size=v.size)

        '''
        super().__init__(filename=filename, ncvar=ncvar, varid=varid)
        
        self._netcdf = None
        
        # By default, close the netCDF file after data array access
        self._close = True

        if ndim is not None:
            self._set_component('ndim', ndim)
        
        if size is not None:
            self._set_component('size', size)

        if shape is not None:
            self._set_component('shape', shape)

        if dtype is not None:
            self._set_component('dtype', dtype)
    #--- End: def
            
    def __getitem__(self, indices):
        '''x.__getitem__(indices) <==> x[indices]

Returns a subspace of the array as an independent numpy array.

The indices that define the subspace must be either `Ellipsis` or a
sequence that contains an index for each dimension. In the latter
case, each dimension's index must either be a `slice` object or a
sequence of two or more integers.

Indexing is similar to numpy indexing. The only difference to numpy
indexing (given the restrictions on the type of indices allowed) is:

  * When two or more dimension's indices are sequences of integers
    then these indices work independently along each dimension
    (similar to the way vector subscripts work in Fortran).

        '''
        netcdf = self.open()
        
#        indices = tuple(self.parse_indices(indices))
        
        ncvar = self.get_ncvar()
        if ncvar is not None:
            # Get the variable by name
#            print ('XXX', ncvar, indices)
            array = netcdf.variables[ncvar][indices]
        else:
            # Get the variable by netCDF ID
            varid = self.get_varid()
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
        name = self.get_ncvar()
        if name is None:
            name = "varid={0}".format(self.get_varid())
        else:
            name = "variable={0}".format(name)

        return "file={0} {1} shape={2}".format(self.get_filename(),
                                               name, self.shape)
    #--- End: def

    # ----------------------------------------------------------------
    # Attributes
    # ----------------------------------------------------------------
    @property
    def dtype(self):
        '''Data-type of the data elements.
         
**Examples:**

>>> a.dtype
dtype('float64')
>>> print(type(a.dtype))
<type 'numpy.dtype'>

        '''
        return self._get_component('dtype')
    #--- End: def
    
    @property
    def ndim(self):
        '''Number of array dimensions
        
**Examples:**

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
        return self._get_component('ndim')
    #--- End: def
    
    @property
    def shape(self):
        '''Tuple of array dimension sizes.

**Examples:**

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
        return self._get_component('shape')
    #--- End: def
    
    @property
    def size(self):        
        '''Number of elements in the array.

**Examples:**

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
        return self._get_component('size')
    #--- End: def
    
    def get_filename(self):
        '''The name of the netCDF file containing the array.

**Examples:**

>>> a.get_filename()
'file.nc'

        '''
        return self._get_component('filename')
    #--- End: def
    
    def get_ncvar(self):
        '''The name of the netCDF variable containing the array.

**Examples:**

>>> print(a.netcdf)
'tas'
>>> print(a.varid)
None

>>> print(a.netcdf)
None
>>> print(a.varid)
4

        '''
        return self._get_component('ncvar')
    #--- End: def
    
    def get_varid(self):
        '''The UNIDATA netCDF interface ID of the variable containing the
array.

**Examples:**

>>> print(a.netcdf)
'tas'
>>> print(a.varid)
None

>>> print(a.netcdf)
None
>>> print(a.varid)
4

        '''
        return self._get_component('varid')
    #--- End: def
    
    # ----------------------------------------------------------------
    # Methods
    # ----------------------------------------------------------------
    def close(self):
        '''Close the `netCDF4.Dataset` for the file containing the data.

:Returns:

    `None`

**Examples:**

>>> a.close()

        '''
        netcdf = self._netcdf
        if netcdf is  None:
            return
        
        netcdf.close()    
        self._netcdf = None
    #--- End: def

    @property
    def array(self):
        '''Return an independent numpy array containing the data.

:Returns:

    `numpy.ndarray`
        An independent numpy array of the data.

**Examples:**

>>> n = numpy.asanyarray(a)
>>> isinstance(n, numpy.ndarray)
True

        '''
        return self[...]
    #--- End: def
    
    def open(self):
        '''Return an open `netCDF4.Dataset` for the file containing the array.

:Returns:

    `netCDF4.Dataset`

**Examples:**

>>> netcdf = a.open()
>>> variable = netcdf.variables[a.get_ncvar()]
>>> variable.getncattr('standard_name')
'eastward_wind'

        '''
        netcdf = self._netcdf
        if netcdf is None:
            try:        
                netcdf = netCDF4.Dataset(self.get_filename(), 'r')
            except RuntimeError as error:
                raise RuntimeError("{}: {}".format(error, filename))        

            self._netcdf = netcdf
            
        return netcdf
    #--- End: def

#--- End: class
