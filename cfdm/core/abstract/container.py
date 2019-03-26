from builtins import (object, str)
from future.utils import with_metaclass

import abc

from copy import copy, deepcopy


class Container(with_metaclass(abc.ABCMeta, object)):
    '''Abstract base class for storing components.

.. versionadded:: 1.7.0

    '''
    def __init__(self):
        '''**Initialisation**

A container is initialised with no parameters. Components are set
after initialisation with the `_set_component` method.

        '''
        self._components = {}
    #--- End: def
        
    def __deepcopy__(self, memo):
        '''Called by the `copy.deepcopy` function.

x.__deepcopy__() <==> copy.deepcopy(x)

.. versionadded:: 1.7.0

**Examples:**

>>> import copy
>>> y = copy.deepcopy(x)

        '''
        return self.copy()
    #--- End: def

    # ----------------------------------------------------------------
    # Private methods
    # ----------------------------------------------------------------
    def _default(self, default, message=None):
        '''<TODO>

.. versionadded:: 1.7.0

:Parameters:

    default: 
        <TODO>
        
    message: `str`, optional 
        <TODO>
        
:Returns:

    <TODO>

**Examples:**

<TODO>

        '''
        if isinstance(default, Exception):
            if message is not None and not default.args:
                default = copy(default)
                default.args = (message,)

            raise default
        
        return default
    #--- End: def
    
    def _del_component(self, component, default=ValueError()):
        '''Remove a component.

.. versionadded:: 1.7.0

.. seealso:: `_get_component`, `_has_component`, `_set_component`

:Parameters:

    component: 
        The name of the component to be removed.

    default: optional
        Return *default* if the component has not been set.

:Returns:

        The removed component. If unset then *default* is returned, if
        provided.

**Examples:**

>>> f._set_component('foo', 'bar')
>>> f._has_component('foo')
True
>>> f._get_component('foo')
'bar'
>>> f._del_component('foo')
'bar'
>>> f._has_component('foo')
False

        '''
        try:
            return self._components.pop(component)
        except KeyError:
             return self._default(default,
                                  "{!r} has no {!r} component".format(
                                      self.__class__.__name__, component))
    #--- End: def

    def _get_component(self, component, default=ValueError()):
        '''Return a component

.. versionadded:: 1.7.0

.. seealso:: `_del_component`, `_has_component`, `_set_component`

:Parameters:

    component: 
        The name of the component to be returned.

    default: optional
        Return *default* if the component has not been set.

:Returns:

        The component. If unset then *default* is returned, if
        provided.

**Examples:**

>>> f._set_component('foo', 'bar')
>>> f._has_component('foo')
True
>>> f._get_component('foo')
'bar'
>>> f._del_component('foo')
'bar'
>>> f._has_component('foo')
False

        '''
        try:            
            return self._components[component]
        except KeyError:
            return self._default(default,
                                 "{!r} object has no {!r} component".format(
                                     self.__class__.__name__, component))
    #--- End: def

    def _has_component(self, component):
        '''Whether a component has been set.

.. versionadded:: 1.7.0

.. seealso:: `_del_component`, `_get_component`, `_set_component`

:Parameters:

    component: 
        The name of the component.

:Returns:

     `bool`
        True if the component has been set, otherwise False.

**Examples:**

>>> f._set_component('foo', 'bar')
>>> f._has_component('foo')
True
>>> f._get_component('foo')
'bar'
>>> f._del_component('foo')
'bar'
>>> f._has_component('foo')
False

        '''
        return component in self._components
    #--- End: def

    def _set_component(self, component, value, copy=True):
        '''Set a component.

.. versionadded:: 1.7.0

.. seealso:: `_del_component`, `_get_component`, `_has_component`

:Parameters:

    component: `str`
        The name of the component.

    value:
        The value for the component.

:Returns:

     `None`

**Examples:**


>>> f._set_component('foo', 'bar')
>>> f._has_component('foo')
True
>>> f._get_component('foo')
'bar'
>>> f._del_component('foo')
'bar'
>>> f._has_component('foo')
False

        '''
        if copy:
            value = deepcopy(value)
            
        self._components[component] = value
    #--- End: def

    # ----------------------------------------------------------------
    # Methods
    # ----------------------------------------------------------------
    @abc.abstractmethod
    def copy(self):
        '''Return a deep copy.

``f.copy()`` is equivalent to ``copy.deepcopy(f)``.

.. versionadded:: 1.7.0

:Returns:

        The deep copy.

**Examples:**

>>> g = f.copy()

        '''
        raise NotImplementedError() # pragma: no cover
    #--- End: def
    
#--- End: class
