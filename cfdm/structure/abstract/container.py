from builtins import (object, str)
from future.utils import with_metaclass

import abc

from copy import deepcopy

_MUST_IMPLEMENT = 'This method must be implemented'


class Container(with_metaclass(abc.ABCMeta, object)):
    '''Abstract base class for storing object components.

    '''
    
    def __init__(self):
        '''**Initialization**

:Parameters:

    source: optional
        Initialise the components from the object given by
        *source*. Note that the components are not deep copied.

        '''
        self._components = {}
    #--- End: def
        
    def __repr__(self):
        '''x.__repr__() <==> repr(x)

        '''
        return '<{0}: {1}>'.format(self.__class__.__name__, str(self))
    #--- End: def

    def __str__(self):
        '''x.__str__() <==> str(x)

        '''
        out = sorted(self._components)
        return ', '.join(out)
    #--- End: def

    def _del_component(self, component):
        '''Delete a component.

.. seealso:: `_get_component`, `_has_component`, `_set_component`

:Parameters:

    component: 
        The name of the component to be deleted.

:Returns:

     out:
        The deleted component, or `None` if the component was not set.

:Examples:

>>> f._set_component('ncvar', 'air_temperature')
>>> f._has_component('ncvar')
True
>>> f._get_component('ncvar')
'air_temperature'
>>> f._del_component('ncvar')
'air_temperature'
>>> f._has_component('ncvar')
False

        '''
        return self._components.pop(component, None)
    #--- End: def

    def _del_component_key(self, component, key):
        '''Delete a component

.. seealso:: `_get_component`, `_has_component`, `_set_component`

:Parameters:

    component: 
        The name of the property to be deleted.

    key: *optional*
        If set then it is assumed that the component is a `dict` from
        which key *key* is deleted, rather than the whole component.

:Returns:

     out:
        The deleted component, or `None` if the component was not set.

:Examples:

>>> f._set_component('ncvar', None, 'air_temperature')
>>> f._has_component('ncvar')
True
>>> f._get_component('ncvar', None)
'air_temperature'
>>> f._del_component('ncvar')
'air_temperature'
>>> f._has_component('ncvar')
False

>>> f._set_component('butterfly', None, {'ilex': 'hairstreak', 'common': 'blue'})
>>> f._has_component('butterfly')
True
>>> f._get_component('butterfly', 'ilex')
'hairstreak'
>>> f._del_component('butterfly', key='ilex')
'hairstreak'
>>> f._get_component('butterfly', None)
{'common': 'blue'}
>>> f._del_component('butterfly')
{'common': 'blue'}
>>> f._has_component('butterfly')
False

        '''
        return self._components[component].pop(key, None)
    #--- End: def

    def _dict_component(self, component, replacement=None, copy=True):
        '''

:Examples 1:

:Parameters:

:Returns:

    out: `dict`

:Examples 2:

        '''
        existing = self._get_component(component, None)

        if existing is None:
            existing = {}
            self._set_component(component, existing)

        out = existing.copy()

        if not replacement:
            return out

        # Still here?
        if copy:
            replacement = deepcopy(replacement)

        existing.clear()
        existing.update(replacement)

        return out
    #--- End: def

    def _get_component(self, component, *default):
        '''Return a component

.. seealso:: `_del_component`, `_has_component`, `_set_component`

:Parameters:

    component: 
        The name of the property to be returned.

    default: optional
        If the component has not been set then the *default* parameter
        is returned, if provided.

:Returns:

     out:
        The component. If the component has not been set then the
        *default* parameter is returned, if provided.

:Examples:

>>> f._set_component('ncvar', 'air_temperature')
>>> f._has_component('ncvar')
True
>>> f._get_component('ncvar')
'air_temperature'
>>> f._del_component('ncvar')
'air_temperature'
>>> f._has_component('ncvar')
False

        '''
        value = self._components.get(component)
        
        if value is None:
            if default:
                return default[0]

            raise AttributeError("{!r} object has no {!r} component".format(
                self.__class__.__name__, component))
            
        return value
    #--- End: def

    def _get_component_key(self, component, key, *default):
        '''Return a component

.. seealso:: `_del_component`, `_has_component`, `_set_component`

:Parameters:

    component: 
        The name of the property to be returned.

    key:
        If not `None` then it is assumed that the component is a
        `dict` from which key *key* is returned, rather than the whole
        component.

    default: optional

        If the component, or dictionary key, has not been set then the
        of *default* parameter is returned, if provided.

:Returns:

     out:
        The component or, if the *key* parameter is not `None`, the
        value of the dictionary component with key *key*. If the
        component, or dictionary componet key, has not been set then
        the of *default* parameter is returned, if provided.

:Examples:

>>> f._set_component('ncvar', None, 'air_temperature')
>>> f._has_component('ncvar')
True
>>> f._get_component('ncvar', None)
'air_temperature'
>>> f._del_component('ncvar')
'air_temperature'
>>> f._has_component('ncvar')
False

>>> f._set_component('butterfly', None, {'ilex': 'hairstreak', 'common': 'blue'})
>>> f._has_component('butterfly')
True
>>> f._get_component('butterfly', 'ilex')
'hairstreak'
>>> f._del_component('butterfly', key='ilex')
'hairstreak'
>>> f._get_component('butterfly', None)
{'common': 'blue'}
>>> f._del_component('butterfly')
{'common': 'blue'}
>>> f._has_component('butterfly')
False

>>> f._set_component('ncvar', None, 'air_temperature')
>>> f._get_component('ncvar', None, 'ncvar is unset')
'air_temperature'
>>> f._del_component('ncvar')
'air_temperature'
>>> f._get_component('ncvar', None, 'ncvar is unset')
'ncvar is unset'

>>> f._set_component('butterfly', None, {'poplar': 'admiral'})
>>> f._get_component('butterfly', 'poplar', 'no poplar butterly')
'admiral'
>>> f._get_component('butterfly', 'small', 'no small butterly')
'no small butterly'

        '''
        component = self._components[component]

        value = component.get(key)
        
        if value is None:
            if default:
                return default[0]

            raise AttributeError("Component {!r} of {!r} object has no key {!r}".format(
                component, self.__class__.__name__, key))
        
        return value
    #--- End: def

    def _has_component(self, component):
        '''Whether a property has been set.

.. seealso:: `_del_component`, `_get_component`, `_set_component`

:Parameters:

    component: 
        The name of the property to be returned.

:Returns:

     out: `bool`
        True if the component has been set, otherwise False.

:Examples:

>>> f._set_component('ncvar', 'air_temperature')
>>> f._has_component('ncvar')
True
>>> f._get_component('ncvar')
'air_temperature'
>>> f._del_component('ncvar')
'air_temperature'
>>> f._has_component('ncvar')
False

        '''
        return component in self._components
    #--- End: def

    def _has_component_key(self, component, key):
        '''
:Examples:

>>> f._set_component('ncvar', None, 'air_temperature')
>>> f._has_component('ncvar')
True
>>> f._get_component('ncvar', None)
'air_temperature'
>>> f._del_component('ncvar')
'air_temperature'
>>> f._has_component('ncvar')
False

>>> f._set_component('butterfly', None, {'ilex': 'hairstreak', 'common': 'blue'})
>>> f._has_component('butterfly')
True
>>> f._get_component('butterfly', 'ilex')
'hairstreak'
>>> f._del_component('butterfly', key='ilex')
'hairstreak'
>>> f._get_component('butterfly', None)
{'common': 'blue'}
>>> f._del_component('butterfly')
{'common': 'blue'}
>>> f._has_component('butterfly')
False

        '''
        component = self._components[component]
        return key in component
    #--- End: def

    def _set_component(self, component, value):
        '''Set a component.

.. seealso:: `_del_component`, `_get_component`, `_has_component`

:Parameters:

    component: `str`
        The name of the component.

    value:
        The value for the component.

:Returns:

     `None`

:Examples:


>>> f._set_component('ncvar', 'air_temperature')
>>> f._has_component('ncvar')
True
>>> f._get_component('ncvar')
'air_temperature'
>>> f._del_component('ncvar')
'air_temperature'
>>> f._has_component('ncvar')
False

        '''
        self._components[component] = value
    #--- End: def

    def _set_component_key(self, component, key, value):
        '''
:Examples:

>>> f._set_component('ncvar', None, 'air_temperature')
>>> f._has_component('ncvar')
True
>>> f._get_component('ncvar', None)
'air_temperature'
>>> f._del_component('ncvar')
'air_temperature'
>>> f._has_component('ncvar')
False

>>> f._set_component('butterfly', None, {'ilex': 'hairstreak', 'common': 'blue'})
>>> f._has_component('butterfly')
True
>>> f._get_component('butterfly', 'ilex')
'hairstreak'  
>>> f._del_component('butterfly', key='ilex')
'hairstreak'
>>> f._get_component('butterfly', None)
{'common': 'blue'}
>>> f._del_component('butterfly')
{'common': 'blue'}
>>> f._has_component('butterfly')
False

        '''
        self._components[component][key] = value
    #--- End: def

    @abc.abstractmethod
    def copy(self):
        '''Return a deep copy.

``f.copy()`` is equivalent to ``copy.deepcopy(f)``.

:Examples 1:

>>> g = f.copy()

:Returns:

    out:
        The deep copy.

        '''
        raise NotImplementedError(_MUST_IMPLEMENT)
    #--- End: def
    
#--- End: class
