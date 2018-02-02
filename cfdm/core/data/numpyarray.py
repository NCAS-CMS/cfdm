from collections import abc

import operator
import sys

import numpy
import netCDF4

from ..functions import abspath, open_files_threshold_exceeded


_file_to_fh_read  = {}
_file_to_fh_write = {}

_debug = False

# ====================================================================
#
# FileArray object
# 
# ====================================================================

class Array(object):
    '''An array.
    
    '''
    __metaclass__ = abc.ABCMeta

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

    @abc.abstractproperty
    def isunique(self):
        pass
    
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

    @abc.abstractmethod
    def close(self):
        '''
        '''
        pass
    #--- End: def

#    def parse_indices(self, indices):
#        '''
#    
#:Parameters:
#    
#    indices: `tuple` (not a `list`!)
#    
#:Returns:
#    
#    out: `list`
#    
#:Examples:
#    
#    '''
#        shape = self.shape
#        
#        parsed_indices = []
#        roll           = {}
#        flip           = []
#        compressed_indices = []
#    
#        if not isinstance(indices, tuple):
#            indices = (indices,)
#    
#        # Initialize the list of parsed indices as the input indices with any
#        # Ellipsis objects expanded
#        length = len(indices)
#        n = len(shape)
#        ndim = n
#        for index in indices:
#            if index is Ellipsis:
#                m = n - length + 1
#                parsed_indices.extend([slice(None)] * m)
#                n -= m            
#            else:
#                parsed_indices.append(index)
#                n -= 1
#    
#            length -= 1
#        #--- End: for
#        len_parsed_indices = len(parsed_indices)
#    
#        if ndim and len_parsed_indices > ndim:
#            raise IndexError("Invalid indices %s for array with shape %s" %
#                             (parsed_indices, shape))
#    
#        if len_parsed_indices < ndim:
#            parsed_indices.extend([slice(None)]*(ndim-len_parsed_indices))
#    
#        if not ndim and parsed_indices:
#            raise IndexError("Scalar array can only be indexed with () or Ellipsis")
#    
#        for i, (index, size) in enumerate(zip(parsed_indices, shape)):
#            if isinstance(index, slice):            
#                continue
#    
#            if isinstance(index, (int, long)):
#                if index < 0: 
#                    index += size
#    
#                index = slice(index, index+1, 1)
#            else:
#                if getattr(getattr(index, 'dtype', None), 'kind', None) == 'b':
#                    # Convert booleans to non-negative integers. We're
#                    # assuming that anything with a dtype attribute also
#                    # has a size attribute.
#                    if index.size != size:
#                        raise IndexError(
#    "Invalid indices {} for array with shape {}".format(parsed_indices, shape))
#                    
#                    index = numpy.where(index)[0]
#                #--- End: if
#    
#                if not numpy.ndim(index):
#                    if index < 0:
#                        index += size
#    
#                    index = slice(index, index+1, 1)
#                else:
#                    len_index = len(index)
#                    if len_index == 1:                
#                        index = index[0]
#                        if index < 0:
#                            index += size
#                        
#                        index = slice(index, index+1, 1)
#                    else:
#                        raise IndexError(
#                            "Invalid indices {} for array with shape {}".format(
#                                parsed_indices, shape))                
#                #--- End: if
#            #--- End: if
#            
#            parsed_indices[i] = index    
#        #--- End: for
#    
#        return parsed_indices
#    #--- End: def

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
        if indices is Ellipsis:
            return array
        
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

    @abc.abstractmethod
    def open(self):
        '''
        '''
        pass
    #---End: def
    
#--- End: class

# ====================================================================
#
# Numpy Array wrapper
# 
# ====================================================================

class NumpyArray(Array):
    '''A numpy  array.

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

Returns an independent numpy array.

        '''
        isunique = self.isunique
        
        array = self.array

        if not isunique:
            if numpy.ma.isMA(array) and not self.ndim:
                # This is because numpy.ma.copy doesn't work for
                # scalar arrays (at the moment, at least)
                ma_array = numpy.ma.empty((), dtype=array.dtype)
                ma_array[...] = array
                array = ma_array
            else:
                array = array.copy()
        #--- End: if

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

    @property
    def isunique(self):
        '''
        '''
        return sys.getrefcount(self.array) <= 2
    
    def open(self):
        pass

    def close(self):
        pass
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
        
#        indices = tuple(self.parse_indices(indices))
        
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

    @property
    def isunique(self):
        '''
        '''
        return True

    def close(self):
        '''Close the `netCDF4.Dataset` for the file containing the data.

:Returns:

    out: `netCDF4.Dataset`

:Examples:

>>> f.close()

        '''
        self.file_close(self.file)
    #--- End: def

    @classmethod
    def file_close(cls, filename):
        '''Close the `netCDF4.Dataset` for a netCDF file.

:Returns:

    `None`

:Examples:

>>> f.file_close(filename)

        '''
        nc = _file_to_fh_read.pop(filename, None)
        if nc is not None and nc.isopen():
            nc.close()

        nc = _file_to_fh_write.pop(filename, None)
        if nc is not None and nc.isopen():
            nc.close()
    #--- End: def

    @classmethod
    def file_open(cls, filename, mode, fmt=None):
        '''Return an open `netCDF4.Dataset` for a netCDF file.

:Returns:

    out: `netCDF4.Dataset`

:Examples:

>>> f.file_open(filename, 'r')
<netCDF4.Dataset at 0x115a4d0>

        '''
        if mode == 'r':
            files = _file_to_fh_read
        else:
            files = _file_to_fh_write

        nc = files.get(filename)

        if nc is None or not nc.isopen():
            if open_files_threshold_exceeded():
                # Close an arbitrary file that has been opened for reading
                for f in _file_to_fh_read:                    
                    cls.file_close(f)
                    break
            #--- End: if

            try:        
                nc = netCDF4.Dataset(filename, mode, format=fmt)
            except RuntimeError as runtime_error:
                raise RuntimeError("{}: {}".format(runtime_error, filename))        

            files[filename] = nc                
        #--- End: if
        
        return nc
    #--- End: def

    def open(self):
        '''Return an open `netCDF4.Dataset` for the file containing the array.

:Returns:

    out: `netCDF4.Dataset`

:Examples:

>>> f.open()
<netCDF4.Dataset at 0x115a4d0>

        '''
        return self.file_open(self.file, 'r')
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

#        indices = self.parse_indices(indices)
        array = self.get_subspace(array, indices)
        
        return array
