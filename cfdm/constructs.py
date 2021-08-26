import logging
from itertools import zip_longest
from re import Pattern

from . import core, mixin
from .core.functions import deepcopy
from .decorators import _manage_log_level_via_verbosity

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
    "air_temperature": ``d = c('air_temperature')``.

    Note that ``c(*identities, **filter_kwargs)`` is equivalent to
    ``c.filter(filter_by_identity=identities, **filter_kwargs)``.

    .. versionadded:: (cfdm) 1.7.0

    """

    def __call__(self, *identities, **filter_kwargs):
        """Select metadata constructs by identity.

        Calling a `Constructs` instance selects metadata constructs by
        identity and is an alias for the `filter_by_identity`
        method. For example, to select constructs that have an
        identity of 'air_temperature': ``d = c('air_temperature')``.

        Note that ``c(*identities, **filter_kwargs)`` is equivalent to
        ``c.filter(filter_by_identity=identities, **filter_kwargs)``.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `filter_by_identity`, `filter`

        :Parameters:

            identities: optional
                Select constructs that have an identity, defined by
                their `!identities` methods, that matches any of the
                given values.

                {{value match}}

                {{displayed identity}}

            {{filter_kwargs: optional}} Also to configure the returned value.

                .. versionadded:: (cfdm) 1.8.9.0

        :Returns:

            `Constructs`
                The selected constructs and their construct keys.

        **Examples:**

        See `filter_by_identity` and `filter` for examples.

        """
        if identities:
            if "filter_by_identity" in filter_kwargs:
                raise TypeError(
                    f"Can't set {self.__class__.__name__}.__call__() "
                    "keyword argument 'filter_by_identity' when "
                    "positional *identities arguments are also set"
                )

            # Ensure that filter_by_identity is the last filter
            # applied, as it's the most expensive.
            filter_kwargs["filter_by_identity"] = identities

        return self.filter(**filter_kwargs)

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
        constructs = self._constructs

        ignore = self._ignore

        out = {
            axes: {
                ctype: {}
                for ctype in array_constructs
                if ctype not in ignore and constructs.get(ctype)
            }
            for axes in data_axes.values()
        }

        for cid, construct in self.filter_by_data(todict=True).items():
            axes = data_axes.get(cid)
            out[axes][construct_type[cid]][cid] = construct

        return out

    def _del_construct(self, key, default=ValueError()):
        """Remove a metadata construct.

        If a domain axis construct is selected for removal then it can't
        be spanned by any metdata construct data arrays, nor be referenced
        by any cell method constructs.

        However, a domain ancillary construct may be removed even if it is
        referenced by coordinate reference construct. In this case the
        reference is replace with `None`.

        If a climatological time cell method construct is removed then the
        climatological status of its corresponding coordinate constructs
        will be reviewed.

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

        >>> x = c._del_construct('auxiliarycoordinate2')

        """
        out = super()._del_construct(key, default=default)

        try:
            is_cell_method = out.construct_type == "cell_method"
        except AttributeError:
            is_cell_method = False

        if is_cell_method:
            # --------------------------------------------------------
            # Since a cell method construct was deleted, check to see
            # if it was for climatological time, and if so reset the
            # climatology status of approriate coordinate constructs.
            # --------------------------------------------------------
            qualifiers = out.qualifiers()
            if "within" in qualifiers or "over" in qualifiers:
                axes = out.get_axes(default=())
                if len(axes) == 1 and axes[0] not in self.filter_by_type(
                    "domain_axis", todict=True
                ):
                    coordinates = {}
                    for ckey, c in self.filter_by_type(
                        "dimension_coordinate",
                        "auxiliary_coordinate",
                        todict=True,
                    ).items():
                        if axes != self.data_axes().get(ckey, ()):
                            continue

                        # This coordinate construct spans the deleted
                        # cell method axes, so unset its climatology
                        # setting.
                        c.set_climatology(False)
                        coordinates[ckey] = c

                    # Reset the climatology settings of all the
                    # modified coordinate constructs. Do this because
                    # there may still be non-deleted cell methods for
                    # the same axes that still define climatological
                    # time.
                    if coordinates:
                        self._set_climatology(coordinates=coordinates)

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
        cell_methods0 = self._construct_dict("cell_method")
        cell_methods1 = other._construct_dict("cell_method")

        len0 = len(cell_methods0)
        if len0 != len(cell_methods1):
            logger(
                "Different numbers of cell methods: "
                f"{cell_methods0!r} != {cell_methods1!r}"
            )  # pragma: no cover
            return False

        if not len0:
            return True

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
                    f"{cm0.__class__.__name__}: Different cell methods "
                    f"(mismatched axes):\n  {cell_methods0}\n  {cell_methods1}"
                )  # pragma: no cover
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
                            f"{cm0.__class__.__name__}: Different cell "
                            "methods (mismatched axes):\n  "
                            f"{ cell_methods0}\n  {cell_methods1}"
                        )  # pragma: no cover
                        return False
                    elif axis0 == axis1:
                        # axes0 and axis 1 are identical standard
                        # names
                        axes1.remove(axis1)
                        indices.append(cm1.get_axes(()).index(axis1))
                    elif axis1 is None:
                        # axis1
                        logger.info(
                            f"{cm0.__class__.__name__}: Different cell "
                            "methods (mismatched axes):\n  "
                            f"{cell_methods0}\n  {cell_methods1}"
                        )  # pragma: no cover
                        return False

            if len(cm1.get_axes(())) != len(indices):
                logger.info(
                    f"{cm0.__class__.__name__}: [4] Different cell methods "
                    f"(mismatched axes):\n  {cell_methods0}\n  {cell_methods1}"
                )  # pragma: no cover
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
                    f"{cm0.__class__.__name__}: Different cell methods: "
                    f"{cell_methods0!r}, {cell_methods1!r}"
                )  # pragma: no cover
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
                f"{self.__class__.__name__}: Different numbers of coordinate "
                f"reference constructs: {len(refs0)} != {len(refs1)}"
            )  # pragma: no cover

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
                        f"{self.__class__.__name__}: Comparing {ref0!r}, "
                        f"{ref1!r}: "
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
                        f"{self.__class__.__name__}: No match for {ref0!r}"
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
        self_sizes = sorted([d.get_size() for d in domain_axes.values()])

        domain_axes = other._construct_dict("domain_axis")
        other_sizes = sorted([d.get_size() for d in domain_axes.values()])

        if self_sizes != other_sizes:
            # There is not a 1-1 correspondence between axis sizes
            logger.info(
                f"{self.__class__.__name__}: Different domain axis sizes: "
                f"{self_sizes} != {other_sizes}"
            )  # pragma: no cover
            return False

        return True

    def _set_climatology(self, cell_methods=None, coordinates=None):
        """Set the climatology flag on approriate coordinate constructs.

        The setting is based on the cell method constructs.

        .. versionadded:: (cfdm) 1.9.0.0

        :Parameters:

            cell_methods: `dict`, optional
                TODO

            coordinates: `dict`, optional
                TODO

        :Returns:

            `list` of `str`
                The domain axis construct identifiers of all
                climatological time axes. The list may contain axis
                duplications.

        """
        out = []

        domain_axes = self.filter_by_type("domain_axis", todict=True)

        if coordinates:
            cell_methods = self.filter_by_type("cell_method", todict=True)
        elif cell_methods:
            coordinates = self.filter_by_type(
                "dimension_coordinate", "auxiliary_coordinate", todict=True
            )
        else:
            cell_methods = self.filter_by_type("cell_method", todict=True)
            coordinates = self.filter_by_type(
                "dimension_coordinate", "auxiliary_coordinate", todict=True
            )

        for key, cm in cell_methods.items():
            qualifiers = cm.qualifiers()
            if not ("within" in qualifiers or "over" in qualifiers):
                continue

            axes = cm.get_axes(default=())
            if len(axes) != 1:
                continue

            axis = axes[0]
            if axis not in domain_axes:
                continue

            # Still here? Then this axis is a climatological time axis
            out.append(axis)

            # Flag the appropriate coordinates as being for
            # climatological time.
            axes = set(axes)
            for ckey, c in coordinates.items():
                if axes != set(self.data_axes().get(ckey, ())):
                    # Construct does not span the cell method axes
                    continue

                # Construct spans the correct axes and has reference
                # time units
                c.set_climatology(True)

        return out

    def _set_construct(self, construct, key=None, axes=None, copy=True):
        """Set a metadata construct.

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
                exisiting construct will be replaced.

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

        >>> key = f._set_construct(c)
        >>> key = f._set_construct(c, copy=False)
        >>> key = f._set_construct(c, axes='domainaxis2')
        >>> key = f._set_construct(c, key='cellmeasure0')

        """
        if copy:
            # Create a deep copy of the construct
            construct = construct.copy()

        key = super()._set_construct(construct, key=key, axes=axes, copy=False)

        # Set any appropriate climatology flags
        construct_type = construct.construct_type
        if construct_type in ("dimension_coordinate", "auxiliary_coordinate"):
            self._set_climatology(coordinates={key: construct})
        elif construct_type == "cell_method":
            self._set_climatology(cell_methods={key: construct})

        # Return the identifier of the construct
        return key

    # ----------------------------------------------------------------
    # Methods
    # ----------------------------------------------------------------
    def _filter_convert_to_domain_axis(
        self, values, check_axis_identities=True
    ):
        """Convert values to domain axis construct identifiers.

        If possible, convert each value from a field data array index
        position to domain axis construct identifiers; or 1-d
        coordinate construct identifier to a domain axis identifier of
        the spanned domain axis construct.

        .. note:: If *values* is an empty sequence then calling this
                  method has no effect, but still takes some time to
                  execute. In other words, if performance is an issue
                  then avoid calling this method when *values* is
                  empty.

        .. versionadded:: (cfdm) 1.8.9.0

        :Parameters:

            values: sequence

            check_axis_identities: `bool` optional
                If True then check for domain axis identities.

        :Returns:

            `list`
                The parsed values

        """
        # Get the original unfiltered constructs. This gives access to
        # the full collection of domain axis, dimension coordinate and
        # auxiliary coordinate constructs.
        unfiltered = self.unfilter(copy=False)
        unfiltered_domain_axes = unfiltered._constructs.get("domain_axis", ())
        unfiltered_data_axes = unfiltered._construct_axes

        field_data = self._field_data_axes

        values2 = []
        for value in values:
            if value in unfiltered_domain_axes:
                # This value is already a domain axis construct
                # identifier
                values2.append(value)
                continue

            if field_data:
                # Try to convert a field data array index position to
                # a domain axis identifier
                try:
                    value = field_data[value]
                except TypeError:
                    pass
                except IndexError:
                    continue
                else:
                    values2.append(value)
                    continue

            # Try to convert a 1-d coordinate into a domain axis
            # identifier
            c = unfiltered.filter(
                filter_by_type=(
                    "dimension_coordinate",
                    "auxiliary_coordinate",
                ),
                filter_by_naxes=(1,),
                filter_by_identity=(value,),
                todict=True,
            )
            if c:
                c_axes = [unfiltered_data_axes[key][0] for key in c]
                if len(set(c_axes)) == 1:
                    value = c_axes[0]
                    values2.append(value)

                continue

            if check_axis_identities:
                # Try to convert a domain axis identity into a domain
                # axis identifier
                c = self.filter(
                    filter_by_type=("domain_axis",),
                    filter_by_identity=(value,),
                    todict=True,
                )
                if len(c) == 1:
                    key, _ = c.popitem()
                    values2.append(key)

        return values2

    @classmethod
    def _filter_parse_args(
        cls,
        method,
        args,
        todict=False,
        axis_mode=None,
        property_mode=None,
        _identity_config=None,
    ):
        """Parse arguments destined for a filter method.

        Specifically transforms the arguments to a filter method
        (e.g. `filter_by_property`) so that they can be used in the
        corresponding underscore filter method
        (e.g. `_filter_by_property`).

        .. versionadded:: (cfdm) 1.8.9.0

        :Parameters:

            method: `str`
                The name of a filter method (e.g. "filter_by_data").

            args: sequence or `dict`
                The input arguments for the filter method defined by
                *method*.

            todict: `bool`
                The value of the filter method's *todict* parameter.

            axis_mode: `str`, optional
                Provide a value for the *axis_mode* parameter of the
                `filter_by_axis` method.

            property_mode: `str`, optional
                Provide a value for the *property_mode* parameter of
                the `filter_by_property` method.

            _identity_config: optional
                Provide a value for the *_config* parameter of the
                `filter_by_identity` method.

        :Returns:

            `tuple`
                The parsed positional arguments for corresponding
                underscore filter method.

        """
        out = (args, todict)

        if method == "filter_by_type":
            return out

        if method == "filter_by_identity":
            out += (_identity_config,)
        elif method == "filter_by_axis":
            out += (axis_mode,)
        elif method == "filter_by_property":
            out += ((property_mode,),)

        return out

    @classmethod
    def _filter_preprocess(cls, arg, todict=False, filter_applied=None):
        """Preprocess a `dict` or `Constructs` prior to filtering.

        .. versionadded:: (cfdm) 1.8.9.0

        :Parameters:

            arg: `Constructs` or `dict`
                Either a `Constructs` object or its dictionary
                representation.

            todict: `bool`, optional
                If True and *arg* is a `Constructs` object, then
                return its dictionary representation.

            filter_applied: `dict` optional
                If *todict* is False and *arg* is a `Constructs`
                object, then add this record to the `_filters_applied`
                attribute.

        :Returns:

            `Constructs` or `dict`, and its pop method
                If *arg* is a `Constructs` object, then either a
                shallow copy or its dictionary representation is
                returned. If *arg* is a `dict` then it is returned
                unchanged. In addtion, the "pop" method of the object
                also returned.

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

    @classmethod
    def _matching_values(cls, value0, construct, value1, basic=False):
        """Whether or not two values are the same.

        :Parameters:

            value0:
                The first value to be matched. Could be a `re.Pattern`
                object.

            construct:
                The construct whose `_equals` method might be used to
                determine whether values can be considered to match.

            value1:
                The second value to be matched.

            basic: `bool`
                If True then replace the expensive `_equals` method
                with ``==``. In this case, *construct* is not used and
                may take any value.

        :Returns:

            `bool`
                Whether or not the two values match.

        """
        if isinstance(value0, Pattern):
            try:
                return value0.search(value1)
            except TypeError:
                return False

        if basic:
            return value0 == value1

        return construct._equals(value1, value0)

    @classmethod
    def _short_iteration(cls, x):
        """The default short cicuit test.

        If this method returns True then only ther first identity
        return by the construct's `!identities` method will be
        checked.

        See `_filter_by_identity` for details.

        .. versionadded:: (cfdm) 1.8.9.0

        :Parameters:

            x: `str`
                The value against which the construct's identities are
                being compared.

        :Returns:

            `bool`
                 Returns `True` if a construct's `identities` method
                 is to short circuit after the first identity is
                 computed, otherwise `False`.

        """
        return (
            isinstance(x, str)
            and "=" not in x
            and ":" not in x
            and "%" not in x
        )

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

    def domain_axes(self, *identities, **filter_kwargs):
        """Return domain axis constructs.

        .. versionadded:: (cfdm) 1.8.9.0

        .. seealso:: `constructs`

        :Parameters:

            identities: `tuple`, optional
                Select domain axis constructs that have an identity,
                defined by their `!identities` methods, that matches
                any of the given values.

                Additionally, the values are matched against construct
                identifiers, with or without the ``'key%'`` prefix.

                Additionally, if for a given ``value``,
                ``c.filter(filter_by_type=["dimension_coordinate",
                "auxiliary_coordinate"], filter_by_naxes=(1,),
                filter_by_identity=(value,))`` returns 1-d coordinate
                constructs that all span the same domain axis
                construct then that domain axis construct is
                selected. See `filter` for details.

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
        cached = filter_kwargs.get("cached")
        if cached is not None:
            return cached

        if filter_kwargs:
            if "filter_by_type" in filter_kwargs:
                raise TypeError(
                    "domain_axes() got an unexpected keyword argument "
                    "'filter_by_type'"
                )

            if identities:
                if "filter_by_identity" in filter_kwargs:
                    raise TypeError(
                        "Can't set domain_axes() keyword argument "
                        "'filter_by_identity' when positional *identities "
                        "arguments are also set"
                    )
            elif "filter_by_identity" in filter_kwargs:
                identities = filter_kwargs["filter_by_identity"]

        if identities:
            # Make sure that filter_by_identity is the last filter
            # applied
            filter_kwargs["filter_by_identity"] = identities

            out, keys, hits, misses = self.filter(
                filter_by_type=("domain_axis",),
                _identity_config={"return_matched": True},
                **filter_kwargs,
            )
            if out is not None:
                return out

            keys.update(
                self._filter_convert_to_domain_axis(
                    misses, check_axis_identities=False
                )
            )

            if not keys:
                # No keys were found but some criteria were provided,
                # so force filter_by_key to return no domain axis
                # constructs.
                keys = (None,)

            filter_kwargs = {
                "filter_by_key": keys,
                "todict": filter_kwargs.get("todict", False),
            }

        return self.filter(filter_by_type=("domain_axis",), **filter_kwargs)

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
                f"{self.__class__.__name__}: Incompatible type: "
                f"{other.__class__.__name__}"
            )  # pragma: no cover
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

        if len(axes_to_constructs0) != len(axes_to_constructs1):
            logger.info(
                f"{self.__class__.__name__}: Can't match constructs"
            )  # pragma: no cover
            return False

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
                            f"{self.__class__.__name__}: Different numbers "
                            f"of {construct_type} constructs: "
                            f"{len(role_constructs0)} != "
                            f"{len(role_constructs1)}"
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
                                f"{self.__class__.__name__}: Comparing "
                                f"{item0!r}, {item1!r}: "
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
                                f"{self.__class__.__name__}: Can't match "
                                f"{item0!r}"
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
                    f"{self.__class__.__name__}: Can't match constructs "
                    f"spanning axes {names}"
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
                        f"{self.__class__.__name__}: Ambiguous axis mapping "
                        f"({self.domain_axis_identity(axes0)} -> both "
                        f"{other.domain_axis_identity(axis1)} and "
                        f"{other.domain_axis_identity(axis0_to_axis1[axis0])})"
                    )  # pragma: no cover
                    if not _return_axis_map:
                        return False
                elif (
                    axis1 in axis1_to_axis0 and axis0 != axis1_to_axis0[axis1]
                ):
                    logger.info(
                        f"{self.__class__.__name__}: Ambiguous axis mapping "
                        f"({self.domain_axis_identity(axis0)} -> both "
                        f"{self.domain_axis_identity(axis1_to_axis0[axis0])} "
                        f"and {other.domain_axis_identity(axes1)})"
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
        cached=None,
        _identity_config={},
        **filters,
    ):
        """Select metadata constructs by a chain of filters.

        This method allows multiple filters defined by the
        "filter_by_*" methods to be chained in an alternative manner
        to calling the individual methods in sequence.

        For instance, to select the domain axis constructs with size
        73 or 96

           >>> c2 = c.filter(filter_by_type=['domain_axis'],
           ...               filter_by_size=[73, 96])

        is equivalent to

           >>> c2 = c.filter_by_type('domain_axis')
           >>> c2 = c2.filter_by_size(73, 96)

        When the results are requested as a dictionary as opposed to a
        `Constructs` object (see the *todict* parameter), using the
        `filter` method to call two or more filters is faster than
        calling the individual methods in sequence. For instance

           >>> d = c.filter(filter_by_type=['dimension_coordinate'],
           ...              filter_by_identity=['time'],
           ...              todict=True)

        is equivalent to, but faster than

           >>> c2 = c.filter_by_type('dimension_coordinate')
           >>> d = c2.filter_by_identity('time', todict=True)

        .. versionadded:: (cfdm) 1.8.9.0

        .. seealso:: `filter_by_axis`, `filter_by_data`,
                     `filter_by_identity`, `filter_by_key`,
                     `filter_by_measure`, `filter_by_method`,
                     `filter_by_identity`, `filter_by_naxes`,
                     `filter_by_ncdim`, `filter_by_ncvar`,
                     `filter_by_property`, `filter_by_type`,
                     `filters_applied`, `inverse_filter`, `unfilter`,
                     `clear_filters_applied`

        :Parameters:

            filters: optional
                Keyword arguments defining the filters to apply. Each
                filter keyword defines a filter method, and its value
                provides the arguments for that method.

                For instance, ``filter_by_type=['domain_axis']`` will
                cause the `filter_by_type` method to be called with
                positional arguments ``*['domain_axis']``.

                The filters are applied in the same order that the
                keyword arguments appear.

                Valid keywords and their values are:

                ======================  ==============================
                Keyword                 Value
                ======================  ==============================
                ``filter_by_axis``      A sequence as expected by the
                                        *axes* parameter of
                                        `filter_by_axis`

                ``filter_by_identity``  A sequence as expected by the
                                        *identities* parameter of
                                        `filter_by_identity`

                ``filter_by_key``       A sequence as expected by the
                                        *keys* parameter of
                                        `filter_by_key`

                ``filter_by_measure``   A sequence as expected by the
                                        *measures* parameter of
                                        `filter_by_measure`

                ``filter_by_method``    A sequence as expected by the
                                        *methods* parameter of
                                        `filter_by_method`

                ``filter_by_naxes``     A sequence as expected by the
                                        *naxes* parameter of
                                        `filter_by_naxes`

                ``filter_by_ncdim``     A sequence as expected by the
                                        *ncdims* parameter of
                                        `filter_by_ncdim`

                ``filter_by_ncvar``     A sequence as expected by the
                                        *ncvars* parameter of
                                        `filter_by_ncvar`

                ``filter_by_size``      A sequence as expected by the
                                        *sizes* parameter of
                                        `filter_by_size`

                ``filter_by_type``      A sequence as expected by the
                                        *types* parameter of
                                        `filter_by_type`

                ``filter_by_property``  A dictionary as expected by
                                        the *properties* parameter of
                                        `filter_by_property`

                ``filter_by_data``      Any value is allowed which
                                        will be ignored, as
                                        `filter_by_data` does not have
                                        any positional arguments.
                ======================  ==============================

            axis_mode: `str`, optional
                Provide a value for the *axis_mode* parameter of the
                `filter_by_axis` method. By default *axis_mode* is
                ``'and'``.

            property_mode: `str`, optional
                Provide a value for the *property_mode* parameter of
                the `filter_by_property` method. By default
                *property_mode* is ``'and'``.

            {{todict: `bool`, optional}}

            {{cached: optional}}

            _identity_config: optional
                Provide a value for the *_config* parameter of the
                `filter_by_identity` method.

        :Returns:

            `Constructs` or `dict` or *cached*
                The selected constructs, or a cached valued.

        """
        if cached is not None:
            return cached

        if not filters:
            out, _ = self._filter_preprocess(self, todict=todict)
            return out

        out = self

        for method, args in filters.items():
            try:
                filter_method = getattr(self, "_" + method)
            except AttributeError:
                raise TypeError(
                    f"{self.__class__.__name__}.filter() has an unexpected "
                    f"keyword argument {method!r}"
                )

            args = self._filter_parse_args(
                method,
                args,
                todict=todict,
                axis_mode=axis_mode,
                property_mode=property_mode,
                _identity_config=_identity_config,
            )

            out = filter_method(out, *args)

        return out

    def _filter_by_axis(
        self,
        arg,
        axes,
        todict,
        axis_mode,
    ):
        """Worker function for `filter_by_axis` and `filter`.

        See `filter_by_axis` for details.

        .. versionadded:: (cfdm) 1.8.9.0

        """
        # Parse the axis_mode parameter
        _or = False
        _exact = False
        _subset = False
        if axis_mode in ("and", None):
            pass
        elif axis_mode == "or":
            _or = True
        elif axis_mode == "exact":
            _exact = True
        elif axis_mode == "subset":
            _subset = True
        elif axes:
            raise ValueError(
                f"{self.__class__.__name__}.filter_by_axis() has incorrect "
                f"'axis_mode' value {axis_mode!r}. "
                "Expected one of 'or', 'and', 'exact', 'subset'"
            )

        filter_applied = {"filter_by_axis": (axes, {"axis_mode": axis_mode})}

        if not axes:
            # Return all constructs that could have data if no axes
            # have been provided
            return self._filter_by_data(
                arg, None, todict, filter_applied=filter_applied
            )

        out, pop = self._filter_preprocess(
            arg,
            filter_applied=filter_applied,
            todict=todict,
        )

        # Convert values to domain axis construct identifiers, if any
        # can be.
        axes2 = self._filter_convert_to_domain_axis(
            axes, check_axis_identities=True
        )

        if not axes2:
            # No arguments found unique domain axis constructs
            if isinstance(out, dict):
                out = {}
            else:
                out._clear()

            return out

        axes = set(axes2)

        data_axes = self._construct_axes

        for cid in tuple(out):
            x = data_axes.get(cid)
            if x is None:
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
                pop(cid)

        return out

    def filter_by_axis(
        self,
        *axes,
        axis_mode="and",
        todict=False,
        cached=None,
    ):
        """Select metadata constructs by axes spanned by their data.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `filter`, `filters_applied`, `inverse_filter`,
                     `clear_filters_applied`, `unfilter`

        :Parameters:

            mode: `str`
                Deprecated at version 1.8.9.0. Use the *axis_mode*
                parameter instead.

            axes: optional
                Select constructs that whose data spans the domain
                axis constructs specified by the given values. A value
                may be:

                * A domain axis construct identifier, with or without
                  the ``'key%'`` prefix.

                * The unique domain axis construct spanned by all of
                  the 1-d coordinate constructs returned by, for a
                  given ``value``,
                  ``c.filter(filter_by_type=["dimension_coordinate",
                  "auxiliary_coordinate"], filter_by_naxes=(1,),
                  filter_by_identity=(value,))``. See `filter` for
                  details.

                * If there is an associated `Field` data array and a
                  value matches the integer position of an array
                  dimension, then the corresponding domain axis
                  construct is specified.

                * A unique domain axis construct identity, defined by
                  its `!identities` methods. In this case a value may
                  be any object that can match via the ``==``
                  operator, or a `re.Pattern` object that matches via
                  its `~re.Pattern.search` method.

                If no axes are provided then all constructs that do,
                or could have data, spanning any domain axes
                constructs, are selected.

            axis_mode: `str`
                Define the relationship between the given domain axes
                and the constructs' data.

                ===========  =========================================
                *axis_mode*  Description
                ===========  =========================================
                ``'and'``    A construct is selected if it spans *all*
                             of the given domain axes, *and possibly
                             others*.

                ``'or'``     A construct is selected if it spans *any*
                             of the domain axes, *and possibly
                             others*.

                ``exact``    A construct is selected if it spans *all*
                             of the given domain axes, *and no
                             others*.

                ``subset``   A construct is selected if it spans *a
                             subset* of the given domain axes, *and no
                             others*.
                ===========  =========================================

                By default *axis_mode* is ``'and'``.

            {{todict: `bool`, optional}}

                .. versionadded:: (cfdm) 1.8.9.0

            {{cached: optional}}

                .. versionadded:: (cfdm) 1.8.9.0

        :Returns:

            `Constructs` or `dict` or *cached*
                The selected constructs, or a cached valued.

        **Examples:**

        Select constructs whose data spans the "domainaxis1" domain
        axis construct:

        >>> d = c.filter_by_axis('domainaxis1')

        Select constructs whose data does not span the "domainaxis2"
        domain axis construct:

        >>> d = c.filter_by_axis('domainaxis2').inverse_filter()

        Select constructs whose data spans the "domainaxis1", but not
        the "domainaxis2" domain axis constructs:

        >>> d = c.filter_by_axis('domainaxis1')
        >>> d = d.filter_by_axis('domainaxis2')
        >>> d  = d.inverse_filter(1)

        Select constructs whose data spans the "domainaxis1" or the
        "domainaxis2" domain axis constructs:

        >>> d = c.filter_by_axis('domainaxis1', 'domainaxis2', axis_mode="or")

        """
        if cached is not None:
            return cached

        return self._filter_by_axis(self, axes, todict, axis_mode)

    def _filter_by_data(self, arg, ignored, todict, filter_applied=None):
        """Worker function for `filter_by_data` and `filter`.

        See `filter_by_data` for details.

        :Parameters:

            ignored:
                This paramaeter is always ignored, but needs to be set
                to something in order to satisfy with the `filter`
                API.

        .. versionadded:: (cfdm) 1.8.9.0

        """
        return self._filter_by_type(
            arg, self._array_constructs, todict, filter_applied=filter_applied
        )

    def filter_by_data(self, todict=False, cached=None):
        """Selects metadata constructs that could contain data.

        Selection is not based on whether they actually have data,
        rather by whether the construct supports the inclusion of
        data. For example, constructs selected by this method will all
        have a `!get_data` method.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `filter`, `filters_applied`, `inverse_filter`,
                     `clear_filters_applied`, `unfilter`

        :Parameters:

            {{todict: `bool`, optional}}

                .. versionadded:: (cfdm) 1.8.9.0

            {{cached: optional}}

                .. versionadded:: (cfdm) 1.8.9.0

        :Returns:

            `Constructs` or `dict` or *cached*
                The selected constructs, or a cached valued.

        **Examples:**

        Select constructs that could contain data:

        >>> d = c.filter_by_data()

        """
        if cached is not None:
            return cached

        return self._filter_by_data(self, None, todict, filter_applied=None)

    def _filter_by_identity(
        self,
        arg,
        identities,
        todict,
        _config,
    ):
        """Worker function for `filter_by_identity` and `filter`.

        See `filter_by_identity` for details.

        .. versionadded:: (cfdm) 1.8.9.0

        """
        out, pop = self._filter_preprocess(
            arg,
            filter_applied={"filter_by_identity": identities},
            todict=todict,
        )

        if not identities:
            # Return all constructs if no identities have been provided
            return out

        # ------------------------------------------------------------
        # The principle here is to iterate over as few individual
        # construct identities as possible, as these can be very
        # expensive to compute.
        # ------------------------------------------------------------
        return_matched = _config.get("return_matched")
        short_iteration = _config.get("short_iteration", self._short_iteration)
        identities_kwargs = _config.get("identities_kwargs", {})

        matched = set()
        hits = []

        # Process identities that are construct identifiers
        identities2 = []
        for value0 in identities:
            if isinstance(value0, str):
                if value0 in out:
                    matched.add(value0)
                    hits.append(value0)
                    continue
                elif value0.startswith("key%") and value0[4:] in out:
                    matched.add(value0[4:])
                    hits.append(value0)
                    continue

            identities2.append(value0)

        if identities2:
            if matched:
                constructs = {
                    cid: c for cid, c in out.items() if cid not in matched
                }
            else:
                constructs = out

            if "short" not in identities_kwargs:
                short = True
                for value0 in identities:
                    if not short_iteration(value0):
                        short = False
                        break

                identities_kwargs["short"] = short

            # Dictionary of construct identifiers and construct
            # identity generators
            generators = {
                cid: construct.identities(generator=True, **identities_kwargs)
                for cid, construct in constructs.items()
            }

            for values in zip_longest(*generators.values(), fillvalue=None):
                # Loop round the each construct's next identity
                for (cid, generator), value1 in zip(
                    generators.items(), values
                ):
                    if value1 is None:
                        # This construct has run out of identities
                        continue

                    # Loop round the given values
                    for value0 in identities:
                        if self._matching_values(
                            value0, None, value1, basic=True
                        ):
                            generator.close()
                            hits.append(value0)
                            matched.add(cid)
                            break

        if return_matched:
            hits = set(hits)
            misses = hits.symmetric_difference(identities)
        else:
            misses = False

        if not misses:
            if not matched:
                if isinstance(out, dict):
                    out = {}
                else:
                    out._clear()
            elif len(matched) <= len(out):
                for cid in tuple(out):
                    if cid not in matched:
                        pop(cid)

        if return_matched:
            if misses:
                out = None

            return out, matched, hits, misses

        return out

    def filter_by_identity(
        self,
        *identities,
        todict=False,
        cached=None,
        _config={},
    ):
        """Select metadata constructs by identity.

        Calling a `Constructs` instance is an alias for
        `filter_by_identity`.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `filter`, `filters_applied`, `inverse_filter`,
                     `clear_filters_applied`, `unfilter`

        :Parameters:

            identities: optional
                Select constructs that have an identity, defined by
                their `!identities` methods, that matches any of the
                given values.

            * A metadata construct identity.

              {{construct selection identity}}

            * The key of a metadata construct

            *Parameter example:*
              ``identity='latitude'``

                {{value match}}

                {{displayed identity}}

            {{todict: `bool`, optional}}

                .. versionadded:: (cfdm) 1.8.9.0

            {{cached: optional}}

                .. versionadded:: (cfdm) 1.8.9.0

            _config: optional
                Additional parameters for configuring the application
                of a construct's `identities` method.

                .. versionadded:: (cfdm) 1.8.9.0

        :Returns:

            `Constructs` or `dict` or *cached*
                The selected constructs, or a cached valued.

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
        if cached is not None:
            return cached

        return self._filter_by_identity(self, identities, todict, _config)

    def _filter_by_key(self, arg, keys, todict):
        """Worker function for `filter_by_key` and `filter`.

        See `filter_by_key` for details.

        .. versionadded:: (cfdm) 1.8.9.0

        """
        out, pop = self._filter_preprocess(
            arg,
            filter_applied={"filter_by_key": keys},
            todict=todict,
        )

        if not keys:
            return out

        for cid in tuple(out):
            if cid in keys:
                continue

            ok = False
            for value0 in keys:
                ok = self._matching_values(value0, None, cid, basic=True)
                if ok:
                    break

            if not ok:
                pop(cid)

        return out

    def filter_by_key(self, *keys, todict=False, cached=None):
        """Select metadata constructs by key.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `filter`, `filters_applied`, `inverse_filter`,
                     `clear_filters_applied`, `unfilter`

        :Parameters:

            key: optional
                Select constructs that have a construct identifier
                (e.g. ``'dimensioncoordinate1'``) that matches any of
                the given values.

                If no keys are provided then all constructs are
                selected.

                {{value match}}

            {{todict: `bool`, optional}}

                .. versionadded:: (cfdm) 1.8.9.0

            {{cached: optional}}

                .. versionadded:: (cfdm) 1.8.9.0

        :Returns:

            `Constructs` or `dict` or *cached*
                The selected constructs, or a cached valued.

        **Examples:**

        Select the construct with key 'domainancillary0':

        >>> d = c.filter_by_key('domainancillary0')

        Select the constructs with keys 'dimensioncoordinate1' or
        'fieldancillary0':

        >>> d = c.filter_by_key('dimensioncoordinate1', 'fieldancillary0')

        """
        if cached is not None:
            return cached

        return self._filter_by_key(self, keys, todict)

    def _filter_by_measure(self, arg, measures, todict):
        """Worker function for `filter_by_measure` and `filter`.

        See `filter_by_measure` for details.

        .. versionadded:: (cfdm) 1.8.9.0

        """
        out, pop = self._filter_preprocess(
            arg,
            filter_applied={"filter_by_measure": measures},
            todict=todict,
        )

        construct_type = self._construct_type
        if not measures:
            for cid in tuple(out):
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
                    ok = self._matching_values(
                        value0, None, value1, basic=True
                    )
                    if ok:
                        break

            if not ok:
                pop(cid)

        return out

    def filter_by_measure(self, *measures, todict=False, cached=None):
        """Select cell measure constructs by measure.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `filter`, `filters_applied`, `inverse_filter`,
                     `clear_filters_applied`, `unfilter`

        :Parameters:

            measures: optional
                Select cell measure constructs that have a measure,
                defined by their `!get_measure` methods, that matches
                any of the given values.

                If no measures are provided then all cell measure
                constructs are selected.

                {{value match}}

            {{todict: `bool`, optional}}

                .. versionadded:: (cfdm) 1.8.9.0

            {{cached: optional}}

                .. versionadded:: (cfdm) 1.8.9.0

        :Returns:

            `Constructs` or `dict` or *cached*
                The selected constructs, or a cached valued.

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
        if cached is not None:
            return cached

        return self._filter_by_measure(self, measures, todict)

    def _filter_by_method(self, arg, methods, todict):
        """Worker function for `filter_by_measure` and `filter`.

        See `filter_by_method` for details.

        .. versionadded:: (cfdm) 1.8.9.0

        """
        out, pop = self._filter_preprocess(
            arg,
            filter_applied={"filter_by_measure": methods},
            todict=todict,
        )

        construct_type = self._construct_type
        if not methods:
            for cid in tuple(out.keys()):
                if construct_type[cid] != "cell_method":
                    pop(cid)

            return out

        for cid, construct in tuple(out.items()):
            if construct_type[cid] != "cell_method":
                pop(cid)
                continue

            value1 = construct.get_method(None)

            ok = False
            if value1 is not None:
                for value0 in methods:
                    ok = self._matching_values(
                        value0, None, value1, basic=True
                    )
                    if ok:
                        break

            if not ok:
                pop(cid)

        return out

    def filter_by_method(self, *methods, todict=False, cached=None):
        """Select cell method constructs by method.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `filter`, `filters_applied`, `inverse_filter`,
                     `clear_filters_applied`, `unfilter`

        :Parameters:

            methods: optional
                Select cell method constructs that have a method,
                defined by their `!get_method` methods, that matches
                any of the given values.

                If no methods are provided then all cell method
                constructs are selected.

                {{value match}}

            {{todict: `bool`, optional}}

                .. versionadded:: (cfdm) 1.8.9.0

            {{cached: optional}}

                .. versionadded:: (cfdm) 1.8.9.0

        :Returns:

            `Constructs` or `dict` or *cached*
                The selected constructs, or a cached valued.

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
        if cached is not None:
            return cached

        return self._filter_by_method(self, methods, todict)

    def _filter_by_naxes(self, arg, naxes, todict):
        """Worker function for `filter_by_naxes` and `filter`.

        See `filter_by_naxes` for details.

        .. versionadded:: (cfdm) 1.8.9.0

        """
        if not naxes:
            # If no naxes have been provided then return all
            # constructs that could have data
            return self._filter_by_data(
                arg, None, todict, filter_applied={"filter_by_naxes": naxes}
            )

        out, pop = self._filter_preprocess(
            arg,
            filter_applied={"filter_by_naxes": naxes},
            todict=todict,
        )

        data_axes = self._construct_axes

        for key in tuple(out):
            x = data_axes.get(key)
            if x is None:
                pop(key)
                continue

            ok = len(x) in naxes
            if not ok:
                pop(key)

        return out

    def filter_by_naxes(self, *naxes, todict=False, cached=None):
        """Selects constructs by the number of axes their data spans.

        Specifically, selects metadata constructs by the number of
        domain axis constructs spanned by their data.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `filter`, `filters_applied`, `inverse_filter`,
                     `clear_filters_applied`, `unfilter`

        :Parameters:

            naxes: optional
                Select constructs that have data whose number of
                dimensions matches any of the given values.

                If no values are provided then all constructs that do
                or could have data, spanning any domain axes
                constructs, are selected.

                A value may be any object that can match an integer
                via ``==``.

            {{todict: `bool`, optional}}

                .. versionadded:: (cfdm) 1.8.9.0

            {{cached: optional}}

                .. versionadded:: (cfdm) 1.8.9.0

        :Returns:

            `Constructs` or `dict` or *cached*
                The selected constructs, or a cached valued.

        **Examples:**

        Select constructs that contain data that spans two domain axis
        constructs:

        >>> d = c.filter_by_naxes(2)

        Select constructs that contain data that spans one or two
        domain axis constructs:

        >>> d = c.filter_by_ncdim(1, 2)

        """
        if cached is not None:
            return cached

        return self._filter_by_naxes(self, naxes, todict)

    def _filter_by_ncdim(self, arg, ncdims, todict):
        """Worker function for `filter_by_ncdim` and `filter`.

        See `filter_by_ncdim` for details.

        .. versionadded:: (cfdm) 1.8.9.0

        """
        out, pop = self._filter_preprocess(
            arg,
            filter_applied={"filter_by_ncdim": ncdims},
            todict=todict,
        )

        if not ncdims:
            # If no ncdims have been provided then return all
            # constructs that could have a netCDF dimension name
            for cid, construct in tuple(out.items()):
                try:
                    construct.nc_get_dimension
                except AttributeError:
                    pop(cid)

            return out

        for cid, construct in tuple(out.items()):
            try:
                nc_get_dimension = construct.nc_get_dimension
            except AttributeError:
                pop(cid)
                continue

            value1 = nc_get_dimension(None)

            ok = False
            if value1 is not None:
                for value0 in ncdims:
                    ok = self._matching_values(
                        value0, None, value1, basic=True
                    )
                    if ok:
                        break

            if not ok:
                pop(cid)

        return out

    def filter_by_ncdim(self, *ncdims, todict=False, cached=None):
        """Select domain axis constructs by netCDF dimension name.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `filter`, `filters_applied`, `inverse_filter`,
                     `clear_filters_applied`, `unfilter`

        :Parameters:

            ncdims: optional
                Select constructs that have a netCDF dimension name,
                defined by their `!nc_get_dimension` methods, that
                match any of the given values.

                If no netCDF dimension names are provided then all
                constructs that do or could have a netCDF dimension
                name are selected.

                {{value match}}

            {{todict: `bool`, optional}}

                .. versionadded:: (cfdm) 1.8.9.0

            {{cached: optional}}

                .. versionadded:: (cfdm) 1.8.9.0

        :Returns:

            `Constructs` or `dict` or *cached*
                The selected constructs, or a cached valued.

        **Examples:**

        Select the domain axis constructs with netCDF dimension name
        'time':

        >>> d = c.filter_by_ncdim('time')

        Select the domain axis constructs with netCDF dimension name
        'time' or 'lat':

        >>> d = c.filter_by_ncdim('time', 'lat')

        """
        if cached is not None:
            return cached

        return self._filter_by_ncdim(self, ncdims, todict)

    def _filter_by_ncvar(self, arg, ncvars, todict):
        """Worker function for `filter_by_ncvar` and `filter`.

        See `filter_by_ncvar` for details.

        .. versionadded:: (cfdm) 1.8.9.0

        """
        out, pop = self._filter_preprocess(
            arg,
            filter_applied={"filter_by_ncvar": ncvars},
            todict=todict,
        )

        if not ncvars:
            # If no ncvars have been provided then return all
            # constructs that could have a netCDF variable name
            for cid, construct in tuple(out.items()):
                try:
                    construct.nc_get_variable
                except AttributeError:
                    pop(cid)

            return out

        for cid, construct in tuple(out.items()):
            try:
                nc_get_variable = construct.nc_get_variable
            except AttributeError:
                pop(cid)
                continue

            value1 = nc_get_variable(None)

            ok = False
            if value1 is not None:
                for value0 in ncvars:
                    ok = self._matching_values(
                        value0, None, value1, basic=True
                    )
                    if ok:
                        break

            if not ok:
                pop(cid)

        return out

    def filter_by_ncvar(self, *ncvars, todict=False, cached=None):
        """Select domain axis constructs by netCDF variable name.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `filter`, `filters_applied`, `inverse_filter`,
                     `clear_filters_applied`, `unfilter`

        :Parameters:

            ncvars: optional
                Select constructs that have a netCDF variable name,
                defined by their `!nc_get_variable` methods, that
                match any of the given values.

                If no netCDF variable names are provided then all
                constructs that do or could have a netCDF variable
                name are selected.

                {{value match}}

            {{todict: `bool`, optional}}

                .. versionadded:: (cfdm) 1.8.9.0

            {{cached: optional}}

                .. versionadded:: (cfdm) 1.8.9.0

        :Returns:

            `Constructs` or `dict` or *cached*
                The selected constructs, or a cached valued.

        **Examples:**

        Select the constructs with netCDF variable name 'time':

        >>> d = c.filter_by_ncvar('time')

        Select the constructs with netCDF variable name 'time' or
        'lat':

        >>> d = c.filter_by_ncvar('time', 'lat')

        """
        if cached is not None:
            return cached

        return self._filter_by_ncvar(self, ncvars, todict)

    def _filter_by_property(self, arg, properties, todict, property_mode):
        """Worker function for `filter_by_property` and `filter`.

        See `filter_by_property`  for details.

        .. versionadded:: (cfdm) 1.8.9.0

        """
        # Parse property_mode
        if not property_mode:
            # property_mode is 'and' by default
            _or = False
        else:
            if len(property_mode) > 1:
                raise ValueError(
                    f"{self.__class__.__name__}.filter_by_property() accepts"
                    "at most one positional parameter, "
                    f"got {len(property_mode)}"
                )

            mode = property_mode[0]
            if mode == "or":
                _or = True
            elif mode == "and":
                _or = False
            else:
                raise ValueError(
                    f"{self.__class__.__name__}.filter_by_property() has "
                    f"incorrect 'property_mode' value ({mode!r}). "
                    "If set must be one of 'or', 'and'"
                )

        out, pop = self._filter_preprocess(
            arg,
            filter_applied={"filter_by_property": (property_mode, properties)},
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
                elif value0 is None:
                    # If a given value is None then match if the
                    # construct the property, regardless of the
                    # construct's property value.
                    ok = True
                else:
                    ok = self._matching_values(value0, construct, value1)

                if _or:
                    if ok:
                        break
                elif not ok:
                    break

            if not ok:
                pop(cid)

        return out

    def filter_by_property(self, *property_mode, **properties):
        """Select metadata constructs by property.

        Unlike the other "filter_by_" methods, this method has no
        *todict* or *cached* parameters. To get the results as a
        dictionary, use the `todict` method on the result, or for
        faster performance use the `filter` method. For instance, to
        get a dictionary of all constructs with a long_name of
        ``'time'`` you could do
        ``c.filter_by_property(long_name="time").todict()``, or the
        faster ``d = c.filter(filter_by_property={"long_name":
        "time"}, todict=True)``. To return a cached result, you have
        to use the `filter` method:
        ``c.filter(filter_by_property={"long_name": "time"},
        cached=x)``.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `filter`, `filters_applied`, `inverse_filter`,
                     `clear_filters_applied`, `unfilter`

        :Parameters:

            property_mode: optional
                Define the behaviour when multiple properties are
                provided:

                ===============  =====================================
                *property_mode*  Description
                ===============  =====================================
                ``'and'``        A construct is selected if it matches
                                 all of the given properties.

                ``'or'``         A construct is selected when at least
                                 one of its properties matches.
                ===============  =====================================

                By default *property_mode* is ``'and'``.

            properties:  optional
                Select constructs that have a CF property, defined by
                their `!properties` methods, that matches any of the
                given values.

                A property names and their given values are specified
                by keyword argument names and values.

                {{value match}}

                The special value of `None` selects any construct that
                has that property, regardless of the construct's
                property value.

                If no properties are provided then all constructs that
                do or could have CF properties, with any values, are
                selected.

        :Returns:

            `Constructs`
                The selected constructs.

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
        return self._filter_by_property(self, properties, False, property_mode)

    def _filter_by_size(self, arg, sizes, todict):
        """Worker function for `filter_by_size` and `filter`.

        See `filter_by_size` for details.

        .. versionadded:: (cfdm) 1.8.9.0

        """
        if not sizes:
            # If no sizes have been provided then return all domain
            # axis constructs
            return self._filter_by_type(
                arg,
                ("domain_axis",),
                todict,
                filter_applied={"filter_by_size": sizes},
            )

        out, pop = self._filter_preprocess(
            arg,
            filter_applied={"filter_by_size": sizes},
            todict=todict,
        )

        construct_type = self._construct_type
        for cid, construct in tuple(out.items()):
            if construct_type[cid] != "domain_axis":
                pop(cid)
                continue

            value1 = construct.get_size(None)

            ok = value1 is not None and value1 in sizes
            if not ok:
                pop(cid)

        return out

    def filter_by_size(self, *sizes, todict=False, cached=None):
        """Select domain axis constructs by size.

        .. versionadded:: (cfdm) 1.7.3

        .. seealso:: `filter`, `filters_applied`, `inverse_filter`,
                     `clear_filters_applied`, `unfilter`

        :Parameters:

            sizes: optional
                Select domain axis constructs that have sizes, defined
                by their `!get_size` methods, that match any of the
                given values.

                If no sizes are provided then all domain axis
                constructs are selected.

                A value may be any object that can match an integer
                via ``==``.

            {{todict: `bool`, optional}}

                .. versionadded:: (cfdm) 1.8.9.0

            {{cached: optional}}

                .. versionadded:: (cfdm) 1.8.9.0

        :Returns:

            `Constructs` or `dict` or *cached*
                The selected constructs, or a cached valued.

        **Examples:**

        Select domain axis constructs that have a size of 1:

        >>> d = c.filter_by_size(1)

        Select domain axis constructs that have a size of 1 or 96:

        >>> d = c.filter_by_size(1, 96)

        """
        if cached is not None:
            return cached

        return self._filter_by_size(self, sizes, todict)

    def _filter_by_type(self, arg, types, todict, filter_applied=None):
        """Worker function for `filter_by_type` and `filter`.

        See `filter_by_type` for details.

        .. versionadded:: (cfdm) 1.8.9.0

        """
        if isinstance(arg, dict):
            if types:
                pop = arg.pop
                construct_type = self._construct_type
                for cid in tuple(arg):
                    if construct_type[cid] not in types:
                        pop(cid)

            return arg

        out = super(Constructs, arg).filter_by_type(*types, todict=todict)

        if not todict:
            if filter_applied is None:
                filter_applied = {"filter_by_type": types}

            out._prefiltered = self.shallow_copy()
            out._filters_applied = arg.filters_applied() + (filter_applied,)

        return out

    def filter_by_type(self, *types, todict=False, cached=None):
        """Select metadata constructs by type.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `filter`, `filters_applied`, `inverse_filter`,
                     `clear_filters_applied`, `unfilter`

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

                .. versionadded:: (cfdm) 1.8.9.0

            {{cached: optional}}

                .. versionadded:: (cfdm) 1.8.9.0

        :Returns:

            `Constructs` or `dict` or *cached*
                The selected constructs, or a cached valued.

        **Examples:**

        Select dimension coordinate constructs:

        >>> d = c.filter_by_type('dimension_coordinate')

        Select dimension coordinate and field ancillary constructs:

        >>> d = c.filter_by_type('dimension_coordinate', 'field_ancillary')

        """
        if cached is not None:
            return cached

        return self._filter_by_type(self, types, todict)

    def filters_applied(self):
        """A history of filters that have been applied.

        The history is returned in a tuple. The last element of the
        tuple describes the last filter applied. Each element is a
        single-entry dictionary whose key is the name of the filter
        method that was used, with a value that gives the arguments
        that were passed to the call of that method. If no filters
        have been applied then the tuple is empty.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `filter`, `inverse_filter`,
                     `clear_filters_applied`, `unfilter`

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

        This method does not change the metadata constructs, it just
        forgets the history of any filters that have previously been
        applied. Use `inverse_filter` or `unfilter` retrieve
        previously filtered constructs.

        The removed history is returned in a tuple. The last element
        of the tuple describes the last filter applied. Each element
        is a single-entry dictionary whose key is the name of the
        filter method that was used, with a value that gives the
        arguments that were passed to the call of that method. If no
        filters have been applied then the tuple is empty.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `filter`, `filters_applied`, `inverse_filter`,
                     `unfilter`

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

        .. seealso:: `filter`, `filters_applied`,
                     `clear_filters_applied`, `unfilter`

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

    def unfilter(self, depth=None, copy=True):
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

        .. seealso:: `filter`, `filters_applied`,
                     `clear_filters_applied`, `inverse_filter`

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

        if copy:
            out = out.shallow_copy()

        return out
