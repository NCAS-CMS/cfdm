import logging

from ..data import Data
from ..decorators import (
    _display_or_return,
    _inplace_enabled,
    _inplace_enabled_define_and_cleanup,
    _manage_log_level_via_verbosity,
    _test_decorator_args,
)
from ..functions import _DEPRECATION_ERROR_METHOD
from . import Properties

logger = logging.getLogger(__name__)


class PropertiesData(Properties):
    """Mixin class for a data array with descriptive properties.

    .. versionadded:: (cfdm) 1.7.0

    """

    def __new__(cls, *args, **kwargs):
        """Store component classes."""
        instance = super().__new__(cls)
        instance._Data = Data
        return instance

    def __getitem__(self, indices):
        """Return a subspace defined by indices.

        f.__getitem__(indices) <==> f[indices]

        Indexing follows rules that are very similar to the numpy
        indexing rules, the only differences being:

        * An integer index i takes the i-th element but does not
          reduce the rank by one.

        * When two or more dimensions' indices are sequences of
          integers then these indices work independently along each
          dimension (similar to the way vector subscripts work in
          Fortran). This is the same behaviour as indexing on a
          Variable object of the netCDF4 package.

        .. versionadded:: (cfdm) 1.7.0

        :Returns:

                The subspace.

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
        new = self.copy()

        data = self.get_data(None, _fill_value=False)
        if data is not None:
            new.set_data(data[indices], copy=False)

        return new

    def __str__(self):
        """Called by the `str` built-in function.

        x.__str__() <==> str(x)

        .. versionadded:: (cfdm) 1.7.0

        """
        data = self.get_data(None, _units=False, _fill_value=False)
        if data is not None:
            dims = ", ".join([str(x) for x in data.shape])
            dims = f"({dims})"
        else:
            dims = ""

        # Units
        units = self.get_property("units", "")
        if units is None:
            isreftime = bool(self.get_property("calendar", False))
        else:
            isreftime = "since" in str(units)

        if isreftime:
            units += " " + self.get_property("calendar", "")

        return f"{self.identity('')}{dims} {units}"

    def _parse_axes(self, axes):
        """Conform axes.

        :Parameters:

            axes: (sequence of) `int`
                {{axes int examples}}

        :Returns:

            `list`
                The conformed axes.

        """
        if axes is None:
            return axes

        if isinstance(axes, int):
            axes = (axes,)

        ndim = self.ndim

        return [(i + ndim if i < 0 else i) for i in axes]

    @classmethod
    def _test_docstring_substitution_classmethod(cls, arg1, arg2):
        """Test docstring substitution on with @classmethod.

            {{inplace: `bool`, optional}}

        {{package}}.{{class}}

        """
        return (arg1, arg2)

    @staticmethod
    def _test_docstring_substitution_staticmethod(arg1, arg2):
        """Test docstring substitution on with @staticmethod.

            {{inplace: `bool`, optional}}

        {{package}}.{{class}}

        """
        return (arg1, arg2)

    def _test_docstring_substitution_3(self, arg1, arg2):
        """Test docstring substitution 3.

            {{inplace: `bool`, optional}}

        {{package}}.{{class}}

        """
        return self.__class__._test_docstring_substitution_staticmethod(
            arg1, arg2
        )

    def _test_docstring_substitution_4(self, arg1, arg2):
        """Test docstring substitution 4.

            {{inplace: `bool`, optional}}

        {{package}}.{{class}}

        """
        return self._test_docstring_substitution_classmethod(arg1, arg2)

    @_test_decorator_args("i")
    @_inplace_enabled(default=False)
    def _test_docstring_substitution(self, inplace=False, verbose=None):
        """Test docstring substitution with two decorators.

        {{inplace: `bool`, optional}}

        {{package}}.{{class}}

        """
        print("In _test_docstring_substitution")

    @property
    def array(self):
        """A numpy array deep copy of the data.

        Changing the returned numpy array does not change the data
        array.

        .. versionadded:: (cfdm) 1.10.0.0

        .. seealso:: `data`, `datetime_array`

        **Examples**

        >>> f.data
        <{{repr}}Data(5): [0, ... 4] kg m-1 s-2>
        >>> a = f.array
        >>> type(a)
        <type 'numpy.ndarray'>
        >>> print(a)
        [0 1 2 3 4]
        >>> a[0] = 999
        >>> print(a)
        [999 1 2 3 4]
        >>> print(f.array)
        [0 1 2 3 4]
        >>> f.data
        <{{repr}}Data(5): [0, ... 4] kg m-1 s-2>

        """
        data = self.get_data(None)
        if data is None:
            raise AttributeError(f"{self.__class__.__name__} has no data")

        return data.array

    @property
    def datetime_array(self):
        """An independent numpy array of date-time objects.

        Only applicable for data with reference time units.

        If the calendar has not been set then the CF default calendar
        will be used and the units will be updated accordingly.

        .. versionadded:: (cfdm) 1.10.0.0

        .. seealso:: `array`, `data`

        **Examples**

        >>> f.units
        'days since 2000-01-01'
        >>> print(f.array)
        [ 0 31 60 91]
        >>> print(f.datetime_array)
        [cftime.DatetimeGregorian(2000-01-01 00:00:00)
         cftime.DatetimeGregorian(2000-02-01 00:00:00)
         cftime.DatetimeGregorian(2000-03-01 00:00:00)
         cftime.DatetimeGregorian(2000-04-01 00:00:00)]

        """
        data = self.get_data(None)
        if data is None:
            raise AttributeError(f"{self.__class__.__name__} has no data")

        return data.datetime_array

    @_inplace_enabled(default=False)
    def apply_masking(self, inplace=False):
        """Apply masking as defined by the CF conventions.

        Masking is applied according to any of the following criteria that
        are applicable:

        * where data elements are equal to the value of the
          ``missing_value`` property;

        * where data elements are equal to the value of the ``_FillValue``
          property;

        * where data elements are strictly less than the value of the
          ``valid_min`` property;

        * where data elements are strictly greater than the value of the
          ``valid_max`` property;

        * where data elements are within the inclusive range specified by
          the two values of ``valid_range`` property.

        If any of the above properties have not been set the no masking is
        applied for that method.

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

                A new instance with masked values, or `None` if the
                operation was in-place.

        **Examples**

        >>> print(v.data.array)
        [9.96920997e+36, 9.96920997e+36, 9.96920997e+36, 9.96920997e+36,
         9.96920997e+36, 9.96920997e+36, 9.96920997e+36, 9.96920997e+36],
         [0.023 0.036 0.045 0.062 0.046 0.073 0.006 0.066]
         [0.11  0.131 0.124 0.146 0.087 0.103 0.057 0.011]
         [0.029 0.059 0.039 0.07  0.058 0.072 0.009 0.017]
        [9.96920997e+36, 9.96920997e+36, 9.96920997e+36, 9.96920997e+36,
         9.96920997e+36, 9.96920997e+36, 9.96920997e+36, 9.96920997e+36]])
        >>> masked_v = v.apply_masking()
        >>> print(masked_v.data.array)
        [[   --    --    --    --    --    --    --    --]
         [0.023 0.036 0.045 0.062 0.046 0.073 0.006 0.066]
         [0.11  0.131 0.124 0.146 0.087 0.103 0.057 0.011]
         [0.029 0.059 0.039 0.07  0.058 0.072 0.009 0.017]
         [   --    --    --    --    --    --    --    --]]

        """
        v = _inplace_enabled_define_and_cleanup(self)

        data = v.get_data(None, _units=False, _fill_value=False)
        if data is not None:
            fill_values = []
            for prop in ("_FillValue", "missing_value"):
                x = v.get_property(prop, None)
                if x is not None:
                    fill_values.append(x)

            kwargs = {"inplace": True, "fill_values": fill_values}

            for prop in ("valid_min", "valid_max", "valid_range"):
                kwargs[prop] = v.get_property(prop, None)

            if kwargs["valid_range"] is not None and (
                kwargs["valid_min"] is not None
                or kwargs["valid_max"] is not None
            ):
                raise ValueError(
                    "Can't apply masking when the 'valid_range' property "
                    "has been set as well as either of the "
                    "'valid_min' or 'valid_max' properties"
                )

            data.apply_masking(**kwargs)

        return v

    @classmethod
    def concatenate(
        cls,
        variables,
        axis=0,
        cull_graph=False,
        relaxed_units=False,
        copy=True,
    ):
        """Join a together sequence of `{{class}}`.

        .. versionadded:: (cfdm) 1.12.0.0

        .. seealso:: `Data.concatenate`, `Data.cull_graph`

        :Parameters:

            variables: sequence of constructs.

            axis: `int`, optional
                Select the axis along which to concatenate, defined
                by its position in the data array. By default
                concatenation is along the axis in position 0.

            {{cull_graph: `bool`, optional}}

            {{relaxed_units: `bool`, optional}}

            {{concatenate copy: `bool`, optional}}

        :Returns:

            `{{class}}`
                The concatenated construct.

        """
        out = variables[0]
        if copy:
            out = out.copy()

        if len(variables) == 1:
            return out

        data = out.get_data(_fill_value=False, _units=False)
        new_data = type(data).concatenate(
            [v.get_data(_fill_value=False) for v in variables],
            axis=axis,
            cull_graph=cull_graph,
            relaxed_units=relaxed_units,
            copy=copy,
        )
        out.set_data(new_data, copy=False)
        return out

    def creation_commands(
        self,
        representative_data=False,
        namespace=None,
        indent=0,
        string=True,
        name="c",
        data_name="data",
        quantization_name="q",
        header=True,
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

            quantization_name: `str`, optional
                The name of the construct's `Quantization` instance
                created by the returned commands.

                .. versionadded:: (cfdm) 1.12.2.0

            {{header: `bool`, optional}}

        :Returns:

            {{returns creation_commands}}

        **Examples**

        >>> x = {{package}}.{{class}}(
        ...     properties={'units': 'Kelvin',
        ...                 'standard_name': 'air_temperature'}
        ... )
        >>> x.set_data([271.15, 274.15, 280])
        >>> print(x.creation_commands(header=False))
        c = {{package}}.{{class}}()
        c.set_properties({'units': 'Kelvin', 'standard_name': 'air_temperature'})
        data = {{package}}.Data([271.15, 274.15, 280.0], units='Kelvin', dtype='f8')
        c.set_data(data)

        """
        if name in (data_name, quantization_name):
            raise ValueError(
                "The 'name' parameter can not have the same value as "
                "either of the 'data_name' or 'quantization_name': "
                f"keywords: {name!r}"
            )

        if data_name == quantization_name:
            raise ValueError(
                "The 'data_name' parameter can not have the same value as "
                f"'quantization_name' keyword: {data_name!r}"
            )

        namespace0 = namespace
        if namespace is None:
            namespace = self._package() + "."
        elif namespace and not namespace.endswith("."):
            namespace += "."

        out = super().creation_commands(
            namespace=namespace,
            indent=indent,
            string=False,
            name=name,
            header=header,
        )

        data = self.get_data(None)
        if data is not None:
            if representative_data:
                out.append(f"{data_name} = {data!r}  # Representative data")
            else:
                out.extend(
                    data.creation_commands(
                        name=data_name,
                        namespace=namespace0,
                        indent=indent,
                        string=False,
                    )
                )

            out.append(f"{name}.set_data({data_name})")

        # Quantization
        q = self.get_quantization(None)
        if q is not None:
            out.extend(
                q.creation_commands(
                    namespace=namespace0,
                    indent=indent,
                    string=False,
                    name=quantization_name,
                    header=False,
                )
            )
            out.append(f"{name}._set_quantization({quantization_name})")

        if string:
            indent = " " * indent
            out[0] = indent + out[0]
            out = ("\n" + indent).join(out)

        return out

    @_display_or_return
    def dump(
        self,
        display=True,
        _key=None,
        _omit_properties=(),
        _prefix="",
        _title=None,
        _create_title=True,
        _level=0,
        _axes=None,
        _axis_names=None,
    ):
        """A full description.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            display: `bool`, optional
                If False then return the description as a string. By
                default the description is printed.

        :Returns:

            {{returns dump}}

        """
        # Properties
        string = super().dump(
            display=False,
            _key=_key,
            _omit_properties=_omit_properties,
            _prefix=_prefix,
            _title=_title,
            _create_title=_create_title,
            _level=_level,
        )
        if string:
            string = [string]
        else:
            string = []

        indent1 = "    " * (_level + 1)

        # Data
        data = self.get_data(None)
        if data is not None:
            if _axes and _axis_names:
                x = [_axis_names[axis] for axis in _axes]
                ndim = data.ndim
                x = x[:ndim]
                if len(x) < ndim:
                    x.extend([str(size) for size in data.shape[len(x) :]])
            else:
                x = [str(size) for size in data.shape]

            shape = ", ".join(x)

            string.append(f"{indent1}{_prefix}Data({shape}) = {data}")

        # Quantization
        q = self.get_quantization(None)
        if q is not None:
            string.append(q.dump(display=False, _level=_level + 1))

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

        {{equals tolerance}}

        Any type of object may be tested but, in general, equality is
        only possible with another object of the same type, or a
        subclass of one. See the *ignore_type* parameter.

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

        >>> x.equals(x)
        True
        >>> x.equals(x.copy())
        True
        >>> x.equals('something else')
        False

        """
        pp = super()._equals_preprocess(
            other, verbose=verbose, ignore_type=ignore_type
        )
        if pp is True or pp is False:
            return pp

        other = pp

        # ------------------------------------------------------------
        # Check external variables (returning True if both are
        # external with the same netCDF variable name)
        # ------------------------------------------------------------
        external0 = self._get_component("external", False)
        external1 = other._get_component("external", False)
        if external0 != external1:
            logger.info(
                f"{self.__class__.__name__}: Only one external variable)"
            )
            return False

        if external0:
            # Both variables are external
            if self.nc_get_variable(None) != other.nc_get_variable(None):
                logger.info(
                    f"{self.__class__.__name__}: External variables have "
                    "different netCDF variable names: "
                    f"{self.nc_get_variable(None)} != "
                    f"{other.nc_get_variable(None)})"
                )
                return False

            return True

        # ------------------------------------------------------------
        # Check the properties
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
        ):
            return False

        # ------------------------------------------------------------
        # Check the quantization components
        # ------------------------------------------------------------
        q0 = self.get_quantization(None)
        q1 = other.get_quantization(None)
        if not (q0 is None and q1 is None) and not self._equals(q0, q1):
            logger.info(
                f"{self.__class__.__name__}: Different quantization metadata"
            )
            return False

        # ------------------------------------------------------------
        # Check the data
        # ------------------------------------------------------------
        if self.has_data() != other.has_data():
            logger.info(
                f"{self.__class__.__name__}: Different data: Only one has data"
            )
            return False

        if self.has_data():
            if not self._equals(
                self.get_data(),
                other.get_data(),
                rtol=rtol,
                atol=atol,
                verbose=verbose,
                ignore_data_type=ignore_data_type,
                ignore_fill_value=ignore_fill_value,
                ignore_compression=ignore_compression,
            ):
                logger.info(f"{self.__class__.__name__}: Different data")
                return False

        return True

    def file_directories(self):
        """The directories of files containing parts of the data.

        Returns the locations of any files referenced by the data.

        .. versionadded:: (cfdm) 1.12.0.0

        .. seealso:: `get_filenames`, `replace_directory`

        :Returns:

            `set`
                The unique set of file directories as absolute paths.

        **Examples**

        >>> d.file_directories()
        {'/home/data1', 'file:///data2'}

        """
        data = self.get_data(None, _fill_value=False, _units=False)
        if data is not None:
            return data.file_directories()

        return set()

    def get_filenames(self, normalise=True):
        """Return the name of the file or files containing the data.

        :Parameters:

            {{normalise: `bool`, optional}}

                .. versionadded:: (cfdm) 1.12.0.0

        :Returns:

            `set` The file names in normalised, absolute form. If the
                data are in memory then an empty `set` is returned.

        """
        data = self.get_data(None, _units=False, _fill_value=False)
        if data is not None:
            return data.get_filenames(normalise=normalise)

        return set()

    def get_quantization(self, default=ValueError()):
        """Get quantization metadata.

        Quantization eliminates false precision, usually by rounding
        the least significant bits of floating-point mantissas to
        zeros, so that a subsequent compression on disk is more
        efficient.

        `{{class}}` data can not be quantized, so the default is
        always returned.

        .. versionadded:: (cfdm) 1.12.2.0

        .. seealso:: `get_quantize_on_write`

        :Parameters:

            default: optional
                Return the value of the *default* keyword, because
                there is no quantization metadata.

                {{default Exception}}

        :Returns:

                The default.

                {{default Exception}}

        """
        if default is None:
            return

        return self._default(
            default,
            message=f"{self.__class__.__name__} has no quantization metadata",
        )

    def get_quantize_on_write(self, default=ValueError()):
        """Get a quantize-on-write instruction.

        Quantization eliminates false precision, usually by rounding
        the least significant bits of floating-point mantissas to
        zeros, so that a subsequent compression on disk is more
        efficient.

        `{{class}}` data can not be quantized, so the default is
        always returned.

        .. versionadded:: (cfdm) 1.12.2.0

        .. seealso:: `get_quantization`

        :Parameters:

            default: optional
                Return the value of the *default* keyword, because
                there is no quantize-on-write instruction.

                {{default Exception}}

        :Returns:

                The default.

                {{default Exception}}

        """
        if default is None:
            return

        return self._default(
            default,
            message=f"{self.__class__.__name__} has no "
            "quantize-on-write instruction",
        )

    @_inplace_enabled(default=False)
    def insert_dimension(self, position=0, inplace=False):
        """Expand the shape of the data array.

        Inserts a new size 1 axis into the data array.

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
                A new instance with expanded data axes. If the
                operation was in-place then `None` is returned.

        **Examples**

        >>> f.shape
        (19, 73, 96)
        >>> f.insert_dimension(position=3).shape
        (19, 73, 96, 1)
        >>> f.insert_dimension(position=-1).shape
        (19, 73, 1, 96)

        """
        v = _inplace_enabled_define_and_cleanup(self)

        data = v.get_data(None, _units=False, _fill_value=False)
        if data is not None:
            data.insert_dimension(position, inplace=True)

        return v

    def nc_clear_dataset_chunksizes(self):
        """Clear the dataset chunking strategy for the data.

        .. versionadded:: (cfdm) 1.12.2.0

        .. seealso:: `nc_dataset_chunksizes`,
                     `nc_set_dataset_chunksizes`, `{{package}}.read`,
                     `{{package}}.write`

        :Returns:

            `None` or `str` or `int` or `tuple` of `int`
                The chunking strategy prior to being cleared, as would
                be returned by `nc_dataset_chunksizes`.

        """
        data = self.get_data(None, _units=False, _fill_value=False)
        if data is not None:
            return data.nc_clear_dataset_chunksizes()

    def nc_clear_hdf5_chunksizes(self):
        """Clear the HDF5 chunking strategy for the data.

        Deprecated at version 1.12.2.0 and is no longer
        available. Use `nc_clear_dataset_chunksizes` instead.

        .. versionadded:: (cfdm) 1.12.0.0

        """
        _DEPRECATION_ERROR_METHOD(
            self,
            "nc_clear_hdf5_chunksizes",
            "Use `nc_clear_dataset_chunksizes` instead.",
            version="1.12.2.0",
            removed_at="5.0.0",
        )  # pragma: no cover

    def nc_hdf5_chunksizes(self, todict=False):
        """Get the HDF5 chunking strategy for the data.

        Deprecated at version 1.12.2.0 and is no longer
        available. Use `nc_dataset_chunksizes` instead.

        .. versionadded:: (cfdm) 1.11.2.0

        """
        _DEPRECATION_ERROR_METHOD(
            self,
            "nc_hdf5_chunksizes",
            "Use `nc_dataset_chunksizes` instead.",
            version="1.12.2.0",
            removed_at="5.0.0",
        )  # pragma: no cover

    def nc_dataset_chunksizes(self, todict=False):
        """Get the dataset chunking strategy for the data.

        .. versionadded:: (cfdm) 1.12.2.0

        .. seealso:: `nc_clear_dataset_chunksizes`,
                     `nc_set_dataset_chunksizes`, `{{package}}.read`,
                     `{{package}}.write`

        :Parameters:

            {{chunk todict: `bool`, optional}}

        :Returns:

            {{Returns nc_dataset_chunksizes}}

        """
        data = self.get_data(None, _units=False, _fill_value=False)
        if data is not None:
            return data.nc_dataset_chunksizes(todict=todict)

    def nc_set_dataset_chunksizes(self, chunksizes):
        """Set the dataset chunking strategy.

        .. versionadded:: (cfdm) 1.12.2.0

        .. seealso:: `nc_dataset_chunksizes`,
                     `nc_clear_dataset_chunksizes`,
                     `{{package}}.read`, `{{package}}.write`

        :Parameters:

            {{chunk chunksizes}}

                  Each dictionary key is an integer that specifies an
                  axis by its position in the data array.

        :Returns:

            `None`

        """
        data = self.get_data(None, _units=False, _fill_value=False)
        if data is not None:
            data.nc_set_dataset_chunksizes(chunksizes)

    def nc_set_hdf5_chunksizes(self, chunksizes):
        """Set the HDF5 chunking strategy.

        Deprecated at version 1.12.2.0 and is no longer
        available. Use `nc_set_dataset_chunksizes` instead.

        .. versionadded:: (cfdm) 1.11.2.0

        """
        _DEPRECATION_ERROR_METHOD(
            self,
            "nc_set_hdf5_chunksizes",
            "Use `nc_set_dataset_chunksizes` instead.",
            version="1.12.2.0",
            removed_at="5.0.0",
        )  # pragma: no cover

    @_inplace_enabled(default=False)
    def persist(self, inplace=False):
        """Persist data into memory.

        {{persist description}}

        **Performance**

        `persist` causes delayed operations to be computed.

        .. versionadded:: (cfdm) 1.12.0.0

        .. seealso:: `array`, `datetime_array`,
                     `{{package}}.Data.persist`

        :Parameters:

            {{inplace: `bool`, optional}}

        :Returns:

            `{{class}}` or `None`
                The construct with persisted data. If the operation
                was in-place then `None` is returned.

        """
        v = _inplace_enabled_define_and_cleanup(self)

        data = v.get_data(None)
        if data is not None:
            data.persist(inplace=True)

        return v

    def replace_directory(
        self,
        old=None,
        new=None,
        normalise=False,
        common=False,
    ):
        """Replace a file directory in-place.

        .. versionadded:: (cfdm) 1.12.0.0

        .. seealso:: `file_directories`, `get_filenames`

        :Parameters:

            {{replace old: `str` or `None`, optional}}

            {{replace new: `str` or `None`, optional}}

            {{replace normalise: `bool`, optional}}

            common: `bool`, optional
                If True the base directory structure that is common to
                all files with *new*.

        :Returns:

            `None`

        """
        data = self.get_data(None, _fill_value=False, _units=False)
        if data is not None:
            return data.replace_directory(
                old=old, new=new, normalise=normalise, common=common
            )

    @_inplace_enabled(default=False)
    def squeeze(self, axes=None, inplace=False):
        """Remove size one axes from the data array.

        By default all size one axes are removed, but particular size
        one axes may be selected for removal.

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
                A new instance with removed size 1 one data axes. If
                the operation was in-place then `None` is returned.

        **Examples**


        >>> f = {{package}}.{{class}}()
        >>> d = {{package}}.Data(numpy.arange(7008).reshape((1, 73, 1, 96)))
        >>> f.set_data(d)
        >>> f.shape
        (1, 73, 1, 96)
        >>> f.squeeze().shape
        (73, 96)
        >>> f.squeeze(0).shape
        (73, 1, 96)
        >>> f.squeeze([-3, 2]).shape
        (73, 96)

        """
        v = _inplace_enabled_define_and_cleanup(self)

        data = v.get_data(None, _units=False, _fill_value=False)
        if data is not None:
            data.squeeze(axes, inplace=True)

        return v

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
        v = _inplace_enabled_define_and_cleanup(self)

        data = v.get_data(None)
        if data is not None:
            data.to_memory(inplace=True)

        return v

    @_inplace_enabled(default=False)
    def transpose(self, axes=None, inplace=False):
        """Permute the axes of the data array.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `insert_dimension`, `squeeze`

        :Parameters:

            axes: (sequence of) `int`, optional
                The new axis order. By default the order is reversed.

                {{axes int examples}}

            {{inplace: `bool`, optional}}

        :Returns:

            `{{class}}` or `None`
                A new instance with permuted data axes. If the operation
                was in-place then `None` is returned.

        **Examples**

        >>> f.shape
        (19, 73, 96)
        >>> f.transpose().shape
        (96, 73, 19)
        >>> f.transpose([1, 0, 2]).shape
        (73, 19, 96)

        """
        v = _inplace_enabled_define_and_cleanup(self)
        data = v.get_data(None, _units=False, _fill_value=False)
        if data is not None:
            data.transpose(axes, inplace=True)

        return v

    @_inplace_enabled(default=False)
    def uncompress(self, inplace=False):
        """Uncompress the construct.

        Whether or not the construct is compressed does not alter its
        functionality nor external appearance.

        A construct that is already uncompressed will be returned
        uncompressed.

        The following type of compression are available:

            * Ragged arrays for discrete sampling geometries
              (DSG). Three different types of ragged array
              representation are supported.

            ..

            * Compression by gathering.

            ..

            * Compression by coordinate subsampling

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
        f = _inplace_enabled_define_and_cleanup(self)

        data = f.get_data(None, _units=False, _fill_value=False)
        if data is not None:
            data.uncompress(inplace=True)

        return f
