from builtins import super
from past.builtins import basestring

from . import abstract

from . import CoordinateConversion
from . import Datum


class CoordinateReference(abstract.Container):
    '''A coordinate reference construct of the CF data model.

    A coordinate reference construct relates the coordinate values of
    the coordinate system to locations in a planetary reference frame.

    The domain of a field construct may contain various coordinate
    systems, each of which is constructed from a subset of the
    dimension and auxiliary coordinate constructs. For example, the
    domain of a four-dimensional field construct may contain
    horizontal (y-x), vertical (z), and temporal (t) coordinate
    systems. There may be more than one of each of these, if there is
    more than one coordinate construct applying to a particular
    spatiotemporal dimension (for example, there could be both
    latitude-longitude and y-x projection coordinate systems). In
    general, a coordinate system may be constructed implicitly from
    any subset of the coordinate constructs, yet a coordinate
    construct does not need to be explicitly or exclusively associated
    with any coordinate system.

    A coordinate system of the field construct can be explicitly
    defined by a coordinate reference construct which relates the
    coordinate values of the coordinate system to locations in a
    planetary reference frame and consists of the following:

    * References to the dimension coordinate and auxiliary coordinate
      constructs that define the coordinate system to which the
      coordinate reference construct applies. Note that the coordinate
      values are not relevant to the coordinate reference construct,
      only their properties.

    ..

    * A definition of a datum specifying the zeroes of the dimension
      and auxiliary coordinate constructs which define the coordinate
      system. The datum may be implied by the metadata of the
      referenced dimension and auxiliary coordinate constructs, or
      explicitly provided.

    ..

    * A coordinate conversion, which defines a formula for converting
      coordinate values taken from the dimension or auxiliary
      coordinate constructs to a different coordinate system. A
      coordinate reference construct relates the coordinate values of
      the field to locations in a planetary reference frame.

    .. versionadded:: 1.7.0

    '''
    def __new__(cls, *args, **kwargs):
        '''This must be overridden in subclasses.

        '''
        instance = super().__new__(cls)
        instance._CoordinateConversion = CoordinateConversion
        instance._Datum                = Datum
        return instance

    def __init__(self, coordinates=None, datum=None,
                 coordinate_conversion=None, source=None, copy=True):
        '''**Initialization**

    :Parameters:

        coordinates: sequence of `str`, optional
            Identify the related dimension and auxiliary coordinate
            constructs by their construct identifiers. Ignored if the
            *source* parameter is set.

            The coordinates may also be set after initialisation with
            the `set_coordinates` and `set_coordinate` methods.

            *Parameter example:*
              ``coordinates=['dimensioncoordinate2']``

            *Parameter example:*
              ``coordinates=('dimensioncoordinate0', 'dimensioncoordinate1')``

        datum: `Datum`, optional
            Set the datum component of the coordinate reference
            construct. Ignored if the *source* parameter is set.

            The datum may also be set after initialisation with the
            `set_datum` method.

        coordinate_conversion: `CoordinateConversion`, optional
            Set the coordinate conversion component of the coordinate
            reference construct. Ignored if the *source* parameter is
            set.

            The coordinate conversion may also be set after
            initialisation with the `set_coordinate_conversion`
            method.

        source: optional
            Initialize the coordinates, datum and coordinate
            conversion from those of *source*.

        copy: `bool`, optional
            If False then do not deep copy arguments prior to
            initialization. By default arguments are deep copied.

        '''
        super().__init__(source=source, copy=copy)

        self._set_component('coordinates', set(), copy=False)

        if source:
            try:
                coordinates = source.coordinates()
            except AttributeError:
                coordinates = None

            try:
                coordinate_conversion = source.get_coordinate_conversion()
            except AttributeError:
                coordinate_conversion = None

            try:
                datum = source.get_datum()
            except AttributeError:
                datum = None
        # --- End: if

        if coordinates is not None:
            self.set_coordinates(coordinates)

        if coordinate_conversion is not None:
            self.set_coordinate_conversion(coordinate_conversion, copy=copy)

        if datum is not None:
            self.set_datum(datum, copy=copy)

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
    'coordinate_reference'

        '''
        return 'coordinate_reference'

    @property
    def coordinate_conversion(self):
        '''Return the coordinate conversion component.

    .. versionadded:: 1.7.0

    .. seealso:: `datum`, `get_coordinate_conversion`

    :Returns:

        `CoordinateConversion`
            The coordinate conversion.

    **Examples:**

    >>> c.coordinate_conversion
    <CoordinateConversion: Parameters: standard_name; Ancillaries: a, b, orog>

        '''
        return self.get_coordinate_conversion()

    @property
    def datum(self):
        '''Return the datum component.

    .. versionadded:: 1.7.0

    .. seealso:: `coordinate_conversion`, `get_datum`

    :Returns:

       `Datum`
            The datum.

    **Examples:**

    >>> c.datum
    <Datum: Parameters: earth_radius>

        '''
        return self.get_datum()

    # ----------------------------------------------------------------
    # Methods
    # ----------------------------------------------------------------
    def clear_coordinates(self):
        '''Remove all references to coordinate constructs.

    .. versionadded:: 1.7.0

    .. seealso:: `del_coordinate`, `coordinates`, `set_coordinates`

    :Returns:

        `set`
            The removed coordinate construct keys.

    **Examples:**

    >>> old = c.clear_coordinates()
    {'dimensioncoordinate0', 'dimensioncoordinate1'}
    >>> c.coordinates()
    set()
    >>> c.set_coordinates(old)
    >>> c.coordinates()
    {'dimensioncoordinate0', 'dimensioncoordinate1'}

        '''
        out = self._get_component('coordinates')
        self._set_component('coordinates', set())
        return out.copy()

    def coordinates(self):
        '''Return all references to coordinate constructs.

    .. versionadded:: 1.7.0

    .. seealso:: `clear_coordinates`, `set_coordinates`

    :Returns:

        `set`
            The coordinate construct keys.

    **Examples:**

    >>> old = c.clear_coordinates()
    {'dimensioncoordinate0', 'dimensioncoordinate1'}
    >>> c.coordinates()
    set()
    >>> c.set_coordinates(old)
    >>> c.coordinates()
    {'dimensioncoordinate0', 'dimensioncoordinate1'}

        '''
        return self._get_component('coordinates').copy()

    def copy(self):
        '''Return a deep copy.

    ``f.copy()`` is equivalent to ``copy.deepcopy(f)``.

    .. versionadded:: 1.7.0

    :Returns:

            The deep copy.

    **Examples:**

    >>> d = c.copy()

        '''
        return type(self)(source=self, copy=True)

    def del_coordinate(self, key, default=ValueError()):
        '''Remove a reference to a coordinate construct.

    .. versionadded:: 1.7.0

    .. seealso:: `coordinates`, `has_coordinate`, `set_coordinate`

    :Parameters:

        key: `str`
            The construct key of the coordinate construct.

              *Parameter example:*
                 ``key='dimensioncoordinate1'``

              *Parameter example:*
                 ``key='auxiliarycoordinate0'``

        default: optional
            Return the value of the *default* parameter if the
            coordinate construct has not been set. If set to an
            `Exception` instance then it will be raised instead.

    :Returns:

          The removed coordinate construct key.

    **Examples:**

    >>> c.coordinates()
    {'dimensioncoordinate0',
     'dimensioncoordinate1'}
    >>> c.del_coordinate('dimensioncoordinate0')
    'dimensioncoordinate0'
    >>> c.coordinates()
    {'dimensioncoordinate1'}
    >>> c.del_coordinate('dimensioncoordinate0', 'not set')
    'not set'

        '''
        coordinates = self._get_component('coordinates')
        if key in coordinates:
            coordinates.remove(key)
            return key

        return self._default(default,
              "{!r} has no {!r} coordinate".format(
                  self.__class__.__name__, key))

    def del_coordinate_conversion(self):
        '''Remove the coordinate conversion component.

    .. versionadded:: 1.7.0

    .. seealso:: `coordinate_conversion`, `get_coordinate_conversion`,
                 `set_coordinate_conversion`

    :Returns:

        `CoordinateConversion`
            The removed coordinate conversion component.

    **Examples:**

    >>> c.del_coordinate_conversion()
    <CoordinateConversion: Parameters(grid_mapping_name, grid_north_pole_latitude, grid_north_pole_longitude)>
    >>> c.get_coordinate_conversion()
    <CF CoordinateConversion: Parameters: ; Ancillaries: >

        '''
        new = self._CoordinateConversion()
        out = self._del_component('coordinate_conversion', new)
        self.set_coordinate_conversion(new)
        return out

    def del_datum(self):
        '''Remove the datum component.

    .. versionadded:: 1.7.0

    .. seealso:: `datum`, `get_datum`, `set_datum`

    :Returns:

        `Datum`
            The removed datum component.

    **Examples:**

    >>> c.del_datum()
    <Datum: Parameters: earth_radius>
    >>> c.get_datum()
    <Datum: Parameters: >

        '''
        new = self._Datum()
        out = self._del_component('datum', new)
        self.set_datum(new)
        return out

    def get_coordinate_conversion(self):
        '''Get the coordinate conversion component.

    .. versionadded:: 1.7.0

    .. seealso:: `coordinate_conversion`, `del_coordinate_conversion`,
                 `set_coordinate_conversion`

    :Returns:

        `CoordinateConversion`
            The coordinate conversion component.

    **Examples:**

    >>> c.get_coordinate_conversion()
    <CF CoordinateConversion: Parameters: standard_name; Ancillaries: a, b, orog>

        '''
        out = self._get_component('coordinate_conversion', None)
        if out is None:
            out = self._CoordinateConversion()
            self.set_coordinate_conversion(out, copy=False)

        return out

    def get_datum(self):
        '''Return the datum component.

    .. versionadded:: 1.7.0

    .. seealso:: `datum`, `get_coordinate_conversion`

    :Returns:

       `Datum`
            The datum component.

    **Examples:**

    >>> c.get_datum()
    <Datum: Parameters: earth_radius>

        '''
        out = self._get_component('datum', None)
        if out is None:
            out = self._Datum()
            self.set_datum(out, copy=False)

        return out

    def has_coordinate(self, key):
        '''Whether a reference to a coordinate construct has been set.

    .. versionadded:: 1.7.0

    .. seealso:: `coordinates`, `del_coordinate`, `set_coordinate`

    :Parameters:

        key: `str`
            The construct key of the coordinate construct.

              *Parameter example:*
                 ``key='dimensioncoordinate1'``

              *Parameter example:*
                 ``key='auxiliarycoordinate0'``

    :Returns:

          `bool`
              `True` if the coordinate construct key has been set,
              otherwise `False`.

    **Examples:**

    >>> c.coordinates()
    {'dimensioncoordinate0',
     'dimensioncoordinate1'}
    >>> c.has_coordinate('dimensioncoordinate0')
    True
    >>> c.has_coordinate('auxiliarycoordinate1')
    False

        '''
        return key in self._get_component('coordinates')

    def set_coordinate(self, key):
        '''Set a reference to a coordinate construct.

    .. versionadded:: 1.7.0

    .. seealso:: `coordinates`, `del_coordinate`, `has_coordinate`

    :Parameters:

        key: `str`
            The construct key of the coordinate construct.

              *Parameter example:*
                 ``key='dimensioncoordinate1'``

              *Parameter example:*
                 ``key='auxiliarycoordinate0'``

    :Returns:

        `None`

    **Examples:**

    >>> c.coordinates()
    {'dimensioncoordinate0',
     'dimensioncoordinate1'}
    >>> c.set_coordinate('auxiliarycoordinate0')
    >>> c.coordinates()
    {'dimensioncoordinate0',
     'dimensioncoordinate1',
     'auxiliarycoordinate0'}

        '''
        c = self._get_component('coordinates')
        c.add(key)

    def set_coordinates(self, coordinates):
        '''Set references to coordinate constructs.

    .. versionadded:: 1.7.0

    .. seealso:: `coordinates`, `clear_coordinates`, `set_coordinate`

    :Parameters:

        coordinates: (sequence of) `str`
            The coordinate construct keys to be set.

            *Parameter example:*
              ``coordinates=['dimensioncoordinate0']``

            *Parameter example:*
              ``coordinates='dimensioncoordinate0'``

            *Parameter example:*
              ``coordinates=set(['dimensioncoordinate0', 'auxiliarycoordinate1'])``

            *Parameter example:*
              ``coordinates=[]``

    :Returns:

        `None`

    **Examples:**

    >>> old = c.clear_coordinates()
    {'dimensioncoordinate0', 'dimensioncoordinate1'}
    >>> c.coordinates()
    set()
    >>> c.set_coordinates(old)
    >>> c.coordinates()
    {'dimensioncoordinate0', 'dimensioncoordinate1'}


        '''
        if isinstance(coordinates, basestring):
            coordinates = (coordinates,)

        self._get_component('coordinates').update(coordinates)

    def set_coordinate_conversion(self, coordinate_conversion, copy=True):
        '''Set the coordinate conversion component.

    .. versionadded:: 1.7.0

    .. seealso:: `coordinate_conversion`, `del_coordinate_conversion`,
                 `get_coordinate_conversion`

    :Parameters:

        coordinate_conversion: `CoordinateConversion`
            The coordinate conversion component to be inserted.

        copy: `bool`, optional
            If False then do not copy the coordinate conversion prior
            to insertion. By default the coordinate conversion is
            copied.

    :Returns:

        `None`

    **Examples:**

    >>> c.set_coordinate_conversion(cc)

    >>> c.set_coordinate_conversion(cc, copy=False)

        '''
        if copy:
            coordinate_conversion = coordinate_conversion.copy()

        self._set_component('coordinate_conversion',
                            coordinate_conversion, copy=False)

    def set_datum(self, datum, copy=True):
        '''Set the datum component.

    .. versionadded:: 1.7.0

    .. seealso:: `datum`, `del_datum`, `get_datum`

    :Parameters:

        datum: `Datum`
            The datum component to be inserted.

        copy: `bool`, optional
            If False then do not copy the datum prior to insertion. By
            default the datum is copied.

    :Returns:

        `None`

    **Examples:**

    >>> c.set_datum(d)

    >>> c.set_datum(d, copy=False)

        '''
        if copy:
            datum = datum.copy()

        self._set_component('datum', datum, copy=False)

# --- End: class
