from ..docstring import _docstring_substitution_definitions
from ..functions import deepcopy
from ..meta import DocstringRewriteMeta


class Container(metaclass=DocstringRewriteMeta):
    """Abstract base class for storing components.

    .. warning:: The ``custom`` component dictionary is only shallow
                 copied when initialised from the *source* parameter,
                 regardless of the value of the *copy* parameter. This
                 is to avoid potentially expensive deep copies of the
                 dictionary values.

                 A subclass of `Container` that requires custom
                 dictionary values to be deep copied should ensure
                 that this occurs its `__init__` method.

    .. versionadded:: (cfdm) 1.7.0

    """

    def __init__(self, source=None, copy=True):
        """**Initialiation**

        :Parameters:

            source: optional
                Initialise the components from those of *source*.

                {{init source}}

            {{init copy: `bool`, optional}}

        """
        self._components = {}

        if source is not None:
            # WARNING: The 'custom' dictionary is only shallow copied
            #          from source
            try:
                custom = source._get_component("custom", {})
            except AttributeError:
                custom = {}
            else:
                custom = custom.copy()
        else:
            custom = {}

        self._set_component("custom", custom, copy=False)

    def __deepcopy__(self, memo):
        """Called by the `copy.deepcopy` function.

        x.__deepcopy__() <==> copy.deepcopy(x)

        .. versionadded:: (cfdm) 1.7.0

        **Examples:**

        >>> import copy
        >>> f = {{package}}.{{class}}()
        >>> g = copy.deepcopy(f)

        """
        return self.copy()

    def __docstring_substitutions__(self):
        """Defines docstring substitutions for a class and subclasses.

        That is, defines docstring substitutions that apply to this
        class and all of its subclasses.

        These are in addtion to, and take precendence over, docstring
        substitutions defined by the base classes of this class.

        See `_docstring_substitutions` for details.

        .. versionaddedd:: (cfdm) 1.8.7.0

        :Returns:

            `dict`
                The docstring substitutions that have been applied.

        """
        return _docstring_substitution_definitions

    def __docstring_package_depth__(self):
        """Returns the package depth for {{package}} substitutions.

        See `_docstring_package_depth` for details.

        """
        return 1

    # ----------------------------------------------------------------
    # Private methods
    # ----------------------------------------------------------------
    def _default(self, default, message=None):
        """Return a value or raise an Exception for a default case.

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

        >>> f = {{package}}.{{class}}()
        >>> f._default(AttributeError())  # Raises Exception
        Traceback (most recent call last):
            ...
        AttributeError
        >>> f._default(ValueError("Missing item"))  # Raises Exception
        Traceback (most recent call last):
            ...
        ValueError: Missing item
        >>> f._default(ValueError(), message="No component")  # Raises Exception
        Traceback (most recent call last):
            ...
        ValueError: No component
        >>> f._default(False)
        False
        >>> f._default('Not set')
        'Not set'
        >>> f._default(1)
        1

        """
        if isinstance(default, Exception):
            if message is not None and not default.args:
                default = type(default)(message)

            raise default

        return default

    def _del_component(self, component, default=ValueError()):
        """Remove a component.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `_get_component`, `_has_component`, `_set_component`

        :Parameters:

            component:
                The name of the component to be removed.

            default: optional
                Return *default* if the component has not been set.

                {{default Exception}}

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

        """
        try:
            return self._components.pop(component)
        except KeyError:
            if default is None:
                return

            return self._default(
                default,
                f"{self.__class__.__name__} has no {component!r} component",
            )

    @property
    def _custom(self):
        """Customisable storage for additional attributes.

        See https://ncas-cms.github.io/cfdm/extensions.html for more
        information.

        .. versionadded:: (cfdm) 1.7.4

        **Examples:**

        >>> f = {{package}}.{{class}}()
        >>> f._custom
        {}
        >>> f._custom['feature_1'] = 1
        >>> g = f.copy()
        >>> g._custom['feature_2'] = 2
        >>> f._custom
        {'feature_1': 1}
        >>> g._custom
        {'feature_1': 1, 'feature_2': 2}
        >>> del g._custom['feature_1']
        >>> g._custom
        {'feature_2': 2}
        >>> f._custom
        {'feature_1': 1}

        """
        return self._get_component("custom")

    def _get_component(self, component, default=ValueError()):
        """Return a component.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `_del_component`, `_has_component`, `_set_component`

        :Parameters:

            component:
                The name of the component to be returned.

            default: optional
                Return *default* if the component has not been set.

                {{default Exception}}

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

        """
        try:
            return self._components[component]
        except KeyError:
            if default is None:
                return

            return self._default(
                default,
                f"{self.__class__.__name__} has no {component!r} component",
            )

    def _has_component(self, component):
        """Whether a component has been set.

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

        """
        return component in self._components

    def _set_component(self, component, value, copy=True):
        """Set a component.

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

        """
        if copy:
            value = deepcopy(value)

        self._components[component] = value

    # ----------------------------------------------------------------
    # Methods
    # ----------------------------------------------------------------
    def copy(self):
        """Return a deep copy.

        ``f.copy()`` is equivalent to ``copy.deepcopy(f)``.

        .. versionadded:: (cfdm) 1.7.0

        :Returns:

            `{{class}}`
                The deep copy.

        **Examples:**

        >>> f = {{package}}.{{class}}()
        >>> g = f.copy()

        """
        return type(self)(source=self, copy=True)
