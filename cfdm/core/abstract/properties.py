from future.utils import with_metaclass
from builtins import (str, super)

import abc

from copy import deepcopy

from . import Container


class Properties(with_metaclass(abc.ABCMeta, Container)):
    '''Abstract base class for an object with descriptive properties.

.. versionadded:: 1.7
    '''
    def __init__(self, properties=None, source=None, copy=True):
        '''**Initialization**

:Parameters:

    properties: `dict`, optional
        Set descriptive properties. The dictionary keys are property
        names, with corresponding values. Ignored if the *source*
        parameter is set.

        *Example:*
           ``properties={'standard_name': 'altitude'}``
        
        Properties may also be set after initialisation with the
        `properties` and `set_property` methods.

    source: optional
        Initialize the properties from those of *source*.

    copy: `bool`, optional
        If False then do not deep copy input parameters prior to
        initialization By default parameters are deep copied.

        '''
        super().__init__()

        self._set_component('properties', {}, copy=False)
        
        if source is not None:
            try:
                properties = source.properties()
            except AttributeError:
                properties = None
        #--- End: if
        
        if properties:
            self.properties(properties, copy=copy)
    #--- End: def

    # ----------------------------------------------------------------
    # Methods
    # ----------------------------------------------------------------
    def copy(self):
        '''Return a deep copy.

``f.copy()`` is equivalent to ``copy.deepcopy(f)``.

.. versionadded:: 1.7

:Returns:

    out:
        The deep copy.

**Examples:**

>>> g = f.copy()

        '''
        return type(self)(source=self, copy=True)
    #--- End: def

    def del_property(self, prop, *default):
        '''Remove a property.

.. versionadded:: 1.7

.. seealso:: `get_property`, `has_property`, `properties`,
             `set_property`

:Parameters:

    prop: `str`
        The name of the property to be removed.

        *Example:*
           ``prop='long_name'``

    default: optional
        Return *default* if the property has not been set.

:Returns:

     out:
        The removed property. If unset then *default* is returned, if
        provided.

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
            if default:
                return default[0]

            raise AttributeError("{!r} has no {!r} property".format(
                self.__class__.__name__, prop))
    #--- End: def

    def get_property(self, prop, *default):
        '''Return a property.

.. versionadded:: 1.7

.. seealso:: `del_property`, `has_property`, `properties`,
             `set_property`

:Parameters:

    prop: `str`
        The name of the property to be returned.

        *Example:*
           ``prop='standard_name'``

    default: optional
        Return *default* if the property has not been set.

:Returns:

    out:
        The value of the property. If unset then *default* is
        returned, if provided.

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
            if default:
                return default[0]

            raise AttributeError("{!r} has no {!r} property".format(
                self.__class__.__name__, prop))
    #--- End: def

    def has_property(self, prop):
        '''Whether a property has been set.

.. versionadded:: 1.7

.. seealso:: `del_property`, `get_property`, `properties`,
             `set_property`

:Parameters:

    prop: `str`
        The name of the property.

        *Example:*
           ``prop='long_name'``

:Returns:

     out: `bool`
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
    #--- End: def

    def properties(self, properties=None, copy=True):
        '''Return or replace all properties.

.. versionadded:: 1.7

.. seealso:: `del_property`, `get_property`, `has_property`,
             `set_property`

:Parameters:

    properties: `dict`, optional   
        Replace all existing properties with those specified in the
        dictionary. If the dictionary is empty then all properties
        will be removed.

        *Example:*
          ``properties={'standard_name': 'altitude', 'foo': 'bar'}``
        
        *Example:*
          ``properties={}``        

    copy: `bool`, optional
        If False then any property values provided by the *properties*
        parameter are not copied before insertion. By default they are
        deep copied.

:Returns:

    out: `dict`
        The properties prior to being changed, or the current
        properties if no changes were specified.

**Examples:**

>>> p = f.properties({'standard_name': 'altitude', 'foo': 'bar'})
>>> f.properties()
{'standard_name': 'altitude',
 'foo': 'bar'}
>>> f.properties({})
{'standard_name': 'altitude',
 'foo': 'bar'}
>>> f.properties()
{}

        '''
        out = self._get_component('properties').copy()

        if properties is not None:
            if copy:
                properties = deepcopy(properties)                
            else:
                properties = properties.copy()

            self._set_component('properties', properties, copy=False)

        return out
    #--- End: def

    def set_property(self, prop, value, copy=True):
        '''Set a property.

.. versionadded:: 1.7

.. seealso:: `del_property`, `get_property`, `has_property`,
             `properties`

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
    #--- End: def

#--- End: class
