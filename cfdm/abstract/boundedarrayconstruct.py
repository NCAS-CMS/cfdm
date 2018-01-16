from collections import abc

from .arrayconstruct import AbstractArray

# ====================================================================
#
# CFDM Bounded variable object
#
# ====================================================================

class AbstractBoundedArray(AbstractArray):
    '''Base class for CFDM dimension coordinate, auxiliary coordinate and
domain ancillary objects.

    '''

    __metaclass__ = abc.ABCMeta
    
    def __init__(self, properties={}, data=None, source=None,
                 bounds=None, copy=True):
        '''**Initialization**

:Parameters:

    properties: `dict`, optional
        Initialize a new instance with CF properties from a
        dictionary's key/value pairs.
  
    data: `Data`, optional
        Provide the new instance with an N-dimensional data array.
  
    bounds: `Data` or `Bounds`, optional
        Provide the new instance with cell bounds.
  
    source: `Variable`, optional
        Take the attributes, CF properties and data array from the
        source object. Any attributes, CF properties or data array
        specified with other parameters are set after initialisation
        from the source instance.
  
    copy: `bool`, optional
        If False then do not copy arguments prior to
        initialization. By default arguments are deep copied.
  
        '''
        self._bounds = None

        if source is not None:
            if isinstance(self, AbstractBoundedArray):
                if bounds is None and source.hasbounds:
                    bounds = source.bounds
        #--- End: if

        # Set attributes, CF properties and data
        super(AbstractBoundedArray, self).__init__(
            properties=properties,
            data=data,
            source=source,
            copy=copy)

        if bounds is not None:
            self.insert_bounds(bounds, copy=copy)
    #--- End: def

    def __getitem__(self, indices):
        '''

x.__getitem__(indices) <==> x[indices]
        
        '''
        if indices is Ellipsis:
            return self.copy()

        # Parse the index
        if not isinstance(indices, tuple):
            indices = (indices,)

        indices = parse_indices(self.shape, indices)

        new = self.copy(_omit_data=True)

        data = self.data

        if _debug:
            cname = self.__class__.__name__
            print '{}.__getitem__: shape    = {}'.format(cname, self.shape)
            print '{}.__getitem__: indices  = {}'.format(cname, indices)

        new._Data = data[tuple(indices)]

        # Subspace the bounds, if there are any
        if not new.hasbounds:
            bounds = None
        else:
            bounds = self.bounds
            if bounds.hasdata:
                indices = list(indices)
                if data.ndim <= 1:
                    index = indices[0]
                    if isinstance(index, slice):
                        if index.step < 0:
                            # This scalar or 1-d variable has been
                            # reversed so reverse its bounds (as per
                            # 7.1 of the conventions)
                            indices.append(slice(None, None, -1))
                    elif data.size > 1 and index[-1] < index[0]:
                        # This 1-d variable has been reversed so
                        # reverse its bounds (as per 7.1 of the
                        # conventions)
                        indices.append(slice(None, None, -1))                    
                #--- End: if

                if _debug:
                    print '{}.__getitem__: indices for bounds ='.format(self.__class__.__name__, indices)
                
                new.bounds._Data = bounds.data[tuple(indices)]
        #--- End: if

        # Return the new bounded variable
        return new
    #--- End: def

    # ----------------------------------------------------------------
    # Attributes
    # ----------------------------------------------------------------
    @property
    def _Bounds(self):
        '''The `Data` object containing the data array.

.. versionadded:: 1.6

        '''
        return self._Bounds
    #--- End: def
    @_Bounds.setter
    def _Bounds(self, value):
        self._Bounds = value
        self._hasbounds = True
    @_Bounds.deleter
    def _Bounds(self):
        self._Bounds = None
        self._hasbounds = False

    @property
    def bounds(self):
        '''The `Bounds` object containing the cell bounds.

.. versionadded:: 2.0

.. seealso:: `lower_bounds`, `upper_bounds`

:Examples:

>>> c
<CF {+Variable}: latitude(64) degrees_north>
>>> c.bounds
<CF Bounds: latitude(64, 2) degrees_north>
>>> c.bounds = b
AttributeError: Can't set 'bounds' attribute. Consider the insert_bounds method.
>>> c.bounds.max()
<CF Data: 90.0 degrees_north>
>>> c.bounds -= 1
AttributeError: Can't set 'bounds' attribute. Consider the insert_bounds method.
>>> b = c.bounds
>>> b -= 1
>>> c.bounds.max()       
<CF Data: 89.0 degrees_north>

        '''
        return self._Bounds
    @bounds.setter
    def bounds(self, value):
        raise AttributeError("use insert_bounds")
    @bounds.deleter
    def bounds(self):  
        raise AttributeError("use remove_bounds")
    #--- End: def
 
    def copy(self):
        '''
        '''
        super(AbstractBoundedArray, self).copy()
    #--- End: def
 
    def dump(self, display=True, field=None, key=None,
             _omit_properties=(), _prefix='', _title=None,
             _create_title=True, _level=0):
        '''Return a string containing a full description of the instance.

.. versionadded:: 1.6

:Parameters:

    display: `bool`, optional
        If False then return the description as a string. By default
        the description is printed, i.e. ``f.dump()`` is equivalent to
        ``print f.dump(display=False)``.

    omit: sequence of `str`, optional
        Omit the given CF properties from the description.

    _prefix: optional
        Ignored.

:Returns:

    out: `None` or `str`
        A string containing the description.

:Examples:

        '''
        return super(AbstractBoundedArray, self).dump(
            display=display, field=field, key=key,
            _omit_properties=_omit_properties, _prefix=_prefix,
            _title=_title, _create_title=_create_title,
            _extra=('bounds',), _level=_level)
    #--- End: def

    def equals(self, other, rtol=None, atol=None, traceback=False,
               ignore_data_type=False, ignore_fill_value=False,
               ignore_properties=(), ignore_construct_type=False):
        '''
        '''
        return super(AbstractBoundedArray, self).equals(
            other,
            rtol=rtol, atol=atol, traceback=tracback,
            ignore_data_type=ignore_data_type,
            ignore_fill_value=ignore_fill_value,
            ignore_properties=ignore_properties,
            ignore_construct_type=ignore_construct_type,
            _extra=('bounds',))
    #--- End: def
        
    def expand_dims(self, position , copy=True):
        '''
        '''
        c = super(AbstractBoundedArray, self).expand_dims(
            position, copy=copy)

        if c.hasbounds:
            position = self._parse_axes([position])[0]
            c.bounds.expand_dims(position, copy=False)

        return c
    #--- End: def        
    
    def insert_bounds(self, bounds, copy=True):
        '''Insert cell bounds.

.. versionadded:: 1.6

.. seealso , `insert_data`, `remove_bounds`, `remove_data`

:Parameters:

    bounds: `Bounds`

    copy: `bool`, optional

:Returns:

    `None`

        '''
        if not getattr(bounds, 'isbounds', False):
            raise ValueError("bounds must be a 'Bounds' object")

        if copy:            
            bounds = bounds.copy()

        self._Bounds = bounds
    #--- End: def

    def remove_bounds(self):
        '''Remove cell bounds.

.. versionadded:: 1.6

.. seealso , `insert_bounds`, `insert_data`, `remove_data`

:Returns:

    out: `None` or `Bounds`

        '''
        if not self.hasbounds:
            return
        
        bounds = self.bounds
        del self._Bounds

        return bounds
    #--- End: def

    def squeeze(self, axes=None , copy=True):
        '''
        '''
        c = super(AbstractBoundedArray, self).squeeze(
            axes, copy=copy)

        if c.hasbounds:
            axes = self._parse_axes(axes)
            c.bounds.squeeze(axes, copy=False)

        return c
    #--- End: def        
    
#--- End: class
