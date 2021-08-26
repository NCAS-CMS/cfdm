from . import abstract


class Constructs(abstract.Container):
    """A container for metadata constructs.

    The following metadata constructs can be included:

    * auxiliary coordinate constructs
    * coordinate reference constructs
    * cell measure constructs
    * dimension coordinate constructs
    * domain ancillary constructs
    * domain axis constructs
    * cell method constructs
    * field ancillary constructs

    The container is used by used by `Field` and `Domain` instances.

    The container is like a dictionary in many ways, in that it stores
    key/value pairs where the key is the unique construct key with
    corresponding metadata construct value, and provides some of the
    usual dictionary methods.

    .. versionadded:: (cfdm) 1.7.0

    """

    def __init__(
        self,
        auxiliary_coordinate=None,
        dimension_coordinate=None,
        domain_ancillary=None,
        field_ancillary=None,
        cell_measure=None,
        coordinate_reference=None,
        domain_axis=None,
        cell_method=None,
        source=None,
        copy=True,
        _use_data=True,
        _view=False,
        _ignore=(),
    ):
        """**Initialisation**

        :Parameters:

            auxiliary_coordinate: `str`, optional
                The base name for keys of auxiliary coordinate
                constructs.

                *Parameter example:*
                  ``auxiliary_coordinate='auxiliarycoordinate'``

            dimension_coordinate: `str`, optional
                The base name for keys of dimension coordinate
                constructs.

                *Parameter example:*
                  ``dimension_coordinate='dimensioncoordinate'``

            domain_ancillary: `str`, optional
                The base name for keys of domain ancillary constructs.

                *Parameter example:*
                  ``domain_ancillary='domainancillary'``

            field_ancillary: `str`, optional
                The base name for keys of field ancillary constructs.

                *Parameter example:*
                  ``field_ancillary='fieldancillary'``

            cell_measure: `str`, optional
                The base name for keys of cell measure constructs.

                *Parameter example:*
                  ``cell_measure='cellmeasure'``

            coordinate_reference: `str`, optional
                The base name for keys of coordinate reference
                constructs.

                *Parameter example:*
                  ``coordinate_reference='coordinatereference'``

            domain_axis: `str`, optional
                The base name for keys of domain axis constructs.

                *Parameter example:*
                  ``domain_axis='domainaxis'``

            cell_method: `str`, optional
                The base name for keys of cell method constructs.

                *Parameter example:*
                  ``cell_method='cellmethod'``

            source: optional
                Initialise the construct keys and contained metadata
                constructs from those of *source*.

            copy: `bool`, optional
                If False then do not deep copy metadata constructs
                from those of *source* prior to initialisation. By
                default such metadata constructs are deep copied.

            _ignore: sequence of `str`, optional
                Ignores the given construct types.

                *Parameter example:*
                  ``_ignore=('cell_method', 'field_ancillary')``

        """
        _ignore = tuple(_ignore)

        if source is not None:

            if _view:
                self.__dict__ = source.__dict__.copy()
                self._ignore = _ignore
                return

            source_constructs = source._constructs

            self._field_data_axes = source._field_data_axes

            self._key_base = source._key_base.copy()
            self._array_constructs = source._array_constructs.copy()
            self._non_array_constructs = source._non_array_constructs.copy()
            self._construct_axes = source._construct_axes.copy()
            self._construct_type = source._construct_type.copy()

            self_construct_axes = self._construct_axes
            self_construct_type = self._construct_type

            d = {}
            for construct_type in source._array_constructs:
                if construct_type in _ignore:
                    for cid in source_constructs.get(construct_type, ()):
                        self_construct_axes.pop(cid, None)
                        self_construct_type.pop(cid, None)

                    continue

                if construct_type not in source_constructs:
                    continue

                if copy:
                    new_v = {}
                    for cid, construct in source_constructs[
                        construct_type
                    ].items():
                        new_v[cid] = construct.copy(data=_use_data)
                else:
                    new_v = source_constructs[construct_type].copy()

                d[construct_type] = new_v

            for construct_type in source._non_array_constructs:
                if construct_type in _ignore:
                    for cid in source_constructs.get(construct_type, ()):
                        self_construct_type.pop(cid, None)

                    continue

                if construct_type not in source_constructs:
                    continue

                if copy:
                    new_v = {}
                    for cid, construct in source_constructs[
                        construct_type
                    ].items():
                        new_v[cid] = construct.copy()
                else:
                    new_v = source_constructs[construct_type].copy()

                d[construct_type] = new_v

            self._constructs = d

            self._ignore = ()

            return

        self._ignore = _ignore

        self._field_data_axes = None

        self._key_base = {}

        self._array_constructs = set()
        self._non_array_constructs = set()

        self._construct_axes = {}

        # The construct type for each key. For example:
        # {'domainaxis1':'domain_axis',
        #  'auxiliarycoordinate3':'auxiliary_coordinate'}
        self._construct_type = {}

        self._constructs = {}

        if auxiliary_coordinate:
            self._key_base["auxiliary_coordinate"] = auxiliary_coordinate
            self._array_constructs.add("auxiliary_coordinate")

        if dimension_coordinate:
            self._key_base["dimension_coordinate"] = dimension_coordinate
            self._array_constructs.add("dimension_coordinate")

        if domain_ancillary:
            self._key_base["domain_ancillary"] = domain_ancillary
            self._array_constructs.add("domain_ancillary")

        if field_ancillary:
            self._key_base["field_ancillary"] = field_ancillary
            self._array_constructs.add("field_ancillary")

        if cell_measure:
            self._key_base["cell_measure"] = cell_measure
            self._array_constructs.add("cell_measure")

        if domain_axis:
            self._key_base["domain_axis"] = domain_axis
            self._non_array_constructs.add("domain_axis")

        if coordinate_reference:
            self._key_base["coordinate_reference"] = coordinate_reference
            self._non_array_constructs.add("coordinate_reference")

        if cell_method:
            self._key_base["cell_method"] = cell_method
            self._non_array_constructs.add("cell_method")

        for x in self._array_constructs:
            self._constructs[x] = {}

        for x in self._non_array_constructs:
            self._constructs[x] = {}

    def __contains__(self, key):
        """Implements membership test operators for construct keys.

        x.__contains__(y) <==> y in x

        .. versionadded:: (cfdm) 1.7.0

        """
        return self.construct_type(key) is not None

    def __copy__(self):
        """Called by the `copy.copy` standard library function.

        .. versionadded:: (cfdm) 1.7.0

        """
        return self.shallow_copy()

    def __deepcopy__(self, memo):
        """Called by the `copy.deepcopy` standard library function.

        .. versionadded:: (cfdm) 1.7.0

        """
        return self.copy()

    def __getitem__(self, key):
        """Return a construct with the given key.

        x.__getitem__(y) <==> x[y]

        .. versionadded:: (cfdm) 1.7.0

        """
        construct_type = self.construct_type(key)
        if construct_type is None:
            raise KeyError(key)

        return self._constructs[construct_type][key]

    def __iter__(self):
        """Called when an iterator is required.

        x.__iter__() <==> iter(x)

        .. versionadded:: (cfdm) 1.7.0

        """
        return iter(self.todict())

    def __len__(self):
        """Return the number of constructs.

        x.__len__() <==> len(x)

        .. versionadded:: (cfdm) 1.7.0

        """
        n = len(self._construct_type)
        ignore = self._ignore
        if ignore:
            constructs = self._constructs
            for ctype in ignore:
                n -= len(constructs[ctype])

        return n

    def _construct_dict(self, construct_type, copy=False):
        """Return the dictionary of constructs of a particular type.

        .. versionadded:: (cfdm) 1.8.9.0

        :Parameters:

            copy: `bool`, optional
                If True and some constructs exisit then the dictionary
                is a shallow copy of that stored in the `_constructs`
                attribute, otherwise it is the same dictionary.

        :Returns:

            `dict`
                The dictionary, keyed by construct identifiers with
                construct values.

        """
        if construct_type in self._ignore:
            return {}

        out = self._constructs.get(construct_type)
        if out is None:
            return {}

        if copy:
            out = out.copy()

        return out

    def _del_data_axes(self, k, *d):
        """Remove and return a construct's axes, if any.

        If k is not found, d is returned if given, otherwise KeyError is
        raised

        """
        return self._construct_axes.pop(k, *d)

    def _view(self, ignore=()):
        """Returns a new container with a view of the same constructs.

        A new `{{class}}` instance is returned that contains the same
        metadata construct instances

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            ignore: sequence of `str`, optional
                Return a view that ignores the given construct types.

                *Parameter example:*
                  ``ignore=('cell_method', 'field_ancillary')``

        :Returns:

            `{{class}}`
                The new constructs container.

        """
        return type(self)(source=self, _ignore=ignore, _view=True)

    def _check_construct_type(self, construct_type, default=ValueError()):
        """Check the type of a metadata construct is valid.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            construct_type: `str`
                The construct type to be checked.

            default: `bool`, optional
                Return the value of the *default* parameter if
                construct type is not valid.

                {{default Exception}}

        :Returns:

            `str` or `None`
                Return the type of of the construct, or if the input
                construct was given as `None`, `None` is returned.

        """
        if (
            construct_type not in self._ignore
            and construct_type in self._key_base
        ) or construct_type is None:
            return construct_type

        if default is None:
            return default

        return self._default(
            default, f"Invalid construct type {construct_type!r}"
        )

    def _construct_type_description(self, construct_type):
        """Format the description of the type of a metadata construct.

        Type name components are formatted to be whitespace-delimited to
        effective words for the purposes of printing to the user.

        """
        return construct_type.replace("_", " ")

    def _del_construct(self, key, default=ValueError()):
        """Remove a metadata construct.

        If a domain axis construct is selected for removal then it
        can't be spanned by any metadata construct data arrays, nor be
        referenced by any cell method constructs.

        However, a domain ancillary construct may be removed even if
        it is referenced by coordinate reference construct. In this
        case the reference is replace with `None`.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `_get_construct`, `_set_construct`

        :Parameters:

            key: `str`
                The key of the construct to be removed.

                *Parameter example:*
                  ``key='auxiliarycoordinate0'``

            default: optional
                Return the value of the *default* parameter if the
                construct can not be removed, or does not exist.

                {{default Exception}}

        :Returns:

                The removed construct.

        **Examples:**

        >>> f = {{package}}.example_field(3)
        >>> c = f.constructs
        >>> x = c._del_construct('auxiliarycoordinate2')

        """
        data_axes = self.data_axes()

        domain_axes = self._construct_dict("domain_axis")

        if key in domain_axes:
            # Fail if the domain axis construct is spanned by a data
            # array
            for xid, axes in data_axes.items():
                if key in axes:
                    if default is None:
                        return default

                    raise ValueError(
                        f"Can't remove domain axis construct {key!r} that "
                        f"spans the data array of metadata construct {xid!r}"
                    )

            cell_methods = self._construct_dict("cell_method")
            for xid, cm in cell_methods.items():
                if key in cm.get_axes(()):
                    if default is None:
                        return default

                    raise ValueError(
                        f"Can't remove domain axis construct {key!r} "
                        "that is referenced by cell method construct "
                        f"{xid!r}"
                    )
        else:
            # Remove references to the removed construct in coordinate
            # reference constructs
            coordinate_references = self._construct_dict(
                "coordinate_reference"
            )
            for ref in coordinate_references.values():
                coordinate_conversion = ref.coordinate_conversion
                for (
                    term,
                    value,
                ) in coordinate_conversion.domain_ancillaries().items():
                    if key == value:
                        coordinate_conversion.set_domain_ancillary(term, None)

                ref.del_coordinate(key, None)

        out = self._pop(key, None)

        if out is None:
            if default is None:
                return default

            return self._default(
                default, f"Can't remove non-existent construct {key!r}"
            )

        return out

    def _dictionary(self, copy=False):
        """Deprecated at 1.8.9.0.

        Use `todict` instead.

        """
        return self.todict()  # pragma: no cover

    def _set_construct(self, construct, key=None, axes=None, copy=True):
        """Set a metadata construct.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `_del_construct`, `_get_construct`,
                     `_set_construct_data_axes`

        :Parameters:

            construct:
                The metadata construct to be inserted.

            key: `str`, optional
                The construct identifier to be used for the
                construct. If not set then a new, unique identifier is
                created automatically. If the identifier already
                exists then the existing construct will be replaced.

                *Parameter example:*
                  ``key='cellmeasure0'``

            axes: (sequence of) `str`, optional
                The construct identifiers of the domain axis
                constructs spanned by the data array. An exception is
                raised if used for a metadata construct that can not
                have a data array, i.e. domain axis, cell method and
                coordinate reference constructs.

                The axes may also be set afterwards with the
                `_set_construct_data_axes` method.

                *Parameter example:*
                  ``axes='domainaxis1'``

                *Parameter example:*
                  ``axes=['domainaxis1']``

                *Parameter example:*
                  ``axes=('domainaxis1', 'domainaxis0')``

            copy: `bool`, optional
                If True then return a copy of the unique selected
                construct. By default the construct is copied.

        :Returns:

             `str`
                The construct identifier for the construct.

        **Examples:**

        >>> f = {{package}}.example_field(3)
        >>> c = f.constructs
        >>> c
        <{{repr}}Constructs: auxiliary_coordinate(6), domain_axis(2)>
        >>> d = {{package}}.DomainAxis(10)
        >>> key1 = c._set_construct(d, copy=False)
        >>> key1
        'domainaxis2'
        >>> print(c.filter_by_type('domain_axis'))
        Constructs:
        {'domainaxis0': <{{repr}}DomainAxis: size(4)>,
         'domainaxis1': <{{repr}}DomainAxis: size(9)>,
         'domainaxis2': <{{repr}}DomainAxis: size(10)>}

        >>> a = {{package}}.CellMeasure(measure='area', properties={'units': 'm2'})
        >>> key2 = c._set_construct(a, key='my_area_cell_measure')
        >>> key2
        'my_area_cell_measure'
        >>> v = {{package}}.CellMeasure(measure='volume', properties={'units': 'm3'})
        >>> key3 = c._set_construct(
        ...     v, key='my_volume_cell_measure', axes='domainaxis2')
        >>> key3
        'my_volume_cell_measure'
        >>> c
        <{{repr}}Constructs: auxiliary_coordinate(6), cell_measure(2), domain_axis(3)>
        >>> print(c.filter_by_type('cell_measure'))
        Constructs:
        {'my_area_cell_measure': <{{repr}}CellMeasure: measure:area m2>,
         'my_volume_cell_measure': <{{repr}}CellMeasure: measure:volume m3>}

        """
        construct_type = self._check_construct_type(construct.construct_type)

        if key is None:
            # Create a new construct identifier
            key = self.new_identifier(construct_type)

        if construct_type in self._array_constructs:
            # ---------------------------------------------------------
            # The construct could have a data array
            # ---------------------------------------------------------
            if axes is not None:
                self._set_construct_data_axes(
                    key=key, axes=axes, construct=construct
                )
        elif axes is not None:
            raise ValueError(
                f"Can't set {construct!r}: Can't provide domain axis "
                "constructs for "
                f"{self._construct_type_description(construct_type)} "
                "construct"
            )

        # Record the construct type
        self._construct_type[key] = construct_type

        if copy:
            # Create a deep copy of the construct
            construct = construct.copy()

        # Insert the construct
        self._constructs[construct_type][key] = construct

        # Return the identifier of the construct
        return key

    def _set_construct_data_axes(self, key, axes, construct=None):
        """Set domain axis constructs for construct identifiers.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            key: `str`, optional
                The construct identifier of metadata construct.

                *Parameter example:*
                  ``key='cellmeasure0'``

            axes: (sequence of) `str`
                The construct identifiers of the domain axis
                constructs spanned by the data array. An exception is
                raised if used for a metadata construct that can not
                have a data array, such as a domain axis construct.

                *Parameter example:*
                  ``axes='domainaxis1'``

                *Parameter example:*
                  ``axes=['domainaxis1']``

                *Parameter example:*
                  ``axes=['domainaxis1', 'domainaxis0']``

        :Returns:

            `None`

        **Examples:**

        >>> f = {{package}}.example_field(3)
        >>> c = f.constructs
        >>> c
        <{{repr}}Constructs: auxiliary_coordinate(6), domain_axis(2)>
        >>> a = {{package}}.CellMeasure(measure='area', properties={'units': 'm2'})
        >>> area_measure_key = c.set_construct(a)
        >>> f._set_construct_data_axes(area_measure_key, axes='domainaxis0')

        """
        if construct is None:
            if self.construct_type(key) is None:
                raise ValueError(
                    "Can't set axes for non-existent construct "
                    f"identifier {key!r}"
                )

            construct = self[key]

        if isinstance(axes, str):
            axes = (axes,)

        domain_axes = self._construct_dict("domain_axis")

        axes_shape = []
        for axis in axes:
            if axis not in domain_axes:
                raise ValueError(
                    f"Can't set {construct!r} domain axes: "
                    f"Domain axis {axis!r} does not exist"
                )

            axes_shape.append(domain_axes[axis].get_size())

        axes_shape = tuple(axes_shape)

        extra_axes = 0
        data = construct.get_data(None)
        if (
            data is not None
            and data.shape[: data.ndim - extra_axes] != axes_shape
        ):
            raise ValueError(
                f"Can't set {construct!r}: Data shape of {data.shape!r} "
                "does not match the shape required by domain axes "
                f"{tuple(axes)}: {axes_shape}"
            )

        try:
            bounds = construct.get_bounds(None)
        except AttributeError:
            pass
        else:
            if bounds is not None:
                data = bounds.get_data(None)
                if (
                    data is not None
                    and data.shape[: len(axes_shape)] != axes_shape
                ):
                    raise ValueError(
                        f"Can't set {construct!r}: Bounds data shape of "
                        f"{data.shape!r} does "
                        "not match the shape required by domain axes "
                        f"{tuple(axes)}: {axes_shape}"
                    )

        self._construct_axes[key] = tuple(axes)

    # ----------------------------------------------------------------
    # Private dictionary-like methods
    # ----------------------------------------------------------------
    def _clear(self):
        """D.clear() -> None.

        Remove all items from D.

        """
        self._ignore = ()
        self._key_base.clear()
        self._array_constructs.clear()
        self._non_array_constructs.clear()
        self._construct_axes.clear()
        self._construct_type.clear()
        self._constructs.clear()

    def _pop(self, k, *d):
        """Removes specified key and returns the corresponding value.

        D.pop(k[,d]) -> v, remove specified key and return the
        corresponding value. If key is not found, d is returned if
        given, otherwise KeyError is raised.

        """
        construct_type = self.construct_type(k)
        if construct_type is not None:
            self._del_data_axes(k, None)
            del self._construct_type[k]
            return self._constructs[construct_type].pop(k)

        if d:
            return d[0]

        raise KeyError(k)

    def _update(self, other):
        """D.update(E) -> None.

        Update D from E.

        """
        self._ignore = tuple(set(self._ignore).union(other._ignore))

        self._key_base.update(other._key_base)
        self._array_constructs.update(other._array_constructs)
        self._non_array_constructs.update(other._non_array_constructs)
        self._construct_axes.update(other._construct_axes)
        self._construct_type.update(other._construct_type)
        self._constructs.update(other._constructs)

    # ----------------------------------------------------------------
    # Dictionary-like methods
    # ----------------------------------------------------------------
    def get(self, key, default=None):
        """Returns the construct for the key, else default.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `items`, `keys`, `values`

        """
        construct_type = self.construct_type(key)
        if construct_type is not None:
            return self._constructs[construct_type][key]

        return default

    def items(self):  # SB NOTE: flaky doctest due to dict_items order
        """Return the items as (construct key, construct) pairs.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `get`, `keys`, `values`

        :Returns:

            `dict_items`
                The construct key and constructs respectively as
                key-value pairs in a Python `dict_items` iterator.

        **Examples:**

        >>> f = {{package}}.example_field(0)
        >>> c = f.constructs
        >>> c_items = c.items()
        >>> print(c_items)
        dict_items([('dimensioncoordinate0', <{{repr}}DimensionCoordinate: latitude(5) degrees_north>),
                    ('dimensioncoordinate1', <{{repr}}DimensionCoordinate: longitude(8) degrees_east>),
                    ('dimensioncoordinate2', <{{repr}}DimensionCoordinate: time(1) days since 2018-12-01 >),
                    ('domainaxis0', <{{repr}}DomainAxis: size(5)>),
                    ('domainaxis1', <{{repr}}DomainAxis: size(8)>),
                    ('domainaxis2', <{{repr}}DomainAxis: size(1)>),
                    ('cellmethod0', <{{repr}}CellMethod: area: mean>)])
        >>> type(c_items)
        <class 'dict_items'>
        >>> dict(c_items)
        {'dimensioncoordinate0': <{{repr}}DimensionCoordinate: latitude(5) degrees_north>,
         'dimensioncoordinate1': <{{repr}}DimensionCoordinate: longitude(8) degrees_east>,
         'dimensioncoordinate2': <{{repr}}DimensionCoordinate: time(1) days since 2018-12-01 >,
         'cellmethod0': <{{repr}}CellMethod: area: mean>,
         'domainaxis0': <{{repr}}DomainAxis: size(5)>,
         'domainaxis1': <{{repr}}DomainAxis: size(8)>,
         'domainaxis2': <{{repr}}DomainAxis: size(1)>}

        """
        return self.todict().items()

    def keys(self):  # SB NOTE: flaky doctest due to dict_items order
        """Return all of the construct keys, in arbitrary order.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `get`, `items`, `values`

        :Returns:

            `dict_keys`
                The construct keys as a Python `dict_keys` iterator.

        **Examples:**

        >>> f = {{package}}.example_field(0)
        >>> c = f.constructs
        >>> c_keys = c.keys()
        >>> print(c_keys)
        dict_keys(['domainaxis0',
                   'domainaxis1',
                   'domainaxis2',
                   'dimensioncoordinate0',
                   'dimensioncoordinate1',
                   'dimensioncoordinate2',
                   'cellmethod0'])
        >>> type(c_keys)
        <class 'dict_keys'>
        >>> list(c_keys)
        ['domainaxis0',
         'domainaxis1',
         'domainaxis2',
         'dimensioncoordinate0',
         'dimensioncoordinate1',
         'dimensioncoordinate2',
         'cellmethod0']

        """
        return self.todict().keys()

    def values(self):  # SB NOTE: flaky doctest due to dict_items order
        """Return all of the metadata constructs, in arbitrary order.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `get`, `items`, `keys`

        :Returns:

            `dict_values`
                The constructs as a Python `dict_values` iterator.

        **Examples:**

        >>> f = {{package}}.example_field(0)
        >>> c = f.constructs
        >>> c_values = c.values()
        >>> print(c_values)
        dict_values([<{{repr}}DimensionCoordinate: latitude(5) degrees_north>,
                     <{{repr}}DimensionCoordinate: longitude(8) degrees_east>,
                     <{{repr}}DimensionCoordinate: time(1) days since 2018-12-01 >,
                     <{{repr}}DomainAxis: size(5)>,
                     <{{repr}}DomainAxis: size(8)>,
                     <{{repr}}DomainAxis: size(1)>,
                     <{{repr}}CellMethod: area: mean>])
        >>> type(c_values)
        <class 'dict_values'>
        >>> list(c_values)
        [<{{repr}}DimensionCoordinate: latitude(5) degrees_north>,
         <{{repr}}DimensionCoordinate: longitude(8) degrees_east>,
         <{{repr}}DimensionCoordinate: time(1) days since 2018-12-01 >,
         <{{repr}}DomainAxis: size(5)>,
         <{{repr}}DomainAxis: size(8)>,
         <{{repr}}DomainAxis: size(1)>,
         <{{repr}}CellMethod: area: mean>]

        """
        return self.todict().values()

    def construct_type(self, key):
        """Return the type of a construct for a given key.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `construct_types`

        :Parameters:

            key: `str`
                A construct identifier.

        :Returns:

            `str` or `None`
                The construct type, or `None` if the *key* is not
                present.

        """
        ctype = self._construct_type.get(key)
        if ctype is not None and ctype in self._ignore:
            return

        return ctype

    def construct_types(self):
        """Return all of the construct types for all keys.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `construct_type`

        """
        out = self._construct_type.copy()

        ignore = self._ignore
        if ignore:
            for key, ctype in self._construct_type.items():
                if ctype in ignore:
                    del out[key]

        return out

    def copy(self, data=True):
        """Return a deep copy.

        ``f.copy()`` is equivalent to ``copy.deepcopy(f)``.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            data: `bool`, optional
                If False then do not copy data contained in the
                metadata constructs. By default such data are copied.

        :Returns:

            `{{class}}`
                The deep copy.

        **Examples:**

        >>> f = {{package}}.example_field(0)
        >>> c = f.constructs
        >>> k = c.copy()
        >>> k = c.copy(data=False)

        """
        return type(self)(
            source=self,
            copy=True,
            _ignore=self._ignore,
            _view=False,
            _use_data=data,
        )

    def data_axes(self):
        """Returns the axes spanned by the data.

        Specifically, returns the domain axis constructs spanned by
        metadata construct data.

        .. versionadded:: (cfdm) 1.7.0

        :Returns:

            `dict`
                The keys of the domain axes constructs spanned by
                metadata construct data.

        **Examples:**

        >>> f = {{package}}.example_field(0)
        >>> c = f.constructs
        >>> print(c)
        Constructs:
        {'cellmethod0': <{{repr}}CellMethod: area: mean>,
         'dimensioncoordinate0': <{{repr}}DimensionCoordinate: latitude(5) degrees_north>,
         'dimensioncoordinate1': <{{repr}}DimensionCoordinate: longitude(8) degrees_east>,
         'dimensioncoordinate2': <{{repr}}DimensionCoordinate: time(1) days since 2018-12-01 >,
         'domainaxis0': <{{repr}}DomainAxis: size(5)>,
         'domainaxis1': <{{repr}}DomainAxis: size(8)>,
         'domainaxis2': <{{repr}}DomainAxis: size(1)>}
        >>> c.data_axes()
        {'dimensioncoordinate0': ('domainaxis0',),
         'dimensioncoordinate1': ('domainaxis1',),
         'dimensioncoordinate2': ('domainaxis2',)}

        """
        out = self._construct_axes.copy()

        ignore = self._ignore
        if not ignore:
            return out

        non_data_constructs = self._non_array_constructs
        for construct_type, keys in self._constructs.items():
            if construct_type in non_data_constructs:
                continue

            if construct_type in ignore:
                for key in keys:
                    out.pop(key, None)

        return out

    def filter_by_type(self, *types, todict=True, cached=None):
        """Select metadata constructs by type.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            types: optional
                Select constructs that have are of any of the given
                types.

                A type is specified by one of the following strings:

                ==========================  ==========================
                *type*                      Construct selected
                ==========================  ==========================
                ``'domain_ancillary'``      Domain ancillary
                ``'dimension_coordinate'``  Dimension coordinate
                ``'domain_axis'``           Domain axis
                ``'auxiliary_coordinate'``  Auxiliary coordinate
                ``'cell_measure'``          Cell measure
                ``'coordinate_reference'``  Coordinate reference
                ``'cell_method'``           Cell method
                ``'field_ancillary'``       Field ancillary
                ==========================  ==========================

                If no types are provided then all constructs are
                selected.

        :Parameters:

            {{todict: `bool`, optional}}

            {{cached: optional}}

        :Returns:

            `{{class}}` or `dict`
                The selected constructs and their construct keys.

        **Examples:**

        Select dimension coordinate constructs:

        >>> f = {{package}}.example_field(1)
        >>> c = f.constructs
        >>> d = c.filter_by_type('dimension_coordinate')
        >>> d
        <{{repr}}Constructs: dimension_coordinate(4)>

        Select dimension coordinate and field ancillary constructs:

        >>> k = c.filter_by_type(
        ...     'dimension_coordinate', 'field_ancillary')
        >>> k
        <{{repr}}Constructs: dimension_coordinate(4), field_ancillary(1)>

        """
        if cached is not None:
            return cached

        if todict:
            # Return a dictionary
            if not types:
                return self.todict()

            out = self._construct_dict(types[0], copy=True)

            if len(types) > 1:
                ignore = self._ignore
                constructs = self._constructs
                for t in types[1:]:
                    if t in constructs and t not in ignore:
                        out.update(constructs[t])

            return out

        # Still here? Then return a `Constructs` object
        if types:
            # Ignore the all but the requested construct types
            ignore = set(self._key_base)
            ignore.difference_update(types)
            ignore.update(self._ignore)
        else:
            # Keep all construct types
            ignore = self._ignore

        return self.shallow_copy(_ignore=ignore)

    def get_data_axes(self, key, default=ValueError()):
        """Return the keys of the axes spanned by a construct's data.

        Specifically, returns the keys of the domain axis constructs
        spanned by the data of a metadata construct.

        .. versionadded:: (cfdm) 1.8.9.0

        :Parameters:

            key: `str`
                Specify a metadata construct.

                *Parameter example:*
                  ``key='auxiliarycoordinate0'``

            default: optional
                Return the value of the *default* parameter if the data
                axes have not been set.

                {{default Exception}}

        :Returns:

            `tuple`
                The keys of the domain axis constructs spanned by the data.

        """
        data_axes = self._construct_axes.get(key)
        if data_axes is not None:
            ignore = self._ignore
            if not ignore or self._construct_type[key] not in ignore:
                return data_axes

        if default is None:
            return default

        return self._default(default, f"No data axes for construct {key!r}")

    def key(self, default=ValueError()):
        """Return the construct key of the sole metadata construct.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `get`, `keys`, `value`

        :Parameters:

            default: optional
                Return the value of the *default* parameter if there
                is not exactly one construct.

                {{default Exception}}

        :Returns:

            `str`
                The construct key.

        **Examples:**

        >>> f = {{package}}.Field()
        >>> c = f.constructs
        >>> d = {{package}}.DimensionCoordinate(
        ...     properties={
        ...         'standard_name': 'latitude', 'units': 'degrees_north'},
        ...     data={{package}}.Data(range(5))
        ... )
        >>> c._set_construct(d)
        'dimensioncoordinate0'
        >>> print(c)
        Constructs:
        {'dimensioncoordinate0': <{{repr}}DimensionCoordinate: latitude(5) degrees_north>}
        >>> c.key()
        'dimensioncoordinate0'
        >>> c.value()
        <{{repr}}DimensionCoordinate: latitude(5) degrees_north>

        """
        d = self.todict()
        n = len(d)
        if n == 1:
            key, _ = d.popitem()
            return key

        if default is None:
            return default

        if not n:
            return self._default(default, "Can't get key for zero constructs")

        return self._default(
            default, f"Can't get key for more than one ({n}) constructs"
        )

    def new_identifier(self, construct_type):
        """Return a new, unused construct key.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            construct_type: `str`
                The construct type for which the identifier is being
                created.

                *Parameter example:*
                  ``construct_type='dimension_coordinate'``

        :Returns:

            `str`
                The new construct identifier.

        **Examples:**

        >>> f = {{package}}.example_field(0)
        >>> c = f.constructs
        >>> c.keys()
        ['domainaxis0',
         'domainaxis1',
         'domainaxis2',
         'dimensioncoordinate0',
         'dimensioncoordinate1',
         'dimensioncoordinate2',
         'cellmethod0']
        >>> c.new_identifier('domain_axis')
        'domainaxis3'
        >>> c.new_identifier('cell_method')
        'cellmethod1'

        """
        construct_type = self._check_construct_type(construct_type)

        keys = self._constructs[construct_type]

        n = len(keys)
        key_base = self._key_base[construct_type]
        key = f"{key_base}{n}"
        while key in keys:
            n += 1
            key = f"{key_base}{n}"

        return key

    def ordered(self):
        """Return the constructs in their predetermined order.

        For cell method constructs, the predetermined order is that in
        which they where added. There is no predetermined ordering for
        all other construct types, and a exception is raised if any
        non-cell method constructs are present.

        Deprecated at version (cfdm) 1.9.0.0, since all metadata
        constructs are now stored in the order in which they where
        added.

        .. versionadded:: (cfdm) 1.7.0

        :Returns:

             `collections.OrderedDict`
                 The constructs and their construct keys, in their
                 predetermined order.

        **Examples:**

        >>> f = {{package}}.Field()
        >>> c = f.constructs
        >>> c.ordered()
        {}
        >>> m1 = {{package}}.CellMethod(axes=['domainaxis1'], method='mean')
        >>> c._set_construct(m1, key='cell_method_for_axis_1')
        'cell_method_for_axis_1'
        >>> m2 = {{package}}.CellMethod(axes=['domainaxis0'], method='minimum')
        >>> c._set_construct(m2, key='cell_method_for_axis_0')
        'cell_method_for_axis_0'
        >>> print(c)
        Constructs:
        {'cell_method_for_axis_0': <{{repr}}CellMethod: domainaxis0: minimum>,
         'cell_method_for_axis_1': <{{repr}}CellMethod: domainaxis1: mean>}
        >>> c.ordered()
        OrderedDict([('cell_method_for_axis_1', <{{repr}}CellMethod: domainaxis1: mean>),
                     ('cell_method_for_axis_0', <{{repr}}CellMethod: domainaxis0: minimum>)])

        """
        raise DeprecationWarning(
            "This method is no longer required from v1.9.0.0, and"
            "will be removed at a later date"
        )

    def replace(self, key, construct, axes=None, copy=True):
        """Replace one metadata construct with another.

        .. note:: No checks on the axes are done.

        """
        construct_type = self.construct_types().get(key)
        if construct_type is None:
            raise ValueError(f"Can't replace non-existent construct {key!r}")

        if axes is not None and construct_type in self._array_constructs:
            self._construct_axes[key] = tuple(axes)

        if copy:
            construct = construct.copy()

        self._constructs[construct_type][key] = construct

    def shallow_copy(self, _ignore=None):
        """Return a shallow copy.

        ``copy.copy(f)`` is equivalent to ``f.shallow_copy()``.

        Any in-place changes to the actual constructs of the copy will
        not be seen in the original `{{class}}` object, and vice
        versa, but the copy and filter history are otherwise
        independent.

        .. versionadded:: (cfdm) 1.8.9.0

        .. seealso:: `view`

        :Returns:

            `{{class}}`
                The shallow copy.

        **Examples:**

        >>> f = {{package}}.example_field(0)
        >>> c = f.constructs
        >>> k = c.shallow_copy()

        """
        if _ignore is None:
            _ignore = self._ignore

        return type(self)(
            source=self, copy=False, _ignore=_ignore, _view=False
        )

    def todict(self, copy=False):
        """Return a dictionary of the metadata constructs.

        .. versionadded:: (cfdm) 1.8.9.0

        :Parameters:

            copy: `bool`, optional
                If True then deep copy the metadata construct values.

        :Returns:

            `dict`
                The dictionary representation, keyed by construct
                identifiers with metadata construct values.

        """
        out = {}
        ignore = self._ignore
        for key, value in self._constructs.items():
            if key not in ignore:
                out.update(value)

        if copy:
            for key, construct in out.items():
                out[key] = construct.copy()

        return out

    def value(self, default=ValueError()):
        """Return the sole metadata construct.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `get`, `key`, `values`

        :Parameters:

            default: optional
                Return the value of the *default* parameter if there
                is not exactly one construct.

                {{default Exception}}

        :Returns:

                The metadata construct.

        **Examples:**

        >>> f = {{package}}.Field()
        >>> c = f.constructs
        >>> d = {{package}}.DimensionCoordinate(
        ...     properties={
        ...         'standard_name': 'latitude', 'units': 'degrees_north'},
        ...     data={{package}}.Data(range(5))
        ... )
        >>> c._set_construct(d)
        'dimensioncoordinate0'
        >>> print(c)
        Constructs:
        {'dimensioncoordinate0': <{{repr}}DimensionCoordinate: latitude(5) degrees_north>}
        >>> c.key()
        'dimensioncoordinate0'
        >>> c.value()
        <{{repr}}DimensionCoordinate: latitude(5) degrees_north>

        """
        d = self.todict()
        n = len(d)
        if n == 1:
            _, construct = d.popitem()
            return construct

        if default is None:
            return default

        if not d:
            return self._default(default, "Can't return zero constructs")

        return self._default(
            default, f"Can't return more than one ({n}) constructs"
        )
