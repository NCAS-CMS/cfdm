import abc

from copy import deepcopy

from .container import Container

# ====================================================================
#

#
# ====================================================================

class Properties(Container):
    '''

Base class for storing a data array with metadata.

A variable contains a data array and metadata comprising properties to
describe the physical nature of the data.

All components of a variable are optional.

'''
    __metaclass__ = abc.ABCMeta

    _special_properties = ()

    def __init__(self, properties=None, source=None, copy=True):
        '''**Initialization**

:Parameters:

    properties: `dict`, optional

    source: optional

    copy: `bool`, optional

        '''
        super(Properties, self).__init__(source=source)

        self._set_component('properties', None, {})
        
        if source is not None:
            properties = source.properties()
        elif not properties:
            properties = {}

        if properties:
            self.properties(properties, copy=copy)
    #--- End: def
        
    def __deepcopy__(self, memo):
        '''Called by the `copy.deepcopy` standard library function.

.. versionadded:: 1.6

        '''
        return self.copy()
    #--- End: def

    def __repr__(self):
        '''x.__repr__() <==> repr(x)

.. versionadded:: 1.6

        '''
        return '<{0}: {1}>'.format(self.__class__.__name__, str(self))
    #--- End: def

    def copy(self):
        '''Return a deep copy.

``f.copy()`` is equivalent to ``copy.deepcopy(f)``.

.. versionadded:: 1.6

:Examples 1:

>>> g = f.copy()

:Returns:

    out:
        The deep copy.

        '''
        return type(self)(source=self, copy=True)
    #--- End: def

    def del_property(self, prop):
        '''Delete a property.

A property describes an aspect of the construct that is independent of
the domain.

A property may have any name and any value. Some properties correspond
to netCDF attributes of variables (e.g. "units", "long_name", and
"standard_name"), or netCDF global file attributes (e.g. "history" and
"institution"),

.. versionadded:: 1.6

.. seealso:: `get_property`, `has_property`, `properties`, `set_property`

:Examples 1:

>>> f.del_property('standard_name')

:Parameters:

    prop: `str`
        The name of the property to be deleted.

:Returns:

     out:
        The value of the deleted property, or `None` if the property
        was not set.

:Examples 2:

>>> f.set_property('project', 'CMIP7')
>>> print f.del_property('project')
'CMIP7'
>>> print f.del_property('project')
None

        '''
        if prop not in self._special_properties:
            return self._del_component('properties', prop)
        else:
            return delattr(self, prop)
    #--- End: def

    def get_property(self, prop, *default):
        '''Return a property.

A property describes an aspect of the construct that is independent of
the domain.

A property may have any name and any value. Some properties correspond
to netCDF attributes of variables (e.g. "units", "long_name", and
"standard_name"), or netCDF global file attributes (e.g. "history" and
"institution"),

.. versionadded:: 1.6

.. seealso:: `del_property`, `has_property`, `properties`, `set_property`

:Examples 1:

>>> x = f.get_property('standard_name')

:Parameters:

    prop: `str`
        The name of the property to be retrieved.

    default: optional
        Return *default* if and only if the property has not been set.

:Returns:

    out:
        The value of the property or the default value. If the
        property has not been set, then *default* if provided
        or else raise an `AttributeError`.

:Examples 2:

>>> f.set_property('standard_name', 'air_temperature')
>>> print f.get_property('standard_name')
'air_temperature'
>>> f.del_property('standard_name')
>>> print f.get_property('standard_name')
AttributeError: Field doesn't have property 'standard_name'
>>> print f.get_property('standard_name', 'UNSET')
'UNSET'

        '''
        try:
            if prop not in self._special_properties:
                return self._get_component('properties', prop, *default)
            else:
                return getattr(self, prop, *default)
        except AttributeError:
            raise AttributeError("{!r} object has no CF property {!r}".format(
                self.__class__.__name__, prop))
    #--- End: def

    def has_property(self, prop):
        '''Whether a CF property has been set.

A property describes an aspect of the construct that is independent
of the domain.

A property may have any name and any value. Some properties correspond
to netCDF attributes of variables (e.g. "units", "long_name", and
"standard_name"), or netCDF global file attributes (e.g. "history" and
"institution"),

.. versionadded:: 1.6

.. seealso:: `del_property`, `get_property`, `properties`, `set_property`

:Examples 1:

>>> x = f.has_property('long_name')

:Parameters:

    prop: `str`
        The name of the property.

:Returns:

     out: `bool`
        True if the property has been set, otherwise False.

:Examples 2:

>>> if f.has_property('standard_name'):
...     print 'Has a standard name'

        '''
        if prop not in self._special_properties:
            return self._has_component('properties', prop)
        else:
            return hasattr(self, prop)
    #--- End: def

    def properties(self, properties=None, copy=True):
        '''Inspect or change the CF properties.

.. versionadded:: 1.6

:Examples 1:

>>> d = f.properties()

:Parameters:

    props: `dict`, optional   
        Set {+variable} attributes from the dictionary of values. If
        the *copy* parameter is True then the values in the *attrs*
        dictionary are deep copied

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
        existing = self._get_component('properties', None, None)

        if existing is None:
            existing = {}
            self._set_component('properties', None, existing)

        out = existing.copy()

        for prop in self._special_properties:
            value = getattr(self, prop, None)
            if value is not None:
                out[prop] = value

        if not properties:
            return out

        # Still here?
        if copy:
            properties = deepcopy(properties)

        existing.clear()
        existing.update(properties)

        for prop in self._special_properties:
            if prop in properties:
                self.set_property(prop, properties[prop])
        #--- End: for

        return out
    #--- End: def

    def set_property(self, prop, value):
        '''Set a property.

A property describes an aspect of the construct that is independent of
the domain.

A property may have any name and any value. Some properties correspond
to netCDF attributes of variables (e.g. "units", "long_name", and
"standard_name"), or netCDF global file attributes (e.g. "history" and
"institution"),

.. versionadded:: 1.6

.. seealso:: `del_property`, `get_property`, `has_property`, `properties`

:Examples 1:

>>> f.set_property('standard_name', 'time')

:Parameters:

    prop: `str`
        The name of the property.

    value:
        The value for the property.

:Returns:

     `None`

        '''
        if prop not in self._special_properties:
            self._set_component('properties', prop, value)
        else:
            setattr(self, prop, value)
    #--- End: def

#--- End: class
