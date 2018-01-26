from collections import abc

from .functions    import RTOL, ATOL, RELAXED_IDENTITIES
from .functions    import equals     as cf_equals

# ====================================================================
#
# Variable Mixin object
#
# ====================================================================

class VariableMixin(object):
    '''

Base class for storing a data array with metadata.

A variable contains a data array and metadata comprising properties to
describe the physical nature of the data.

All components of a variable are optional.

'''
    __metaclass__ = abc.ABCMeta

    def __getitem__(self, indices):
        '''

Called to implement evaluation of x[indices].

x.__getitem__(indices) <==> x[indices]

.. versionadded:: 1.6

'''
        data = self.get_data(None)
        if data is None:
            raise ValueError("j   m,.wuioy8y h;.jn")

        new = self.copy(data=False)
        new.set_data(data[indices])
        return new
    #--- End: def

    def __setitem__(self, indices, value):
        '''

Called to implement assignment to x[indices]

x.__setitem__(indices, value) <==> x[indices]

.. versionadded:: 1.6

'''
        data = self.get_data(None)
        if data is None:
            raise ValueError("Can't set elements when there is no data")    

        value = type(data).asdata(value)
        data[indices] = value
    #--- End: def

    def __str__(self):
        '''Called by the :py:obj:`str` built-in function.

x.__str__() <==> str(x)

        '''
        name = self.name('')

        data = self.get_data(None)
        if data is not None:
            dims = ', '.join([str(x) for x in data.shape])
            dims = '({0})'.format(dims)
        else:
            dims = ''

        # Units
        units = self.get_property('units', '')
        if self.isreftime:
            units += ' '+self.get_property('calendar', '')
            
        return '{0}{1} {2}'.format(self.name(''), dims, units)
    #--- End: def

    def _dump_properties(self, properties, prefix='', indent='')
        '''

.. versionadded:: 1.6

:Parameters:

    omit: sequence of `str`, optional
        Omit the given CF properties from the description.

    _level: `int`, optional

:Returns:

    out: `str`

:Examples:

'''
        string = []

        # Simple properties
        simple = self.properties()
        attrs  = sorted(set(simple) - set(omit))
        for prop, value in properties:
            name   = '{0}{1}{2} = '.format(indent, prefix, prop)
            value  = repr(value)
            subsequent_indent = ' ' * len(name)
            if value.startswith("'") or value.startswith('"'):
                subsequent_indent = '{0} '.format(subsequent_indent)
                
            string.append(textwrap.fill(name+value, 79,
                                        subsequent_indent=subsequent_indent))

        return '\n'.join(string)
    #--- End: def

    def copy(self, data=True):
        '''Return a deep copy.

``f.copy()`` is equivalent to ``copy.deepcopy(f)``.

.. versionadded:: 1.6

:Examples 1:

>>> g = f.copy()

:Returns:

    out: `{+Variable}`
        The deep copy.

:Examples 2:

>>> g = f.copy()
>>> g is f
False
>>> f.equals(g)
True
>>> import copy
>>> h = copy.deepcopy(f)
>>> h is f
False
>>> f.equals(g)
True

        '''
        new = type(self)(source=self, copy=True,
                         _use_source_data=data)
    #--- End: def

    @abc.abstractmethod
    def dump(self, display=True, field=None, key=None,
             _omit_properties=(), _prefix='', _title=None,
             _create_title=True, _level=0):
        '''

Return a string containing a full description of the instance.

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

>>> f.{+name}()
Data(1, 2) = [[2999-12-01 00:00:00, 3000-12-01 00:00:00]] 360_day
axis = 'T'
standard_name = 'time'

>>> f.{+name}(omit=('axis',))
Data(1, 2) = [[2999-12-01 00:00:00, 3000-12-01 00:00:00]] 360_day
standard_name = 'time'

'''
        indent0 = '    ' * _level
        indent1 = '    ' * (_level+1)

        string = []
        
        # ------------------------------------------------------------
        # Title
        # ------------------------------------------------------------
        if _create_title:
            if _title is None:
                string.append('{0}{1}: {2}'.format(indent0,
                                                   self.__class__.__name__,
                                                   self.name(default='')))
            else:
                string.append(indent0 + _title)
        #--- End: if
        
        # ------------------------------------------------------------
        # Properties
        # ------------------------------------------------------------
        properties = self.properties()
        if _omit_properties:
            for prop in properties.keys():
                if prop in _omit_properties:
                    del properties[prop]
        #--- End: if

        properties = self._dump_properties(properties,
                                           prefix=_prefix,
                                           indent=indent1)
        if properties:
            string.append(properties)

        # ------------------------------------------------------------
        # Data
        # ------------------------------------------------------------
        data = self.get_data(None)
        if data is not None:
            if field and key:
                ndim = data.ndim
                x = ['{0}({1})'.format(field.domain_axis_name(axis),
                                       field.domain_axes()[axis].size)
                     for axis in field.construct_axes(key)]

                x = x[:ndim]
                    
                if len(x) < ndim:
                    x.append(str(data.shape[len(x):]))
            else:
                x = [str(size) for size in data.shape]
           
            string.append('{0}{1}Data({2}) = {3}'.format(indent1,
                                                         _prefix,
                                                         ' '.join(x),
                                                         str(data)))

        string = '\n'.join(string)
       
        if display:
            print string
        else:
            return string
    #--- End: def

    def equals(self, other, rtol=None, atol=None, traceback=False,
               ignore_data_type=False, ignore_fill_value=False,
               ignore_properties=(), ignore_construct_type=False,
               _extra=()):
        '''

True if two {+variable}s are equal, False otherwise.

.. versionadded:: 1.6

:Parameters:

    other: n 
        The object to compare for equality.

    {+atol}

    {+rtol}

    ignore_fill_value: `bool`, optional
        If True then data arrays with different fill values are
        considered equal. By default they are considered unequal.

    traceback: `bool`, optional
        If True then print a traceback highlighting where the two
        {+variable}s differ.

    ignore_properties: `tuple`, optional
        The names of CF properties to omit from the comparison.

:Returns: 

    out: `bool`
        Whether or not the two {+variable}s are equal.

:Examples:

>>> f.equals(f)
True
>>> g = f + 1
>>> f.equals(g)
False
>>> g -= 1
>>> f.equals(g)
True
>>> f.setprop('name', 'name0')
>>> g.setprop('name', 'name1')
>>> f.equals(g)
False
>>> f.equals(g, ignore=['name'])
True

'''
        # Check for object identity
        if self is other:
            return True

        # Check that each instance is of the same type
        if not ignore_construct_type and not isinstance(other, self.__class__):
            if traceback:
                print("{0}: Incompatible types: {0}, {1}".format(
			self.__class__.__name__,
			other.__class__.__name__))
	    return False

        # ------------------------------------------------------------
        # Check the properties
        # ------------------------------------------------------------
        if ignore_fill_value:
            ignore_properties += ('_FillValue', 'missing_value')

        self_properties  = set(self.properties()).difference(ignore_properties)
        other_properties = set(other.properties()).difference(ignore_properties)
        if self_properties != other_properties:
            if traceback:
                print("{0}: Different properties: {1}, {2}".format( 
                    self.__class__.__name__,
                    self_properties, other_properties))
            return False

        if rtol is None:
            rtol = RTOL()
        if atol is None:
            atol = ATOL()

        for prop in self_properties:
            x = self.get_property(prop)
            y = other.get_property(prop)

            if not cf_equals(x, y, rtol=rtol, atol=atol,
                             ignore_fill_value=ignore_fill_value,
                             traceback=traceback):
                if traceback:
                    print("{0}: Different {1}: {2!r}, {3!r}".format(
                        self.__class__.__name__, prop, x, y))
                return False
        #--- End: for

        # ------------------------------------------------------------
        # Check the data
        # ------------------------------------------------------------
        if self.has_data() != other.has_data():
            if traceback:
                print("{0}: Different {1}".format(self.__class__.__name__, attr))
            return False
            
        if self.has_data():
            if not cf_equals(self.get_data(), other.get_data(),
                             rtol=rtol, atol=atol,
                             traceback=traceback,
                             ignore_data_type=ignore_data_type,
                             ignore_construct_type=ignore_construct_type,
                             ignore_fill_value=ignore_fill_value):
                if traceback:
                    print("{0}: Different {1}".format(self.__class__.__name__, attr))
                return False
        #--- End: for

        return True
    #--- End: def

    def expand_dims(self, position=0, copy=True):
        '''Insert a size 1 axis into the data array.

.. versionadded:: 1.6

.. seealso:: `squeeze`, `transpose`

:Examples 1:

>>> g = f.{+name}()

:Parameters:

    position: `int`, optional    
        Specify the position amongst the data array axes where the new
        axis is to be inserted. By default the new axis is inserted at
        position 0, the slowest varying position.

    {+copy}

:Returns:

    `None`

:Examples:

>>> v.{+name}(2)
>>> v.{+name}(-1)

        '''       
        if copy:
            v = self.copy()
        else:
            v = self

        data = v.get_data(None)
        if data is not None:
            data.expand_dims(position, copy=False)
        
        return v
    #--- End: def
    
    def HDF_chunks(self, *chunksizes):
        '''{+HDF_chunks}
        
.. versionadded:: 1.6

:Examples 1:
        
To define chunks which are the full size for each axis except for the
first axis which is to have a chunk size of 12:

>>> old_chunks = f.{+name}({0: 12})

:Parameters:

    {+chunksizes}

:Returns:

    out: `dict`
        The chunk sizes prior to the new setting, or the current
        current sizes if no new values are specified.

        '''
        if self.has_data():
            old_chunks = self.get_data().HDF_chunks(*chunksizes)
        else:
            old_chunks = None

#        if self.hasbounds:
#            self.bounds.HDF_chunks(*chunksizes)

        return old_chunks
    #--- End: def

    def name(self, default=None, ncvar=True):
        '''Return a name for the {+variable}.

By default the name is the first found of the following:

  1. The `standard_name` CF property.
  
  2. The `long_name` CF property, preceeded by the string
     ``'long_name:'``.

  3. If the *ncvar* parameter is True, the netCDF variable name as
     returned by the `ncvar` method, preceeded by the string
     ``'ncvar%'``.
  
  4. The value of the *default* parameter.

.. versionadded:: 1.6

:Examples 1:

>>> n = f.{+name}()
>>> n = f.{+name}(default='NO NAME')

:Parameters:

    default: optional
        If no name can be found then return the value of the *default*
        parameter. By default the default is `None`.

    ncvar: `bool`, optional

:Returns:

    out:
        The name.

:Examples 2:

>>> f.setprop('standard_name', 'air_temperature')
>>> f.setprop('long_name', 'temperature of the air')
>>> f.ncvar('tas')
>>> f.{+name}()
'air_temperature'
>>> f.delprop('standard_name')
>>> f.{+name}()
'long_name:temperature of the air'
>>> f.delprop('long_name')
>>> f.{+name}()
'ncvar%tas'
>>> f.ncvar(None)
>>> f.{+name}()
None
>>> f.{+name}('no_name')
'no_name'
>>> f.setprop('standard_name', 'air_temperature')
>>> f.{+name}('no_name')
'air_temperature'

        '''
        n = self.get_property('standard_name', None)
        if n is not None:
            return n

        n = self.get_property('long_name', None)
        if n is not None:
            return 'long_name:{0}'.format(n)

        if ncvar:
            n = self.ncvar()
            if n is not None:
                return 'ncvar%{0}'.format(n)
            
        return default
    #--- End: def
    
    def squeeze(self, axes=None, copy=True):
        '''Remove size 1 dimensions from the data array

.. versionadded:: 1.6

.. seealso:: `expand_dims`

:Examples 1:

>>> f.{+name}()

:Parameters:

    axes: (sequence of) `int`, optional
        The size 1 axes to remove. By default, all size 1 axes are
        removed. Size 1 axes for removal are identified by their
        integer positions in the data array.
    
    {+copy}

:Returns:

    out: `{+Variable}`

:Examples:

>>> f.{+name}(1)
>>> f.{+name}([1, 2])

        '''
        if copy:
            v = self.copy()
        else:
            v = self

        data = v.get_data(None)
        if data is not None:
            data.squeeze(axes, copy=False)

        return v
    #--- End: def

    # ----------------------------------------------------------------
    # Attribute (read only)
    # ----------------------------------------------------------------
    @property
    def dtarray(self):
        '''An independent numpy array of date-time objects.

Only applicable for reference time units.

If the calendar has not been set then the CF default calendar will be
used.

The data type of the data array is unchanged.

.. versionadded:: 1.6

.. seealso:: `array`, `asdatetime`, `asreftime`, `dtvarray`, `varray`

:Examples:

        '''
        if not self.hasdata:
            raise AttributeError("{} has no data".format(self.__class__.__name__))

        return self.data.dtarray
#
#        array = self.data.array
#
#        mask = None
#        if numpy.ma.isMA(array):
#            # num2date has issues if the mask is nomask
#            mask = array.mask
#            if mask is numpy.ma.nomask or not numpy.ma.is_masked(array):
#                array = array.view(numpy.ndarray)
#        #--- End: if
#
#        utime = Utime(self.getprop('units'),
#                      self.getptop('calendar', 'gregorian'))
#        array = utime.num2date(array)
#    
#        if mask is None:
#            # There is no missing data
#            array = numpy.array(array, dtype=object)
#        else:
#            # There is missing data
#            array = numpy.ma.masked_where(mask, array)
#            if not numpy.ndim(array):
#                array = numpy.ma.masked_all((), dtype=object)
#
#        return array
#    #--- End: def

    def datum(self, *index):
        '''

Return an element of the data array as a standard Python scalar.

The first and last elements are always returned with ``f.datum(0)``
and ``f.datum(-1)`` respectively, even if the data array is a scalar
array or has two or more dimensions.

.. versionadded:: 1.6

.. seealso:: `array`

:Parameters:

    index: optional
        Specify which element to return. When no positional arguments
        are provided, the method only works for data arrays with one
        element (but any number of dimensions), and the single element
        is returned. If positional arguments are given then they must
        be one of the following:

          * An integer. This argument is interpreted as a flat index
            into the array, specifying which element to copy and
            return.
         
              Example: If the data aray shape is ``(2, 3, 6)`` then:
                * ``f.{+name}(0)`` is equivalent to ``f.{+name}(0, 0, 0)``.
                * ``f.{+name}(-1)`` is equivalent to ``f.{+name}(1, 2, 5)``.
                * ``f.{+name}(16)`` is equivalent to ``f.{+name}(0, 2, 4)``.

            If *index* is ``0`` or ``-1`` then the first or last data
            array element respecitively will be returned, even if the
            data array is a scalar array or has two or more
            dimensions.
        ..
         
          * Two or more integers. These arguments are interpreted as a
            multidimensionsal index to the array. There must be the
            same number of integers as data array dimensions.
        ..
         
          * A tuple of integers. This argument is interpreted as a
            multidimensionsal index to the array. There must be the
            same number of integers as data array dimensions.
         
              Example: ``f.datum((0, 2, 4))`` is equivalent to
              ``f.datum(0, 2, 4)``; and ``f.datum(())`` is equivalent
              to ``f.datum()``.

:Returns:

    out:
        A copy of the specified element of the array as a suitable
        Python scalar.

:Examples:

>>> print f.array
2
>>> f.{+name}()
2
>>> 2 == f.{+name}(0) == f.{+name}(-1) == f.{+name}(())
True

>>> print f.array
[[2]]
>>> 2 == f.{+name}() == f.{+name}(0) == f.{+name}(-1)
True
>>> 2 == f.{+name}(0, 0) == f.{+name}((-1, -1)) == f.{+name}(-1, 0)
True

>>> print f.array
[[4 -- 6]
 [1 2 3]]
>>> f.{+name}(0)
4     
>>> f.{+name}(-1)
3     
>>> f.{+name}(1)
masked
>>> f.{+name}(4)
2     
>>> f.{+name}(-2)
2     
>>> f.{+name}(0, 0)
4     
>>> f.{+name}(-2, -1)
6     
>>> f.{+name}(1, 2)
3     
>>> f.{+name}((0, 2))
6

'''
        if not self.hasdata:
            raise ValueError(
                "ERROR: Can't return an element when there is no data array")
        
        return self.data.datum(*index)
    #--- End: def

    def _parse_axes(self, axes):
        if axes is None:
            return axes

        ndim = self.data.ndim
        return [(i + ndim if i < 0 else i) for i in axes]
    #--- End: def
    
    @property
    def isreftime(self):
        '''

.. versionadded:: 1.6

        '''
        units = self.getprop('units', None)
        if units is None:
            return bool(self.getprop('calendar', False))

        return 'since' in units
    #--- End: def

    def open(self):
        '''
'''
        if self.hasdata:
            self.data.open()
    #--- End: def

#--- End: class
