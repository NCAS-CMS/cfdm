from collections import abc

from .construct import AbtractConstruct

# ====================================================================
#
# ArrayConstruct object
#
# ====================================================================

class AbstractArrayConstruct(AbstractConstruct):
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
                 copy=True):
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
        super(AbstractArrayConstruct, self).__init__()
        
        self._fill_value = None

        # _hasbounds is True if and only if there are cell bounds.
        self._hasbounds = False

        # _hasdata is True if and only if there is a data array
        self._hasdata = False

        self._ancillaries = set()
        
        # Initialize the _private dictionary, unless it has already
        # been set.
        if not hasattr(self, '_private'):
            self._private = {'special_attributes': {},
                             'properties'        : {}}
        
        if source is not None:
            if not getattr(source, 'isarrayconstruct', False):
                raise ValueError(
                    "ERROR: source must be (a subclass of) a ArrayConstruct: {}".format(
                        source.__class__.__name__))

            if data is None and source.hasdata:
                data = Data.asdata(source)

            p = source.properties()
            if properties:
                p.update(properties)
            properties = p
        #--- End: if

        if properties:
            self.properties(properties, copy=copy)

        if data is not None:
            self.insert_data(data, copy=copy)
    #--- End: def

    def __str__(self):
        '''Called by the :py:obj:`str` built-in function.

x.__str__() <==> str(x)

        '''
        name = self.name('')
        
        if self.hasdata:
            dims = ', '.join([str(x) for x in self.data.shape])
            dims = '({0})'.format(dims)
        else:
            dims = ''

        # Units
        units = self.getprop('units', '')
        calendar = self.getprop('calendar', '')
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
        #--- End: for

        return '\n'.join(string)
    #--- End: def

    # ================================================================
    # Attributes
    # ================================================================
    @property
    def _Data(self):
        '''The `Data` object containing the data array.

.. versionadded:: 1.6

        '''
        if self.hasdata:
            return self._private['Data']

        raise AttributeError("{} doesn't have any data".format(
            self.__class__.__name__))
    #--- End: def
    @_Data.setter
    def _Data(self, value):
        private = self._private
        private['Data'] = value

        self._hasdata = True
    #--- End: def
    @_Data.deleter
    def _Data(self):
        private = self._private
        data = private.pop('Data', None)

        if data is None:
            raise AttributeError(
                "Can't delete non-existent data".format(
                    self.__class__.__name__))

        self._hasdata = False
    #--- End: def

    @property
    def data(self):
        '''

The `Data` object containing the data array.

.. versionadded:: 1.6

.. seealso:: `array`, `Data`, `hasdata`, `varray`

:Examples:

>>> if f.hasdata:
...     print f.data

'''       
        if self.hasdata:
            data = self._Data
            data.fill_value = self._fill_value            
            data.units      = self.getprop('units', None)
            data.calendar   = self.getprop('calendar', None)
            return data 

        raise AttributeError("{} object doesn't have attribute 'data'".format(
            self.__class__.__name__))
    #--- End: def
    @data.setter
    def data(self, value):
        old = getattr(self, 'data', None)

        if old is None:
            raise ValueError(
"Can't set 'data' when data has not previously been set with the 'insert_data' method")

        if old.shape != value.shape: 
            raise ValueError(
"Can't set 'data' to new data with different shape. Consider the 'insert_data' method.")
       
        self._Data = value
    #--- End: def
    
    # ----------------------------------------------------------------
    # Attribute (read only)
    # ----------------------------------------------------------------
    @property
    def hasbounds(self):
        '''True if there are cell bounds.

If present then cell bounds are stored in the `!bounds` attribute.

.. versionadded:: 1.6

:Examples:

>>> if c.hasbounds:
...     print c.bounds

        '''      
        return self._hasbounds
    #--- End: def

    # ----------------------------------------------------------------
    # Attribute (read only)
    # ----------------------------------------------------------------
    @property
    def hasdata(self):
        '''

True if there is a data array.

If present, the data array is stored in the `data` attribute.

.. versionadded:: 1.6

.. seealso:: `data`, `hasbounds`

:Examples:

>>> if f.hasdata:
...     print f.data

'''      
        return self._hasdata
    #--- End: def

    def remove_data(self):
        '''Remove and return the data array.

.. versionadded:: 1.6

.. seealso:: `insert_data`

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
        if not self.hasdata:
            return

        data = self.data
        del self._Data

        return data
    #--- End: def

    def copy(self, _omit_special=None, _omit_properties=False,
             _omit_attributes=False):
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
        new = type(self)()

        self_dict = self.__dict__.copy()
        
        self_private = self_dict.pop('_private')
            
        new._fill_value = self_dict.pop('_fill_value')
        new._hasbounds  = self_dict.pop('_hasbounds')
        new._hasdata    = self_dict.pop('_hasdata')
            
        if self_dict and not _omit_attributes:        
            try:
                new.__dict__.update(loads(dumps(self_dict, -1)))
            except PicklingError:
                new.__dict__.update(deepcopy(self_dict))
                
        private = {}

        if self.hasdata:
            new.insert_data(self.data, copy=True)
 
        # ------------------------------------------------------------
        # Copy special attributes. These attributes are special
        # because they have a copy() method which return a deep copy.
        # ------------------------------------------------------------
        special = self_private['special_attributes'].copy()
        if _omit_special:            
            for prop in _omit_special:
                special.pop(prop, None)

        for prop, value in special.iteritems():
            special[prop] = value.copy()

        private['special_attributes'] = special

        if not _omit_properties:
            try:
                private['properties'] = loads(dumps(self_private['properties'], -1))
            except PicklingError:
                private['properties'] = deepcopy(self_private['properties'])
        else:
            private['properties'] = {}

        new._private = private

        if self.hasbounds:
            bounds = self.bounds.copy(_omit_data=_omit_data,
                                      _only_data=_only_data)
            new._set_special_attr('bounds', bounds)        

        return new
    #--- End: def

#    @abc.abstractmethod
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
        if self.hasdata:
            data = self.data
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
        #--- End: if
        
        # ------------------------------------------------------------
        # Ancillary objects
        # ------------------------------------------------------------
        for ancillary in getattr(self, '_ancillaries', ()):
            x = getattr(self, ancillary, None)
            if x is None:
                continue

            if not isinstance(x, ArrayConstruct):
                string.append('{0}{1} = {2}'.format(indent1, attr, repr(x)))
                continue
                              
#            name = attr.title().replace(' ', '')

            string.append(x.dump(display=False, field=field, key=key,
                                 _prefix=_prefix+ancillary+'.',
                                 _create_title=False, _level=level+1))          
        #--- End: for

        string = '\n'.join(string)
       
        if display:
            print string
        else:
            return string
    #--- End: def

    def equals(self, other, rtol=None, atol=None, traceback=False,
               ignore_data_type=False, ignore_fill_value=False,
               ignore_properties=(), ignore_construct_type=False,
               _extra=(), **kwargs):
        '''

True if two {+variable}s are equal, False otherwise.

.. versionadded:: 1.6

:Parameters:

    other: 
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
        #--- End: if

        # ------------------------------------------------------------
        # Check the simple properties
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
        #--- End: if

        if rtol is None:
            rtol = RTOL()
        if atol is None:
            atol = ATOL()

        for prop in self_properties:
            x = self.getprop(prop)
            y = other.getprop(prop)

            if not cf_equals(x, y, rtol=rtol, atol=atol,
                             ignore_fill_value=ignore_fill_value,
                             traceback=traceback):
                if traceback:
                    print("{0}: Different {1}: {2!r}, {3!r}".format(
                        self.__class__.__name__, prop, x, y))
                return False
        #--- End: for

        _extra += ('data',)

        for attr in _extra:
            self_hasattr  = hasattr(self, attr)
            other_hasattr = hasattr(other, attr)
            if self_hasattr != hasattr(other, attr):
                if traceback:
                    print("{0}: Different {1}".format(self.__class__.__name__, attr))
                return False
                
            if self_hasattr:
                if not getattr(self, attr).equals(getattr(other, attr),
                        rtol=rtol, atol=atol,
                        traceback=traceback,
                        ignore_data_type=ignore_data_type,
                        ignore_construct_type=ignore_construct_type,
                        ignore_fill_value=ignore_fill_value,
                        **kwargs):
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

        if self.hasdata:
            v.data.expand_dims(position, copy=False)
        
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
                d = self.data.dtype
                fillval = netCDF4.default_fillvals[d.kind + str(d.itemsize)]
            else:
                fillval = default 
        #--- End: if

        return fillval
    #--- End: def

    def setprop(self, prop, value):
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
        self._private['properties'][prop] = value
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

        if v.hasdata:
            v.data.squeeze(axes, copy=False)

        return v
    #--- End: def

    def hasprop(self, prop):
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
        return prop in self._private['properties']
    #--- End: def

    @property
    def isarrayconstruct(self):
        '''True DCH

.. versionadded:: 1.6

:Examples:

>>> f.sarrayconstruct
True
        '''
        return True
    #--- End: def

    def insert_data(self, data, copy=True):
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

    def getprop(self, prop, *default):
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
        d = self._private['properties']

        if default:
            return d.get(prop, default[0])

        try:
            return d[prop]
        except KeyError:
            raise AttributeError("{} doesn't have CF property {}".format(
                self.__class__.__name__, prop))
    #--- End: def

    def delprop(self, prop):
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
            del self._private['properties'][prop]
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
        if self.hasdata:
            self.data.open()
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
        if self.hasdata:
            old_chunks = self.data.HDF_chunks(*chunksizes)
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
        n = self.getprop('standard_name', None)
        if n is not None:
            return n

        n = self.getprop('long_name', None)
        if n is not None:
            return 'long_name:{0}'.format(n)

        if ncvar:
            n = self.ncvar()
            if n is not None:
                return 'ncvar%{0}'.format(n)
            
        return default
    #--- End: def
    
    def properties(self, props=None, clear=False, copy=True):
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
#        if copy:            
        out = deepcopy(self._private['properties'])
#        else:
#            out = self._simple_properties().copy()
            
#        # Include properties that are not listed in the simple
#        # properties dictionary
#        for prop in ('units', 'calendar'):
#            _ = getattr(self, prop, None)
#            if _ is not None:
#                out[prop] = _
#        #--- End: for

        if clear:
            self._private['properties'].clear()
            return out

        if not props:
            return out

        setprop = self.setprop
        delprop = self.delprop
        if copy:
            for prop, value in props.iteritems():
                if value is None:
                    # Delete this property
                    delprop(prop)
                else:
                    setprop(prop, deepcopy(value))
        else:
            for prop, value in props.iteritems():
                if value is None:
                    # Delete this property
                    delprop(prop)
                else:
                    setprop(prop, value)

        return out
    #--- End: def

#--- End: class
