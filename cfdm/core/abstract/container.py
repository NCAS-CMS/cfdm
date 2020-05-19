from builtins import (object, str)
from future.utils import with_metaclass

import abc

from copy import copy, deepcopy


class Container(with_metaclass(abc.ABCMeta, object)):
    '''Abstract base class for storing components.

    .. versionadded:: 1.7.0

    '''
    def __init__(self, source=None, copy=True):
        '''**Initialisation**

    A container is initialised with no parameters. Components are set
    after initialisation with the `_set_component` method.

        '''
        self._components = {}

        if source is not None:
            try:
                custom = source._get_component('custom', {})
            except AttributeError:
                custom = {}
            else:
                custom = custom.copy()
#                if custom:
#                        custom = deepcopy(custom)
#                    else:
#                        custom = custom.copy()
#                else:
#                    custom = {}
        else:
            custom = {}

        self._set_component('custom', custom, copy=False)

    def __deepcopy__(self, memo):
        '''Called by the `copy.deepcopy` function.

    x.__deepcopy__() <==> copy.deepcopy(x)

    .. versionadded:: 1.7.0

    **Examples:**

    >>> import copy
    >>> y = copy.deepcopy(x)

        '''
        return self.copy()

    # ----------------------------------------------------------------
    # Private methods
    # ----------------------------------------------------------------
    def _default(self, default, message=None):
        '''TODO

    .. versionadded:: 1.7.0

    :Parameters:

        default:
            TODO

        message: `str`, optional
            TODO

    :Returns:

        TODO

    **Examples:**

    TODO

        '''
        if isinstance(default, Exception):
            if message is not None and not default.args:
                default = copy(default)
                default.args = (message,)

            raise default

        return default

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

            The removed component. If unset then *default* is
            returned, if provided.

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

    @property
    def _custom(self):
        '''Storage for additional attributes.

    .. versionadded:: 1.7.4

    **Examples:**

    >>> f._custom
    {}
    >>> f._custom['feature'] = ['f']
    >>> g = f.copy()
    >>> g._custom['feature'][0] = 'g'
    >>> f._custom
    {'feature': ['f']}
    >>> g._custom
    {'feature': ['g']}
    >>> del g._custom['feature']
    >>> f._custom
    {'feature': ['f']}
    >>> g._custom
    {}

    '''
        return self._get_component('custom')

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
                                 "{!r} has no {!r} component".format(
                                     self.__class__.__name__, component))

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

    # ----------------------------------------------------------------
    # Methods
    # ----------------------------------------------------------------
    def copy(self):
        '''Return a deep copy.

    ``f.copy()`` is equivalent to ``copy.deepcopy(f)``.

    .. versionadded:: 1.7.0

    :Returns:

            The deep copy.

    **Examples:**

    >>> g = f.copy()

        '''
        return type(self)(source=self, copy=True)

# --- End: class
