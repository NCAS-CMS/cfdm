import logging

from ..decorators import (
    _display_or_return,
    _inplace_enabled,
    _inplace_enabled_define_and_cleanup,
    _manage_log_level_via_verbosity,
)
from . import PropertiesData

logger = logging.getLogger(__name__)


class PropertiesDataBounds(PropertiesData):
    """Mixin for a data array with descriptive properties and bounds.

    .. versionadded:: (cfdm) 1.7.0

    """

    def __init__(
        self,
        properties=None,
        data=None,
        bounds=None,
        geometry=None,
        interior_ring=None,
        node_count=None,
        part_node_count=None,
        source=None,
        copy=True,
        _use_data=True,
    ):
        """**Initialisation**

        :Parameters:

            properties: `dict`, optional
                Set descriptive properties. The dictionary keys are
                property names, with corresponding values.

                Properties may also be set after initialisation with
                the `properties` and `set_property` methods.

                *Parameter example:*
                  ``properties={'standard_name': 'longitude'}``

            {{init data: data_like, optional}}

            bounds: `Bounds`, optional
                Set the bounds array.

                The bounds array may also be set after initialisation
                with the `set_bounds` method.

            geometry: `str`, optional
                Set the geometry type.

                The geometry type may also be set after initialisation
                with the `set_geometry` method.

                *Parameter example:*
                  ``geometry='polygon'``

            interior_ring: `InteriorRing`, optional
                Set the interior ring variable.

                The interior ring variable may also be set after
                initialisation with the `set_interior_ring` method.

            node_count: `NodeCount`, optional
                Set the node count variable for geometry
                bounds.

                The node count variable may also be set after
                initialisation with the `set_node_count` method.

            part_node_count: `PartNodeCount`, optional
                Set the part node count variable for geometry
                bounds.

                The part node count variable may also be set after
                initialisation with the `set_node_count` method.

            {{init source: optional}}

            {{init copy: `bool`, optional}}

        """
        # Initialise properties, data, geometry and interior ring
        super().__init__(
            properties=properties,
            data=data,
            bounds=bounds,
            source=source,
            geometry=geometry,
            interior_ring=interior_ring,
            copy=copy,
            _use_data=_use_data,
        )

        # Get node count and part node count variables from source
        if source is not None:
            try:
                node_count = source.get_node_count(None)
            except AttributeError:
                node_count = None

            try:
                part_node_count = source.get_part_node_count(None)
            except AttributeError:
                part_node_count = None

        # Initialise node count
        if node_count is not None:
            self.set_node_count(node_count, copy=copy)

        # Initialise part node count
        if part_node_count is not None:
            self.set_part_node_count(part_node_count, copy=copy)

    def __getitem__(self, indices):
        """Return a subspace of the construct defined by indices.

        f.__getitem__(indices) <==> f[indices]

        The new subspace contains the same properties and similar
        components to the original construct, but the latter are also
        subspaced over their corresponding axes.

        Indexing follows rules that are very similar to the numpy
        indexing rules, the only differences being:

        * An integer index i takes the i-th element but does not
          reduce the rank by one.

        * When two or more dimensions' indices are sequences of integers
          then these indices work independently along each dimension
          (similar to the way vector subscripts work in Fortran). This is
          the same behaviour as indexing on a Variable object of the
          netCDF4 package.

        :Returns:

            `{{class}}`
                The subspace of the construct.

        **Examples**

        >>> f.shape
        (1, 10, 9)
        >>> f[:, :, 1].shape
        (1, 10, 1)
        >>> f[:, 0].shape
        (1, 1, 9)
        >>> f[..., 6:3:-1, 3:6].shape
        (1, 3, 3)
        >>> f[0, [2, 9], [4, 8]].shape
        (1, 2, 2)
        >>> f[0, :, -2].shape
        (1, 10, 1)

        """
        if indices is Ellipsis:
            return self.copy()

        if not isinstance(indices, tuple):
            indices = (indices,)

        new = super().__getitem__(indices)

        # Subspace the interior ring array, if there is one.
        interior_ring = self.get_interior_ring(None)
        if interior_ring is not None:
            new.set_interior_ring(interior_ring[indices], copy=False)

        # Subspace the bounds, if there are any.
        self_bounds = self.get_bounds(None)
        if self_bounds is not None:
            data = self_bounds.get_data(None, _units=False, _fill_value=False)
            if data is not None:
                # There is a bounds array
                bounds_indices = list(data._parse_indices(indices))

                if data.ndim <= 2:
                    index = bounds_indices[0]
                    if isinstance(index, slice):
                        if index.step and index.step < 0:
                            # This scalar or 1-d variable has been
                            # reversed so reverse its bounds (as per
                            # 7.1 of the conventions)
                            bounds_indices[-1] = slice(None, None, -1)
                    elif data.size > 1 and int(index[-1]) < int(index[0]):
                        # This 1-d variable has been reversed so
                        # reverse its bounds (as per 7.1 of the
                        # conventions)
                        bounds_indices[-1] = slice(None, None, -1)

                new.set_bounds(self_bounds[tuple(bounds_indices)], copy=False)

        # Return the new bounded variable
        return new

    def __str__(self):
        """Called by the `str` built-in function.

        x.__str__() <==> str(x)

        .. versionadded:: (cfdm) 1.7.0

        """
        shape = None
        data = self.get_data(None, _units=False, _fill_value=False)
        bounds = self.get_bounds(None)
        if data is not None:
            shape = data.shape

        if shape is not None:
            dims = ", ".join([str(x) for x in shape])
            dims = f"({dims})"
        else:
            dims = ""

        # ------------------------------------------------------------
        # Units and calendar
        # ------------------------------------------------------------

        units = self.get_property("units", None)
        if units is None and bounds is not None:
            units = bounds.get_property("units", None)

        calendar = self.get_property("calendar", None)
        if calendar is None and bounds is not None:
            calendar = bounds.get_property("calendar", None)

        if units is None:
            isreftime = calendar is not None
            units = ""
        else:
            isreftime = "since" in units

        if isreftime:
            if calendar is None:
                calendar = ""

            units += " " + calendar

        return f"{self.identity('')}{dims} {units}"

    def _original_filenames(self, define=None, update=None, clear=False):
        """The names of files containing the original data and metadata.

        {{original filenames}}

        .. versionadded:: (cfdm) 1.10.0.1

        :Parameters:

            {{define: (sequence of) `str`, optional}}

            {{update: (sequence of) `str`, optional}}

            {{clear: `bool` optional}}

        :Returns:

            `set`
                {{Returns original filenames}}

                If the *define* or *update* parameter is set then
                `None` is returned.

        """
        out = super()._original_filenames(
            define=define, update=update, clear=clear
        )
        if out is None:
            return

        bounds = self.get_bounds(None)
        if bounds is not None:
            out.update(bounds._original_filenames(clear=clear))

        interior_ring = self.get_interior_ring(None)
        if interior_ring is not None:
            out.update(interior_ring._original_filenames(clear=clear))

        return out

    @_inplace_enabled(default=False)
    def apply_masking(self, bounds=True, inplace=False):
        """Apply masking as defined by the CF conventions.

        Masking is applied according to any of the following criteria
        that are applicable:

        * where data elements are equal to the value of the
          ``missing_value`` property;

        * where data elements are equal to the value of the
          ``_FillValue`` property;

        * where data elements are strictly less than the value of the
          ``valid_min`` property;

        * where data elements are strictly greater than the value of
          the ``valid_max`` property;

        * where data elements are within the inclusive range specified
          by the two values of ``valid_range`` property.

        If any of the above properties have not been set the no
        masking is applied for that method.

        The cell bounds, if any, are also masked according to the same
        criteria as the parent construct. If, however, any of the
        relevant properties are explicitly set on the bounds instance
        then their values will be used in preference to those of the
        parent construct.

        Elements that are already masked remain so.

        .. note:: If using the `apply_masking` method on a construct
                  that has been read from a dataset with the
                  ``mask=False`` parameter to the `read` function,
                  then the mask defined in the dataset can only be
                  recreated if the ``missing_value``, ``_FillValue``,
                  ``valid_min``, ``valid_max``, and ``valid_range``
                  properties have not been updated.

        .. versionadded:: (cfdm) 1.8.2

        .. seealso:: `Data.apply_masking`, `read`, `write`

        :Parameters:

            {{inplace: `bool`, optional}}

        :Returns:

            `{{class}}` or `None`
                A new instance with masked values, or `None` if the
                operation was in-place.

        **Examples**

        >>> print(c.data.array)
        [9.96920997e+36, 9.96920997e+36, 9.96920997e+36, 9.96920997e+36,
         9.96920997e+36, 9.96920997e+36, 9.96920997e+36, 9.96920997e+36],
         [0.023 0.036 0.045 0.062 0.046 0.073 0.006 0.066]
         [0.11  0.131 0.124 0.146 0.087 0.103 0.057 0.011]
         [0.029 0.059 0.039 0.07  0.058 0.072 0.009 0.017]
        [9.96920997e+36, 9.96920997e+36, 9.96920997e+36, 9.96920997e+36,
         9.96920997e+36, 9.96920997e+36, 9.96920997e+36, 9.96920997e+36]])
        >>> masked_c = c.apply_masking()
        >>> print(masked_c.data.array)
        [[   --    --    --    --    --    --    --    --]
         [0.023 0.036 0.045 0.062 0.046 0.073 0.006 0.066]
         [0.11  0.131 0.124 0.146 0.087 0.103 0.057 0.011]
         [0.029 0.059 0.039 0.07  0.058 0.072 0.009 0.017]
         [   --    --    --    --    --    --    --    --]]

        """
        c = _inplace_enabled_define_and_cleanup(self)
        super(PropertiesDataBounds, c).apply_masking(inplace=True)

        data = c.get_bounds_data(None, _units=False, _fill_value=False)
        if data is not None:
            b = c.get_bounds()

            fill_values = []
            for prop in ("_FillValue", "missing_value"):
                x = b.get_property(prop, c.get_property(prop, None))
                if x is not None:
                    fill_values.append(x)

            kwargs = {"inplace": True, "fill_values": fill_values}

            for prop in ("valid_min", "valid_max", "valid_range"):
                kwargs[prop] = b.get_property(prop, c.get_property(prop, None))

            data.apply_masking(**kwargs)

        return c

    def creation_commands(
        self,
        representative_data=False,
        namespace=None,
        indent=0,
        string=True,
        name="c",
        data_name="data",
        bounds_name="b",
        interior_ring_name="i",
        header=True,
        _coordinate=False,
    ):
        """Return the commands that would create the construct.

        .. versionadded:: (cfdm) 1.8.7.0

        .. seealso:: `{{package}}.Data.creation_commands`,
                     `{{package}}.Field.creation_commands`

        :Parameters:

            {{representative_data: `bool`, optional}}

            {{namespace: `str`, optional}}

            {{indent: `int`, optional}}

            {{string: `bool`, optional}}

            {{name: `str`, optional}}

            {{data_name: `str`, optional}}

            bounds_name: `str`, optional
                The name of the construct's `Bounds` instance created
                by the returned commands.

                *Parameter example:*
                  ``name='bounds1'``

            interior_ring_name: `str`, optional
                The name of the construct's `InteriorRing` instance
                created by the returned commands.

                *Parameter example:*
                  ``name='ir1'``

            {{header: `bool`, optional}}

        :Returns:

            {{returns creation_commands}}

        **Examples**

        >>> x = {{package}}.{{class}}(
        ...     properties={'units': 'degrees_east',
        ...                 'standard_name': 'longitude'}
        ... )
        >>> x.set_data([22.5, 67.5, 112.5])
        >>> b = {{package}}.Bounds()
        >>> b.set_data([[0.0, 45.0], [45.0, 90.0], [90.0, 135.0]])
        >>> x.set_bounds(b)
        >>> print(x.creation_commands(header=False))
        c = {{package}}.{{class}}()
        c.set_properties({'units': 'degrees_east', 'standard_name': 'longitude'})
        data = {{package}}.Data([22.5, 67.5, 112.5], units='degrees_east', dtype='f8')
        c.set_data(data)
        b = {{package}}.Bounds()
        data = {{package}}.Data([[0.0, 45.0], [45.0, 90.0], [90.0, 135.0]], units='degrees_east', dtype='f8')
        b.set_data(data)
        c.set_bounds(b)

        """
        if name in (data_name, bounds_name, interior_ring_name):
            raise ValueError(
                "The 'name' parameter can not have the same value as "
                "any of the 'data_name', 'bounds_name', or "
                f"'interior_ring_name' parameters: {name!r}"
            )

        if data_name in (name, bounds_name, interior_ring_name):
            raise ValueError(
                "The 'data_name' parameter can not have "
                "the same value as any of the 'name', 'bounds_name', "
                f"or 'interior_ring_name' parameters: {data_name!r}"
            )

        namespace0 = namespace
        if namespace is None:
            namespace = self._package() + "."
        elif namespace and not namespace.endswith("."):
            namespace += "."

        out = super().creation_commands(
            representative_data=representative_data,
            indent=0,
            namespace=namespace,
            string=False,
            name=name,
            data_name=data_name,
            header=header,
        )

        # Geometry type
        geometry = self.get_geometry(None)
        if geometry is not None:
            out.append(f"{name}.set_geometry({geometry!r})")

        # Climatology
        if _coordinate and self.get_climatology(False):
            out.append("{}.set_climatology(True)".format(name))

        bounds = self.get_bounds(None)
        if bounds is not None:
            out.extend(
                bounds.creation_commands(
                    representative_data=representative_data,
                    indent=0,
                    namespace=namespace0,
                    string=False,
                    name=bounds_name,
                    data_name=data_name,
                    header=False,
                )
            )
            out.append(f"{name}.set_bounds({bounds_name})")

        interior_ring = self.get_interior_ring(None)
        if interior_ring is not None:
            out.extend(
                interior_ring.creation_commands(
                    representative_data=representative_data,
                    indent=0,
                    namespace=namespace0,
                    string=False,
                    name=interior_ring_name,
                    data_name=data_name,
                    header=False,
                )
            )
            out.append(f"{name}.set_interior_ring({interior_ring_name})")

        if string:
            indent = " " * indent
            out[0] = indent + out[0]
            out = ("\n" + indent).join(out)

        return out

    def del_node_count(self, default=ValueError()):
        """Remove the node count variable for geometry bounds.

        .. versionadded:: (cfdm) 1.8.0

        .. seealso:: `get_node_count`, `has_node_count`,
                     `set_node_count`

        :Parameters:

            default: optional
                Return the value of the *default* parameter if the
                node count variable has not been set.

                {{default Exception}}

        :Returns:

            `NodeCount`
                The removed node count variable.

        **Examples**

        >>> n = {{package}}.NodeCount(properties={'long_name': 'node counts'})
        >>> c.set_node_count(n)
        >>> c.has_node_count()
        True
        >>> c.get_node_count()
        <{{repr}}NodeCount: long_name=node counts>
        >>> c.del_node_count()
        <{{repr}}NodeCount: long_name=node counts>
        >>> c.has_node_count()
        False

        """
        try:
            return self._del_component("node_count")
        except ValueError:
            if default is None:
                return default

            return self._default(
                default,
                f"{self.__class__.__name__} has no node count variable",
            )

    def del_part_node_count(self, default=ValueError()):
        """Remove the part node count variable for geometry bounds.

        .. versionadded:: (cfdm) 1.8.0

        .. seealso:: `get_part_node_count`, `has_part_node_count`,
                     `set_part_node_count`

        :Parameters:

            default: optional
                Return the value of the *default* parameter if the part
                node count variable has not been set.

                {{default Exception}}

        :Returns:

            `PartNodeCount`
                The removed part node count variable.

        **Examples**

        >>> p = {{package}}.PartNodeCount(properties={'long_name': 'part node counts'})
        >>> c.set_part_node_count(p)
        >>> c.has_part_node_count()
        True
        >>> c.get_part_node_count()
        <{{repr}}PartNodeCount: long_name=part node counts>
        >>> c.del_part_node_count()
        <{{repr}}PartNodeCount: long_name=part node counts>
        >>> c.has_part_node_count()
        False

        """
        try:
            return self._del_component("part_node_count")
        except ValueError:
            if default is None:
                return default

            return self._default(
                default,
                f"{self.__class__.__name__} has no part node count variable",
            )

    @_display_or_return
    def dump(
        self,
        display=True,
        _key=None,
        _omit_properties=None,
        _prefix="",
        _title=None,
        _create_title=True,
        _level=0,
        _axes=None,
        _axis_names=None,
    ):
        """A full description.

        :Parameters:

            display: `bool`, optional
                If False then return the description as a string. By
                default

        :Returns:

            {{returns dump}}

        """
        # ------------------------------------------------------------
        # Properties and Data
        # ------------------------------------------------------------
        string = super().dump(
            display=False,
            _key=_key,
            _omit_properties=_omit_properties,
            _prefix=_prefix,
            _title=_title,
            _create_title=_create_title,
            _level=_level,
            _axes=_axes,
            _axis_names=_axis_names,
        )

        string = [string]

        # ------------------------------------------------------------
        # Geometry type
        # ------------------------------------------------------------
        geometry = self.get_geometry(None)
        if geometry is not None:
            indent1 = "    " * (_level + 1)
            string.append(f"{indent1}{_prefix}Geometry: {geometry}")

        # ------------------------------------------------------------
        # Bounds
        # ------------------------------------------------------------
        bounds = self.get_bounds(None)
        if bounds is not None:
            string.append(
                bounds.dump(
                    display=False,
                    _key=_key,
                    _prefix=_prefix + "Bounds:",
                    _create_title=False,
                    _level=_level,
                    _axes=_axes,
                    _axis_names=_axis_names,
                )
            )

        # -------------------------------------------------------------
        # Interior ring
        # ------------------------------------------------------------
        interior_ring = self.get_interior_ring(None)
        if interior_ring is not None:
            string.append(
                interior_ring.dump(
                    display=False,
                    _key=_key,
                    _prefix=_prefix + "Interior Ring:",
                    _create_title=False,
                    _level=_level,
                    _axes=_axes,
                    _axis_names=_axis_names,
                )
            )

        return "\n".join(string)

    @_manage_log_level_via_verbosity
    def equals(
        self,
        other,
        rtol=None,
        atol=None,
        verbose=None,
        ignore_data_type=False,
        ignore_fill_value=False,
        ignore_properties=None,
        ignore_compression=True,
        ignore_type=False,
    ):
        """Whether two instances are the same.

        Equality is strict by default. This means that:

        * the same descriptive properties must be present, with the
          same values and data types, and vector-valued properties
          must also have same the size and be element-wise equal (see
          the *ignore_properties* and *ignore_data_type* parameters),
          and

        ..

        * if there are data arrays then they must have same shape and
          data type, the same missing data mask, and be element-wise
          equal (see the *ignore_data_type* parameter).

        ..

        * if there are bounds then their descriptive properties (if
          any) must be the same and their data arrays must have same
          shape and data type, the same missing data mask, and be
          element-wise equal (see the *ignore_properties* and
          *ignore_data_type* parameters).

        {{equals tolerance}}

        {{equals compression}}

        {{equals netCDF}}

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:


            other:
                The object to compare for equality.

            {{atol: number, optional}}

            {{rtol: number, optional}}

            {{ignore_fill_value: `bool`, optional}}

            {{verbose: `int` or `str` or `None`, optional}}

            {{ignore_properties: (sequence of) `str`, optional}}

            {{ignore_data_type: `bool`, optional}}

            {{ignore_compression: `bool`, optional}}

            {{ignore_type: `bool`, optional}}

        :Returns:

            `bool`
                Whether the two instances are equal.

        **Examples**

        >>> p.equals(p)
        True
        >>> p.equals(p.copy())
        True
        >>> p.equals('not a colection of properties')
        False

        """
        # ------------------------------------------------------------
        # Check the properties and data
        # ------------------------------------------------------------
        if not super().equals(
            other,
            rtol=rtol,
            atol=atol,
            verbose=verbose,
            ignore_data_type=ignore_data_type,
            ignore_fill_value=ignore_fill_value,
            ignore_properties=ignore_properties,
            ignore_type=ignore_type,
            ignore_compression=ignore_compression,
        ):
            return False

        # ------------------------------------------------------------
        # Check the geometry type
        # ------------------------------------------------------------
        if self.get_geometry(None) != other.get_geometry(None):
            logger.info(
                f"{self.__class__.__name__}: Different geometry types: "
                f"{self.get_geometry(None)}, {other.get_geometry(None)}"
            )
            return False

        # ------------------------------------------------------------
        # Check the bounds
        # ------------------------------------------------------------
        self_has_bounds = self.has_bounds()
        if self_has_bounds != other.has_bounds():
            logger.info(f"{self.__class__.__name__}: Different bounds")
            return False

        if self_has_bounds:
            if not self._equals(
                self.get_bounds(),
                other.get_bounds(),
                rtol=rtol,
                atol=atol,
                verbose=verbose,
                ignore_data_type=ignore_data_type,
                ignore_type=ignore_type,
                ignore_fill_value=ignore_fill_value,
                ignore_compression=ignore_compression,
            ):
                logger.info(
                    f"{self.__class__.__name__}: Different bounds"
                )  # pragma: no cover

                return False

        # ------------------------------------------------------------
        # Check the interior ring
        # ------------------------------------------------------------
        self_has_interior_ring = self.has_interior_ring()
        if self_has_interior_ring != other.has_interior_ring():
            logger.info(
                f"{self.__class__.__name__}: Different interior ring"
            )  # pragma: no cover

            return False

        if self_has_interior_ring:
            if not self._equals(
                self.get_interior_ring(),
                other.get_interior_ring(),
                rtol=rtol,
                atol=atol,
                verbose=verbose,
                ignore_data_type=ignore_data_type,
                ignore_type=ignore_type,
                ignore_fill_value=ignore_fill_value,
                ignore_compression=ignore_compression,
            ):
                logger.info(
                    f"{self.__class__.__name__}: Different interior ring"
                )  # pragma: no cover

                return False

        return True

    def get_node_count(self, default=ValueError()):
        """Return the node count variable for geometry bounds.

        .. versionadded:: (cfdm) 1.8.0

        .. seealso:: `del_node_count`, `has_node_count`, `set_node_count`

        :Parameters:

            default: optional
                Return the value of the *default* parameter if a node
                count variable has not been set.

                {{default Exception}}

        :Returns:

            `NodeCount`
                The node count variable.

        **Examples**

        >>> n = {{package}}.NodeCount(properties={'long_name': 'node counts'})
        >>> c.set_node_count(n)
        >>> c.has_node_count()
        True
        >>> c.get_node_count()
        <{{repr}}NodeCount: long_name=node counts>
        >>> c.del_node_count()
        <{{repr}}NodeCount: long_name=node counts>
        >>> c.has_node_count()
        False

        """
        out = self._get_component("node_count", None)
        if out is None:
            if default is None:
                return default

            return self._default(
                default,
                f"{self.__class__.__name__} has no node count variable",
            )

        return out

    def get_part_node_count(self, default=ValueError()):
        """Return the part node count variable for geometry bounds.

        .. versionadded:: (cfdm) 1.8.0

        .. seealso:: `del_part_node_count`, `get_node_count`,
                     `has_part_node_count`, `set_part_node_count`

        :Parameters:

            default: optional
                Return the value of the *default* parameter if the part
                node count variable has not been set.

                {{default Exception}}

        :Returns:

            `PartNodeCount`
                The part node count variable.

        **Examples**

        >>> p = {{package}}.PartNodeCount(properties={'long_name': 'part node counts'})
        >>> c.set_part_node_count(p)
        >>> c.has_part_node_count()
        True
        >>> c.get_part_node_count()
        <{{repr}}PartNodeCount: long_name=part node counts>
        >>> c.del_part_node_count()
        <{{repr}}PartNodeCount: long_name=part node counts>
        >>> c.has_part_node_count()
        False

        """
        out = self._get_component("part_node_count", None)
        if out is None:
            if default is None:
                return default

            return self._default(
                default,
                f"{self.__class__.__name__} has no part node count variable",
            )

        return out

    def has_node_count(self):
        """Whether geometry bounds have a node count variable.

        .. versionadded:: (cfdm) 1.8.0

        .. seealso:: `del_node_count`, `get_node_count`, `set_node_count`

        :Returns:

            `bool`
                True if there is a node count variable, otherwise False.

        **Examples**


        >>> n = {{package}}.NodeCount(properties={'long_name': 'node counts'})
        >>> c.set_node_count(n)
        >>> c.has_node_count()
        True
        >>> c.get_node_count()
        <{{repr}}NodeCount: long_name=node counts>
        >>> c.del_node_count()
        <{{repr}}NodeCount: long_name=node counts>
        >>> c.has_node_count()
        False

        """
        return self._has_component("node_count")

    def has_part_node_count(self):
        """Whether geometry bounds have a part node count variable.

        .. versionadded:: (cfdm) 1.8.0

        .. seealso:: `del_part_node_count`, `get_part_node_count`,
                     `set_part_node_count`

        :Returns:

            `bool`
                True if there is a part node count variable, otherwise
                False.

        **Examples**

        >>> p = {{package}}.PartNodeCount(properties={'long_name': 'part node counts'})
        >>> c.set_part_node_count(p)
        >>> c.has_part_node_count()
        True
        >>> c.get_part_node_count()
        <{{repr}}PartNodeCount: long_name=part node counts>
        >>> c.del_part_node_count()
        <{{repr}}PartNodeCount: long_name=part node counts>
        >>> c.has_part_node_count()
        False

        """
        return self._has_component("part_node_count")

    def identities(self, generator=False, **kwargs):
        """Return all possible identities.

        The identities comprise:

        * The ``standard_name`` property.
        * All properties, preceded by the property name and a colon,
          e.g. ``'long_name:Air temperature'``.
        * The netCDF variable name, preceded by ``'ncvar%'``.
        * The identities of the bounds, if any.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `identity`

        :Parameters:

            generator: `bool`, optional
                If True then return a generator for the identities,
                rather than a list.

                .. versionadded:: (cfdm) 1.8.9.0

            kwargs: optional
                Additional configuration parameters. Currently
                none. Unrecognised parameters are ignored.

                .. versionadded:: (cfdm) 1.8.9.0

        :Returns:

            `list` or generator
                The identities.

        **Examples**

        >>> f.properties()
        {'foo': 'bar',
         'long_name': 'Air Temperature',
         'standard_name': 'air_temperature'}
        >>> f.nc_get_variable()
        'tas'
        >>> f.identities()
        ['air_temperature',
         'long_name=Air Temperature',
         'foo=bar',
         'standard_name=air_temperature',
         'ncvar%tas']

        >>> f.properties()
        {}
        >>> f.bounds.properties()
        {'axis': 'Z',
         'units': 'm'}
        >>> f.identities()
        ['axis=Z', 'units=m', 'ncvar%z']
        >>> for i in f.identities(generator=True):
        ...     print(i)
        ...
        axis=Z
        units=m
        ncvar%z

        """
        bounds = self.get_bounds(None)
        if bounds is not None:
            post = (bounds.identities(generator=True),)
            post0 = kwargs.pop("post", None)
            if post0:
                post = tuple(post0) + post

            kwargs["post"] = post

        return super().identities(generator=generator, **kwargs)

    def identity(self, default=""):
        """Return the canonical identity.

        By default the identity is the first found of the following:

        1. The ``standard_name`` property.
        2. The ``cf_role`` property, preceded by ``'cf_role='``.
        3. The ``axis`` property, preceded by ``'axis='``.
        4. The ``long_name`` property, preceded by ``'long_name='``.
        5. The netCDF variable name, preceded by ``'ncvar%'``.
        6. The identity of the bounds, if any.
        7. The value of the *default* parameter.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `identities`

        :Parameters:

            default: optional
                If no identity can be found then return the value of the
                default parameter.

        :Returns:

                The identity.

        **Examples**

        >>> f.properties()
        {'foo': 'bar',
         'long_name': 'Air Temperature',
         'standard_name': 'air_temperature'}
        >>> f.nc_get_variable()
        'tas'
        >>> f.identity()
        'air_temperature'
        >>> f.del_property('standard_name')
        'air_temperature'
        >>> f.identity(default='no identity')
        'air_temperature'
        >>> f.identity()
        'long_name=Air Temperature'
        >>> f.del_property('long_name')
        >>> f.identity()
        'ncvar%tas'
        >>> f.nc_del_variable()
        'tas'
        >>> f.identity()
        'ncvar%tas'
        >>> f.identity()
        ''
        >>> f.identity(default='no identity')
        'no identity'

        >>> f.properties()
        {}
        >>> f.bounds.properties()
        {'axis': 'Z',
         'units': 'm'}
        >>> f.identity()
        'axis=Z'

        """
        identity = super().identity(default=None)
        if identity is not None:
            return identity

        bounds = self.get_bounds(None)
        if bounds is not None:
            return bounds.identity(default=default)

        return default

    def get_bounds(self, default=ValueError()):
        """Return the bounds.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `bounds`, `get_data`, `del_bounds`, `has_bounds`,
                     `set_bounds`

        :Parameters:

            default: optional
                Return the value of the *default* parameter if bounds have
                not been set.

                {{default Exception}}

        :Returns:

            `Bounds`
                The bounds.

        **Examples**

        >>> b = {{package}}.Bounds(data={{package}}.Data(range(10).reshape(5, 2)))
        >>> c.set_bounds(b)
        >>> c.has_bounds()
        True
        >>> c.get_bounds()
        <{{repr}}Bounds: (5, 2) >
        >>> b = c.del_bounds()
        >>> b
        <{{repr}}Bounds: (5, 2) >
        >>> c.has_bounds()
        False
        >>> print(c.get_bounds(None))
        None
        >>> print(c.del_bounds(None))
        None

        """
        bounds = super().get_bounds(default=None)

        if bounds is None:
            if default is None:
                return

            return self._default(
                default, f"{self.__class__.__name__} has no bounds"
            )

        bounds._set_component(
            "inherited_properties", self.properties(), copy=False
        )

        return bounds

    def get_bounds_data(
        self, default=ValueError(), _units=True, _fill_value=True
    ):
        """Return the bounds data.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `bounds`, `get_bounds`, `get_data`

        :Parameters:

            default: optional
                Return the value of the *default* parameter if there are
                no bounds data.

                {{default Exception}}

        :Returns:

            `Data`
                The bounds data.

        **Examples**

        >>> f = {{package}}.example_field(0)
        >>> x = f.construct('latitude')
        >>> x.get_bounds_data()
        <{{repr}}Data(5, 2): [[-90.0, ..., 90.0]] degrees_north>

        """
        bounds = self.get_bounds(default=None)
        if bounds is None:
            if default is None:
                return

            return self._default(
                default, f"{self.__class__.__name__} has no bounds data"
            )

        data = bounds.get_data(
            default=None, _units=_units, _fill_value=_fill_value
        )
        if data is None:
            if default is None:
                return

            return self._default(
                default, f"{self.__class__.__name__} has no bounds data"
            )

        return data

    @_inplace_enabled(default=False)
    def insert_dimension(self, position, inplace=False):
        """Expand the shape of the data array.

        Inserts a new size 1 axis into the data array. A corresponding
        axis is also inserted into the bounds data array, if present.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `squeeze`, `transpose`

        :Parameters:

            position: `int`, optional
                Specify the position that the new axis will have in
                the data array. By default the new axis has position
                0, the slowest varying position. Negative integers
                counting from the last position are allowed.

                *Parameter example:*
                  ``position=2``

                *Parameter example:*
                  ``position=-1``

            {{inplace: `bool`, optional}}

        :Returns:

            `{{class}}` or `None`
                The new construct with expanded data axes. If the
                operation was in-place then `None` is returned.

        **Examples**

        >>> f.shape
        (19, 73, 96)
        >>> f.insert_dimension(position=3).shape
        (96, 73, 19, 1)
        >>> g = f.insert_dimension(position=-1)
        >>> g.shape
        (19, 73, 1, 96)
        >>> f.bounds.shape
        (19, 73, 96, 4)
        >>> g.bounds.shape
        (19, 73, 1, 96, 4)

        """
        c = _inplace_enabled_define_and_cleanup(self)

        # Parse position
        ndim = c.ndim
        if -ndim - 1 <= position < 0:
            position += ndim + 1
        elif not 0 <= position <= ndim:
            raise ValueError(
                f"Can't insert dimension: Invalid position: {position!r}"
            )

        super(PropertiesDataBounds, c).insert_dimension(position, inplace=True)

        # ------------------------------------------------------------
        # Expand the dims of the bounds
        # ------------------------------------------------------------
        bounds = c.get_bounds(None)
        if bounds is not None:
            bounds.insert_dimension(position, inplace=True)

        # ------------------------------------------------------------
        # Expand the dims of the interior_ring
        # ------------------------------------------------------------
        interior_ring = c.get_interior_ring(None)
        if interior_ring is not None:
            interior_ring.insert_dimension(position, inplace=True)

        return c

    def set_node_count(self, node_count, copy=True):
        """Set the node count variable for geometry bounds.

        .. versionadded:: (cfdm) 1.8.0

        .. seealso:: `del_node_count`, `get_node_count`,
                     `has_node_count`

        :Parameters:

            node_count: `NodeCount`
                The node count variable to be inserted.

            copy: `bool`, optional
                If True (the default) then copy the node count
                variable prior to insertion.

        :Returns:

            `None`

        **Examples**

        >>> n = {{package}}.NodeCount(properties={'long_name': 'node counts'})
        >>> c.set_node_count(n)
        >>> c.has_node_count()
        True
        >>> c.get_node_count()
        <{{repr}}NodeCount: long_name=node counts>
        >>> c.del_node_count()
        <{{repr}}NodeCount: long_name=node counts>
        >>> c.has_node_count()
        False

        """
        if copy:
            node_count = node_count.copy()

        self._set_component("node_count", node_count, copy=False)

    def set_part_node_count(self, part_node_count, copy=True):
        """Set the part node count variable for geometry bounds.

        .. versionadded:: (cfdm) 1.8.0

        .. seealso:: `del_part_node_count`, `get_part_node_count`,
                     `has_part_node_count`

        :Parameters:

            part_node_count: `PartNodeCount`
                The part node count variable to be inserted.

            copy: `bool`, optional
                If True (the default) then copy the part node count
                variable prior to insertion.

        :Returns:

            `None`

        **Examples**

        >>> p = {{package}}.PartNodeCount(properties={'long_name':
        ...                                           'part node counts'})
        >>> c.set_part_node_count(p)
        >>> c.has_part_node_count()
        True
        >>> c.get_part_node_count()
        <{{repr}}PartNodeCount: long_name=part node counts>
        >>> c.del_part_node_count()
        <{{repr}}PartNodeCount: long_name=part node counts>
        >>> c.has_part_node_count()
        False

        """
        if copy:
            part_node_count = part_node_count.copy()

        self._set_component("part_node_count", part_node_count, copy=False)

    @_inplace_enabled(default=False)
    def squeeze(self, axes=None, inplace=False):
        """Remove size one axes from the data array.

        By default all size one axes are removed, but particular size
        one axes may be selected for removal. Corresponding axes are
        also removed from the bounds data array, if present.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `insert_dimension`, `transpose`

        :Parameters:

            axes: (sequence of) `int`, optional
                The positions of the size one axes to be removed. By
                default all size one axes are removed.

                {{axes int examples}}

            {{inplace: `bool`, optional}}

        :Returns:

            `{{class}}` or `None`
                The new construct with removed data axes. If the
                operation was in-place then `None` is returned.

        **Examples**

        >>> f.shape
        (1, 73, 1, 96)
        >>> f.squeeze().shape
        (73, 96)
        >>> f.squeeze(0).shape
        (73, 1, 96)
        >>> g = f.squeeze([-3, 2])
        >>> g.shape
        (73, 96)
        >>> f.bounds.shape
        (1, 73, 1, 96, 4)
        >>> g.shape
        (73, 96, 4)

        """
        if axes is None:
            axes = tuple([i for i, n in enumerate(self.shape) if n == 1])

        c = _inplace_enabled_define_and_cleanup(self)
        super(PropertiesDataBounds, c).squeeze(axes, inplace=True)

        # ------------------------------------------------------------
        # Squeeze the bounds
        # ------------------------------------------------------------
        bounds = c.get_bounds(None)
        if bounds is not None:
            bounds.squeeze(axes, inplace=True)

        # ------------------------------------------------------------
        # Squeeze the interior_ring
        # ------------------------------------------------------------
        interior_ring = c.get_interior_ring(None)
        if interior_ring is not None:
            interior_ring.squeeze(axes, inplace=True)

        return c

    @_inplace_enabled(default=False)
    def to_memory(self, inplace=False):
        """Bring data on disk into memory.

        There is no change to data that is already in memory.

        :Parameters:

            inplace: `bool`, optional
                If True then do the operation in-place and return `None`.

        :Returns:

            `{{class}}` or `None`
                A copy with the data in memory, or `None` if the
                operation was in-place.

        """
        c = _inplace_enabled_define_and_cleanup(self)

        data = c.get_data(None)
        if data is not None:
            data.to_memory(inplace=True)

        bounds = c.get_bounds(None)
        if bounds is not None:
            bounds.to_memory(inplace=True)

        interior_ring = c.get_interior_ring(None)
        if interior_ring is not None:
            interior_ring.to_memory(inplace=True)

        return c

    @_inplace_enabled(default=False)
    def transpose(self, axes=None, inplace=False):
        """Permute the axes of the data array.

        Corresponding axes of the bounds data array, if present, are
        also permuted.

        Note that if i) the data array is two-dimensional, ii) the two
        axes have been permuted, and iii) each cell has four bounds
        values; then columns 1 and 3 (counting from 0) of the bounds
        axis are swapped to preserve contiguity bounds in adjacent
        cells. See section 7.1 "Cell Boundaries" of the CF conventions
        for details.

        .. seealso:: `insert_dimension`, `squeeze`

        :Parameters:

            axes: (sequence of) `int`, optional
                The new axis order. By default the order is reversed.

                {{axes int examples}}

            {{inplace: `bool`, optional}}

        :Returns:

            `{{class}}` or `None`
                The new construct with permuted data axes. If the
                operation was in-place then `None` is returned.

        **Examples**

        >>> f.shape
        (19, 73, 96)
        >>> f.transpose().shape
        (96, 73, 19)
        >>> g = f.transpose([1, 0, 2])
        >>> g.shape
        (73, 19, 96)
        >>> f.bounds.shape
        (19, 73, 96, 4)
        >>> g.bounds.shape
        (73, 19, 96, 4)

        """
        ndim = self.ndim
        if axes is None:
            axes = list(range(ndim - 1, -1, -1))
        else:
            axes = self._parse_axes(axes)

        # ------------------------------------------------------------
        # Transpose the coordinates
        # ------------------------------------------------------------
        c = _inplace_enabled_define_and_cleanup(self)
        super(PropertiesDataBounds, c).transpose(axes, inplace=True)

        # ------------------------------------------------------------
        # Transpose the bounds
        # ------------------------------------------------------------
        bounds = c.get_bounds(None)
        data = c.get_bounds_data(None, _fill_value=False)
        if bounds is not None:
            b_axes = axes[:]
            b_axes.extend(list(range(ndim, data.ndim)))
            bounds.transpose(b_axes, inplace=True)

            data = bounds.get_data(None, _fill_value=False)
            if (
                data is not None
                and ndim == 2
                and data.ndim == 3
                and data.shape[-1] == 4
                and b_axes[0:2] == [1, 0]
            ):
                # Swap elements 1 and 3 of the trailing dimension so
                # that the values are still contiguous (if they ever
                # were). See section 7.1 of the CF conventions.
                data[:, :, slice(1, 4, 2)] = data[:, :, slice(3, 0, -2)]
                bounds.set_data(data, copy=False)

        # ------------------------------------------------------------
        # Transpose the interior ring
        # ------------------------------------------------------------
        interior_ring = c.get_interior_ring(None)
        if interior_ring is not None:
            interior_ring.transpose(axes + [-1], inplace=True)

        return c

    @_inplace_enabled(default=False)
    def uncompress(self, inplace=False):
        """Uncompress the construct.

        Compression saves space by identifying and removing unwanted
        missing data. Such compression techniques store the data more
        efficiently and result in no precision loss.

        Whether or not the construct is compressed does not alter its
        functionality nor external appearance.

        A construct that is already uncompressed will be returned
        unchanged.

        The following type of compression are available:

            * Ragged arrays for discrete sampling geometries
              (DSG). Three different types of ragged array
              representation are supported.

            ..

            * Compression by gathering.

        .. versionadded:: (cfdm) 1.7.11

        :Parameters:

            {{inplace: `bool`, optional}}

        :Returns:

            `{{class}}` or `None`
                The uncompressed construct, or `None` if the operation
                was in-place.

        **Examples**

        >>> f.data.get_compression_type()
        'ragged contiguous'
        >>> g = f.uncompress()
        >>> g.data.get_compression_type()
        ''
        >>> g.equals(f)
        True

        """
        v = _inplace_enabled_define_and_cleanup(self)
        super(PropertiesDataBounds, v).uncompress(inplace=True)

        bounds = v.get_bounds(None)
        if bounds is not None:
            bounds.uncompress(inplace=True)

        return v
