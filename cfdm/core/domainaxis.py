from builtins import (str, super)

from . import abstract


class DomainAxis(abstract.Container):
    '''A domain axis construct of the CF data model.

    A domain axis construct specifies the number of points along an
    independent axis of the domain. It comprises a positive integer
    representing the size of the axis. In CF-netCDF it is usually
    defined either by a netCDF dimension or by a scalar coordinate
    variable, which implies a domain axis of size one. The field
    construct's data array spans the domain axis constructs of the
    domain, with the optional exception of size one axes, because
    their presence makes no difference to the order of the elements.

    .. versionadded:: 1.7.0

    '''
    def __init__(self, size=None, source=None, copy=True):
        '''**Initialization**

    :Parameters:

        size: `int`, optional
            The size of the domain axis.

            *Parameter example:*
              ``size=192``

            The size may also be set after initialisation with the
            `set_size` method.

        source:
            Initialize the size from that of source.

        copy: `bool`, optional
            If False then do not deep copy input parameters prior to
            initialization. By default arguments are deep copied.

        '''
        super().__init__(source=source, copy=copy)

        if source is not None:
            try:
                size = source.get_size(None)
            except AttributeError:
                size = None
        # --- End: if

        if size is not None:
            self.set_size(size)

    @property
    def construct_type(self):
        '''Return a description of the construct type.

    .. versionadded:: 1.7.0

    :Returns:

        `str`
            The construct type.

    **Examples:**

    >>> f.construct_type
    'domain_axis'

        '''
        return 'domain_axis'

# This is inherited
#    def copy(self):
#        '''Return a deep copy.
#
#    ``d.copy()`` is equivalent to ``copy.deepcopy(d)``.
#
#    .. versionadded:: 1.7.0
#
#    :Returns:
#
#            The deep copy.
#
#    **Examples:**
#
#    >>> e = d.copy()
#
#        '''
#        return type(self)(source=self, copy=True)

    def del_size(self, default=ValueError()):
        '''Remove the size.

    .. versionadded:: 1.7.0

    .. seealso:: `get_size`, `has_size`, `set_size`

    :Parameters:

        default: optional
            Return the value of the *default* parameter if the size
            has not been set. If set to an `Exception` instance then
            it will be raised instead.

    :Returns:

            The removed size.

    **Examples:**

    >>> d.set_size(96)
    >>> d.has_size()
    True
    >>> d.get_size()
    96
    >>> d.del_size()
    96
    >>> d.has_size()
    False
    >>> print(d.del_size(None))
    None
    >>> print(d.get_size(None))
    None

        '''
        try:
            return self._del_component('size')
        except ValueError:
            return self._default(default,
              "{!r} has no size".format(self.__class__.__name__))

    def has_size(self):
        '''Whether the size has been set.

    .. versionadded:: 1.7.0

    .. seealso:: `del_size`, `get_size`, `set_size`

    :Returns:

         `bool`
            True if the size has been set, otherwise False.

    **Examples:**

    >>> d.set_size(96)
    >>> d.has_size()
    True
    >>> d.get_size()
    96
    >>> d.del_size()
    96
    >>> d.has_size()
    False
    >>> print(d.del_size(None))
    None
    >>> print(d.get_size(None))
    None

        '''
        return self._has_component('size')

    def get_size(self, default=ValueError()):
        '''Return the size.

    .. versionadded:: 1.7.0

    .. seealso:: `del_size`, `has_size`, `set_size`

    :Parameters:

        default: optional
            Return the value of the *default* parameter if the size
            has not been set. If set to an `Exception` instance then
            it will be raised instead.

    :Returns:

            The size.

    **Examples:**

    >>> d.set_size(96)
    >>> d.has_size()
    True
    >>> d.get_size()
    96
    >>> d.del_size()
    96
    >>> d.has_size()
    False
    >>> print(d.del_size(None))
    None
    >>> print(d.get_size(None))
    None

        '''
        try:
            return self._get_component('size')
        except ValueError:
            return self._default(default,
              "{!r} has no size".format(self.__class__.__name__))

    def set_size(self, size, copy=True):
        '''Set the size.

    .. versionadded:: 1.7.0

    .. seealso:: `del_size`, `get_size`, `has_size`

    :Parameters:

        value: `int`
            The size.

        copy: `bool`, optional
            If True then set a deep copy of *size*.

    :Returns:

         `None`

    **Examples:**

    >>> d.set_size(96)
    >>> d.has_size()
    True
    >>> d.get_size()
    96
    >>> d.del_size()
    96
    >>> d.has_size()
    False
    >>> print(d.del_size(None))
    None
    >>> print(d.get_size(None))

        '''
        self._set_component('size', size, copy=copy)

# --- End: class
