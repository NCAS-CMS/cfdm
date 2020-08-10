import inspect
import re

from copy import copy, deepcopy

from ..meta import RewriteDocstringMeta


class Container(metaclass=RewriteDocstringMeta):
    '''Mixin class for storing components.

    .. versionadded:: (cfdm) 1.7.0

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

    .. versionadded:: (cfdm) 1.7.0

    **Examples:**

    >>> import copy
    >>> y = copy.deepcopy(x)

        '''
        return self.copy()

    def __docstring_substitution__(self):
        '''TODO

    Substitutions may be easily modified by overriding the
    __docstring_substitution__ method.

    Modifications can be applied to any class, and will only apply to
    that class and all of its subclases.

    If the key is a string then the special subtitutions will be
    applied to the dictionary values *after* its replacement in the
    docstring.

    If the key is a compiled regular expession then the special
    subtitutions will be applied to the match of the regular
    expression *after* its replacement in the docstring.

    For example:

       def __docstring_substitution__(self):
           def _upper(match):
               return match.group(1).upper()

           out = super().__docstring_substitution__()

           # Simple substitutions
           out['{{repr}}'] = 'CF: '
           out['{{foo}}'] = 'bar'

           out['{{parameter: `int`}}'] = """parameter: `int`
               This parameter does something to `{{class}}`
               instances. It has no default value.""",

           # Regular expression subsititions
           #
           # Convert text to upper case
           out[re.compile('{{<upper (.*?)>}}')] = _upper

           return out

        '''
        return {
            # --------------------------------------------------------
            # Simple substitutions.
            #
            # All occurences of the key are replaced with the value.
            #
            # Note that special subtitutions will be applied to the
            # value *after* its replacement in the docstring.
            # --------------------------------------------------------
            '{{repr}}': '',

            '{{default: optional}}': '''default: optional
            Return the value of the *default* parameter if data have
            not been set. If set to an `Exception` instance then it
            will be raised instead.''',

            '{{inplace: `bool`, optional}}': '''inplace: `bool`, optional
            If True then do the operation in-place and return `None`.'''

            # --------------------------------------------------------
            # Regular expression substitutions.
            #
            # The key must be an `re.Pattern` object, i.e. a compiled
            # regular expression, e.g as created by `re.compile`.
            #
            # The value must be a callable that, when passed the Match
            # object created by evaulating the regular expression
            # against the docstring, must return the replacement
            # string to be used.
            #
            # Note that special subtitutions will be applied to the
            # match of the regular expression *after* its replacement
            # in the docstring.
            # --------------------------------------------------------
        }

    # ----------------------------------------------------------------
    # Private methods
    # ----------------------------------------------------------------
    def _default(self, default, message=None):
        '''Return a value or raise an Exception for a default case.

    .. versionadded:: (cfdm) 1.7.0

    :Parameters:

        default:
            The value to return, or to raise if set to an `Exception`
            instance.

        message: `str`, optional
            The error message to raise with *default* if it is an
            `Exception` instance.

    :Returns:

            The value of *default* if it is not an `Exception`
            instance.

    **Examples:**

    >>> f = cfdm.example_field(0)
    >>> f._default(AttributeError())  # Raises Exception
    AttributeError
    >>> f._default(ValueError(), message="No component")  # Raises Exception
    ValueError: No component
    >>> f._default(False)
    False
    >>> f._default('Not set')
    'Not set'
    >>> f._default(1)
    1

        '''
        if isinstance(default, Exception):
            if message is not None and not default.args:
                default = copy(default)
                default.args = (message,)

            raise default

        return default

    def _del_component(self, component, default=ValueError()):
        '''Remove a component.

    .. versionadded:: (cfdm) 1.7.0

    .. seealso:: `_get_component`, `_has_component`, `_set_component`

    :Parameters:

        component:
            The name of the component to be removed.

        {{default: optional}}

    :Returns:

            The removed component. If unset then *default* is
            returned, if provided.

    **Examples:**

    >>> f = {{package}}.{{class}}()
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

    .. versionadded:: (cfdm) 1.7.4

    **Examples:**

    >>> f = {{package}}.{{class}}()
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

    .. versionadded:: (cfdm) 1.7.0

    .. seealso:: `_del_component`, `_has_component`, `_set_component`

    :Parameters:

        component:
            The name of the component to be returned.

        {{default: optional}}

    :Returns:

            The component. If unset then *default* is returned, if
            provided.

    **Examples:**

    >>> f = {{package}}.{{class}}()
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

    .. versionadded:: (cfdm) 1.7.0

    .. seealso:: `_del_component`, `_get_component`, `_set_component`

    :Parameters:

        component:
            The name of the component.

    :Returns:

        `bool`
            True if the component has been set, otherwise False.

    **Examples:**

    >>> f = {{package}}.{{class}}()
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

    .. versionadded:: (cfdm) 1.7.0

    .. seealso:: `_del_component`, `_get_component`, `_has_component`

    :Parameters:

        component: `str`
            The name of the component.

        value:
            The value for the component.

    :Returns:

        `None`

    **Examples:**

    >>> f = {{package}}.{{class}}()
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

    @classmethod
    def _docstring_substitutions(cls):
        '''Return the docstring substitutions that apply to methods of this
    class.

    :Returns:

        `dict`
            The docstring substitutions. A dictionary key matches text
            in the docstrings, with a corresponding value its
            replacement.

        '''
        d = {}
        for klass in cls.__bases__[::-1] + (cls,):
            d_s = getattr(klass, '__docstring_substitution__', None)
            if d_s is None:
                continue

            d.update(d_s(None))

        return d

    # ----------------------------------------------------------------
    # Methods
    # ----------------------------------------------------------------
    def copy(self):
        '''Return a deep copy.

    ``f.copy()`` is equivalent to ``copy.deepcopy(f)``.

    .. versionadded:: (cfdm) 1.7.0

    :Returns:

        `{{class}}`
            The deep copy.

    **Examples:**

    >>> g = f.copy()

        '''
        return type(self)(source=self, copy=True)

# --- End: class
