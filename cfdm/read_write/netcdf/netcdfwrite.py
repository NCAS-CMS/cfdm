import copy
import logging
import os
import re
from distutils.version import LooseVersion

import netCDF4
import numpy

from ...decorators import _manage_log_level_via_verbosity
from .. import IOWrite
from .netcdfread import NetCDFRead

logger = logging.getLogger(__name__)


class NetCDFWrite(IOWrite):
    """A container for writing Fields to a netCDF dataset."""

    def cf_description_of_file_contents_attributes(self):
        """Description of file contents properties."""
        return (
            "comment",
            "Conventions",
            "featureType",
            "history",
            "institution",
            "references",
            "source",
            "title",
        )

    def cf_geometry_types(self):
        """Geometry types.

        .. versionadded:: (cfdm) 1.8.0

        """
        return set(
            (
                "point",
                "line",
                "polygon",
            )
        )

    def cf_cell_method_qualifiers(self):
        """Cell method qualifiers."""
        return set(
            (
                "within",
                "where",
                "over",
                "interval",
                "comment",
            )
        )

    def _create_netcdf_group(self, nc, group_name):
        """Creates a new netCDF4 group object.

        .. versionadded:: (cfdm) 1.8.6.0

        :Parameters:

            nc: `netCDF4._netCDF4.Group` or `netCDF4.Dataset`

            group_name: `str`
                The name of the group.

        :Returns:

            `netCDF4._netCDF4.Group`
                The new group object.

        """
        return nc.createGroup(group_name)

    def _create_netcdf_variable_name(self, parent, default):
        #                            force_use_existing=False):
        """Create an appropriate name for a netCDF variable.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            parent:

            default: `str`

        :Returns:

            `str`
                The netCDF variable name.

        """
        ncvar = self.implementation.nc_get_variable(parent, None)

        #        if force_use_existing:
        #            if ncvar is None:
        #                raise ValueError()
        #
        #            return ncvar

        if ncvar is None:
            try:
                ncvar = self.implementation.get_property(
                    parent, "standard_name", default
                )
            except AttributeError:
                ncvar = default
        elif not self.write_vars["group"]:
            # A flat file has been requested, so strip off any group
            # structure from the name.
            ncvar = self._remove_group_structure(ncvar)

        return self._netcdf_name(ncvar)

    def _netcdf_name(self, base, dimsize=None, role=None):
        """Return a new netCDF variable or dimension name.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            base: `str`

            dimsize: `int`, optional

            role: `str`, optional

        :Returns:

            `str`
                NetCDF dimension name or netCDF variable name.

        """
        if base is None:
            return

        g = self.write_vars

        ncvar_names = g["ncvar_names"]
        ncdim_names = g["ncdim_to_size"]

        existing_names = g["ncvar_names"].union(ncdim_names)

        if dimsize is not None:
            if not role:
                raise ValueError("Must supply role when providing dimsize")

            #            if base in g['dimensions_with_role'].get(role, ()):
            #                if base in ncdim_names and dimsize == g['ncdim_to_size'][base]:
            #                    # Return the name of an existing netCDF dimension
            #                    # with this name, this size, and matching the
            #                    # given role.
            #                    return base
            for ncdim in g["dimensions_with_role"].get(role, ()):
                if g["ncdim_to_size"][ncdim] == dimsize:
                    # Return the name of an existing netCDF dimension
                    # with this name, this size, and matching the
                    # given role.
                    return ncdim

        if base in existing_names:
            counter = g.setdefault("count_" + base, 1)

            ncvar = f"{base}_{counter}"
            while ncvar in existing_names:
                counter += 1
                ncvar = f"{base}_{counter}"
        else:
            ncvar = base

        ncvar = ncvar.replace(" ", "_")

        ncvar_names.add(ncvar)

        if role and dimsize is not None:
            g["dimensions_with_role"].setdefault(role, []).append(ncvar)

        return ncvar

    def _numpy_compressed(self, array):
        """Return all the non-masked data as a 1-d array.

        .. versionadded:: (cfdm) 1.8.0

        :Parameters:

            array: `numpy.ndarray`
               A numpy array, that may or may not be masked.

        :Returns:

            `numpy.ndarray`
                The compressed numpy array.

        **Examples:**

        >>> x = numpy.ma.array(numpy.arange(5), mask=[0]*2 + [1]*3)
        >>> c = n._numpy_compressed(x)
        >>> c
        array([0, 1])
        >>> type(c)
        <type 'numpy.ndarray'>

        """
        if numpy.ma.isMA(array):
            return array.compressed()

        return array.flatten()

    def _write_attributes(self, parent, ncvar, extra=None, omit=()):
        """Write netCDF attributes to the netCDF file.

        :Parameters:

            parent:

            ncvar: `str`

            extra: `dict`, optional

            omit: sequence of `str`, optional

        :Returns:

            `dict`

        """
        # To avoid mutable default argument (an anti-pattern) of extra={}
        if extra is None:
            extra = {}
        g = self.write_vars

        if parent is None:
            netcdf_attrs = {}
        else:
            netcdf_attrs = self.implementation.get_properties(parent)

        netcdf_attrs.update(extra)

        for attr in omit:
            netcdf_attrs.pop(attr, None)

        if not netcdf_attrs:
            return {}

        # Make sure that _FillValue and missing data have the same
        # data type as the data
        for attr in ("_FillValue", "missing_value"):
            if attr not in netcdf_attrs:
                continue

            data = self.implementation.get_data(parent, None)
            if data is not None:
                dtype = g["datatype"].get(data.dtype, data.dtype)
                netcdf_attrs[attr] = numpy.array(
                    netcdf_attrs[attr], dtype=dtype
                )

        skip_set_fill_value = False
        if g["post_dry_run"] and parent is not None:
            # Manage possibly pre-existing fill values:
            data = self.implementation.get_data(parent, None)
            if data is not None:
                # Check if there is already a fill value applied to the data,
                # and if so, that it is compatible with the one set to be set:
                if data.has_fill_value() and "_FillValue" in netcdf_attrs:
                    if data.get_fill_value() == netcdf_attrs["_FillValue"]:
                        # The fill value to be set is the same as the one
                        # that already applies to the already-set data,
                        # so we should not (and indeed can't) set it again.
                        skip_set_fill_value = True
                    else:  # can't have incompatible FV to the existing data
                        raise ValueError(
                            "Cannot set an incompatible fill value on "
                            "data with a fill value already defined."
                        )

            if skip_set_fill_value and "_FillValue" in netcdf_attrs:
                del netcdf_attrs["_FillValue"]

        if not g["dry_run"]:
            g["nc"][ncvar].setncatts(netcdf_attrs)

        if skip_set_fill_value:
            # Re-add as known attribute since this FV is already set
            netcdf_attrs["_FillValue"] = self.implementation.get_data(
                parent, None
            ).get_fill_value()

        return netcdf_attrs

    def _character_array(self, array):
        """Converts a numpy array of strings to character data type.

        As well as the data type conversion from string to character,
        the output numpy character array is given an extra trailing
        dimension.

        :Parameters:

            array: `numpy.ndarray`

        :Returns:

            `numpy.ndarray`

        **Examples:**

        >>> print(a, a.shape, a.dtype.itemsize)
        ['fu' 'bar'] (2,) 3
        >>> b = _character_array(a)
        >>> print(b, b.shape, b.dtype.itemsize)
        [['f' 'u' ' ']
         ['b' 'a' 'r']] (2, 3) 1

        >>> print(a, a.shape, a.dtype.itemsize)
        [-- 'bar'] (2,) 3
        >>> b = _character_array(a)
        >>> print(b, b.shape, b.dtype.itemsize)
        [[-- -- --]
         ['b' 'a' 'r']] (2, 3) 1

        """
        #        strlen = array.dtype.itemsize
        original_shape = array.shape
        original_size = array.size

        masked = numpy.ma.isMA(array)
        if masked:
            fill_value = array.fill_value
            array = numpy.ma.filled(array, fill_value="")

        if array.dtype.kind == "U":
            array = array.astype("S")

        array = numpy.array(tuple(array.tobytes().decode("ascii")), dtype="S1")

        #        else:
        #            # dtype is 'U'
        #            x = []
        #            for s in array.flatten():
        #                x.extend(tuple(s.ljust(N, '\x00')))
        #
        #            array = numpy.array(k, dtype='S1')

        array.resize(original_shape + (array.size // original_size,))
        #        if masked:
        #            array = numpy.ma.array(array, mask=mask, fill_value=fill_value)

        #        if array.dtype.kind == 'U':
        #            # Convert unicode to string
        #            array = array.astype('S')
        #
        #        new = netCDF4.stringtochar(array, encoding='none')

        if masked:
            array = numpy.ma.masked_where(array == "", array)
            array.set_fill_value(fill_value)

        if array.dtype.kind != "S":
            raise ValueError("Array must have string data type.")

        #            new = numpy.ma.array(new, mask=mask, fill_value=fill_value)

        #        new = numpy.ma.masked_all(shape + (strlen,), dtype='S1')
        #
        #        for index in numpy.ndindex(shape):
        #            value = array[index]
        #            if value is numpy.ma.masked:
        #                new[index] = numpy.ma.masked
        #            else:
        #                new[index] = tuple(value.ljust(strlen, ' '))

        return array

    def _datatype(self, variable):
        """Returns the input variable array's netCDF4-like data type.

        Specifically return the `netCDF4.createVariable` data type
        corresponding to the data type of the array of the input
        variable.

        For example, if variable.dtype is 'float32', then 'f4' will be
        returned.

        For a NETCDF4 or CFA4 format file, numpy string data types will
        either return `str` regardless of the numpy string length (and a
        netCDF4 string type variable will be created) or, if
        `self.write_vars['string']`` is `False`, ``'S1'`` (see below).

        For all other output netCDF formats (such NETCDF4_CLASSIC,
        NETCDF3_64BIT, etc.) numpy string data types will return 'S1'
        regardless of the numpy string length. This means that the
        required conversion of multi-character datatype numpy arrays into
        single-character datatype numpy arrays (with an extra trailing
        dimension) is expected to be done elsewhere (currently in the
        _write_netcdf_variable method).

        If the input variable has no `!dtype` attribute (or it is None)
        then 'S1' is returned, or `str` for NETCDF files.

        :Parameters:

            variable:
                A numpy array or an object with a `get_data` method.

        :Returns:

           `str` or str
               The `netCDF4.createVariable` data type corresponding to the
               datatype of the array of the input variable.

        """
        g = self.write_vars

        if not isinstance(variable, numpy.ndarray):
            data = self.implementation.get_data(variable, None)
            if data is None:
                return "S1"
        else:
            data = variable

        dtype = getattr(data, "dtype", None)
        if dtype is None or dtype.kind in "SU":
            if g["fmt"] == "NETCDF4" and g["string"]:
                return str

            return "S1"

        new_dtype = g["datatype"].get(dtype, None)
        if new_dtype is not None:
            dtype = new_dtype

        return f"{dtype.kind}{dtype.itemsize}"

    def _string_length_dimension(self, size):
        """Creates a netCDF dimension for string variables if necessary.

        :Parameters:

            size: `int`

        :Returns:

            `str`
                The netCDF dimension name.

        """
        g = self.write_vars

        # ------------------------------------------------------------
        # Create a new dimension for the maximum string length
        # ------------------------------------------------------------
        ncdim = self._netcdf_name(
            f"strlen{size}", dimsize=size, role="string_length"
        )

        if ncdim not in g["ncdim_to_size"]:
            # This string length dimension needs creating
            g["ncdim_to_size"][ncdim] = size

            # Define (and create if necessary) the group in which to
            # place this netCDF dimension.
            parent_group = self._parent_group(ncdim)

            if not g["dry_run"]:
                try:
                    parent_group.createDimension(ncdim, size)
                except RuntimeError:
                    pass  # TODO convert to 'raise' via fixes upstream

        return ncdim

    def _netcdf_dimensions(self, field, key, construct):
        """Returns the netCDF dimension names for the construct axes.

        The names are returned in a tuple. If the metadata construct
        has no data, then `None` is returned.

        :Parameters:

            field: Field construct

            key: `str`

        :Returns:

            `tuple` or `None`
                The netCDF dimension names, or `None` if there are no
                data.

        """
        g = self.write_vars

        domain_axes = self.implementation.get_construct_data_axes(field, key)
        if domain_axes is None:
            # No data
            return

        domain_axes = tuple(domain_axes)

        ncdims = [g["axis_to_ncdim"][axis] for axis in domain_axes]

        compression_type = self.implementation.get_compression_type(construct)
        if compression_type:
            sample_dimension_position = (
                self.implementation.get_sample_dimension_position(construct)
            )
            compressed_axes = tuple(
                self.implementation.get_compressed_axes(field, key, construct)
            )
            compressed_ncdims = tuple(
                [g["axis_to_ncdim"][axis] for axis in compressed_axes]
            )
            sample_ncdim = g["sample_ncdim"].get(compressed_ncdims)

            if compression_type == "gathered":
                # ----------------------------------------------------
                # Compression by gathering
                # ----------------------------------------------------
                if sample_ncdim is None:
                    # The list variable has not yet been written to
                    # the file, so write it and also get the netCDF
                    # name of the sample dimension.
                    list_variable = self.implementation.get_list(construct)
                    sample_ncdim = self._write_list_variable(
                        field,
                        list_variable,
                        compress=" ".join(compressed_ncdims),
                    )
                    g["sample_ncdim"][compressed_ncdims] = sample_ncdim

            elif compression_type == "ragged contiguous":
                # ----------------------------------------------------
                # Compression by contiguous ragged array
                #
                # No need to do anything because i) the count variable
                # has already been written to the file, ii) we already
                # have the position of the sample dimension in the
                # compressed array, and iii) we already have the
                # netCDF name of the sample dimension.
                # ----------------------------------------------------
                pass

            elif compression_type == "ragged indexed":
                # ----------------------------------------------------
                # Compression by indexed ragged array
                #
                # No need to do anything because i) the index variable
                # has already been written to the file, ii) we already
                # have the position of the sample dimension in the
                # compressed array, and iii) we already have the
                # netCDF name of the sample dimension.
                # ----------------------------------------------------
                pass
            elif compression_type == "ragged indexed contiguous":
                pass
            else:
                raise ValueError(
                    f"Can't write {construct!r}: Unknown compression "
                    f"type: {compression_type!r}"
                )

            n = len(compressed_ncdims)
            ncdims[
                sample_dimension_position : sample_dimension_position + n
            ] = [sample_ncdim]

        return tuple(ncdims)

    def _write_dimension(
        self, ncdim, f, axis=None, unlimited=False, size=None
    ):
        """Write a netCDF dimension to the file.

        :Parameters:

            ncdim: `str`
                The netCDF dimension name.

            f: Field construct

            axis: `str` or `None`
                The field's domain axis identifier.

            unlimited: `bool`, optional
                If `True` then create an unlimited dimension. By default
                dimensions are not unlimited.

            size: `int`, optional
                Must be set if *axis* is `None`.

        :Returns:

            `None`

        """
        g = self.write_vars

        if axis is not None:
            domain_axis = self.implementation.get_domain_axes(f)[axis]
            logger.info(
                f"    Writing {domain_axis!r} to netCDF dimension: {ncdim}"
            )  # pragma: no cover

            size = self.implementation.get_domain_axis_size(f, axis)
            g["axis_to_ncdim"][axis] = ncdim

        g["ncdim_to_size"][ncdim] = size

        # Define (and create if necessary) the group in which to place
        # this netCDF dimension.
        parent_group = self._parent_group(ncdim)

        if g["group"] and "/" in ncdim:
            # This dimension needs to go into a sub-group so replace
            # its name with its basename (CF>=1.8)
            ncdim = self._remove_group_structure(ncdim)

        if not g["dry_run"]:
            if unlimited:
                # Create an unlimited dimension
                size = None
                try:
                    parent_group.createDimension(ncdim, size)
                except RuntimeError as error:
                    message = (
                        "Can't create unlimited dimension "
                        f"in {g['netcdf'].file_format} file ({error})."
                    )

                    error = str(error)
                    if error == "NetCDF: NC_UNLIMITED size already in use":
                        raise RuntimeError(
                            message
                            + f" In a {g['netcdf'].file_format} file only one "
                            "unlimited dimension is allowed. Consider using "
                            "a netCDF4 format."
                        )

                    raise RuntimeError(message)
            else:
                try:
                    parent_group.createDimension(ncdim, size)
                except RuntimeError as error:
                    raise RuntimeError(
                        f"Can't create size {size} dimension {ncdim!r} in "
                        f"{g['netcdf'].file_format} file ({error})"
                    )

        g["dimensions"].add(ncdim)

    def _write_dimension_coordinate(self, f, key, coord, ncdim, coordinates):
        """Writes a coordinate variable and its bounds variable to file.

        This also writes a new netCDF dimension to the file and, if
        required, a new netCDF dimension for the bounds.

        :Parameters:

            f: Field construct

            key: `str`

            coord: Dimension coordinate construct

            ncdim: `str` or `None`
                The name of the netCDF dimension for this dimension
                coordinate construct, including any groups structure. Note
                that the group structure may be different to the
                corodinate variable, and the basename.

            coordinates: `list`
               This list may get updated in-place.

               .. versionadded:: (cfdm) .8.7.0

        :Returns:

            `str`
                The netCDF name of the dimension coordinate.

        """
        g = self.write_vars

        seen = g["seen"]

        data_axes = self.implementation.get_construct_data_axes(f, key)
        axis = data_axes[0]

        create = False
        if not self._already_in_file(coord):
            create = True
        elif seen[id(coord)]["ncdims"] != ():
            if seen[id(coord)]["ncvar"] != seen[id(coord)]["ncdims"][0]:
                # Already seen this coordinate but it was an auxiliary
                # coordinate, so it needs to be created as a dimension
                # coordinate.
                create = True

        if create:
            # ncvar = self._create_netcdf_variable_name(coord,
            #                                           default='coordinate')
            ncvar = self._create_netcdf_variable_name(coord, default=None)

            if ncvar is None:
                # No netCDF variable name has been set, so use the
                # corresponding netCDF dimension name
                ncvar = ncdim

            if ncvar is None:
                # No netCDF variable name not correponding to a netCDF
                # dimension name has been set, so create a default
                # netCDF variable name.
                ncvar = self._create_netcdf_variable_name(
                    coord, default="coordinate"
                )

            ncdim = ncvar

            # Create a new dimension
            unlimited = self.implementation.nc_is_unlimited_axis(f, axis)

            #            if ncdim is None:
            #                # A netCDF dimension name has NOT been specified, so
            #                # put the dimension in the root group with the same
            #                # name as the coordinate variable.
            #                ncdim = self._remove_group_structure(ncvar)
            #            elif ncdim in g['dimensions']:
            #                # A netCDF dimension name has been specified, but
            #                # matches one already in the file, so put the
            #                # dimension in the root group with the same name as
            #                # the coordinate variable.
            #                ncdim = self._remove_group_structure(ncvar)
            #            else:
            #                ncdim = ncvar
            #            if ncdim is not None:
            #                # A netCDF dimension name HAS been specified, so make
            #                # sure that the basename of the coordinate variable
            #                # matches the basename of the dimension.
            #                if g['group']:
            #                    _, groups = self._remove_group_structure(
            #                        ncvar, return_groups=True)
            #                    ncvar = groups + self._remove_group_structure(ncdim)
            #                else:
            #                    ncvar = ncdim
            #
            #            if g['group']:
            #
            #                _, groups = self._remove_group_structure(
            #                    ncvar, return_groups=True)
            #               ncvar = groups + self._remove_group_structure(ncdim)
            #            else:
            #                ncvar = ncdim

            self._write_dimension(ncdim, f, axis, unlimited=unlimited)

            ncdimensions = self._netcdf_dimensions(f, key, coord)

            # If this dimension coordinate has bounds then write the
            # bounds to the netCDF file and add the 'bounds' or
            # 'climatology' attribute (as appropriate) to a dictionary
            # of extra attributes
            extra = self._write_bounds(f, coord, key, ncdimensions, ncvar)

            # Create a new dimension coordinate variable
            self._write_netcdf_variable(
                ncvar, ncdimensions, coord, extra=extra
            )
        else:
            ncvar = seen[id(coord)]["ncvar"]
            ncdimensions = seen[id(coord)]["ncdims"]

        g["key_to_ncvar"][key] = ncvar
        g["key_to_ncdims"][key] = ncdimensions
        g["axis_to_ncdim"][axis] = seen[id(coord)]["ncdims"][0]

        if g["coordinates"] and ncvar is not None:
            # Add the dimension coordinate netCDF variable name to the
            # 'coordinates' attribute
            coordinates.append(ncvar)

        return ncvar

    def _write_count_variable(
        self, f, count_variable, ncdim=None, create_ncdim=True
    ):
        """Write a count variable to the netCDF file."""
        g = self.write_vars

        if not self._already_in_file(count_variable):
            ncvar = self._create_netcdf_variable_name(
                count_variable, default="count"
            )

            if create_ncdim:
                ncdim = self._netcdf_name(ncdim)
                self._write_dimension(
                    ncdim,
                    f,
                    None,
                    size=self.implementation.get_data_size(count_variable),
                )

            # --------------------------------------------------------
            # Create the sample dimension
            # --------------------------------------------------------
            _ = self.implementation.nc_get_sample_dimension(
                count_variable, "element"
            )
            sample_ncdim = self._netcdf_name(_)
            self._write_dimension(
                sample_ncdim,
                f,
                None,
                size=int(self.implementation.get_data_sum(count_variable)),
            )

            extra = {"sample_dimension": sample_ncdim}

            # Create a new list variable
            self._write_netcdf_variable(
                ncvar, (ncdim,), count_variable, extra=extra
            )

            g["count_variable_sample_dimension"][ncvar] = sample_ncdim
        else:
            ncvar = g["seen"][id(count_variable)]["ncvar"]
            sample_ncdim = g["count_variable_sample_dimension"][ncvar]

        return sample_ncdim

    def _write_index_variable(
        self,
        f,
        index_variable,
        sample_dimension,
        ncdim=None,
        create_ncdim=True,
        instance_dimension=None,
    ):
        """Write an index variable to the netCDF file.

        :Parameters:

            f: Field construct

            index_variable: Index variable

            sample_dimension: `str`
                The name of the netCDF sample dimension.

            ncdim: `str`, optional

            create_ncdim: bool, optional

            instance_dimension: `str`, optional
                The name of the netCDF instance dimension.

        :Returns:

            `str`
                The name of the netCDF sample dimension.

        """
        g = self.write_vars

        if not self._already_in_file(index_variable):
            ncvar = self._create_netcdf_variable_name(
                index_variable, default="index"
            )

            if create_ncdim:
                ncdim = self._netcdf_name(ncdim)
                self._write_dimension(
                    ncdim,
                    f,
                    None,
                    size=self.implementation.get_data_size(index_variable),
                )

            # Create a new list variable
            extra = {"instance_dimension": instance_dimension}
            self._write_netcdf_variable(
                ncvar, (ncdim,), index_variable, extra=extra
            )

            g["index_variable_sample_dimension"][ncvar] = sample_dimension
        else:
            ncvar = g["seen"][id(index_variable)]["ncvar"]

        return sample_dimension

    def _write_list_variable(self, f, list_variable, compress):
        """Write a list variable to the netCDF file."""
        g = self.write_vars

        create = not self._already_in_file(list_variable)

        if create:
            ncvar = self._create_netcdf_variable_name(
                list_variable, default="list"
            )

            # Create a new dimension
            self._write_dimension(
                ncvar, f, size=self.implementation.get_data_size(list_variable)
            )

            extra = {"compress": compress}

            # Create a new list variable
            self._write_netcdf_variable(
                ncvar, (ncvar,), list_variable, extra=extra
            )

            self.implementation.nc_set_variable(list_variable, ncvar)  # Why?
        else:
            ncvar = g["seen"][id(list_variable)]["ncvar"]

        return ncvar

    def _write_scalar_data(self, value, ncvar):
        """Write a dimension coordinate and bounds to the netCDF file.

        This also writes a new netCDF dimension to the file and, if
        required, a new netCDF bounds dimension.

        .. note:: This function updates ``g['seen']``.

        :Parameters:

            data: Data instance

            ncvar: `str`

        :Returns:

            `str`
                The netCDF name of the scalar data variable

        """
        g = self.write_vars

        seen = g["seen"]

        create = not self._already_in_file(value, ncdims=())

        if create:
            ncvar = self._netcdf_name(ncvar)  # DCH ?

            # Create a new dimension coordinate variable
            self._write_netcdf_variable(ncvar, (), value)
        else:
            ncvar = seen[id(value)]["ncvar"]

        return ncvar

    def _create_geometry_container(self, field):
        """Create a geometry container variable in the netCDF file.

        .. versionadded:: (cfdm) 1.8.0

        :Parameters:

            field: Field construct

        :Returns:

            `dict`
                A representation off the CF-netCDF geometry container
                variable for field construct. If there is no geometry
                container then the dictionary is empty.

        """
        g = self.write_vars

        gc = {}
        for key, coord in self.implementation.get_auxiliary_coordinates(
            field
        ).items():
            geometry_type = self.implementation.get_geometry(coord, None)
            if geometry_type not in self.cf_geometry_types():
                # No geometry bounds for this auxiliary coordinate
                continue

            nodes = self.implementation.get_bounds(coord)
            if nodes is None:
                # No geometry nodes for this auxiliary coordinate
                continue

            # assuming 1-d coord ...
            geometry_dimension = g["key_to_ncdims"][key][0]

            geometry_id = (geometry_dimension, geometry_type)
            gc.setdefault(
                geometry_id,
                {"geometry_type": geometry_type}
                #                 'geometry_dimension': geometry_dimension,
            )

            # Nodes
            nodes_ncvar = g["seen"][id(nodes)]["ncvar"]
            gc[geometry_id].setdefault("node_coordinates", []).append(
                nodes_ncvar
            )

            # Coordinates
            try:
                coord_ncvar = g["seen"][id(coord)]["ncvar"]
            except KeyError:
                # There is no netCDF auxiliary coordinate variable
                pass
            else:
                gc[geometry_id].setdefault("coordinates", []).append(
                    coord_ncvar
                )

            # Grid mapping
            grid_mappings = [
                g["seen"][id(cr)]["ncvar"]
                # TODO replace field.coordinate_references with
                # self.implemenetation call
                for cr in field.coordinate_references().values()
                if (
                    cr.coordinate_conversion.get_parameter(
                        "grid_mapping_name", None
                    )
                    is not None
                    and key in cr.coordinates()
                )
            ]
            gc[geometry_id].setdefault("grid_mapping", []).extend(
                grid_mappings
            )

            # Node count
            try:
                ncvar = g["geometry_encoding"][nodes_ncvar]["node_count"]
            except KeyError:
                # There is no node count variable
                pass
            else:
                gc[geometry_id].setdefault("node_count", []).append(ncvar)

            # Part node count
            try:
                ncvar = g["geometry_encoding"][nodes_ncvar]["part_node_count"]
            except KeyError:
                # There is no part node count variable
                pass
            else:
                gc[geometry_id].setdefault("part_node_count", []).append(ncvar)

            # Interior ring
            try:
                ncvar = g["geometry_encoding"][nodes_ncvar]["interior_ring"]
            except KeyError:
                # There is no interior ring variable
                pass
            else:
                gc[geometry_id].setdefault("interior_ring", []).append(ncvar)

        if not gc:
            # This field has no geometries
            return {}

        for x in gc.values():
            # Node coordinates
            if "node_coordinates" in x:
                x["node_coordinates"] = " ".join(sorted(x["node_coordinates"]))

            # Coordinates
            if "coordinates" in x:
                x["coordinates"] = " ".join(sorted(x["coordinates"]))

            # Grid mapping
            grid_mappings = set(x.get("grid_mapping", ()))
            if len(grid_mappings) == 1:
                x["grid_mapping"] = grid_mappings.pop()
            elif len(grid_mappings) > 1:
                raise ValueError(
                    f"Can't write {field!r}: Geometry container has multiple "
                    f"grid mapping variables: {x['grid_mapping']!r}"
                )

            # Node count
            nc = set(x.get("node_count", ()))
            if len(nc) == 1:
                x["node_count"] = nc.pop()
            elif len(nc) > 1:
                raise ValueError(
                    f"Can't write {field!r}: Geometry container has multiple "
                    f"node count variables: {x['node_count']!r}"
                )

            # Part node count
            pnc = set(x.get("part_node_count", ()))
            if len(pnc) == 1:
                x["part_node_count"] = pnc.pop()
            elif len(pnc) > 1:
                raise ValueError(
                    f"Can't write {field!r}: Geometry container has multiple "
                    f"part node count variables: {x['part_node_count']!r}"
                )

            # Interior ring
            ir = set(x.get("interior_ring", ()))
            if len(ir) == 1:
                x["interior_ring"] = ir.pop()
            elif len(ir) > 1:
                raise ValueError(
                    f"Can't write {field!r}: Geometry container has multiple "
                    f"interior ring variables: {x['interior_ring']!r}"
                )

        if len(gc) > 1:
            raise ValueError(
                f"Can't write {field!r}: Multiple geometry containers: "
                f"{list(gc.values())!r}"
            )

        _, geometry_container = gc.popitem()

        g["geometry_dimensions"].add(geometry_dimension)

        return geometry_container

    def _already_in_file(self, variable, ncdims=None, ignore_type=False):
        """True if a variable already exists in g['seen'].

        Specifically, returns True if a variable is logically equal any
        variable in the g['seen'] dictionary.

        If this is the case then the variable has already been written to
        the output netCDF file and so we don't need to do it again.

        If 'ncdims' is set then a extra condition for equality is applied,
        namely that of 'ncdims' being equal to the netCDF dimensions
        (names and order) to that of a variable in the g['seen']
        dictionary.

        When `True` is returned, the input variable is added to the
        g['seen'] dictionary.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            variable:

            ncdims: `tuple`, optional

            ignore_type: `bool`, optional

        :Returns:

            `bool`
                `True` if the variable has already been written to the
                file, `False` otherwise.

        """
        g = self.write_vars

        seen = g["seen"]

        for value in seen.values():
            if ncdims is not None and ncdims != value["ncdims"]:
                # The netCDF dimensions (names and order) of the input
                # variable are different to those of this variable in
                # the 'seen' dictionary
                continue

            # Still here?
            if self.implementation.equal_components(
                variable, value["variable"], ignore_type=ignore_type
            ):
                seen[id(variable)] = {
                    "variable": variable,
                    "ncvar": value["ncvar"],
                    "ncdims": value["ncdims"],
                }
                return True

        return False

    def _write_geometry_container(self, field, geometry_container):
        """Write a netCDF geometry container variable.

        .. versionadded:: (cfdm) 1.8.0

        :Returns:

            `str`
                The netCDF variable name for the geometry container.

        """
        g = self.write_vars

        for ncvar, gc in g["geometry_containers"].items():
            if geometry_container == gc:
                # Use this existing geometry container
                return ncvar

        # Still here? Then write the geometry container to the file
        ncvar = self.implementation.nc_get_geometry_variable(
            field, default="geometry_container"
        )
        ncvar = self._netcdf_name(ncvar)

        logger.info(
            f"    Writing geometry container variable: {ncvar}"
        )  # pragma: no cover
        logger.info(f"        {geometry_container}")  # pragma: no cover

        kwargs = {
            "varname": ncvar,
            "datatype": "S1",
            "dimensions": (),
            "endian": g["endian"],
        }
        kwargs.update(g["netcdf_compression"])

        if not g["dry_run"]:
            self._createVariable(**kwargs)

            g["nc"][ncvar].setncatts(geometry_container)

        # Update the 'geometry_containers' dictionary
        g["geometry_containers"][ncvar] = geometry_container

        return ncvar

    def _write_bounds(
        self, f, coord, coord_key, coord_ncdimensions, coord_ncvar=None
    ):
        """Creates a bounds netCDF variable and returns its name.

        Specifically, creates a bounds netCDF variable, creating a new
        bounds netCDF dimension if required. Returns the bounds
        variable's netCDF variable name.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            f: Field construct

            coord:

            coord_key: `str`
                The coordinate construct key.

            coord_ncdimensions: `tuple` of `str`
                The ordered netCDF dimension names of the coordinate's
                dimensions (which do not include the bounds dimension).

            coord_ncvar: `str`
                The netCDF variable name of the parent variable

        :Returns:

            `dict`

        **Examples:**

        >>> _write_bounds(c, ('dim2',))
        {'bounds': 'lat_bounds'}

        >>> _write_bounds(c, ('dim2',))
        {'nodes': 'x'}

        >>> _write_bounds(c, ('dim2',))
        {'climatology': 'time_bnds'}

        """
        g = self.write_vars

        bounds = self.implementation.get_bounds(coord, None)
        if bounds is None:
            return {}

        data = self.implementation.get_data(bounds, None)
        if data is None:
            return {}

        if g["output_version"] >= g[
            "CF-1.8"
        ] and self.implementation.is_geometry(coord):

            # --------------------------------------------------------
            # CF>=1.8 and we have geometry bounds, which are dealt
            # with separately
            # --------------------------------------------------------
            extra = self._write_node_coordinates(
                coord, coord_ncvar, coord_ncdimensions
            )
            return extra

        # Still here? Then this coordinate has non-geometry bounds
        # with data
        extra = {}

        size = data.shape[-1]

        #        bounds_ncdim = self._netcdf_name('bounds{0}'.format(size),
        #                                  dimsize=size, role='bounds')

        bounds_ncdim = self.implementation.nc_get_dimension(
            bounds, f"bounds{size}"
        )
        if not g["group"]:
            # A flat file has been requested, so strip off any group
            # structure from the name.
            bounds_ncdim = self._remove_group_structure(bounds_ncdim)

        bounds_ncdim = self._netcdf_name(
            bounds_ncdim, dimsize=size, role="bounds"
        )

        # Check if this bounds variable has not been previously
        # created.
        ncdimensions = coord_ncdimensions + (bounds_ncdim,)
        if self._already_in_file(bounds, ncdimensions):
            # This bounds variable has been previously created, so no
            # need to do so again.
            ncvar = g["seen"][id(bounds)]["ncvar"]
        else:
            # This bounds variable has not been previously created, so
            # create it now.
            ncdim_to_size = g["ncdim_to_size"]
            if bounds_ncdim not in ncdim_to_size:
                logger.info(
                    f"    Writing size {size} netCDF dimension for "
                    f"bounds: {bounds_ncdim}"
                )  # pragma: no cover

                ncdim_to_size[bounds_ncdim] = size

                # Define (and create if necessary) the group in which
                # to place this netCDF dimension.
                parent_group = self._parent_group(bounds_ncdim)

                if g["group"] and "/" in bounds_ncdim:
                    # This dimension needs to go into a sub-group so
                    # replace its name with its basename (CF>=1.8)
                    base_bounds_ncdim = self._remove_group_structure(
                        bounds_ncdim
                    )
                else:
                    base_bounds_ncdim = bounds_ncdim

                if not g["dry_run"]:
                    try:
                        parent_group.createDimension(base_bounds_ncdim, size)
                    except RuntimeError:
                        raise

                # Set the netCDF bounds variable name
                default = coord_ncvar + "_bounds"
            else:
                default = "bounds"

            ncvar = self.implementation.nc_get_variable(
                bounds, default=default
            )

            if not self.write_vars["group"]:
                # A flat file has been requested, so strip off any
                # group structure from the name (for now).
                ncvar = self._remove_group_structure(ncvar)

            ncvar = self._netcdf_name(ncvar)

            # If no groups have been set on the bounds, then put the
            # bounds variable in the same group as its parent
            # coordinates
            bounds_groups = self._groups(ncvar)
            coord_groups = self._groups(coord_ncvar)
            if not bounds_groups and coord_groups:
                ncvar = coord_groups + ncvar

            #            for ncdim in ncdimensions:
            #                _, ncdim_groups = self._remove_group_structure(
            #                    ncdim,
            #                    return_groups=True)
            #                if not bounds_groups.startswith(ncdim_groups):
            #                    raise ValueError(
            #                        "Can't find create a netCDF variable from {!r} "
            #                        "with a dimension that is not in the same group or "
            #                        "a sub-group as the variable: {}".format(bounds, ncdim)
            #                    )

            # Note that, in a field, bounds always have equal units to
            # their parent coordinate

            # Select properties to omit
            omit = []
            for prop in g["omit_bounds_properties"]:
                if self.implementation.has_property(coord, prop):
                    omit.append(prop)

            # Create the bounds netCDF variable
            self._write_netcdf_variable(ncvar, ncdimensions, bounds, omit=omit)

        extra["bounds"] = ncvar
        axes = self.implementation.get_construct_data_axes(f, coord_key)
        for clim_axis in self.implementation.climatological_time_axes(f):
            if (clim_axis,) == axes:
                logger.info(
                    "    Setting climatological bounds"
                )  # pragma: no cover

                extra["climatology"] = extra.pop("bounds")
                break

        g["bounds"][coord_ncvar] = ncvar

        return extra

    def _write_node_coordinates(self, coord, coord_ncvar, coord_ncdimensions):
        """Create a netCDF node coordinates variable.

        This will create:

        * A netCDF node dimension, if required.
        * A netCDF node count variable, if required.
        * A netCDF part node count variable, if required.
        * A netCDF interior ring variable, if required.

        .. versionadded:: (cfdm) 1.8.0

        :Parameters:

            coord:

            coord_ncvar: `str`

            coord_ncdimensions: `list`

        :Returns:

            `dict`

        """
        g = self.write_vars

        bounds = self.implementation.get_bounds(coord, None)
        if bounds is None:
            # This coordinate construct has no bounds
            return {}

        data = self.implementation.get_data(bounds, None)
        if data is None:
            # The bounds have no data
            return {}

        # Still here? Then this coordinate has a nodes attribute
        # which contains data.

        # Create the node coordinates flattened data
        array = self.implementation.get_array(data)
        array = self._numpy_compressed(array)
        data = self.implementation.initialise_Data(array=array, copy=False)

        # ------------------------------------------------------------
        # Create a bounds variable to hold the node coordinates
        # variable. This is what will be written to disk.
        # ------------------------------------------------------------
        nodes = self.implementation.initialise_Bounds()
        self.implementation.set_data(nodes, data, copy=False)

        properties = self.implementation.get_properties(bounds)
        self.implementation.set_properties(nodes, properties)

        # Set inherited properties on node variables
        inherited_properties = self.implementation.get_inherited_properties(
            bounds
        )
        self.implementation.set_inherited_properties(
            nodes, inherited_properties
        )

        # Find the base of the netCDF part dimension name
        size = self.implementation.get_data_size(nodes)
        ncdim = self._get_node_ncdimension(nodes, default="node")
        ncdim = self._netcdf_name(ncdim, dimsize=size, role="node")

        create = True
        if self._already_in_file(nodes, (ncdim,)):
            # This node coordinates variable has been previously
            # created, so no need to do so again.
            ncvar = g["seen"][id(nodes)]["ncvar"]

            geometry_dimension = g["geometry_encoding"][ncvar][
                "geometry_dimension"
            ]

            if geometry_dimension == coord_ncdimensions[0]:
                # The node coordinate variable already exists, and the
                # corresponding encoding variables span the correct
                # dimension.
                create = False

                # We need to log the original Bounds variable as being
                # in the file, too. This is so that the geometry
                # container variable can be created later on.
                g["seen"][id(bounds)] = {
                    "ncvar": ncvar,
                    "variable": bounds,
                    "ncdims": None,
                }
            else:
                # The node coordinate variable already exists, but the
                # corresponding encoding variables span the wrong
                # dimension => we have to create a new node
                # coordinates variable.
                create = True

        if create:
            # This node coordinates variable has not been previously
            # created, so create it now.
            ncdim_to_size = g["ncdim_to_size"]
            if ncdim not in ncdim_to_size:
                size = self.implementation.get_data_size(nodes)
                logger.info(
                    f"    Writing size {size} netCDF node dimension: "
                    f"{ncdim}"
                )  # pragma: no cover

                ncdim_to_size[ncdim] = size

                # Define (and create if necessary) the group in which
                # to place this netCDF dimension.
                parent_group = self._parent_group(ncdim)

                if g["group"] and "/" in ncdim:
                    # This dimension needs to go into a sub-group so
                    # replace its name with its basename (CF>=1.8)
                    ncdim = self._remove_group_structure(ncdim)

                if not g["dry_run"]:
                    parent_group.createDimension(ncdim, size)

            # Set an appropriate default netCDF node coordinates
            # variable name
            axis = self.implementation.get_property(bounds, "axis")
            if axis is not None:
                default = str(axis).lower()
            else:
                default = "node_coordinate"

            ncvar = self.implementation.nc_get_variable(
                bounds, default=default
            )
            if not self.write_vars["group"]:
                # A flat file has been requested, so strip off any
                # group structure from the name.
                ncvar = self._remove_group_structure(ncvar)

            ncvar = self._netcdf_name(ncvar)

            # Create the netCDF node coordinates variable
            self._write_netcdf_variable(ncvar, (ncdim,), nodes)

            encodings = {}

            nc_encodings = self._write_node_count(
                coord, bounds, coord_ncdimensions, encodings
            )
            encodings.update(nc_encodings)

            pnc_encodings = self._write_part_node_count(
                coord, bounds, encodings
            )
            encodings.update(pnc_encodings)

            ir_encodings = self._write_interior_ring(coord, bounds, encodings)
            encodings.update(ir_encodings)

            g["geometry_encoding"][ncvar] = encodings

            # We need to log the original Bounds variable as being in
            # the file, too. This is so that the geometry container
            # variable can be created later on.
            g["seen"][id(bounds)] = {
                "ncvar": ncvar,
                "variable": bounds,
                "ncdims": None,
            }

        if coord_ncvar is not None:
            g["bounds"][coord_ncvar] = ncvar

        return {"nodes": ncvar}

    def _write_node_count(self, coord, bounds, coord_ncdimensions, encodings):
        """Create a netCDF node count variable.

        .. versionadded:: (cfdm) 1.8.0

        :Parameters:

            coord:

            bounds:

            coord_ncdimensions: sequence of `str`
                The netCDF instance dimension

            encodings: `dict`
                Ignored.

        :Returns:

            `dict`

        """
        g = self.write_vars

        # Create the node count flattened data
        array = self.implementation.get_array(
            self.implementation.get_data(bounds)
        )
        if self.implementation.get_data_ndim(bounds) == 2:  # DCH
            array = numpy.ma.count(array, axis=1)  # DCH
        else:  # DCH
            array = numpy.ma.count(array, axis=2).sum(axis=1)  # DCH

        data = self.implementation.initialise_Data(array=array, copy=False)

        # ------------------------------------------------------------
        # Create a count variable to hold the node count data and
        # properties. This is what will be written to disk.
        # ------------------------------------------------------------
        count = self.implementation.initialise_Count()
        self.implementation.set_data(count, data, copy=False)

        # Find the base of the netCDF node count variable name
        nc = self.implementation.get_node_count(coord)

        if nc is not None:
            ncvar = self.implementation.nc_get_variable(
                nc, default="node_count"
            )

            if not self.write_vars["group"]:
                # A flat file has been requested, so strip off any
                # group structure from the name.
                ncvar = self._remove_group_structure(ncvar)

            # Copy node count variable properties to the new count
            # variable
            properties = self.implementation.get_properties(nc)
            self.implementation.set_properties(count, properties)
        else:
            ncvar = "node_count"

        geometry_dimension = coord_ncdimensions[0]

        if self._already_in_file(count, (geometry_dimension,)):
            # This node count variable has been previously created, so
            # no need to do so again.
            ncvar = g["seen"][id(count)]["ncvar"]
        else:
            # This node count variable has not been previously
            # created, so create it now.
            if geometry_dimension not in g["ncdim_to_size"]:
                raise ValueError(
                    "The netCDF geometry dimension should already exist ..."
                )

            ncvar = self._netcdf_name(ncvar)

            # Create the netCDF node count variable
            self._write_netcdf_variable(ncvar, (geometry_dimension,), count)

        # Return encodings
        return {"geometry_dimension": geometry_dimension, "node_count": ncvar}

    def _get_part_ncdimension(self, coord, default=None):
        """Gets dimension name for part node counts or interior rings.

        Specifically, gets the base of the netCDF dimension for part
        node count and interior ring variables.

        .. versionadded:: (cfdm) 1.8.0

        :Returns:

            The netCDF dimension name, or else the value of the *default*
            parameter.

        """
        ncdim = None

        pnc = self.implementation.get_part_node_count(coord)
        if pnc is not None:
            # Try to get the netCDF dimension from a part node count
            # variable
            ncdim = self.implementation.nc_get_dimension(pnc, default=None)

        if ncdim is None:
            # Try to get the netCDF dimension from an interior ring
            # variable
            interior_ring = self.implementation.get_interior_ring(coord)
            if interior_ring is not None:
                ncdim = self.implementation.nc_get_dimension(
                    interior_ring, default=None
                )

        if ncdim is not None:
            # Found a netCDF dimension
            if not self.write_vars["group"]:
                # A flat file has been requested, so strip off any
                # group structure from the name.
                ncdim = self._remove_group_structure(ncdim)

            return ncdim

        # Return the default
        return default

    def _parent_group(self, name):
        """Returns the parent group due for a dimension or variable.

        That is, the parent group in which a dimension or variable is
        to be created.

        .. versionadded:: (cfdm) 1.8.6.0

        :Parameters:

            name: `str`
                The name of the netCDF dimension or variable.

        :Returns:

            `netCDF.Dataset` or `netCDF._netCDF4.Group`

        """
        g = self.write_vars

        parent_group = g["netcdf"]

        if not g["group"] or "/" not in name:
            return parent_group

        if not name.startswith("/"):
            raise ValueError(
                f"Invalid netCDF name {name!r}: missing a leading '/'"
            )

        for group_name in name.split("/")[1:-1]:
            parent_group = self._write_group(parent_group, group_name)

        return parent_group

    def _remove_group_structure(self, name, return_groups=False):
        """Strip off any group structure from the name.

        .. versionaddedd:: (cfdm) 1.8.6.0

        :Parameters:

            name: `str`

            return_groups: `bool`, optional

        :Returns:

            `str`

        **Examples:**

        w._remove_group_structure('lat')
        'lat'
        w._remove_group_structure('/forecast/lat')
        'lat'
        w._remove_group_structure('/forecast/model/lat')
        'lat'
        w._remove_group_structure('lat', return_groups=True)
        'lat', ''
        w._remove_group_structure('/forecast/lat', return_groups=True)
        'lat', '/forecast/'
        w._remove_group_structure('/forecast/model/lat', return_groups=True)
        'lat', '/forecast/model/'

        """
        structure = name.split("/")
        basename = structure[-1]

        if return_groups:
            groups = "/".join(structure[:-1])
            if groups:
                groups += "/"

            return basename, groups

        return basename

    def _groups(self, name):
        """Strip off any group structure from the name.

        .. versionaddedd:: 1.8.7.0

        :Parameters:

            name: `str`

        :Returns:

            `str`

        **Examples:**

        w._groups('lat')
        ''
        w._groups('/forecast/lat')
        '/forecast/'
        w._groups('/forecast/model/lat')
        '/forecast/model/'

        """
        _, groups = self._remove_group_structure(name, return_groups=True)

        return groups

    def _get_node_ncdimension(self, bounds, default=None):
        """Get the netCDF dimension from a node count variable.

        .. versionadded:: (cfdm) 1.8.0

        :Parameters:

            bounds: Bounds component

            default: optional

        :Returns:

            The netCDF dimension name, or else the value of the *default*
            parameter.

        """
        ncdim = self.implementation.nc_get_dimension(bounds, default=None)
        if ncdim is not None:
            # Found a netCDF dimension
            if not self.write_vars["group"]:
                # A flat file has been requested, so strip off any
                # group structure from the name.
                ncdim = self._remove_group_structure(ncdim)

            return ncdim

        # Return the default
        return default

    def _write_part_node_count(self, coord, bounds, encodings):
        """Creates a bounds netCDF variable and returns its name.

        Create a bounds netCDF variable, creating a new bounds netCDF
        dimension if required. Return the bounds variable's netCDF
        variable name.

        .. versionadded:: (cfdm) 1.8.0

        :Parameters:

            coord:

            coord_ncvar: `str`
                The netCDF variable name of the parent variable

        :Returns:

            `dict`

        **Examples:**

        >>> _write_part_node_count(c, b)
        {'part_node_count': 'pnc'}

        >>> _write_part_node_count(c, b)
        {}

        """
        #        if self.implementation.get_data_ndim(bounds) < 3: # DCH
        #            # No need for a part node count variable required
        #            return {}
        if self.implementation.get_data_shape(bounds)[1] == 1:
            # No part node count variable required
            return {}

        g = self.write_vars

        # Create the part node count flattened data
        array = self.implementation.get_array(
            self.implementation.get_data(bounds)
        )
        array = numpy.trim_zeros(numpy.ma.count(array, axis=2).flatten())
        data = self.implementation.initialise_Data(array=array, copy=False)

        # ------------------------------------------------------------
        # Create a count variable to hold the part node count data and
        # properties. This is what will be written to disk.
        # ------------------------------------------------------------
        count = self.implementation.initialise_Count()
        self.implementation.set_data(count, data, copy=False)

        # Find the base of the netCDF part_node_count variable name
        pnc = self.implementation.get_part_node_count(coord)
        if pnc is not None:
            ncvar = self.implementation.nc_get_variable(
                pnc, default="part_node_count"
            )
            if not self.write_vars["group"]:
                # A flat file has been requested, so strip off any
                # group structure from the name.
                ncvar = self._remove_group_structure(ncvar)

            # Copy part node count variable properties to the new
            # count variable
            properties = self.implementation.get_properties(pnc)
            self.implementation.set_properties(count, properties)
        else:
            ncvar = "part_node_count"

        # Find the base of the netCDF part dimension name
        size = self.implementation.get_data_size(count)
        if g["part_ncdim"] is not None:
            ncdim = g["part_ncdim"]
        elif "part_ncdim" in encodings:
            ncdim = encodings["part_ncdim"]
        else:
            ncdim = self._get_part_ncdimension(coord, default="part")
            ncdim = self._netcdf_name(ncdim, dimsize=size, role="part")

        if self._already_in_file(count, (ncdim,)):
            # This part node count variable has been previously
            # created, so no need to do so again.
            ncvar = g["seen"][id(count)]["ncvar"]
        else:
            ncdim_to_size = g["ncdim_to_size"]
            if ncdim not in ncdim_to_size:
                logger.info(
                    f"    Writing size {size} netCDF part " f"dimension{ncdim}"
                )  # pragma: no cover

                ncdim_to_size[ncdim] = size

                # Define (and create if necessary) the group in which
                # to place this netCDF dimension.
                parent_group = self._parent_group(ncdim)

                if g["group"] and "/" in ncdim:
                    # This dimension needs to go into a sub-group so
                    # replace its name with its basename (CF>=1.8)
                    ncdim = self._remove_group_structure(ncdim)

                if not g["dry_run"]:
                    parent_group.createDimension(ncdim, size)

            ncvar = self._netcdf_name(ncvar)

            # Create the netCDF part_node_count variable
            self._write_netcdf_variable(ncvar, (ncdim,), count)

        g["part_ncdim"] = ncdim

        # Return encodings
        return {"part_node_count": ncvar, "part_ncdim": ncdim}

    def _write_interior_ring(self, coord, bounds, encodings):
        """Write an interior ring variable to the netCDF file.

        .. versionadded:: (cfdm) 1.8.0

        :Parameters:

            coord:

            coord_ncvar: `str`
                The netCDF variable name of the parent variable

            encodings:

        :Returns:

            `dict`

        """
        interior_ring = self.implementation.get_interior_ring(coord)
        if interior_ring is None:
            return {}

        g = self.write_vars

        #        array = self.implementation.get_data(interior_ring).array.compressed()
        data = self.implementation.get_data(interior_ring)
        array = self.implementation.get_array(data)
        array = self._numpy_compressed(array)

        # Replace the data with its compressed, flattened version
        interior_ring = self.implementation.copy_construct(interior_ring)
        data = self.implementation.initialise_Data(array=array, copy=False)
        self.implementation.set_data(interior_ring, data, copy=False)

        ncvar = self.implementation.nc_get_variable(
            interior_ring, default="interior_ring"
        )

        if not self.write_vars["group"]:
            # A flat file has been requested, so strip off any group
            # structure from the name.
            ncvar = self._remove_group_structure(ncvar)

        size = self.implementation.get_data_size(interior_ring)
        if g["part_ncdim"] is not None:
            ncdim = g["part_ncdim"]
        elif "part_ncdim" in encodings:
            ncdim = encodings["part_ncdim"]
        else:
            ncdim = self._get_part_ncdimension(coord, default="part")
            ncdim = self._netcdf_name(ncdim, dimsize=size, role="part")

        if self._already_in_file(interior_ring, (ncdim,)):
            # This interior ring variable has been previously created,
            # so no need to do so again.
            ncvar = g["seen"][id(interior_ring)]["ncvar"]
        else:
            ncdim_to_size = g["ncdim_to_size"]
            if ncdim not in ncdim_to_size:
                logger.info(
                    f"    Writing size {size} netCDF part " f"dimension{ncdim}"
                )  # pragma: no cover
                ncdim_to_size[ncdim] = size

                # Define (and create if necessary) the group in which
                # to place this netCDF dimension.
                parent_group = self._parent_group(ncdim)

                if g["group"] and "/" in ncdim:
                    # This dimension needs to go into a sub-group so
                    # replace its name with its basename (CF>=1.8)
                    ncdim = self._remove_group_structure(ncdim)

                if not g["dry_run"]:
                    parent_group.createDimension(ncdim, size)

            ncvar = self._netcdf_name(ncvar)

            # Create the netCDF interior ring variable
            self._write_netcdf_variable(ncvar, (ncdim,), interior_ring)

        g["part_ncdim"] = ncdim

        # Return encodings
        return {"interior_ring": ncvar, "part_ncdim": ncdim}

    def _write_scalar_coordinate(
        self, f, key, coord_1d, axis, coordinates, extra=None
    ):
        """Write a scalar coordinate and its bounds to the netCDF file.

        It is assumed that the input coordinate is has size 1, but this is not
        checked.

        If an equal scalar coordinate has already been written to the file
        then the input coordinate is not written.

        :Parameters:

            f: Field construct

            key: `str`
                The coordinate construct key

            coordinate
            axis : str
                The field's axis identifier for the scalar coordinate.

            coordinates: `list`

        :Returns:

            coordinates: `list`
                The updated list of netCDF auxiliary coordinate names.

        """
        # To avoid mutable default argument (an anti-pattern) of extra={}
        if extra is None:
            extra = {}

        g = self.write_vars

        scalar_coord = self.implementation.squeeze(coord_1d, axes=0)

        if not self._already_in_file(scalar_coord, ()):
            ncvar = self._create_netcdf_variable_name(
                scalar_coord, default="scalar"
            )
            # If this scalar coordinate has bounds then create the
            # bounds netCDF variable and add the 'bounds' or
            # 'climatology' (as appropriate) attribute to the
            # dictionary of extra attributes
            bounds_extra = self._write_bounds(f, scalar_coord, key, (), ncvar)

            # Create a new scalar coordinate variable
            self._write_netcdf_variable(
                ncvar, (), scalar_coord, extra=bounds_extra
            )

        else:
            # This scalar coordinate has already been written to the
            # file
            ncvar = g["seen"][id(scalar_coord)]["ncvar"]

        g["axis_to_ncscalar"][axis] = ncvar

        g["key_to_ncvar"][key] = ncvar

        coordinates.append(ncvar)

        return coordinates

    def _write_auxiliary_coordinate(self, f, key, coord, coordinates):
        """Write auxiliary coordinates and bounds to the netCDF file.

        If an equal auxiliary coordinate has already been written to the file
        then the input coordinate is not written.

        :Parameters:

            f: Field construct

            key: `str`

            coord: Coordinate construct

            coordinates: `list`

        :Returns:

            `list`
                The list of netCDF auxiliary coordinate names updated in
                place.

        """
        g = self.write_vars

        ncvar = None

        # The netCDF dimensions for the auxiliary coordinate variable
        ncdimensions = self._netcdf_dimensions(f, key, coord)

        if self._already_in_file(coord, ncdimensions):
            ncvar = g["seen"][id(coord)]["ncvar"]

            # Register that bounds as being the file, too. This is so
            # that a geometry container variable can be created later
            # on, if required.
            bounds_ncvar = g["bounds"].get(ncvar)
            if bounds_ncvar is not None:
                bounds = self.implementation.get_bounds(coord, None)
                if bounds is not None:
                    g["seen"][id(bounds)] = {
                        "ncvar": bounds_ncvar,
                        "variable": bounds,
                        "ncdims": None,
                    }
        else:
            if (
                not self.implementation.get_properties(coord)
                and self.implementation.get_data(coord, default=None) is None
            ):
                # No coordinates, but possibly bounds
                self._write_bounds(
                    f, coord, key, ncdimensions, coord_ncvar=None
                )
            else:
                ncvar = self._create_netcdf_variable_name(
                    coord, default="auxiliary"
                )

                # TODO: move setting of bounds ncvar to here - why?

                # If this auxiliary coordinate has bounds then create
                # the bounds netCDF variable and add the 'bounds',
                # 'climatology' or 'nodes' attribute (as appropriate)
                # to the dictionary of extra attributes.
                extra = self._write_bounds(f, coord, key, ncdimensions, ncvar)

                # Create a new auxiliary coordinate variable, if it has data
                if self.implementation.get_data(coord, None) is not None:
                    self._write_netcdf_variable(
                        ncvar, ncdimensions, coord, extra=extra
                    )

        #                g['key_to_ncvar'][key] = ncvar
        #                g['key_to_ncdims'][key] = ncdimensions

        g["key_to_ncvar"][key] = ncvar
        g["key_to_ncdims"][key] = ncdimensions

        if ncvar is not None:
            coordinates.append(ncvar)

        return coordinates

    def _write_domain_ancillary(self, f, key, anc):
        """Write a domain ancillary and its bounds to the netCDF file.

        If an equal domain ancillary has already been written to the file
        athen it is not re-written.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            f: Field construct

            key: `str`
                The internal identifier of the domain ancillary object.

            anc: Domain ancillary construct

        :Returns:

            `str`
                The netCDF variable name of the domain ancillary variable.

        """
        g = self.write_vars

        if g["post_dry_run"]:
            logger.warning(
                "At present domain ancillary constructs of appended fields "
                "may not be handled correctly by netCDF write append mode "
                "and can appear as extra fields. Set them on fields using "
                "`set_domain_ancillary` and similar methods if required."
            )

        ncdimensions = self._netcdf_dimensions(f, key, anc)

        create = not self._already_in_file(anc, ncdimensions, ignore_type=True)

        if not create:
            ncvar = g["seen"][id(anc)]["ncvar"]
        else:
            # See if we can set the default netCDF variable name to
            # its formula_terms term
            default = None
            for ref in self.implementation.get_coordinate_references(
                f
            ).values():
                for (
                    term,
                    da_key,
                ) in (  # DCH ALERT
                    ref.coordinate_conversion.domain_ancillaries().items()
                ):
                    if da_key == key:
                        default = term
                        break

                if default is not None:
                    break

            if default is None:
                default = "domain_ancillary"

            ncvar = self._create_netcdf_variable_name(anc, default=default)

            # If this domain ancillary has bounds then create the bounds
            # netCDF variable
            self._write_bounds(f, anc, key, ncdimensions, ncvar)

            # Create a new domain ancillary variable
            self._write_netcdf_variable(ncvar, ncdimensions, anc)

        g["key_to_ncvar"][key] = ncvar
        g["key_to_ncdims"][key] = ncdimensions

        return ncvar

    def _write_field_ancillary(self, f, key, anc):
        """Write a field ancillary to the netCDF file.

        If an equal field ancillary has already been written to the file
        then it is not re-written.

        :Parameters:

            f : Field construct

            key : str

            anc : Field ancillary construct

        :Returns:

            `str`
                The netCDF variable name of the field ancillary object.

        **Examples:**

        >>> ncvar = _write_field_ancillary(f, 'fieldancillary2', anc)

        """
        g = self.write_vars

        ncdimensions = self._netcdf_dimensions(f, key, anc)

        create = not self._already_in_file(anc, ncdimensions)

        if not create:
            ncvar = g["seen"][id(anc)]["ncvar"]
        else:
            ncvar = self._create_netcdf_variable_name(
                anc, default="ancillary_data"
            )

            # Create a new field ancillary variable
            self._write_netcdf_variable(ncvar, ncdimensions, anc)

        g["key_to_ncvar"][key] = ncvar
        g["key_to_ncdims"][key] = ncdimensions

        return ncvar

    def _write_cell_measure(self, field, key, cell_measure):
        """Write a cell measure construct to the netCDF file.

        If an identical construct has already in the file then the cell
        measure will not be written.

        :Parameters:

            field: Field construct
                The field containing the cell measure.

            key: `str`
                The identifier of the cell measure (e.g. 'cellmeasure0').

            cell_measure: Cell measure construct

        :Returns:

            `str`
                The 'measure: ncvar'.

        """
        g = self.write_vars

        measure = self.implementation.get_measure(cell_measure)
        if measure is None:
            raise ValueError(
                "Can't create a netCDF cell measure variable "
                "without a 'measure' property"
            )

        ncdimensions = self._netcdf_dimensions(field, key, cell_measure)

        if self._already_in_file(cell_measure, ncdimensions):
            # Use existing cell measure variable
            ncvar = g["seen"][id(cell_measure)]["ncvar"]
        elif self.implementation.nc_get_external(cell_measure):
            # The cell measure is external
            ncvar = self._create_netcdf_variable_name(
                cell_measure, default="cell_measure"
            )

            # Add ncvar to the global external_variables attribute
            self._set_external_variables(ncvar)

            # Create a new field to write out to the external file
            if g["external_file"] is not None:
                self._create_external(
                    field=field,
                    construct_id=key,
                    ncvar=ncvar,
                    ncdimensions=ncdimensions,
                )
        else:
            ncvar = self._create_netcdf_variable_name(
                cell_measure, default="cell_measure"
            )

            # Create a new cell measure variable
            self._write_netcdf_variable(ncvar, ncdimensions, cell_measure)

        g["key_to_ncvar"][key] = ncvar
        g["key_to_ncdims"][key] = ncdimensions

        # Update the field's cell_measures list
        return f"{measure}: {ncvar}"

    def _set_external_variables(self, ncvar):
        """Add ncvar to the global external_variables attribute."""
        g = self.write_vars

        external_variables = g["external_variables"]

        if external_variables:
            external_variables = f"{external_variables} {ncvar}"
        else:
            external_variables = ncvar
            g["global_attributes"].add("external_variables")

        if not g["dry_run"] and not g["post_dry_run"]:
            g["netcdf"].setncattr("external_variables", external_variables)

        g["external_variables"] = external_variables

    def _create_external(
        self, field=None, construct_id=None, ncvar=None, ncdimensions=None
    ):
        """Creates a new field to flag to write to an external file.

        .. versionadded:: (cfdm) 1.7.0

        """
        g = self.write_vars

        if ncdimensions is None:
            return

        # Still here?
        external = self.implementation.convert(
            field=field, construct_id=construct_id
        )

        # Set the correct netCDF variable and dimension names
        self.implementation.nc_set_variable(external, ncvar)

        external_domain_axes = self.implementation.get_domain_axes(external)
        for ncdim, axis in zip(
            ncdimensions, self.implementation.get_field_data_axes(external)
        ):
            external_domain_axis = external_domain_axes[axis]
            self.implementation.nc_set_dimension(external_domain_axis, ncdim)

        g["external_fields"].append(external)

        return external

    def _createVariable(self, **kwargs):
        """Create a variable in the netCDF file.

        .. versionadded:: (cfdm) 1.7.0

        """
        g = self.write_vars

        ncvar = kwargs["varname"]

        g["nc"][ncvar] = g["netcdf"].createVariable(**kwargs)

    def _write_grid_mapping(self, f, ref, multiple_grid_mappings):
        """Write a grid mapping georeference to the netCDF file.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            f: Field construct

            ref: Coordinate reference construct
                The grid mapping coordinate reference to write to the file.

            multiple_grid_mappings: `bool`

        :Returns:

            `str`

        """
        g = self.write_vars

        if self._already_in_file(ref):
            # Use existing grid_mapping variable
            ncvar = g["seen"][id(ref)]["ncvar"]

        else:
            # Create a new grid mapping variable
            cc_parameters = (
                self.implementation.get_coordinate_conversion_parameters(ref)
            )
            default = cc_parameters.get("grid_mapping_name", "grid_mapping")
            ncvar = self._create_netcdf_variable_name(ref, default=default)

            logger.info(
                f"    Writing {ref!r} to netCDF variable: {ncvar}"
            )  # pragma: no cover

            kwargs = {
                "varname": ncvar,
                "datatype": "S1",
                "dimensions": (),
                "endian": g["endian"],
            }
            kwargs.update(g["netcdf_compression"])

            if not g["dry_run"]:
                self._createVariable(**kwargs)

            # Add named parameters
            parameters = self.implementation.get_datum_parameters(ref)

            common = set(parameters).intersection(cc_parameters)
            if common:
                raise ValueError(
                    "Can't create CF-netCDF grid mapping variable: "
                    f"{common.pop()!r} is defined as both a coordinate "
                    "conversion and a datum parameter."
                )

            parameters.update(cc_parameters)

            for term, value in list(parameters.items()):
                if value is None:
                    del parameters[term]
                    continue

                if numpy.size(value) == 1:
                    value = numpy.array(value, copy=False).item()
                else:
                    value = numpy.array(value, copy=False).tolist()

                parameters[term] = value

            if not g["dry_run"]:
                g["nc"][ncvar].setncatts(parameters)

            # Update the 'seen' dictionary
            g["seen"][id(ref)] = {
                "variable": ref,
                "ncvar": ncvar,
                # Grid mappings have no netCDF dimensions
                "ncdims": (),
            }

        if multiple_grid_mappings:
            keys_to_ncvars = " ".join(
                sorted(
                    [
                        g["key_to_ncvar"][key]
                        for key in self.implementation.get_coordinate_reference_coordinates(
                            ref
                        )
                    ]
                )
            )
            return f"{ncvar}: {keys_to_ncvars}"
        else:
            return ncvar

    def _write_netcdf_variable(
        self,
        ncvar,
        ncdimensions,
        cfvar,
        omit=(),
        extra=None,
        fill=False,
        data_variable=False,
        domain_variable=False,
    ):
        """Creates a new netCDF variable for a construct.

        The new netCDF variable is created from *cfvar* with name
        *ncvar* and dimensions *ncdimensions*. It's properties
        are given by cfvar.properties(), less any given by the *omit*
        argument. If a new string-length netCDF dimension is required
        then it will also be created.

        The ``seen`` dictionary is updated to account for the new
        variable.

        *cfvar*.

            :Parameters:

                ncvar: `str`
                    The netCDF name of the variable.

                dimensions: `tuple`
                    The netCDF dimension names of the variable

                cfvar: `Variable`
                    The construct to write to the netCDF file.

                omit: sequence of `str`, optional

                extra: `dict`, optional

                data_variable: `bool`, optional
                    True if the a data variable is being written.

                domain_variable: `bool`, optional
                    True if the a domain variable is being written.

                    .. versionadded:: (cfdm) 1.9.0.0

            :Returns:

                `None`

        """
        # To avoid mutable default argument (an anti-pattern) of extra={}
        if extra is None:
            extra = {}

        g = self.write_vars

        # ------------------------------------------------------------
        # Set the netCDF4.createVariable datatype
        # ------------------------------------------------------------
        if domain_variable:
            data = None
            datatype = "S1"
            original_ncdimensions = ()
            ncdimensions = ()
        else:
            datatype = self._datatype(cfvar)
            data = self.implementation.get_data(cfvar, None)

            original_ncdimensions = ncdimensions

            data, ncdimensions = self._transform_strings(
                cfvar, data, ncdimensions
            )

        # Update the 'seen' dictionary
        g["seen"][id(cfvar)] = {
            "variable": cfvar,
            "ncvar": ncvar,
            "ncdims": original_ncdimensions,
        }

        # Don't ever write any variables in the 'dry run' read iteration of an
        # append-mode write (only write in the second post-dry-run iteration).
        if g["dry_run"]:
            return

        logger.info(f"    Writing {cfvar!r}")  # pragma: no cover

        # ------------------------------------------------------------
        # Find the fill value - the value that the variable's data get
        # filled before any data is written. if the fill value is
        # False then the variable is not pre-filled.
        # ------------------------------------------------------------
        if fill or g["post_dry_run"]:  # or append mode's appending iteration
            fill_value = self.implementation.get_property(
                cfvar, "_FillValue", None
            )
        else:
            fill_value = None

        if data_variable:
            lsd = g["least_significant_digit"]
        else:
            lsd = None

        # Set HDF chunksizes
        chunksizes = None
        if data is not None:
            chunksizes = self.implementation.nc_get_hdf5_chunksizes(data)

        if chunksizes is not None:
            logger.detail(
                f"      HDF5 chunksizes: {chunksizes}"
            )  # pragma: no cover

        # ------------------------------------------------------------
        # Check that each dimension of the netCDF variable name is in
        # the same group or else in a sub-group (CF>=1.8)
        # ------------------------------------------------------------
        if g["group"]:
            groups = self._groups(ncvar)
            for ncdim in ncdimensions:
                ncdim_groups = self._groups(ncdim)
                if not groups.startswith(ncdim_groups):
                    raise ValueError(
                        f"Can't create netCDF variable {ncvar!r} from "
                        f"{cfvar!r} with dimension {ncdim!r} that is not in "
                        "the same group or a sub-group as the variable."
                    )

        # ------------------------------------------------------------
        # Replace netCDF dimension names with their basenames
        # (CF>=1.8)
        # ------------------------------------------------------------
        ncdimensions_basename = [
            self._remove_group_structure(ncdim) for ncdim in ncdimensions
        ]

        # ------------------------------------------------------------
        # Create a new netCDF variable
        # ------------------------------------------------------------
        kwargs = {
            "varname": ncvar,
            "datatype": datatype,
            "dimensions": ncdimensions_basename,
            "endian": g["endian"],
            "chunksizes": chunksizes,
            "least_significant_digit": lsd,
        }
        if fill_value is not None:
            kwargs["fill_value"] = fill_value

        kwargs.update(g["netcdf_compression"])

        # Note: this is a trivial assignment in standalone cfdm, but required
        # for non-trivial customisation applied by subclasses e.g. in cf-python
        kwargs = self._customize_createVariable(cfvar, kwargs)

        logger.info(
            "        to netCDF variable: "
            f"{ncvar}({ncvar, ', '.join(ncdimensions)})"
        )  # pragma: no cover

        try:
            self._createVariable(**kwargs)
        except RuntimeError as error:
            error = str(error)
            message = (
                f"Can't create variable in {g['netcdf'].file_format} file "
                f"from {cfvar!r} ({error})"
            )
            if error == (
                "NetCDF: Not a valid data type or _FillValue type mismatch"
            ):
                raise ValueError(
                    f"Can't write {cfvar.data.dtype.name} data from {cfvar!r} "
                    f"to a {g['netcdf'].file_format} file. "
                    "Consider using a netCDF4 format, or use the 'datatype' "
                    "parameter, or change the datatype before writing."
                )
            elif error == "NetCDF: NC_UNLIMITED in the wrong index":
                raise RuntimeError(
                    f"{message}. In a {g['netcdf'].file_format} file the "
                    "unlimited dimension must be the first (leftmost) "
                    "dimension of the variable. "
                    "Consider using a netCDF4 format."
                )
            else:
                raise RuntimeError(message)

        # ------------------------------------------------------------
        # Write attributes to the netCDF variable
        # ------------------------------------------------------------
        attributes = self._write_attributes(
            cfvar, ncvar, extra=extra, omit=omit
        )

        # ------------------------------------------------------------
        # Write data to the netCDF variable
        #
        # Note that we don't need to worry about scale_factor and
        # add_offset, since if a data array is *not* a numpy array,
        # then it will have its own scale_factor and add_offset
        # parameters which will be applied when the array is realised,
        # and the python netCDF4 package will deal with the case when
        # scale_factor or add_offset are set as properties on the
        # variable.
        # ------------------------------------------------------------
        if data is not None:
            # Find the missing data values, if any.
            _FillValue = self.implementation.get_property(
                cfvar, "_FillValue", None
            )
            missing_value = self.implementation.get_property(
                cfvar, "missing_value", None
            )
            unset_values = [
                value
                for value in (_FillValue, missing_value)
                if value is not None
            ]

            compressed = bool(
                set(ncdimensions).intersection(g["sample_ncdim"].values())
            )

            self._write_data(
                data,
                cfvar,
                ncvar,
                ncdimensions,
                unset_values=unset_values,
                compressed=compressed,
                attributes=attributes,
            )

    def _customize_createVariable(self, cfvar, kwargs):
        """Customises `netCDF4.Dataset.createVariable` keywords.

        The keyword arguments may be changed in subclasses which
        override this method.

        .. versionadded:: (cfdm) 1.7.6

        :Parameters:

            cfvar: cfdm instance that contains data

            kwargs: `dict`

        :Returns:

            `dict`
                Dictionary of keyword arguments to be passed to
                `netCDF4.Dataset.createVariable`.

        """
        # This method is trivial but the intention is that subclasses will
        # override it to perform any desired customisation. Notably see
        # the equivalent method in cf-python which is non-trivial.
        return kwargs

    def _transform_strings(self, construct, data, ncdimensions):
        """Transform metadata construct arrays with string data type.

        .. versionadded:: (cfdm) 1.7.3

        :Parameters:

            construct: metadata construct object

            data: Data instance or `None`

            ncdimensions: `tuple`

        :Returns:

            `Data`, `tuple`

        """
        datatype = self._datatype(construct)

        if data is not None and datatype == "S1":
            # --------------------------------------------------------
            # Convert a string data type numpy array into a character
            # data type ('S1') numpy array with an extra trailing
            # dimension. Note that for NETCDF4 output files, datatype
            # is str, so this conversion does not happen.
            # --------------------------------------------------------
            array = self.implementation.get_array(data)
            #            if numpy.ma.is_masked(array):
            #                array = array.compressed()
            #            else:
            #                array = array.flatten()
            array = self._numpy_compressed(array)

            strlen = len(max(array, key=len))

            data = self._convert_to_char(data)
            ncdim = self._string_length_dimension(strlen)

            ncdimensions = ncdimensions + (ncdim,)

        return data, ncdimensions

    def _write_data(
        self,
        data,
        cfvar,
        ncvar,
        ncdimensions,
        unset_values=(),
        compressed=False,
        attributes=None,
    ):
        """Write a data array to the netCDF file.

        :Parameters:

            data: Data instance

            cfvar: cfdm instance

            ncvar: `str`

            ncdimensions: `tuple` of `str`

            unset_values: sequence of numbers

            attributes: `dict`, optional
                The netCDF attributes for the constructs that have been
                written to the file.

        """
        # To avoid mutable default argument (an anti-pattern) of attributes={}
        if attributes is None:
            attributes = {}

        g = self.write_vars

        if compressed:
            # if set(ncdimensions).intersection(g['sample_ncdim'].values()):
            # Get the data as a compressed numpy array
            array = self.implementation.get_compressed_array(data)
        else:
            # Get the data as an uncompressed numpy array
            array = self.implementation.get_array(data)

        # Convert data type
        new_dtype = g["datatype"].get(array.dtype)
        if new_dtype is not None:
            array = array.astype(new_dtype)

        # Check that the array doesn't contain any elements
        # which are equal to any of the missing data values
        if unset_values:
            # if numpy.ma.is_masked(array):
            #     temp_array = array.compressed()
            # else:
            #     temp_array = array
            if numpy.intersect1d(
                unset_values, self._numpy_compressed(array)
            ).size:
                raise ValueError(
                    "ERROR: Can't write data that has _FillValue or "
                    f"missing_value at unmasked point: {ncvar!r}"
                )

        if (
            g["fmt"] == "NETCDF4"
            and array.dtype.kind in "SU"
            and numpy.ma.isMA(array)
        ):
            # VLEN variables can not be assigned to by masked arrays
            # https://github.com/Unidata/netcdf4-python/pull/465
            array = array.filled("")

        if g["warn_valid"]:
            # Check for out-of-range values
            self._check_valid(cfvar, array, attributes)

        # Copy the array into the netCDF variable
        g["nc"][ncvar][...] = array

    def _check_valid(self, cfvar, array, attributes):
        """Checks if an array is considered fully valid.

        Specifically, checks array for out-of-range values, as
        defined by the valid_[min|max|range] attributes.

        .. versionadded:: (cfdm) 1.8.3

        :Parameters:

            cfvar: Construct

            array: `numpy.ndarray`

            attributes: `dict`

        :Returns:

            `bool`
                Whether or not a warning was issued.

        """
        out = 0

        valid_range = None
        valid_min = None
        valid_max = None

        if "valid_range" in attributes:
            prop = "valid_range"
            valid_range = True
            valid_min, valid_max = attributes[prop]

        # Note: leave this as str.format() as different variables are applied
        message = (
            "WARNING: {!r} has data values written to {} "
            "that are strictly {} than the valid {} "
            "defined by the {} property: {}. "
            "Set warn_valid=False to remove warning."
        )

        if "valid_min" in attributes:
            prop = "valid_min"
            if valid_range:
                raise ValueError(
                    f"Can't write {cfvar!r} with both {prop} and "
                    "valid_range properties"
                )

            valid_min = attributes[prop]

        if valid_min is not None and array.min() < valid_min:
            print(
                message.format(
                    cfvar,
                    self.write_vars["filename"],
                    "less",
                    "minimum",
                    prop,
                    valid_min,
                )
            )
            out += 1

        if "valid_max" in attributes:
            prop = "valid_max"
            if valid_range:
                raise ValueError(
                    f"Can't write {cfvar!r} with both {prop} and "
                    "valid_range properties"
                )

            valid_max = attributes[prop]

        if valid_max is not None and array.max() > valid_max:
            print(
                message.format(
                    cfvar,
                    self.write_vars["filename"],
                    "greater",
                    "maximum",
                    prop,
                    valid_max,
                )
            )
            out += 1

        return bool(out)

    def _convert_to_char(self, data):
        """Convert string data into character data.

        The returned Data object will have data type 'S1' and will
        have an extra trailing dimension.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            data: Data instance

        :Returns:

            Data instance

        """
        data = self.implementation.initialise_Data(
            array=self._character_array(self.implementation.get_array(data)),
            units=self.implementation.get_data_units(data, None),
            calendar=self.implementation.get_data_calendar(data, None),
            copy=False,
        )

        return data

    def _write_field_or_domain(
        self, f, add_to_seen=False, allow_data_insert_dimension=True
    ):
        """Write a field or domain construct to the file.

        All of the metadata constructs are also written.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            f: `Field` or `Domain`

            add_to_seen: bool, optional

            allow_data_insert_dimension: `bool`, optional

        :Returns:

            `None`

        """
        g = self.write_vars
        ncdim_size_to_spanning_constructs = []
        seen = g["seen"]

        logger.info(f"  Writing {f!r}:")  # pragma: no cover

        # Work out if we have a field or domain instance. CF-1.9
        domain = self.implementation.is_domain(f)
        field = not domain

        if domain and g["output_version"] < g["CF-1.9"]:
            raise ValueError(
                "Can't create domain variables in a "
                f"CF-{g['output_version']} dataset. Need CF-1.9 or later."
            )

        seen = g["seen"]

        org_f = f
        if add_to_seen:
            id_f = id(f)

        # Copy the field/domain, as we are almost certainly about to
        # do terrible things to it (or are we? should review this)
        f = self.implementation.copy_construct(org_f)

        if field:
            # Get the construct identifiers of the domain axes that
            # span the field's data
            data_axes = list(self.implementation.get_field_data_axes(f))
        else:
            # Get the domain axis construct identifiers of the domain
            # axes that define the domain. CF-1.9
            data_axes = list(self.implementation.get_domain_axes(f))

        # Mapping of domain axis identifiers to netCDF dimension
        # names. This gets reset for each new field/domain that is
        # written to the file.
        #
        # For example: {'domainaxis1': 'lon'}
        g["axis_to_ncdim"] = {}

        # Mapping of domain axis identifiers to netCDF scalar
        # coordinate variable names. This gets reset for each new
        # field/domain that is written to the file.
        #
        # For example: {'domainaxis0': 'time'}
        g["axis_to_ncscalar"] = {}

        # Mapping of construct internal identifiers to netCDF variable
        # names. This gets reset for each new field/domain that is
        # written to the file.
        #
        # For example: {'dimensioncoordinate1': 'longitude'}
        g["key_to_ncvar"] = {}

        # Mapping of construct internal identifiers to their netCDF
        # dimensions. This gets reset for each new field/domain that
        # is written to the file.
        #
        # For example: {'dimensioncoordinate1': ['longitude']}
        g["key_to_ncdims"] = {}

        # Type of compression applied to the field/domain
        compression_type = self.implementation.get_compression_type(f)
        g["compression_type"] = compression_type
        logger.info(
            f"    Compression = {g['compression_type']!r}"
        )  # pragma: no cover

        #
        g["sample_ncdim"] = {}

        #
        g["part_ncdim"] = None

        # Initialize the list of the field/domain's auxiliary/scalar
        # coordinates
        coordinates = []

        if g["output_version"] >= g[
            "CF-1.8"
        ] and not self.implementation.conform_geometry_variables(f):
            raise ValueError(
                f"Can't write {f!r}: node count, part node count, "
                "or interior ring variables have "
                "inconsistent properties"
            )

        g["formula_terms_refs"] = [
            ref
            for ref in list(
                self.implementation.get_coordinate_references(f).values()
            )
            if self.implementation.get_coordinate_conversion_parameters(
                ref
            ).get("standard_name", False)
        ]

        g["grid_mapping_refs"] = [
            ref
            for ref in list(
                self.implementation.get_coordinate_references(f).values()
            )
            if self.implementation.get_coordinate_conversion_parameters(
                ref
            ).get("grid_mapping_name", False)
        ]

        field_coordinates = self.implementation.get_coordinates(f)

        owning_coordinates = []
        standard_names = []
        computed_standard_names = []
        for ref in g["formula_terms_refs"]:
            coord_key = None

            standard_name = (
                self.implementation.get_coordinate_conversion_parameters(
                    ref
                ).get("standard_name")
            )
            computed_standard_name = (
                self.implementation.get_coordinate_conversion_parameters(
                    ref
                ).get("computed_standard_name")
            )

            if (
                standard_name is not None
                and computed_standard_name is not None
            ):
                for (
                    key
                ) in self.implementation.get_coordinate_reference_coordinates(
                    ref
                ):
                    coord = field_coordinates[key]

                    if not (
                        self.implementation.get_data_ndim(coord) == 1
                        and self.implementation.get_property(
                            coord, "standard_name", None
                        )
                        == standard_name
                    ):
                        continue

                    if coord_key is not None:
                        coord_key = None
                        break

                    coord_key = key

            owning_coordinates.append(coord_key)
            standard_names.append(standard_name)
            computed_standard_names.append(computed_standard_name)

        for key, csn in zip(owning_coordinates, computed_standard_names):
            if key is None:
                continue

            x = self.implementation.get_property(
                coord, "computed_standard_name", None
            )
            if x is None:
                self.implementation.set_property(
                    field_coordinates[key], "computed_standard_name", csn
                )
            elif x != csn:
                raise ValueError("Standard name could not be computed.")

        dimension_coordinates = self.implementation.get_dimension_coordinates(
            f
        )

        # For each of the field/domain's domain axes ...
        domain_axes = self.implementation.get_domain_axes(f)

        for axis, domain_axis in sorted(domain_axes.items()):
            ncdim = self.implementation.nc_get_dimension(
                domain_axis, default=None
            )
            #            if ncdim is not None:
            #                ncdim = self._netcdf_name(ncdim)
            found_dimension_coordinate = False
            for key, dim_coord in dimension_coordinates.items():
                if self.implementation.get_construct_data_axes(f, key) != (
                    axis,
                ):
                    continue

                # ----------------------------------------------------
                # Still here? Then a dimension coordinate exists for
                # this domain axis.
                # ----------------------------------------------------
                if axis in data_axes:
                    # The data array spans this domain axis, so write
                    # the dimension coordinate to the file as a
                    # coordinate variable.
                    ncvar = self._write_dimension_coordinate(
                        f, key, dim_coord, ncdim=ncdim, coordinates=coordinates
                    )
                else:
                    # The data array does not span this axis (and
                    # therefore the dimension coordinate must have
                    # size 1).
                    if (
                        not g["scalar"]
                        or len(
                            self.implementation.get_constructs(f, axes=[axis])
                        )
                        >= 2
                    ):
                        # Either A) it has been requested to not write
                        # scalar coordinate variables; or B) there ARE
                        # auxiliary coordinates, cell measures, domain
                        # ancillaries or field ancillaries which span
                        # this domain axis. Therefore write the
                        # dimension coordinate to the file as a
                        # coordinate variable.
                        ncvar = self._write_dimension_coordinate(
                            f,
                            key,
                            dim_coord,
                            ncdim=ncdim,
                            coordinates=coordinates,
                        )

                        # Expand the field's data array to include
                        # this domain axis
                        if field:
                            f = self.implementation.field_insert_dimension(
                                f, position=0, axis=axis
                            )
                    else:
                        # Scalar coordinate variables are being
                        # allowed; and there are NO auxiliary
                        # coordinates, cell measures, domain
                        # ancillaries or field ancillaries which span
                        # this domain axis. Therefore write the
                        # dimension coordinate to the file as a scalar
                        # coordinate variable.
                        coordinates = self._write_scalar_coordinate(
                            f, key, dim_coord, axis, coordinates
                        )

                # If it's a 'dry run' for append mode, assume a dimension
                # coordinate has not been found in order to run through the
                # remaining logic below.
                found_dimension_coordinate = True
                break

            if not found_dimension_coordinate:
                # ----------------------------------------------------
                # There is NO dimension coordinate for this axis
                # ----------------------------------------------------
                spanning_constructs = self.implementation.get_constructs(
                    f, axes=[axis]
                )

                spanning_auxiliary_coordinates = (
                    self.implementation.get_auxiliary_coordinates(
                        f, axes=[axis], exact=True
                    )
                )

                if (
                    axis not in data_axes
                    and spanning_constructs
                    and spanning_constructs != spanning_auxiliary_coordinates
                ):
                    # The data array doesn't span the domain axis but
                    # a cell measure, domain ancillary, field
                    # ancillary, or an N-d (N>1) auxiliary coordinate
                    # does => expand the data array to include it.
                    if field:
                        f = self.implementation.field_insert_dimension(
                            f, position=0, axis=axis
                        )
                        data_axes.append(axis)

                #                spanning_constructs = self.implementation.get_constructs(
                #                    f, axes=[axis])
                #
                #                if axis not in data_axes and spanning_constructs:
                #                    # The data array doesn't span the domain axis but
                #                    # an auxiliary coordinate, cell measure, domain
                #                    # ancillary or field ancillary does, so expand the
                #                    # data array to include it.
                #                    f = self.implementation.field_insert_dimension(
                #                            f, position=0, axis=axis)
                #                    data_axes.append(axis)

                # If the data array (now) spans this domain axis then
                # create a netCDF dimension for it
                if axis in data_axes:
                    axis_size0 = self.implementation.get_domain_axis_size(
                        f, axis
                    )

                    use_existing_dimension = False

                    if spanning_constructs:
                        for key, construct in list(
                            spanning_constructs.items()
                        ):
                            axes = self.implementation.get_construct_data_axes(
                                f, key
                            )
                            spanning_constructs[key] = (
                                construct,
                                axes.index(axis),
                            )

                        for b1 in g["ncdim_size_to_spanning_constructs"]:
                            (ncdim1, axis_size1), constructs1 = list(
                                b1.items()
                            )[0]

                            if axis_size0 != axis_size1:
                                continue

                            constructs1 = constructs1.copy()

                            matched_construct = False

                            for key0, (
                                construct0,
                                index0,
                            ) in spanning_constructs.items():
                                for key1, (
                                    construct1,
                                    index1,
                                ) in constructs1.items():
                                    if (
                                        index0 == index1
                                        and self.implementation.equal_components(
                                            construct0, construct1
                                        )
                                    ):
                                        del constructs1[key1]
                                        matched_construct = True
                                        break

                                if matched_construct:
                                    break

                            if matched_construct:
                                use_existing_dimension = True
                                break

                    if use_existing_dimension:
                        g["axis_to_ncdim"][axis] = ncdim1
                    elif (
                        g["compression_type"] == "ragged contiguous"
                        and len(data_axes) == 2
                        and axis == data_axes[1]
                    ):
                        # Do not create a netCDF dimension for the
                        # element dimension
                        g["axis_to_ncdim"][axis] = "ragged_contiguous_element"
                    elif (
                        g["compression_type"] == "ragged indexed"
                        and len(data_axes) == 2
                        and axis == data_axes[1]
                    ):
                        # Do not create a netCDF dimension for the
                        # element dimension
                        g["axis_to_ncdim"][axis] = "ragged_indexed_element"
                    elif (
                        g["compression_type"] == "ragged indexed contiguous"
                        and len(data_axes) == 3
                        and axis == data_axes[1]
                    ):
                        # Do not create a netCDF dimension for the
                        # element dimension
                        g["axis_to_ncdim"][
                            axis
                        ] = "ragged_indexed_contiguous_element1"
                    elif (
                        g["compression_type"] == "ragged indexed contiguous"
                        and len(data_axes) == 3
                        and axis == data_axes[2]
                    ):
                        # Do not create a netCDF dimension for the
                        # element dimension
                        g["axis_to_ncdim"][
                            axis
                        ] = "ragged_indexed_contiguous_element2"
                    else:
                        domain_axis = self.implementation.get_domain_axes(f)[
                            axis
                        ]
                        ncdim = self.implementation.nc_get_dimension(
                            domain_axis, "dim"
                        )

                        if not g["group"]:
                            # A flat file has been requested, so strip
                            # off any group structure from the name.
                            ncdim = self._remove_group_structure(ncdim)

                        ncdim = self._netcdf_name(ncdim)

                        unlimited = self.implementation.nc_is_unlimited_axis(
                            f, axis
                        )
                        self._write_dimension(
                            ncdim, f, axis, unlimited=unlimited
                        )

                        ncdim_size_to_spanning_constructs.append(
                            {(ncdim, axis_size0): spanning_constructs}
                        )

        if field:
            field_data_axes = tuple(self.implementation.get_field_data_axes(f))
        else:
            # For a domain, the domain axes should NOT have changed
            # since we last retrieved them. CF-1.9
            field_data_axes = tuple(data_axes)

        data_ncdimensions = [
            g["axis_to_ncdim"][axis] for axis in field_data_axes
        ]

        # ------------------------------------------------------------
        # Now that we've dealt with all of the axes, deal with
        # compression
        # ------------------------------------------------------------
        if compression_type:
            compressed_axes = tuple(self.implementation.get_compressed_axes(f))
            #            g['compressed_axes'] = compressed_axes
            compressed_ncdims = tuple(
                [g["axis_to_ncdim"][axis] for axis in compressed_axes]
            )

            if compression_type == "gathered":
                # ----------------------------------------------------
                # Compression by gathering
                #
                # Write the list variable to the file, making a note
                # of the netCDF sample dimension.
                # ----------------------------------------------------
                list_variable = self.implementation.get_list(f)
                compress = " ".join(compressed_ncdims)
                sample_ncdim = self._write_list_variable(
                    f, list_variable, compress=compress
                )

            elif compression_type == "ragged contiguous":
                # ----------------------------------------------------
                # Compression by contiguous ragged array
                #
                # Write the count variable to the file, making a note
                # of the netCDF sample dimension.
                # ----------------------------------------------------
                count = self.implementation.get_count(f)
                sample_ncdim = self._write_count_variable(
                    f, count, ncdim=data_ncdimensions[0], create_ncdim=False
                )

            elif compression_type == "ragged indexed":
                # ----------------------------------------------------
                # Compression by indexed ragged array
                #
                # Write the index variable to the file, making a note
                # of the netCDF sample dimension.
                # ----------------------------------------------------
                index = self.implementation.get_index(f)
                index_ncdim = self.implementation.nc_get_dimension(
                    index, default="sample"
                )
                if not g["group"]:
                    # A flat file has been requested, so strip off any
                    # group structure from the name.
                    index_ncdim = self._remove_group_structure(index_ncdim)

                sample_ncdim = self._write_index_variable(
                    f,
                    index,
                    sample_dimension=index_ncdim,
                    ncdim=index_ncdim,
                    create_ncdim=True,
                    instance_dimension=data_ncdimensions[0],
                )

            elif compression_type == "ragged indexed contiguous":
                # ----------------------------------------------------
                # Compression by indexed contigous ragged array
                #
                # Write the index variable to the file, making a note
                # of the netCDF sample dimension.
                # ----------------------------------------------------
                count = self.implementation.get_count(f)
                count_ncdim = self.implementation.nc_get_dimension(
                    count, default="feature"
                )

                if not g["group"]:
                    # A flat file has been requested, so strip off any
                    # group structure from the name.
                    count_ncdim = self._remove_group_structure(count_ncdim)

                sample_ncdim = self._write_count_variable(
                    f, count, ncdim=count_ncdim, create_ncdim=True
                )

                if not g["group"]:
                    # A flat file has been requested, so strip off any
                    # group structure from the name.
                    sample_ncdim = self._remove_group_structure(sample_ncdim)

                index_ncdim = count_ncdim
                index = self.implementation.get_index(f)
                self._write_index_variable(
                    f,
                    index,
                    sample_dimension=sample_ncdim,
                    ncdim=index_ncdim,
                    create_ncdim=False,
                    instance_dimension=data_ncdimensions[0],
                )

                g["sample_ncdim"][compressed_ncdims[0:2]] = index_ncdim
            else:
                raise ValueError(
                    f"Can't write {org_f!r}: Unknown compression type: "
                    f"{compression_type!r}"
                )

            g["sample_ncdim"][compressed_ncdims] = sample_ncdim

            if field:
                n = len(compressed_ncdims)
                sample_dimension = (
                    self.implementation.get_sample_dimension_position(f)
                )
                data_ncdimensions[sample_dimension : sample_dimension + n] = [
                    sample_ncdim
                ]
            else:
                # The dimensions for domain variables are not
                # ordered. CF-1.9
                data_ncdimensions = [
                    ncdim
                    for ncdim in data_ncdimensions
                    if ncdim not in compressed_ncdims
                ]
                data_ncdimensions.append(sample_ncdim)

        data_ncdimensions = tuple(data_ncdimensions)

        # ------------------------------------------------------------
        # Create auxiliary coordinate variables, except those which
        # might be completely specified elsewhere by a transformation.
        # ------------------------------------------------------------

        # Initialize the list of 'coordinates' attribute variable
        # values (each of the form 'name')
        for key, aux_coord in sorted(
            self.implementation.get_auxiliary_coordinates(f).items()
        ):
            axes = self.implementation.get_construct_data_axes(f, key)
            if len(axes) > 1 or axes[0] in data_axes:
                # This auxiliary coordinate construct spans at least
                # one of the dimensions of the field constuct's data
                # array, or the domain constructs dimensions.
                coordinates = self._write_auxiliary_coordinate(
                    f, key, aux_coord, coordinates
                )
            else:
                # This auxiliary coordinate needs to be written as a
                # scalar coordinate variable
                coordinates = self._write_scalar_coordinate(
                    f, key, aux_coord, axis, coordinates
                )

        # ------------------------------------------------------------
        # Create netCDF variables from domain ancillaries
        # ------------------------------------------------------------
        for key, anc in sorted(
            self.implementation.get_domain_ancillaries(f).items()
        ):
            self._write_domain_ancillary(f, key, anc)

        # ------------------------------------------------------------
        # Create netCDF variables from cell measures
        # ------------------------------------------------------------
        # Set the list of 'cell_measures' attribute values (each of
        # the form 'measure: name')
        cell_measures = [
            self._write_cell_measure(f, key, msr)
            for key, msr in sorted(
                self.implementation.get_cell_measures(f).items()
            )
        ]

        # ------------------------------------------------------------
        # Create netCDF formula_terms attributes from vertical
        # coordinate references
        # ------------------------------------------------------------
        for ref in g["formula_terms_refs"]:
            formula_terms = []
            bounds_formula_terms = []
            owning_coord_key = None

            standard_name = (
                self.implementation.get_coordinate_conversion_parameters(
                    ref
                ).get("standard_name")
            )
            if standard_name is not None:
                c = []
                for (
                    key
                ) in self.implementation.get_coordinate_reference_coordinates(
                    ref
                ):
                    coord = self.implementation.get_coordinates(f)[key]
                    if (
                        self.implementation.get_property(
                            coord, "standard_name", None
                        )
                        == standard_name
                    ):
                        c.append((key, coord))

                if len(c) == 1:
                    owning_coord_key, _ = c[0]

            z_axis = self.implementation.get_construct_data_axes(
                f, owning_coord_key
            )[0]

            if owning_coord_key is not None:
                # This formula_terms coordinate reference matches up
                # with an existing coordinate

                for (
                    term,
                    value,
                ) in self.implementation.get_coordinate_conversion_parameters(
                    ref
                ).items():
                    if value is None:
                        continue

                    if term in ("standard_name", "computed_standard_name"):
                        continue

                    ncvar = self._write_scalar_data(value, ncvar=term)

                    formula_terms.append(f"{term}: {ncvar}")
                    bounds_formula_terms.append(f"{term}: {ncvar}")

                for (
                    term,
                    key,
                ) in (
                    ref.coordinate_conversion.domain_ancillaries().items()
                ):  # DCH ALERT
                    if key is None:
                        continue

                    domain_anc = self.implementation.get_domain_ancillaries(f)[
                        key
                    ]
                    if domain_anc is None:
                        continue

                    if id(domain_anc) not in seen:
                        continue

                    # Get the netCDF variable name for the domain
                    # ancillary and add it to the formula_terms attribute
                    ncvar = seen[id(domain_anc)]["ncvar"]
                    formula_terms.append(f"{term}: {ncvar}")

                    bounds = g["bounds"].get(ncvar, None)
                    if bounds is not None:
                        if z_axis not in (
                            self.implementation.get_construct_data_axes(f, key)
                        ):
                            bounds = None

                    if bounds is None:
                        bounds_formula_terms.append(f"{term}: {ncvar}")
                    else:
                        bounds_formula_terms.append(f"{term}: {bounds}")

            # Add the formula_terms attribute to the parent coordinate
            # variable
            if formula_terms:
                ncvar = g["key_to_ncvar"][owning_coord_key]
                formula_terms = " ".join(formula_terms)
                if not g["dry_run"] and not g["post_dry_run"]:
                    try:
                        g["nc"][ncvar].setncattr(
                            "formula_terms", formula_terms
                        )
                    except KeyError:
                        pass  # TODO convert to 'raise' via fixes upstream

                logger.info(
                    "    Writing formula_terms attribute to "
                    f"netCDF variable {ncvar}: {formula_terms!r}"
                )  # pragma: no cover

                # Add the formula_terms attribute to the parent
                # coordinate bounds variable
                bounds_ncvar = g["bounds"].get(ncvar)
                if bounds_ncvar is not None:
                    bounds_formula_terms = " ".join(bounds_formula_terms)
                    if not g["dry_run"] and not g["post_dry_run"]:
                        try:
                            g["nc"][bounds_ncvar].setncattr(
                                "formula_terms", bounds_formula_terms
                            )
                        except KeyError:
                            pass  # TODO convert to 'raise' via fixes upstream

                    logger.info(
                        "    Writing formula_terms to netCDF bounds variable "
                        f"{bounds_ncvar}: {bounds_formula_terms!r}"
                    )  # pragma: no cover

            # Deal with a vertical datum
            if owning_coord_key is not None:
                self._create_vertical_datum(ref, owning_coord_key)

        # ------------------------------------------------------------
        # Create netCDF variables grid mappings
        # ------------------------------------------------------------
        multiple_grid_mappings = len(g["grid_mapping_refs"]) > 1

        grid_mapping = [
            self._write_grid_mapping(f, ref, multiple_grid_mappings)
            for ref in g["grid_mapping_refs"]
        ]

        # ------------------------------------------------------------
        # Field ancillary variables
        #
        # Create the 'ancillary_variables' CF-netCDF attribute and
        # create the referenced CF-netCDF ancillary variables
        # ------------------------------------------------------------
        if field:
            ancillary_variables = [
                self._write_field_ancillary(f, key, anc)
                for key, anc in self.implementation.get_field_ancillaries(
                    f
                ).items()
            ]

        # ------------------------------------------------------------
        # Create the CF-netCDF data/domain variable
        # ------------------------------------------------------------
        if field:
            default = "data"
        else:
            default = "domain"

        ncvar = self._create_netcdf_variable_name(f, default=default)

        ncdimensions = data_ncdimensions

        extra = {}

        # Cell measures
        if cell_measures:
            cell_measures = " ".join(cell_measures)
            logger.info(
                "    Writing cell_measures attribute to "
                f"netCDF variable {ncvar}: {cell_measures!r}"
            )  # pragma: no cover

            extra["cell_measures"] = cell_measures

        # Auxiliary/scalar coordinates
        if coordinates:
            coordinates = " ".join(coordinates)
            logger.info(
                "    Writing coordinates attribute to "
                f"netCDF variable {ncvar}: {coordinates!r}"
            )  # pragma: no cover

            extra["coordinates"] = coordinates

        # Grid mapping
        if grid_mapping:
            grid_mapping = " ".join(grid_mapping)
            logger.info(
                "    Writing grid_mapping attribute to "
                f"netCDF variable {ncvar}: {grid_mapping!r}"
            )  # pragma: no cover

            extra["grid_mapping"] = grid_mapping

        # Ancillary variables
        if field and ancillary_variables:
            ancillary_variables = " ".join(ancillary_variables)
            logger.info(
                "    Writing ancillary_variables attribute to "
                f"netCDF variable {ncvar}: {ancillary_variables!r}"
            )  # pragma: no cover

            extra["ancillary_variables"] = ancillary_variables

        # name can be a dimension of the variable, a scalar coordinate
        # variable, a valid standard name, or the word 'area'
        if field:
            cell_methods = self.implementation.get_cell_methods(f)
            if cell_methods:
                axis_map = g["axis_to_ncdim"].copy()
                axis_map.update(g["axis_to_ncscalar"])

                cell_methods_strings = []
                for cm in list(cell_methods.values()):
                    if not self.cf_cell_method_qualifiers().issuperset(
                        self.implementation.get_cell_method_qualifiers(cm)
                    ):
                        raise ValueError(
                            "Can't write {!r}: Unknown cell method "
                            "property: {!r}".format(org_f, cm.properties())
                        )

                    axes = [
                        axis_map.get(axis, axis)
                        for axis in self.implementation.get_cell_method_axes(
                            cm, ()
                        )
                    ]
                    self.implementation.set_cell_method_axes(cm, axes)
                    cell_methods_strings.append(
                        self.implementation.get_cell_method_string(cm)
                    )

                cell_methods = " ".join(cell_methods_strings)
                logger.info(
                    "    Writing cell_methods attribute to "
                    "netCDF variable {}: {}".format(ncvar, cell_methods)
                )  # pragma: no cover

                extra["cell_methods"] = cell_methods

        # ------------------------------------------------------------
        # Geometry container (CF>=1.8)
        # ------------------------------------------------------------
        if g["output_version"] >= g["CF-1.8"]:
            geometry_container = self._create_geometry_container(f)
            if geometry_container:
                gc_ncvar = self._write_geometry_container(
                    f, geometry_container
                )
                extra["geometry"] = gc_ncvar

        # ------------------------------------------------------------
        # Create a new CF-netCDF data/domain variable
        # ------------------------------------------------------------
        # Omit any global attributes from the variable
        omit = g["global_attributes"]
        if g["group"] and self.implementation.nc_get_variable_groups(f):
            # Also omit any group attributes from the variable
            # (CF>=1.8)
            groups = self.implementation.nc_get_group_attributes(f)
            if groups:
                omit = tuple(omit)
                omit += tuple(groups)

        if domain:
            # Include the dimanions attribute on doain
            # variables. CF-1.9
            extra["dimensions"] = " ".join(sorted(ncdimensions))

        # Note that for domain variables the ncdimensions parameter is
        # automatically changed to () within the
        # _write_netcdf_variable method.  CF-1.9
        self._write_netcdf_variable(
            ncvar,
            ncdimensions,
            f,
            omit=omit,
            extra=extra,
            data_variable=field,
            domain_variable=domain,
        )

        # Update the 'seen' dictionary, if required
        if add_to_seen:
            seen[id_f] = {
                "variable": org_f,
                "ncvar": ncvar,
                "ncdims": ncdimensions,
            }

        if ncdim_size_to_spanning_constructs:
            g["ncdim_size_to_spanning_constructs"].extend(
                ncdim_size_to_spanning_constructs
            )

    def _create_vertical_datum(self, ref, coord_key):
        """Deal with a vertical datum.

        .. versionaddedd:: 1.7.0

        """
        g = self.write_vars

        if not self.implementation.has_datum(ref):
            return

        count = [0, None]
        for grid_mapping in g["grid_mapping_refs"]:
            if self.implementation.equal_datums(ref, grid_mapping):
                count = [count[0] + 1, grid_mapping]
                if count[0] > 1:
                    break

        if count[0] == 1:
            # Add the vertical coordinate to an existing
            # horizontal coordinate reference
            logger.info(
                f"      Adding {coord_key!r} to {grid_mapping!r}"
            )  # pragma: no cover

            grid_mapping = count[1]
            self.implementation.set_coordinate_reference_coordinate(
                grid_mapping, coord_key
            )
        else:
            # Create a new horizontal coordinate reference for the
            # vertical datum
            logger.info(
                "    Creating a new horizontal coordinate reference "
                "for the vertical datum"
            )  # pragma: no cover

            new_grid_mapping = (
                self.implementation.initialise_CoordinateReference()
            )

            self.implementation.set_coordinate_reference_coordinates(
                coordinate_reference=new_grid_mapping, coordinates=[coord_key]
            )

            coordinate_conversion = (
                self.implementation.initialise_CoordinateConversion(
                    parameters={"grid_mapping_name": "latitude_longitude"}
                )
            )
            self.implementation.set_coordinate_conversion(
                coordinate_reference=new_grid_mapping,
                coordinate_conversion=coordinate_conversion,
            )

            datum = self.implementation.get_datum(ref)
            self.implementation.set_datum(
                coordinate_reference=new_grid_mapping, datum=datum
            )

            ncvar = self.implementation.nc_get_variable(datum)
            if ncvar is not None:
                if not self.write_vars["group"]:
                    # A flat file has been requested, so strip off any
                    # group structure from the name.
                    ncvar = self._remove_group_structure(ncvar)

                self.implementation.nc_set_variable(new_grid_mapping, ncvar)

            g["grid_mapping_refs"].append(new_grid_mapping)

    def _unlimited(self, field, axis):
        """Whether an axis is unlimited.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            field: Field construct

            axis: `str`

        :Returns:

            `bool`

        """
        return self.implementation.nc_is_unlimited_axis(field, axis)

    def _write_group(self, parent_group, group_name):
        """Creates a new netCDF4 parent group object.

        .. versionadded:: (cfdm) 1.8.6.0

        :Parameters:

            parent_group: `netCDF4.Dateset` or `netCDF4._netCDF4.Group`

            group_name: `str`

        :Returns:

            `netCDF4._netCDF4.Group`

        """
        return parent_group.createGroup(group_name)

    def _write_group_attributes(self, fields):
        """Writes the netCDF group-level attributes to the file.

        :Parameters:

            fields : `list` of field constructs

        :Returns:

            `None`

        """
        g = self.write_vars

        group_attributes = {}

        # ------------------------------------------------------------
        # Add properties that have been marked as group-level on each
        # field
        # ------------------------------------------------------------
        xx = {}
        for f in fields:
            groups = self.implementation.nc_get_variable_groups(f)
            if groups:
                xx.setdefault(groups, []).append(f)
                group_attributes.setdefault(groups, {}).update(
                    self.implementation.nc_get_group_attributes(f)
                )

        for groups, fields in xx.items():
            this_group_attributes = group_attributes[groups]

            f0 = fields[0]
            for prop in tuple(this_group_attributes):
                prop0 = self.implementation.get_property(f0, prop, None)

                if prop0 is None:
                    this_group_attributes.pop(prop)
                    continue

                if len(fields) > 1:
                    for f in fields[1:]:
                        prop1 = self.implementation.get_property(f, prop, None)
                        if not self.implementation.equal_properties(
                            prop0, prop1
                        ):
                            this_group_attributes.pop(prop)
                            break

            # --------------------------------------------------------
            # Write the group-level attributes to the file
            # --------------------------------------------------------
            # Replace None values with actual values
            for attr, value in this_group_attributes.items():
                if value is not None:
                    continue

                this_group_attributes[attr] = self.implementation.get_property(
                    f0, attr
                )

            nc = g["netcdf"]
            for group in groups:
                if group in nc.groups:
                    nc = nc.groups[group]
                else:
                    nc = self._create_netcdf_group(nc, group)

            if not g["dry_run"]:
                nc.setncatts(this_group_attributes)

            group_attributes[groups] = tuple(this_group_attributes)

        g["group_attributes"] = group_attributes

    def _write_global_attributes(self, fields):
        """Writes all netCDF global properties to the netCDF4 dataset.

        Specifically, finds the netCDF global properties from all of
        the input fields and writes them to the `netCDF4.Dataset`.

        :Parameters:

            fields : `list` of field constructs

        :Returns:

            `None`

        """
        g = self.write_vars

        # ------------------------------------------------------------
        # Initialize the global attributes with those requested to be
        # such
        # ------------------------------------------------------------
        global_attributes = g["global_attributes"]

        # ------------------------------------------------------------
        # Add in the standard "description of file contents"
        # attributes
        # ------------------------------------------------------------
        global_attributes.update(
            self.cf_description_of_file_contents_attributes()
        )

        # ------------------------------------------------------------
        # Add properties that have been marked as global on each field
        # ------------------------------------------------------------
        force_global = {}
        for f in fields:
            for attr, v in self.implementation.nc_get_global_attributes(
                f
            ).items():
                if v is None:
                    global_attributes.add(attr)
                else:
                    force_global.setdefault(attr, []).append(v)

        if "Conventions" not in force_global:
            for f in fields:
                v = self.implementation.nc_get_global_attributes(f).get(
                    "Conventions"
                )
                if v is not None:
                    force_global.setdefault("Conventions", []).append(v)

        force_global = {
            attr: v[0]
            for attr, v in force_global.items()
            if len(v) == len(fields) and len(set(v)) == 1
        }

        # File descriptors supercede "forced" global attributes
        for attr in g["file_descriptors"]:
            force_global.pop(attr, None)

        # ------------------------------------------------------------
        # Remove attributes that have been specifically requested to
        # not be global attributes.
        # ------------------------------------------------------------
        global_attributes.difference_update(g["variable_attributes"])

        # ------------------------------------------------------------
        # Remove properties listed as file descriptors.
        # ------------------------------------------------------------
        global_attributes.difference_update(g["file_descriptors"])

        # ------------------------------------------------------------
        # Remove attributes that are "forced" global attributes. These
        # are dealt with separately, because they may appear as global
        # and variable attributes.
        # ------------------------------------------------------------
        global_attributes.difference_update(force_global)

        # ------------------------------------------------------------
        # Remove global attributes that have different values for
        # different fields
        # ------------------------------------------------------------
        f0 = fields[0]
        for prop in tuple(global_attributes):
            prop0 = self.implementation.get_property(f0, prop, None)

            if prop0 is None:
                global_attributes.remove(prop)
                continue

            if len(fields) > 1:
                for f in fields[1:]:
                    prop1 = self.implementation.get_property(f, prop, None)
                    if not self.implementation.equal_properties(prop0, prop1):
                        global_attributes.remove(prop)
                        break

        # -----------------------------------------------------------
        # Write the Conventions global attribute to the file
        # ------------------------------------------------------------
        delimiter = " "
        set_Conventions = force_global.pop("Conventions", None)
        if g["Conventions"]:
            if isinstance(g["Conventions"], str):
                g["Conventions"] = [g["Conventions"]]
            else:
                g["Conventions"] = list(g["Conventions"])
        else:
            if set_Conventions is None:
                g["Conventions"] = []
            else:
                if "," in set_Conventions:
                    g["Conventions"] = set_Conventions.split(",")
                else:
                    g["Conventions"] = set_Conventions.split()

        for i, c in enumerate(g["Conventions"][:]):
            x = re.search(r"CF-(\d.*)", c)
            if x:
                g["Conventions"].pop(i)

        if [x for x in g["Conventions"] if "," in x]:
            raise ValueError(
                f"Conventions names can not contain commas: {g['Conventions']}"
            )

        g["output_version"] = g["latest_version"]
        g["Conventions"] = ["CF-" + str(g["output_version"])] + list(
            g["Conventions"]
        )

        if [x for x in g["Conventions"] if " " in x]:
            # At least one of the conventions contains blanks
            # space, so join them with commas.
            delimiter = ","

        if not g["dry_run"] and not g["post_dry_run"]:
            g["netcdf"].setncattr(
                "Conventions", delimiter.join(g["Conventions"])
            )

            # ------------------------------------------------------------
            # Write the file descriptors to the file
            # ------------------------------------------------------------
            for attr, value in g["file_descriptors"].items():
                g["netcdf"].setncattr(attr, value)

            # ------------------------------------------------------------
            # Write other global attributes to the file
            # ------------------------------------------------------------
            for attr in global_attributes - set(("Conventions",)):
                g["netcdf"].setncattr(
                    attr, self.implementation.get_property(f0, attr)
                )

            # ------------------------------------------------------------
            # Write "forced" global attributes to the file
            # ------------------------------------------------------------
            for attr, v in force_global.items():
                g["netcdf"].setncattr(attr, v)

        g["global_attributes"] = global_attributes

    def file_close(self, filename):
        """Close the netCDF file that has been written.

        .. versionadded:: (cfdm) 1.7.0

        :Returns:

            `None`

        """
        self.write_vars["netcdf"].close()

    def file_open(self, filename, mode, fmt, fields):
        """Open the netCDF file for writing.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            filename: `str`
                As for the *filename* parameter for initialising a
                `netCDF.Dataset` instance.

            mode: `str`
                As for the *mode* parameter for initialising a
                `netCDF.Dataset` instance.

            fmt: `str`
                As for the *format* parameter for initialising a
                `netCDF.Dataset` instance.

            fields: sequence of `Field`
                The field constructs to be written.

        :Returns:

            `netCDF.Dataset`
                A `netCDF4.Dataset` object for the file.

        """
        if fields and mode != "r":
            filename = os.path.abspath(filename)
            for f in fields:
                if filename in self.implementation.get_filenames(f):
                    raise ValueError(
                        "Can't write to a file that contains data "
                        f"that needs to be read: {filename}"
                    )

        # mode == 'w' is safer than != 'a' in case of a typo (the letters
        # are neighbours on a QWERTY keyboard) since 'w' is destructive.
        # Note that for append ('a') mode the original file is never wiped.
        if mode == "w" and self.write_vars["overwrite"]:
            os.remove(filename)

        try:
            nc = netCDF4.Dataset(filename, mode, format=fmt)
        except RuntimeError as error:
            raise RuntimeError(f"{error}: {filename}")

        return nc

    @_manage_log_level_via_verbosity
    def write(
        self,
        fields,
        filename,
        fmt="NETCDF4",
        mode="w",
        overwrite=True,
        global_attributes=None,
        variable_attributes=None,
        file_descriptors=None,
        external=None,
        Conventions=None,
        datatype=None,
        least_significant_digit=None,
        endian="native",
        compress=0,
        fletcher32=False,
        shuffle=True,
        scalar=True,
        string=True,
        extra_write_vars=None,
        verbose=None,
        warn_valid=True,
        group=True,
        coordinates=False,
    ):
        """Write field and domain constructs to a netCDF file.

        NetCDF dimension and variable names will be taken from
        variables' `ncvar` attributes and the field attribute
        `!ncdimensions` if present, otherwise they are inferred from
        standard names or set to defaults. NetCDF names may be
        automatically given a numerical suffix to avoid duplication.

        Output netCDF file global properties are those which occur in the set
        of CF global properties and non-standard data variable properties and
        which have equal values across all input fields.

        Logically identical field components are only written to the file
        once, apart from when they need to fulfil both dimension coordinate
        and auxiliary coordinate roles for different data variables.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            fields : (sequence of) `cfdm.Field`
                The field or fields to write to the file.

                See `cfdm.write` for details.

            filename: str
                The output CF-netCDF file.

                See `cfdm.write` for details.

            mode: `str`, optional
                Specify the mode of write access for the output file. One of:

                ========  =================================================
                *mode*    Description
                ========  =================================================
                ``'w'``   Open a new file for writing to. If it exists and
                          *overwrite* is True then the file is deleted
                          prior to being recreated.

                ``'a'``   Open an existing file for appending new
                          information to. The new information will be
                          incorporated whilst the original contents of the
                          file will be preserved.

                          In practice this means that new fields will be
                          created, whilst the original fields will not be
                          edited at all. Coordinates on the fields, where
                          equal, will be shared as standard.

                          For append mode, note the following:

                          * Global attributes on the file
                            will remain the same as they were originally,
                            so will become inaccurate where appended fields
                            have incompatible attributes. To rectify this,
                            manually inspect and edit them as appropriate
                            after the append operation using methods such as
                            `nc_clear_global_attributes` and
                            `nc_set_global_attribute`.

                          * Fields with incompatible ``featureType`` to
                            the original file cannot be appended.

                          * At present fields with groups cannot be
                            appended, but this will be possible in a future
                            version. Groups can however be cleared, the
                            fields appended, and groups re-applied, via
                            methods such as `nc_clear_variable_groups` and
                            `nc_set_variable_groups`, to achieve the same
                            for now.

                          * At present domain ancillary constructs of
                            appended fields may not be handled correctly
                            and can appear as extra fields. Set them on the
                            resultant fields using `set_domain_ancillary`
                            and similar methods if required.

                ``'r+'``  Alias for ``'a'``.

                ========  =================================================

                By default the file is opened with write access mode
                ``'w'``.

            overwrite: bool, optional
                If False then raise an exception if the output file
                pre-exists. By default a pre-existing output file is
                over written.

                See `cfdm.write` for details.

            verbose: bool, optional
                See `cfdm.write` for details.

            file_descriptors: `dict`, optional
                Create description of file contents netCDF global
                attributes from the specified attributes and their values.

                See `cfdm.write` for details.

            global_attributes: (sequence of) `str`, optional
                Create netCDF global attributes from the specified field
                construct properties, rather than netCDF data variable
                attributes.

                See `cfdm.write` for details.

            variable_attributes: (sequence of) `str`, optional
                Create netCDF data variable attributes from the specified
                field construct properties.

                See `cfdm.write` for details.

            external: `str`, optional
                Write metadata constructs that have data and are marked as
                external to the named external file. Ignored if there are
                no such constructs.

                See `cfdm.write` for details.

            datatype : dict, optional
                Specify data type conversions to be applied prior to writing
                data to disk.

                See `cfdm.write` for details.

            Conventions: (sequence of) `str`, optional
                Specify conventions to be recorded by the netCDF global
                 ``Conventions`` attribute.

                See `cfdm.write` for details.

            endian: `str`, optional
                The endian-ness of the output file.

                See `cfdm.write` for details.

            compress: `int`, optional
                Regulate the speed and efficiency of compression.

                See `cfdm.write` for details.

            least_significant_digit: `int`, optional
                Truncate the input field construct data arrays, but not
                the data arrays of metadata constructs.

                See `cfdm.write` for details.

            fletcher32: `bool`, optional
                If True then the Fletcher-32 HDF5 checksum algorithm is
                activated to detect compression errors. Ignored if
                *compress* is ``0``.

                See `cfdm.write` for details.

            shuffle: `bool`, optional
                If True (the default) then the HDF5 shuffle filter (which
                de-interlaces a block of data before compression by
                reordering the bytes by storing the first byte of all of a
                variable's values in the chunk contiguously, followed by
                all the second bytes, and so on) is turned off.

                See `cfdm.write` for details.

            string: `bool`, optional
                By default string-valued construct data are written as
                netCDF arrays of type string if the output file format is
                ``'NETCDF4'``, or of type char with an extra dimension
                denoting the maximum string length for any other output
                file format (see the *fmt* parameter). If *string* is False
                then string-valued construct data are written as netCDF
                arrays of type char with an extra dimension denoting the
                maximum string length, regardless of the selected output
                file format.

                See `cfdm.write` for details.

                .. versionadded:: (cfdm) 1.8.0

            warn_valid: `bool`, optional
                If False then do not print a warning when writing
                "out-of-range" data, as indicated by the values, if
                present, of any of the ``valid_min``, ``valid_max`` or
                ``valid_range`` properties on field and metadata
                constructs that have data.

                See `cfdm.write` for details.

                .. versionadded:: (cfdm) 1.8.3

            group: `bool`, optional
                If False then create a "flat" netCDF file, i.e. one with
                only the root group, regardless of any group structure
                specified by the field constructs.

                See `cfdm.write` for details.

                .. versionadded:: (cfdm) 1.8.6.0

            coordinates: `bool`, optional
                If True then include CF-netCDF coordinate variable names
                in the 'coordinates' attribute of output data
                variables.

                See `cfdm.write` for details.

                .. versionadded:: (cfdm) 1.8.7.0

        :Returns:

            `None`

        **Examples:**

        See `cfdm.write` for examples.

        """
        logger.info(f"Writing to {fmt}")  # pragma: no cover

        # Expand file name
        filename = os.path.expanduser(os.path.expandvars(filename))

        # ------------------------------------------------------------
        # Initialise netCDF write parameters
        # ------------------------------------------------------------
        self.write_vars = {
            "filename": filename,
            # Format of output file
            "fmt": None,
            # netCDF4.Dataset instance
            "netcdf": None,
            # Map netCDF variable names to netCDF4.Variable instances
            "nc": {},
            # Map netCDF dimension names to netCDF dimension sizes
            "ncdim_to_size": {},
            # Set of all netCDF dimension and netCDF variable names.
            "ncvar_names": set(()),
            # Set of global or non-standard CF properties which have
            # identical values across all input fields.
            "variable_attributes": set(),
            "global_attributes": set(),
            "file_descriptors": {},
            "group": group,
            "group_attributes": {},
            "bounds": {},
            # NetCDF compression/endian
            "netcdf_compression": {},
            "endian": "native",
            "least_significant_digit": None,
            # CF properties which need not be set on bounds if they're set
            # on the parent coordinate
            "omit_bounds_properties": (
                "units",
                "standard_name",
                "axis",
                "positive",
                "calendar",
                "month_lengths",
                "leap_year",
                "leap_month",
            ),
            # Data type conversions to be applied prior to writing
            "datatype": {},
            # Whether or not to write string data-types to netCDF4
            # files (as opposed to car data-types).
            "string": string,
            # Conventions
            "Conventions": Conventions,
            "ncdim_size_to_spanning_constructs": [],
            "count_variable_sample_dimension": {},
            "index_variable_sample_dimension": {},
            "external_variables": "",
            "external_fields": [],
            "geometry_containers": {},
            "geometry_encoding": {},
            "geometry_dimensions": set(),
            "dimensions_with_role": {},
            "dimensions": set(),
            "latest_version": LooseVersion(
                self.implementation.get_cf_version()
            ),
            "version": {},
            # Warn for the presence of out-of-range data with of
            # valid_[min|max|range] attributes?
            "warn_valid": bool(warn_valid),
            "valid_properties": set(("valid_min", "valid_max", "valid_range")),
            # Whether or not to name dimension corodinates in the
            # 'coordinates' attribute
            "coordinates": bool(coordinates),
            # Dictionary of netCDF variable names and netCDF
            # dimensions keyed by items of the field (such as a
            # coordinate or a coordinate reference)
            "seen": {},
            # Dry run: populate 'seen' dict without actually writing to file.
            "dry_run": False,
            # To indicate if the previous iteration was a dry run:
            "post_dry_run": False,
            # Note: need write_vars keys to specify dry runs (iterations)
            # and subsequent runs despite them being implied by the mode ('r'
            # and 'a' for dry_run and post_dry_run respectively) so that the
            # mode does not need to be passed to various methods, where a
            # pair of such keys seem clearer than one "effective mode" key.
        }

        if mode not in ("w", "a", "r+"):
            raise ValueError(
                "cfdm.write mode parameter must be one of 'w', 'a' or 'r+', "
                f"but got '{mode}'"
            )
        elif mode == "r+":  # support alias used by netCDF4.Dataset mode
            mode = "a"

        effective_mode = mode  # actual mode to use for the first IO iteration
        effective_fields = fields

        if mode == "a":
            # First read in the fields from the existing file:
            effective_fields = NetCDFRead(self.implementation).read(filename)

            # Read rather than append for the first iteration to ensure nothing
            # gets written; only want to update the 'seen' dictionary first.
            effective_mode = "r"
            overwrite = False
            self.write_vars["dry_run"] = True

            # Make lists of the fields to aid with iteration over them below:
            if not isinstance(fields, (list, tuple)):
                fields = [fields]
            if not isinstance(effective_fields, (list, tuple)):
                effective_fields = [effective_fields]

            # Fail ASAP if can't perform the operation:
            # 1. because attempting to append at least one field with group(s)
            if fmt == "NETCDF4":
                for f in fields:
                    if self.implementation.nc_get_variable_groups(f):
                        raise ValueError(
                            "At present append mode is unable to append fields "
                            "which have groups, however groups can be cleared, "
                            "the fields appended, and groups re-applied, via "
                            "methods such as 'nc_clear_variable_groups' and "
                            "'nc_set_variable_groups', to achieve the same."
                        )

            # 2. because the featureType on the original fields and the fields
            # to be appended are incompatible:
            original_ft = False  # no FT, distinguish from 'None' attr. value
            appended_fields_fts = []
            for ef in effective_fields:  # i.e original fields
                if "featureType" in ef.nc_global_attributes():
                    original_ft = ef.nc_global_attributes()["featureType"]
            for f in fields:  # i.e. fields to be appended
                if (
                    "featureType" in f.nc_global_attributes()
                    and f.nc_global_attributes()["featureType"] is not None
                ):
                    appended_fields_fts.append(
                        f.nc_global_attributes()["featureType"]
                    )
            # Incompatible if: 1) the appended fields have more than one
            # FT between them, 2) the original FT is not appropriate for
            # all appended fields, or 3) there is no original FT but one
            # or more across all appended fields.
            if (
                len(appended_fields_fts) > 1
                or (
                    len(appended_fields_fts) == 1
                    and original_ft is not False
                    and original_ft != appended_fields_fts[0]
                )
                or (appended_fields_fts and original_ft is not False)
            ):
                raise ValueError(
                    "Can't append fields with an incompatible 'featureType' "
                    "global attribute to the original file."
                )

        self._file_io_iteration(
            mode=effective_mode,
            overwrite=overwrite,
            fields=effective_fields,
            filename=filename,
            fmt=fmt,
            global_attributes=global_attributes,
            variable_attributes=variable_attributes,
            file_descriptors=file_descriptors,
            external=external,
            Conventions=Conventions,
            datatype=datatype,
            least_significant_digit=least_significant_digit,
            endian=endian,
            compress=compress,
            fletcher32=fletcher32,
            shuffle=shuffle,
            scalar=scalar,
            string=string,
            extra_write_vars=extra_write_vars,
            warn_valid=warn_valid,
            group=group,
        )

        if mode == "w":  # only one iteration required in this simple case
            return
        elif mode == "a":  # need another iteration to append after reading
            self.write_vars["dry_run"] = False
            self.write_vars["post_dry_run"] = True  # i.e. follows a dry run

            # Perform a second iteration to append, with knowledge of the
            # constructs existing in the file from the first iteration.
            return self._file_io_iteration(
                mode=mode,
                overwrite=overwrite,
                fields=fields,
                filename=filename,
                fmt=fmt,
                global_attributes=global_attributes,
                variable_attributes=variable_attributes,
                file_descriptors=file_descriptors,
                external=external,
                Conventions=Conventions,
                datatype=datatype,
                least_significant_digit=least_significant_digit,
                endian=endian,
                compress=compress,
                fletcher32=fletcher32,
                shuffle=shuffle,
                scalar=scalar,
                string=string,
                extra_write_vars=extra_write_vars,
                warn_valid=warn_valid,
                group=group,
            )

    def _file_io_iteration(
        self,
        mode,
        overwrite,
        fields,
        filename,
        fmt,
        global_attributes,
        variable_attributes,
        file_descriptors,
        external,
        Conventions,
        datatype,
        least_significant_digit,
        endian,
        compress,
        fletcher32,
        shuffle,
        scalar,
        string,
        extra_write_vars,
        warn_valid,
        group,
    ):
        """Perform a file-writing iteration with the given settings."""
        # ------------------------------------------------------------
        # Initiate file IO with given write variables
        # ------------------------------------------------------------
        if mode == "w":
            desc = "Writing to"
        elif mode == "a":  # append mode on a post-dry run when it appends
            desc = "Appending to"
        else:  # includes append mode on a dry-run when it does just read
            desc = "Reading from"
        logger.info(f"{desc} {fmt}")  # pragma: no cover

        g = self.write_vars

        # ------------------------------------------------------------
        # Set possible versions
        # ------------------------------------------------------------
        for version in ("1.6", "1.7", "1.8", "1.9"):
            g["CF-" + version] = LooseVersion(version)

        if extra_write_vars:
            g.update(copy.deepcopy(extra_write_vars))

        compress = int(compress)
        zlib = bool(compress)

        netcdf3_fmts = (
            "NETCDF3_CLASSIC",
            "NETCDF3_64BIT",
            "NETCDF3_64BIT_OFFSET",
            "NETCDF3_64BIT_DATA",
        )
        netcdf4_fmts = (
            "NETCDF4",
            "NETCDF4_CLASSIC",
        )
        if fmt not in netcdf3_fmts + netcdf4_fmts:
            raise ValueError(f"Unknown output file format: {fmt}")
        elif fmt in netcdf3_fmts:
            if compress in netcdf3_fmts:
                raise ValueError(f"Can't compress {fmt} format file")
            if group in netcdf3_fmts:
                # Can't write groups to a netCDF3 file
                g["group"] = False

        # ------------------------------------------------------------
        # Set up global/non-global attributes
        # ------------------------------------------------------------
        if variable_attributes:
            if isinstance(variable_attributes, str):
                variable_attributes = set((variable_attributes,))
            else:
                variable_attributes = set(variable_attributes)

            g["variable_attributes"] = variable_attributes

            if "Conventions" in variable_attributes:
                raise ValueError(
                    "Can't prevent the 'Conventions' property from being "
                    f"a netCDF global variable: {variable_attributes}"
                )

        if global_attributes:
            if isinstance(global_attributes, str):
                global_attributes = set((global_attributes,))
            else:
                global_attributes = set(global_attributes)

            g["global_attributes"] = global_attributes

        if file_descriptors:
            if "Conventions" in file_descriptors:
                raise ValueError(
                    "Use the Conventions parameter to specify conventions, "
                    "rather than a file descriptor."
                )

            g["file_descriptors"] = file_descriptors

        # ------------------------------------------------------------
        # Set up data type conversions. By default, Booleans are
        # converted to 32-bit integers and python objects are
        # converted to 64-bit floats.
        # ------------------------------------------------------------
        dtype_conversions = {
            numpy.dtype(bool): numpy.dtype("int32"),
            numpy.dtype(object): numpy.dtype(float),
        }
        if datatype:
            dtype_conversions.update(datatype)

        g["datatype"].update(dtype_conversions)

        # -------------------------------------------------------
        # Compression/endian
        # -------------------------------------------------------
        g["netcdf_compression"].update(
            {
                "zlib": zlib,
                "complevel": compress,
                "fletcher32": bool(fletcher32),
                "shuffle": bool(shuffle),
            }
        )
        g["endian"] = endian
        g["least_significant_digit"] = least_significant_digit

        g["fmt"] = fmt

        if isinstance(
            fields,
            (
                self.implementation.get_class("Field"),
                self.implementation.get_class("Domain"),
            ),
        ):
            fields = (fields,)
        else:
            try:
                fields = tuple(fields)
            except TypeError:
                raise TypeError(
                    "'fields' parameter must be a (sequence of) "
                    "Field or Domain instances"
                )

        # ------------------------------------------------------------
        # Scalar coordinate variables
        # ------------------------------------------------------------
        g["scalar"] = scalar

        g["overwrite"] = overwrite

        # ------------------------------------------------------------
        # Open the output netCDF file
        # ------------------------------------------------------------
        if os.path.isfile(filename):
            if mode == "w" and not overwrite:
                raise IOError(
                    "Can't write with mode {mode!r} to existing file "
                    f"{os.path.abspath(filename)} unless overwrite=True"
                )

            if not os.access(filename, os.W_OK):
                raise IOError(
                    "Can't write to existing file "
                    f"{os.path.abspath(filename)} without permission"
                )
        else:
            g["overwrite"] = False

        g["filename"] = filename
        g["netcdf"] = self.file_open(filename, mode, fmt, fields)

        #        # -----------------------------------------------------------
        #        # Set the fill mode for a Dataset open for writing to
        #        off. This # will prevent the data from being pre-filled with
        #        fill values, # which may result in some performance
        #        improvements.  #
        #        -------------------------------------------------------------
        #        g['netcdf'].set_fill_off()

        if not g["dry_run"]:
            # ------------------------------------------------------------
            # Write global properties to the file first. This is important
            # as doing it later could slow things down enormously. This
            # function also creates the g['global_attributes'] set, which
            # is used in the _write_field function.
            # ------------------------------------------------------------
            self._write_global_attributes(fields)

            # ------------------------------------------------------------
            # Write group-level properties to the file next
            # ------------------------------------------------------------
            if (
                g["group"] and not g["post_dry_run"]
            ):  # i.e. not for append mode
                self._write_group_attributes(fields)
        else:
            g["output_version"] = g["latest_version"]

        if external is not None:
            if g["output_version"] < g["CF-1.7"]:
                raise ValueError(
                    "Can't create external variables at "
                    f"CF-{g['output_version']}. Need CF-1.7 or later."
                )

            external = os.path.expanduser(os.path.expandvars(external))
            if os.path.realpath(external) == os.path.realpath(filename):
                raise ValueError(
                    "Can't set filename and external to the " "same path"
                )

        g["external_file"] = external

        # ------------------------------------------------------------
        # Write each field construct
        # ------------------------------------------------------------
        for f in fields:
            self._write_field_or_domain(f)

        # ------------------------------------------------------------
        # Write all of the buffered data to disk
        # ------------------------------------------------------------
        # For append mode, it is cleaner code-wise to close the file
        # on the read iteration and re-open it for the append
        # iteration. So we always close it here.
        self.file_close(filename)

        # ------------------------------------------------------------
        # Write external fields to the external file
        # ------------------------------------------------------------
        if g["external_fields"] and g["external_file"] is not None:
            self.write(
                fields=g["external_fields"],
                filename=g["external_file"],
                fmt=fmt,
                overwrite=overwrite,
                datatype=datatype,
                endian=endian,
                compress=compress,
                fletcher32=fletcher32,
                shuffle=shuffle,
                extra_write_vars=extra_write_vars,
            )
