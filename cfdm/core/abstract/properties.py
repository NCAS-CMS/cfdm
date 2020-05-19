from future.utils import with_metaclass
from builtins import (str, super)

import abc

from copy import deepcopy

from . import Container


class Properties(with_metaclass(abc.ABCMeta, Container)):
    '''Abstract base class for an object with descriptive properties.

    .. versionadded:: 1.7.0

    '''
    def __init__(self, properties=None, source=None, copy=True):
        '''**Initialization**

    :Parameters:

        properties: `dict`, optional
            Set descriptive properties. The dictionary keys are
            property names, with corresponding values. Ignored if the
            *source* parameter is set.

            Properties may also be set after initialisation with the
            `set_properties` and `set_property` methods.

            *Parameter example:*
               ``properties={'standard_name': 'altitude'}``

        source: optional
            Initialize the properties from those of *source*.

        copy: `bool`, optional
            If False then do not deep copy input parameters prior to
            initialization By default parameters are deep copied.

        '''
        super().__init__(source=source, copy=copy)

        if source is not None:
            try:
                properties = source.properties()
            except AttributeError:
                properties = None
        # --- End: if

        self._set_component('properties', {}, copy=False)

        if properties is not None:
            self.set_properties(properties, copy=copy)

    # ----------------------------------------------------------------
    # Methods
    # ----------------------------------------------------------------
    def clear_properties(self):
        '''Remove all properties.

    .. versionadded:: 1.7.0

    .. seealso:: `del_property` `properties`, `set_properties`

    :Returns:

        `dict`
            The properties that have been removed.

    **Examples:**

    >>> f.properties()
    {}
    >>> f.set_properties({'standard_name': 'air_pressure', 'long_name': 'Air Pressure'})
    >>> f.properties()
    {'standard_name': 'air_pressure',
     'foo': 'bar',
     'long_name': 'Air Pressure'}
    >>> f.set_properties({'standard_name': 'air_pressure', 'foo': 'bar'})
    >>> f.properties()
    {'standard_name': 'air_pressure',
     'foo': 'bar',
     'long_name': 'Air Pressure'}
    >>> f.clear_properties()
    {'standard_name': 'air_pressure',
     'foo': 'bar',
     'long_name': 'Air Pressure'}
    >>> f.properties()
    {}

        '''
        out = self._get_component('properties')
        self._set_component('properties', {})
        return out.copy()

    def del_property(self, prop, default=ValueError()):
        '''Remove a property.

    .. versionadded:: 1.7.0

    .. seealso:: `clear_properties`, `get_property`, `has_property`,
                 `properties`, `set_property`

    :Parameters:

        prop: `str`
            The name of the property to be removed.

            *Parameter example:*
               ``prop='long_name'``

        default: optional
            Return the value of the *default* parameter if the
            property has not been set. If set to an `Exception`
            instance then it will be raised instead.

    :Returns:

            The removed property.

    **Examples:**

    >>> f.set_property('project', 'CMIP7')
    >>> f.has_property('project')
    True
    >>> f.get_property('project')
    'CMIP7'
    >>> f.del_property('project')
    'CMIP7'
    >>> f.has_property('project')
    False
    >>> print(f.del_property('project', None))
    None
    >>> print(f.get_property('project', None))
    None

        '''
        try:
            return self._get_component('properties').pop(prop)
        except KeyError:
            return self._default(default,
                                 "{!r} has no {!r} property".format(
                                 self.__class__.__name__, prop))

    def get_property(self, prop, default=ValueError()):
        '''Return a property.

    .. versionadded:: 1.7.0

    .. seealso:: `del_property`, `has_property`, `properties`,
                 `set_property`

    :Parameters:

        prop: `str`
            The name of the property to be returned.

            *Parameter example:*
               ``prop='standard_name'``

        default: optional
            Return the value of the *default* parameter if the
            property has not been set. If set to an `Exception`
            instance then it will be raised instead.

    :Returns:

            The value of the property.

    **Examples:**

    >>> f.set_property('project', 'CMIP7')
    >>> f.has_property('project')
    True
    >>> f.get_property('project')
    'CMIP7'
    >>> f.del_property('project')
    'CMIP7'
    >>> f.has_property('project')
    False
    >>> print(f.del_property('project', None))
    None
    >>> print(f.get_property('project', None))
    None

        '''
        try:
            return self._get_component('properties')[prop]
        except KeyError:
            return self._default(default,
                                 "{!r} has no {!r} property".format(
                                     self.__class__.__name__, prop))

    def has_property(self, prop):
        '''Whether a property has been set.

    .. versionadded:: 1.7.0

    .. seealso:: `del_property`, `get_property`, `properties`,
                 `set_property`

    :Parameters:

        prop: `str`
            The name of the property.

            *Parameter example:*
               ``prop='long_name'``

    :Returns:

        `bool`
            True if the property has been set, otherwise False.

    **Examples:**

    >>> f.set_property('project', 'CMIP7')
    >>> f.has_property('project')
    True
    >>> f.get_property('project')
    'CMIP7'
    >>> f.del_property('project')
    'CMIP7'
    >>> f.has_property('project')
    False
    >>> print(f.del_property('project', None))
    None
    >>> print(f.get_property('project', None))
    None

        '''
        return prop in self._get_component('properties')

    def properties(self):
        '''Return all properties.

    .. versionadded:: 1.7.0

    .. seealso:: `clear_properties`, `get_property`, `has_property`
                 `set_properties`

    :Returns:

        `dict`
            The properties.

    **Examples:**

    >>> f.properties()
    {}
    >>> f.set_properties({'standard_name': 'air_pressure', 'long_name': 'Air Pressure'})
    >>> f.properties()
    {'standard_name': 'air_pressure',
     'foo': 'bar',
     'long_name': 'Air Pressure'}
    >>> f.set_properties({'standard_name': 'air_pressure', 'foo': 'bar'})
    >>> f.properties()
    {'standard_name': 'air_pressure',
     'foo': 'bar',
     'long_name': 'Air Pressure'}
    >>> f.clear_properties()
    {'standard_name': 'air_pressure',
     'foo': 'bar',
     'long_name': 'Air Pressure'}
    >>> f.properties()
    {}

        '''
        return self._get_component('properties').copy()

    def set_properties(self, properties, copy=True):
        '''Set properties.

    .. versionadded:: 1.7.0

    .. seealso:: `clear_properties`, `properties`, `set_property`

    :Parameters:

        properties: `dict`
            Store the properties from the dictionary supplied.

            *Parameter example:*

              ``properties={'standard_name': 'altitude', 'foo': 'bar'}``

        copy: `bool`, optional
            If False then any property values provided by the
            *properties* parameter are not copied before insertion. By
            default they are deep copied.

    :Returns:

        `None`

    **Examples:**

    >>> f.properties()
    {}
    >>> f.set_properties({'standard_name': 'air_pressure', 'long_name': 'Air Pressure'})
    >>> f.properties()
    {'standard_name': 'air_pressure',
     'foo': 'bar',
     'long_name': 'Air Pressure'}
    >>> f.set_properties({'standard_name': 'air_pressure', 'foo': 'bar'})
    >>> f.properties()
    {'standard_name': 'air_pressure',
     'foo': 'bar',
     'long_name': 'Air Pressure'}
    >>> f.clear_properties()
    {'standard_name': 'air_pressure',
     'foo': 'bar',
     'long_name': 'Air Pressure'}
    >>> f.properties()
    {}

        '''
        if copy:
            properties = deepcopy(properties)
        else:
            properties = properties.copy()

        self._get_component('properties').update(properties)

    def set_property(self, prop, value, copy=True):
        '''Set a property.

    .. versionadded:: 1.7.0

    .. seealso:: `del_property`, `get_property`, `has_property`,
                 `properties`, `set_properties`

    :Parameters:

        prop: `str`
            The name of the property to be set.

        value:
            The value for the property.

        copy: `bool`, optional
            If True then set a deep copy of *value*.

    :Returns:

         `None`

    **Examples:**

    >>> f.set_property('project', 'CMIP7')
    >>> f.has_property('project')
    True
    >>> f.get_property('project')
    'CMIP7'
    >>> f.del_property('project')
    'CMIP7'
    >>> f.has_property('project')
    False
    >>> print(f.del_property('project', None))
    None
    >>> print(f.get_property('project', None))
    None

        '''
        if copy:
            value = deepcopy(value)

        self._get_component('properties')[prop] = value

# --- End: class
