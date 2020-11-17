from collections import OrderedDict
from copy import copy

from . import abstract


class Constructs(abstract.Container):
    '''A container for metadata constructs.

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

    '''
    def __init__(self,
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
                 _ignore=()):
        '''**Initialization**

    :Parameters:

        auxiliary_coordinate: `str`, optional
            The base name for keys of auxiliary coordinate constructs.

            *Parameter example:*
              ``auxiliary_coordinate='auxiliarycoordinate'``

        dimension_coordinate: `str`, optional
            The base name for keys of dimension coordinate constructs.

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
            The base name for keys of coordinate reference constructs.

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
            Initialize the construct keys and contained metadata
            constructs from those of *source*.

        copy: `bool`, optional
            If False then do not deep copy metadata constructs from
            those of *source* prior to initialization. By default such
            metadata constructs are deep copied.

        _ignore: sequence of `str`, optional
            Ignores the given construct types.

            *Parameter example:*
              ``_ignore=('cell_method', 'field_ancillary')``

        '''
        self._ignore = tuple(set(_ignore))

        if source is not None:

            self._field_data_axes = source._field_data_axes

            if _view:
                self._key_base = source._key_base
                self._array_constructs = source._array_constructs
                self._non_array_constructs = source._non_array_constructs
                self._ordered_constructs = source._ordered_constructs
                self._construct_axes = source._construct_axes
                self._construct_type = source._construct_type
                self._constructs = source._constructs
                return

            self._key_base = source._key_base.copy()
            self._array_constructs = source._array_constructs.copy()
            self._non_array_constructs = source._non_array_constructs.copy()
            self._ordered_constructs = source._ordered_constructs.copy()
            self._construct_axes = source._construct_axes.copy()
            self._construct_type = source._construct_type.copy()
            self._constructs = source._constructs.copy()

            d = {}
            for construct_type in source._array_constructs:
                if construct_type in self._ignore:
                    for cid in source._constructs.get(construct_type, ()):
                        self._construct_axes.pop(cid, None)
                        self._construct_type.pop(cid, None)
                    # --- End: for

                    continue

                if construct_type not in source._constructs:
                    continue

                if copy:
                    if construct_type in source._ordered_constructs:
                        new_v = OrderedDict()
                    else:
                        new_v = {}

                    for cid, construct in (
                            source._constructs[construct_type].items()):
                        new_v[cid] = construct.copy(data=_use_data)
                else:
                    new_v = source._constructs[construct_type].copy()

                d[construct_type] = new_v
            # --- End: for

            for construct_type in source._non_array_constructs:
                if construct_type in self._ignore:
                    for cid in source._constructs.get(construct_type, ()):
                        self._construct_type.pop(cid, None)
                    continue

                if construct_type not in source._constructs:
                    continue

                if copy:
                    if construct_type in source._ordered_constructs:
                        new_v = OrderedDict()
                    else:
                        new_v = {}

                    for cid, construct in (
                            source._constructs[construct_type].items()):
                        new_v[cid] = construct.copy()
                else:
                    new_v = source._constructs[construct_type].copy()

                d[construct_type] = new_v
            # --- End: for

            self._constructs = d

            self._ignore = ()

            return
        # --- End: if

        self._field_data_axes = None

        self._key_base = {}

        self._array_constructs = set()
        self._non_array_constructs = set()
        self._ordered_constructs = set()

        self._construct_axes = {}

        # The construct type for each key. For example:
        # {'domainaxis1'         :'domain_axis',
        #  'auxiliarycoordinate3':'auxiliary_coordinate'}
        self._construct_type = {}

        self._constructs = {}

        if auxiliary_coordinate:
            self._key_base['auxiliary_coordinate'] = auxiliary_coordinate
            self._array_constructs.add('auxiliary_coordinate')

        if dimension_coordinate:
            self._key_base['dimension_coordinate'] = dimension_coordinate
            self._array_constructs.add('dimension_coordinate')

        if domain_ancillary:
            self._key_base['domain_ancillary'] = domain_ancillary
            self._array_constructs.add('domain_ancillary')

        if field_ancillary:
            self._key_base['field_ancillary'] = field_ancillary
            self._array_constructs.add('field_ancillary')

        if cell_measure:
            self._key_base['cell_measure'] = cell_measure
            self._array_constructs.add('cell_measure')

        if domain_axis:
            self._key_base['domain_axis'] = domain_axis
            self._non_array_constructs.add('domain_axis')

        if coordinate_reference:
            self._key_base['coordinate_reference'] = coordinate_reference
            self._non_array_constructs.add('coordinate_reference')

        if cell_method:
            self._key_base['cell_method'] = cell_method
            self._non_array_constructs.add('cell_method')
            self._ordered_constructs.add('cell_method')

        for x in self._array_constructs:
            self._constructs[x] = {}

        for x in self._non_array_constructs:
            self._constructs[x] = {}

        for x in self._ordered_constructs:
            self._constructs[x] = OrderedDict()

    def __contains__(self, key):
        '''Called to implement membership test operators for construct keys.

    x.__contains__(y) <==> y in x

    .. versionadded:: (cfdm) 1.7.0

        '''
        return key in self._construct_type

    def __copy__(self):
        '''Called by the `copy.copy` standard library function.

    .. versionadded:: (cfdm) 1.7.0

        '''
        return self.shallow_copy()

    def __deepcopy__(self, memo):
        '''Called by the `copy.deepcopy` standard library function.

    .. versionadded:: (cfdm) 1.7.0

        '''
        return self.copy()

    def __getitem__(self, key):
        '''Return a construct with the given key.

    x.__getitem__(y) <==> x[y]

    .. versionadded:: (cfdm) 1.7.0

        '''
        construct_type = self.construct_type(key)  # ignore??
        if construct_type is None:
            raise KeyError(key)

        d = self._constructs.get(construct_type)
        if d is None:
            d = {}

        return d[key]

    def __iter__(self):
        '''Called when an iterator is required.

    x.__iter__() <==> iter(x)

    .. versionadded:: (cfdm) 1.7.0

        '''
        return iter(self._dictionary().keys())

    def __len__(self):
        '''Return the number of constructs.

    x.__len__() <==> len(x)

    .. versionadded:: (cfdm) 1.7.0

        '''
        return len(self._dictionary())

    # ----------------------------------------------------------------
    # Private methods
    # ----------------------------------------------------------------
    def _del_data_axes(self, k, *d):
        '''Remove and return a construct's axes, if any.

    If k is not found, d is returned if given, otherwise KeyError is
    raised

        '''
        return self._construct_axes.pop(k, *d)

    def _view(self, ignore=()):
        '''Return a new container with a view the same metadata constructs.

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

        '''
        return type(self)(source=self, _ignore=ignore, _view=True)

    def _check_construct_type(self, construct_type, default=ValueError()):
        '''Check the type of a metadata construct is valid.

    .. versionadded:: (cfdm) 1.7.0

    :Parameters:

        construct_type: `str`
            The construct type to be checked.

        default: `bool`, optional
            Return the value of the *default* parameter if construct
            type is not valid.

            {{default Exception}}

    :Returns:

        `str` or `None`
            Return the type of of the construct, or if the input
            construct was given as `None`, `None` is returned.

        '''
        if construct_type is None:
            return None

        x = self._key_base
        if self._ignore:
            x = set(x).difference(self._ignore)

        if construct_type not in x:
            return self._default(
                default,
                "Invalid construct type {0!r}. Must be one of {1}".format(
                    construct_type, sorted(x)))

        return construct_type

    def _construct_type_description(self, construct_type):
        '''Format the description of the type of a metadata construct.

        Type name components are formatted to be whitespace-delimited to
        effective words for the purposes of printing to the user.
        '''
        return construct_type.replace('_', ' ')

    def _dictionary(self, copy=False):
        '''
        '''
        out = {}
        ignore = self._ignore
        for key, value in self._constructs.items():
            if key not in ignore:
                out.update(value)
        # --- End: if

        if copy:
            for key, construct in list(out.items()):
                out[key] = construct.copy()
        # --- End: if

        return out

    def _del_construct(self, key, default=ValueError()):
        '''Remove a metadata construct.

    If a domain axis construct is selected for removal then it can't
    be spanned by any metadata construct data arrays, nor be referenced
    by any cell method constructs.

    However, a domain ancillary construct may be removed even if it is
    referenced by coordinate reference construct. In this case the
    reference is replace with `None`.

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

    >>> x = f._del_construct('auxiliarycoordinate2')

        '''
        data_axes = self.data_axes()
        if key in self.filter_by_type('domain_axis'):
            # Fail if the domain axis construct is spanned by a data
            # array
            for xid, axes in data_axes.items():
                if key in axes:
                    raise ValueError(
                        "Can't remove domain axis construct {!r} that spans "
                        "the data array of metadata construct {!r}".format(
                            key, xid)
                    )

            # Fail if the domain axis construct is referenced by a
            # cell method construct
#            try:
#                cell_methods = self.filter_by_type('cell_method')
#            except ValueError:
#                # Cell methods are not possible for this Constructs
#                # instance
#                pass
#            else:
#                for xid, cm in cell_methods.items():
#                    axes = cm.get_axes(())
#                    if key in axes:
#                        raise ValueError(
#                            "Can't remove domain axis construct {!r} "
#                            "that is referenced by cell method construct "
#                            "{!r}".format(key, xid)
#                        )

            for xid, cm in self.filter_by_type('cell_method').items():
                axes = cm.get_axes(())
                if key in axes:
                    raise ValueError(
                        "Can't remove domain axis construct {!r} "
                        "that is referenced by cell method construct "
                        "{!r}".format(key, xid)
                    )
        else:
            # Remove references to the removed construct in coordinate
            # reference constructs
            for ref in self.filter_by_type('coordinate_reference').values():
                coordinate_conversion = ref.coordinate_conversion
                for term, value in (
                        coordinate_conversion.domain_ancillaries().items()):
                    if key == value:
                        coordinate_conversion.set_domain_ancillary(term, None)
                # --- End: for

                ref.del_coordinate(key, None)
        # --- End: if

        out = self._pop(key, None)

        if out is None:
            return self._default(
                default, "Can't get remove non-existent construct")

        return out

    def _set_construct(self, construct, key=None, axes=None,
                       copy=True):
        '''Set a metadata construct.

    .. versionadded:: (cfdm) 1.7.0

    .. seealso:: `_del_construct`, `_get_construct`,
                 `_set_construct_data_axes`

    :Parameters:

        construct:
            The metadata construct to be inserted.

        key: `str`, optional
            The construct identifier to be used for the construct. If
            not set then a new, unique identifier is created
            automatically. If the identifier already exists then the
            existing construct will be replaced.

            *Parameter example:*
              ``key='cellmeasure0'``

        axes: (sequence of) `str`, optional
            The construct identifiers of the domain axis constructs
            spanned by the data array. An exception is raised if used
            for a metadata construct that can not have a data array,
            i.e. domain axis, cell method and coordinate reference
            constructs.

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

    >>> key = f.set_construct(c)
    >>> key = f.set_construct(c, copy=False)
    >>> key = f.set_construct(c, axes='domainaxis2')
    >>> key = f.set_construct(c, key='cellmeasure0')

        '''
        construct_type = self._check_construct_type(construct.construct_type)

        if key is None:
            # Create a new construct identifier
            key = self.new_identifier(construct_type)

        if construct_type in self._array_constructs:
            # ---------------------------------------------------------
            # The construct could have a data array
            # ---------------------------------------------------------
            if axes is not None:
                self._set_construct_data_axes(key=key, axes=axes,
                                              construct=construct)
        elif axes is not None:
            raise ValueError(
                "Can't set {!r}: Can't provide domain axis constructs for "
                "{} construct".format(
                    construct,
                    self._construct_type_description(construct_type)
                )
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
        '''Set domain axis constructs for construct identifiers.

    .. versionadded:: (cfdm) 1.7.0

    :Parameters:

        key: `str`, optional
            The construct identifier of metadata construct.

            *Parameter example:*
              ``key='cellmeasure0'``

        axes: (sequence of) `str`
            The construct identifiers of the domain axis constructs
            spanned by the data array. An exception is raised if used
            for a metadata construct that can not have a data array,
            such as a domain axis construct.

            *Parameter example:*
              ``axes='domainaxis1'``

            *Parameter example:*
              ``axes=['domainaxis1']``

            *Parameter example:*
              ``axes=['domainaxis1', 'domainaxis0']``

    :Returns:

        `None`

    **Examples:**

    >>> key = f.set_construct(c)
    >>> f._set_construct_data_axes(key, axes='domainaxis1')

        '''
        if construct is None:
            if self.construct_type(key) is None:
                raise ValueError(
                    "Can't set axes for non-existent construct "
                    "identifier {!r}".format(key)
                )

            construct = self[key]

        if isinstance(axes, str):
            axes = (axes,)

        domain_axes = self.filter_by_type('domain_axis')

        axes_shape = []
        for axis in axes:
            if axis not in domain_axes:
                raise ValueError(
                    "Can't set {!r} domain axes: Domain axis {!r} does not "
                    "exist".format(construct, axis)
                )

            axes_shape.append(domain_axes[axis].get_size())

        axes_shape = tuple(axes_shape)

        extra_axes = 0
        data = construct.get_data(None)
        if (
                data is not None
                and data.shape[:data.ndim - extra_axes] != axes_shape
        ):
            raise ValueError(
                "Can't set {!r}: Data shape of {!r} does not match the "
                "shape required by domain axes {}: {}".format(
                    construct, data.shape, tuple(axes), axes_shape)
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
                        and data.shape[:len(axes_shape)] != axes_shape
                ):
                    raise ValueError(
                        "Can't set {!r}: Bounds data shape of {!r} does "
                        "not match the shape required by domain axes "
                        "{}: {}".format(
                            construct, data.shape, tuple(axes), axes_shape)
                    )
        # --- End: try

        self._construct_axes[key] = tuple(axes)

    # ----------------------------------------------------------------
    # Private dictionary-like methods
    # ----------------------------------------------------------------
    def _pop(self, k, *d):
        '''D.pop(k[,d]) -> v, remove specified key and return the
    corresponding value.

    If k is not found, d is returned if given, otherwise KeyError is
    raised

        '''
        # Remove the construct axes, if any
        self._del_data_axes(k, None)

        # Find the construct type
        try:
            construct_type = self._construct_type.pop(k)
        except KeyError as error:
            if d:
                return d[0]

            raise KeyError(error)

        # Remove and return the construct
        return self._constructs[construct_type].pop(k, *d)

    def _update(self, other):
        '''D.update(E) -> None. Update D from E.

        '''
        self._ignore = tuple(set(self._ignore).union(other._ignore))

        self._key_base.update(other._key_base)
        self._array_constructs.update(other._array_constructs)
        self._non_array_constructs.update(other._non_array_constructs)
        self._ordered_constructs.update(other._ordered_constructs)
        self._construct_axes.update(other._construct_axes)
        self._construct_type.update(other._construct_type)
        self._constructs.update(other._constructs)

    # ----------------------------------------------------------------
    # Dictionary-like methods
    # ----------------------------------------------------------------
    def get(self, key, *default):
        '''Return the construct for construct key, if it exists, else default.

    .. versionadded:: (cfdm) 1.7.0

    .. seealso:: `items`, `keys`, `values`

        '''
        return self._dictionary().get(key, *default)

    def items(self):
        '''Return the items as (construct key, construct) pairs.

    .. versionadded:: (cfdm) 1.7.0

    .. seealso:: `get`, `keys`, `values`

    :Returns:

        `dict_items`
            The construct key and constructs respectively as key-value pairs
            in a Python `dict_items` iterator.

    **Examples:**

    >>> c = {{package}}.example_field(0)
    >>> c_items = c.constructs.items()
    >>> print(c_items)
    dict_items([
         ('dimensioncoordinate0', <{{repr}}DimensionCoordinate: latitude(5) degrees_north>),
         ('dimensioncoordinate1', <{{repr}}DimensionCoordinate: longitude(8) degrees_east>),
         ('dimensioncoordinate2', <{{repr}}DimensionCoordinate: time(1) days since 2018-12-01 >),
         ('domainaxis0', <{{repr}}DomainAxis: size(5)>),
         ('domainaxis1', <{{repr}}DomainAxis: size(8)>),
         ('domainaxis2', <{{repr}}DomainAxis: size(1)>),
         ('cellmethod0', <{{repr}}CellMethod: area: mean>)
    ])
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

        '''
        return self._dictionary().items()

    def keys(self):
        '''Return all of the construct keys, in arbitrary order.

    .. versionadded:: (cfdm) 1.7.0

    .. seealso:: `get`, `items`, `values`

    :Returns:

        `dict_keys`
            The construct keys as a Python `dict_keys` iterator.

    **Examples:**

    >>> c = {{package}}.example_field(0)
    >>> c_keys = c.constructs.keys()
    >>> print(c_keys)
    dict_keys([
         'domainaxis0',
         'domainaxis1',
         'domainaxis2',
         'dimensioncoordinate0',
         'dimensioncoordinate1',
         'dimensioncoordinate2',
         'cellmethod0'
    ])
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

        '''
        return self._construct_type.keys()

    def values(self):
        '''Return all of the metadata constructs, in arbitrary order.

    .. versionadded:: (cfdm) 1.7.0

    .. seealso:: `get`, `items`, `keys`

    :Returns:

        `dict_values`
            The constructs as a Python `dict_values` iterator.

    **Examples:**

    >>> c = {{package}}.example_field(0)
    >>> c_values = c.constructs.values()
    >>> print(c_values)
    dict_values([
        <{{repr}}DimensionCoordinate: latitude(5) degrees_north>,
        <{{repr}}DimensionCoordinate: longitude(8) degrees_east>,
        <{{repr}}DimensionCoordinate: time(1) days since 2018-12-01 >,
        <{{repr}}CellMethod: area: mean>,
        <{{repr}}DomainAxis: size(5)>,
        <{{repr}}DomainAxis: size(8)>,
        <{{repr}}DomainAxis: size(1)>
    ])
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

        '''
        return self._dictionary().values()

    # ----------------------------------------------------------------
    # Methods
    # ----------------------------------------------------------------
    def construct_type(self, key):
        '''Return the type of a metadata construct for a given key.

    .. versionadded:: (cfdm) 1.7.0

    .. seealso:: `construct_types`

        '''
        x = self._construct_type.get(key)
        if x in self._ignore:
            return

        return x

    def construct_types(self):
        '''Return all of the construct types for all keys.

    .. versionadded:: (cfdm) 1.7.0

    .. seealso:: `construct_type`

        '''
        out = self._construct_type.copy()
        if self._ignore:
            for x in self._ignore:
                del out[x]
        # --- End: if

        return out

    def copy(self, data=True):
        '''Return a deep copy.

    ``f.copy()`` is equivalent to ``copy.deepcopy(f)``.

    .. versionadded:: (cfdm) 1.7.0

    :Parameters:

        data: `bool`, optional
            If False then do not copy data contained in the metadata
            constructs. By default such data are copied.

    :Returns:

        `{{class}}`
            The deep copy.

    **Examples:**

    >>> g = f.copy()
    >>> g = f.copy(data=False)

        '''
        return type(self)(source=self, copy=True, _ignore=self._ignore,
                          _view=False, _use_data=data)

    def data_axes(self):
        '''Return the domain axis constructs spanned by metadata construct
    data.

    .. versionadded:: (cfdm) 1.7.0

    :Returns:

        `dict`

            The keys of the domain axes constructs spanned by metadata
            construct data.

    **Examples:**

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

        '''
        if not self._ignore:
            return self._construct_axes.copy()
        else:
            ignore = self._ignore
            out = {}
            for construct_type, keys in self._constructs.items():
                if construct_type not in ignore:
                    for key in keys:
                        _ = self._construct_axes.get(key)
                        if _ is not None:
                            out[key] = _
            # --- End: for

            return out

    def filter_by_type(self, *types):
        '''Select metadata constructs by type.

    .. versionadded:: (cfdm) 1.7.0

    :Parameters:

        types: optional
            Select constructs that have are of any of the given types.

            A type is specified by one of the following strings:

            ==========================  ================================
            *type*                      Construct selected
            ==========================  ================================
            ``'domain_ancillary'``      Domain ancillary constructs
            ``'dimension_coordinate'``  Dimension coordinate constructs
            ``'domain_axis'``           Domain axis constructs
            ``'auxiliary_coordinate'``  Auxiliary coordinate constructs
            ``'cell_measure'``          Cell measure constructs
            ``'coordinate_reference'``  Coordinate reference constructs
            ``'cell_method'``           Cell method constructs
            ``'field_ancillary'``       Field ancillary constructs
            ==========================  ================================

            If no types are provided then all constructs are selected.

    :Returns:

        `{{class}}`
            The selected constructs and their construct keys.

    **Examples:**

    Select dimension coordinate constructs:

    >>> d = c.filter_by_type('dimension_coordinate')

    Select dimension coordinate and field ancillary constructs:

    >>> d = c.filter_by_type('dimension_coordinate',
        'field_ancillary')

        '''
        if types:
            # Ignore the all but the requested construct types
            ignore = set(self._key_base)
            ignore.difference_update(set(types))
            ignore.update(self._ignore)
        else:
            # Keep all construct types
            ignore = self._ignore

        return self.shallow_copy(_ignore=ignore)

    def key(self, default=ValueError()):
        '''Return the construct key of the sole metadata construct.

    .. versionadded:: (cfdm) 1.7.0

    .. seealso:: `get`, `keys`, `value`

    :Parameters:

        default: optional
            Return the value of the *default* parameter if there is
            not exactly one construct. If set to an `Exception`
            instance then it will be raised instead.

    :Returns:

        `str`
            The construct key.

    **Examples:**

    >>> print(c)
    Constructs:
    {'dimensioncoordinate0': <{{repr}}DimensionCoordinate: latitude(5) degrees_north>}
    >>> c.key(
    'dimensioncoordinate0'
    >>> c.value()
    <{{repr}}DimensionCoordinate: latitude(5) degrees_north>

        '''
        if not self:
            return self._default(default, "Can't get key for zero constructs")

        if len(self) > 1:
            return self._default(
                default, "Can't get key for {} constructs".format(len(self)))

        key, _ = self._dictionary().popitem()

        return key

    def new_identifier(self, construct_type):
        '''Return a new, unused construct key.

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

    >>> c.keys()
    ['domainaxis0',
     'domainaxis1',
     'domainaxis2',
     'dimensioncoordinate2',
     'dimensioncoordinate0',
     'dimensioncoordinate1',
     'cellmethod0']
    >>> c.new_identifier('domain_axis')
    'domainaxis3'
    >>> c.keys()
    ['domainaxis0',
     'domainaxis1',
     'domainaxis2',
     'dimensioncoordinate2',
     'dimensioncoordinate0',
     'dimensioncoordinate1',
     'cellmethod0']

        '''
        construct_type = self._check_construct_type(construct_type)

        keys = self._constructs[construct_type]

        n = len(keys)
        key_base = self._key_base[construct_type]
        key = '{0}{1}'.format(key_base, n)
        while key in keys:
            n += 1
            key = '{0}{1}'.format(key_base, n)

        return key

    def ordered(self):
        '''Return the constructs in their predetermined order.

    For cell method constructs, the predetermined order is that in
    which they where added.

    .. versionadded:: (cfdm) 1.7.0

    :Returns:

         `collections.OrderedDict`
             The constructs and their construct keys, in their
             predetermined order.

    **Examples:**

    >>> print(c)
    onstructs:
    {'cellmethod0': <{{repr}}CellMethod: domainaxis1: domainaxis2: mean>,
     'cellmethod1': <{{repr}}CellMethod: domainaxis3: maximum>}
    >>> c.ordered()
    OrderedDict([('cellmethod0', <{{repr}}CellMethod: domainaxis1: domainaxis2: mean>),
                 ('cellmethod1', <{{repr}}CellMethod: domainaxis3: maximum>)])

        '''
        if len(self._constructs) > 1:
            raise ValueError(
                "Can't order multiple construct types: {!r}".format(self))

        if self._ordered_constructs != set(self._constructs):
            raise ValueError(
                "Can't order un-orderable construct type: {!r}".format(self))

        return self._constructs[tuple(self._ordered_constructs)[0]].copy()

    def replace(self, key, construct, axes=None, copy=True):
        '''Replace one metadata construct with another.

    .. note:: No checks on the axes are done.

        '''
        construct_type = self.construct_types().get(key)
        if construct_type is None:
            raise ValueError(
                "Can't replace non-existent construct {!r}".format(key))

        if axes is not None and construct_type in self._array_constructs:
            self._construct_axes[key] = tuple(axes)

        if copy:
            construct = construct.copy()

        self._constructs[construct_type][key] = construct

    def shallow_copy(self, _ignore=None):
        '''Return a shallow copy.

    ``copy.copy(f)`` is equivalent to ``f.shallow_copy()``.

    .. versionadded:: (cfdm) 1.7.0

    :Returns:

            The shallow copy.

    **Examples:**

    >>> g = f.shallow_copy()

        '''
        if _ignore is None:
            _ignore = self._ignore

        return type(self)(source=self, copy=False, _ignore=_ignore,
                          _view=False)

    def value(self, default=ValueError()):
        '''Return the sole metadata construct.

    .. versionadded:: (cfdm) 1.7.0

    .. seealso:: `get`, `key`, `values`

    :Parameters:

        default: optional
            Return the value of the *default* parameter if there is
            not exactly one construct. If set to an `Exception`
            instance then it will be raised instead.

    :Returns:

            The metadata construct.

    **Examples:**

    >>> print(c)
    Constructs:
    {'dimensioncoordinate0': <{{repr}}DimensionCoordinate: latitude(5) degrees_north>}
    >>> c.key(
    'dimensioncoordinate0'
    >>> c.value()
    <{{repr}}DimensionCoordinate: latitude(5) degrees_north>

        '''
        if not self:
            return self._default(default, "Can't return zero constructs")

        if len(self) > 1:
            return self._default(
                default, "Can't return {} constructs".format(len(self)))

        _, construct = self._dictionary().popitem()

        return construct

# --- End: class
