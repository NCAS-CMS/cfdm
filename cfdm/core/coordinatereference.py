from . import CoordinateConversion, Datum, abstract


class CoordinateReference(abstract.Container):
    """A coordinate reference construct of the CF data model.

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

    .. versionadded:: (cfdm) 1.7.0

    """

    def __new__(cls, *args, **kwargs):
        """This must be overridden in subclasses."""
        instance = super().__new__(cls)
        instance._CoordinateConversion = CoordinateConversion
        instance._Datum = Datum
        return instance

    def __init__(
        self,
        coordinates=None,
        datum=None,
        coordinate_conversion=None,
        source=None,
        copy=True,
    ):
        """**Initialisation**

        :Parameters:

            coordinates: sequence of `str`, optional
                Identify the related dimension and auxiliary
                coordinate constructs by their construct
                identifiers. Ignored if the *source* parameter is set.

                The coordinates may also be set after initialisation
                with the `set_coordinates` and `set_coordinate`
                methods.

                *Parameter example:*
                  ``coordinates=['dimensioncoordinate2']``

                *Parameter example:*
                  ``coordinates=('dimensioncoordinate0', 'dimensioncoordinate1')``

            datum: `Datum`, optional
                Set the datum component of the coordinate reference
                construct. Ignored if the *source* parameter is set.

                The datum may also be set after initialisation with
                the `set_datum` method.

            coordinate_conversion: `CoordinateConversion`, optional
                Set the coordinate conversion component of the
                coordinate reference construct. Ignored if the
                *source* parameter is set.

                The coordinate conversion may also be set after
                initialisation with the `set_coordinate_conversion`
                method.

            source: optional
                Initialise the coordinates, datum and coordinate
                conversion from those of *source*.

                {{init source}}

            {{init copy: `bool`, optional}}

        """
        super().__init__(source=source, copy=copy)

        self._set_component("coordinates", set(), copy=False)

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
        """Return a description of the construct type.

        .. versionadded:: (cfdm) 1.7.0

        :Returns:

            `str`
                The construct type.

        **Examples:**

        >>> c = {{package}}.{{class}}()
        >>> c.construct_type
        'coordinate_reference'

        """
        return "coordinate_reference"

    @property
    def coordinate_conversion(self):
        """Return the coordinate conversion component.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `datum`, `get_coordinate_conversion`

        :Returns:

            `CoordinateConversion`
                The coordinate conversion.

        **Examples:**

        >>> orog = {{package}}.DomainAncillary()
        >>> c = {{package}}.CoordinateConversion(
        ...     parameters={
        ...         'standard_name': 'atmosphere_hybrid_height_coordinate',
        ...     },
        ...     domain_ancillaries={'orog': orog}
        ... )
        >>> r = {{package}}.{{class}}(coordinate_conversion=c)
        >>> r.coordinate_conversion
        <{{repr}}CoordinateConversion: Parameters: standard_name; Ancillaries: orog>

        """
        return self.get_coordinate_conversion()

    @property
    def datum(self):
        """Return the datum component.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `coordinate_conversion`, `get_datum`

        :Returns:

           `Datum`
                The datum.

        **Examples:**

        >>> d = {{package}}.Datum(parameters={'earth_radius': 7000000})
        >>> r = {{package}}.{{class}}(datum=d)
        >>> r
        <{{repr}}CoordinateReference: >
        >>> r.datum
        <{{repr}}Datum: Parameters: earth_radius>

        """
        return self.get_datum()

    # ----------------------------------------------------------------
    # Methods
    # ----------------------------------------------------------------
    def clear_coordinates(self):
        """Remove all references to coordinate constructs.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `del_coordinate`, `coordinates`, `set_coordinates`

        :Returns:

            `set`
                The removed coordinate construct keys.

        **Examples:**

        >>> r = {{package}}.{{class}}()
        >>> r.set_coordinates(['dimensioncoordinate0', 'auxiliarycoordinate1'])
        >>> sorted(r.coordinates())
        ['auxiliarycoordinate1', 'dimensioncoordinate0']
        >>> sorted(r.clear_coordinates())
        ['auxiliarycoordinate1', 'dimensioncoordinate0']
        >>> r.coordinates()
        set()

        """
        out = self._get_component("coordinates")
        self._set_component("coordinates", set(), copy=False)
        return out.copy()

    def coordinates(self):
        """Return all references to coordinate constructs.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `clear_coordinates`, `set_coordinates`

        :Returns:

            `set`
                The coordinate construct keys.

        **Examples:**

        >>> r = {{package}}.{{class}}()
        >>> r.set_coordinates(['dimensioncoordinate0', 'auxiliarycoordinate1'])
        >>> sorted(r.coordinates())
        ['auxiliarycoordinate1', 'dimensioncoordinate0']
        >>> sorted(r.clear_coordinates())
        ['auxiliarycoordinate1', 'dimensioncoordinate0']
        >>> r.coordinates()
        set()

        """
        return self._get_component("coordinates").copy()

    def copy(self):
        """Return a deep copy.

        ``f.copy()`` is equivalent to ``copy.deepcopy(f)``.

        .. versionadded:: (cfdm) 1.7.0

        :Returns:

            `{{class}}`
                The deep copy.

        **Examples:**

        >>> r = {{package}}.{{class}}()
        >>> s = r.copy()

        """
        return type(self)(source=self, copy=True)

    def del_coordinate(self, key, default=ValueError()):
        """Remove a reference to a coordinate construct.

        .. versionadded:: (cfdm) 1.7.0

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

        >>> r = {{package}}.{{class}}()
        >>> r.set_coordinates(['dimensioncoordinate0', 'auxiliarycoordinate1'])
        >>> r.coordinates()
        {'auxiliarycoordinate1', 'dimensioncoordinate0'}
        >>> r.del_coordinate('dimensioncoordinate0')
        'dimensioncoordinate0'
        >>> r.coordinates()
        {'auxiliarycoordinate1'}
        >>> r.del_coordinate('dimensioncoordinate0', 'not set')
        'not set'

        """
        coordinates = self._get_component("coordinates")
        if key in coordinates:
            coordinates.remove(key)
            return key

        if default is None:
            return

        return self._default(
            default, f"{self.__class__.__name__!r} has no {key!r} coordinate"
        )

    def del_coordinate_conversion(self):
        """Remove the coordinate conversion component.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `coordinate_conversion`, `get_coordinate_conversion`,
                     `set_coordinate_conversion`

        :Returns:

            `CoordinateConversion`
                The removed coordinate conversion component.

        **Examples:**

        >>> r = {{package}}.{{class}}()
        >>> orog = {{package}}.DomainAncillary()
        >>> c = {{package}}.CoordinateConversion(
        ...     parameters={
        ...         'standard_name': 'atmosphere_hybrid_height_coordinate',
        ...     },
        ...     domain_ancillaries={'orog': orog}
        ... )
        >>> r.set_coordinate_conversion(c)
        >>> r.get_coordinate_conversion()
        <{{repr}}CoordinateConversion: Parameters: standard_name; Ancillaries: orog>
        >>> r.del_coordinate_conversion()
        <{{repr}}CoordinateConversion: Parameters: standard_name; Ancillaries: orog>
        >>> r.get_coordinate_conversion()
        <{{repr}}CoordinateConversion: Parameters: ; Ancillaries: >

        """
        new = self._CoordinateConversion()
        out = self._del_component("coordinate_conversion", new)
        self.set_coordinate_conversion(new, copy=False)
        return out

    def del_datum(self):
        """Remove the datum component.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `datum`, `get_datum`, `set_datum`

        :Returns:

            `Datum`
                The removed datum component.

        **Examples:**

        >>> r = {{package}}.{{class}}()
        >>> d = {{package}}.Datum(parameters={'earth_radius': 7000000})
        >>> r.set_datum(d)
        >>> r.get_datum()
        <{{repr}}Datum: Parameters: earth_radius>
        >>> r.del_datum()
        <{{repr}}Datum: Parameters: earth_radius>
        >>> r.get_datum()
        <{{repr}}Datum: Parameters: >

        """
        new = self._Datum()
        out = self._del_component("datum", new)
        self.set_datum(new, copy=False)
        return out

    def get_coordinate_conversion(self):
        """Get the coordinate conversion component.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `coordinate_conversion`, `del_coordinate_conversion`,
                     `set_coordinate_conversion`

        :Returns:

            `CoordinateConversion`
                The coordinate conversion component.

        **Examples:**

        >>> r = {{package}}.{{class}}()
        >>> orog = {{package}}.DomainAncillary()
        >>> c = {{package}}.CoordinateConversion(
        ...     parameters={
        ...         'standard_name': 'atmosphere_hybrid_height_coordinate',
        ...     },
        ...     domain_ancillaries={'orog': orog}
        ... )
        >>> r.set_coordinate_conversion(c)
        >>> r.get_coordinate_conversion()
        <{{repr}}CoordinateConversion: Parameters: standard_name; Ancillaries: orog>
        >>> r.del_coordinate_conversion()
        <{{repr}}CoordinateConversion: Parameters: standard_name; Ancillaries: orog>
        >>> r.get_coordinate_conversion()
        <{{repr}}CoordinateConversion: Parameters: ; Ancillaries: >

        """
        out = self._get_component("coordinate_conversion", None)
        if out is None:
            out = self._CoordinateConversion()
            self.set_coordinate_conversion(out, copy=False)

        return out

    def get_datum(self):
        """Return the datum component.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `datum`, `get_coordinate_conversion`

        :Returns:

           `Datum`
                The datum component.

        **Examples:**

        >>> r = {{package}}.{{class}}()
        >>> d = {{package}}.Datum(parameters={'earth_radius': 7000000})
        >>> r.set_datum(d)
        >>> r.get_datum()
        <{{repr}}Datum: Parameters: earth_radius>
        >>> r.del_datum()
        <{{repr}}Datum: Parameters: earth_radius>
        >>> r.get_datum()
        <{{repr}}Datum: Parameters: >

        """
        out = self._get_component("datum", None)
        if out is None:
            out = self._Datum()
            self.set_datum(out, copy=False)

        return out

    def has_coordinate(self, key):
        """Whether a reference to a coordinate construct has been set.

        .. versionadded:: (cfdm) 1.7.0

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

        >>> r = {{package}}.{{class}}()
        >>> r.set_coordinates(['dimensioncoordinate0', 'auxiliarycoordinate1'])
        >>> r.coordinates()
        {'auxiliarycoordinate1', 'dimensioncoordinate0'}
        >>> r.has_coordinate('dimensioncoordinate0')
        True
        >>> r.has_coordinate('dimensioncoordinate1')
        False

        """
        return key in self._get_component("coordinates")

    def set_coordinate(self, key):
        """Set a reference to a coordinate construct.

        .. versionadded:: (cfdm) 1.7.0

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

        >>> r = {{package}}.{{class}}()
        >>> r.set_coordinate('dimensioncoordinate0')
        >>> r.coordinates()
        {'dimensioncoordinate0'}
        >>> r.has_coordinate('dimensioncoordinate0')
        True
        >>> r.has_coordinate('auxiliarycoordinate0')
        False

        """
        c = self._get_component("coordinates")
        c.add(key)

    def set_coordinates(self, coordinates):  # SB NOTE: flaky doctest set order
        """Set references to coordinate constructs.

        .. versionadded:: (cfdm) 1.7.0

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

        >>> r = {{package}}.{{class}}()
        >>> r.set_coordinates(['dimensioncoordinate0', 'auxiliarycoordinate1'])
        >>> r.coordinates()
        {'auxiliarycoordinate1', 'dimensioncoordinate0'}
        >>> r.clear_coordinates()
        {'auxiliarycoordinate1', 'dimensioncoordinate0'}
        >>> r.coordinates()
        set()

        """
        if isinstance(coordinates, str):
            coordinates = (coordinates,)

        self._get_component("coordinates").update(coordinates)

    def set_coordinate_conversion(self, coordinate_conversion, copy=True):
        """Set the coordinate conversion component.

        .. versionadded:: (cfdm) 1.7.0

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

        >>> r = {{package}}.{{class}}()
        >>> orog = {{package}}.DomainAncillary()
        >>> c = {{package}}.CoordinateConversion(
        ...     parameters={
        ...         'standard_name': 'atmosphere_hybrid_height_coordinate',
        ...     },
        ...     domain_ancillaries={'orog': orog}
        ... )
        >>> r.set_coordinate_conversion(c)
        >>> r.get_coordinate_conversion()
        <{{repr}}CoordinateConversion: Parameters: standard_name; Ancillaries: orog>
        >>> r.del_coordinate_conversion()
        <{{repr}}CoordinateConversion: Parameters: standard_name; Ancillaries: orog>
        >>> r.get_coordinate_conversion()
        <{{repr}}CoordinateConversion: Parameters: ; Ancillaries: >

        """
        if copy:
            coordinate_conversion = coordinate_conversion.copy()

        self._set_component(
            "coordinate_conversion", coordinate_conversion, copy=False
        )

    def set_datum(self, datum, copy=True):
        """Set the datum component.

        .. versionadded:: (cfdm) 1.7.0

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

        >>> r = {{package}}.{{class}}()
        >>> d = {{package}}.Datum(parameters={'earth_radius': 7000000})
        >>> r.set_datum(d)
        >>> r.get_datum()
        <{{repr}}Datum: Parameters: earth_radius>
        >>> r.del_datum()
        <{{repr}}Datum: Parameters: earth_radius>
        >>> r.get_datum()
        <{{repr}}Datum: Parameters: >

        """
        if copy:
            datum = datum.copy()

        self._set_component("datum", datum, copy=False)
