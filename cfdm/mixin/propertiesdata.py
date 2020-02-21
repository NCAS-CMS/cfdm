from __future__ import print_function
from builtins import (str, super)

from . import Container
from . import Properties


class PropertiesData(Properties):
    '''Mixin class for a data array with descriptive properties.

    .. versionadded:: 1.7.0

    '''
    def __getitem__(self, indices):
        '''Return a subspace defined by indices

    f.__getitem__(indices) <==> f[indices]
    
    Indexing follows rules that are very similar to the numpy indexing
    rules, the only differences being:
    
    * An integer index i takes the i-th element but does not reduce
      the rank by one.
    
    * When two or more dimensions' indices are sequences of integers
      then these indices work independently along each dimension
      (similar to the way vector subscripts work in Fortran). This is
      the same behaviour as indexing on a Variable object of the
      netCDF4 package.
    
    .. versionadded:: 1.7.0
    
    :Returns:
    
            The subspace.
    
    **Examples:**
    
    >>> f.shape
    (1, 10, 9)
    >>> f[:, :, 1].shape
    (1, 10, 1)
    >>> f[:, 0].shape
    (1, 1, 9)
    >>> f[..., 6:3:-1, 3:6].shape
    (1, 3, 3)
    >>> f[0, [2, 9], [4, 8]].shape
    (1, 2, 2)
    >>> f[0, :, -2].shape
    (1, 10, 1)

        '''
        new = self.copy() #data=False)
        
        data = self.get_data(None)
        if data is not None:
            new.set_data(data[indices], copy=False)
        
        return new


    def __str__(self):
        '''Called by the `str` built-in function.

    x.__str__() <==> str(x)

    .. versionadded:: 1.7.0

        '''
        name = self.identity('')

        data = self.get_data(None)
        if data is not None:
            dims = ', '.join([str(x) for x in data.shape])
            dims = '({0})'.format(dims)
        else:
            dims = ''

        # Units
        units = self.get_property('units', '')
        if units is None:
            isreftime = bool(self.get_property('calendar', False))
        else:
            isreftime = 'since' in units
            
        if isreftime:
            units += ' '+self.get_property('calendar', '')
            
        return '{0}{1} {2}'.format(self.identity(''), dims, units)


    # ----------------------------------------------------------------
    # Private methods
    # ----------------------------------------------------------------
    def _parse_axes(self, axes):
        '''Conform axes.

    :Parameters:
    
        axes: (sequence of) `int`
    
    :Returns:
    
        `list`
            The conformed axes.

        '''
#        ndim = self.data.ndim
#        ndim = self.ndim
        
#        if axes is None:
#            return list(range(ndim))
        
        if axes is None:
            return axes

        if isinstance(axes, int):
            axes = (axes,)
            
        ndim = self.ndim
        
        return [(i + ndim if i < 0 else i) for i in axes]


    # ----------------------------------------------------------------
    # Attributes
    # ----------------------------------------------------------------
    @property
    def dtype(self):
        '''Data-type of the data elements.

    **Examples:**
    
    >>> d.dtype
    dtype('float64')
    >>> type(d.dtype)
    <type 'numpy.dtype'>

        '''
        data = self.get_data(None)
        if data is not None:
            return data.dtype

        raise AttributeError("{!r} object has no attribute 'dtype'".format(
            self.__class__.__name__))


    @property
    def ndim(self):
        '''The number of dimensions in the data array.

    .. seealso:: `data`, `has_data`, `isscalar`, `shape`, `size`

    **Examples:**

    >>> f.shape
    (73, 96)
    >>> f.ndim
    2
    >>> f.size
    7008

    >>> f.shape
    (73, 1, 96)
    >>> f.ndim
    3
    >>> f.size
    7008

    >>>  f.shape
    (73,)
    >>> f.ndim
    1
    >>> f.size
    73

    >>> f.shape
    ()
    >>> f.ndim
    0
    >>> f.size
    1

        '''
        data = self.get_data(None)
        if data is not None:
            return data.ndim

        raise AttributeError("{!r} object has no attribute 'ndim'".format(
            self.__class__.__name__))

    
    @property
    def shape(self):
        '''A tuple of the data array's dimension sizes.

    .. seealso:: `data`, `has_data`, `ndim`, `size`

    **Examples:**

    >>> f.shape
    (73, 96)
    >>> f.ndim
    2
    >>> f.size
    7008

    >>> f.shape
    (73, 1, 96)
    >>> f.ndim
    3
    >>> f.size
    7008

    >>> f.shape
    (73,)
    >>> f.ndim
    1
    >>> f.size
    73

    >>> f.shape
    ()
    >>> f.ndim
    0
    >>> f.size
    1

        '''
        data = self.get_data(None)
        if data is not None:
            return data.shape

        raise AttributeError("{!r} object has no attribute 'shape'".format(
            self.__class__.__name__))


    @property
    def size(self):
        '''The number of elements in the data array.

    .. seealso:: `data`, `has_data`, `ndim`, `shape`

    **Examples:**

    >>> f.shape
    (73, 96)
    >>> f.ndim
    2
    >>> f.size
    7008

    >>> f.shape
    (73, 1, 96)
    >>> f.ndim
    3
    >>> f.size
    7008

    >>> f.shape
    (73,)
    >>> f.ndim
    1
    >>> f.size
    73

    >>> f.shape
    ()
    >>> f.ndim
    0
    >>> f.size
    1

        '''
        data = self.get_data(None)
        if data is not None:
            return data.size

        raise AttributeError("{!r} object has no attribute 'size'".format(
            self.__class__.__name__))


    # ----------------------------------------------------------------
    # Methods
    # ----------------------------------------------------------------
    def dump(self, display=True, _key=None, _omit_properties=(),
             _prefix='', _title=None, _create_title=True, _level=0,
             _axes=None, _axis_names=None):
        '''A full description.

    .. versionadded:: 1.7.0
    
    :Parameters:
    
        display: `bool`, optional
            If False then return the description as a string. By
            default the description is printed.
    
    :Returns:
    
            The description. If *display* is True then the description
            is printed and `None` is returned. Otherwise the
            description is returned as a string.

        '''
        # ------------------------------------------------------------
        # Properties
        # ------------------------------------------------------------
        string = super().dump(display=False, _key=_key,
                              _omit_properties=_omit_properties,
                              _prefix=_prefix, _title=_title,
                              _create_title=_create_title,
                              _level=_level)
        if string:
            string = [string]
        else:
            string = []
            
        indent0 = '    ' * _level
        indent1 = '    ' * (_level+1)

        # ------------------------------------------------------------
        # Data
        # ------------------------------------------------------------
        data = self.get_data(None)
        if data is not None:
            if _axes and _axis_names:
                x = [_axis_names[axis] for axis in _axes]
                ndim = data.ndim
                x = x[:ndim]                    
                if len(x) < ndim:
                    x.extend([str(size) for size in data.shape[len(x):]])
            else:
                x = [str(size) for size in data.shape]

            shape = ', '.join(x)
            
            string.append('{0}{1}Data({2}) = {3}'.format(indent1,
                                                         _prefix,
                                                         shape,
                                                         str(data)))
        
        string = '\n'.join(string)
       
        if display:
            print(string)
        else:
            return string


    def equals(self, other, rtol=None, atol=None, verbose=False,
               ignore_data_type=False, ignore_fill_value=False,
               ignore_properties=(), ignore_compression=True,
               ignore_type=False):
        '''Whether two instances are the same.

    Equality is strict by default. This means that:
    
    * the same descriptive properties must be present, with the same
      values and data types, and vector-valued properties must also
      have same the size and be element-wise equal (see the
      *ignore_properties* and *ignore_data_type* parameters), and
    
    ..
    
    * if there are data arrays then they must have same shape and data
      type, the same missing data mask, and be element-wise equal (see
      the *ignore_data_type* parameter).
    
    Two real numbers ``x`` and ``y`` are considered equal if
    ``|x-y|<=atol+rtol|y|``, where ``atol`` (the tolerance on absolute
    differences) and ``rtol`` (the tolerance on relative differences)
    are positive, typically very small numbers. See the *atol* and
    *rtol* parameters.
    
    Any compression is ignored by default, with only the arrays in
    their uncompressed forms being compared. See the
    *ignore_compression* parameter.

    Any type of object may be tested but, in general, equality is only
    possible with another object of the same type, or a subclass of
    one. See the *ignore_type* parameter.
    
    NetCDF elements, such as netCDF variable and dimension names, do
    not constitute part of the CF data model and so are not checked.
    
    .. versionadded:: 1.7.0
    
    :Parameters:
    
        other: 
            The object to compare for equality.
    
        atol: float, optional
            The tolerance on absolute differences between real
            numbers. The default value is set by the `cfdm.ATOL`
            function.
            
        rtol: float, optional
            The tolerance on relative differences between real
            numbers. The default value is set by the `cfdm.RTOL`
            function.
    
        ignore_fill_value: `bool`, optional
            If True then the "_FillValue" and "missing_value"
            properties are omitted from the comparison.
    
        verbose: `bool`, optional
            If True then print information about differences that lead
            to inequality.
    
        ignore_properties: sequence of `str`, optional
            The names of properties to omit from the comparison.
    
        ignore_data_type: `bool`, optional
            If True then ignore the data types in all numerical
            comparisons. By default different numerical data types
            imply inequality, regardless of whether the elements are
            within the tolerance for equality.
    
        ignore_compression: `bool`, optional
            If False then the compression type and, if applicable, the
            underlying compressed arrays must be the same, as well as
            the arrays in their uncompressed forms. By default only
            the the arrays in their uncompressed forms are compared.
    
        ignore_type: `bool`, optional
            Any type of object may be tested but, in general, equality
            is only possible with another object of the same type, or
            a subclass of one. If *ignore_type* is True then equality
            is possible for any object with a compatible API.
    
    :Returns: 
      
        `bool`
            Whether the two instances are equal.
    
    **Examples:**
    
    >>> x.equals(x)
    True
    >>> x.equals(x.copy())
    True
    >>> x.equals('something else')
    False

        '''
        pp = super()._equals_preprocess(other, verbose=verbose,
                                        ignore_type=ignore_type)
        if pp is True or pp is False:
            return pp
        
        other = pp

        # ------------------------------------------------------------
        # Check external variables (returning True if both are
        # external with the same netCDF variable name)
        # ------------------------------------------------------------
        external0 = self._get_component('external', False)
        external1 = other._get_component('external', False)
        if external0 != external1:
            if verbose:
                print("{0}: Only one external variable)".format(
                    self.__class__.__name__))
            return False
        elif external0:
            # Both variables are external
            if self.nc_get_variable(None) != other.nc_get_variable(None):
                if verbose:
                    print(
                        "{0}: External variable have different netCDF variable names: {} != {})".format(
                            self.__class__.__name__,
                            self.nc_get_variable(None),
                            other.nc_get_variable(None)))
                return False

            return True
                
        # ------------------------------------------------------------
        # Check the properties
        # ------------------------------------------------------------
        if not super().equals(
                other, rtol=rtol, atol=atol,
                verbose=verbose,
                ignore_data_type=ignore_data_type,
                ignore_fill_value=ignore_fill_value,
                ignore_properties=ignore_properties,
                ignore_type=ignore_type): 
            return False

        # ------------------------------------------------------------
        # Check the data
        # ------------------------------------------------------------
        if self.has_data() != other.has_data():
            if verbose:
                print(
                    "{0}: Different data: Only one {0} has data".format(
                        self.__class__.__name__))
            return False
            
        if self.has_data():
            if not self._equals(self.get_data(), other.get_data(),
                                rtol=rtol, atol=atol,
                                verbose=verbose,
                                ignore_data_type=ignore_data_type,
                                ignore_fill_value=ignore_fill_value,
                                ignore_compression=ignore_compression):
                if verbose:
                    print("{0}: Different data".format(self.__class__.__name__))
                return False
        #--- End: if

        return True


    def insert_dimension(self, position=0, inplace=False):
        '''Expand the shape of the data array.

    Inserts a new size 1 axis into the data array.
    
    .. versionadded:: 1.7.0
    
    .. seealso:: `squeeze`, `transpose`
    
    :Parameters:
    
        position: `int`, optional
            Specify the position that the new axis will have in the
            data array. By default the new axis has position 0, the
            slowest varying position. Negative integers counting from
            the last position are allowed.
    
            *Parameter example:*
              ``position=2``
    
            *Parameter example:*
              ``position=-1``
    
        inplace: `bool`, optional
            If True then do the operation in-place and return `None`.
    
    :Returns:
    
            A new instance with expanded data axes. If the operation
            was in-place then `None` is returned.
    
    **Examples:**
    
    >>> f.shape
    (19, 73, 96)
    >>> f.insert_dimension(position=3).shape
    (19, 73, 96, 1)
    >>> f.insert_dimension(position=-1).shape
    (19, 73, 1, 96)

        '''       
        if inplace:
            v = self
        else:
            v = self.copy()
       
        data = v.get_data(None)
        if data is not None:
            data.insert_dimension(position, inplace=True)

        if inplace:
            v = None            
        return v

    
    def squeeze(self, axes=None, inplace=False):
        '''Remove size one axes from the data array.

    By default all size one axes are removed, but particular size one
    axes may be selected for removal.
    
    .. versionadded:: 1.7.0
    
    .. seealso:: `insert_dimension`, `transpose`
    
    :Parameters:
    
        axes: (sequence of) `int`
            The positions of the size one axes to be removed. By
            default all size one axes are removed. Each axis is
            identified by its original integer position. Negative
            integers counting from the last position are allowed.
    
            *Parameter example:*
              ``axes=0``
    
            *Parameter example:*
              ``axes=-2``
    
            *Parameter example:*
              ``axes=[2, 0]``
    
        inplace: `bool`, optional
            If True then do the operation in-place and return `None`.
    
    :Returns:
    
            A new instance with removed data axes. If the operation
            was in-place then `None` is returned.
    
    **Examples:**
    
    >>> f.shape
    (1, 73, 1, 96)
    >>> f.squeeze().shape
    (73, 96)
    >>> f.squeeze(0).shape
    (73, 1, 96)
    >>> f.squeeze([-3, 2]).shape
    (73, 96)

        '''
        if inplace:
            v = self
        else:
            v = self.copy()

        data = v.get_data(None)
        if data is not None:
            data.squeeze(axes, inplace=True)

        if inplace:
            v = None
        return v


    def transpose(self, axes=None, inplace=False):
        '''Permute the axes of the data array.

    .. versionadded:: 1.7.0
    
    .. seealso:: `insert_dimension`, `squeeze`
    
    :Parameters:
    
        axes: (sequence of) `int`
            The new axis order. By default the order is reversed. Each
            axis in the new order is identified by its original
            integer position. Negative integers counting from the last
            position are allowed.
    
            *Parameter example:*
              ``axes=[2, 0, 1]``
    
            *Parameter example:*
              ``axes=[-1, 0, 1]``
    
        inplace: `bool`, optional
            If True then do the operation in-place and return `None`.
    
    :Returns:
    
            A new instance with permuted data axes. If the operation
            was in-place then `None` is returned.
    
    **Examples:**
    
    >>> f.shape
    (19, 73, 96)
    >>> f.tranpose().shape
    (96, 73, 19)
    >>> f.tranpose([1, 0, 2]).shape
    (73, 19, 96)

        '''       
        if inplace:
            v = self
        else:
            v = self.copy()
 
        data = v.get_data(None)
        if data is not None:
            data.transpose(axes, inplace=True)
        
        if inplace:
            v = None

        return v

    
    def uncompress(self, inplace=False):
        '''Uncompress the construct.

    Compression saves space by identifying and removing unwanted
    missing data. Such compression techniques store the data more
    efficiently and result in no precision loss.

    Whether or not the construct is compressed does not alter its
    functionality nor external appearance.

    A construct that is already uncompressed will be returned
    uncompressed.

    The following type of compression are available:

        * Ragged arrays for discrete sampling geometries (DSG). Three
          different types of ragged array representation are
          supported.
        
        ..
        
        * Compression by gathering.

    .. versionadded:: 1.7.11
    
    :Parameters:

        inplace: `bool`, optional
            If True then do the operation in-place and return `None`.
    
    :Returns:

            The uncompressed construct, or `None` if the operation was
            in-place.

    **Examples:** 

    >>> f.data.get_compression_type()
    'ragged contiguous'
    >>> g = f.uncompress()
    >>> g.data.get_compression_type()
    ''
    >>> g.equals(f)
    True

        '''
        if inplace:
            f = self
        else:
            f = self.copy()
            
        data = f.get_data(None)
        if data is not None:
            data.uncompress(inplace=True)
            
        if inplace:
            f = None
        return f    


#--- End: class
