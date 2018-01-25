from collections import abc

from .construct import AbstractConstruct

# ====================================================================
#
# ArrayConstruct object
#
# ====================================================================

class AbstractArray(AbstractConstruct):
    '''

Base class for storing a data array with metadata.

A variable contains a data array and metadata comprising properties to
describe the physical nature of the data.

All components of a variable are optional.

'''
    __metaclass__ = abc.ABCMeta

    _special_properties = set(('_FillValue',
                               'missing_value'))

    def __init__(self, properties={}, data=None, source=None,
                 copy=True, _use_data=True):
        '''**Initialization**

:Parameters:

    properties: `dict`, optional
        Initialize properties from the dictionary's key/value pairs.

    data: `Data`, optional
        Provide a data array.
        
    source: `{+Variable}`, optional
        Take the attributes, CF properties and data array from the
        source {+variable}. Any attributes, CF properties or data
        array specified with other parameters are set after
        initialisation from the source {+variable}.

    copy: `bool`, optional
        If False then do not deep copy arguments prior to
        initialization. By default arguments are deep copied.

        '''
        self._properties = {}
        
        if source is not None:
            if not isinstance(source, AbstractArray):
                raise ValueError(
"ERROR: source must be a subclass of 'AbstractArray'. Got {!r}".format(
    source.__class__.__name__))

            # Data
            if _use_data and data is None:
                data = source.get_data(None)

            # Properties
            p = source.properties()
            if properties:
                p.update(properties)
            properties = p

        if properties:
            self.properties(properties, copy=copy, data=_use_data)

        if _use_data and data is not None:
            self.set_data(data, copy=copy)
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
        calendar = self.get_property('calendar', '')
        if calendar:
            units += ' '+calendar
            
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

#    @property
#    def data(self):
#        '''
#
#The `Data` object containing the data array.
#
#.. versionadded:: 1.6
#
#.. seealso:: `array`, `Data`, `hasdata`, `varray`
#
#:Examples:
#
#>>> if f.hasdata:
#...     print f.data
#
#'''       
#        if self.hasdata:
#            data = self._Data
#            data.fill_value = self._fill_value            
#            data.units      = self.get_property('units', None)
#            data.calendar   = self.get_property('calendar', None)
#            return data 
#
#        raise AttributeError("{} object doesn't have attribute 'data'".format(
#            self.__class__.__name__))
#    #--- End: def
#    @data.setter
#    def data(self, value):
#        old = getattr(self, 'data', None)
#
#        if old is None:
#            raise ValueError(
#"Can't set 'data' when data has not previously been set with the 'set_data' method")
#
#        if old.shape != value.shape: 
#            raise ValueError(
#"Can't set 'data' to new data with different shape. Consider the 'set_data' method.")
#       
#        self._Data = value
#    #--- End: def
    
    def get_data(self, *default):
        '''
        '''
        data = getattr(self, '_data', None)
        if data is not None:
            data.fill_value = self._fill_value            
            data.units      = self.get_property('units', None)
            data.calendar   = self.get_property('calendar', None)
            return data

        if default:
            return default[0]

        raise AttributeError("sdij ;soij in kl")
    #--- End: def

    def has_data(self):
        '''

True if there is a data array.

If present, the data array is stored in the `data` attribute.

.. versionadded:: 1.6

.. seealso:: `data`

:Examples:

>>> if f.has_data():
...     print f.data

'''      
        return hasattr(self, '_data')
    #--- End: def

    def del_data(self):
        '''Remove and return the data array.

.. versionadded:: 1.6

.. seealso:: `set_data`

:Returns: 

    out: `Data` or `None`
        The removed data array, or `None` if there isn't one.

:Examples:

>>> f.hasdata
True
>>> print f.data
[0, ..., 9] m
>>> d = f.remove_data()
>>> print d
[0, ..., 9] m
>>> f.hasdata
False
>>> print f.remove_data()
None

        '''
        if not self.has_data():
            return

        data = self._data
        del self._data
        return data
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
        
#        # ------------------------------------------------------------
#        # Extra arrays (e.g. bounds)
#        # ------------------------------------------------------------
#        for attribute in _extra:
#            x = getattr(self, attribute, None)
#            if x is None:
#                continue
#            
#            if not isinstance(x, AbstractArray):
#                string.append('{0}{1} = {2}'.format(indent1, attribute, x))
#                continue
#            
#            #            name = attribute.title().replace(' ', '')
#            
#            string.append(x.dump(display=False, field=field, key=key,
#                                 _prefix=_prefix+attribute+'.',
#                                 _create_title=False, _level=level+1))          
#
#        #-------------------------------------------------------------
#        # Ancillary properties (e.g. geometry_type)
#        # ------------------------------------------------------------
#        for prop, x in sorted(self.ancillary_properties().items()):
#            string.append('{0}{1}ancillary.{2} = {3}'.format(indent1, _prefix,
#                                                             ancillary, x))
#
##        for prop in sorted(getattr(self, '_ancillary_properties', [])):
##            x = getattr(self, prop, None)
##            if x is None:
##                continue
##
##            string.append('{0}{1}ancillary.{2} = {3}'.format(indent1, _prefix,
#                                                             ancillary, x))
#
#        # ------------------------------------------------------------
#        # Ancillary arrays (e.g. topology_connectivity)
#        # ------------------------------------------------------------
#        for ancillary, x in sorted(self.ancillary_arrays().items()):
#            if not isinstance(x, AbstractArray):
#                string.append('{0}{1}ancillary.{2} = {3}'.format(indent1, _prefix,
#                                                                 ancillary, x))
#                continue
#
#            string.append(x.dump(display=False, field=field, key=key,
#                                 _prefix=_prefix+'ancillary.'+ancillary+'.',
#                                 _create_title=False, _level=level+1))          
#
##        for ancillary in sorted(getattr(self, '_ancillary_arrays', [])):
##            x = getattr(self, ancillary, None)
##            if x is None:
##                continue
##
##            if not isinstance(x, AbstractArray):
##                string.append('{0}{1}ancillary.{2} = {3}'.format(indent1, _prefix,
##                                                                 ancillary, x))
##                continue
##
##            string.append(x.dump(display=False, field=field, key=key,
##                                 _prefix=_prefix+'ancillary.'+ancillary+'.',
##                                 _create_title=False, _level=level+1))          

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
#        _extra = ('data',) + tuple(sorted(self._ancillary_arrays)) + _extra
#
#        for attr in _extra:
        if self.has_data() != other.has_data():
            if traceback:
                print("{0}: Different {1}".format(self.__class__.__name__, attr))
            return False
            
        if self.has_data():
            if not self.get_data().equals(other.get_data(), rtol=rtol,
                                          atol=atol, traceback=traceback,
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
    
    def fill_value(self, default=None):
        '''Return the data array missing data value.

This is the value of the `missing_value` CF property, or if that is
not set, the value of the `_FillValue` CF property, else if that is
not set, ``None``. In the last case the default `numpy` missing data
value for the array's data type is assumed if a missing data value is
required.

.. versionadded:: 1.6

:Parameters:

    default: optional
        If the missing value is unset then return this value. By
        default, *default* is `None`. If *default* is the special
        value ``'netCDF'`` then return the netCDF default value
        appropriate to the data array's data type is used. These may
        be found as follows:

        >>> import netCDF4
        >>> print netCDF4.default_fillvals    

:Returns:

    out:
        The missing data value, or the value specified by *default* if
        one has not been set.

:Examples:

>>> f.{+name}()
None
>>> f._FillValue = -1e30
>>> f.{+name}()
-1e30
>>> f.missing_value = 1073741824
>>> f.{+name}()
1073741824
>>> del f.missing_value
>>> f.{+name}()
-1e30
>>> del f._FillValue
>>> f.{+name}()
None
>>> f,dtype
dtype('float64')
>>> f.{+name}(default='netCDF')
9.969209968386869e+36
>>> f._FillValue = -999
>>> f.{+name}(default='netCDF')
-999

        '''
        fillval = self._fill_value

        if fillval is None:
            if default == 'netCDF':
                d = self.get_data().dtype
                fillval = netCDF4.default_fillvals[d.kind + str(d.itemsize)]
            else:
                fillval = default 
        #--- End: if

        return fillval
    #--- End: def

    def set_property(self, prop, value):
        '''Set a CF or non-CF property.

.. versionadded:: 1.6

.. seealso:: `delprop`, `getprop`, `hasprop`

:Examples 1:

>>> f.setprop('standard_name', 'time')
>>> f.setprop('project', 'CMIP7')

:Parameters:

    prop: `str`
        The name of the property.

    value:
        The value for the property.

:Returns:

     `None`

        '''
        self._properties[prop] = value
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

    def has_property(self, prop):
        '''

Return True if a CF property exists, otherise False.

.. versionadded:: 1.6

.. seealso:: `delprop`, `getprop`, `setprop`

:Examples 1:

>>> if f.{+name}('standard_name'):
...     print 'Has standard name'

:Parameters:

    prop: `str`
        The name of the property.

:Returns:

     out: `bool`
         True if the CF property exists, otherwise False.

'''
        return prop in self._properties
    #--- End: def

    def set_data(self, data, copy=True):
        '''Insert a new data array into the variable in place.

.. versionadded:: 1.6

:Parameters:

    data: `Data`

    copy: `bool`, optional

:Returns:

    `None`

        '''
        if not copy:
            self._Data = data
        else:
            self._Data = data.copy()
    #--- End: def

    def get_property(self, prop, *default):
        '''

Get a CF property.

When a default argument is given, it is returned when the attribute
doesn't exist; without it, an exception is raised in that case.

.. versionadded:: 1.6

.. seealso:: `delprop`, `hasprop`, `setprop`

:Examples 1:

>>> f.{+name}('standard_name')

:Parameters:

    prop: `str`
        The name of the CF property to be retrieved.

    default: optional
        Return *default* if and only if the variable does not have the
        named property.

:Returns:

    out:
        The value of the named property or the default value, if set.

:Examples 2:

>>> f.setprop('standard_name', 'air_temperature')
>>> f.{+name}('standard_name')
'air_temperature'
>>> f.delprop('standard_name')
>>> f.{+name}('standard_name')
AttributeError: Field doesn't have CF property 'standard_name'
>>> f.{+name}('standard_name', 'foo')
'foo'

'''        
        d = self._properties

        if default:
            return d.get(prop, default[0])

        try:
            return d[prop]
        except KeyError:
            raise AttributeError("{} doesn't have CF property {}".format(
                self.__class__.__name__, prop))
    #--- End: def

    def del_property(self, prop):
        '''Delete a CF or non-CF property.

.. versionadded:: 1.6

.. seealso:: `getprop`, `hasprop`, `setprop`

:Examples 1:

>>> f.{+name}('standard_name')

:Parameters:

    prop: `str`
        The name of the property to be deleted.

:Returns:

     `None`

:Examples 2:

>>> f.setprop('project', 'CMIP7')
>>> f.{+name}('project')
>>> f.{+name}('project')
AttributeError: Can't delete non-existent property 'project'

        '''
        # Still here? Then delete a simple attribute
        try:
            del self._properties[prop]
        except KeyError:
            raise AttributeError(
                "Can't delete non-existent CF property {!r}".format(prop))
    #--- End: def

    def ncvar(self, *name):
        '''
        '''
        if not name:
            return self._ncvar


        name = name[0]
        self._ncvar = name

        return name
    #--- End: def
    
    def open(self):
        '''
'''
        if self.has_data():
            self.get_data().open()
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
    
    def properties(self, properties=None, clear=False, copy=True):
        '''Inspect or change the CF properties.

.. versionadded:: 1.6

:Examples 1:

>>> f.{+name}()

:Parameters:

    props: `dict`, optional   
        Set {+variable} attributes from the dictionary of values. If
        the *copy* parameter is True then the values in the *attrs*
        dictionary are deep copied

    clear: `bool`, optional
        If True then delete all CF properties.

    copy: `bool`, optional
        If False then any property values provided bythe *props*
        parameter are not copied before insertion into the
        {+variable}. By default they are deep copied.

:Returns:

    out: `dict`
        The CF properties prior to being changed, or the current CF
        properties if no changes were specified.

:Examples 2:

        '''
        out = self._properties
        if copy:            
            out = deepcopy(out)
        else:
            out = out.copy()
                    
        if clear:
            self._properties.clear()

        if not properties:
            return out

        # Still here?
        if copy:
            properties = deepcopy(properties)
        else:
            properties = properties.copy()

        # Delete None-valued properties
        for key, value in properties.items():
            if value is None:
                del properties[key]
        #--- End: for

        self._properties.update(properties)

        return out
    #--- End: def

#--- End: class
