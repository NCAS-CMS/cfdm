import re


class ConstructAccess:
    """Mixin to manipulate constructs stored in a `Constructs` object.

    .. versionadded:: (cfdm) 1.7.0

    """

    def _construct_types(
        self,
        _ctypes,
        _method,
        identities,
        todict=False,
        cached=None,
        **kwargs,
    ):
        """TODO.

        .. versionadded:: (cfdm) 1.8.10.0

        """
        if not _ctypes:
            filter_kwargs = kwargs
        else:
            if not (identities or kwargs):
                # Calling filter_by_type directly is faster
                return self.constructs.filter_by_type(
                    *_ctypes, todict=todict, cached=cached
                )

            # Ensure that filter_by_types is the first filter
            # applied, as it's the cheapest
            filter_kwargs = {"filter_by_type": _ctypes}

            if kwargs:
                if "filter_by_type" in kwargs:
                    raise TypeError(
                        f"{_method}() got an unexpected keyword argument "
                        "'filter_by_type'"
                    )

                filter_kwargs.update(kwargs)

        if identities:
            if "filter_by_identity" in kwargs:
                raise TypeError(
                    f"Can't set {_method}() keyword argument "
                    "'filter_by_identity' when positional *identities "
                    "arguments are also set"
                )

            # Ensure that filter_by_identity is the last filter
            # applied, as it's the most expensive.
            filter_kwargs["filter_by_identity"] = identities

        return self.constructs.filter(
            todict=todict, cached=cached, **filter_kwargs
        )

    def _unique_construct_names(self):
        """Return unique metadata construct names.

        .. versionadded:: (cfdm) 1.7.0

        **Examples:**

        >>> f._unique_construct_names()
        {'cellmethod0': 'method:mean',
         'dimensioncoordinate0': 'latitude',
         'dimensioncoordinate1': 'longitude',
         'dimensioncoordinate2': 'time',
         'domainaxis0': 'ncdim%lat',
         'domainaxis1': 'ncdim%lon',
         'domainaxis2': 'key%domainaxis2'}

        """
        key_to_name = {}
        ignore = self.constructs._ignore

        for ctype, d in self.constructs._constructs.items():
            if ctype in ignore:
                continue

            name_to_keys = {}

            for key, construct in d.items():
                name = construct.identity(default="key%" + key)
                name_to_keys.setdefault(name, []).append(key)
                key_to_name[key] = name

            for name, keys in name_to_keys.items():
                if len(keys) <= 1:
                    continue

                for key in keys:
                    key_to_name[key] = "{0}{{{1}}}".format(
                        name, re.findall(r"\d+$", key)[0]
                    )

        return key_to_name

    def _unique_domain_axis_identities(self):
        """Return unique domain axis construct names.

        .. versionadded:: (cfdm) 1.7.0

        **Examples:**

        >>> f._unique_domain_axis_identities()
        {'domainaxis0': 'latitude(5)',
         'domainaxis1': 'longitude(8)',
         'domainaxis2': 'time(1)'}

        """
        key_to_name = {}
        name_to_keys = {}

        for key, value in self.domain_axes(todict=True).items():
            name_size = (
                self.constructs.domain_axis_identity(key),
                value.get_size(""),
            )
            name_to_keys.setdefault(name_size, []).append(key)
            key_to_name[key] = name_size

        for (name, size), keys in name_to_keys.items():
            if len(keys) == 1:
                key_to_name[keys[0]] = f"{name}({size})"
            else:
                for key in keys:
                    key_to_name[key] = "{0}{{{1}}}({2})".format(
                        name, re.findall(r"\d+$", key)[0], size
                    )

        return key_to_name

    def coordinate_references(self, *identities, **kwargs):
        """Return coordinate reference constructs.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `constructs`

        :Parameters:

            {{cached: optional}}

            {{todict: `bool`, optional}}

        :Returns:

            `Constructs` or `dict`
                The constructs and their construct keys.


        **Examples:**

        >>> f.coordinate_references()
        Constructs:
        {}

        >>> f.coordinate_references()
        Constructs:
        {'coordinatereference0': <{{repr}}CoordinateReference: atmosphere_hybrid_height_coordinate>,
         'coordinatereference1': <{{repr}}CoordinateReference: rotated_latitude_longitude>}

        """
        return self._construct_types(
            ("coordinate_reference",),
            "coordinate_references",
            identities,
            **kwargs,
        )

    def domain_axes(self, *identities, **kwargs):
        """Return domain axis constructs.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `constructs`

        :Parameters:

            identities: optional

            kwargs: optional

        :Returns:

            `Constructs` or `dict`
                The domain axis constructs and their construct keys.

        **Examples:**

        >>> f.domain_axes()
        Constructs:
        {}

        >>> f.domain_axes()
        Constructs:
        {'domainaxis0': <{{repr}}DomainAxis: size(1)>,
         'domainaxis1': <{{repr}}DomainAxis: size(10)>,
         'domainaxis2': <{{repr}}DomainAxis: size(9)>,
         'domainaxis3': <{{repr}}DomainAxis: size(1)>}

        """
        return self._construct_types(
            ("domain_axis",), "domain_axes", identities, **kwargs
        )

    def auxiliary_coordinates(self, *identities, **kwargs):
        """Return auxiliary coordinate constructs.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `constructs`

        :Parameters:

            {{cached: optional}}

            {{todict: `bool`, optional}}

        :Returns:

            `Constructs` or `dict`
                The auxiliary coordinate constructs and their construct
                keys.

        **Examples:**

        >>> f.auxiliary_coordinates()
        Constructs:
        {}

        >>> f.auxiliary_coordinates()
        Constructs:
        {'auxiliarycoordinate0': <{{repr}}AuxiliaryCoordinate: latitude(10, 9) degrees_N>,
         'auxiliarycoordinate1': <{{repr}}AuxiliaryCoordinate: longitude(9, 10) degrees_E>,
         'auxiliarycoordinate2': <{{repr}}AuxiliaryCoordinate: long_name:Grid latitude name(10) >}

        """
        return self._construct_types(
            ("auxiliary_coordinate",),
            "auxiliary_coordinates",
            identities,
            **kwargs,
        )

    def dimension_coordinates(self, *identities, **kwargs):
        """Return dimension coordinate constructs.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `constructs`

        :Parameters:

            {{cached: optional}}

            {{todict: `bool`, optional}}

        :Returns:

            `Constructs` or `dict`
                The dimension coordinate constructs and their construct
                keys.

        **Examples:**

        >>> f.dimension_coordinates()
        Constructs:
        {}

        >>> f.dimension_coordinates()
        Constructs:
        {'dimensioncoordinate0': <{{repr}}DimensionCoordinate: atmosphere_hybrid_height_coordinate(1) >,
         'dimensioncoordinate1': <{{repr}}DimensionCoordinate: grid_latitude(10) degrees>,
         'dimensioncoordinate2': <{{repr}}DimensionCoordinate: grid_longitude(9) degrees>,
         'dimensioncoordinate3': <{{repr}}DimensionCoordinate: time(1) days since 2018-12-01 >}

        """
        return self._construct_types(
            ("dimension_coordinate",),
            "dimension_coordinates",
            identities,
            **kwargs,
        )

    def coordinates(self, *identities, **kwargs):
        """Return dimension and auxiliary coordinate constructs.

        . versionadded:: (cfdm) 1.7.0

        . seealso:: `auxiliary_coordinates`, `constructs`,
                    `dimension_coordinates`

        :Parameters:


            {{todict: `bool`, optional}}

        Returns:

           `Constructs` or `dict`
               The auxiliary coordinate and dimension coordinate
               constructs and their construct keys.

        *Examples:**

        >> f.coordinates()
        onstructs:
        }

        >> f.coordinates()
        onstructs:
        'auxiliarycoordinate0': <{{repr}}AuxiliaryCoordinate: latitude(10, 9) degrees_N>,
        'auxiliarycoordinate1': <{{repr}}AuxiliaryCoordinate: longitude(9, 10) degrees_E>,
        'auxiliarycoordinate2': <{{repr}}AuxiliaryCoordinate: long_name=Grid latitude name(10) >,
        'dimensioncoordinate0': <{{repr}}DimensionCoordinate: atmosphere_hybrid_height_coordinate(1) >,
        'dimensioncoordinate1': <{{repr}}DimensionCoordinate: grid_latitude(10) degrees>,
        'dimensioncoordinate2': <{{repr}}DimensionCoordinate: grid_longitude(9) degrees>,
        'dimensioncoordinate3': <{{repr}}DimensionCoordinate: time(1) days since 2018-12-01 >}

        """
        return self._construct_types(
            (
                "dimension_coordinate",
                "auxiliary_coordinate",
            ),
            "coordinates",
            identities,
            **kwargs,
        )

    def domain_ancillaries(self, *identities, **kwargs):
        """Return domain ancillary constructs.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `constructs`

        :Parameters:


            {{todict: `bool`, optional}}

        :Returns:

            `Constructs` or `dict`
                The domain ancillary constructs and their construct keys.

        **Examples:**

        >>> f.domain_ancillaries
        Constructs:
        {}

        >>> f.domain_ancillaries
        Constructs:
        {'domainancillary0': <{{repr}}DomainAncillary: ncvar%a(1) m>,
         'domainancillary1': <{{repr}}DomainAncillary: ncvar%b(1) >,
         'domainancillary2': <{{repr}}DomainAncillary: surface_altitude(10, 9) m>}

        """
        return self._construct_types(
            ("domain_ancillary",), "domain_ancillaries", identities, **kwargs
        )

    def cell_measures(self, *identities, **kwargs):
        """Return cell measure constructs.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `constructs`

        :Parameters:


        :Returns:

            `Constructs` or `dict`
                The cell measure constructs and their construct keys.

        **Examples:**

        >>> f.cell_measures
        Constructs:
        {}

        >>> f.cell_measures
        Constructs:
        {'cellmeasure0': <{{repr}}CellMeasure: measure%area(9, 10) km2>}

        """
        return self._construct_types(
            ("cell_measure",), "cell_measures", identities, **kwargs
        )

    def construct(self, identity=None, default=ValueError(), **kwargs):
        """Select a metadata construct by its identity.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `construct_key`, `constructs`

        :Parameters:

            identity: optional
                Select constructs that have the given identity. If exactly
                one construct is selected then it is returned, otherwise
                an exception is raised.

                The identity is specified by a string
                (e.g. ``'latitude'``, ``'long_name=time'``, etc.); or a
                compiled regular expression
                (e.g. ``re.compile('^atmosphere')``), for which all
                constructs whose identities match (via `re.search`) are
                selected.

                Each construct has a number of identities, and is selected
                if any of them match any of those provided. A construct's
                identities are those returned by its `!identities`
                method. In the following example, the construct ``c`` has
                four identities:

                   >>> c.identities()
                   ['time', 'long_name=Time', 'foo=bar', 'ncvar%T']

                In addition, each construct also has an identity based its
                construct key (e.g. ``'key%dimensioncoordinate2'``)

                Note that in the output of a `print` call or `!dump`
                method, a construct is always described by one of its
                identities, and so this description may always be used as
                an *identity* argument.

            default: optional
                Return the value of the *default* parameter if the
                property has not been set.

                {{default Exception}}

        :Returns:

                The selected construct.

        **Examples:**

        >>> print(f.constructs)
        Constructs:
        {'cellmethod0': {{repr}}<CellMethod: area: mean>,
         'dimensioncoordinate0': <{{repr}}DimensionCoordinate: latitude(5) degrees_north>,
         'dimensioncoordinate1': <{{repr}}DimensionCoordinate: longitude(8) degrees_east>,
         'dimensioncoordinate2': <{{repr}}DimensionCoordinate: long_name=time(1) days since 2018-12-01 >,
         'domainaxis0': <{{repr}}DomainAxis: size(5)>,
         'domainaxis1': <{{repr}}DomainAxis: size(8)>,
         'domainaxis2': <{{repr}}DomainAxis: size(1)>}

        Select the construct that has the "standard_name" property of 'latitude':

        >>> f.construct('latitude')
        <{{repr}}DimensionCoordinate: latitude(5) degrees_north>

        Select the cell method construct that has a "method" of 'mean':

        >>> f.construct('method:mean')
        <{{repr}}CellMethod: area: mean>

        Attempt to select the construct whose "standard_name" start with the
        letter 'l':

        >>> import re
        >>> f.construct(re.compile('^l'))
        ValueError: Can't return 2 constructs
        >>> f.construct(re.compile('^l'), default='no construct')
        'no construct'

        """
        if identity is None:
            identity = ()
        else:
            identity = (identity,)

        kwargs["todict"] = True

        c = self._construct_types(
            (),
            "construct",
            identity,
            **kwargs,
        )

        n = len(c)
        if n == 1:
            _, c = c.popitem()
            return c

        if not n:
            return self._default(default, "Can't return zero constructs")

        return self._default(
            default, f"Can't return more than one ({n}) construct"
        )

    def construct_key(self, identity=None, default=ValueError(), **kwargs):
        """Select the key of a metadata construct by its identity.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `construct`, `constructs`

        :Parameters:

            identity: optional
                Select constructs that have the given identity. If exactly
                one construct is selected then it is returned, otherwise
                an exception is raised.

                The identity is specified by a string
                (e.g. ``'latitude'``, ``'long_name=time'``, etc.); or a
                compiled regular expression
                (e.g. ``re.compile('^atmosphere')``), for which all
                constructs whose identities match (via `re.search`) are
                selected.

                Each construct has a number of identities, and is selected
                if any of them match any of those provided. A construct's
                identities are those returned by its `!identities`
                method. In the following example, the construct ``c`` has
                four identities:

                   >>> c.identities()
                   ['time', 'long_name=Time', 'foo=bar', 'ncvar%T']

                In addition, each construct also has an identity based its
                construct key (e.g. ``'key%dimensioncoordinate2'``)

                Note that in the output of a `print` call or `!dump`
                method, a construct is always described by one of its
                identities, and so this description may always be used as
                an *identity* argument.

            default: optional
                Return the value of the *default* parameter if the
                property has not been set

                {{default Exception}}

        :Returns:

            `str`
                The key of the selected construct.

        **Examples:**

        >>> print(f.constructs)
        Constructs:
        {'cellmethod0': <{{repr}}ellMethod: area: mean>,
         'dimensioncoordinate0': <{{repr}}DimensionCoordinate: latitude(5) degrees_north>,
         'dimensioncoordinate1': <{{repr}}DimensionCoordinate: longitude(8) degrees_east>,
         'dimensioncoordinate2': <{{repr}}DimensionCoordinate: long_name=time(1) days since 2018-12-01 >,
         'domainaxis0': <{{repr}}DomainAxis: size(5)>,
         'domainaxis1': <{{repr}}DomainAxis: size(8)>,
         'domainaxis2': <{{repr}}DomainAxis: size(1)>}

        Select the construct that has the "standard_name" property of
        'latitude':

        >>> f.construct_key('latitude')
         'dimensioncoordinate0'

        Select the cell method construct that has a "method" of 'mean':

        >>> f.construct_key('method:mean')
        'cellmethod0'

        Attempt to select the construct whose "standard_name" start with
        the letter 'l':

        >>> import re
        >>> f.construct_key(re.compile('^l'))
        ValueError: Can't return the key of 2 constructs
        >>> f.construct_key(re.compile('^l'), default='no construct')
        'no construct'

        """
        if identity is None:
            identity = ()
        else:
            identity = (identity,)

        kwargs["todict"] = True

        c = self._construct_types(
            (),
            "construct",
            identity,
            **kwargs,
        )

        n = len(c)
        if n == 1:
            key, _ = c.popitem()
            return key

        if not n:
            return self._default(
                default, "Can't return the key of zero constructs"
            )

        return self._default(
            default, f"Can't return the keys of more than one ({n}) construct"
        )

    def domain_axis_key(self, identity, default=ValueError()):
        """Returns the domain axis key spanned by the coordinates.

        Specifically, returns the key of the domain axis construct that
        is spanned by 1-d coordinate constructs.

        :Parameters:

            identity:
                Select the 1-d coordinate constructs that have the
                given identity.

                An identity is specified by a string
                (e.g. ``'latitude'``, ``'long_name=time'``, etc.); or
                a compiled regular expression
                (e.g. ``re.compile('^atmosphere')``), for which all
                constructs whose identities match (via `re.search`)
                are selected.

                Each coordinate construct has a number of identities,
                and is selected if any of them match any of those
                provided. A construct's identities are those returned
                by its `!identities` method. In the following example,
                the construct ``x`` has four identities:

                   >>> x.identities()
                   ['time', 'long_name=Time', 'foo=bar', 'ncvar%T']

                In addition, each construct also has an identity based
                its construct key
                (e.g. ``'key%dimensioncoordinate2'``)

                Note that in the output of a `print` call or `!dump`
                method, a construct is always described by one of its
                identities, and so this description may always be used
                as an *identity* argument.

            default: optional
                Return the value of the *default* parameter if a domain
                axis construct can not be found.

                {{default Exception}}

        :Returns:

            `str`
                The key of the domain axis construct that is spanned by
                the data of the selected 1-d coordinate constructs.

        **Examples:**

        >>> print(f.constructs())
        Constructs:
        {'dimensioncoordinate0': <{{repr}}DimensionCoordinate: time(1) days since 1964-01-21 00:00:00 >,
         'dimensioncoordinate1': <{{repr}}DimensionCoordinate: pressure(23) mbar>,
         'dimensioncoordinate2': <{{repr}}DimensionCoordinate: latitude(160) degrees_north>,
         'dimensioncoordinate3': <{{repr}}DimensionCoordinate: longitude(320) degrees_east>,
         'domainaxis0': <{{repr}}DomainAxis: size(1)>,
         'domainaxis1': <{{repr}}DomainAxis: size(23)>,
         'domainaxis2': <{{repr}}DomainAxis: size(160)>,
         'domainaxis3': <{{repr}}DomainAxis: size(320)>}
        >>> f.domain.domain_axis_key('time')
        'domainaxis0'
        >>> f.domain.domain_axis_key('longitude')
        'domainaxis3'

        """
        # Select 1-d coordinate constructs with the given identity
        c = self.constructs.filter(
            filter_by_type=("dimension_coordinate", "auxiliary_coordinate"),
            filter_by_naxes=(1,),
            filter_by_identity=(identity,),
            todict=True,
        )

        if not c:
            return self._default(
                default,
                f"There are no 1-d {identity!r} coordinate constructs",
            )

        data_axes = self.constructs.data_axes()
        domain_axes = self.domain_axes(todict=True)

        keys = []
        for ckey, coord in c.items():
            axes = data_axes.get(ckey)
            if not axes:
                continue

            key = axes[0]
            if domain_axes.get(key):
                keys.append(key)

        keys = set(keys)

        if not keys:
            return self._default(
                default,
                "1-d {identity!r} coordinate constructs "
                "have not been assigned a domain axis construct",
            )

        if len(keys) > 1:
            return self._default(
                default,
                f"Multiple 1-d {identity!r} coordinate constructs "
                "span multiple domain axes: {keys!r}",
            )

        return keys.pop()
