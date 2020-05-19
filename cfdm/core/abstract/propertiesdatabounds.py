from builtins import super
from future.utils import with_metaclass

import abc

from . import PropertiesData


class PropertiesDataBounds(with_metaclass(abc.ABCMeta, PropertiesData)):
    '''Abstract base class for a data array with bounds and descriptive
    properties.

    .. versionadded:: 1.7.0

    '''
    def __init__(self, properties=None, data=None, bounds=None,
                 geometry=None, interior_ring=None, source=None,
                 copy=True, _use_data=True):
        '''**Initialization**

    :Parameters:

        properties: `dict`, optional
            Set descriptive properties. The dictionary keys are
            property names, with corresponding values. Ignored if the
            *source* parameter is set.

            Properties may also be set after initialisation with the
            `set_properties` and `set_property` methods.

            *Parameter example:*
               ``properties={'standard_name': 'longitude'}``

        data: `Data`, optional
            Set the data array. Ignored if the *source* parameter is
            set.

            The data array may also be set after initialisation with
            the `set_data` method.

        bounds: `Bounds`, optional
            Set the bounds array. Ignored if the *source* parameter is
            set.

            The bounds array may also be set after initialisation with
            the `set_bounds` method.

        geometry: `str`, optional
            Set the geometry type. Ignored if the *source* parameter
            is set.

            The geometry type may also be set after initialisation
            with the `set_geometry` method.

            *Parameter example:*
               ``geometry='polygon'``

        interior_ring: `InteriorRing`, optional
            Set the interior ring variable. Ignored if the *source*
            parameter is set.

            The interior ring variable may also be set after
            initialisation with the `set_interior_ring` method.

        source: optional
            Initialize the properties, geometry type, data, bounds and
            interior ring from those of *source*.

        copy: `bool`, optional
            If False then do not deep copy input parameters prior to
            initialization. By default arguments are deep copied.

        '''
        # Initialise properties and data
        super().__init__(properties=properties, data=data,
                         source=source, copy=copy,
                         _use_data=_use_data)

        # Get bounds, geometry type and interior ring from source
        if source is not None:
            try:
                bounds = source.get_bounds(None)
            except AttributeError:
                bounds = None

            try:
                geometry = source.get_geometry(None)
            except AttributeError:
                geometry = None

            try:
                interior_ring = source.get_interior_ring(None)
            except AttributeError:
                interior_ring = None
        # --- End: if

        # Initialise bounds
        if bounds is not None:
            if copy or not _use_data:
                bounds = bounds.copy(data=_use_data)

            self.set_bounds(bounds, copy=False)

        # Initialise the geometry type
        if geometry is not None:
            self.set_geometry(geometry)

        # Initialise interior ring
        if interior_ring is not None:
            if copy or not _use_data:
                interior_ring = interior_ring.copy(data=_use_data)

            self.set_interior_ring(interior_ring, copy=False)

    # ----------------------------------------------------------------
    # Attributes
    # ----------------------------------------------------------------
    @property
    def bounds(self):
        '''Return the bounds.

    ``f.bounds`` is equivalent to ``f.get_bounds()``

    .. versionadded:: 1.7.0

    .. seealso:: `data`, `del_bounds`, `get_bounds`, `has_bounds`,
                 `set_bounds`

    :Returns:

        `Bounds`
            The bounds.

    **Examples:**

    >>> import numpy
    >>> b = cfdm.Bounds(data=cfdm.Data(numpy.arange(10).reshape(5, 2)))
    >>> c.set_bounds(b)
    >>> c.has_bounds()
    True
    >>> b = c.bounds
    >>> b
    <Bounds: (5, 2) >
    >>> b.data
    <Data(5, 2): [[0, ..., 9]]>
    >>> b.data.shape
    (5, 2)

        '''
        return self.get_bounds()

    @property
    def interior_ring(self):
        '''Return the interior ring variable for polygon geometries.

    ``f.interior_ring`` is equivalent to ``f.get_interior_ring()``

    .. versionadded:: 1.8.0

    .. seealso:: `data`, `del_interior_ring`, `get_interior_ring`,
                 `has_interior_ring`, `set_interior_ring`

    :Returns:

        `InteriorRing`
            The interior ring variable.

    **Examples:**

    >>> import numpy
    >>> i = cfdm.InteriorRing(data=cfdm.Data(numpy.arange(10).reshape(5, 2)))
    >>> c.set_interior_ring(i)
    >>> c.has_interior_ring()
    True
    >>> i = c.interior_ring
    >>> i
    <InteriorRing: (5, 2) >
    >>> i.data
    <Data(5, 2): [[0, ..., 9]]>
    >>> i.data.shape
    (5, 2)

        '''
        return self.get_interior_ring()

    # ----------------------------------------------------------------
    # Methods
    # ----------------------------------------------------------------
    def del_bounds(self, default=ValueError()):
        '''Remove the bounds.

    .. versionadded:: 1.7.0

    .. seealso:: `del_data`, `get_bounds`, `has_bounds`, `set_bounds`

    :Parameters:

        default: optional
            Return the value of the *default* parameter if bounds have
            not been set. If set to an `Exception` instance then it
            will be raised instead.

    :Returns:

            The removed bounds.

    **Examples:**

    >>> import numpy
    >>> b = cfdm.Bounds(data=cfdm.Data(numpy.arange(10).reshape(5, 2)))
    >>> c.set_bounds(b)
    >>> c.has_bounds()
    True
    >>> c.get_bounds()
    <Bounds: (5, 2) >
    >>> b = c.del_bounds()
    >>> b
    <Bounds: (5, 2) >
    >>> c.has_bounds()
    False
    >>> print(c.get_bounds(None))
    None
    >>> print(c.del_bounds(None))
    None

        '''
        try:
            return self._del_component('bounds')
        except ValueError:
            return self._default(default,
                           "{!r} has no bounds".format(self.__class__.__name__))

    def del_geometry(self, default=ValueError()):
        '''TODO

    .. versionadded:: 1.8.0

    .. seealso:: `get_geometry`, `has_geometry`, `set_geometry`

    :Parameters:

        default: optional
            Return the value of the *default* parameter if the
            geometry type has not been set. If set to an `Exception`
            instance then it will be raised instead.

    :Returns:

            The removed geometry type.

    **Examples:**

    TODO

        '''
        try:
            return self._del_component('geometry')
        except ValueError:
            return self._default(default,
                           "{!r} has no geometry type".format(self.__class__.__name__))

    def get_bounds(self, default=ValueError()):
        '''Return the bounds.

    .. versionadded:: 1.7.0

    .. seealso:: `bounds`, `get_data`, `del_bounds`, `has_bounds`,
                 `set_bounds`

    :Parameters:

        default: optional
            Return the value of the *default* parameter if bounds have
            not been set. If set to an `Exception` instance then it
            will be raised instead.

    :Returns:

            The bounds.

    **Examples:**

    >>> import numpy
    >>> b = cfdm.Bounds(data=cfdm.Data(numpy.arange(10).reshape(5, 2)))
    >>> c.set_bounds(b)
    >>> c.has_bounds()
    True
    >>> c.get_bounds()
    <Bounds: (5, 2) >
    >>> b = c.del_bounds()
    >>> b
    <Bounds: (5, 2) >
    >>> c.has_bounds()
    False
    >>> print(c.get_bounds(None))
    None
    >>> print(c.del_bounds(None))
    None

        '''
        try:
            return self._get_component('bounds')
        except ValueError:
            return self._default(default,
                           "{!r} has no bounds".format(self.__class__.__name__))

    def get_geometry(self, default=ValueError()):
        '''Return the geometry type.

    .. versionadded:: 1.8.0

    .. seealso:: `get_data`, `has_bounds`, `set_bounds`

    :Parameters:

        default: optional
            Return the value of the *default* parameter if the
            geometry type has not been set. If set to an `Exception`
            instance then it will be raised instead.

    :Returns:

            TODO

    **Examples:**

    TODO

        '''
        try:
            return self._get_component('geometry')
        except ValueError:
            return self._default(default,
                    "{!r} has no geometry type".format(self.__class__.__name__))

    def get_interior_ring(self, default=ValueError()):
        '''Return the interior ring variable for polygon geometries.

    ``f.get_interior_ring()`` is equivalent to ``f.interior_ring``

    .. versionadded:: 1.8.0

    .. seealso:: `data`, `del_interior_ring`, `has_interior_ring`,
                 `interior_ring`, `set_interior_ring`

    :Parameters:

        default: optional
            Return the value of the *default* parameter if interior
            ring data have not been set. If set to an `Exception`
            instance then it will be raised instead.

    :Returns:

            The interior ring variable.

    **Examples:**

    >>> import numpy
    >>> i = cfdm.InteriorRing(data=cfdm.Data(numpy.arange(10).reshape(5, 2)))
    >>> c.set_interior_ring(i)
    >>> c.has_interior_ring()
    True
    >>> i = c.get_interior_ring()
    >>> i
    <InteriorRing: (5, 2) >
    >>> i.data
    <Data(5, 2): [[0, ..., 9]]>
    >>> i.data.shape
    (5, 2)

        '''
        try:
            return self._get_component('interior_ring')
        except ValueError:
            return self._default(default,
                    "{!r} has no interior ring variable".format(self.__class__.__name__))

    def has_bounds(self):
        '''Whether or not there are bounds.

    .. versionadded:: 1.7.0

    .. seealso:: `del_bounds`, `get_bounds`, `has_data`, `set_bounds`

    :Returns:

        `bool`
            True if there are bounds, otherwise False.

    **Examples:**

    >>> import numpy
    >>> b = cfdm.Bounds(data=cfdm.Data(numpy.arange(10).reshape(5, 2)))
    >>> c.set_bounds(b)
    >>> c.has_bounds()
    True
    >>> c.get_bounds()
    <Bounds: (5, 2) >
    >>> b = c.del_bounds()
    >>> b
    <Bounds: (5, 2) >
    >>> c.has_bounds()
    False
    >>> print(c.get_bounds(None))
    None
    >>> print(c.del_bounds(None))
    None

        '''
        return self._has_component('bounds')

    def has_geometry(self):
        '''True if there is a goemetry type. TODO

    .. versionadded:: 1.8.0

    .. seealso:: TODO

    :Returns:

        `bool`

    **Examples:**

    >>> x = c.has_geometry()

            '''
        return self._has_component('geometry')

    def has_interior_ring(self):
        '''Whether or not there is an interior ring variable.

    .. versionadded:: 1.8.0

    .. seealso:: `del_interior_ring`, `get_interior_ring`,
                 `interior_ring`, `set_interior_ring`

    :Returns:

        `bool`
            True if there is an interior ring variable, otherwise
            False.

    **Examples:**

    >>> if c.has_interior_ring():
    ...     print 'Has interior ring'

        '''
        return self._has_component('interior_ring')

    def set_bounds(self, bounds, copy=True):
        '''Set the bounds.

    .. versionadded:: 1.7.0

    .. seealso:: `del_bounds`, `get_bounds`, `has_bounds`, `set_data`

    :Parameters:

        data: `Bounds`
            The bounds to be inserted.

        copy: `bool`, optional
            If False then do not copy the bounds prior to
            insertion. By default the bounds are copied.

    :Returns:

        `None`

    **Examples:**

    >>> import numpy
    >>> b = cfdm.Bounds(data=cfdm.Data(numpy.arange(10).reshape(5, 2)))
    >>> c.set_bounds(b)
    >>> c.has_bounds()
    True
    >>> c.get_bounds()
    <Bounds: (5, 2) >
    >>> b = c.del_bounds()
    >>> b
    <Bounds: (5, 2) >
    >>> c.has_bounds()
    False
    >>> print(c.get_bounds(None))
    None
    >>> print(c.del_bounds(None))
    None

        '''
        if copy:
            bounds = bounds.copy()

        self._set_component('bounds', bounds, copy=False)

    def set_geometry(self, value, copy=True):
        '''Set the geometry type.

    .. versionadded:: 1.8.0

    .. seealso:: TODO

    :Parameters:

        value: `str`
            TODO

    :Returns:

        `None`

    **Examples:**

    TODO
        '''
        self._set_component('geometry', value, copy=copy)

    def set_interior_ring(self, interior_ring, copy=True):
        '''Set the interior_ring.

    .. versionadded:: 1.8.0

    .. seealso:: `del_interior_ring`, `get_interior_ring`,
                 `interior_ring`, `has_interior_ring`

    :Parameters:

        interior_ring: `InteriorRing`
            The interior_ring to be inserted.

        copy: `bool`, optional
            If False then do not copy the interior_ring prior to
            insertion. By default the interior_ring are copied.

    :Returns:

        `None`

    **Examples:**

    >>> c.set_interior_ring(i)

        '''
        if copy:
            interior_ring = interior_ring.copy()

        self._set_component('interior_ring', interior_ring, copy=False)

# --- End: class
