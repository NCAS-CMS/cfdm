from os       import close
from sys      import getrefcount
from tempfile import mkstemp
from operator import mul

from numpy import empty   as numpy_empty
from numpy import full    as numpy_full
from numpy import load    as numpy_load
from numpy import ndarray as numpy_ndarray
from numpy import save    as numpy_save

from numpy.ma import array      as numpy_ma_array
from numpy.ma import is_masked  as numpy_ma_is_masked
from numpy.ma import masked_all as numpy_ma_masked_all

from ..functions import parse_indices, get_subspace, abspath
from ..functions import inspect as cf_inspect
from ..constants import CONSTANTS

_debug = False


# ====================================================================
#
# CompressedArray object
#
# ====================================================================

class CompressedArray(object):
    '''
'''
    def __init__(self, array, shape, compression):
        '''
        
**Initialization**

:Parameters:

    array: 

    shape: `tuple`
        The shape of the uncompressed array

    compression: `dict`
'''
        # DO NOT CHANGE IN PLACE
        self.array = array

        # DO NOT CHANGE IN PLACE
        self.compression = compression

        # DO NOT CHANGE IN PLACE
        self.shape = tuple(shape)

        # DO NOT CHANGE IN PLACE            
        self.ndim  = len(shape)

        # DO NOT CHANGE IN PLACE
        self.size  = long(reduce(mul, shape, 1))
    #---End: def

    def __getitem__(self, indices):
        '''

x.__getitem__(indices) <==> x[indices]

Returns a numpy array.

'''
        compression = self.compression
        (compression_type, uncompression) = self.compression.items()[0]
        
        # The compressed array
        array = self.array
        
        # Initialize the full, uncompressed output array with missing
        # data everywhere
        uarray = numpy_ma_masked_all(self.shape, dtype=array.dtype)

        r_indices = [slice(None)] * array.ndim
        p_indices = [slice(None)] * uarray.ndim        
        
        if compression_type == 'gathered':
            sample_axis           = uncompression['axis']
            uncompression_indices = uncompression['indices']
            
            compressed_axes = range(sample_axis, self.ndim - (array.ndim - sample_axis - 1))
            n_compressed_axes = len(compressed_axes)
            
            zzz = [reduce(mul, [shape[i] for i in compressed_axes[i:]], 1)
                   for i in range(1, n_compressed_axes)]
            
            zeros = [0] * n_compressed_axes
            for ii, b in enumerate(uncompression_indices):
                r_indices[sample_axis] = ii
                
                xxx = zeros[:]
                for i, z in enumerate(zzz):                
                    if b >= z:
                        (a, b) = divmod(b, z)
                        xxx[i] = a
                    xxx[-1] = b
                #--- End: for
                        
                for j, x in izip(compressed_axes, xxx):
                    p_indices[j] = x
                    
                uarray[p_indices] = r_data[r_indices]
            #--- End: for

        elif compression_type == 'DSG_contiguous':
            instance_axis  = uncompression['instance_axis']
            instance_index = uncompression['instance_index']
            element_axis   = uncompression['c_element_axis']
            sample_indices = uncompression['c_element_indices']
            p_indices[instance_axis] = instance_index
            p_indices[element_axis]  = slice(0, sample_indices.stop - sample_indices.start)
            
            uarray[tuple(p_indices)] = array[sample_indices]
            
            if _debug:
                print 'instance_axis    =', instance_axis
                print 'instance_index   =', instance_index
                print 'element_axis     =', element_axis
                print 'sample_indices   =', sample_indices
                print 'p_indices        =', p_indices
                print 'uarray.shape     =', uarray.shape
                print 'self.array.shape =', array.shape

        elif compression_type == 'DSG_indexed':
            instance_axis  = uncompression['instance_axis']
            instance_index = uncompression['instance_index']
            element_axis   = uncompression['i_element_axis']
            sample_indices = uncompression['i_element_indices']
            
            p_indices[instance_axis] = instance_index
            p_indices[element_axis]  = slice(0, len(sample_indices))
            
            uarray[tuple(p_indices)] = array[sample_indices]
            
            if _debug:
                print 'instance_axis    =', instance_axis
                print 'instance_index   =', instance_index
                print 'element_axis     =', element_axis
                print 'sample_indices   =', sample_indices
                print 'p_indices        =', p_indices
                print 'uarray.shape     =', uarray.shape
                print 'self.array.shape =', array.shape

        elif compression_type == 'DSG_indexed_contiguous':
            instance_axis     = uncompression['instance_axis']
            instance_index    = uncompression['instance_index']
            i_element_axis    = uncompression['i_element_axis']
            i_element_index   = uncompression['i_element_index']
            c_element_axis    = uncompression['c_element_axis']
            c_element_indices = uncompression['c_element_indices']
            
            p_indices[instance_axis]  = instance_index
            p_indices[i_element_axis] = i_element_index
            p_indices[c_element_axis] = slice(0, c_element_indices.stop - c_element_indices.start)
            
            uarray[tuple(p_indices)] = array[c_element_indices]
        else:
            raise ValueError("Unkown compression type: {}".format(compression_type))
        
        if indices is Ellipsis:
            return uarray
        else:
            if _debug:
                print 'indices =', indices
            indices = parse_indices(self.shape, indices)
            if _debug:
                print 'parse_indices(self.shape, indices) =', indices
                
            return get_subspace(uarray, indices)
    #--- End: def

    def __repr__(self):
        '''

x.__repr__() <==> repr(x)
        '''
        return "<CF %s: %s>" % (self.__class__.__name__, str(self.array))
    #--- End: def

    @property
    def dtype(self):
        return self.array.dtype

    @property    
    def file(self):
        '''The file on disk which contains the compressed array, or `None` of
the array is in memory.

:Examples:

>>> self.file
'/home/foo/bar.nc'

        '''        
        return getattr(self.array, 'file', None)
    #--- End: def

    def close(self):
        '''

Close all referenced open files.

:Returns:

    None

:Examples:

>>> f.close()

'''     
        if self.on_disk():
            self.array.close()
    #--- End: def

    def copy(self):
        '''
'''
        C = self.__class__
        new = C.__new__(C)
        new.__dict__ = self.__dict__.copy()
        return new
    #--- End: def

    def inspect(self):
        '''

Inspect the object for debugging.

.. seealso:: `cf.inspect`

:Returns: 

    None

'''
        print cf_inspect(self)
    #--- End: def
        
    def on_disk(self):
        '''True if and only if the compressed array is on disk as opposed to
in memory.

:Examples:

>>> a.on_disk()
True

        '''
        return not hasattr(self.array, '__array_interface__')
    #--- End: if

    def unique(self):
        '''
'''
        return getrefcount(self.array) <= 2
    #--- End: def
#--- End: class

# ====================================================================
#
# FileArray object
# 
# ====================================================================

class FileArray(object):
    '''

A sub-array stored in a file.
    
.. note:: Subclasses must define the following methods:
          `!__getitem__`, `!__str__`, `!close` and `!open`.
    
'''
    def __init__(self, **kwargs):
        '''
        
**Initialization**

:Parameters:

    file : str
        The netCDF file name in normalized, absolute form.

    dtype : numpy.dtype
        The numpy data type of the data array.

    ndim : int
        Number of dimensions in the data array.

    shape : tuple
        The data array's dimension sizes.

    size : int
        Number of elements in the data array.

'''
        self.__dict__ = kwargs

        f = getattr(self, 'file', None)
        if f is not None:
            self.file = abspath(f)
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
        return "<CF %s: %s>" % (self.__class__.__name__, str(self))
    #--- End: def
     
    def __str__(self):
        '''

x.__str__() <==> str(x)

'''
        return "%s in %s" % (self.shape, self.file)
    #--- End: def
    
    def copy(self):
        '''

Return a deep copy.

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
#        return type(self)(**self.__dict__)
    #--- End: def
    
    def inspect(self):
        '''

Inspect the object for debugging.

.. seealso:: `cf.inspect`

:Returns: 

    None

'''
        print cf_inspect(self)
    #--- End: def
        
    def fff():
        pass

    def close(self):
        pass
    #--- End: def

    def open(self):
        pass
    #--- End: def

#--- End: class

# ====================================================================
#
# _TempFileArray object
#
# ====================================================================

class _TempFileArray(FileArray):
    ''' 

A indexable N-dimensional array supporting masked values.

The array is stored on disk in a temporary file until it is
accessed. The directory containing the temporary file may be found and
set with the `cf.TEMPDIR` function.

'''

    def __init__(self, array):
        '''

**Initialization**

:Parameters:

    array : numpy array
        The array to be stored on disk in a temporary file.        

:Examples:

>>> f = _TempFileArray(numpy.array([1, 2, 3, 4, 5]))
>>> f = _TempFileArray(numpy.ma.array([1, 2, 3, 4, 5]))

'''
#        array = kwargs.pop('array')
#
#        super(_TempFileArray, self).__init__()

        # ------------------------------------------------------------
        # Use mkstemp because we want to be responsible for deleting
        # the temporary file when done with it.
        # ------------------------------------------------------------
        fd, _partition_file = mkstemp(prefix='cf_array_', suffix='.npy', 
                                      dir=CONSTANTS['TEMPDIR'])
        close(fd)

        # The name of the temporary file storing the array
        self._partition_file = _partition_file

        # Numpy data type of the array
        self.dtype = array.dtype

        # Tuple of the array's dimension sizes
        self.shape = array.shape

        # Number of elements in the array
        self.size = array.size

        # Number of dimensions in the array
        self.ndim = array.ndim

        if numpy_ma_is_masked(array):
            # Array is a masked array. Save it as record array with
            # 'data' and 'mask' elements because this seems much
            # faster than using numpy.ma.dump.
            self._masked_as_record = True
            numpy_save(_partition_file, array.toflex())
        else:
            self._masked_as_record = False
            if hasattr(array, 'mask'):
                # Array is a masked array with no masked elements
                numpy_save(_partition_file, array.view(numpy_ndarray))
            else:
                # Array is not a masked array.
                numpy_save(_partition_file, array)
    #--- End: def

    def __getitem__(self, indices):
        '''

x.__getitem__(indices) <==> x[indices]

Returns a numpy array.

'''
        array = numpy_load(self._partition_file)

        indices = parse_indices(array.shape, indices)

        array = get_subspace(array, indices)

        if self._masked_as_record:
            # Convert a record array to a masked array
            array = numpy_ma_array(array['_data'], mask=array['_mask'],
                                   copy=False)
            array.shrink_mask()
        #--- End: if

        # Return the numpy array
        return array
    #--- End: def

    def __str__(self):
        '''

x.__str__() <==> str(x)

'''
        return '%s in %s' % (self.shape, self._partition_file)
    #--- End: def

    def close(self):
        '''

Close all referenced open files.

:Returns:

    None

:Examples:

>>> f.close()

'''     
        # No open files are referenced
        pass
    #--- End: def
   
#--- End: class

#class CreateArray(FileArray):
#    '''
#**Initialization**
#
#:Parameters:
#
#    dtype: `numpy.dtype`
#        The numpy data type of the data array.
#
#    ndim: `int`
#        Number of dimensions in the data array.
#
#    shape: `tuple`
#        The data array's dimension sizes.
#
#    size: `int`
#        Number of elements in the data array.
#
#    fill_value: scalar, optional
#
#    _masked : bool
#
#'''
#
#    def __getitem__(self, indices):
#        '''
#
#x.__getitem__(indices) <==> x[indices]
#
#Returns a numpy array.
#
#        '''
#        array_shape = []
#        for index in parse_indices(self.shape, indices):
#            if isinstance(index, slice):                
#                step = index.step
#                if step == 1:
#                    array_shape.append(index.stop - index.start)
#                elif step == -1:
#                    stop = index.stop
#                    if stop is None:
#                        array_shape.append(index.start + 1)
#                    else:
#                        array_shape.append(index.start - index.stop)
#                else:                    
#                    stop = index.stop
#                    if stop is None:
#                        stop = -1
#                       
#                    a, b = divmod(stop - index.start, step)
#                    if b:
#                        a += 1
#                    array_shape.append(a)
#            else:
#                array_shape.append(len(index))
#        #-- End: for
#
#        if self.fill_value is not None:
#            return numpy_full(array_shape, fill_value=self.fill_value, dtype=self.dtype)
##        elif _masked:
##            return numpy_ma_masked_all(array_shape, dtype=self.dtype)
#        else:    
#            return numpy_empty(array_shape, dtype=self.dtype)
#    #--- End: def
#
#    def __repr__(self):
#        '''
#
#x.__repr__() <==> repr(x)
#
#'''
#        return "<CF {0}: shape={1}, dtype={2}, fill_value={3}>".format(
#            self.__class__.__name__, self.shape, self.dtype, self.fill_value)
#    #--- End: def
#
#    def __str__(self):
#        '''
#
#x.__str__() <==> str(x)
#
#'''
#        return repr(self)
#    #--- End: def
#
#    def reshape(self, newshape):
#        '''
#'''
#        new = self.copy()        
#        new.shape = newshape
#        new.ndim  = len(newshape)
#        return new
#    #--- End: def
#
#    def resize(self, newshape):
#        '''
#'''
#        self.shape = newshape
#        self.ndim  = len(newshape)
#    #--- End: def
##--- End: class

class FilledArray(FileArray):
    '''
**Initialization**

:Parameters:

    dtype : numpy.dtype
        The numpy data type of the data array.

    ndim : int
        Number of dimensions in the data array.

    shape : tuple
        The data array's dimension sizes.

    size : int
        Number of elements in the data array.

    fill_value : scalar, optional

    masked_all: `bool`

'''
    def __init__(self, **kwargs):
        '''
        '''
        super(FilledArray, self).__init__(**kwargs)
        self.file = None
    #--- End: def

    def __getitem__(self, indices):
        '''

x.__getitem__(indices) <==> x[indices]

Returns a numpy array.

        '''
        if indices is Ellipsis:
            array_shape = self.shape
        else:
            array_shape = []
            for index in parse_indices(self.shape, indices):
                if isinstance(index, slice):                
                    step = index.step
                    if step == 1:
                        array_shape.append(index.stop - index.start)
                    elif step == -1:
                        stop = index.stop
                        if stop is None:
                            array_shape.append(index.start + 1)
                        else:
                            array_shape.append(index.start - index.stop)
                    else:                    
                        stop = index.stop
                        if stop is None:
                            stop = -1
                           
                        a, b = divmod(stop - index.start, step)
                        if b:
                            a += 1
                        array_shape.append(a)
                else:
                    array_shape.append(len(index))
            #-- End: for
        #-- End: if

        if getattr(self, 'masked_all', False):
            return numpy_ma_masked_all(array_shape, dtype=self.dtype)                
        elif self.fill_value is not None:
            return numpy_full(array_shape, fill_value=self.fill_value, dtype=self.dtype)
        else:
            return numpy_empty(array_shape, dtype=self.dtype)
    #--- End: def

    def __repr__(self):
        '''

x.__repr__() <==> repr(x)

'''
        return "<CF {0}: shape={1}, dtype={2}, fill_value={3}>".format(
            self.__class__.__name__, self.shape, self.dtype, self.fill_value)
    #--- End: def

    def __str__(self):
        '''

x.__str__() <==> str(x)

'''
        return repr(self)
    #--- End: def

    def reshape(self, newshape):
        '''
'''
        new = self.copy()        
        new.shape = newshape
        new.ndim  = len(newshape)
        return new
    #--- End: def

    def resize(self, newshape):
        '''
'''
        self.shape = newshape
        self.ndim  = len(newshape)
    #--- End: def

    def view(self):
        '''
'''
        return self[...]
    #--- End: def

#--- End: class

# ====================================================================
#
# SharedMemoryArray object
#
# ====================================================================

_shared_memory_array = {}

class SharedMemoryArray(object):
    '''
    '''
    def __init__(self, array):
        '''
:Parameters:

    array : numpy.ndarary
'''

        # Set the mask
        if numpy_ma_isMA(array):
            self.mask = type(self)(array.mask)
            array = array.data
        else:
            self.mask = None

        dtype = array.dtype
        shape = array.shape
        size  = array.size

        mp_Array = multiprocessing_Array(_typecode[dtype.char], size)

        a = numpy_frombuffer(mp_Array.get_obj(), dtype=dtype)
        a.resize(shape)
        a[...] = array

        self.__array_interface__ = a.__array_interface__

        self.shape = shape
        self.dtype = dtype
        self.size  = size
        self.ndim  = array.ndim
        self.flags = {'C_CONTIGUOUS': a.flags['C_CONTIGUOUS']}
        self.base  = None

        _shared_memory_array[id(self)] = mp_Array 
    #--- End: def

    def __copy__(self):
        '''

Used if copy.copy is called on the variable.

``f.__copy__() is equivalent to ``copy.copy(f)``.

:Returns:

    out :
        A shallow copy.

:Examples:

>>> import copy
>>> g = copy.copy(f)

'''
        C = self.__class__
        new = C.__new__(C)
        new.__dict__ = self.__dict__.copy()

        new.flags = self.flags.copy()

        _shared_memory_array[id(new)] = _shared_memory_array[id(self)]       

        mask = new.mask
        if mask is not None:
            new.mask = mask.__copy__()
            
        return new
    #--- End: def

    def __deepcopy__(self, memo):
        '''

Used if copy.deepcopy is called on the variable.

``f.__deepcopy__(memo) is equivalent to ``copy.deepcopy(f)``.

:Returns:

    out :
        A deep copy.

:Examples:

>>> import copy
>>> g = copy.deepcopy(f)

'''
        return self.copy()
    #--- End: def

    def __del__(self):
        '''

Called when the object's reference count reaches zero.

'''
        _shared_memory_array.pop(id(self), None)
    #--- End: def

    def __getitem__(self, indices):
        '''
'''      
        array = self.view()
        if indices is Ellipsis:
            return array

        indices = parse_indices(array.shape, indices)
        return get_subspace(array, indices)
    #--- End: def

    def __repr__(self):
        '''

x.__repr__() <==> repr(x)

'''   
        out = '<CF {0}: {1}'.format(self.__class__.__name__,         
                                    self.__array_interface__)
        mask = self.mask
        if mask:
            out += ' MASK: {0}>'.format(mask.__array_interface__)
        else:
            out += '>'

        return out
    #--- End: def

    def copy(self):
        '''

Return a deep copy.

``f.copy() is equivalent to ``copy.deepcopy(f)``.

:Returns:

    out :
        A deep copy.

:Examples:

>>> g = f.copy()

'''
        return type(self)(self.view())
    #--- End: def

    def inspect(self):
        '''

Inspect the object for debugging.

.. seealso:: `cf.inspect`

:Returns: 

    None
'''
        print cf_inspect(self)
    #--- End: def
        
    def view(self):
        '''
'''
        mask = self.mask
        if mask is None:
            array = numpy_array(self, copy=False)
        else:
            array = numpy_ma_array(self, copy=False)
            array.mask = numpy_array(mask, copy=False)

        return array
    #--- End: 

    def print_base(self):
        out = repr(_shared_memory_array[id(self)])
        if self.mask:
            out += '\nMASK: ', repr(self.print_base())
        print out
#--- End: class
