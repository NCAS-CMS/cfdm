from builtins import (str, super)
from past.builtins import basestring

from copy import deepcopy

from . import abstract


class CellMethod(abstract.Container):
    '''A cell method construct of the CF data model.

    One or more cell method constructs describe how the cell values of
    the field construct represent the variation of the physical
    quantity within its cells, i.e. the structure of the data at a
    higher resolution.

    A single cell method construct consists of a set of axes, a
    "method" property which describes how a value of the field
    construct's data array describes the variation of the quantity
    within a cell over those axes (e.g. a value might represent the
    cell area average), and descriptive qualifiers serving to indicate
    more precisely how the method was applied (e.g. recording the
    spacing of the original data, or the fact that the method was
    applied only over El Nino years).

    .. versionadded:: 1.7.0

    '''
    def __init__(self, axes=None, method=None, qualifiers=None,
                 source=None, copy=True):
        '''**Initialisation**

    :Parameters:

        axes: (sequence of) `str`, optional
            Set the axes of the cell method construct, specified
            either by the construct identifiers of domain axis
            constructs, standard names, or the special string
            ``'area'``.

            The axes may also be set after initialisation with the
            `set_axes` method.

            *Parameter example:*
              ``axes='domainaxis0'``

            *Parameter example:*
              ``axes=['domainaxis0']``

            *Parameter example:*
              ``axes=('domainaxis0', 'domainaxis1')``

            *Parameter example:*
              ``axes='area'``

            *Parameter example:*
              ``axes=['domainaxis2', 'time']``

        method: `str`, optional
            Set the axes of the cell method construct. Either one or
            more domain axis construct identifiers or standard
            names. Ignored if the *source* parameter is set.

            The method may also be set after initialisation with the
            `set_method` method.

            *Parameter example:*
              ``method='mean'``

        qualifiers: `dict`, optional
            Set descriptive qualifiers. The dictionary keys are
            qualifer names, with corresponding values. Ignored if the
            *source* parameter is set.

            Qualifiers may also be set after initialisation with the
            `qualifiers` and `set_qualifier` methods.

            *Parameter example:*
              ``qualifiers={'comment': 'sampled instantaneously'}``

            *Parameter example:*
              ``qualifiers={'where': 'sea', ''over': 'ice'}``

        source: optional
            Initialize the axes, method and qualifiers from those of
            *source*.

        copy: `bool`, optional
            If False then do not deep copy input parameters prior to
            initialization By default parameters are deep copied.

        '''
        super().__init__()

        if source:
            try:
                axes = source.get_axes(None)
            except AttributeErrror:
                axes = None

            try:
                method = source.get_method(None)
            except AttributeErrror:
                method = None

            try:
                qualifiers = source.qualifiers()
            except AttributeError:
                qualifiers = None
        # --- End: if

        if axes is not None:
            axes = self.set_axes(axes)

        if method is not None:
            method = self.set_method(method)

        if qualifiers is None:
            qualifiers = {}

        self._set_component('qualifiers', qualifiers, copy=copy)

    # ----------------------------------------------------------------
    # Attributes
    # ----------------------------------------------------------------
    @property
    def construct_type(self):
        '''Return a description of the construct type.

    .. versionadded:: 1.7.0

    :Returns:

        `str`
            The construct type.

    **Examples:**

    >>> f.construct_type
    'cell_method'

        '''
        return 'cell_method'

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

    def del_axes(self, default=ValueError()):
        '''Remove the axes of the cell method.

    .. versionadded:: 1.7.0

    .. seealso:: `get_axes`, `has_axes`, `set_axes`

    :Parameters:

        default: optional
            Return the value of the *default* parameter if axes have
            not been set. If set to an `Exception` instance then it
            will be raised instead.

    :Returns:

        `tuple`
            The removed axes, identified by domain axis construct key
            or standard name.

    **Examples:**

    >>> c.set_axes('domainaxis1')
    >>> c.has_axes()
    True
    >>> c.get_axes()
    ('domainaxis1',)
    >>> c.del_axes()
    >>> c.has_axes()
    False
    >>> c.get_axes('NO AXES')
    'NO AXES'
    >>> c.del_axes('NO AXES')
    'NO AXES'

        '''
        try:
            return self._del_component('axes')
        except ValueError:
            return self._default(default,
                                 "{!r} has no axes".format(
                                     self.__class__.__name__))

    def del_method(self, default=ValueError()):
        '''Remove the method of the cell method.

    .. versionadded:: 1.7.0

    .. seealso:: `get_method`, `has_method`, `set_method`

    :Parameters:

        default: optional
            Return the value of the *default* parameter if the method
            has not been set. If set to an `Exception` instance then
            it will be raised instead.

    :Returns:

        `str`
            The removed method.

    **Examples:**

    >>> c.set_method('minimum')
    >>> c.has_method()
    True
    >>> c.get_method()
    ('time',)
    >>> c.del_method()
    >>> c.has_method()
    False
    >>> c.get_method('NO METHOD')
    'NO METHOD'
    >>> c.del_method('NO METHOD')
    'NO METHOD'

        '''
        try:
            return self._del_component('method')
        except ValueError:
            return self._default(default,
                                 "{!r} has no method".format(
                                     self.__class__.__name__))

    def del_qualifier(self, qualifier, default=ValueError()):
        '''Remove a qualifier of the cell method.

    .. versionadded:: 1.7.0

    .. seealso:: `get_qualifier`, `has_qualifier`, `qualifiers`,
                 `set_qualifier`

    :Parameters:

        qualifier:
            The name of the qualifier to be removed.

            *Parameter example:*
              ``qualifier='where'``

        default: optional
            Return the value of the *default* parameter if the
            qualifier has not been set. If set to an `Exception`
            instance then it will be raised instead.

    :Returns:

            The removed qualifier.

    **Examples:**

    >>> c.set_qualifier('where', 'land')
    >>> c.get_qualifier('where', 'no qualifier')
    'land'
    >>> c.del_qualifier('where')
    'land'
    >>> c.get_qualifier('where')
    ValueError: 'CellMethod' has no 'where' qualifier
    >>> c.del_qualifier('where', 'no qualifier')
    'no qualifier'

        '''
        try:
            return self._get_component('qualifiers').pop(qualifier)
        except KeyError:
            return self._default(default, "{!r} has no {!r} qualifier".format(
                self.__class__.__name__, qualifier))

    def get_axes(self, default=ValueError()):
        '''Return the axes of the cell method.

    .. versionadded:: 1.7.0

    .. seealso:: `del_axes`, `has_axes`, `set_axes`

    :Parameters:

        default: optional
            Return the value of the *default* parameter if axes have
            not been set. If set to an `Exception` instance then it
            will be raised instead.

    :Returns:

        `tuple`
            The axes.

    **Examples:**

    >>> c.set_axes('domainaxis1')
    >>> c.has_axes()
    True
    >>> c.get_axes()
    ('domainaxis1',)
    >>> c.del_axes()
    >>> c.has_axes()
    False
    >>> c.get_axes('NO AXES')
    'NO AXES'
    >>> c.del_axes('NO AXES')
    'NO AXES'

        '''
        try:
            return self._get_component('axes')
        except ValueError:
            return self._default(default,
                                 "{!r} has no axes".format(
                                     self.__class__.__name__))

    def get_method(self, default=ValueError()):
        '''Return the method of the cell method.

    .. versionadded:: 1.7.0

    .. seealso:: `del_method`, `has_method`, `set_method`

    :Parameters:

        default: optional
            Return the value of the *default* parameter if the method
            has not been set. If set to an `Exception` instance then
            it will be raised instead.

    :Returns:

        `str`
            The method.

    **Examples:**

    >>> c.set_method('minimum')
    >>> c.has_method()
    True
    >>> c.get_method()
    'minimum'
    >>> c.del_method()
    >>> c.has_method()
    False
    >>> c.get_method('NO METHOD')
    'NO METHOD'
    >>> c.del_method('NO METHOD')
    'NO METHOD'

        '''
        try:
            return self._get_component('method')
        except ValueError:
            return self._default(default,
                                 "{!r} has no method".format(
                                     self.__class__.__name__))

    def get_qualifier(self, qualifier, default=ValueError()):
        '''Return a qualifier of the cell method.

    .. versionadded:: 1.7.0

    .. seealso:: `del_qualifier`, `has_qualifier`, `qualifiers`,
                 `set_qualifier`

    :Parameters:

        qualifier:
            The name of the qualifier to be returned.

            *Parameter example:*
              ``qualifier='where'``

        default: optional
            Return the value of the *default* parameter if the
            qualifier has not been set. If set to an `Exception`
            instance then it will be raised instead.

    :Returns:

            The value of the qualifier.

    **Examples:**

    >>> c.set_qualifier('where', 'land')
    >>> c.get_qualifier('where', 'no qualifier')
    'land'
    >>> c.del_qualifier('where')
    'land'
    >>> c.get_qualifier('where')
    ValueError: 'CellMethod' has no 'where' qualifier
    >>> c.get_qualifier('where', 'no qualifier')
    'no qualifier'

        '''
        try:
            return self._get_component('qualifiers')[qualifier]
        except KeyError:
            return self._default(default, "{!r} has no {!r} qualifier".format(
                self.__class__.__name__, qualifier))

    def has_axes(self):
        '''Whether the axes of the cell method have been set.

    .. versionadded:: 1.7.0

    .. seealso:: `del_axes`, `get_axes`, `set_axes`

    :Returns:

        `bool`
            `True` if the axes have been set, otherwise `False`.

    **Examples:**

    >>> c.set_axes('domainaxis1')
    >>> c.has_axes()
    True
    >>> c.get_axes()
    ('domainaxis1',)
    >>> c.del_axes()
    >>> c.has_axes()
    False
    >>> c.get_axes('NO AXES')
    'NO AXES'
    >>> c.del_axes('NO AXES')
    'NO AXES'

        '''
        return self._has_component('axes')

    def has_method(self):
        '''Whether the method of the cell method has been set.

    .. versionadded:: 1.7.0

    .. seealso:: `del_axes`, `get_method`, `set_method`

    :Returns:

        `bool`
            `True` if the method has been set, otherwise `False`.

    **Examples:**

    >>> c.set_method('minimum')
    >>> c.has_method()
    True
    >>> c.get_method()
    'minimum'
    >>> c.del_method()
    >>> c.has_method()
    False
    >>> c.get_method('NO METHOD')
    'NO METHOD'
    >>> c.del_method('NO METHOD')
    'NO METHOD'

        '''
        return self._has_component('method')

    def has_qualifier(self, qualifier):
        '''Whether a qualifier of the cell method has been set.

    .. versionadded:: 1.7.0

    .. seealso:: `del_qualifier`, `get_qualifier`, `qualifiers`,
                 `set_qualifier`

    :Parameters:

        qualifier: `str`
            The name of the qualifier.

    :Returns:

        `bool`
            `True` if the qualifier has been set, otherwise `False`.

    **Examples:**

    >>> c.set_qualifier('where', 'land')
    >>> c.has_qualifier('where')
    True
    >>> c.del_qualifier('where')
    'land'
    >>> c.has_qualifier('where')
    False

        '''
        return qualifier in self._get_component('qualifiers')

    def qualifiers(self):
        '''Return all qualifiers of the cell method.

    .. versionadded:: 1.7.0

    .. seealso:: `del_qualifier`, `get_qualifier`, `has_qualifier`,
                 `set_qualifier`

    :Returns:

        `dict`
            The qualifiers.

    **Examples:**

    >>> c.qualifiers()
    {'interval': [<Data(): 0.1 degrees>],
     'where': 'land'}

    >>> f.qualifiers()
    {}

        '''
        return self._get_component('qualifiers').copy()

    def set_axes(self, value, copy=True):
        '''Set the axes of the cell method.

    .. versionadded:: 1.7.0

    .. seealso:: `del_axes`, `get_axes`, `has_axes`

    :Parameters:

        value: (sequence of) `str`
            The axes, specified either by the construct identifiers of
            domain axis constructs, standard names, or the special
            string ``'area'``.

            *Parameter example:*
              ``axes='domainaxis0'``

            *Parameter example:*
              ``axes='time'``

            *Parameter example:*
              ``axes='area'``

            *Parameter example:*
              ``axes=['domainaxis0', 'domainaxis2']``

            *Parameter example:*
              ``axes=['time', 'area']``

            *Parameter example:*
              ``axes=['domainaxis0', 'time']``

    :Returns:

        `None`

    **Examples:**

    >>> c.set_axes('domainaxis1')
    >>> c.has_axes()
    True
    >>> c.get_axes()
    ('domainaxis1',)
    >>> c.del_axes()
    >>> c.has_axes()
    False
    >>> c.get_axes('NO AXES')
    'NO AXES'
    >>> c.del_axes('NO AXES')
    'NO AXES'

    >>> c.set_axes(['domainaxis1', 'domainaxis0'])

    >>> c.set_axes(['time', 'domainaxis0'])

    >>> c.set_axes('time')

        '''
        if copy:
            value = deepcopy(value)

        if isinstance(value, basestring):
            value = (value,)
        else:
            value = tuple(value)

        return self._set_component('axes', value, copy=False)

    def set_method(self, value, copy=True):
        '''Set the method of the cell method.

    .. versionadded:: 1.7.0

    .. seealso:: `del_method`, `get_method`, `has_method`

    :Parameters:

        value: `str`
            The value for the method.

        copy: `bool`, optional
            If True then set a deep copy of *value*.

    :Returns:

        `None`

    **Examples:**

    >>> c.set_method('minimum')
    >>> c.has_method()
    True
    >>> c.get_method()
    'minimum'
    >>> c.del_method()
    >>> c.has_method()
    False
    >>> c.get_method('NO METHOD')
    'NO METHOD'
    >>> c.del_method('NO METHOD')
    'NO METHOD'

        '''
        return self._set_component('method', value, copy=copy)

    def set_qualifier(self, qualifier, value, copy=True):
        '''Set a qualifier of the cell method.

    .. versionadded:: 1.7.0

    .. seealso:: `del_qualifier`, `get_qualifier`, `has_qualifier`,
                 `qualifiers`

    :Parameters:

        qualifier: `str`
            The name of the qualifier to be set.

        value:
            The value for the qualifier.

        copy: `bool`, optional
            If True then set a deep copy of *value*.

    :Returns:

        `None`

    **Examples:**

    >>> c.set_qualifier('where', 'land')
    >>> c.get_qualifier('where')
    'land'

        '''
        if copy:
            value = deepcopy(value)

        self._get_component('qualifiers')[qualifier] = value

# --- End: class
