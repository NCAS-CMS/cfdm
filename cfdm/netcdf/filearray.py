#from numpy import array   as numpy_array
#from numpy import reshape as numpy_reshape
#
#from numpy.ma import masked as numpy_ma_masked
#from numpy.ma import resize as numpy_ma_resize
#from numpy.ma import where  as numpy_ma_where
#
#from operator import mul
#
#from .functions import _open_netcdf_file
#
#from ..data.filearray import FileArray
#
#
## ====================================================================
##
## NetCDFFileArray object
##
## ====================================================================
#
#class NetCDFFileArray(FileArray):
#    ''' 
#
#A sub-array stored in a netCDF file.
#    
#**Initialization**
#
#:Parameters:
#
#    file : str
#        The netCDF file name in normalized, absolute form.
#
#    dtype : numpy.dtype
#        The numpy data type of the data array.
#
#    ndim : int
#        Number of dimensions in the data array.
#
#    shape : tuple
#        The data array's dimension sizes.
#
#    size : int
#        Number of elements in the data array.
#
#    ncvar : str, optional
#        The netCDF variable name containing the data array. Must be
#        set if *varid* is not set.
#
#    varid : int, optional
#        The netCDF ID of the variable containing the data array. Must
#        be set if *ncvar* is not set. Ignored if *ncvar* is set.
#
#    ragged: `int`, optional
#        Reduction in logical rank due to ragged array representation.
#
#    gathered: `int`, optional
#        Reduction in logical rank due to compression by gathering.
#
#:Examples:
#
#>>> import netCDF4
#>>> import os
#>>> nc = netCDF4.Dataset('file.nc', 'r')
#>>> v = nc.variable['tas']
#>>> a = NetCDFFileArray(file=os.path.abspath('file.nc'), ncvar='tas',
#                        dtype=v.dtype, ndim=v.ndim, shape=v.shape, size=v.size)
#
#'''
#    def __getitem__(self, indices):
#        '''
#
#x.__getitem__(indices) <==> x[indices]
#
#Returns a numpy array.
#
#''' 
#        nc = self.open()
#        
#        ncvar = getattr(self, 'ncvar', None)
#
#        if ncvar is not None:
#            # Get the variable by name
#            array = nc.variables[ncvar][indices]
#        else:
#            # Get the variable by netCDF ID
#            varid = self.varid
#            for value in nc.variables.itervalues():
#                if value._varid == varid:
#                    array = value[indices]
#                    break
#        #--- End: if
#
#        if not self.ndim:
#            # Hmm netCDF4 has a thing for making scalar size 1 , 1d
#            array = array.squeeze()
#
#        # ------------------------------------------------------------
#        # If approriate, collapse (by concatenation) the outermost
#        # (fastest varying) dimension of string valued array into
#        # memory. E.g. [['a','b','c']] becomes ['abc']
#        # ------------------------------------------------------------
#        if array.dtype.kind == 'S' and array.ndim > (self.ndim -
#                                                     getattr(self, 'gathered', 0) -
#                                                     getattr(self, 'ragged', 0)):
#            strlen = array.shape[-1]
#            
#            new_shape = array.shape[0:-1]
#            new_size  = long(reduce(mul, new_shape, 1))
#            
#            array = numpy_ma_resize(array, (new_size, strlen))
#            
#            array = array.filled(fill_value='')
#
#            array = numpy_array([''.join(x).rstrip() for x in array],
#                                dtype='S%d' % strlen)
#            
#            array = array.reshape(new_shape)
#
#            array = numpy_ma_where(array=='', numpy_ma_masked, array)
#        #--- End: if
#
#        return array
#    #--- End: def
#
#    def __str__(self):
#        '''
#
#x.__str__() <==> str(x)
#
#'''      
#        name = getattr(self, 'ncvar', None)
#        if name is None:
#            name = self.varid
#
#        return "%s%s in %s" % (name, self.shape, self.file)
#    #--- End: def
#    
#    def close(self):
#        '''
#
#Close the file containing the data array.
#
#If the file is not open then no action is taken.
#
#:Returns:
#
#    None
#
#:Examples:
#
#>>> f.close()
#
#'''
#        _close_netcdf_file(self.file)
#    #--- End: def
#
#    @property
#    def  file_pointer(self):
#        '''
#'''
#        offset = getattr(self, 'ncvar', None)
#        if offset is None:
#            offset = self.varid
#
#        return (self.file, offset)
#    #--- End: def
#
#    def open(self):
#        '''
#
#Return a `netCDF4.Dataset` object for the file containing the data
#array.
#
#:Returns:
#
#    out : netCDF4.Dataset
#
#:Examples:
#
#>>> f.open()
#<netCDF4.Dataset at 0x115a4d0>
#
#'''
#        return _open_netcdf_file(self.file, 'r')
#    #--- End: def
#
##--- End: class
