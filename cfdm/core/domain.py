from . import Constructs, abstract, mixin


class Domain(mixin.FieldDomain, abstract.Properties):
    """A domain construct of the CF data model.

    The domain represents a set of discrete "locations" in what
    generally would be a multi-dimensional space, either in the real
    world or in a model's simulated world. The data array elements of
    a field construct correspond to individual location of a domain.

    The domain construct is defined collectively by the following
    constructs of the CF data model: domain axis, dimension
    coordinate, auxiliary coordinate, cell measure, coordinate
    reference, and domain ancillary constructs; as well as properties
    to describe the domain.

    .. versionadded:: (cfdm) 1.7.0

    """

    # Define the base of the identity keys for each construct type
    _construct_key_base = {
        "auxiliary_coordinate": "auxiliarycoordinate",
        "cell_measure": "cellmeasure",
        "coordinate_reference": "coordinatereference",
        "dimension_coordinate": "dimensioncoordinate",
        "domain_ancillary": "domainancillary",
        "domain_axis": "domainaxis",
    }

    def __new__(cls, *args, **kwargs):
        """This must be overridden in subclasses."""
        instance = super().__new__(cls)
        instance._Constructs = Constructs
        return instance

    def __init__(
        self, properties=None, source=None, copy=True, _use_data=True
    ):
        """**Initialisation**

        :Parameters:

            {{init properties: `dict`, optional}}

            *Parameter example:*
               ``properties={'long_name': 'Domain for model'}``

            source: optional
                Initialise the metadata constructs from those of
                *source*.

                {{init source}}

                A new domain may also be instantiated with the
                `fromconstructs` class method.

            {{init copy: `bool`, optional}}

        """
        super().__init__(properties=properties, source=source, copy=copy)

        if source is not None:
            try:
                constructs = source.constructs
            except AttributeError:
                constructs = self._Constructs(**self._construct_key_base)
                copy = False
                _use_data = True
            else:
                constructs = constructs._view(
                    ignore=("cell_method", "field_ancillary")
                )
        else:
            constructs = self._Constructs(**self._construct_key_base)
            copy = False
            _use_data = True

        if copy or not _use_data:
            constructs = constructs.copy(data=_use_data)

        self._set_component("constructs", constructs, copy=False)

    # ----------------------------------------------------------------
    # Attributes
    # ----------------------------------------------------------------
    @property
    def construct_type(self):
        """Return a description of the construct type.

        .. versionadded:: (cfdm) 1.9.0.0

        :Returns:
            `str`
                The construct type.

        **Examples:**

        >>> d = {{package}}.{{class}}()
        >>> d.construct_type
        'domain'

        """
        return "domain"

    @property
    def constructs(self):
        """Return the metadata constructs.

        .. versionadded:: (cfdm) 1.7.0

        :Returns:

            `Constructs`
                The constructs.

        **Examples:**

        >>> d = {{package}}.example_field(0)
        >>> print(d.constructs)
        Constructs:
        {'cellmethod0': <CellMethod: area: mean>,
         'dimensioncoordinate0': <{{repr}}DimensionCoordinate: latitude(5) degrees_north>,
         'dimensioncoordinate1': <{{repr}}DimensionCoordinate: longitude(8) degrees_east>,
         'dimensioncoordinate2': <{{repr}}DimensionCoordinate: time(1) days since 2018-12-01 >,
         'domainaxis0': <{{repr}}DomainAxis: size(5)>,
         'domainaxis1': <{{repr}}DomainAxis: size(8)>,
         'domainaxis2': <{{repr}}DomainAxis: size(1)>}

        """
        return self._get_component("constructs")

    # ----------------------------------------------------------------
    # Methods
    # ----------------------------------------------------------------
    def copy(self, data=True):
        """Return a deep copy.

        ``d.copy()`` is equivalent to ``copy.deepcopy(d)``.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `fromconstructs`

        :Parameters:

            data: `bool`, optional
                If False then do not copy data. By default data are
                copied.

        :Returns:

            `{{class}}`
                The deep copy.

        **Examples:**

        >>> d = {{package}}.{{class}}()
        >>> e = d.copy()

        """
        return type(self)(source=self, copy=True, _use_data=data)

    def del_construct(self, key, default=ValueError()):
        """Remove a metadata construct.

        If a domain axis construct is selected for removal then it
        can't be spanned by any data arrays of the metadata
        constructs. However, a domain ancillary construct may be
        removed even if it is referenced by coordinate reference
        construct.

        .. versionadded:: (cfdm) 1.9.0.0

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

        >>> f.del_construct('auxiliarycoordinate2')
        <{{repr}}AuxiliaryCoordinate: latitude(111, 106) degrees_north>
        >>> f.del_construct('auxiliarycoordinate2')
        ValueError: Can't get remove non-existent construct
        >>> f.del_construct('auxiliarycoordinate2', default=False)
        False

        """
        return self.constructs._del_construct(key, default=default)

    @classmethod
    def fromconstructs(cls, constructs, copy=False):
        """Return a new domain containing the given metadata constructs.

        The new domain acts as a view to the given constructs,
        i.e. changes to the domain, such as the addition or removal of
        a construct, will also affect the input `Constructs` instance.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            constructs: `Constructs`
                The constructs from which to create the new
                domain. Cell method and field ancillary constructs are
                ignored.

            copy: `bool`, optional
                If True then deep copy the metadata constructs prior
                to initialization. By default the metadata constructs
                are not copied. Note that even when *copy* is True,
                the input `Constructs` container is not copied.

        :Returns:

            `{{class}}`
                The domain created from a view of the constructs.

        **Examples:**

        >>> f = {{package}}.example_field(0)
        >>> d = {{package}}.{{class}}.fromconstructs(f.constructs)
        >>> d
        <Domain: {1, 5, 8}>
        >>> d = {{package}}.{{class}}.fromconstructs(f.constructs.copy())

        """
        domain = cls()
        domain._set_component(
            "constructs",
            constructs._view(ignore=("cell_method", "field_ancillary")),
            copy=copy,
        )

        domain.constructs._field_data_axes = None

        return domain
