import operator
import sys

import numpy
import netCDF4

from ..functions import parse_indices, abspath

_debug = False

# ====================================================================
#
# FileArray object
# 
# ====================================================================

class Array(object):
    '''An array stored in a file.
    
.. note:: Subclasses must define the following methods:
          `!__getitem__`, `!__str__`, `!close` and `!open`.

    '''
    def __init__(self, **kwargs):
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
        self.__dict__ = kwargs

#        f = getattr(self, 'file', None)
#        if f is not None:
#            self.file = abspath(f)
    #--- End: def
            
    def __deepcopy__(self, memo):
        '''

Used if copy.deepcopy is called on the variable.

'''
        return self.copy()
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
        return "shape={0}, dtype={1}".format(self.shape, self.dtype)
    #--- End: def

    def copy(self):
        '''Return a deep copy.

``f.copy() is equivalent to ``copy.deepcopy(f)``.

:Returns:

    out :
        A deep copy.

:Examples:

>>> g = f.copy()

        '''
        C = self.__class__
        new = C.__new__(C)
        new.__dict__ = self.__dict__.copy()
        return new
    #--- End: def
    
    def close(self):
        pass
    #--- End: def

    @classmethod
    def get_subspace(cls, array, indices):
        '''
    
:Parameters:

    array : numpy array

    indices : list

Subset the input numpy array with the given indices. Indexing is similar to
that of a numpy array. The differences to numpy array indexing are:

1. An integer index i takes the i-th element but does not reduce the rank of
   the output array by one.

2. When more than one dimension's slice is a 1-d boolean array or 1-d sequence
   of integers then these indices work independently along each dimension
   (similar to the way vector subscripts work in Fortran).

indices must contain an index for each dimension of the input array.
    '''
        gg = [i for i, x in enumerate(indices) if not isinstance(x, slice)]
        len_gg = len(gg)
    
        if len_gg < 2:
            # ------------------------------------------------------------
            # At most one axis has a list-of-integers index so we can do a
            # normal numpy subspace
            # ------------------------------------------------------------
            return array[tuple(indices)]
    
        else:
            # ------------------------------------------------------------
            # At least two axes have list-of-integers indices so we can't
            # do a normal numpy subspace
            # ------------------------------------------------------------
            if numpy.ma.isMA(array):
                take = numpy.ma.take
            else:
                take = numpy.take
    
            indices = indices[:]
            for axis in gg:
                array = take(array, indices[axis], axis=axis)
                indices[axis] = slice(None)
            #--- End: for
    
            if len_gg < len(indices):
                array = array[tuple(indices)]
    
            return array
        #--- End: if
    #--- End: def

    def open(self, keep_open=False):
        pass
    #--- End: def

#--- End: class

# ====================================================================
#
# Array object
# 
# ====================================================================

class NumpyArray(Array):
    '''An numpy  array.

    '''
    def __init__(self, array=None):
        '''
        
**Initialization**

:Parameters:

    array: `numpy.ndarray`

        '''
        super(NumpyArray, self).__init__(array=array)
    #--- End: def

    def __getitem__(self, indices):
        '''

x.__getitem__(indices) <==> x[indices]

Returns a numpy array.

'''
        if sys.getrefcount(self.array) <= 2:
            array = self.array
        else:
            if numpy.ma.isMA and not self.ndim:
                # This is because numpy.ma.copy doesn't work for
                # scalar arrays (at the moment, at least)
                array = numpy.ma.masked_all((), dtype=self.array.dtype)
                array[...] = self.array
            else:
                array = self.array.copy()
        #--- End: if

        if indices is Ellipsis:
            return array
            
        indices = parse_indices(array.shape, indices)

        return self.get_subspace(array, indices)
    #--- End: def

    @property
    def ndim(self):
        return self.array.ndim

    @property
    def shape(self):
        return self.array.shape

    @property
    def size(self):
        return self.array.size

    @property
    def dtype(self):
        return self.array.dtype

#--- End: class

# ====================================================================
#
# NetCDFArray object
#
# ====================================================================

class NetCDFArray(Array):
    '''A sub-array stored in a netCDF file.
    
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
    def __init__(self, **kwargs):
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
        super(NetCDFArray, self).__init__(**kwargs)

        f = getattr(self, 'file', None)
        if f is not None:
            self.file = abspath(f)
    #--- End: def
            
    def __getitem__(self, indices):
        '''

x.__getitem__(indices) <==> x[indices]

Returns a numpy array.

'''
        nc = self.open()
        
        indices = tuple(parse_indices(self.shape, indices))
        
        ncvar = getattr(self, 'ncvar', None)

        if ncvar is not None:
            # Get the variable by name
            array = nc.variables[ncvar][indices]
        else:
            # Get the variable by netCDF ID
            varid = self.varid
            for value in nc.variables.itervalues():
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
        if array.dtype.kind == 'S' and array.ndim > (self.ndim -
                                                     getattr(self, 'gathered', 0) -
                                                     getattr(self, 'ragged', 0)):
            strlen = array.shape[-1]
            
            new_shape = array.shape[0:-1]
            new_size  = long(reduce(operator.mul, new_shape, 1))
            
            array = numpy.ma.resize(array, (new_size, strlen))
            
            array = array.filled(fill_value='')

            array = numpy.array([''.join(x).rstrip() for x in array],
                                dtype='S%d' % strlen)
            
            array = array.reshape(new_shape)

            array = numpy.ma.where(array=='', numpy.ma.masked, array)
        #--- End: if

        if not getattr(self, 'keep_open', False):
            self.close()
        
        return array
    #--- End: def

    def __repr__(self):
        '''

x.__repr__() <==> repr(x)

'''      
        return "<{0}>".format(self.__class__.__name__, str(self))
    #--- End: def
     
    def __str__(self):
        '''

x.__str__() <==> str(x)

'''
        return "{0} in {1}".format(self.shape, self.file)
    #--- End: def
    
    def __str__(self):
        '''

x.__str__() <==> str(x)

'''      
        name = getattr(self, 'ncvar', None)
        if name is None:
            name = self.varid

        return "%s%s in %s" % (name, self.shape, self.file)
    #--- End: def
    
    def close(self):
        '''Close the file containing the array.

If the file is not open then no action is taken.

:Returns:

    `None`

:Examples:

>>> f.close()

        '''
        nc = getattr(self, 'nc', None)
        if nc is not None:
            nc.close()
            del self.nc

        self.keep_open = False
    #--- End: def

    def open(self, keep_open=False):
        '''

Return a `netCDF4.Dataset` object for the file containing the data
array.

:Returns:

    out: `netCDF4.Dataset`

:Examples:

>>> f.open()
<netCDF4.Dataset at 0x115a4d0>

'''
        nc = getattr(self, 'nc', None)
        if nc is None or not nc.isopen():
            self.nc = self.open_netcdf_file(self.file, 'r')

        self.keep_open = keep_open
        
        return nc
    #--- End: def

    @classmethod
    def open_netcdf_file(cls, filename, mode, fmt=None):
        '''

Return a `netCDF4.Dataset` object for the file containing the data
array.

:Returns:

    out: `netCDF4.Dataset`

:Examples:

>>> f.open_netcdf_file(filename)
<netCDF4.Dataset at 0x115a4d0>

'''        
        try:        
            nc = netCDF4.Dataset(filename, mode, format=fmt)
        except RuntimeError as runtime_error:
            raise RuntimeError("{}: {}".format(runtime_error, filename))        

        return nc
    #--- End: def

#--- End: class

class GatheredArray(Array):
    '''
    '''        
    def __getitem__(self, indices):
        '''
        '''

        array = numpy.ma.masked_all(self.shape, dtype=dtype)
        
        compressed_axes = range(self.sample_axis, array.ndim - (self.gathered_array.ndim - self.sample_axis - 1))
        
        zzz = [reduce(operator.mul, [array.shape[i] for i in compressed_axes[i:]], 1)
               for i in range(1, len(compressed_axes))]
        
        xxx = [[0] * self.indices.size for i in compressed_axes]


        for n, b in enumerate(self.indices.varray):
            if not zzz or b < zzz[-1]:
                xxx[-1][n] = b
                continue
            
            for i, z in enumerate(zzz):
                if b >= z:
                    (a, b) = divmod(b, z)
                    xxx[i][n] = a
                    xxx[-1][n] = b
        #--- End: for

        uncompressed_indices = [slice(None)] * array.ndim        
        for i, x in enumerate(xxx):
            uncompressed_indices[sample_axis+i] = x

        array[tuple(uncompressed_indices)] = self.gathered_array[...]

        if indices is Ellpisis:
            return array

        indices = parse_indices(array.shape, indices)
        array = self.get_subspace(array, indices)
        
        return array
