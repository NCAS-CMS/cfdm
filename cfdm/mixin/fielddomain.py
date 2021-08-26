import logging
import re

from ..decorators import _manage_log_level_via_verbosity

logger = logging.getLogger(__name__)


class FieldDomain:
    """Mixin class for methods of field and domain constructs.

    .. versionadded:: (cfdm) 1.9.0.0

    """

    # ----------------------------------------------------------------
    # Private methods
    # ----------------------------------------------------------------
    def _apply_masking_constructs(self):
        """Apply masking to metadata constructs in-place.

        Masking is applied to all metadata constructs with data.

        See `Field.apply_masking` or `Domain.apply_masking` for details

        .. versionadded:: (cfdm) 1.9.0.0

        :Returns:

            `None`

        """
        # Apply masking to the metadata constructs
        for c in self.constructs.filter_by_data(todict=True).values():
            c.apply_masking(inplace=True)

    def _get_data_compression_variables(self, component):
        """TODO."""
        out = []
        for construct in self.constructs.filter_by_data(todict=True).values():
            data = construct.get_data(None)
            if data is None:
                continue

            x = getattr(data, f"get_{component}")(None)
            if x is None:
                continue

            out.append(x)

        for construct in self.constructs.filter_by_data(todict=True).values():
            if not construct.has_bounds():
                continue

            data = construct.get_bounds_data(None)
            if data is None:
                continue

            x = getattr(data, f"get_{component}")(None)
            if x is None:
                continue

            out.append(x)

        for construct in self.coordinates(todict=True).values():
            interior_ring = construct.get_interior_ring(None)
            if interior_ring is None:
                continue

            data = interior_ring.get_data(None)
            if data is None:
                continue

            x = getattr(data, f"get_{component}")(None)
            if x is None:
                continue

            out.append(x)

        return out

    def _get_coordinate_geometry_variables(self, component):
        """Return the list of variables for the geometry coordinates.

        :Parameters:

            component: `str`

        :Returns:

            `list'

        """
        out = []
        for construct in self.coordinates(todict=True).values():
            x = getattr(construct, f"get_{component}")(None)
            if x is None:
                continue

            out.append(x)

        return out

    def _filter_return_construct(self, c, key, item, default, _method):
        """Return construct, or key, or both, or default.

        :Parameters:

            c: `Constructs` or `dict`

            key: `bool`, optional
                If True then return the selected construct
                identifier. By default the construct itself is
                returned.

            item: `bool`, optional
                If True then return the selected construct identifier
                and the construct itself. By default the construct
                itself is returned. If *key* is True then *item* is
                ignored.

            _method: `str`
                The name of the ultimate calling method.

        :Returns:

                The selected construct, or its identifier if *key* is
                True, or a tuple of both if *item* is True.

        """
        n = len(c)
        if n == 1:
            k, construct = c.popitem()
            if key:
                return k

            if item:
                return k, construct

            return construct

        if default is None:
            return default

        return self._default(
            default,
            f"{self.__class__.__name__}.{_method}() can't return {n} "
            "constructs",
        )

    def _filter_interface(
        self,
        _ctypes,
        _method,
        identities,
        cached=None,
        construct=False,
        key=False,
        item=False,
        default=None,
        _identity_config={},
        **filter_kwargs,
    ):
        """An optimised interface to `Constructs.filter`.

        .. versionadded:: (cfdm) 1.8.9.0

        :Parameters:

            _ctypes: `tuple` of `str`
                The construct types to restrict the selection to.

            _method: `str`
                The name of the calling method.

            identities: `tuple`
                Select constructs that have an identity, defined by
                their `!identities` methods, that matches any of the
                given tuple values.

                {{value match}}

            {{todict: `bool`, optional}}

            {{cached: optional}}

            {{filter_kwargs: optional}}

        :Returns:

            `Constructs` or `dict` or *cached*
                If *cached* is `None`, return the selected
                constructs. If *cached* is not `None`, return
                *cached*.

        """
        if cached is not None:
            return cached

        if not _ctypes:
            kwargs = filter_kwargs
        else:
            # Ensure that filter_by_types is the first filter
            # applied, as it's the cheapest
            if not (identities or filter_kwargs):
                # This a very common pattern for which calling
                # filter_by_type directly is faster
                if construct:
                    todict = True
                else:
                    todict = False

                c = self.constructs.filter_by_type(*_ctypes, todict=todict)

                if not construct:
                    # Return Constructs or dict
                    return c

                # Return construct, or key, or both, or default
                return self._filter_return_construct(
                    c, key, item, default, _method
                )
                # n = len(c)
                # if n == 1:
                #    k, construct = c.popitem()
                #    if key:
                #        return k
                #
                #    if item:
                #        return k, construct
                #
                #    return construct
                #
                # if default is None:
                #    return default
                #
                # return self._default(
                #    default,
                #    f"{self.__class__.__name__}.{_method}() can't return {n} "
                #    "constructs",
                # )

            kwargs = {"filter_by_type": _ctypes}

            if filter_kwargs:
                if "filter_by_type" in filter_kwargs:
                    raise TypeError(
                        f"{self.__class__.__name__}.{_method}() got an "
                        "unexpected keyword argument 'filter_by_type'"
                    )

                kwargs.update(filter_kwargs)

        # Ensure that filter_by_identity is the one of the last
        # filters applied, as it's expensive.
        if filter_kwargs:
            if identities:
                if "filter_by_identity" in filter_kwargs:
                    raise TypeError(
                        f"Can't set {self.__class__.__name__}.{_method}() "
                        "keyword argument 'filter_by_identity' when "
                        "positional *identities arguments are also set"
                    )

                kwargs["filter_by_identity"] = identities
            elif "filter_by_identity" in filter_kwargs:
                kwargs["filter_by_identity"] = filter_kwargs[
                    "filter_by_identity"
                ]
        elif identities:
            kwargs["filter_by_identity"] = identities

        if construct:
            kwargs["todict"] = True

        c = self.constructs.filter(
            _identity_config=_identity_config,
            **kwargs,
        )

        if not construct:
            # Return Constructs or dict
            return c

        # Return construct, or key, or both, or default
        return self._filter_return_construct(c, key, item, default, _method)

        # if len(c) == 1:
        #    k, construct = c.popitem()
        #    if key:
        #        return k
        #
        #    if item:
        #        return k, construct
        #
        #    return construct
        #
        # if default is None:
        #    return default
        #
        # return self._default(
        #    default,
        #    f"{self.__class__.__name__}.{_method}() can't return {len(c)} "
        #    "constructs",
        # )

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
                    found = re.findall(r"\d+$", key)[0]
                    key_to_name[key] = f"{name}{{{found}}}"

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
                    found = re.findall(r"\d+$", key)[0]
                    key_to_name[key] = f"{name}{{{found}}}({size})"

        return key_to_name

    def auxiliary_coordinates(self, *identities, **filter_kwargs):
        """Return auxiliary coordinate constructs.

        Note that ``f.auxiliary_coordinates(*identities,
        **filter_kwargs)`` is equivalent to
        ``f.constructs.filter(filter_by_type=["auxiliary_coordinate"],
        filter_by_identity=identities, **filter_kwargs)``.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `constructs`

        :Parameters:

            identities: optional
                Select auxiliary coordinate constructs that have an
                identity, defined by their `!identities` methods, that
                matches any of the given values.

                If no identities are provided then all auxiliary
                coordinate constructs are selected.

                {{value match}}

                {{displayed identity}}

            {{filter_kwargs: optional}} Also to configure the returned value.

                .. versionadded:: (cfdm) 1.8.9.0

        :Returns:

                {{Returns constructs}}

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
        return self._filter_interface(
            ("auxiliary_coordinate",),
            "auxiliary_coordinates",
            identities,
            **filter_kwargs,
        )

    def coordinates(self, *identities, **filter_kwargs):
        """Return dimension and auxiliary coordinate constructs.

        Note that ``f.coordinates(*identities, **filter_kwargs)`` is
        equivalent to
        ``f.constructs.filter(filter_by_type=["dimension_coordinate",
        "auxiliary_coordinate"], filter_by_identity=identities,
        **filter_kwargs)``.

        . versionadded:: (cfdm) 1.7.0

        . seealso:: `auxiliary_coordinates`, `constructs`,
                    `dimension_coordinates`

        :Parameters:

            identities: optional
                Select dimension and auxiliary coordinate constructs
                that have an identity, defined by their `!identities`
                methods, that matches any of the given values.

                If no identities are provided then all dimension and
                auxiliary coordinate constructs are selected.

                {{value match}}

                {{displayed identity}}

            {{filter_kwargs: optional}} Also to configure the returned value.

                .. versionadded:: (cfdm) 1.8.9.0

        :Returns:

                {{Returns constructs}}

        *Examples:**

        >> f.coordinates()
        Constructs:
        }

        >> f.coordinates()
        Constructs:
        'auxiliarycoordinate0': <{{repr}}AuxiliaryCoordinate: latitude(10, 9) degrees_N>,
        'auxiliarycoordinate1': <{{repr}}AuxiliaryCoordinate: longitude(9, 10) degrees_E>,
        'auxiliarycoordinate2': <{{repr}}AuxiliaryCoordinate: long_name=Grid latitude name(10) >,
        'dimensioncoordinate0': <{{repr}}DimensionCoordinate: atmosphere_hybrid_height_coordinate(1) >,
        'dimensioncoordinate1': <{{repr}}DimensionCoordinate: grid_latitude(10) degrees>,
        'dimensioncoordinate2': <{{repr}}DimensionCoordinate: grid_longitude(9) degrees>,
        'dimensioncoordinate3': <{{repr}}DimensionCoordinate: time(1) days since 2018-12-01 >}

        """
        return self._filter_interface(
            (
                "dimension_coordinate",
                "auxiliary_coordinate",
            ),
            "coordinates",
            identities,
            **filter_kwargs,
        )

    def coordinate_references(self, *identities, **filter_kwargs):
        """Return coordinate reference constructs.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `constructs`

        :Parameters:

            identities: optional
                Select coordinate reference constructs that have an
                identity, defined by their `!identities` methods, that
                matches any of the given values.

                Additionally, the values are matched against construct
                identifiers, with or without the ``'key%'`` prefix.

                If no identities are provided then all coordinate
                reference constructs are selected.

                {{value match}}

                {{displayed identity}}

            {{filter_kwargs: optional}} Also to configure the returned value.

                .. versionadded:: (cfdm) 1.8.9.0

        :Returns:

                {{Returns constructs}}

        **Examples:**

        >>> f.coordinate_references()
        Constructs:
        {}

        >>> f.coordinate_references()
        Constructs:
        {'coordinatereference0': <{{repr}}CoordinateReference: atmosphere_hybrid_height_coordinate>,
         'coordinatereference1': <{{repr}}CoordinateReference: rotated_latitude_longitude>}

        """
        return self._filter_interface(
            ("coordinate_reference",),
            "coordinate_references",
            identities,
            **filter_kwargs,
        )

    def del_construct(self, *identity, default=ValueError(), **filter_kwargs):
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

            identity:
                Select the unique construct that has the identity,
                defined by its `!identities` method, that matches the
                given values.

                Additionally, the values are matched against construct
                identifiers, with or without the ``'key%'`` prefix.

                {{value match}}

                {{displayed identity}}

            default: optional
                Return the value of the *default* parameter if the
                data axes have not been set.

                {{default Exception}}

            {{filter_kwargs: optional}}

                .. versionadded:: (cfdm) 1.8.9.0

        :Returns:

                The removed metadata construct.

        **Examples:**

        >>> f = {{package}}.example_field(0)
        >>> print(f)
        Field: specific_humidity (ncvar%q)
        ----------------------------------
        Data            : specific_humidity(latitude(5), longitude(8)) 1
        Cell methods    : area: mean
        Dimension coords: latitude(5) = [-75.0, ..., 75.0] degrees_north
                        : longitude(8) = [22.5, ..., 337.5] degrees_east
                        : time(1) = [2019-01-01 00:00:00]
        >>> f.del_construct('time')
        <{{repr}}DimensionCoordinate: time(1) days since 2018-12-01 >
        >>> f.del_construct('time')
        Traceback (most recent call last):
            ...
        ValueError: Can't remove non-existent construct 'ti
        >>> f.del_construct('time', default='No time')
        'No time'
        >>> f.del_construct('dimensioncoordinate1')
        <{{repr}}DimensionCoordinate: longitude(8) degrees_east>
        >>> print(f)
        Field: specific_humidity (ncvar%q)
        ----------------------------------
        Data            : specific_humidity(latitude(5), ncdim%lon(8)) 1
        Cell methods    : area: mean
        Dimension coords: latitude(5) = [-75.0, ..., 75.0] degrees_north

        """
        key = self.construct_key(*identity, default=None, **filter_kwargs)
        if key is not None:
            return self.constructs._del_construct(key)

        if default is None:
            return default

        return self._default(default, "Can't find unique construct to remove")

    def dimension_coordinates(self, *identities, **filter_kwargs):
        """Return dimension coordinate constructs.

        Note that ``f.dimension_coordinates(*identities,
        **filter_kwargs)`` is equivalent to
        ``f.constructs.filter(filter_by_type=["dimension_coordinate"],
        filter_by_identity=identities, **filter_kwargs)``.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `constructs`

        :Parameters:

            identities: optional
                Select dimension coordinate constructs that have an
                identity, defined by their `!identities` methods, that
                matches any of the given values.

                If no identities are provided then all dimension
                coordinate constructs are selected.

                {{value match}}

                {{displayed identity}}

            {{filter_kwargs: optional}} Also to configure the returned value.

                .. versionadded:: (cfdm) 1.8.9.0

        :Returns:

                {{Returns constructs}}

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
        return self._filter_interface(
            ("dimension_coordinate",),
            "dimension_coordinates",
            identities,
            **filter_kwargs,
        )

    def domain_axes(self, *identities, **filter_kwargs):
        """Return domain axis constructs.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `constructs`

        :Parameters:

            identities: `tuple`, optional
                Select domain axis constructs that have an identity,
                defined by their `!identities` methods, that matches
                any of the given values.

                Additionally, the values are matched against construct
                identifiers, with or without the ``'key%'`` prefix.

                Additionally, if for a given ``value``,
                ``f.coordinates(value, filter_by_naxes=(1,))`` returns
                1-d coordinate constructs that all span the same
                domain axis construct then that domain axis construct
                is selected. See `coordinates` for details.

                Additionally, if there is an associated `Field` data
                array and a value matches the integer position of an
                array dimension, then the corresponding domain axis
                construct is selected.

                If no values are provided then all domain axis
                constructs are selected.

                {{value match}}

                {{displayed identity}}

            {{filter_kwargs: optional}} Also to configure the returned value.

                .. versionadded:: (cfdm) 1.8.9.0

        :Returns:

                {{Returns constructs}}

        **Examples:**

        """
        return self.constructs.domain_axes(*identities, **filter_kwargs)

    def domain_ancillaries(self, *identities, **filter_kwargs):
        """Return domain ancillary constructs.

        Note that ``f.domain_ancillaries(*identities,
        **filter_kwargs)`` is equivalent to
        ``f.constructs.filter(filter_by_type=["domain_ancillary"],
        filter_by_identity=identities, **filter_kwargs)``.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `constructs`

        :Parameters:

            identities: optional
                Select domain ancillary constructs that have an
                identity, defined by their `!identities` methods, that
                matches any of the given values.

                {{value match}}

                {{displayed identity}}

            {{filter_kwargs: optional}} Also to configure the returned value.

                .. versionadded:: (cfdm) 1.8.9.0

        :Returns:

                {{Returns constructs}}

        **Examples:**

        >>> f.domain_ancillaries()
        Constructs:
        {}

        >>> f.domain_ancillaries()
        Constructs:
        {'domainancillary0': <{{repr}}DomainAncillary: ncvar%a(1) m>,
         'domainancillary1': <{{repr}}DomainAncillary: ncvar%b(1) >,
         'domainancillary2': <{{repr}}DomainAncillary: surface_altitude(10, 9) m>}

        """
        return self._filter_interface(
            ("domain_ancillary",),
            "domain_ancillaries",
            identities,
            **filter_kwargs,
        )

    def cell_measures(self, *identities, **filter_kwargs):
        """Return cell measure constructs.

        ``f.cell_measures(*identities, **filter_kwargs)`` is
        equivalent to
        ``f.constructs.filter(filter_by_type=["cell_measure"],
        filter_by_identity=identities, **filter_kwargs)``.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `constructs`

        :Parameters:

            identities: optional
                Select cell measure constructs that have an identity,
                defined by their `!identities` methods, that matches
                any of the given values.

                If no identities are provided then all cell measure
                constructs are selected.

                {{value match}}

                {{displayed identity}}

            {{filter_kwargs: optional}} Also to configure the returned value.

                .. versionadded:: (cfdm) 1.8.9.0

        :Returns:

                {{Returns constructs}}

        **Examples:**

        >>> f.cell_measures()
        Constructs:
        {}

        >>> f.cell_measures()
        Constructs:
        {'cellmeasure0': <{{repr}}CellMeasure: measure%area(9, 10) km2>}

        """
        return self._filter_interface(
            ("cell_measure",), "cell_measures", identities, **filter_kwargs
        )

    def construct(self, *identity, default=ValueError(), **filter_kwargs):
        """Return a metadata construct.

        {{unique construct}}

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `constructs`, `construct_item`, `construct_key`

        :Parameters:

            identity: optional
                Select constructs that have an identity, defined by
                their `!identities` methods, that matches any of the
                given values.

                Additionally, the values are matched against construct
                identifiers, with or without the ``'key%'`` prefix.

                If no values are provided then all constructs are
                selected.

                {{value match}}

                {{displayed identity}}

            default: optional
                Return the value of the *default* parameter if there
                is no unique construct.

                {{default Exception}}

            {{filter_kwargs: optional}}

                .. versionadded:: (cfdm) 1.8.9.0

        :Returns:

                The selected construct.

        **Examples:**

        >>> f = {{package}}.example_{{class_lower}}(0)

        Select the construct that has the "standard_name" property of
        'latitude':

        >>> print(f.constructs.filter_by_property(standard_name=None))
        Constructs:
        {'dimensioncoordinate0': <{{repr}}DimensionCoordinate: latitude(5) degrees_north>,
         'dimensioncoordinate1': <{{repr}}DimensionCoordinate: longitude(8) degrees_east>,
         'dimensioncoordinate2': <{{repr}}DimensionCoordinate: long_name=time(1) days since 2018-12-01 >}
        >>> f.construct('latitude')
        <{{repr}}DimensionCoordinate: latitude(5) degrees_north>

        Attempt to select a unique construct whose "standard_name"
        start with the letter 'l':

        >>> import re
        >>> f.construct(re.compile('^l'))
        Traceback
            ...
        ValueError: {{class}}.construct() can't return 2 constructs
        >>> f.construct(re.compile('^l'), default='no unique construct')
        'no unique construct'

        """
        return self._filter_interface(
            (),
            "construct",
            identity,
            construct=True,
            key=False,
            item=False,
            default=default,
            **filter_kwargs,
        )

    def construct_item(self, *identity, default=ValueError(), **filter_kwargs):
        """Return a metadata construct and its identifier.

        {{unique construct}}

        .. versionadded:: (cfdm) 1.8.9.0

        .. seealso:: `constructs`, `construct`, `construct_key`

        :Parameters:

            identity: optional
                Select constructs that have an identity, defined by
                their `!identities` methods, that matches any of the
                given values.

                Additionally, the values are matched against construct
                identifiers, with or without the ``'key%'`` prefix.

                If no values are provided then all constructs are
                selected.

                {{value match}}

                {{displayed identity}}

            default: optional
                Return the value of the *default* parameter if there
                is no unique construct.

                {{default Exception}}

            {{filter_kwargs: optional}}

                .. versionadded:: (cfdm) 1.8.9.0

        :Returns:

            `tuple`
                The selected construct and its construct identifier.

        **Examples:**

        >>> f = {{package}}.example_{{class_lower}}(0)

        Select the construct that has the "standard_name" property of
        'latitude':

        >>> print(f.constructs.filter_by_property(standard_name=None))
        Constructs:
        {'dimensioncoordinate0': <{{repr}}DimensionCoordinate: latitude(5) degrees_north>,
         'dimensioncoordinate1': <{{repr}}DimensionCoordinate: longitude(8) degrees_east>,
         'dimensioncoordinate2': <{{repr}}DimensionCoordinate: long_name=time(1) days since 2018-12-01 >}
        >>> f.construct_item('latitude')
        ('dimensioncoordinate1', <{{repr}}DimensionCoordinate: latitude(5) degrees_north>)

        Attempt to select a unique construct whose "standard_name"
        start with the letter 'l':

        >>> import re
        >>> f.construct(re.compile('^l'))
        Traceback
            ...
        ValueError: {{class}}.construct() can't return 2 constructs
        >>> f.construct(re.compile('^l'), default='no unique construct')
        'no unique construct'

        """
        return self._filter_interface(
            (),
            "construct",
            identity,
            construct=True,
            key=False,
            item=True,
            default=default,
            **filter_kwargs,
        )

    def construct_key(self, *identity, default=ValueError(), **filter_kwargs):
        """Return the identifier of a metadata construct.

        {{unique construct}}

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `constructs`, `construct`, `construct_item`

        :Parameters:

            identity: optional
                Select constructs that have an identity, defined by
                their `!identities` methods, that matches any of the
                given values.

                Additionally, the values are matched against construct
                identifiers, with or without the ``'key%'`` prefix.

                If no values are provided then all constructs are
                selected.

                {{value match}}

                {{displayed identity}}

            default: optional
                Return the value of the *default* parameter if there
                is no unique construct.

                {{default Exception}}

            {{filter_kwargs: optional}}

                .. versionadded:: (cfdm) 1.8.9.0

        :Returns:

            `str`
                The identifier of the selected construct.

        **Examples:**

        >>> f = {{package}}.example_{{class_lower}}(0)

        Select the construct that has the "standard_name" property of
        'latitude':

        >>> print(f.constructs.filter_by_property(standard_name=None))
        Constructs:
        {'dimensioncoordinate0': <{{repr}}DimensionCoordinate: latitude(5) degrees_north>,
         'dimensioncoordinate1': <{{repr}}DimensionCoordinate: longitude(8) degrees_east>,
         'dimensioncoordinate2': <{{repr}}DimensionCoordinate: long_name=time(1) days since 2018-12-01 >}
        >>> f.construct_key('latitude')
        'dimensioncoordinate1'

        Attempt to select a unique construct whose "standard_name"
        start with the letter 'l':

        >>> import re
        >>> f.construct(re.compile('^l'))
        Traceback
            ...
        ValueError: {{class}}.construct() can't return 2 constructs
        >>> f.construct(re.compile('^l'), default='no unique construct')
        'no unique construct'

        """
        return self._filter_interface(
            (),
            "construct",
            identity,
            construct=True,
            key=True,
            item=False,
            default=default,
            **filter_kwargs,
        )

    def domain_axis_key(
        self, *identity, default=ValueError(), **filter_kwargs
    ):
        """Returns the domain axis key spanned by 1-d coordinates.

        Specifically, returns the key of the domain axis construct that
        is spanned by 1-d coordinate constructs.

        :Parameters:

            identity: optional
                Select the 1-d dimension coordinate constructs that
                have an identity, defined by their `!identities`
                methods, that matches any of the given values.

                If no values are provided then all 1-d dimension
                coordinate constructs are selected.

                {{value match}}

                {{displayed identity}}

            default: optional
                Return the value of the *default* parameter if there
                is no unique construct.

                {{default Exception}}

            {{filter_kwargs: optional}}

                .. versionadded:: (cfdm) 1.8.9.0

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
        filter_kwargs["filter_by_naxes"] = (1,)
        filter_kwargs["todict"] = True

        # Select 1-d coordinate constructs with the given identity
        c = self.coordinates(*identity, **filter_kwargs)
        if not c:
            if default is None:
                return default

            return self._default(
                default,
                "There are no 1-d coordinate constructs",
            )

        data_axes = self.constructs.data_axes()
        domain_axes = self.domain_axes(todict=True)

        keys = []
        for ckey, coord in c.items():
            axes = data_axes.get(ckey)
            if axes is None:
                continue

            key = axes[0]
            if key in domain_axes:
                keys.append(key)

        keys = set(keys)

        if len(keys) == 1:
            return keys.pop()

        if default is None:
            return default

        if not keys:
            return self._default(
                default,
                "Some selected 1-d coordinate constructs "
                "have not been assigned a domain axis construct",
            )

        return self._default(
            default,
            "The selected 1-d coordinate constructs "
            f"span multiple domain axes: {keys!r}",
        )

    @_manage_log_level_via_verbosity
    def equals(
        self,
        other,
        rtol=None,
        atol=None,
        verbose=None,
        ignore_data_type=False,
        ignore_fill_value=False,
        ignore_properties=(),
        ignore_compression=True,
        ignore_type=False,
    ):
        """Whether two constructs are the same.

        Equality is strict by default. This means that for two
        constructs to be considered equal they must have corresponding
        metadata constructs and for each pair of constructs:

        * the same descriptive properties must be present, with the
          same values and data types, and vector-valued properties
          must also have same the size and be element-wise equal (see
          the *ignore_properties* and *ignore_data_type* parameters),
          and

        ..

        * if there are data arrays then they must have same shape and
          data type, the same missing data mask, and be element-wise
          equal (see the *ignore_data_type* parameter).

        {{equals tolerance}}

        {{equals compression}}

        Any type of object may be tested but, in general, equality is
        only possible with another field construct, or a subclass of
        one. See the *ignore_type* parameter.

        {{equals netCDF}}

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            other:
                The object to compare for equality.

            {{atol: number, optional}}

            {{rtol: number, optional}}

            {{ignore_fill_value: `bool`, optional}}

            ignore_properties: sequence of `str`, optional
                The names of properties of the construct (not the
                metadata constructs) to omit from the comparison. Note
                that the ``Conventions`` property is always omitted.

            {{ignore_data_type: `bool`, optional}}

            {{ignore_compression: `bool`, optional}}

            {{ignore_type: `bool`, optional}}

            {{verbose: `int` or `str` or `None`, optional}}

        :Returns:

            `bool`
                Whether the two constructs are equal.

        **Examples:**

        >>> f.equals(f)
        True
        >>> f.equals(f.copy())
        True
        >>> f.equals(f[...])
        True
        >>> f.equals('a string, not a construct')
        False

        >>> g = f.copy()
        >>> g.set_property('foo', 'bar')
        >>> f.equals(g)
        False
        >>> f.equals(g, verbose=3)
        {{class}}: Non-common property name: foo
        {{class}}: Different properties
        False

        """
        # Check the properties and data
        ignore_properties = tuple(ignore_properties) + ("Conventions",)

        if not super().equals(
            other,
            rtol=rtol,
            atol=atol,
            verbose=verbose,
            ignore_data_type=ignore_data_type,
            ignore_fill_value=ignore_fill_value,
            ignore_properties=ignore_properties,
            ignore_compression=ignore_compression,
            ignore_type=ignore_type,
        ):
            return False

        # Check the constructs
        if not self.constructs.equals(
            other.constructs,
            rtol=rtol,
            atol=atol,
            verbose=verbose,
            ignore_data_type=ignore_data_type,
            ignore_fill_value=ignore_fill_value,
            ignore_compression=ignore_compression,
            _ignore_type=False,
        ):
            logger.info(
                f"{self.__class__.__name__}: Different metadata constructs"
            )
            return False
        #        if not self._equals(
        #            self.constructs,
        #            other.constructs,
        #            rtol=rtol,
        #            atol=atol,
        #            verbose=verbose,
        #            ignore_data_type=ignore_data_type,
        #            ignore_fill_value=ignore_fill_value,
        #            ignore_compression=ignore_compression,
        #            _ignore_type=False,
        #        ):
        #            logger.info(
        #                f"{self.__class__.__name__}: Different metadata constructs"
        #            )
        #            return False

        return True

    def has_construct(self, *identity, **filter_kwargs):
        """Whether a unique metadata construct exists.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `get_construct`, `constructs`, `has_construct`,
                     `set_construct`

        :Parameters:

            identity:
                Select the unique construct that has the identity,
                defined by its `!identities` method, that matches the
                given values.

                Additionally, the values are matched against construct
                identifiers, with or without the ``'key%'`` prefix.

                {{value match}}

                {{displayed identity}}

                .. versionadded:: (cfdm) 1.8.9.0

            {{filter_kwargs: optional}}

                .. versionadded:: (cfdm) 1.8.9.0

        :Returns:

                Whether or not a unique construct can be identified.

        **Examples:**

        >>> f = {{package}}.example_field(0)
        >>> print(f)
        Field: specific_humidity (ncvar%q)
        ----------------------------------
        Data            : specific_humidity(latitude(5), longitude(8)) 1
        Cell methods    : area: mean
        Dimension coords: latitude(5) = [-75.0, ..., 75.0] degrees_north
                        : longitude(8) = [22.5, ..., 337.5] degrees_east
                        : time(1) = [2019-01-01 00:00:00]
        >>> f.has_construct('time')
        True
        >>> f.del_construct('altitude')
        False

        """
        return bool(
            self.construct(*identity, default=None, **filter_kwargs)
            is not None
        )

    def has_geometry(self):
        """Return whether or not any coordinates have cell geometries.

        .. versionadded:: (cfdm) 1.8.0

        :Returns:

            `bool`
                True if there are geometries, otherwise False.

        **Examples:**

        >>> f = {{package}}.{{class}}()
        >>> f.has_geometry()
        False

        """
        for c in self.constructs.filter_by_type(
            "auxiliary_coordinate",
            "dimension_coordinate",
            "domain_ancillary",
            todict=True,
        ).values():
            if c.has_geometry():
                return True

        return False
