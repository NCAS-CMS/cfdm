import abc
import inspect
import re

from copy import copy, deepcopy

from . import RewriteDocstringMeta


class Container(metaclass=RewriteDocstringMeta): #abc.ABCMeta):
    '''Base class for storing components.

    .. versionadded:: 1.7.0

    '''
    def __init__(self, source=None, copy=True):
        '''**Initialisation**

        '''
        self._components = {}
                
        if source is not None:
            try:
                custom = source._get_component('custom', {})
            except AttributeError:
                custom = {}
            else:
                custom = custom.copy()
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

    def __docstring_substitution__(self):
        '''TODO

    Substitutions may be easily modified by overriding the
    __docstring_substitution__ method. Modifications can be applied to
    any class, and will only apply to that class and all of its
    subclases.

       def __docstring_substitution__(self):
           def upper(match):
               return match.group(1).upper()

           out = super().__docstring_substitution__()

           out['{{repr}}'] = 'CF: ', 

           out['{{foo}}'] = 'bar', 

           out['{{parameter: `int`}}'] = """parameter: `int`
               This parameter does something to `{{class}}`
               instances. It has no default value.""",

           # Convert the text to upper case
           out['{{<upper>}}'] = (re.compile('{{<upper (.*?>}}'), upper)

           return out

    To disable docstring substitutions for a parent class and all of
    its subclasses, override this method on the parent class to return
    an empty dictionary. In this case note that substitions will still
    be applied to methods inherited by the parent class, and any
    special class name substitutions will use the class name of the
    class that defines the method.

        '''
        def _replacement_class(match, core=False):
            class_name = match.group(1)
            if core:
                class_name = 'core.' + class_name
                
            return class_name

        return {
            # --------------------------------------------------------
            # Special susbstitutions that depend on the class
            # containing the docstring. Do not override these.
            # --------------------------------------------------------
            # Replace {{package}} with the package name
            '{{package}}': True,
            # Replace {{class}} with the name of the parent class
            # method
            '{{class}}': True,
            # Replace {{+Name}} with Name unless the parent class is
            # in the cfdm.core package, in whcih case replace it with
            # core.Name.
            #
            # E.g. {{+Data}} is replaced by either Data or core.Data
            '{{+class}}': (re.compile('{{\+(\w.*?)}}'), _replacement_class),
            
            # --------------------------------------------------------
            # General substition. The key must not contain a colon
            # (:). The key must not contain a plus (+). The key must
            # not be of the form {{<...>}}.
            # --------------------------------------------------------
            '{{repr}}': '',

            # --------------------------------------------------------
            # General regex substition. The key must be of the form
            # {{<name>}}. The key is not expected to appear in te
            # docstring that form. Instead, the text to be operated on
            # should follow the name inside the angle brackets. The
            # key must not contain a colon (:). The key must not
            # contain a plus (+).
            #
            # The value must be tuple containing a compiled regular
            # expression and function to define the susbstition for
            # each occurrence. The function should operate on the
            # Match object returned by the evaulation of the regular
            # expression.
            # --------------------------------------------------------

            # --------------------------------------------------------
            # Keyword parameter description substition. The key must
            # contain a colon (:). Special substitutions will be
            # applied to these values
            # --------------------------------------------------------
            '{{default: optional}}': '''default: optional
            Return the value of the *default* parameter if data have
            not been set. If set to an `Exception` instance then it
            will be raised instead.''',
        }
    
    # ----------------------------------------------------------------
    # Private methods
    # ----------------------------------------------------------------
    def _default(self, default, message=None):
        '''Parse and return the default value for anoyther method.

    .. versionadded:: 1.7.0

    :Parameters:

        default:
            TODO

        message: `str`, optional
            TODO

    :Returns:

            The parsed default value.

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

    >>> f = {+package}.{+class}()
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
            return self._default(
                default, "{!r} has no {!r} component".format(
                    self.__class__.__name__, component)
            )

    @property
    def _custom(self):
        '''Customisable storage for additional attributes.

    .. versionadded:: 1.7.4

    **Examples:**

    >>> f = {+package}.{+class}()
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

    >>> f = {+package}.{+class}()
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

    >>> f = {+package}.{+class}()
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

    >>> f = {+package}.{+class}()
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

        `{+class}`        
            The deep copy.

    **Examples:**

    >>> g = f.copy()

        '''
        return type(self)(source=self, copy=True)

# --- End: class
