from collections import abc

from .array import Array, _file_to_fh_read, _file_to_fh_write

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
    __metaclass__ = abc.ABCMeta

    # Always close the netCDF file after access
    self._close = True

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

        # Close the netCDF file
        if self._close:
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
        nc = self._nc        
        del self._nc
        nc.close()
#        self.file_close(self.file)
    #--- End: def

#    @classmethod
#    def file_close(cls, filename):
#        '''Close the `netCDF4.Dataset` for a netCDF file.
#
#:Returns:
#
#    `None`
#
#:Examples:
#
#>>> f.file_close(filename)
#
#        '''
#        nc = _file_to_fh_read.pop(filename, None)
#        if nc is not None and nc.isopen():
#            nc.close()
#
#        nc = _file_to_fh_write.pop(filename, None)
#        if nc is not None and nc.isopen():
#            nc.close()
#    #--- End: def

    @classmethod
    def file_open(cls, filename, mode, fmt=None):
        '''Return an open `netCDF4.Dataset` for a netCDF file.

:Returns:

    out: `netCDF4.Dataset`

:Examples:

>>> f.file_open(filename, 'r')
<netCDF4.Dataset at 0x115a4d0>

        '''
#        if mode == 'r':
#            files = _file_to_fh_read
#        else:
#            files = _file_to_fh_write
#
#        nc, count = files.get(filename, (None, 0))
#THREADSAFE? Just open files each time, i think ...
#        if nc is None or not nc.isopen():
#            #if open_files_threshold_exceeded():
#            #    # Close an arbitrary file that has been opened for reading
#            #    for f in _file_to_fh_read:                    
#            #        cls.file_close(f)
#            #        break
#            ##--- End: if
#
#            if count == 0:
#                try:        
#                    nc = netCDF4.Dataset(filename, mode, format=fmt)
#                except RuntimeError as runtime_error:
#                    raise RuntimeError("{}: {}".format(runtime_error, filename))        
#                else:
#                    files[filename] = (nc, count+1)
#            #--- End: if
#
#        return nc
#        #--- End: if
        
        try:        
            return netCDF4.Dataset(filename, mode, format=fmt)
        except RuntimeError as runtime_error:
            raise RuntimeError("{}: {}".format(runtime_error, filename))        
    #--- End: def

    def open(self):
        '''Return an open `netCDF4.Dataset` for the file containing the array.

:Returns:

    out: `netCDF4.Dataset`

:Examples:

>>> f.open()
<netCDF4.Dataset at 0x115a4d0>

        '''
        nc = self.file_open(self.file, 'r')
        self._nc = nc
        return nc
    #--- End: def

#--- End: class
