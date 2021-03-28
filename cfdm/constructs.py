import logging

from itertools import chain

from . import core
from . import mixin

from .decorators import _manage_log_level_via_verbosity
from .core.functions import deepcopy

logger = logging.getLogger(__name__)


class Constructs(mixin.Container, core.Constructs):
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


    **Calling**

    Calling a `Constructs` instance selects metadata constructs by
    identity and is an alias for the `filter_by_identity` method. For
    example, to select constructs that have an identity of
    'air_temperature': ``d = c('air_temperature')``.

    .. versionadded:: (cfdm) 1.7.0

    """

    @classmethod
    def _filter_args(
            cls,
            method,
            args,
            original=None,
            todict=False,
            property_mode=None,
    ):
        """TODO.

        .. versionadded:: (cfdm) 1.8.10.0

        :Parameters:

        """
        args0 = (original, todict, None)

        if method in == "filter_by_property":
            # `_filter_by_property` has a different syntax to the
            # other "_filter_by_*"
            if property_mode is None:
                return args0

            return args0 + (property_mode,)

        return args0 + tuple(args)

    @classmethod
    def _filter_kwargs(
            cls,
            method,
            args,
            axis_mode=None,
            _identities_config=None,
    ):
        """TODO.

        .. versionadded:: (cfdm) 1.8.10.0

        :Parameters:

        """
        if isinstance(args, dict):
            return args

        kwargs = {}

        if not _identities_config and axis_mode is None:
            return kwargs

        if _identities_config and method == "filter_by_identity":
            kwargs["_identities_config"] = _identities_config
            return kwargs

        if axis_mode is not None and method == "filter_by_axis":
            kwargs["mode"] = axis_mode
            return kwargs
    @staticmethod
    def _filter_preprocess(arg, todict=False, filter_applied=None):
        """TODO.

        .. versionadded:: (cfdm) 1.8.10.0

        :Parameters:

            arg: `Constructs` or `dict`
                TODO

            todict: `bool`, optional
                If True, and *arg* is a `Constructs` object, then
                return a dictionary.

            filter_applied: `dict` optional
                TODO

        """
        if isinstance(arg, dict):
            return arg, arg.pop

        if todict:
            arg = arg.todict()
            return arg, arg.pop

        arg = arg.shallow_copy()

        if filter_applied:
            arg._prefiltered = arg.shallow_copy()
            arg._filters_applied = arg.filters_applied() + (filter_applied,)

        return arg, arg._pop

    def __call__(self, *identities, axis_mode=None,
                 property_mode=None, todict=False, cache=None,
                 **kwargs ):
        """Select metadata constructs by identity.

        Calling a `Constructs` instance selects metadata constructs by
        identity and is an alias for the `filter_by_identity`
        method. For example, to select constructs that have an
        identity of 'air_temperature': ``d = c('air_temperature')``.

        Note that ``c(*identities)`` is logically equivalent to
        ``c.filter_by_identity(*identities)``; and ``c(*identities,
        **kwargs)`` is logically equivalent to
        ``c.filter(**kwargs).filter_by_identity(*identities)``.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `filter_by_identity`

        :Parameters:

            identities: optional
                See `filter_by_identity` for details.

            {{todict: `bool`, optional}}

            {{cache: optional}}

        :Returns:

            `Constructs`
                The selected constructs and their construct keys.

        **Examples:**

        >>> print(c('latitude'))
        Constructs:
        {'dimensioncoordinate0': <DimensionCoordinate: latitude(5) degrees_north>}
        >>> print(c.filter_by_identity('latitude'))
        Constructs:
        {'dimensioncoordinate0': <DimensionCoordinate: latitude(5) degrees_north>}

        See `filter_by_identity` for more examples.

        """
        if not kwargs:
            return self.filter_by_identity(
                *identities, todict=todict, cache=cache
            )

        if identities:
            if "filter_by_identity" in kwargs:
                raise TypeError(
                    f"Can't set {self.__class__.__name__}.__call__() "
                    "keyword argument 'filter_by_identity' when "
                    "positional *identities arguments are also set"
                )

            kwargs["filter_by_identity"] = identities

        return self.filter(axis_mode=axis_mode,
                           property_mode=property_mode, todict=todict,
                           cache=cache, **kwargs)

    def __repr__(self):
        """Called by the `repr` built-in function.

        x.__repr__() <==> repr(x)

        .. versionadded:: (cfdm) 1.7.0

        """
        ignore = self._ignore
        construct_types = [
            f"{c}({len(v)})"
            for c, v in sorted(self._constructs.items())
            if len(v) and c not in ignore
        ]

        return f"<{self.__class__.__name__}: {', '.join(construct_types)}>"

    def __str__(self):
        """Called by the `str` built-in function.

        x.__str__() <==> str(x)

        .. versionadded:: (cfdm) 1.7.0

        """
        out = ["Constructs:"]

        ignore = self._ignore
        construct_types = [
            c
            for c, v in sorted(self._constructs.items())
            if len(v) and c not in ignore
        ]

        first = "{"
        for construct_type in construct_types:
            for key, value in sorted(self._constructs[construct_type].items()):
                if first:
                    out[0] = out[0] + f"\n{{{key!r}: {value!r},"
                    first = False
                else:
                    out.append(f"{key!r}: {value!r},")

        if first:
            out[0] = out[0] + "\n{}"
        else:
            out[-1] = out[-1][:-1] + "}"

        return "\n ".join(out)

    # ----------------------------------------------------------------
    # Private methods
    # ----------------------------------------------------------------
    def _axes_to_constructs(self):
        """Maps domain axes to constructs whose data span them.

        This is useful for ascertaining whether or not two `Constructs`
        instances are equal.

        .. versionadded:: (cfdm) 1.7.0

        :Returns:

            `dict`

        **Examples:**

        >>> f.constructs._axes_to_constructs()
        {('domainaxis0',): {'auxiliary_coordinate': {},
                            'cell_measure'        : {},
                            'dimension_coordinate': {'dimensioncoordinate0': <DimensionCoordinate: atmosphere_hybrid_height_coordinate(1) >},
                            'domain_ancillary'    : {'domainancillary0': <DomainAncillary: ncvar%a(1) m>,
                                                     'domainancillary1': <DomainAncillary: ncvar%b(1) >},
                            'field_ancillary'     : {}},
         ('domainaxis1',): {'auxiliary_coordinate': {'auxiliarycoordinate2': <AuxiliaryCoordinate: long_name=Grid latitude name(10) >},
                            'cell_measure'        : {},
                            'dimension_coordinate': {'dimensioncoordinate1': <DimensionCoordinate: grid_latitude(10) degrees>},
                            'domain_ancillary'    : {},
                            'field_ancillary'     : {}},
         ('domainaxis1', 'domainaxis2'): {'auxiliary_coordinate': {'auxiliarycoordinate0': <AuxiliaryCoordinate: latitude(10, 9) degrees_N>},
                                          'cell_measure'        : {},
                                          'dimension_coordinate': {},
                                          'domain_ancillary'    : {'domainancillary2': <DomainAncillary: surface_altitude(10, 9) m>},
                                          'field_ancillary'     : {'fieldancillary0': <FieldAncillary: air_temperature standard_error(10, 9) K>}},
         ('domainaxis2',): {'auxiliary_coordinate': {},
                            'cell_measure'        : {},
                            'dimension_coordinate': {'dimensioncoordinate2': <DimensionCoordinate: grid_longitude(9) degrees>},
                            'domain_ancillary'    : {},
                            'field_ancillary'     : {}},
         ('domainaxis2', 'domainaxis1'): {'auxiliary_coordinate': {'auxiliarycoordinate1': <AuxiliaryCoordinate: longitude(9, 10) degrees_E>},
                                          'cell_measure'        : {'cellmeasure0': <CellMeasure: measure:area(9, 10) km2>},
                                          'dimension_coordinate': {},
                                          'domain_ancillary'    : {},
                                          'field_ancillary'     : {}},
         ('domainaxis3',): {'auxiliary_coordinate': {},
                            'cell_measure'        : {},
                            'dimension_coordinate': {'dimensioncoordinate3': <DimensionCoordinate: time(1) days since 2018-12-01 >},
                            'domain_ancillary'    : {},
                            'field_ancillary'     : {}}}

        """
        data_axes = self.data_axes()
        array_constructs = self._array_constructs
        construct_type = self._construct_type
        ignore = self._ignore

        out = {
            axes: {
                ctype: {} for ctype in array_constructs if ctype not in ignore
            }
            for axes in data_axes.values()
        }

        for cid, construct in self.filter_by_data(todict=True).items():
            axes = data_axes.get(cid)
            out[axes][construct_type[cid]][cid] = construct

        return out

    @_manage_log_level_via_verbosity
    def _equals_cell_method(
        self,
        other,
        rtol=None,
        atol=None,
        verbose=None,
        ignore_type=False,
        axis1_to_axis0=None,
        key1_to_key0=None,
    ):
        """Whether two cell method constructs are the same."""
        # TODO add todict=True calls when ordered goes post Python 3.6
        cell_methods0 = self.filter_by_type("cell_method")
        cell_methods1 = other.filter_by_type("cell_method")

        len0 = len(cell_methods0)
        if len0 != len(cell_methods1):
            logger(
                "Different numbers of cell methods: "
                f"{cell_methods0!r} != {cell_methods1!r}"
            )
            return False

        if not len0:
            return True

        cell_methods0 = cell_methods0.ordered()
        cell_methods1 = cell_methods1.ordered()

        axis0_to_axis1 = {
            axis0: axis1 for axis1, axis0 in axis1_to_axis0.items()
        }

        for cm0, cm1 in zip(
            tuple(cell_methods0.values()), tuple(cell_methods1.values())
        ):
            # Check that there are the same number of axes
            axes0 = cm0.get_axes(())
            axes1 = list(cm1.get_axes(()))
            if len(axes0) != len(axes1):
                logger.info(
                    f"{cm0.__class__.__name__}: Different cell methods (mismatched axes):"
                    f"\n  {cell_methods0.ordered()}\n  {cell_methods1.ordered()}"
                )
                return False

            indices = []
            for axis0 in axes0:
                if axis0 is None:
                    return False
                for axis1 in axes1:
                    if axis0 in axis0_to_axis1 and axis1 in axis1_to_axis0:
                        if axis1 == axis0_to_axis1[axis0]:
                            # axis0 and axis1 are domain axis
                            # constructs that correspond to each other
                            axes1.remove(axis1)
                            indices.append(cm1.get_axes(()).index(axis1))
                            break
                    elif axis0 in axis0_to_axis1 or axis1 in axis1_to_axis0:
                        # Only one of axis0 and axis1 is a domain axis
                        # construct
                        logger.info(
                            "{0}: Different cell methods "
                            "(mismatched axes):\n  {1}\n  {2}".format(
                                cm0.__class__.__name__,
                                cell_methods0,
                                cell_methods1,
                            )
                        )
                        return False
                    elif axis0 == axis1:
                        # axes0 and axis 1 are identical standard
                        # names
                        axes1.remove(axis1)
                        indices.append(cm1.get_axes(()).index(axis1))
                    elif axis1 is None:
                        # axis1
                        logger.info(
                            "{0}: Different cell methods "
                            "(mismatched axes):\n  {1}\n  {2}".format(
                                cm0.__class__.__name__,
                                cell_methods0,
                                cell_methods1,
                            )
                        )
                        return False

            if len(cm1.get_axes(())) != len(indices):
                logger.info(
                    "{0}: [4] Different cell methods "
                    "(mismatched axes):\n  {1}\n  {2}".format(
                        cm0.__class__.__name__, cell_methods0, cell_methods1
                    )
                )
                return False

            cm1 = cm1.sorted(indices=indices)
            cm1.set_axes(axes0)

            if not cm0.equals(
                cm1,
                atol=atol,
                rtol=rtol,
                verbose=verbose,
                ignore_type=ignore_type,
            ):
                logger.info(
                    "Verbose: Different cell methods: "
                    "{0!r}, {1!r}".format(cell_methods0, cell_methods1)
                )
                return False

        return True

    @_manage_log_level_via_verbosity
    def _equals_coordinate_reference(
        self,
        other,
        rtol=None,
        atol=None,
        verbose=None,
        ignore_type=False,
        axis1_to_axis0=None,
        key1_to_key0=None,
    ):
        """Whether two coordinate reference constructs are the same."""
        refs0 = self._construct_dict("coordinate_reference")
        refs1 = other._construct_dict("coordinate_reference", copy=True)

        if len(refs0) != len(refs1):
            logger.info(
                "{}: Different numbers of coordinate reference constructs: "
                "{} != {}".format(
                    self.__class__.__name__,
                    len(refs0),
                    len(refs1),
                )
            )

            return False

        if refs0:
            if verbose == -1:
                debug_verbose = 2
            else:
                debug_verbose = 0

            for ref0 in refs0.values():
                found_match = False
                for key1, ref1 in tuple(refs1.items()):
                    logger.debug(
                        "{0}: Comparing {1!r}, {2!r}: ".format(
                            self.__class__.__name__, ref0, ref1
                        )
                    )  # pragma: no cover

                    if not ref0.equals(
                        ref1,
                        rtol=rtol,
                        atol=atol,
                        verbose=debug_verbose,
                        ignore_type=ignore_type,
                    ):
                        continue

                    # Coordinates
                    coordinates0 = ref0.coordinates()
                    coordinates1 = set()
                    for value in ref1.coordinates():
                        coordinates1.add(key1_to_key0.get(value, value))

                    if coordinates0 != coordinates1:
                        logger.debug(
                            "Coordinates don't match"
                        )  # pragma: no cover

                        continue

                    # Domain ancillary-valued coordinate conversion terms
                    terms0 = ref0.coordinate_conversion.domain_ancillaries()

                    terms1 = {
                        term: key1_to_key0.get(key, key)
                        for term, key in (
                            ref1.coordinate_conversion.domain_ancillaries().items()
                        )
                    }

                    if terms0 != terms1:
                        logger.debug(
                            "Coordinate conversion domain ancillaries "
                            "don't match"
                        )  # pragma: no cover

                        continue

                    logger.debug("OK")  # pragma: no cover

                    found_match = True
                    del refs1[key1]
                    break

                if not found_match:
                    logger.info(
                        "{}: No match for {!r})".format(
                            self.__class__.__name__, ref0
                        )
                    )  # pragma: no cover
                    return False

        return True

    @_manage_log_level_via_verbosity
    def _equals_domain_axis(
        self,
        other,
        rtol=None,
        atol=None,
        verbose=None,
        ignore_type=False,
        axis1_to_axis0=None,
        key1_to_key0=None,
    ):
        """Whether two domain axes constructs are the same."""
        domain_axes = self._construct_dict("domain_axis")
        self_sizes = [d.get_size() for d in domain_axes.values()]

        domain_axes = other._construct_dict("domain_axis")
        other_sizes = [d.get_size() for d in domain_axes.values()]

        if sorted(self_sizes) != sorted(other_sizes):
            # There is not a 1-1 correspondence between axis sizes
            logger.info(
                "{0}: Different domain axis sizes: {1} != {2}".format(
                    self.__class__.__name__,
                    sorted(self_sizes),
                    sorted(other_sizes),
                )
            )
            return False

        return True

    def copy(self, data=True):
        """Return a deep copy.

        ``f.copy()`` is equivalent to ``copy.deepcopy(f)``.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            data: `bool`, optional
                If False then do not copy data contained in the metadata
                constructs. By default such data are copied.

        :Returns:

            `Constructs`
                The deep copy.

        **Examples:**

        >>> g = f.copy()
        >>> g = f.copy(data=False)

        """
        out = super().copy(data=data)

        prefiltered = getattr(self, "_prefiltered", None)
        if prefiltered is not None:
            out._prefiltered = prefiltered.copy(data=data)
            out._filters_applied = self._filters_applied

        return out

    def domain_axis_identity(self, key):
        """Return the canonical identity for a domain axis construct.

        The identity is the first found of the following:

        1. The canonical identity of a dimension coordinate construct that
           span the domain axis construct.
        2. The identity of a one-dimensional auxiliary coordinate
           construct that spans the domain axis construct. This will
           either be the value of a ``standard_name``, ``cf_role``
           (preceded by ``'cf_role='``) or ``axis`` (preceded by
           ``'axis='``) property, as appropriate.
        3. The netCDF dimension name, preceded by 'ncdim%'.
        4. The domain axis construct key, preceded by 'key%'.

        :Parameters:

            key: `str`
                The construct key for the domain axis construct.

                *Parameter example:*
                  ``key='domainaxis2'``

        :Returns:

            `str`
                The identity.

        **Examples:**

        >>> c.domain_axis_identity('domainaxis1')
        'longitude'
        >>> c.domain_axis_identity('domainaxis2')
        'axis=Y'
        >>> c.domain_axis_identity('domainaxis3')
        'cf_role=timeseries_id'
        >>> c.domain_axis_identity('domainaxis4')
        'key%domainaxis4')

        """
        domain_axes = self._construct_dict("domain_axis")

        if key not in domain_axes:
            raise ValueError(f"No domain axis construct with key {key!r}")

        constructs_data_axes = self.data_axes()

        # Try to get the identity from an dimension coordinate
        dimension_coordinates = self._construct_dict("dimension_coordinate")
        identity = ""
        for dkey, dim in dimension_coordinates.items():
            if constructs_data_axes.get(dkey) == (key,):
                identity = dim.identity()
                if identity.startswith("ncvar%"):
                    identity = ""

                break

        if identity:
            return identity

        # Try to get the identity from an auxiliary coordinate
        auxiliary_coordinates = self._construct_dict("auxiliary_coordinate")

        identities = []
        for akey, aux in auxiliary_coordinates.items():
            if constructs_data_axes.get(akey) == (key,):
                identity = aux.identity()
                if not identity.startswith("ncvar%"):
                    identities.append(identity)

        if len(identities) == 1:
            return identities[0]
        elif len(identities) > 1:
            cf_role = []
            axis = []
            for i in identities:
                if i.startswith("axis="):
                    axis.append(i)
                elif i.startswith("cf_role="):
                    cf_role.append(i)

            if len(cf_role) == 1:
                return cf_role[0]

            if len(axis) == 1:
                return axis[0]

        # Try to get the identity from an netCDF dimension name
        ncdim = domain_axes[key].nc_get_dimension(None)
        if ncdim is not None:
            return f"ncdim%{ncdim}"

        # Get the identity from the domain axis construct key
        return f"key%{key}"

    @_manage_log_level_via_verbosity
    def equals(
        self,
        other,
        rtol=None,
        atol=None,
        verbose=None,
        ignore_data_type=False,
        ignore_fill_value=False,
        ignore_compression=True,
        _ignore_type=False,
        _return_axis_map=False,
    ):
        """Whether two `Constructs` instances are the same.

        {{equals tolerance}}

        {{equals compression}}

        Any type of object may be tested but equality is only possible
        with another `Constructs` construct, or a subclass of one.

        {{equals netCDF}}

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            other:
                The object to compare for equality.

            {{atol: number, optional}}

            {{rtol: number, optional}}

            ignore_fill_value: `bool`, optional
                If True then the ``_FillValue`` and ``missing_value``
                properties are omitted from the comparison for the
                metadata constructs.

            {{ignore_data_type: `bool`, optional}}

            {{ignore_compression: `bool`, optional}}

            {{verbose: `int` or `str` or `None`, optional}}

        :Returns:

            `bool`
                Whether the two instances are equal.

        **Examples:**

        >>> x.equals(x)
        True
        >>> x.equals(x.copy())
        True
        >>> x.equals('something else')
        False

        """
        if self is other:
            if not _return_axis_map:
                return True

        # Check that each instance is the same type
        if not isinstance(other, self.__class__):
            logger.info(
                "{0}: Incompatible type: {1}".format(
                    self.__class__.__name__, other.__class__.__name__
                )
            )
            if not _return_axis_map:
                return False

        if verbose == -1:
            debug_verbose = 2
        else:
            debug_verbose = 0

        axes0_to_axes1 = {}
        axis0_to_axis1 = {}
        axis1_to_axis0 = {}
        key1_to_key0 = {}

        # ------------------------------------------------------------
        # Domain axis constructs
        # ------------------------------------------------------------
        if not self._equals_domain_axis(
            other,
            rtol=rtol,
            atol=atol,
            verbose=verbose,
            ignore_type=_ignore_type,
            axis1_to_axis0=axis1_to_axis0,
            key1_to_key0=key1_to_key0,
        ):
            if not _return_axis_map:
                return False

        # ------------------------------------------------------------
        # Constructs with arrays
        # ------------------------------------------------------------
        log = []
        axes_to_constructs0 = self._axes_to_constructs()
        axes_to_constructs1 = other._axes_to_constructs()

        for axes0, constructs0 in axes_to_constructs0.items():
            matched_all_constructs_with_these_axes = False

            len_axes0 = len(axes0)
            for axes1, constructs1 in tuple(axes_to_constructs1.items()):

                constructs1 = constructs1.copy()

                if len_axes0 != len(axes1):
                    # axes1 and axes0 contain different number of
                    # domain axes.
                    continue

                for construct_type in self._array_constructs:
                    # role_constructs0 = constructs0[construct_type]
                    # role_constructs1 = constructs1[construct_type].copy()
                    role_constructs0 = constructs0.get(construct_type, {})
                    role_constructs1 = constructs1.get(
                        construct_type, {}
                    ).copy()

                    if len(role_constructs0) != len(role_constructs1):
                        # There are the different numbers of
                        # constructs of this type
                        matched_all_constructs_with_these_axes = False
                        log.append(
                            "{0}: Different numbers of {1} "
                            "constructs: {2} != {3}".format(
                                self.__class__.__name__,
                                construct_type,
                                len(role_constructs0),
                                len(role_constructs1),
                            )
                        )
                        break

                    # Note: the following set of log calls are not warnings
                    # as such, but set them as warnings so they only emerge
                    # at higher verbosity level than 'INFO'.

                    # Check that there are matching pairs of equal
                    # constructs
                    matched_construct = True
                    for key0, item0 in role_constructs0.items():
                        matched_construct = False
                        for key1, item1 in tuple(role_constructs1.items()):
                            logger.debug(
                                "{}: Comparing {!r}, {!r}: ".format(
                                    self.__class__.__name__, item0, item1
                                )
                            )  # pragma: no cover

                            if item0.equals(
                                item1,
                                rtol=rtol,
                                atol=atol,
                                verbose=debug_verbose,
                                ignore_data_type=ignore_data_type,
                                ignore_fill_value=ignore_fill_value,
                                ignore_compression=ignore_compression,
                                ignore_type=_ignore_type,
                            ):
                                logger.debug("OK")  # pragma: no cover

                                del role_constructs1[key1]
                                key1_to_key0[key1] = key0
                                matched_construct = True
                                break

                        if not matched_construct:
                            log.append(
                                "{0}: Can't match {1!r}".format(
                                    self.__class__.__name__, item0
                                )
                            )
                            break

                    if role_constructs1:
                        # At least one construct in other is not equal
                        # to a construct in self
                        break

                    # Still here? Then all constructs of this type
                    # that spanning these axes match
                    constructs1.pop(construct_type, None)

                matched_all_constructs_with_these_axes = not constructs1
                if matched_all_constructs_with_these_axes:
                    del axes_to_constructs1[axes1]
                    break

            if not matched_all_constructs_with_these_axes:
                names = [self.domain_axis_identity(axis0) for axis0 in axes0]
                logger.info(
                    "{0}: Can't match constructs "
                    "spanning axes {1}".format(self.__class__.__name__, names)
                )
                if log:
                    logger.info("\n".join(log))
                if not _return_axis_map:
                    return False
            else:
                # Map item axes in the two instances
                axes0_to_axes1[axes0] = axes1

        for axes0, axes1 in axes0_to_axes1.items():
            for axis0, axis1 in zip(axes0, axes1):
                if axis0 in axis0_to_axis1 and axis1 != axis0_to_axis1[axis0]:
                    logger.info(
                        "{0}: Ambiguous axis mapping "
                        "({1} -> both {2} and {3})".format(
                            self.__class__.__name__,
                            self.domain_axis_identity(axes0),
                            other.domain_axis_identity(axis1),
                            other.domain_axis_identity(axis0_to_axis1[axis0]),
                        )
                    )  # pragma: no cover
                    if not _return_axis_map:
                        return False
                elif (
                    axis1 in axis1_to_axis0 and axis0 != axis1_to_axis0[axis1]
                ):
                    logger.info(
                        "{0}: Ambiguous axis mapping "
                        "({1} -> both {2} and {3})".format(
                            self.__class__.__name__,
                            self.domain_axis_identity(axis0),
                            self.domain_axis_identity(axis1_to_axis0[axis0]),
                            other.domain_axis_identity(axes1),
                        )
                    )  # pragma: no cover
                    if not _return_axis_map:
                        return False

                axis0_to_axis1[axis0] = axis1
                axis1_to_axis0[axis1] = axis0

        if _return_axis_map:
            return axis0_to_axis1

        # ------------------------------------------------------------
        # Constructs with no arrays
        # ------------------------------------------------------------
        for construct_type in self._non_array_constructs:
            if not getattr(self, "_equals_" + construct_type)(
                other,
                rtol=rtol,
                atol=atol,
                verbose=verbose,
                ignore_type=_ignore_type,
                axis1_to_axis0=axis1_to_axis0,
                key1_to_key0=key1_to_key0,
            ):
                return False

        # ------------------------------------------------------------
        # Still here? Then the two objects are equal
        # ------------------------------------------------------------
        return True

    def filter(
        self,
        axis_mode="and",
        property_mode="and",
        todict=False,
        cache=None,
        _identities_config={},
        **filters,
    ):
        """Select metadata constructs by a sequence of filters.

        This method allows multiple filters defined by the
        "filter_by_*" methods to be chained in an alternative manner
        to calling the individual methods in sequence. For instance,
        to select the domain axis constucts with size 73

           >>> c2 = c.filter(filter_by_type=['domain_axis'],
           ...               filter_by_size=[73])

        is equivalent to

           >>> c2 = c.filter_by_type('domain_axis')
           >>> c2 = c2.filter_by_size(73)

        When the resultsis requested as a dictionary as opposed to a
        `{{class}}` object (see the *todict* parameter), using the
        `filter` method to call two or more filters is considerably
        faster than calling the individual methods in sequence. For
        instance

           >>> d = c.filter(filter_by_type=['domain_axis'],
           ...              filter_by_size=[73],
           ...              todict=True)

        is equivalent to, but considerably faster than

           >>> c2 = c.filter_by_type('domain_axis')
           >>> d = c2.filter_by_size(73, todict=True)

        .. versionadded:: (cfdm) 1.8.10.0

        .. seealso:: TODO `filters_applied`, `inverse_filter`,
                     `unfilter`

        :Parameters:

            filters: optional
                Keyword arguments defining the filters to apply. Each
                filter keyword defines a filter method, and its value
                provides the arguments for that method. For instance,
                the parameter ``filter_by_type=['domain_axis']`` will
                cause the `filter_by_type` method to be called with
                positional arguments ``*['domain_axis']``. The filters
                will be applied in the same order that the keyword
                arguments appear.

                Valid keywords and their values are:

                ==================  ==================================
                Keyword             Value
                ==================  ==================================
                filter_by_axis      A sequence as expected by the
                                    *axis* parameter of
                                    `filter_by_axis`

                filter_by_data----- ???

                filter_by_identity- A sequence as expected by the
                                    *identities* parameter of
                                    `filter_by_identity`

                filter_by_key ----- A sequence as expected by the
                                    *keys* parameter of
                                    `filter_by_key`

                filter_by_measure-- A sequence as expected by the
                                    *measure* parameter of
                                    `filter_by_measure`

                filter_by_method--- A sequence as expected by the
                                    *methods* parameter of
                                    `filter_by_method`

                filter_by_naxes---- A sequence as expected by the
                                    *naxes* parameter of
                                    `filter_by_naxes`

                filter_by_ncdim---- A sequence as expected by the
                                    *ncdims* parameter of
                                    `filter_by_ncdim`


                filter_by_ncvar---- A sequence as expected by the
                                    *ncvars* parameter of
                                    `filter_by_ncvar`

                filter_by_property- A dictionary as expected by the
                                    *properties* parameter of
                                    `filter_by_property`

                filter_by_size ---- A sequence as expected by the
                                    *sizes* parameter of
                                    `filter_by_size`

                filter_by_type      A sequence as expected by the
                                    *types* parameter of
                                    `filter_by_type`
                ==================  ==================================

            axis_mode: `str`, optional
                TODO

            property_mode: `str`, optional
                TODO

            {{todict: `bool`, optional}}

            {{cache: optional}}

        :Returns:
            TODO

        **Examples:**

        TODO

        """
        if cache is not None:
            return cache

        cls = type(self)
        if not filters:
            out, _ = cls._filter_preprocess(self, todict=todict)
            return out

        _data_axes = self._construct_axes

        # Apply filters
        out = self
        for method_name, args in filters.items():
            try:
                filter_method = getattr(cls, "_" + method_name)
            except AttributeError:
                raise TypeError(
                    "filter() got an unexpected keyword argument "
                    f"{method_name!r}"
                )

            kwargs = cls._filter_kwargs(
                method_name,
                args,
                axis_mode=axis_mode,
                _identities_config=_identities_config,
            )

            args = cls._filter_args(
                method_name,
                args,
                original=self,
                todict=todict,
                property_mode=property_mode,
            )

            out = filter_method(out, *args, **kwargs)

        return out

    @classmethod
    def _filter_by_axis(
        cls,
        arg,
        original,
        todict,
        cache,
        *axes,
        axis_mode="and",
    ):
        """Worker function for `filter_by_axis` and `filter`.

        .. versionadded:: (cfdm) 1.8.10.0

        """
        if cache is not None:
            return cache

        # Parse the axis_mode parameter
        _or = False
        _exact = False
        _subset = False
        if axis_mode == "and":
            pass
        elif axis_mode == "or":
            _or = True
        elif axis_mode == "exact":
            _exact = True
        elif axis_mode == "subset":
            _subset = True
        elif axes:
            raise ValueError(
                "'axis_mode' parameter must be one of 'and', 'or', 'exact', "
                f"'subset'. Got: {axis_mode!r}"
            )

        out, pop = cls._filter_preprocess(
            arg,
            filter_applied={"filter_by_axis": (axes, {"axis_mode": axis_mode})},
            todict=todict,
        )

        data_axes = original._construct_axes
        if not axes:
            construct_type = original._construct_type
            for cid in tuple(out.keys()):
                if construct_type[cid] not in data_axes:
                    # This construct does not have data axes
                    pop(cid)

            return out

        axes = set(axes)

        # Still here?
        for cid in tuple(out):
            x = data_axes.get(cid)
            if x is None:
                # This construct does not have data axes
                pop(cid)
                continue

            ok = True
            if _exact:
                if set(x) != axes:
                    ok = False
            elif _subset:
                if not set(x).issubset(axes):
                    ok = False
            else:
                for axis_key in axes:
                    ok = axis_key in x
                    if _or:
                        if ok:
                            break
                    elif not ok:
                        break

            if not ok:
                # This construct ..
                pop(cid)

        return out

    def filter_by_axis(
        self,
        *axes,
        axis_mode="and",
        todict=False,
        cache=None,
    ):
        """Select metadata constructs by axes spanned by their data.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `filter_by_data`, `filter_by_key`,
                     `filter_by_measure`, `filter_by_method`,
                     `filter_by_identity`, `filter_by_naxes`,
                     `filter_by_ncdim`, `filter_by_ncvar`,
                     `filter_by_property`, `filter_by_type`,
                     `filters_applied`, `inverse_filter`, `unfilter`

        :Parameters:

            axes: optional
                Select the constructs whose data spans particular
                domain axis constructs.

                A domain axis construct is identified by its construct
                key (e.g. ``'domainaxis1'``).

                If no axes are provided then all constructs that do or
                could have data, spanning any domain axes constructs,
                are selected.

            axis_mode: `str`, optional
                Define the relationship between the given domain axes
                and the constructs' data.

                ===========  =================================================
                *axis_mode*  Description
                ===========  =================================================
                ``'and'``   A construct is selected if it spans *all* of the
                            given domain axes, *and possibly others*.

                ``'or'``    A construct is selected if it spans *any* of the
                            domain axes, *and possibly others*.

                ``exact``   A construct is selected if it spans *all* of the
                            given domain axes, *and no others*.

                ``subset``  A construct is selected if it spans *a subset* of
                            the given domain axes, *and no others*.
                ===========  ==================================================

                By default *axis_mode* is ``'and'``.

            {{todict: `bool`, optional}}

            {{cache: optional}}

        :Returns:

            `Constructs`
                The selected constructs and their construct keys.

        **Examples:**

        Select constructs whose data spans the "domainaxis1" domain
        axis construct:

        >>> d = c.filter_by_axis('and', 'domainaxis1')

        Select constructs whose data does not span the "domainaxis2"
        domain axis construct:

        >>> d = c.filter_by_axis('and', 'domainaxis2').inverse_filter()

        Select constructs whose data spans the "domainaxis1", but not
        the "domainaxis2" domain axis constructs:

        >>> d = c.filter_by_axis('and', 'domainaxis1')
        >>> d = d.filter_by_axis('and', 'domainaxis2')
        >>> d  = d.inverse_filter(1)

        Select constructs whose data spans the "domainaxis1" or the
        "domainaxis2" domain axis constructs:

        >>> d = c.filter_by_axis('or', 'domainaxis1', 'domainaxis2')

        """
        return self._filter_by_axis(
            self,
            self,
            todict,
            cache,
            *axes,
            axis_mode=axis_mode,
        )

    def filter_by_data(self, todict=False, cache=None):
        """Selects metadata constructs that could contain data.

        Selection is not based on whether they actually have data,
        rather by whether the construct supports the inclusion of
        data. For example, constructs selected by this method will all
        have a `!get_data` method.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `filter_by_axis`, `filter_by_key`,
                     `filter_by_measure`, `filter_by_method`,
                     `filter_by_identity`, `filter_by_naxes`,
                     `filter_by_ncdim`, `filter_by_ncvar`,
                     `filter_by_property`, `filter_by_type`,
                     `filters_applied`, `inverse_filter`, `unfilter`

        :Parameters:

            {{todict: `bool`, optional}}

            {{cache: optional}}

        :Returns:

            `Constructs` or `dict`
                The selected constructs and their construct keys.

        **Examples:**

        Select constructs that could contain data:

        >>> d = c.filter_by_data()

        """
        return self.filter_by_type(
            *self._array_constructs, todict=todict, cache=cache
        )

    @classmethod
    def _filter_by_identity(
        cls,
        arg,
            original,
        todict,
        cache,
        *identities,
        _identities_config={},
    ):
        """Worker function for `filter_by_identity` and `filter`.

        .. versionadded:: (cfdm) 1.8.10.0
        """
        if cache is not None:
            return cache

        out, pop = cls._filter_preprocess(
            arg,
            filter_applied={"filter_by_identity": identities},
            todict=todict,
        )

        if not identities:
            # Return all constructs if no identities have been provided
            return out

        for cid, construct in tuple(out.items()):
            ok = False
            for value1 in chain(
                ("key%" + cid,),
                construct.identities(generator=True, **_identities_config),
            ):
                for value0 in identities:
                    ok = cls._matching_values(
                        value0, construct, value1, basic=True
                    )
                    if ok:
                        break

                if ok:
                    break

            if not ok:
                # This construct does not match any of the identities
                pop(cid)

        return out

    def filter_by_identity(
        self,
        *identities,
        todict=False,
        cache=None,
        _identities_config={},
    ):
        """Select metadata constructs by identity.

        TODO Calling a `Constructs` instance selects metadata
        constructs by identity and is an alias for the
        `filter_by_identity` method.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `filter_by_axis`, `filter_by_data`,
                     `filter_by_key`, `filter_by_measure`,
                     `filter_by_method`, `filter_by_naxes`,
                     `filter_by_ncdim`, `filter_by_ncvar`,
                     `filter_by_property`, `filter_by_type`,
                     `filters_applied`, `inverse_filter`, `unfilter`

        :Parameters:

            identities: optional
                Select constructs that have any of the given
                identities.

                An identity is specified by a string
                (e.g. ``'latitude'``, ``'long_name=time'``, etc.); or
                a compiled regular expression
                (e.g. ``re.compile('^atmosphere')``), for which all
                constructs whose identities match (via `re.search`)
                are selected.

                If no identities are provided then all constructs are
                selected.

                Each construct has a number of identities, and is
                selected if any of them match any of those provided. A
                construct's identities are those returned by its
                `!identities` method. In the following example, the
                construct ``x`` has four identities:

                   >>> x.identities()
                   ['time', 'long_name=Time', 'foo=bar', 'ncvar%T']

                In addition, each construct also has an identity based
                its construct key
                (e.g. ``'key%dimensioncoordinate2'``)

                Note that in the output of a `print` call or `!dump`
                method, a construct is always described by one of its
                identities, and so this description may always be used
                as an *identities* argument.

            {{todict: `bool`, optional}}

            {{cache: optional}}

            kwargs: optional
                Additional parameters for configuring each construct's
                `identities` method. ``generator=True`` is passed by
                default.

                .. versionadded:: (cfdm) 1.8.10.0

        :Returns:

            `Constructs`
                The selected constructs and their construct keys.

        **Examples:**

        Select constructs that have a ``standard_name`` property of
        'latitude':

        >>> d = c.filter_by_identity('latitude')

        Select constructs that have a ``long_name`` property of
        'Height':

        >>> d = c.filter_by_identity('long_name=Height')

        Select constructs that have a ``standard_name`` property of
        'latitude' or a "foo" property of 'bar':

        >>> d = c.filter_by_identity('latitude', 'foo=bar')

        Select constructs that have a netCDF variable name of 'time':

        >>> d = c.filter_by_identity('ncvar%time')

        """
        return self._filter_by_identity(
            self,
            self,
            todict,
            cache,
            *identities,
            _identities_config=_identities_config,
        )

    def filter_by_key(self, *keys, todict=False, cache=None):
        """Select metadata constructs by key.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `filter_by_axis`, `filter_by_data`,
                     `filter_by_measure`, `filter_by_method`,
                     `filter_by_identity`, `filter_by_naxes`,
                     `filter_by_ncdim`, `filter_by_ncvar`,
                     `filter_by_property`, `filter_by_type`,
                     `filters_applied`, `inverse_filter`, `unfilter`

        :Parameters:

            keys: optional
                Select constructs that have any of the given construct
                keys.

                A key is specified by a string
                (e.g. ``'fieldancillary0'``).

                If no keys are provided then all constructs are
                selected.

            {{todict: `bool`, optional}}

            {{cache: optional}}

        :Returns:

            `Constructs`
                The selected constructs and their construct keys.

        **Examples:**

        Select the construct with key 'domainancillary0':

        >>> d = c.filter_by_key('domainancillary0')

        Select the constructs with keys 'dimensioncoordinate1' or
        'fieldancillary0':

        >>> d = c.filter_by_key('dimensioncoordinate1', 'fieldancillary0')

        """
        out = self.shallow_copy()

        out._prefiltered = self.shallow_copy()
        out._filters_applied = self.filters_applied() + (
            {"filter_by_key": keys},
        )

        if not keys:
            return out

        for cid in tuple(out._construct_type):
            if cid not in keys:
                out._pop(cid)

        return out

    @classmethod
    def _filter_by_measure(cls, arg, original, todict, cache, *measures):
        """Worker function for `filter_by_measure` and `filter`.

        .. versionadded:: (cfdm) 1.8.10.0

        :Parameters:

            arg: `Constructs` or `dict`
                TODO

            original: `Constructs`
                TODO

            todict: 
                As for *todict* in `filter_by_type`

            cache: 
                As for *cache* in `filter_by_type`
        """
        if cache is not None:
            return cache

        out, pop = cls._filter_preprocess(
            arg,
            filter_applied={"filter_by_measure": measures},
            todict=todict,
        )

        construct_type = original._construct_type
        if not measures:
            for cid in tuple(out.keys()):
                if construct_type[cid] != "cell_measure":
                    pop(cid)

            return out

        for cid, construct in tuple(out.items()):
            if construct_type[cid] != "cell_measure":
                pop(cid)
                continue

            value1 = construct.get_measure(None)

            ok = False
            if value1 is not None:
                for value0 in measures:
                    ok = cls._matching_values(
                        value0, construct, value1, basic=True
                    )
                    if ok:
                        break

            if not ok:
                # This construct does not match any of the measures
                pop(cid)

        return out

    def filter_by_measure(self, *measures, todict=False, cache=None):
        """Select cell measure constructs by measure.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `filter_by_axis`, `filter_by_data`,
                     `filter_by_key`, `filter_by_method`,
                     `filter_by_identity`, `filter_by_naxes`,
                     `filter_by_ncdim`, `filter_by_ncvar`,
                     `filter_by_property`, `filter_by_type`,
                     `filters_applied`, `inverse_filter`, `unfilter`

        :Parameters:

            measures: optional
                Select cell measure constructs that have any of the
                given measure values.

                A measure is specified by a string (e.g. ``'area'``);
                or a compiled regular expression
                (e.g. ``re.compile('^a')``), for which all constructs
                whose measures match (via `re.search`) are selected.

                If no measures are provided then all cell measure
                constructs are selected.

            {{todict: `bool`, optional}}

            {{cache: optional}}

        :Returns:

            `Constructs`
                The selected cell measure constructs and their
                construct keys.

        **Examples:**

        >>> print(t.constructs.filter_by_type('measure'))
        Constructs:
        {'cellmeasure0': <{{repr}}CellMeasure: measure:area(9, 10) km2>,
         'cellmeasure1': <{{repr}}CellMeasure: measure:volume(3, 9, 10) m3>}

        Select cell measure constructs that have a measure of 'area':

        >>> print(c.filter_by_measure('area'))
        Constructs:
        {'cellmeasure0': <{{repr}}CellMeasure: measure:area(9, 10) km2>}

        Select cell measure constructs that have a measure of 'area'
        or 'volume':

        >>> print(c.filter_by_measure('area', 'volume'))
        Constructs:
        {'cellmeasure0': <{{repr}}CellMeasure: measure:area(9, 10) km2>,
         'cellmeasure1': <{{repr}}CellMeasure: measure:volume(3, 9, 10) m3>}

        Select cell measure constructs that have a measure of start
        with the letter "a" or "v":

        >>> print(c.filter_by_measure(re.compile('^a|v')))
        Constructs:
        {'cellmeasure0': <{{repr}}CellMeasure: measure:area(9, 10) km2>,
         'cellmeasure1': <{{repr}}CellMeasure: measure:volume(3, 9, 10) m3>}

        Select cell measure constructs that have a measure of any
        value:

        >>> print(c.filer_by_measure())
        Constructs:
        {'cellmeasure0': <{{repr}}CellMeasure: measure:area(9, 10) km2>,
         'cellmeasure1': <{{repr}}CellMeasure: measure:volume(3, 9, 10) m3>}

        """
        return self._filter_by_measure(self, self, todict, cache, *measures)

    def filter_by_method(self, *methods, todict=False, cache=None):
        """Select cell method constructs by method.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `filter_by_axis`, `filter_by_data`,
                     `filter_by_key`, `filter_by_measure`,
                     `filter_by_identity`, `filter_by_naxes`,
                     `filter_by_ncdim`, `filter_by_ncvar`,
                     `filter_by_property`, `filter_by_type`,
                     `filters_applied`, `inverse_filter`, `unfilter`

        :Parameters:

            methods: optional
                Select cell method constructs that have any of the
                given methods.

                A method is specified by a string (e.g. ``'mean'``);
                or a compiled regular expression
                (e.g. ``re.compile('^m')``), for which all constructs
                whose methods match (via `re.search`) are selected.

                If no methods are provided then all cell method
                constructs are selected.

            {{todict: `bool`, optional}}

            {{cache: optional}}

        :Returns:

            `Constructs`
                The selected cell method constructs and their
                construct keys.

        **Examples:**

        >>> print(c.constructs.filter_by_type('cell_method'))
        Constructs:
        {'cellmethod0': <{{repr}}CellMethod: domainaxis1: domainaxis2: mean where land (interval: 0.1 degrees)>,
         'cellmethod1': <{{repr}}CellMethod: domainaxis3: maximum>}

        Select cell method constructs that have a method of 'mean':

        >>> print(c.filter_by_method('mean'))
        Constructs:
        {'cellmethod0': <{{repr}}CellMethod: domainaxis1: domainaxis2: mean where land (interval: 0.1 degrees)>}

        Select cell method constructs that have a method of 'mean' or
        'maximum':

        >>> print(c.filter_by_method('mean', 'maximum'))
        Constructs:
        {'cellmethod0': <{{repr}}CellMethod: domainaxis1: domainaxis2: mean where land (interval: 0.1 degrees)>,
         'cellmethod1': <{{repr}}CellMethod: domainaxis3: maximum>}

        Select cell method constructs that have a method that contain
        the letter 'x':

        >>> import re
        >>> print(c.filter_by_method(re.compile('x')))
        Constructs:
        {'cellmethod1': <{{repr}}CellMethod: domainaxis3: maximum>}

        Select cell method constructs that have a method of any value:

        >>> print(c.filter_by_method())
        Constructs:
        {'cellmethod0': <{{repr}}CellMethod: domainaxis1: domainaxis2: mean where land (interval: 0.1 degrees)>,
         'cellmethod1': <{{repr}}CellMethod: domainaxis3: maximum>}

        """
        out = self.shallow_copy()

        out._prefiltered = self.shallow_copy()
        out._filters_applied = self.filters_applied() + (
            {"filter_by_method": methods},
        )

        for cid, construct in tuple(out.items()):
            if self._construct_type[cid] != "cell_method":
                out._pop(cid)
                continue

            #            try:
            #                get_method = construct.get_method
            #            except AttributeError:
            #                # This construct doesn't have a "get_method" method
            #                out._pop(cid)
            #                continue

            if not methods:
                continue

            ok = False
            value1 = construct.get_method(None)
            for value0 in methods:
                ok = self._matching_values(
                    value0, construct, value1, basic=True
                )
                if ok:
                    break

            if not ok:
                # This construct does not match any of the methods
                out._pop(cid)

        return out

    @classmethod
    def _filter_by_naxes( cls, arg, original, todict, cache, *naxes):
        """Worker function for `filter_by_naxes` and `filter`.

        .. versionadded:: (cfdm) 1.8.10.0
        """
        if cache is not None:
            return cache

        out, pop = cls._filter_preprocess(
            arg,
            filter_applied={"filter_by_naxes": naxes},
            todict=todict,
        )
        
        data_axes = original._construct_axes
        if not naxes:
            # Return all constructs that have data if no naxes have
            # been provided
            for cid in tuple(out):
                if cid not in data_axes:
                    # This construct does not have data axes
                    pop(cid)

            return out

        for key in tuple(out):
            x = data_axes.get(key)
            if x is None:
                pop(key)
                continue

            len_x = len(x)

            ok = True
            for n in naxes:
                if n == len_x:
                    ok = True
                    break

                ok = False

            if not ok:
                # This construct does not have the right number of axes
                pop(key)

        return out

    def filter_by_naxes(
        self, *naxes, todict=False, cache=None, _data_axes=None
    ):
        """Selects constructs by the number of axes their data spans.

        Specifically, selects metadata constructs by the number of
        domain axis constructs spanned by their data.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `filter_by_axis`, `filter_by_data`,
                     `filter_by_key`, `filter_by_measure`,
                     `filter_by_method`, `filter_by_identity`,
                     `filter_by_ncdim`, `filter_by_ncvar`,
                     `filter_by_property`, `filter_by_type`,
                     `filters_applied`, `inverse_filter`, `unfilter`

        :Parameters:

            naxes: optional
                Select constructs whose data spans a particular number
                of domain axis constructs.

                A number of domain axis constructs is given by an
                `int`.

                If no numbers are provided then all constructs that do
                or could have data, spanning any domain axes
                constructs, are selected.

            {{todict: `bool`, optional}}

            {{cache: optional}}

        :Returns:

            `Constructs`
                The selected domain axis constructs and their
                construct keys.

        **Examples:**

        Select constructs that contain data that spans two domain axis
        constructs:

        >>> d = c.filter_by_naxes(2)

        Select constructs that contain data that spans one or two
        domain axis constructs:

        >>> d = c.filter_by_ncdim(1, 2)

        """
        return self._filter_by_naxes(
            self,
            self, todict, cache, 
            *naxes,
        )

    def filter_by_ncdim(self, *ncdims, todict=False, cache=None):
        """Select domain axis constructs by netCDF dimension name.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `filter_by_axis`, `filter_by_data`,
                     `filter_by_key`, `filter_by_measure`,
                     `filter_by_method`, `filter_by_naxes`,
                     `filter_by_identity`, `filter_by_ncvar`,
                     `filter_by_property`, `filter_by_type`,
                     `filters_applied`, `inverse_filter`, `unfilter`

        :Parameters:

            ncdims: optional
                Select domain axis constructs that have any of the
                given netCDF dimension names.

                A netCDF dimension name is specified by a string
                (e.g. ``'time'``); or a compiled regular expression
                (e.g. ``re.compile('^lat')``), for which all
                constructs whose netCDF dimension names match (via
                `re.search`) are selected.

                If no netCDF dimension names are provided then all
                domain axis constructs are selected.

            {{todict: `bool`, optional}}

            {{cache: optional}}

        :Returns:

            `Constructs`
                The selected domain axis constructs and their
                construct keys.

        **Examples:**

        Select the domain axis constructs with netCDF dimension name
        'time':

        >>> d = c.filter_by_ncdim('time')

        Select the domain axis constructs with netCDF dimension name
        'time' or 'lat':

        >>> d = c.filter_by_ncdim('time', 'lat')

        """
        out = self.shallow_copy()

        out._prefiltered = self.shallow_copy()
        out._filters_applied = self.filters_applied() + (
            {"filter_by_ncdim": ncdims},
        )

        for cid, construct in tuple(out.items()):
            try:
                nc_get_dimension = construct.nc_get_dimension
            except AttributeError:
                # This construct doesn't have a "nc_get_dimension"
                # method
                out._pop(cid)
                continue

            if not ncdims:
                continue

            value1 = nc_get_dimension(None)
            ok = False
            for value0 in ncdims:
                ok = self._matching_values(
                    value0, construct, value1, basic=True
                )
                if ok:
                    break

            if not ok:
                # This construct does not match any of the netCDF
                # dimension names
                out._pop(cid)

        return out

    def filter_by_ncvar(self, *ncvars, todict=False, cache=None):
        """Select domain axis constructs by netCDF variable name.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `filter_by_axis`, `filter_by_data`,
                     `filter_by_key`, `filter_by_measure`,
                     `filter_by_method`, `filter_by_naxes`,
                     `filter_by_identity`, `filter_by_ncdim`,
                     `filter_by_property`, `filter_by_type`,
                     `filters_applied`, `inverse_filter`, `unfilter`

        :Parameters:

            ncvars: optional
                Select constructs that have any of the given netCDF
                variable names.

                A netCDF variable name is specified by a string
                (e.g. ``'time'``); or a compiled regular expression
                (e.g. ``re.compile('^lat')``), for which all
                constructs whose netCDF variable names match (via
                `re.search`) are selected.

                If no netCDF variable names are provided then all
                constructs that do or could have a netCDF variable
                name, with any value, are selected.

            {{todict: `bool`, optional}}

            {{cache: optional}}

        :Returns:

            `Constructs`
                The selected constructs and their construct keys.

        **Examples:**

        Select the constructs with netCDF variable name 'time':

        >>> d = c.filter_by_ncvar('time')

        Select the constructs with netCDF variable name 'time' or
        'lat':

        >>> d = c.filter_by_ncvar('time', 'lat')

        """
        out = self.shallow_copy()

        out._prefiltered = self.shallow_copy()
        out._filters_applied = self.filters_applied() + (
            {"filter_by_ncvar": ncvars},
        )

        for cid, construct in tuple(out.items()):
            try:
                nc_get_variable = construct.nc_get_variable
            except AttributeError:
                # This construct doesn't have a "nc_get_variable"
                # method
                out._pop(cid)
                continue

            if not ncvars:
                continue

            value1 = nc_get_variable(None)
            ok = False
            for value0 in ncvars:
                ok = self._matching_values(
                    value0, construct, value1, basic=True
                )
                if ok:
                    break

            if not ok:
                # This construct does not match any of the netCDF
                # variable names
                out._pop(cid)

        return out

    @classmethod
    def _matching_values(cls, value0, construct, value1, basic=False):
        """Whether or not two values are the same.

        :Parameters:

            value0:
                The first value to be matched.

            construct:
                The construct whose `_equals` method is used to
                determine whether values can be considered to match.

            value1:
                The second value to be matched.

            basic: `bool`
                If True then value0 and value1 will be compared with
                the basic ``==`` operator.

        :Returns:

            `bool`
                Whether or not the two values match.

        """
        if value1 is not None:
            try:
                result = value0.search(value1)
            except (AttributeError, TypeError):
                result = construct._equals(value1, value0, basic=basic)

            if result:
                # This construct matches this property
                return True

        return False

    @classmethod
    def _filter_by_property(cls, arg, todict, cache, *mode, **properties):
        """Worker function for `filter_by_property` and `filter`.

        .. versionadded:: (cfdm) 1.8.10.0

        """
        if cache is not None:
            return cache

        # Parse mode
        _or = False
        if mode:
            if len(mode) > 1:
                raise ValueError("Can provide at most one positional argument")

            x = mode[0]
            if x == "or":
                _or = True
            elif x != "and":
                raise ValueError(
                    "Positional argument 'mode', if provided, "
                    "must be 'or' or 'and'"
                )

        out, pop = cls._filter_preprocess(
            arg,
            filter_applied={"filter_by_property": (mode, properties)},
            todict=todict,
        )

        if not properties:
            for cid, construct in tuple(out.items()):
                try:
                    construct.get_property
                except AttributeError:
                    pop(cid)

            return out

        for cid, construct in tuple(out.items()):
            try:
                get_property = construct.get_property
            except AttributeError:
                pop(cid)
                continue

            ok = True
            for name, value0 in properties.items():
                value1 = get_property(name, None)
                if value1 is None:
                    ok = False
                else:
                    ok = self._matching_values(value0, construct, value1)

                if _or:
                    if ok:
                        break
                elif not ok:
                    break

            if not ok:
                # This construct does not match any of the properties
                pop(cid)

        return out

    def filter_by_property(self, *mode, **properties):
        """Select metadata constructs by property.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `filter_by_axis`, `filter_by_data`,
                     `filter_by_key`, `filter_by_measure`,
                     `filter_by_method`, `filter_by_naxes`,
                     `filter_by_identity`, `filter_by_ncdim`,
                     `filter_by_ncvar`, `filter_by_type`,
                     `filters_applied`, `inverse_filter`, `unfilter`

        :Parameters:

            mode: optional
                Define the behaviour when multiple properties are
                provided.

                By default (or if the *mode* parameter is ``'and'``) a
                construct is selected if it matches all of the given
                properties, but if the *mode* parameter is ``'or'``
                then a construct will be selected when at least one of
                its properties matches.

            properties:  optional
                Select constructs that have properties with the given
                values.

                By default a construct is selected if it matches all
                of the given properties, but it may alternatively be
                selected when at least one of its properties matches
                (see the *mode* positional parameter).

                A property value is given by a keyword parameter of
                the property name. The value may be a scalar or vector
                (e.g. ``'latitude'``, ``4``, ``['foo', 'bar']``); or a
                compiled regular expression
                (e.g. ``re.compile('^ocean')``), for which all
                constructs whose methods match (via `re.search`) are
                selected.

                If no properties are provided then all constructs that
                do or could have properties, with any values, are
                selected.

        :Returns:

            `Constructs`
                The selected constructs and their construct keys.

        **Examples:**

        Select constructs that have a ``standard_name`` of 'latitude':

        >>> d = c.filter_by_property(standard_name='latitude')

        Select constructs that have a ``long_name`` of 'height' *and*
        ``units`` of 'm':

        >>> d = c.filter_by_property(long_name='height', units='m')

        Select constructs that have a ``long_name`` of 'height' *or* a
        ``foo`` of 'bar':

        >>> d = c.filter_by_property('or', long_name='height', foo='bar')

        Select constructs that have a ``standard_name`` which contains
        start with the string 'air':

        >>> import re
        >>> d = c.filter_by_property(standard_name=re.compile('^air'))

        """
        return self._filter_by_property(self, self, False, None,
                                        *mode, **properties)

    @classmethod
    def _filter_by_size(
            cls, arg, original, todict, cache, *sizes
    ):
        """Worker function for `filter_by_size` and `filter`.

        .. versionadded:: (cfdm) 1.8.10.0
        """
        if cache is not None:
            return cache

        out, pop = cls._filter_preprocess(
            arg,
            filter_applied={"filter_by_size": sizes},
            todict=todict,
        )

        if not sizes:
            for cid, construct in tuple(out.items()):
                try:
                    construct.get_size
                except AttributeError:
                    pop(cid)

            return out

            dd = _xxx._constructs.get("domain_axis", {})
            for cid in tuple(out):
                if cid not in dd:
                    pop(cid)

            return out

        for cid, construct in tuple(out.items()):
            try:
                get_size = construct.get_size
            except AttributeError:
                pop(cid)
                continue

            value0 = get_size(None)

            ok = False
            for value1 in sizes:
                ok = cls._matching_values(
                    value1, construct, value0, basic=True
                )
                if ok:
                    break

            if not ok:
                # This construct does not match any of the sizes
                pop(cid)

        return out

    def filter_by_size(self, *sizes, todict=False, cache=None):
        """Select domain axis constructs by size.

        .. versionadded:: (cfdm) 1.7.3

        .. seealso:: `filter_by_axis`, `filter_by_data`,
                     `filter_by_key`, `filter_by_measure`,
                     `filter_by_method`, `filter_by_naxes`,
                     `filter_by_identity`, `filter_by_ncdim`,
                     `filter_by_ncvar`, `filter_by_property`,
                     `filter_by_type`, `filters_applied`,
                     `inverse_filter`, `unfilter`

        :Parameters:

            sizes: optional
                Select domain axis constructs that have any of the
                given sizes.

                A size is specified by an `int`.

                If no sizes are provided then all domain axis
                constructs are selected.

            {{todict: `bool`, optional}}

            {{cache: optional}}

        :Returns:

            `Constructs`
                The selected domain axis constructs and their
                construct keys.

        **Examples:**

        Select domain axis constructs that have a size of 1:

        >>> d = c.filter_by_size(1)

        Select domain axis constructs that have a size of 1 or 96:

        >>> d = c.filter_by_size(1, 96)

        """
        return self._filter_by_size(self, self, todict, cache, *sizes)

    @classmethod
    def _filter_by_type(
        cls, self, *types, todict=False, cache=None, _data_axes=None
    ):
        """Worker function for `filter_by_type` and `filter`.

        .. versionadded:: (cfdm) 1.8.10.0
        """
        if cache is not None:
            return cache

        if isinstance(self, dict):
            raise ValueError(
                "When 'filter_by_type' is used with other filters "
                f"by {cls.__name__}.filter then it must be "
                "the first filter applied"
            )

        out = super(Constructs, self).filter_by_type(*types, todict=todict)

        if todict:
            return out

        out._prefiltered = self.shallow_copy()
        out._filters_applied = self.filters_applied() + (
            {"filter_by_type": types},
        )

        return out

    def filter_by_type(self, *types, todict=False, cache=None):
        """Select metadata constructs by type.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `filter_by_axis`, `filter_by_data`,
                     `filter_by_key`, `filter_by_measure`,
                     `filter_by_method`, `filter_by_naxes`,
                     `filter_by_ncdim`, `filter_by_ncvar`,
                     `filter_by_identity`, `filter_by_property`,
                     `filters_applied`, `inverse_filter`, `unfilter`

        :Parameters:

            types: optional
                Select constructs that have are of any of the given
                types.

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

            {{todict: `bool`, optional}}

            {{cache: optional}}

        :Returns:

            `Constructs` or `dict`
                The selected constructs and their construct keys.

        **Examples:**

        Select dimension coordinate constructs:

        >>> d = c.filter_by_type('dimension_coordinate')

        Select dimension coordinate and field ancillary constructs:

        >>> d = c.filter_by_type('dimension_coordinate', 'field_ancillary')

        """
        return self._filter_by_type(self, self, todict, cache, *types)

    def filters_applied(self):
        """A history of filters that have been applied.

        The history is returned in a tuple. The last element of the
        tuple describes the last filter applied. Each element is a
        single-entry dictionary whose key is the name of the filter
        method that was used, with a value that gives the arguments
        that were passed to the call of that method. If no filters
        have been applied then the tuple is empty.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `filter_by_axis`, `filter_by_data`,
                     `filter_by_key`, `filter_by_measure`,
                     `filter_by_method`, `filter_by_naxes`,
                     `filter_by_identity`, `filter_by_ncdim`,
                     `filter_by_ncvar`, `filter_by_property`,
                     `filter_by_type`, `inverse_filter`, `unfilter`

        :Returns:

            `tuple`
                The history of filters that have been applied, ordered
                from first to last. If no filters have been applied
                then the tuple is empty.


        **Examples:**

        >>> print(c)
        {'auxiliarycoordinate0': <{{repr}}AuxiliaryCoordinate: latitude(10, 9) degrees_N>,
         'auxiliarycoordinate1': <{{repr}}AuxiliaryCoordinate: longitude(9, 10) degrees_E>,
         'coordinatereference1': <{{repr}}CoordinateReference: grid_mapping_name:rotated_latitude_longitude>,
         'dimensioncoordinate1': <{{repr}}DimensionCoordinate: grid_latitude(10) degrees>,
         'dimensioncoordinate2': <{{repr}}DimensionCoordinate: grid_longitude(9) degrees>,
         'domainaxis1': <{{repr}}DomainAxis: size(10)>,
         'domainaxis2': <{{repr}}DomainAxis: size(9)>}
        >>> c.filters_applied()
        ()
        >>> c = c.filter_by_type('dimension_coordinate', 'auxiliary_coordinate')
        >>> c.filters_applied()
        ({'filter_by_type': ('dimension_coordinate', 'auxiliary_coordinate')},)
        >>> c = c.filter_by_property(units='degrees')
        >>> c.filters_applied()
        ({'filter_by_type': ('dimension_coordinate', 'auxiliary_coordinate')},
         {'filter_by_property': ((), {'units': 'degrees'})})
        >>> c = c.filter_by_property('or', standard_name='grid_latitude', axis='Y')
        >>> c.filters_applied()
        ({'filter_by_type': ('dimension_coordinate', 'auxiliary_coordinate')},
         {'filter_by_property': ((), {'units': 'degrees'})},
         {'filter_by_property': (('or',), {'axis': 'Y', 'standard_name': 'grid_latitude'})})
        >>> print(c)
        Constructs:
        {'dimensioncoordinate1': <{{repr}}DimensionCoordinate: grid_latitude(10) degrees>}

        """
        filters = getattr(self, "_filters_applied", None)
        if filters is None:
            return ()

        return deepcopy(filters)

    def clear_filters_applied(self):
        """Remove the history of filters that have been applied.

        The removed history is returned in a tuple. The last element
        of the tuple describes the last filter applied. Each element
        is a single-entry dictionary whose key is the name of the
        filter method that was used, with a value that gives the
        arguments that were passed to the call of that method. If no
        filters have been applied then the tuple is empty.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `filter_by_axis`, `filter_by_data`,
                     `filter_by_key`, `filter_by_measure`,
                     `filter_by_method`, `filter_by_naxes`,
                     `filter_by_identity`, `filter_by_ncdim`,
                     `filter_by_ncvar`, `filter_by_property`,
                     `filter_by_type`, `inverse_filter`, `unfilter`

        :Returns:

            `tuple`
                The removed history of filters that have been applied,
                ordered from first to last. If no filters have been
                applied then the tuple is empty.


        **Examples:**

        >>> c.filters_applied()
        ({'filter_by_naxes': (3, 1)},
         {'filter_by_identity': ('grid_longitude',)})
        >>> c.clear_filters_applied()
        ({'filter_by_naxes': (3, 1)},
         {'filter_by_identity': ('grid_longitude',)})
        >>> c.filters_applied()
        ()

        """
        out = self.filters_applied()
        self._filters_applied = None
        self._prefiltered = None
        return out

    def inverse_filter(self, depth=None):
        """Return the inverse of previous filters.

        By default, the inverse comprises all of the constructs that
        were *not* selected by all previously applied filters. If no
        filters have been applied, then this will result in empty
        `Constructs` instance being returned.

        If the *depth* parameter is set to *N* then the inverse is
        relative to the constructs selected by the *N*-th most
        recently applied filter.

        A history of the filters that have been applied is returned in
        a `tuple` by the `filters_applied` method. The last element of
        the tuple describes the last filter applied. If no filters
        have been applied then the tuple is empty.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `filter_by_axis`, `filter_by_data`,
                     `filter_by_key`, `filter_by_measure`,
                     `filter_by_method`, `filter_by_naxes`,
                     `filter_by_identity`, `filter_by_ncdim`,
                     `filter_by_ncvar`, `filter_by_property`,
                     `filter_by_type`, `filters_applied`, `unfilter`

        :Parameters:

             depth: `int`, optional
                If set to ``N`` then the inverse is relative to the
                constructs selected by the ``N``-th most recently
                applied filter. By default the inverse is relative to
                the constructs selected by all previously applied
                filters. ``N`` may be larger than the total number of
                filters applied, which results in the default
                behaviour.

        :Returns:

            `Constructs`
                The constructs, and their construct keys, that were
                not selected by the last filter applied. If no
                filtering has been applied, or the last filter was an
                inverse filter, then an empty `Constructs` instance is
                returned.

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
        >>> print(c.inverse_filter())
        Constructs:
        {}
        >>> d = c.filter_by_type('dimension_coordinate', 'cell_method')
        >>> print(d)
        Constructs:
        {'cellmethod0': <{{repr}}CellMethod: area: mean>,
         'dimensioncoordinate0': <{{repr}}DimensionCoordinate: latitude(5) degrees_north>,
         'dimensioncoordinate1': <{{repr}}DimensionCoordinate: longitude(8) degrees_east>,
         'dimensioncoordinate2': <{{repr}}DimensionCoordinate: time(1) days since 2018-12-01 >}
        >>> print(d.inverse_filter())
        Constructs:
        {'domainaxis0': <{{repr}}DomainAxis: size(5)>,
         'domainaxis1': <{{repr}}DomainAxis: size(8)>,
         'domainaxis2': <{{repr}}DomainAxis: size(1)>}
        >>> e = d.filter_by_method('mean')
        >>> print(e)
        Constructs:
        {'cellmethod0': <{{repr}}CellMethod: area: mean>}
        >>> print(e.inverse_filter(1))
        Constructs:
        {'dimensioncoordinate0': <{{repr}}DimensionCoordinate: latitude(5) degrees_north>,
         'dimensioncoordinate1': <{{repr}}DimensionCoordinate: longitude(8) degrees_east>,
         'dimensioncoordinate2': <{{repr}}DimensionCoordinate: time(1) days since 2018-12-01 >}
        >>> print(e.inverse_filter())
        Constructs:
        {'dimensioncoordinate0': <{{repr}}DimensionCoordinate: latitude(5) degrees_north>,
         'dimensioncoordinate1': <{{repr}}DimensionCoordinate: longitude(8) degrees_east>,
         'dimensioncoordinate2': <{{repr}}DimensionCoordinate: time(1) days since 2018-12-01 >,
         'domainaxis0': <{{repr}}DomainAxis: size(5)>,
         'domainaxis1': <{{repr}}DomainAxis: size(8)>,
         'domainaxis2': <{{repr}}DomainAxis: size(1)>}
        >>> print(e.inverse_filter(1).inverse_filter())
        Constructs:
        {'cellmethod0': <{{repr}}CellMethod: area: mean>,
         'domainaxis0': <{{repr}}DomainAxis: size(5)>,
         'domainaxis1': <{{repr}}DomainAxis: size(8)>,
         'domainaxis2': <{{repr}}DomainAxis: size(1)>}

        """
        out = self.unfilter(depth=depth)

        if depth:
            if "inverse_filter" in self.filters_applied()[-1]:
                filters = out.filters_applied()
                d = 1
                while True:
                    if d > len(filters) or "inverse_filter" not in filters[-d]:
                        break

                    d += 1

                if d > 1:
                    out = self.unfilter(depth=depth + d - 1)

                return out

        for key in self:
            out._pop(key)

        out._filters_applied = self.filters_applied() + (
            {"inverse_filter": ()},
        )

        out._prefiltered = self.shallow_copy()

        return out

    def shallow_copy(self, _ignore=None):
        """Return a shallow copy.

        ``f.shallow_copy()`` is equivalent to ``copy.copy(f)``.

        Any in-place changes to the actual constructs of the copy will
        not be seen in the original `{{class}}` object, and vice
        versa, but the copy is otherwise independent of its parent.

        .. versionadded:: (cfdm) 1.7.0

        :Returns:

            `Constructs`
                The shallow copy.

        **Examples:**

        >>> g = f.shallow_copy()

        """
        out = super().shallow_copy(_ignore=_ignore)

        prefiltered = getattr(self, "_prefiltered", None)
        if prefiltered is not None:
            out._prefiltered = prefiltered.shallow_copy()
            out._filters_applied = self._filters_applied

        return out

    def unfilter(self, depth=None):
        """Return the constructs that existed prior to previous filters.

        By default, the unfiltered constructs are those that existed
        before all previously applied filters.

        If the *depth* parameter is set to *N* then the unfiltered
        constructs are those that existed before the *N*-th most
        recently applied filter.

        A history of the filters that have been applied is returned in
        a `tuple` by the `filters_applied` method. The last element of
        the tuple describes the last filter applied. If no filters
        have been applied then the tuple is empty.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `filter_by_axis`, `filter_by_data`,
                     `filter_by_key`, `filter_by_measure`,
                     `filter_by_method`, `filter_by_naxes`,
                     `filter_by_identity`, `filter_by_ncdim`,
                     `filter_by_ncvar`, `filter_by_property`,
                     `filter_by_type`, `filters_applied`,
                     `inverse_filter`

        :Parameters:

             depth: `int`, optional
                If set to ``N`` then return the constructs selected by
                the ``N``-th most recently applied filter. By default
                the constructs from before all previously applied
                filters are returned. ``N`` may be larger than the
                total number of filters applied, which results in the
                default behaviour.

        :Returns:

            `Constructs`
                The constructs, and their construct keys, that existed
                before the last filter was applied. If no filters have
                been applied then all of the constructs are returned.

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
        >>> d = c.filter_by_type('dimension_coordinate', 'cell_method')
        >>> print(d)
        Constructs:
        {'cellmethod0': <{{repr}}CellMethod: area: mean>,
         'dimensioncoordinate0': <{{repr}}DimensionCoordinate: latitude(5) degrees_north>,
         'dimensioncoordinate1': <{{repr}}DimensionCoordinate: longitude(8) degrees_east>,
         'dimensioncoordinate2': <{{repr}}DimensionCoordinate: time(1) days since 2018-12-01 >}
        >>> d.unfilter().equals(c)
        True
        >>> e = d.filter_by_method('mean')
        >>> print(e)
        Constructs:
        {'cellmethod0': <{{repr}}CellMethod: area: mean>}
        >>> c.unfilter().equals(c)
        True
        >>> c.unfilter(0).equals(c)
        True
        >>> e.unfilter().equals(c)
        True
        >>> e.unfilter(1).equals(d)
        True
        >>> e.unfilter(2).equals(c)
        True

        If no filters have been applied then the unfiltered constructs are
        unchanged:

        >>> c.filters_applied()
        ()
        >>> c.unfilter().equals(c)
        True

        """
        out = self

        if depth is None:
            while True:
                prefiltered = getattr(out, "_prefiltered", None)
                if prefiltered is None:
                    break

                out = prefiltered
        else:
            for _ in range(depth):
                prefiltered = getattr(out, "_prefiltered", None)
                if prefiltered is not None:
                    out = prefiltered
                else:
                    break

        return out.shallow_copy()
