import numpy

from . import Constructs, Domain, abstract, mixin


class Field(mixin.FieldDomain, abstract.PropertiesData):
    """A field construct of the CF data model.

    The field construct is central to the CF data model, and includes
    all the other constructs. A field corresponds to a CF-netCDF data
    variable with all of its metadata. All CF-netCDF elements are
    mapped to a field construct or some element of the CF field
    construct. The field construct contains all the data and metadata
    which can be extracted from the file using the CF conventions.

    The field construct consists of a data array and the definition of
    its domain (that describes the locations of each cell of the data
    array), field ancillary constructs containing metadata defined
    over the same domain, and cell method constructs to describe how
    the cell values represent the variation of the physical quantity
    within the cells of the domain. The domain is defined collectively
    by the following constructs of the CF data model: domain axis,
    dimension coordinate, auxiliary coordinate, cell measure,
    coordinate reference and domain ancillary constructs. All of the
    constructs contained by the field construct are optional.

    The field construct also has optional properties to describe
    aspects of the data that are independent of the domain. These
    correspond to some netCDF attributes of variables (e.g. units,
    long_name and standard_name), and some netCDF global file
    attributes (e.g. history and institution).

    .. versionadded:: (cfdm) 1.7.0

    """

    # ----------------------------------------------------------------
    # Define the base of the identity keys for each construct type
    # ----------------------------------------------------------------
    _construct_key_base = {
        "auxiliary_coordinate": "auxiliarycoordinate",
        "cell_measure": "cellmeasure",
        "cell_method": "cellmethod",
        "coordinate_reference": "coordinatereference",
        "dimension_coordinate": "dimensioncoordinate",
        "domain_ancillary": "domainancillary",
        "domain_axis": "domainaxis",
        "field_ancillary": "fieldancillary",
    }

    def __new__(cls, *args, **kwargs):
        """This must be overridden in subclasses.

        .. versionadded:: (cfdm) 1.7.0

        """
        instance = super().__new__(cls)
        instance._Constructs = Constructs
        instance._Domain = Domain
        return instance

    def __init__(
        self, properties=None, source=None, copy=True, _use_data=True
    ):
        """**Initialisation**

        :Parameters:

            {{init properties: `dict`, optional}}

                *Parameter example:*
                   ``properties={'standard_name': 'air_temperature'}``

            source: optional
                Initialise the properties, data and metadata
                constructs from those of *source*.

                {{init source}}

            {{init copy: `bool`, optional}}

        """
        # To avoid mutable default argument (an anti-pattern) of properties={}
        if properties is None:
            properties = {}

        super().__init__(
            properties=properties, source=source, copy=copy, _use_data=False
        )

        if source is not None:
            # Initialise constructs and the data from the source
            # parameter
            try:
                constructs = source.constructs
            except AttributeError:
                constructs = None

            try:
                data = source.get_data(default=None)
            except AttributeError:
                data = None

            try:
                data_axes = source.get_data_axes(default=None)
            except AttributeError:
                data_axes = None

            if constructs is not None and (copy or not _use_data):
                constructs = constructs.copy(data=_use_data)
        else:
            constructs = None
            data = None
            data_axes = None

        if constructs is None:
            constructs = self._Constructs(**self._construct_key_base)

        self._set_component("constructs", constructs, copy=False)

        if data is not None and _use_data:
            self.set_data(data, data_axes, copy=copy)
        elif data_axes is not None:
            self.set_data_axes(data_axes)

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

        >>> f = {{package}}.{{class}}()
        >>> f.construct_type
        'field'

        """
        return "field"

    @property
    def constructs(self):
        """Return the metadata constructs.

        .. versionadded:: (cfdm) 1.7.0

        :Returns:

            `Constructs`
                The constructs.

        **Examples:**

        >>> f = {{package}}.example_field(0)
        >>> print(f.constructs)
        Constructs:
        {'cellmethod0': <{{repr}}CellMethod: area: mean>,
         'dimensioncoordinate0': <{{repr}}DimensionCoordinate: latitude(5) degrees_north>,
         'dimensioncoordinate1': <{{repr}}DimensionCoordinate: longitude(8) degrees_east>,
         'dimensioncoordinate2': <{{repr}}DimensionCoordinate: time(1) days since 2018-12-01 >,
         'domainaxis0': <{{repr}}DomainAxis: size(5)>,
         'domainaxis1': <{{repr}}DomainAxis: size(8)>,
         'domainaxis2': <{{repr}}DomainAxis: size(1)>}

        """
        return self._get_component("constructs")

    @property
    def domain(self):
        """Return the domain.

        ``f.domain`` is equivalent to ``f.get_domain()``

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `get_domain`

        :Returns:

            `Domain`
                The domain.

        **Examples:**

        >>> f = {{package}}.example_field(2)
        >>> f.domain
        <Domain: {1, 5, 8, 36}>

        >>> d0 = f.domain
        >>> d1 = f.get_domain()
        >>> d0.equals(d1)
        True

        """
        return self.get_domain()

    # ----------------------------------------------------------------
    # Methods
    # ----------------------------------------------------------------
    def del_data_axes(self, key=None, default=ValueError()):
        """Removes the keys of the axes spanned by the construct data.

        Specifically, removes the keys of the domain axis constructs
        spanned by the data of the field or of a metadata construct.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `get_data_axes`, `has_data_axes`, `set_data_axes`

        :Parameters:

            key: `str`, optional
                Specify a metadata construct, instead of the field
                construct.

                *Parameter example:*
                  ``key='auxiliarycoordinate0'``

            default: optional
                Return the value of the *default* parameter if the data
                axes have not been set.

                {{default Exception}}

        :Returns:

            `tuple`
                The removed keys of the domain axis constructs spanned by
                the data.

        **Examples:**

        >>> f = {{package}}.example_field(0)
        >>> f.get_data_axes()
        ('domainaxis0', 'domainaxis1')
        >>> f.get_data_axes(key='dimensioncoordinate2')
        ('domainaxis2',)
        >>> f.has_data_axes()
        True

        >>> f.del_data_axes()
        ('domainaxis0', 'domainaxis1')
        >>> f.has_data_axes()
        False
        >>> f.get_data_axes(default='no axes')
        'no axes'

        """
        if key is not None:
            return super().del_data_axes(key, default=default)

        return self._del_component("data_axes", default=default)

    def get_domain(self):
        """Return the domain.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `domain`

        :Returns:

            `Domain`
                 The domain.

        **Examples:**

        >>> f = {{package}}.example_field(2)
        >>> f.get_domain()
        <Domain: {1, 5, 8, 36}>

        >>> d0 = f.domain
        >>> d1 = f.get_domain()
        >>> d0.equals(d1)
        True

        """
        return self._Domain.fromconstructs(self.constructs, copy=False)

    def get_data_axes(self, key=None, default=ValueError()):
        """Gets the keys of the axes spanned by the construct data.

        Specifically, returns the keys of the domain axis constructs
        spanned by the data of the field or of a metadata construct.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `del_data_axes`, `get_data`, `set_data_axes`

        :Parameters:

            key: `str`, optional
                Specify a metadata construct, instead of the field
                construct.

                *Parameter example:*
                  ``key='auxiliarycoordinate0'``

            default: optional
                Return the value of the *default* parameter if the data
                axes have not been set.

                {{default Exception}}

        :Returns:

            `tuple`
                The keys of the domain axis constructs spanned by the
                data.

        **Examples:**

        >>> f = {{package}}.example_field(0)
        >>> f.get_data_axes()
        ('domainaxis0', 'domainaxis1')
        >>> f.get_data_axes(key='dimensioncoordinate2')
        ('domainaxis2',)
        >>> f.has_data_axes()
        True

        >>> f.del_data_axes()
        ('domainaxis0', 'domainaxis1')
        >>> f.has_data_axes()
        False
        >>> f.get_data_axes(default='no axes')
        'no axes'

        """
        if key is not None:
            return super().get_data_axes(key, default=default)

        return self._get_component("data_axes", default=default)

    def has_data_axes(self, key=None):
        """Whether the axes spanned by the construct data have been set.

        Specifically, whether the domain axis constructs spanned by the
        data of the field or of a metadata construct have been set.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `del_data_axes`, `get_data_axes`, `set_data_axes`

        :Parameters:

            key: `str`, optional
                Specify a metadata construct, instead of the field
                construct.

                *Parameter example:*
                  ``key='domainancillary1'``

        :Returns:

            `bool`
                True if domain axis constructs that span the data been
                set, otherwise False.

        **Examples:**

        >>> f = {{package}}.example_field(0)
        >>> f.get_data_axes()
        ('domainaxis0', 'domainaxis1')
        >>> f.get_data_axes('dimensioncoordinate2')
        ('domainaxis2',)
        >>> f.has_data_axes()
        True

        >>> f.del_data_axes()
        ('domainaxis0', 'domainaxis1')
        >>> f.has_data_axes()
        False
        >>> f.get_data_axes(default='no axes')
        'no axes'

        """
        if key is None:
            axes = self.get_data_axes(default=None)
        else:
            axes = self.get_data_axes(key, default=None)

        if axes is None:
            return False

        return super().has_data_axes(key)

    def del_construct(self, key, default=ValueError()):
        """Remove a metadata construct.

        If a domain axis construct is selected for removal then it
        can't be spanned by any data arrays of the field nor metadata
        constructs, nor be referenced by any cell method
        constructs. However, a domain ancillary construct may be
        removed even if it is referenced by coordinate reference
        construct.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `get_construct`, `constructs`, `has_construct`,
                     `set_construct`

        :Parameters:

            key: `str`
                The construct identifier of the metadata construct to
                be removed.

                *Parameter example:*
                  ``key='auxiliarycoordinate0'``

            default: optional
                Return the value of the *default* parameter if the
                data axes have not been set.

                {{default Exception}}

        :Returns:

                The removed metadata construct.

        **Examples:**

        >>> f = {{package}}.example_field(4)
        >>> f.del_construct('auxiliarycoordinate2')
        <{{repr}}AuxiliaryCoordinate: longitude(3) degrees_east>

        >>> f = {{package}}.example_field(0)
        >>> f.del_construct('auxiliarycoordinate2')
        Traceback (most recent call last):
            ...
        ValueError: Can't remove non-existent construct
        >>> f.del_construct('auxiliarycoordinate2', default=False)
        False

        """
        domain_axes = self.constructs.filter_by_type(
            "domain_axis", todict=True
        )
        if key in domain_axes and key in self.get_data_axes(default=()):
            raise ValueError(
                f"Can't remove domain axis {key!r} that is spanned by the "
                "data of the field construct"
            )

        return self.constructs._del_construct(key, default=default)

    def set_data(self, data, axes=None, copy=True, inplace=True):
        """Set the data of the field construct.

        The units, calendar and fill value properties of the data
        object are removed prior to insertion.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `del_data`, `get_data`, `has_data`, `set_data_axes`

        :Parameters:

            data: data_like
                The data to be inserted.

                {{data_like}}

            axes: (sequence of) `str`, or `None`
                The identifiers of the domain axes spanned by the data
                array. If `None` then the data axes are not set.

                The axes may also be set afterwards with the
                `set_data_axes` method.

                *Parameter example:*
                  ``axes=['domainaxis2']``

                *Parameter example:*
                  ``axes='domainaxis2'``

                *Parameter example:*
                  ``axes=['domainaxis2', 'domainaxis1']``

                *Parameter example:*
                  ``axes=None``

            copy: `bool`, optional
                If False then do not copy the data prior to insertion. By
                default the data are copied.

            {{inplace: `bool`, optional (default True)}}

                .. versionadded:: (cfdm) 1.8.7.0

        :Returns:

            `None` or `{{class}}`
                If the operation was in-place then `None` is returned,
                otherwise return a new `{{class}}` instance containing the
                new data.

        **Examples:**

        >>> f = {{package}}.{{class}}()
        >>> f.set_data([1, 2, 3])
        >>> f.has_data()
        True
        >>> f.get_data()
        <{{repr}}Data(3): [1, 2, 3]>
        >>> f.data
        <{{repr}}Data(3): [1, 2, 3]>

        >>> f.del_data()
        <{{repr}}Data(3): [1, 2, 3]>
        >>> g = f.set_data([4, 5, 6], inplace=False)
        >>> g.data
        <{{repr}}Data(3): [4, 5, 6]>
        >>> f.has_data()
        False
        >>> print(f.get_data(None))
        None
        >>> print(f.del_data(None))
        None

        """
        if inplace:
            f = self
        else:
            f = self.copy(data=False)

        if axes is None:
            existing_axes = f.get_data_axes(default=None)
            if existing_axes is not None:
                f.set_data_axes(axes=existing_axes, _shape=numpy.shape(data))
        else:
            f.set_data_axes(axes=axes, _shape=numpy.shape(data))

        super(Field, f).set_data(data, copy=copy, inplace=True)

        if inplace:
            return

        return f

    def set_data_axes(self, axes, key=None, _shape=None):
        """Sets the axes spanned by the construct data.

        Specifically, sets the domain axis constructs spanned by the
        data of the field or of a metadata construct.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `del_data_axes`, `get_data`, `get_data_axes`,
                     `has_data_axes`

        :Parameters:

             axes: sequence of `str`
                The identifiers of the domain axis constructs spanned by
                the data of the field or of a metadata construct.

                *Parameter example:*
                  ``axes='domainaxis1'``

                *Parameter example:*
                  ``axes=['domainaxis1']``

                *Parameter example:*
                  ``axes=['domainaxis1', 'domainaxis0']``

             key: `str`, optional
                Specify a metadata construct, instead of the field
                construct.

                *Parameter example:*
                  ``key='domainancillary1'``

        :Returns:

            `None`

        **Examples:**

        Set the domain axis constructs spanned by the data of the field
        construct:

        >>> f = {{package}}.{{class}}()
        >>> f.set_data_axes(['domainaxis0', 'domainaxis1'])
        >>> f.get_data_axes()
        ('domainaxis0', 'domainaxis1')

        Set the domain axis constructs spanned by the data of a metadata
        construct:

        >>> f = {{package}}.example_field(5)
        >>> f.set_data_axes(['domainaxis1'], key='dimensioncoordinate1')

        """
        if isinstance(axes, str):
            axes = (axes,)

        if key is not None:
            return super().set_data_axes(axes=axes, key=key)

        if _shape is None:
            data = self.get_data(None)
            if data is not None:
                _shape = data.shape

        if _shape is not None:
            domain_axes = self.constructs.filter_by_type(
                "domain_axis", todict=True
            )
            axes_shape = []
            for axis in axes:
                if axis not in domain_axes:
                    raise ValueError(
                        "Can't set field construct data axes: Domain axis "
                        f"{axis!r} doesn't exist"
                    )

                axes_shape.append(domain_axes[axis].get_size())

            if _shape != tuple(axes_shape):
                raise ValueError(
                    "Can't set field construct data axes: Data array shape "
                    f"of {_shape!r} does not match the shape of the given "
                    f"domain axes {tuple(axes)}: {tuple(axes_shape)}"
                )

        axes = tuple(axes)
        self._set_component("data_axes", axes, copy=False)

        self.constructs._field_data_axes = axes
