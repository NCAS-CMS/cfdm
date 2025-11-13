import copy
import logging
import os
from math import prod
from numbers import Integral

import numpy as np

from cfdm.data.dask_utils import cfdm_to_memory
from cfdm.decorators import _manage_log_level_via_verbosity
from cfdm.functions import abspath, dirname, integer_dtype

from .. import IOWrite
from .constants import (
    CF_QUANTIZATION_PARAMETER_LIMITS,
    CF_QUANTIZATION_PARAMETERS,
    NETCDF3_FMTS,
    NETCDF4_FMTS,
    NETCDF_QUANTIZATION_PARAMETERS,
    NETCDF_QUANTIZE_MODES,
    ZARR_FMTS,
)
from .netcdfread import NetCDFRead

logger = logging.getLogger(__name__)


class AggregationError(Exception):
    """An error relating to CF aggregation.

    .. versionadded:: (cfdm) 1.12.0.0

    """

    pass


class NetCDFWrite(IOWrite):
    """A container for writing Fields to a netCDF dataset.

    NetCDF3, netCDF4 and Zarr output formats are supported.

    """

    def __new__(cls, *args, **kwargs):
        """Store the NetCDFRead class."""
        instance = super().__new__(cls)
        instance._NetCDFRead = NetCDFRead
        return instance

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
        return set(("point", "line", "polygon"))

    def cf_cell_method_qualifiers(self):
        """Cell method qualifiers."""
        return set(("within", "where", "over", "interval", "comment"))

    def _createGroup(self, parent, group_name):
        """Creates a new dataset group object.

        .. versionadded:: (cfdm) 1.8.6.0

        :Parameters:

            parent: `netCDF4.Dateset` or `netCDF4.Group` or `Zarr.Group`
                The group in which to create the new group.

            group_name: `str`
                The name of the group.

        :Returns:

            `netCDF4.Group` or `Zarr.Group`
                The new group object.

        """
        g = self.write_vars
        match g["backend"]:
            case "netCDF4":
                return parent.createGroup(group_name)

            case "zarr":
                if group_name in parent:
                    return parent[group_name]

                return parent.create_group(
                    group_name, overwrite=g["overwrite"]
                )

    def _create_variable_name(self, parent, default):
        """Create an appropriate name for a dataset variable.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            parent:

            default: `str`

        :Returns:

            `str`
                The dataset variable name.

        """
        ncvar = self.implementation.nc_get_variable(parent, None)

        if ncvar is None:
            try:
                ncvar = self.implementation.get_property(
                    parent, "standard_name", default
                )
            except AttributeError:
                ncvar = default
        elif not self.write_vars["group"]:
            # A flat dataset has been requested, so strip off any
            # group structure from the name.
            ncvar = self._remove_group_structure(ncvar)

        return self._name(ncvar)

    def _name(self, base, dimsize=None, role=None):
        """Return a new variable or dimension name for the dataset.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            base: `str`

            dimsize: `int`, optional

            role: `str`, optional

        :Returns:

            `str`
                The name of the new dimension or variable.

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

            for ncdim in g["dimensions_with_role"].get(role, ()):
                if g["ncdim_to_size"][ncdim] == dimsize:
                    # Return the name of an existing dataset dimension
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

        **Examples**

        >>> x = numpy.ma.array(numpy.arange(5), mask=[0]*2 + [1]*3)
        >>> c = n._numpy_compressed(x)
        >>> c
        array([0, 1])
        >>> type(c)
        <type 'numpy.ndarray'>

        """
        if np.ma.isMA(array):
            return array.compressed()

        return array.flatten()

    def _write_variable_attributes(self, parent, ncvar, extra=None, omit=()):
        """Write variable attributes to the dataset.

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
                netcdf_attrs[attr] = np.array(netcdf_attrs[attr], dtype=dtype)

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
            self._set_attributes(netcdf_attrs, ncvar)

        if skip_set_fill_value:
            # Re-add as known attribute since this FV is already set
            netcdf_attrs["_FillValue"] = self.implementation.get_data(
                parent, None
            ).get_fill_value()

        return netcdf_attrs

    def _set_attributes(self, attributes, ncvar=None, group=None):
        """Set dataset attributes on a variable or group.

        .. versionadded:: (cfdm) NEXTVERSION

        :Parameters:

            attributes: `dict`
                The attributes.

            ncvar: `str`, optional
                The variable on which to set the attributes. Must be
                set if *group* is `None`.

            group: `str`, optional
                The group on which to set the attributes. Must be set
                if *ncvar* is `None`.

        :Returns:

            `None`

        """
        g = self.write_vars
        if ncvar is not None:
            # Set variable attributes
            x = g["nc"][ncvar]
        elif group is not None:
            # Set group-level attributes
            x = group
        else:
            raise ValueError("Must set ncvar or group")

        match g["backend"]:
            case "netCDF4":
                x.setncatts(attributes)
            case "zarr":
                # `zarr` can't encode numpy arrays in the zarr.json
                # file
                for attr, value in attributes.items():
                    if isinstance(value, np.ndarray):
                        attributes[attr] = value.tolist()

                x.update_attributes(attributes)

    def _character_array(self, array):
        """Converts a numpy array of strings to character data type.

        As well as the data type conversion from string to character,
        the output numpy character array is given an extra trailing
        dimension.

        :Parameters:

            array: `numpy.ndarray`

        :Returns:

            `numpy.ndarray`

        **Examples**

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

        masked = np.ma.isMA(array)
        if masked:
            fill_value = array.fill_value
            array = np.ma.filled(array, fill_value="")

        if array.dtype.kind == "U":
            array = array.astype("S")

        array = np.array(tuple(array.tobytes().decode("ascii")), dtype="S1")

        array.resize(original_shape + (array.size // original_size,))

        if masked:
            array = np.ma.masked_where(array == b"", array)
            array.set_fill_value(fill_value)

        if array.dtype.kind != "S":
            raise ValueError("Array must have string data type.")

        return array

    def _datatype(self, variable):
        """Returns the input variable array's netCDF4-like data type.

        Specifically return the `netCDF4.createVariable` data type
        corresponding to the data type of the array of the input
        variable.

        For example, if variable.dtype is 'float32', then 'f4' will be
        returned.

        For a NETCDF4 format dataset, numpy string data types will
        either return `str` regardless of the numpy string length (and
        a netCDF4 string type variable will be created) or, if
        `self.write_vars['string']`` is `False`, ``'S1'`` (see below).

        For all other output netCDF formats (such NETCDF4_CLASSIC,
        NETCDF3_64BIT, etc.) numpy string data types will return 'S1'
        regardless of the numpy string length. This means that the
        required conversion of multi-character datatype numpy arrays into
        single-character datatype numpy arrays (with an extra trailing
        dimension) is expected to be done elsewhere (currently in the
        _write_netcdf_variable method).

        If the input variable has no `!dtype` attribute (or it is
        None) then 'S1' is returned, or `str` for NETCDF datasets.

        :Parameters:

            variable:
                A numpy array or an object with a `get_data` method.

        :Returns:

           `str` or str
               The `_createVariable` data type corresponding to the
               datatype of the array of the input variable.

        """
        g = self.write_vars

        if not isinstance(variable, np.ndarray):
            data = self.implementation.get_data(variable, None)
            if data is None:
                if g["fmt"] == "ZARR3":
                    return str

                return "S1"
        else:
            data = variable

        dtype = getattr(data, "dtype", None)
        if dtype is None or dtype.kind in "SU":
            fmt = g["fmt"]
            if fmt == "NETCDF4" and g["string"]:
                return str

            if fmt == "ZARR3":
                return str

            return "S1"

        new_dtype = g["datatype"].get(dtype, None)
        if new_dtype is not None:
            dtype = new_dtype

        return f"{dtype.kind}{dtype.itemsize}"

    def _string_length_dimension(self, size):
        """Return a dataset dimension for string variables.

        The dataset dimension will be created, if required.

        :Parameters:

            size: `int`

        :Returns:

            `str`
                The dataset dimension name.

        """
        g = self.write_vars

        # ------------------------------------------------------------
        # Create a new dimension for the maximum string length
        # ------------------------------------------------------------
        ncdim = self._name(f"strlen{size}", dimsize=size, role="string_length")

        if ncdim not in g["ncdim_to_size"]:
            # This string length dimension needs creating
            g["ncdim_to_size"][ncdim] = size

            # Define (and create if necessary) the group in which to
            # place this dataset dimension.
            parent_group = self._parent_group(ncdim)

            if not g["dry_run"]:
                try:
                    self._createDimension(parent_group, ncdim, size)
                except RuntimeError:
                    pass  # TODO convert to 'raise' via fixes upstream

        return ncdim

    def _createDimension(self, group, ncdim, size):
        """Create a dataset dimension in group.

        .. versionadded:: (cfdm) NEXTVERSION

        :Parameters:

            group: `netCDF.Dataset` or `netCDF.Group` or `zarr.Group`
                The group in which to create the dimension.

            ncdim: `str`
                The name of the dimension in the group.

            size: `int`
                The size of the dimension.

        :Returns:

            `None`

        """
        match self.write_vars["backend"]:
            case "netCDF4":
                group.createDimension(ncdim, size)
            case "zarr":
                # Dimensions are not created in Zarr datasets
                pass

    def _dataset_dimensions(self, field, key, construct):
        """Returns the dataset dimension names for the construct.

        The names are returned in a tuple. If the metadata construct
        has no data, then `None` is returned.

        :Parameters:

            field: Field construct

            key: `str`
                The construct identifier of the metadata construct.

                *Parameter example:*
                  ``'auxiliarycoordinate1'``

        :Returns:

            `tuple` or `None`
                The dataset dimension names, or `None` if there are no
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
                    # the dataset, so write it and also get the
                    # dataset name of the sample dimension.
                    list_variable = self.implementation.get_list(construct)
                    sample_ncdim = self._write_list_variable(
                        field,
                        list_variable,
                        #
                        compress=" ".join(compressed_ncdims),
                    )
                    g["sample_ncdim"][compressed_ncdims] = sample_ncdim

            elif compression_type == "ragged contiguous":
                # ----------------------------------------------------
                # Compression by contiguous ragged array
                #
                # No need to do anything because i) the count variable
                # has already been written to the dataset, ii) we
                # already have the position of the sample dimension in
                # the compressed array, and iii) we already have the
                # dataset name of the sample dimension.
                # ----------------------------------------------------
                pass

            elif compression_type == "ragged indexed":
                # ----------------------------------------------------
                # Compression by indexed ragged array
                #
                # No need to do anything because i) the index variable
                # has already been written to the dataset, ii) we
                # already have the position of the sample dimension in
                # the compressed array, and iii) we already have the
                # dataset name of the sample dimension.
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
        """Write a dimension to the dataset.

        :Parameters:

            ncdim: `str`
                The dataset dimension name.

            f: `Field` or `Domain`

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
                f"    Writing {domain_axis!r} to dimension: {ncdim}"
            )  # pragma: no cover

            size = self.implementation.get_domain_axis_size(f, axis)
            g["axis_to_ncdim"][axis] = ncdim

        g["ncdim_to_size"][ncdim] = size

        # Define (and create if necessary) the group in which to place
        # this dataset dimension.
        parent_group = self._parent_group(ncdim)

        if g["group"] and "/" in ncdim and g["backend"] != "zarr":
            # This dimension needs to go into a sub-group so replace
            # its name with its basename (CF>=1.8)
            ncdim = self._remove_group_structure(ncdim)

        # Dimensions are not created in Zarr datasets
        if not g["dry_run"] and g["backend"] != "zarr":
            if unlimited:
                # Create an unlimited dimension
                size = None
                try:
                    parent_group.createDimension(ncdim, size)
                except RuntimeError as error:
                    message = (
                        "Can't create unlimited dimension "
                        f"in {g['netcdf'].data_model} dataset ({error})."
                    )

                    error = str(error)
                    if error == "NetCDF: NC_UNLIMITED size already in use":
                        raise RuntimeError(
                            message
                            + f" In a {g['netcdf'].data_model} dataset only "
                            "one unlimited dimension is allowed. Consider "
                            "using a netCDF4 format."
                        )

                    raise RuntimeError(message)
                else:
                    g["unlimited_dimensions"].add(ncdim)
            else:
                try:
                    parent_group.createDimension(ncdim, size)
                except RuntimeError as error:
                    raise RuntimeError(
                        f"Can't create size {size} dimension {ncdim!r} in "
                        f"{g['netcdf'].data_model} dataset ({error})"
                    )

        g["dimensions"].add(ncdim)

    def _write_dimension_coordinate(self, f, key, coord, ncdim, coordinates):
        """Write a coordinate and bounds variables to the dataset.

        For netCDF datasets, this also writes a new dimension to the
        dataset and, if required, a new dimension for the bounds.

        :Parameters:

            f: Field construct

            key: `str`

            coord: Dimension coordinate construct

            ncdim: `str` or `None`
                The name of the dataset dimension for this dimension
                coordinate construct, including any groups
                structure. Note that the group structure may be
                different to the coordinate variable, and the
                basename.

            coordinates: `list`
               This list may get updated in-place.

               .. versionadded:: (cfdm) 1.8.7.0

        :Returns:

            `str`
                The dataset name of the dimension coordinate.

        """
        g = self.write_vars
        seen = g["seen"]

        data_axes = self.implementation.get_construct_data_axes(f, key)
        axis = data_axes[0]

        coord = self._change_reference_datetime(coord)

        already_in_file = self._already_in_file(coord)

        create = False
        if not already_in_file:
            create = True
        elif seen[id(coord)]["ncdims"] != ():
            if seen[id(coord)]["ncvar"] != seen[id(coord)]["ncdims"][0]:
                # Already seen this coordinate but it was an auxiliary
                # coordinate, so it needs to be created as a dimension
                # coordinate.
                create = True

        # If the dimension coordinate is already in the dataset but
        # not in an approriate group then we have to create a new
        # dataset variable. This is to prevent a downstream error
        # ocurring when the parent data variable tries to reference
        # one of its dataset dimensions that is not in the same group
        # nor a parent group.
        if already_in_file and not create:
            ncvar = coord.nc_get_variable("")
            groups = self._groups(seen[id(coord)]["ncvar"])
            if not ncvar.startswith(groups):
                create = True

        if create:
            ncvar = self._create_variable_name(coord, default=None)
            if ncvar is None:
                # No dataset variable name has been set, so use the
                # corresponding dataset dimension name
                ncvar = ncdim

            if ncvar is None:
                # No dataset variable name not correponding to a
                # dataset dimension name has been set, so create a
                # default dataset variable name.
                ncvar = self._create_variable_name(coord, default="coordinate")

            ncdim = ncvar

            # Create a new dataset dimension
            unlimited = self._unlimited(f, axis)
            self._write_dimension(ncdim, f, axis, unlimited=unlimited)

            ncdimensions = self._dataset_dimensions(f, key, coord)

            # If this dimension coordinate has bounds then write the
            # bounds to the dataset and add the 'bounds' or
            # 'climatology' attribute (as appropriate) to a dictionary
            # of extra attributes
            extra = self._write_bounds(f, coord, key, ncdimensions, ncvar)

            # Create a new dimension coordinate dataset variable
            self._write_netcdf_variable(
                ncvar,
                ncdimensions,
                coord,
                self.implementation.get_data_axes(f, key),
                extra=extra,
            )
        else:
            ncvar = seen[id(coord)]["ncvar"]
            ncdimensions = seen[id(coord)]["ncdims"]

        g["key_to_ncvar"][key] = ncvar
        g["key_to_ncdims"][key] = ncdimensions
        g["axis_to_ncdim"][axis] = seen[id(coord)]["ncdims"][0]

        if g["coordinates"] and ncvar is not None:
            # Add the dimension coordinate dataset variable name to
            # the 'coordinates' attribute
            coordinates.append(ncvar)

        return ncvar

    def _write_count_variable(
        self, f, count_variable, ncdim=None, create_ncdim=True
    ):
        """Write a count variable to the dataset."""
        g = self.write_vars

        if not self._already_in_file(count_variable):
            ncvar = self._create_variable_name(count_variable, default="count")

            if create_ncdim:
                ncdim = self._name(ncdim)
                self._write_dimension(
                    ncdim,
                    f,
                    None,
                    size=self.implementation.get_data_size(count_variable),
                )

            # --------------------------------------------------------
            # Create the sample dimension
            # --------------------------------------------------------
            sample_ncdim = self.implementation.nc_get_sample_dimension(
                count_variable, "element"
            )
            sample_ncdim = self._name(sample_ncdim)
            self._write_dimension(
                sample_ncdim,
                f,
                None,
                size=int(self.implementation.get_data_sum(count_variable)),
            )

            extra = {"sample_dimension": sample_ncdim}

            # Create a new count variable
            self._write_netcdf_variable(
                ncvar, (ncdim,), count_variable, None, extra=extra
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
        """Write an index variable to the dataset.

        :Parameters:

            f: Field construct

            index_variable: Index variable

            sample_dimension: `str`
                The name of the dataset sample dimension.

            ncdim: `str`, optional

            create_ncdim: bool, optional

            instance_dimension: `str`, optional
                The name of the dataset instance dimension.

        :Returns:

            `str`
                The name of the dataset sample dimension.

        """
        g = self.write_vars

        if not self._already_in_file(index_variable):
            ncvar = self._create_variable_name(index_variable, default="index")

            if create_ncdim:
                ncdim = self._name(ncdim)
                self._write_dimension(
                    ncdim,
                    f,
                    None,
                    size=self.implementation.get_data_size(index_variable),
                )

            # Create a new index variable
            extra = {"instance_dimension": instance_dimension}
            self._write_netcdf_variable(
                ncvar, (ncdim,), index_variable, None, extra=extra
            )

            g["index_variable_sample_dimension"][ncvar] = sample_dimension
        else:
            ncvar = g["seen"][id(index_variable)]["ncvar"]

        return sample_dimension

    def _write_list_variable(self, f, list_variable, compress):
        """Write a list variable to the dataset."""
        g = self.write_vars

        create = not self._already_in_file(list_variable)

        if create:
            ncvar = self._create_variable_name(list_variable, default="list")

            # Create a new dimension
            self._write_dimension(
                ncvar, f, size=self.implementation.get_data_size(list_variable)
            )

            extra = {"compress": compress}

            # Create a new list variable
            self._write_netcdf_variable(
                ncvar, (ncvar,), list_variable, None, extra=extra
            )

            self.implementation.nc_set_variable(list_variable, ncvar)  # Why?
        else:
            ncvar = g["seen"][id(list_variable)]["ncvar"]

        return ncvar

    def _write_scalar_data(self, f, value, ncvar):
        """Write a dimension coordinate and bounds to the dataset.

        For netCDF datasets, this also writes a new dimension to the
        dataset and, if required, a new bounds dimension.

        .. note:: This function updates ``g['seen']``.

        :Parameters:

            data: Data instance

            ncvar: `str`

        :Returns:

            `str`
                The dataset name of the scalar data variable

        """
        g = self.write_vars

        seen = g["seen"]

        create = not self._already_in_file(value, ncdims=())

        if create:
            ncvar = self._name(ncvar)  # DCH ?

            # Create a new dimension coordinate variable
            self._write_netcdf_variable(ncvar, (), value, None)
        else:
            ncvar = seen[id(value)]["ncvar"]

        return ncvar

    def _create_geometry_container(self, field):
        """Create a geometry container variable in the dataset.

        .. versionadded:: (cfdm) 1.8.0

        :Parameters:

            field: Field construct

        :Returns:

            `dict`
                A representation off the CF geometry container
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
            gc.setdefault(geometry_id, {"geometry_type": geometry_type})

            # Nodes
            nodes_ncvar = g["seen"][id(nodes)]["ncvar"]
            gc[geometry_id].setdefault("node_coordinates", []).append(
                nodes_ncvar
            )

            # Coordinates
            try:
                coord_ncvar = g["seen"][id(coord)]["ncvar"]
            except KeyError:
                # There is no auxiliary coordinate dataset variable
                pass
            else:
                gc[geometry_id].setdefault("coordinates", []).append(
                    coord_ncvar
                )

            # Grid mapping
            grid_mappings = [
                g["seen"][id(cr)]["ncvar"]
                for cr in self.implementation.get_coordinate_references(
                    field
                ).values()
                if self.implementation.get_coordinate_conversion_parameters(
                    cr
                ).get("grid_mapping_name")
                is not None
                and key in cr.coordinates()
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

        If this is the case then the variable has already been written
        to the output dataset and so we don't need to do it again.

        If 'ncdims' is set then a extra condition for equality is
        applied, namely that of 'ncdims' being equal to the dataset
        dimensions (names and order) to that of a variable in the
        g['seen'] dictionary.

        When `True` is returned, the input variable is added to the
        g['seen'] dictionary.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            variable:

            ncdims: `tuple`, optional

                *Parameter example:*
                  ``('x', 'y')``

                *Parameter example:*
                  Dimensions can be in a group other than the root
                  group: ``('/Dew_Point/stations',)``

            ignore_type: `bool`, optional

        :Returns:

            `bool`
                `True` if the variable has already been written to the
                dataset, `False` otherwise.

        """
        g = self.write_vars

        seen = g["seen"]

        for value in seen.values():
            if ncdims is not None and ncdims != value["ncdims"]:
                # The dataset dimensions (names and order) of the
                # input variable are different to those of this
                # variable in the 'seen' dictionary
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
        """Write a geometry container variable to the dataset.

        .. versionadded:: (cfdm) 1.8.0

        :Returns:

            `str`
                The dataset variable name for the geometry container.

        """
        g = self.write_vars

        for ncvar, gc in g["geometry_containers"].items():
            if geometry_container == gc:
                # Use this existing geometry container
                return ncvar

        # Still here? Then write the geometry container to the
        # dataset.
        ncvar = self.implementation.nc_get_geometry_variable(
            field, default="geometry_container"
        )
        ncvar = self._name(ncvar)

        logger.info(
            f"    Writing geometry container variable: {ncvar}"
        )  # pragma: no cover
        logger.info(f"        {geometry_container}")  # pragma: no cover

        kwargs = {
            "varname": ncvar,
            "datatype": "S1",
            "endian": g["endian"],
        }
        kwargs.update(g["netcdf_compression"])

        if not g["dry_run"]:
            self._createVariable(**kwargs)
            self._set_attributes(geometry_container, ncvar)

        # Update the 'geometry_containers' dictionary
        g["geometry_containers"][ncvar] = geometry_container

        return ncvar

    def _write_bounds(
        self, f, coord, coord_key, coord_ncdimensions, coord_ncvar=None
    ):
        """Creates a bounds dataset variable.

        For netCDF datasets, also creates a new bounds dimension if
        required.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            f: Field construct

            coord:

            coord_key: `str`
                The coordinate construct key.

            coord_ncdimensions: `tuple` of `str`
                The ordered dataset dimension names of the
                coordinate's dimensions (which do not include the
                bounds dimension).

            coord_ncvar: `str`
                The datset variable name of the parent variable

        :Returns:

            `dict`

        **Examples**

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
                f, coord, coord_ncvar, coord_ncdimensions
            )
            return extra

        # Still here? Then this coordinate has non-geometry bounds
        # with data
        extra = {}

        size = data.shape[-1]

        bounds_ncdim = self.implementation.nc_get_dimension(
            bounds, f"bounds{size}"
        )
        if not g["group"]:
            # A flat dataset has been requested, so strip off any
            # group structure from the name.
            bounds_ncdim = self._remove_group_structure(bounds_ncdim)

        bounds_ncdim = self._name(bounds_ncdim, dimsize=size, role="bounds")

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
                    f"    Writing size {size} dimension for "
                    f"bounds: {bounds_ncdim}"
                )  # pragma: no cover

                ncdim_to_size[bounds_ncdim] = size

                # Define (and create if necessary) the group in which
                # to place this dataset dimension.
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
                        self._createDimension(
                            parent_group, base_bounds_ncdim, size
                        )
                    except RuntimeError:
                        raise

                # Set the bounds dataset variable name
                default = coord_ncvar + "_bounds"
            else:
                default = "bounds"

            ncvar = self.implementation.nc_get_variable(
                bounds, default=default
            )

            if not self.write_vars["group"]:
                # A flat dataset has been requested, so strip off any
                # group structure from the name (for now).
                ncvar = self._remove_group_structure(ncvar)

            ncvar = self._name(ncvar)

            # If no groups have been set on the bounds, then put the
            # bounds variable in the same group as its parent
            # coordinates
            bounds_groups = self._groups(ncvar)
            coord_groups = self._groups(coord_ncvar)
            if not bounds_groups and coord_groups:
                ncvar = coord_groups + ncvar

            # Note that, in a field, bounds always have equal units to
            # their parent coordinate

            # Select properties to omit
            omit = []
            for prop in g["omit_bounds_properties"]:
                if self.implementation.has_property(coord, prop):
                    omit.append(prop)

            # Create the bounds dataset variable
            self._write_netcdf_variable(
                ncvar,
                ncdimensions,
                bounds,
                self.implementation.get_data_axes(f, coord_key),
                omit=omit,
                construct_type=self.implementation.get_construct_type(coord),
            )

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

    def _write_node_coordinates(
        self, f, coord, coord_ncvar, coord_ncdimensions
    ):
        """Create a node coordinates dataset variable.

        This will create:

        * A dataset node dimension, if required.
        * A dataset node count variable, if required.
        * A dataset part node count variable, if required.
        * A dataset interior ring variable, if required.

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

        # Find the base of the 'part' dataset dimension name
        size = self.implementation.get_data_size(nodes)
        ncdim = self._get_node_ncdimension(nodes, default="node")
        ncdim = self._name(ncdim, dimsize=size, role="node")

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
                # in the dataset, too. This is so that the geometry
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
                    f"    Writing size {size} geometry node dimension: {ncdim}"
                )  # pragma: no cover

                ncdim_to_size[ncdim] = size

                # Define (and create if necessary) the group in which
                # to place this dataset dimension.
                parent_group = self._parent_group(ncdim)

                if g["group"] and "/" in ncdim:
                    # This dimension needs to go into a sub-group so
                    # replace its name with its basename (CF>=1.8)
                    ncdim = self._remove_group_structure(ncdim)

                if not g["dry_run"]:
                    # parent_group.createDimension(ncdim, size)
                    self._createDimension(parent_group, ncdim, size)

            # Set an appropriate default node coordinates dataset
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
                # A flat dataset has been requested, so strip off any
                # group structure from the name.
                ncvar = self._remove_group_structure(ncvar)

            ncvar = self._name(ncvar)

            # Create the node coordinates dataset variable
            self._write_netcdf_variable(
                ncvar,
                (ncdim,),
                nodes,
                None,
                construct_type=self.implementation.get_construct_type(coord),
            )

            encodings = {}

            nc_encodings = self._write_node_count(
                f, coord, bounds, coord_ncdimensions, encodings
            )
            encodings.update(nc_encodings)

            pnc_encodings = self._write_part_node_count(
                f, coord, bounds, encodings
            )
            encodings.update(pnc_encodings)

            ir_encodings = self._write_interior_ring(
                f, coord, bounds, encodings
            )
            encodings.update(ir_encodings)

            g["geometry_encoding"][ncvar] = encodings

            # We need to log the original Bounds variable as being in
            # the dataset, too. This is so that the geometry container
            # variable can be created later on.
            g["seen"][id(bounds)] = {
                "ncvar": ncvar,
                "variable": bounds,
                "ncdims": None,
            }

        if coord_ncvar is not None:
            g["bounds"][coord_ncvar] = ncvar

        return {"nodes": ncvar}

    def _write_node_count(
        self, f, coord, bounds, coord_ncdimensions, encodings
    ):
        """Create a node count dataset variable.

        .. versionadded:: (cfdm) 1.8.0

        :Parameters:

            coord:

            bounds:

            coord_ncdimensions: sequence of `str`
                The dataset instance dimension

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
            array = np.ma.count(array, axis=1)  # DCH
        else:  # DCH
            array = np.ma.count(array, axis=2).sum(axis=1)  # DCH

        array = self._int32(array)

        data = self.implementation.initialise_Data(array=array, copy=False)

        # ------------------------------------------------------------
        # Create a count variable to hold the node count data and
        # properties. This is what will be written to disk.
        # ------------------------------------------------------------
        count = self.implementation.initialise_Count()
        self.implementation.set_data(count, data, copy=False)

        # Find the base of the node count dataset variable name
        nc = self.implementation.get_node_count(coord)

        if nc is not None:
            ncvar = self.implementation.nc_get_variable(
                nc, default="node_count"
            )

            if not self.write_vars["group"]:
                # A flat dataset has been requested, so strip off any
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
                    "The dataset geometry dimension should already exist ..."
                )

            ncvar = self._name(ncvar)

            # Create the node count dataset variable
            self._write_netcdf_variable(
                ncvar, (geometry_dimension,), count, None
            )

        # Return encodings
        return {"geometry_dimension": geometry_dimension, "node_count": ncvar}

    def _get_part_ncdimension(self, coord, default=None):
        """Gets dimension name for part node counts or interior rings.

        Specifically, gets the base of the dataset dimension for part
        node count and interior ring variables.

        .. versionadded:: (cfdm) 1.8.0

        :Returns:

            The dataset dimension name, or else the value of the
            *default* parameter.

        """
        ncdim = None

        pnc = self.implementation.get_part_node_count(coord)
        if pnc is not None:
            # Try to get the dataset dimension from a part node count
            # variable
            ncdim = self.implementation.nc_get_dimension(pnc, default=None)

        if ncdim is None:
            # Try to get the dataset dimension from an interior ring
            # variable
            interior_ring = self.implementation.get_interior_ring(coord)
            if interior_ring is not None:
                ncdim = self.implementation.nc_get_dimension(
                    interior_ring, default=None
                )

        if ncdim is not None:
            # Found a dataset dimension
            if not self.write_vars["group"]:
                # A flat dataset has been requested, so strip off any
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
                The name of the dataset dimension or variable.

        :Returns:

            `netCDF.Dataset` or `netCDF.Group` or `zarr.Group`

        """
        g = self.write_vars

        parent_group = g["dataset"]

        if not g["group"] or "/" not in name:
            return parent_group

        if not name.startswith("/"):
            raise ValueError(
                f"Invalid dataset name {name!r}: missing a leading '/'"
            )

        for group_name in name.split("/")[1:-1]:
            parent_group = self._createGroup(parent_group, group_name)

        return parent_group

    def _remove_group_structure(self, name, return_groups=False):
        """Strip off any group structure from the name.

        .. versionaddedd:: (cfdm) 1.8.6.0

        :Parameters:

            name: `str`

            return_groups: `bool`, optional

        :Returns:

            `str`

        **Examples**

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

        .. versionaddedd:: (cfdm) 1.8.7.0

        :Parameters:

            name: `str`

        :Returns:

            `str`

        **Examples**

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
        """Get the dataset dimension from a node count variable.

        .. versionadded:: (cfdm) 1.8.0

        :Parameters:

            bounds: Bounds component

            default: optional

        :Returns:

            The dimension name, or else the value of the *default*
            parameter.

        """
        ncdim = self.implementation.nc_get_dimension(bounds, default=None)
        if ncdim is not None:
            # Found a dimension
            if not self.write_vars["group"]:
                # A flat dataset has been requested, so strip off any
                # group structure from the name.
                ncdim = self._remove_group_structure(ncdim)

            return ncdim

        # Return the default
        return default

    def _write_part_node_count(self, f, coord, bounds, encodings):
        """Creates a part node count variable and returns its name.

        .. versionadded:: (cfdm) 1.8.0

        :Parameters:

            coord:

        :Returns:

            `dict`

        **Examples**

        >>> _write_part_node_count(c, b)
        {'part_node_count': 'pnc'}

        >>> _write_part_node_count(c, b)
        {}

        """
        if self.implementation.get_data_shape(bounds)[1] == 1:
            # No part node count variable required
            return {}

        g = self.write_vars

        # Create the part node count flattened data
        array = self.implementation.get_array(
            self.implementation.get_data(bounds)
        )
        array = np.trim_zeros(np.ma.count(array, axis=2).flatten())
        array = self._int32(array)

        data = self.implementation.initialise_Data(array=array, copy=False)

        # ------------------------------------------------------------
        # Create a count variable to hold the part node count data and
        # properties. This is what will be written to disk.
        # ------------------------------------------------------------
        count = self.implementation.initialise_Count()
        self.implementation.set_data(count, data, copy=False)

        # Find the base of the dataset part_node_count variable name
        pnc = self.implementation.get_part_node_count(coord)
        if pnc is not None:
            ncvar = self.implementation.nc_get_variable(
                pnc, default="part_node_count"
            )
            if not self.write_vars["group"]:
                # A flat dataset has been requested, so strip off any
                # group structure from the name.
                ncvar = self._remove_group_structure(ncvar)

            # Copy part node count variable properties to the new
            # count variable
            properties = self.implementation.get_properties(pnc)
            self.implementation.set_properties(count, properties)
        else:
            ncvar = "part_node_count"

        # Find the base of the dataset part dimension name
        size = self.implementation.get_data_size(count)
        if g["part_ncdim"] is not None:
            ncdim = g["part_ncdim"]
        elif "part_ncdim" in encodings:
            ncdim = encodings["part_ncdim"]
        else:
            ncdim = self._get_part_ncdimension(coord, default="part")
            ncdim = self._name(ncdim, dimsize=size, role="part")

        if self._already_in_file(count, (ncdim,)):
            # This part node count variable has been previously
            # created, so no need to do so again.
            ncvar = g["seen"][id(count)]["ncvar"]
        else:
            ncdim_to_size = g["ncdim_to_size"]
            if ncdim not in ncdim_to_size:
                logger.info(
                    f"    Writing size {size} geometry part "
                    f"dimension: {ncdim}"
                )  # pragma: no cover

                ncdim_to_size[ncdim] = size

                # Define (and create if necessary) the group in which
                # to place this dataset dimension.
                parent_group = self._parent_group(ncdim)

                if g["group"] and "/" in ncdim:
                    # This dimension needs to go into a sub-group so
                    # replace its name with its basename (CF>=1.8)
                    ncdim = self._remove_group_structure(ncdim)

                if not g["dry_run"]:
                    # parent_group.createDimension(ncdim, size)
                    self._createDimension(parent_group, ncdim, size)

            ncvar = self._name(ncvar)

            # Create the dataset part_node_count variable
            self._write_netcdf_variable(ncvar, (ncdim,), count, None)

        g["part_ncdim"] = ncdim

        # Return encodings
        return {"part_node_count": ncvar, "part_ncdim": ncdim}

    def _write_interior_ring(self, f, coord, bounds, encodings):
        """Write an interior ring variable to the dataset.

        .. versionadded:: (cfdm) 1.8.0

        :Parameters:

            coord:

            coord_ncvar: `str`
                The dataset variable name of the parent variable

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
            # A flat dataset has been requested, so strip off any
            # group structure from the name.
            ncvar = self._remove_group_structure(ncvar)

        size = self.implementation.get_data_size(interior_ring)
        if g["part_ncdim"] is not None:
            ncdim = g["part_ncdim"]
        elif "part_ncdim" in encodings:
            ncdim = encodings["part_ncdim"]
        else:
            ncdim = self._get_part_ncdimension(coord, default="part")
            ncdim = self._name(ncdim, dimsize=size, role="part")

        if self._already_in_file(interior_ring, (ncdim,)):
            # This interior ring variable has been previously created,
            # so no need to do so again.
            ncvar = g["seen"][id(interior_ring)]["ncvar"]
        else:
            ncdim_to_size = g["ncdim_to_size"]
            if ncdim not in ncdim_to_size:
                logger.info(
                    f"    Writing size {size} geometry part "
                    f"dimension: {ncdim}"
                )  # pragma: no cover
                ncdim_to_size[ncdim] = size

                # Define (and create if necessary) the group in which
                # to place this dataset dimension.
                parent_group = self._parent_group(ncdim)

                if g["group"] and "/" in ncdim:
                    # This dimension needs to go into a sub-group so
                    # replace its name with its basename (CF>=1.8)
                    ncdim = self._remove_group_structure(ncdim)

                if not g["dry_run"]:
                    # parent_group.createDimension(ncdim, size)
                    self._createDimension(parent_group, ncdim, size)

            ncvar = self._name(ncvar)

            # Create the dataset interior ring variable
            self._write_netcdf_variable(
                ncvar,
                (ncdim,),
                interior_ring,
                None,
                construct_type=self.implementation.get_construct_type(coord),
            )

        g["part_ncdim"] = ncdim

        # Return encodings
        return {"interior_ring": ncvar, "part_ncdim": ncdim}

    def _write_scalar_coordinate(
        self, f, key, coord_1d, axis, coordinates, extra=None
    ):
        """Write a scalar coordinate and its bounds to the dataset.

        It is assumed that the input coordinate has size 1, but this
        is not checked.

        If an equal scalar coordinate has already been written to the
        dataset then the input coordinate is not written.

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
                The updated list of auxiliary coordinate dataset
                variable names.

        """
        # To avoid mutable default argument (an anti-pattern) of extra={}
        if extra is None:
            extra = {}

        g = self.write_vars

        coord_1d = self._change_reference_datetime(coord_1d)

        scalar_coord = self.implementation.squeeze(coord_1d, axes=0)

        if not self._already_in_file(scalar_coord, ()):
            ncvar = self._create_variable_name(scalar_coord, default="scalar")
            # If this scalar coordinate has bounds then create the
            # bounds dataset variable and add the 'bounds' or
            # 'climatology' (as appropriate) attribute to the
            # dictionary of extra attributes
            bounds_extra = self._write_bounds(f, scalar_coord, key, (), ncvar)

            # Create a new scalar coordinate variable
            self._write_netcdf_variable(
                ncvar,
                (),
                scalar_coord,
                self.implementation.get_data_axes(f, key),
                extra=bounds_extra,
            )

        else:
            # This scalar coordinate has already been written to the
            # dataset
            ncvar = g["seen"][id(scalar_coord)]["ncvar"]

        g["axis_to_ncscalar"][axis] = ncvar

        g["key_to_ncvar"][key] = ncvar

        coordinates.append(ncvar)

        return coordinates

    def _write_auxiliary_coordinate(self, f, key, coord, coordinates):
        """Write auxiliary coordinates and bounds to the dataset.

        If an equal auxiliary coordinate has already been written to
        the dataset then the input coordinate is not written.

        :Parameters:

            f: Field construct

            key: `str`
                The identifier of the coordinate construct,
                e.g. ``'auxiliarycoordinate1'``.

            coord: Coordinate construct

            coordinates: `list`

        :Returns:

            `list`
                The list of auxiliary coordinate dataset variable
                names updated in place.

        """
        g = self.write_vars

        ncvar = None

        # The dataset dimensions for the auxiliary coordinate variable
        ncdimensions = self._dataset_dimensions(f, key, coord)

        coord = self._change_reference_datetime(coord)

        already_in_file = self._already_in_file(coord, ncdimensions)

        create = False

        if already_in_file:
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
            create = True

        if create:
            if (
                not self.implementation.get_properties(coord)
                and self.implementation.get_data(coord, default=None) is None
            ):
                # No coordinates, but possibly bounds
                self._write_bounds(
                    f, coord, key, ncdimensions, coord_ncvar=None
                )
            else:
                ncvar = self._create_variable_name(coord, default="auxiliary")

                # TODO: move setting of bounds ncvar to here - why?

                # If this auxiliary coordinate has bounds then create
                # the bounds dataset variable and add the 'bounds',
                # 'climatology' or 'nodes' attribute (as appropriate)
                # to the dictionary of extra attributes.
                extra = self._write_bounds(f, coord, key, ncdimensions, ncvar)

                # Create a new auxiliary coordinate variable, if it has data
                if self.implementation.get_data(coord, None) is not None:
                    self._write_netcdf_variable(
                        ncvar,
                        ncdimensions,
                        coord,
                        self.implementation.get_data_axes(f, key),
                        extra=extra,
                    )

        g["key_to_ncvar"][key] = ncvar
        g["key_to_ncdims"][key] = ncdimensions

        if ncvar is not None:
            coordinates.append(ncvar)

        return coordinates

    def _write_domain_ancillary(self, f, key, anc):
        """Write a domain ancillary and its bounds to the dataset.

        If an equal domain ancillary has already been written to the
        dataset then it is not re-written.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            f: Field construct

            key: `str`
                The internal identifier of the domain ancillary object.

            anc: Domain ancillary construct

        :Returns:

            `str`
                The dataset name of the domain ancillary variable.

        """
        g = self.write_vars

        if g["post_dry_run"]:
            logger.warning(
                "At present domain ancillary constructs of appended fields "
                "may not be handled correctly by write append mode "
                "and can appear as extra fields. Set them on fields using "
                "`set_domain_ancillary` and similar methods if required."
            )

        ncdimensions = self._dataset_dimensions(f, key, anc)

        create = not self._already_in_file(anc, ncdimensions, ignore_type=True)

        if not create:
            ncvar = g["seen"][id(anc)]["ncvar"]
        else:
            # See if we can set the default dataset variable name to
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

            ncvar = self._create_variable_name(anc, default=default)

            # If this domain ancillary has bounds then create the
            # bounds dataset variable
            self._write_bounds(f, anc, key, ncdimensions, ncvar)

            # Create a new domain ancillary variable
            self._write_netcdf_variable(
                ncvar,
                ncdimensions,
                anc,
                self.implementation.get_data_axes(f, key),
            )

        g["key_to_ncvar"][key] = ncvar
        g["key_to_ncdims"][key] = ncdimensions

        return ncvar

    def _write_field_ancillary(
        self,
        f,
        key,
        anc,
    ):
        """Write a field ancillary to the dataset.

        If an equal field ancillary has already been written to the
        dataset then it is not re-written.

        :Parameters:

            f : `Field`

            key : `str`

            anc : `FieldAncillary`

        :Returns:

            `str`
                The dataset variable name of the field ancillary
                object. If no ancillary variable was written then an
                empty string is returned.

        **Examples**

        >>> ncvar = _write_field_ancillary(f, 'fieldancillary2', anc)

        """
        g = self.write_vars

        ncdimensions = self._dataset_dimensions(f, key, anc)

        create = not self._already_in_file(anc, ncdimensions)

        if not create:
            ncvar = g["seen"][id(anc)]["ncvar"]
        else:
            ncvar = self._create_variable_name(anc, default="ancillary_data")

            # Create a new field ancillary variable
            self._write_netcdf_variable(
                ncvar,
                ncdimensions,
                anc,
                self.implementation.get_data_axes(f, key),
            )

        g["key_to_ncvar"][key] = ncvar
        g["key_to_ncdims"][key] = ncdimensions

        return ncvar

    def _write_cell_measure(self, f, key, cell_measure):
        """Write a cell measure construct to the dataset.

        If an identical construct has already in the dataset then the
        cell measure will not be written.

        :Parameters:

            f: `Field` or `Domain`
                The field containing the cell measure.

            key: `str`
                The identifier of the cell measure
                (e.g. ``'cellmeasure0'``).

            cell_measure: `CellMeasure`

        :Returns:

            `str`
                The 'measure: ncvar'.

        """
        g = self.write_vars

        measure = self.implementation.get_measure(cell_measure)
        if measure is None:
            raise ValueError(
                "Can't create a CF cell measure variable "
                "without a 'measure' property"
            )

        ncdimensions = self._dataset_dimensions(f, key, cell_measure)

        if self._already_in_file(cell_measure, ncdimensions):
            # Use existing cell measure variable
            ncvar = g["seen"][id(cell_measure)]["ncvar"]
        elif self.implementation.nc_get_external(cell_measure):
            # The cell measure is external
            ncvar = self.implementation.nc_get_variable(
                cell_measure, default=None
            )
            if ncvar is None:
                raise ValueError(
                    "Can't create an external CF cell measure "
                    "variable without a dataset variable name"
                )

            # Add ncvar to the global external_variables attribute
            self._set_external_variables(ncvar)

            if (
                g["external_dataset"] is not None
                and self.implementation.get_data(cell_measure, None)
                is not None
            ):
                # Create a new field to write out to the external
                # dataset
                self._create_external(
                    field=f,
                    construct_id=key,
                    ncvar=ncvar,
                    ncdimensions=ncdimensions,
                )
        else:
            ncvar = self._create_variable_name(
                cell_measure, default="cell_measure"
            )

            # Create a new (internal) cell measure variable
            self._write_netcdf_variable(
                ncvar,
                ncdimensions,
                cell_measure,
                self.implementation.get_data_axes(f, key),
            )

        g["key_to_ncvar"][key] = ncvar
        g["key_to_ncdims"][key] = ncdimensions

        # Update the field's cell_measures list
        return f"{measure}: {ncvar}"

    def _set_external_variables(self, ncvar):
        """Add ncvar to the global external_variables attribute."""
        g = self.write_vars

        external_variables = g["external_variables"]

        if not external_variables:
            g["global_attributes"].add("external_variables")

        if ncvar not in external_variables:
            external_variables.add(ncvar)
            if not g["dry_run"] and not g["post_dry_run"]:
                self._set_attributes(
                    {
                        "external_variables": " ".join(
                            sorted(external_variables)
                        )
                    },
                    group=g["dataset"],
                )

    def _create_external(
        self, field=None, construct_id=None, ncvar=None, ncdimensions=None
    ):
        """Creates a new field to flag to write to an external dataset.

        .. versionadded:: (cfdm) 1.7.0

        """
        g = self.write_vars

        if ncdimensions is None:
            return

        # Still here?
        external = self.implementation.convert(
            field=field, construct_id=construct_id
        )

        # Set the correct dataset variable and dimension names
        self.implementation.nc_set_variable(external, ncvar)

        external_domain_axes = self.implementation.get_domain_axes(external)
        for ncdim, axis in zip(
            ncdimensions, self.implementation.get_field_data_axes(external)
        ):
            external_domain_axis = external_domain_axes[axis]
            self.implementation.nc_set_dimension(external_domain_axis, ncdim)

        # Don't write fields that are already in the list for being
        # written
        new = True
        for f in g["external_fields"]:
            if self.implementation.equal_components(external, f):
                new = False
                break

        if new:
            g["external_fields"].append(external)

        return external

    def _createVariable(self, **kwargs):
        """Create a variable in the dataset.

        .. versionadded:: (cfdm) 1.7.0

        """
        g = self.write_vars

        ncvar = kwargs["varname"]

        match g["backend"]:
            case "netCDF4":
                netcdf4_kwargs = kwargs
                if "dimensions" not in kwargs:
                    netcdf4_kwargs["dimensions"] = ()

                contiguous = kwargs.get("contiguous")

                NETCDF4 = g["dataset"].data_model.startswith("NETCDF4")
                if NETCDF4 and contiguous:
                    # NETCDF4 contiguous variables can't be compressed
                    kwargs["compression"] = None
                    kwargs["complevel"] = 0

                    # NETCDF4 contiguous variables can't span unlimited
                    # dimensions
                    unlimited_dimensions = g[
                        "unlimited_dimensions"
                    ].intersection(kwargs.get("dimensions", ()))
                    if unlimited_dimensions:
                        data_model = g["dataset"].data_model
                        raise ValueError(
                            f"Can't create variable {ncvar!r} in "
                            f"{data_model} dataset: "
                            f"In {data_model} it is not allowed to write "
                            "contiguous (as opposed to chunked) data "
                            "that spans one or more unlimited dimensions: "
                            f"{unlimited_dimensions}"
                        )

                if contiguous:
                    netcdf4_kwargs.pop("fletcher32", None)

                # Remove Zarr-specific kwargs
                netcdf4_kwargs.pop("shape", None)
                netcdf4_kwargs.pop("shards", None)

                variable = g["dataset"].createVariable(**netcdf4_kwargs)

            case "zarr":
                shape = kwargs.get("shape", ())
                chunks = kwargs.get("chunksizes", shape)
                shards = kwargs.get("shards")

                if chunks is None:
                    # One chunk for the entire array
                    chunks = shape

                if shards is not None:
                    # Create the shard shape in the format expected by
                    # `zarr.create_array`. 'shards' is currently
                    # defined by how many *chunks* along each
                    # dimension are in each shard, but `zarr` requires
                    # shards defined by how many *array elements*
                    # along each dimension are in each shard.
                    if chunks == shape:
                        # One chunk
                        #
                        # It doesn't matter what 'shards' is, because
                        # the data only has one chunk.
                        shards = None
                    else:
                        ndim = len(chunks)
                        if isinstance(shards, Integral):
                            # Make a conservative estimate of how many
                            # whole chunks along each dimension are in
                            # a shard. This may result in fewer than
                            # 'shards' chunks in each shard, but is
                            # guaranteed to give us a shard shape of
                            # less than the data shape, which is a
                            # `zarr` requirement.
                            n = int(shards ** (1 / ndim))
                            shards = (n,) * ndim

                        if prod(shards) > 1:
                            # More than one chunk per shard.
                            #
                            # E.g. shards=(10, 11, 12) and chunks=(10,
                            #      20, 30) => shards=(100, 220, 360)
                            shards = [c * n for c, n in zip(chunks, shards)]
                        else:
                            # One chunk per shard.
                            #
                            # E.g. shards=(1, 1, 1) => shards=None
                            shards = None

                dtype = kwargs["datatype"]
                if dtype == "S1":
                    dtype = str

                zarr_kwargs = {
                    "name": ncvar,
                    "shape": shape,
                    "dtype": dtype,
                    "chunks": chunks,
                    "shards": shards,
                    "fill_value": kwargs.get("fill_value"),
                    "dimension_names": kwargs.get("dimensions", ()),
                    "storage_options": g.get("storage_options"),
                    "overwrite": g["overwrite"],
                }

                variable = g["dataset"].create_array(**zarr_kwargs)

        g["nc"][ncvar] = variable

    def _write_grid_mapping(self, f, ref, multiple_grid_mappings):
        """Write a grid mapping georeference to the dataset.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            f: `Field` or `Domain`

            ref: `CoordinateReference`
                The grid mapping coordinate reference to write to the
                dataset.

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
            ncvar = self._create_variable_name(ref, default=default)

            logger.info(
                f"    Writing {ref!r} to variable: {ncvar}"
            )  # pragma: no cover

            kwargs = {
                "varname": ncvar,
                "datatype": "S1",
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
                    "Can't create CF grid mapping variable: "
                    f"{common.pop()!r} is defined as both a coordinate "
                    "conversion and a datum parameter."
                )

            parameters.update(cc_parameters)

            for term, value in list(parameters.items()):
                if value is None:
                    del parameters[term]
                    continue

                if np.size(value) == 1:
                    value = np.array(value).item()
                else:
                    value = np.array(value).tolist()

                parameters[term] = value

            if not g["dry_run"]:
                self._set_attributes(parameters, ncvar)

            # Update the 'seen' dictionary
            g["seen"][id(ref)] = {
                "variable": ref,
                "ncvar": ncvar,
                # Grid mappings variables are scalar
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
        domain_axes,
        omit=(),
        extra=None,
        fill=False,
        data_variable=False,
        domain_variable=False,
        construct_type=None,
        chunking=None,
    ):
        """Creates a new netCDF variable for a construct.

        The new netCDF variable is created from *cfvar* with name
        *ncvar* and dimensions *ncdimensions*. It's properties
        are given by cfvar.properties(), less any given by the *omit*
        argument. If a new string-length netCDF dimension is required
        then it will also be created.

        The ``seen`` dictionary is updated to account for the new
        variable.

        :Parameters:

            ncvar: `str`
                The netCDF name of the variable.

            ncdimensions: `tuple`
                The netCDF dimension names of the variable

            cfvar: `Variable` or `Data`
                The construct to write to the dataset.

            domain_axes: `None`, or `tuple` of `str`
                The domain axis construct identifiers for *cfvar*.

                .. versionadded:: (cfdm) 1.10.1.0

            omit: sequence of `str`, optional

            extra: `dict`, optional

            domain_variable: `bool`, optional
                True if cf-netCDF domain variable is being written.

                .. versionadded:: (cfdm) 1.9.0.0

            construct_type: `str`, optional
                The construct type, or its parent if it is not a
                construct.

                .. versionadded:: (cfdm) 1.10.1.0

            chunking: sequence, optional
                Set `_createVariable` 'contiguous', 'chunksizes', and
                'shards' parameters (in that order). If `None` (the
                default), then these parameters are inferred from the
                data.

                .. versionadded:: (cfdm) 1.12.0.0

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
            data = self.implementation.get_data(cfvar, None)
            original_ncdimensions = ncdimensions

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

        logger.info(
            f"    Writing {cfvar!r} to variable: {ncvar}"
        )  # pragma: no cover

        # Set 'construct_type'
        if not construct_type:
            construct_type = self.implementation.get_construct_type(cfvar)

        # Do this after the dry_run return else may attempt to transform
        # the arrays with string dtype on an append-mode read iteration (bad).
        datatype = None
        if not domain_variable:
            datatype = self._datatype(cfvar)
            data, ncdimensions = self._transform_strings(
                data,
                ncdimensions,
            )

        # Whether or not to write the data
        omit_data = construct_type in g["omit_data"]

        # ------------------------------------------------------------
        # Find the fill value - the value that the variable's data get
        # filled before any data is written. if the fill value is
        # False then the variable is not pre-filled.
        # ------------------------------------------------------------
        match g["backend"]:
            case "netCDF4":
                if (
                    omit_data or fill or g["post_dry_run"]
                ):  # or append mode's appending iteration
                    fill_value = self.implementation.get_property(
                        cfvar, "_FillValue", None
                    )
                else:
                    fill_value = None

            case "zarr":
                # Set the `zarr` fill_value to the missing value of
                # 'cfvar', defaulting to the netCDF default fill value
                # if no missing value is available
                fill_value = self._missing_value(cfvar, datatype)

        if data_variable:
            lsd = g["least_significant_digit"]
        else:
            lsd = None

        # Set the dataset chunk strategy
        if chunking:
            contiguous, chunksizes, shards = chunking
        else:
            contiguous, chunksizes, shards = self._chunking_parameters(
                data, ncdimensions
            )

        logger.debug(
            f"      chunksizes: {chunksizes!r}, "
            f"contiguous: {contiguous!r}, "
            f"shards: {shards!r}"
        )  # pragma: no cover

        # ------------------------------------------------------------
        # Check that each dimension of the dataset variable is in the
        # same group or a parent group (CF>=1.8)
        # ------------------------------------------------------------
        if g["group"]:
            groups = self._groups(ncvar)
            for ncdim in ncdimensions:
                ncdim_groups = self._groups(ncdim)
                if not groups.startswith(ncdim_groups):
                    raise ValueError(
                        f"Can't create variable {ncvar!r} from "
                        f"{cfvar!r} with dimension {ncdim!r} that is "
                        "not in the same group nor in a parent group."
                    )

        # ------------------------------------------------------------
        # Create a new dataset variable
        # ------------------------------------------------------------
        kwargs = {
            "varname": ncvar,
            "datatype": datatype,
            "endian": g["endian"],
            "contiguous": contiguous,
            "chunksizes": chunksizes,
            "shards": shards,
            "least_significant_digit": lsd,
            "fill_value": fill_value,
            "chunk_cache": g["chunk_cache"],
        }

        # ------------------------------------------------------------
        # Replace dataset dimension names with their basenames
        # (CF>=1.8)
        # ------------------------------------------------------------
        if g["backend"] == "zarr":
            # ... but not for Zarr. This is because the Zarr data
            # model doesn't have the concept of dimensions belonging
            # to a group (unlike netCDF), so by keeping the group
            # structure in the dimension names we can know which group
            # they belong to.
            kwargs["dimensions"] = ncdimensions
        else:
            ncdimensions_basename = [
                self._remove_group_structure(ncdim) for ncdim in ncdimensions
            ]
            kwargs["dimensions"] = ncdimensions_basename

        if data is not None:
            compressed = self._compressed_data(ncdimensions)
            if compressed:
                # Write data in its compressed form
                shape = data.source().source().shape
            else:
                shape = data.shape

            kwargs["shape"] = shape

        # ------------------------------------------------------------
        # Create a quantization container variable, add any extra
        # quantization attributes, and if required instruct
        # `_createVariable`to perform the quantization.
        # ------------------------------------------------------------
        q = self.implementation.get_quantize_on_write(cfvar, None)
        if q is not None:
            quantize_on_write = True
        else:
            q = self.implementation.get_quantization(cfvar, None)
            quantize_on_write = False

        if q is not None:
            # There are some quantization metadata - either

            # CF quantization algorithm name (e.g. 'bitgroom')
            algorithm = self.implementation.get_parameter(q, "algorithm", None)

            # Get the CF quantization parameter name and value
            # (e.g. 'quantization_nsd' and 6)
            cf_parameter = CF_QUANTIZATION_PARAMETERS.get(algorithm)
            cf_ns = self.implementation.del_parameter(q, cf_parameter, None)

            # Remove the NetCDF-C library quantization attribute
            # (e.g. '_QuantizeBitRoundNumberOfSignificantBits')
            netcdf_parameter = NETCDF_QUANTIZATION_PARAMETERS.get(algorithm)
            netcdf_ns = self.implementation.del_parameter(
                q, netcdf_parameter, None
            )

            # Create a quantization container variable in the dataset,
            # if it doesn't already exist (and after having removed
            # any per-variable quantization parameters, such as
            # "quantization_nsd").
            if quantize_on_write:
                if g["backend"] == "zarr":
                    raise NotImplementedError(
                        f"Can't yet quantize-on-write {cfvar!r} to a Zarr "
                        "dataset"
                    )

                # Set "implemention" to this version of the netCDF-C
                # library
                import netCDF4

                self.implementation.set_parameter(
                    q,
                    "implementation",
                    f"libnetcdf version {netCDF4.__netcdf4libversion__}",
                    copy=False,
                )

            q_ncvar = self._write_quantization_container(q)

            # Update the variable's extra attributes
            extra = extra.copy()
            extra["quantization"] = q_ncvar
            if cf_ns is not None:
                extra[cf_parameter] = cf_ns

            if not quantize_on_write:
                # We're not performing any quantization, so also set
                # the netCDF-C-defined attribute.
                if netcdf_ns is not None:
                    extra[netcdf_parameter] = netcdf_ns
            else:
                # ----------------------------------------------------
                # We are going to perform quantization
                # ----------------------------------------------------
                quantize_mode = NETCDF_QUANTIZE_MODES.get(algorithm)

                if algorithm == "digitround":
                    raise ValueError(
                        f"Can't quantize {cfvar!r} with algorithm "
                        f"{algorithm!r}, because it is not yet available "
                        "from the netCDF-C library"
                    )

                if quantize_mode is None:
                    raise ValueError(
                        f"Can't quantize {cfvar!r} with non-standardised "
                        f"algorithm {algorithm!r}. Valid algorithms are "
                        f"{tuple(NETCDF_QUANTIZE_MODES)}"
                    )

                if g["fmt"] not in NETCDF4_FMTS:
                    raise ValueError(
                        f"Can't quantize {cfvar!r} into a {g['fmt']} "
                        "format dataset. Quantization is only possible when "
                        f"writing to one of the {NETCDF4_FMTS} formats."
                    )

                if not datatype.startswith("f"):
                    raise ValueError(
                        f"Can't quantize {cfvar!r} with data type "
                        f"{datatype!r}. Only floating point data can be "
                        "quantized."
                    )

                if cf_ns is None:
                    raise ValueError(
                        f"Can't quantize {cfvar!r} because the "
                        f"{cf_parameter!r} parameter has not been defined"
                    )

                u = CF_QUANTIZATION_PARAMETER_LIMITS[cf_parameter][datatype]
                if not 1 <= cf_ns <= u:
                    raise ValueError(
                        f"Can't quantize {cfvar!r} with a {cf_parameter!r} "
                        f"parameter value of {cf_ns}. {cf_parameter!r} must "
                        f"lie in the range [1, {u}]"
                    )

                # Update the kwargs for `_createVariable` to perform
                # the quantization during the write process
                kwargs["quantize_mode"] = quantize_mode
                kwargs["significant_digits"] = cf_ns

        # ------------------------------------------------------------
        # For aggregation variables, create a dictionary containing
        # the fragment array variables' data.
        #
        # E.g. {'map': <Data(2, 1): [[5, 8]]>,
        #       'location': <Data(1, 1): [[data/file.nc.nc]]>,
        #       'variable': <Data(1, 1): [[q]]>}
        # ------------------------------------------------------------
        cfa = None
        if self._cfa_write_status(ncvar, cfvar, construct_type, domain_axes):
            try:
                cfa = self._cfa_fragment_array_variables(data, cfvar)
            except AggregationError:
                if g["cfa"].get("strict", True):
                    # Raise the exception in 'strict' mode
                    if g["mode"] == "w":
                        self.dataset_remove()

                    raise

                # In 'non-strict' mode, write the data to a normal
                # non-aggregation variable.
                g["cfa_write_status"][ncvar] = False
            else:
                # We're going to create a scalar aggregation variable,
                # so override dimensions and dataset chunking strategy
                # keyword arguments. This is necessary because the
                # dimensions and dataset chunking strategy will
                # otherwise reflect the aggregated data in memory,
                # rather than the scalar variable in the dataset.
                kwargs["contiguous"] = True
                kwargs["chunksizes"] = None
                kwargs["dimensions"] = ()
                kwargs["shape"] = ()
                kwargs["shards"] = None

        # Add compression parameters (but not for scalars or vlen
        # strings).
        #
        # From the NUG:
        #
        #   Compression is permitted but may not be effective for VLEN
        #   data, because the compression is applied to structures
        #   containing lengths and pointers to the data, rather than
        #   the actual data.
        if kwargs["dimensions"] and kwargs["datatype"] != str:
            kwargs.update(g["netcdf_compression"])

        # Note: this is a trivial assignment in standalone cfdm, but
        # allows for non-trivial customisation applied by subclasses.
        kwargs = self._customise_createVariable(
            cfvar, construct_type, domain_axes, kwargs
        )

        logger.info(
            f"      dimensions: ({', '.join(ncdimensions)})"
        )  # pragma: no cover

        try:
            self._createVariable(**kwargs)
        except RuntimeError as error:
            error = str(error)
            message = (
                f"Can't create variable in {g['netcdf'].data_model} dataset "
                f"from {cfvar!r}: {error}. "
                f"_createVariable arguments: {kwargs}"
            )
            if error == (
                "NetCDF: Not a valid data type or _FillValue type mismatch"
            ):
                raise ValueError(
                    f"Can't write {cfvar.data.dtype.name} data from {cfvar!r} "
                    f"to a {g['netcdf'].data_model} dataset. "
                    "Consider using a netCDF4 format, or use the 'datatype' "
                    "parameter, or change the datatype before writing."
                )
            elif error == "NetCDF: NC_UNLIMITED in the wrong index":
                raise RuntimeError(
                    f"{message}. In a {g['netcdf'].data_model} dataset the "
                    "unlimited dimension must be the first (leftmost) "
                    "dimension of the variable. "
                    "Consider using a netCDF4 format."
                )
            else:
                raise RuntimeError(message)

        # ------------------------------------------------------------
        # Write attributes to the dataset variable
        # ------------------------------------------------------------
        attributes = self._write_variable_attributes(
            cfvar, ncvar, extra=extra, omit=omit
        )

        # ------------------------------------------------------------
        # Write data to the dataset variable
        #
        # Note that we don't need to worry about scale_factor and
        # add_offset, since if a data array is *not* a numpy array,
        # then it will have its own scale_factor and add_offset
        # parameters which will be applied when the array is realised,
        # and the python netCDF4 package will deal with the case when
        # scale_factor or add_offset are set as properties on the
        # variable.
        # ------------------------------------------------------------
        if data is not None and not omit_data:
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

            self._write_data(
                data,
                cfvar,
                ncvar,
                ncdimensions,
                domain_axes,
                unset_values=unset_values,
                compressed=self._compressed_data(ncdimensions),
                attributes=attributes,
                construct_type=construct_type,
                cfa=cfa,
            )

    def _customise_createVariable(
        self, cfvar, construct_type, domain_axes, kwargs
    ):
        """Customises `_createVariable` keywords.

        The keyword arguments may be changed in subclasses which
        override this method.

        .. versionadded:: (cfdm) 1.7.6

        :Parameters:

            cfvar: cfdm instance that contains data

            construct_type: `str`
                The construct type of the *cfvar*, or its parent if
                *cfvar* is not a construct.

                .. versionadded:: (cfdm) 1.10.1.0

            domain_axes: `None`, or `tuple` of `str`
                The domain axis construct identifiers for *cfvar*.

                .. versionadded:: (cfdm) 1.10.1.0

            kwargs: `dict`

        :Returns:

            `dict`
                Dictionary of keyword arguments to be passed to
                `_createVariable`.

        """
        # This method is trivial but the intention is that subclasses
        # may override it to perform any desired customisation.
        return kwargs

    def _transform_strings(self, data, ncdimensions):
        """Transform metadata construct arrays with string data type.

        .. versionadded:: (cfdm) 1.7.3

        :Parameters:

            data: `Data` or `None`

            ncdimensions: `tuple`

        :Returns:

            `Data`, `tuple`

        """
        datatype = self._datatype(data)

        if data is not None and datatype == "S1":
            # --------------------------------------------------------
            # Convert a string data type numpy array into a character
            # data type ('S1') numpy array with an extra trailing
            # dimension. Note that for NETCDF4 output files, datatype
            # is str, so this conversion does not happen.
            # --------------------------------------------------------
            array = self.implementation.get_array(data)
            array = self._numpy_compressed(array)

            strlen = len(max(array, key=len))
            del array

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
        domain_axes=None,
        unset_values=(),
        compressed=False,
        attributes=None,
        construct_type=None,
        cfa=None,
    ):
        """Write a data array to the dataset.

        :Parameters:

            data: `Data` instance

            cfvar: cfdm instance

            ncvar: `str`

            ncdimensions: `tuple` of `str`

            domain_axes: `None`, or `tuple` of `str`
                The domain axis construct identidifiers for *cfvar*.

                .. versionadded:: (cfdm) 1.10.1.0

            unset_values: sequence of numbers

            attributes: `dict`, optional
                The dataset attributes for the constructs that have
                been written to the dataset.

            construct_type: `str`
                The construct type of the *cfvar*, or its parent if
                *cfvar* is not a construct.

                .. versionadded:: (cfdm) 1.10.1.0

            cfa: `dict`, optional
                For aggregation variables, a dictionary containing the
                fragment array variables' data.

                .. versionadded:: (cfdm) 1.12.0.0

        :Returns:

            `None`

        """
        g = self.write_vars

        if cfa:
            # --------------------------------------------------------
            # Write the data as an aggregation variable
            # --------------------------------------------------------
            self._cfa_create_data(cfa, ncvar, ncdimensions, data, cfvar)
            return

        # ------------------------------------------------------------
        # Still here? The write a normal (non-aggregation) variable
        # ------------------------------------------------------------
        import dask.array as da

        zarr = g["backend"] == "zarr"

        if compressed:
            # Write data in its compressed form
            data = data.source().source()

        # Get the dask array
        dx = da.asanyarray(data)

        # Convert the data type
        new_dtype = g["datatype"].get(dx.dtype)
        if new_dtype is not None:
            dx = dx.astype(new_dtype)

        # VLEN variables can not be assigned to by masked arrays
        # (https://github.com/Unidata/netcdf4-python/pull/465), so
        # fill missing data in string (as opposed to char) data types.
        if g["fmt"] == "NETCDF4" and dx.dtype.kind in "SU":
            dx = dx.map_blocks(
                self._filled_string_array,
                fill_value="",
                meta=np.array((), dx.dtype),
            )

        # Initialise the dataset lock for the data writing from Dask
        lock = None

        # Rechunk the Dask array to shards, if applicable.
        if zarr:
            # When a Zarr variable is sharded, the Dask array must be
            # rechunked to the shards because "when writing data, a
            # full shard must be written in one go for optimal
            # performance and to avoid concurrency issues."
            # https://zarr.readthedocs.io/en/stable/user-guide/arrays.html#sharding
            shards = g["nc"][ncvar].shards
            if shards is not None:
                dx = dx.rechunk(shards)
                # This rechunking has aligned Dask chunk boundaries
                # with Zarr chunk boundaries, so we don't need to lock
                # the write.
                lock = False

        # Check for out-of-range values
        if g["warn_valid"]:
            if construct_type:
                var = cfvar
            else:
                var = None

            dx = dx.map_blocks(
                self._check_valid,
                cfvar=var,
                attributes=attributes,
                meta=np.array((), dx.dtype),
            )

        if zarr:
            # `zarr` can't write a masked array to a variable, so we
            # have to manually replace missing data with the fill
            # value.
            dx = dx.map_blocks(
                self._filled_array,
                meta=np.array((), dx.dtype),
                fill_value=g["nc"][ncvar].fill_value,
            )

        if lock is None:
            # We need to define the dataset lock for data writing from
            # Dask
            from cfdm.data.locks import netcdf_lock as lock

        da.store(
            dx, g["nc"][ncvar], compute=True, return_stored=False, lock=lock
        )

    def _filled_array(self, array, fill_value):
        """Replace masked values with a fill value.

        .. versionadded:: (cfdm) NEXTVERSION

        :Parameters:

            array: `numpy.ndarray`
                The arry to be filled.

            fill_value:
                The fill value.

        :Returns:

            `numpy.ndarray`

        """
        if np.ma.isMA(array):
            return array.filled(fill_value)

        return array

    def _check_valid(self, array, cfvar=None, attributes=None):
        """Checks for array values outside of the valid range.

        Specifically, checks array for out-of-range values, as
        defined by the valid_[min|max|range] attributes.

        .. versionadded:: (cfdm) 1.8.3

        :Parameters:

            array: `numpy.ndarray`
                The array to be checked.

            cfvar: construct
                The CF construct containing the array.

            attributes: `dict`
                The variable's CF properties.

        :Returns:

            `numpy.ndarray`
                The input array, unchanged.

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
                    self.write_vars["dataset_name"],
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
                    self.write_vars["dataset_name"],
                    "greater",
                    "maximum",
                    prop,
                    valid_max,
                )
            )
            out += 1

        return array

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
        """Write a field or domain construct to the dataset.

        All of the metadata constructs are also written.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            f: `Field` or `Domain`

            add_to_seen: bool, optional

            allow_data_insert_dimension: `bool`, optional

        :Returns:

            `None`

        """
        import re

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

        # Mapping of domain axis identifiers to dataset dimension
        # names. This gets reset for each new field/domain that is
        # written to the dataset.
        #
        # For example: {'domainaxis1': 'lon'}
        g["axis_to_ncdim"] = {}

        # Mapping of domain axis identifiers to dataset scalar
        # coordinate variable names. This gets reset for each new
        # field/domain that is written to the dataset.
        #
        # For example: {'domainaxis0': 'time'}
        g["axis_to_ncscalar"] = {}

        # Mapping of construct internal identifiers to dataset
        # variable names. This gets reset for each new field/domain
        # that is written to the dataset.
        #
        # For example: {'dimensioncoordinate1': 'longitude'}
        g["key_to_ncvar"] = {}

        # Mapping of construct internal identifiers to their dataset
        # dimensions. This gets reset for each new field/domain that
        # is written to the dataset.
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

        # Initialise the list of the field/domain's auxiliary/scalar
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

        # Check if the field or domain has a domain topology construct
        # (CF>=1.11)
        ugrid = self.implementation.has_domain_topology(f)
        if ugrid:
            raise NotImplementedError(
                "Can't yet write UGRID datasets. "
                "This feature is coming soon ..."
            )

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
                self.implementation.set_properties(
                    field_coordinates[key],
                    {"computed_standard_name": csn},
                    copy=False,
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
                    # the dimension coordinate to the dataset as a
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
                        # dimension coordinate to the dataset as a
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
                        # dimension coordinate to the dataset as a
                        # scalar coordinate variable.
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

                # If the data array (now) spans this domain axis then
                # create a dataset dimension for it
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

                            for (
                                key0,
                                (construct0, index0),
                            ) in spanning_constructs.items():
                                for (
                                    key1,
                                    (construct1, index1),
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

                            if (
                                matched_construct
                                and self._dimension_in_subgroup(f, ncdim1)
                            ):
                                use_existing_dimension = True
                                break

                    if use_existing_dimension:
                        g["axis_to_ncdim"][axis] = ncdim1
                    elif (
                        g["compression_type"] == "ragged contiguous"
                        and len(data_axes) == 2
                        and axis == data_axes[1]
                    ):
                        # Do not create a dataset dimension for the
                        # element dimension
                        g["axis_to_ncdim"][axis] = "ragged_contiguous_element"
                    elif (
                        g["compression_type"] == "ragged indexed"
                        and len(data_axes) == 2
                        and axis == data_axes[1]
                    ):
                        # Do not create a dataset dimension for the
                        # element dimension
                        g["axis_to_ncdim"][axis] = "ragged_indexed_element"
                    elif (
                        g["compression_type"] == "ragged indexed contiguous"
                        and len(data_axes) == 3
                        and axis == data_axes[1]
                    ):
                        # Do not create a dataset dimension for the
                        # element dimension
                        g["axis_to_ncdim"][
                            axis
                        ] = "ragged_indexed_contiguous_element1"
                    elif (
                        g["compression_type"] == "ragged indexed contiguous"
                        and len(data_axes) == 3
                        and axis == data_axes[2]
                    ):
                        # Do not create a dataset dimension for the
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
                            # A flat dataset has been requested, so
                            # strip off any group structure from the
                            # name.
                            ncdim = self._remove_group_structure(ncdim)

                        ncdim = self._name(ncdim)

                        unlimited = self._unlimited(f, axis)
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
                # Write the list variable to the dataset, making a
                # note of the dataset sample dimension.
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
                # Write the count variable to the dataset, making a
                # note of the dataset sample dimension.
                # ----------------------------------------------------
                count = self.implementation.get_count(f)
                sample_ncdim = self._write_count_variable(
                    f, count, ncdim=data_ncdimensions[0], create_ncdim=False
                )

            elif compression_type == "ragged indexed":
                # ----------------------------------------------------
                # Compression by indexed ragged array
                #
                # Write the index variable to the dataset, making a
                # note of the dataset sample dimension.
                # ----------------------------------------------------
                index = self.implementation.get_index(f)
                index_ncdim = self.implementation.nc_get_dimension(
                    index, default="sample"
                )
                if not g["group"]:
                    # A flat dataset has been requested, so strip off
                    # any group structure from the name.
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
                # Write the index variable to the dataset, making a
                # note of the dataset sample dimension.
                # ----------------------------------------------------
                count = self.implementation.get_count(f)
                count_ncdim = self.implementation.nc_get_dimension(
                    count, default="feature"
                )

                if not g["group"]:
                    # A flat dataset has been requested, so strip off
                    # any group structure from the name.
                    count_ncdim = self._remove_group_structure(count_ncdim)

                sample_ncdim = self._write_count_variable(
                    f, count, ncdim=count_ncdim, create_ncdim=True
                )

                if not g["group"]:
                    # A flat dataset has been requested, so strip off any
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

        # Initialise the list of 'coordinates' attribute variable
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
        # Create dataset variables from domain ancillaries
        # ------------------------------------------------------------
        for key, anc in sorted(
            self.implementation.get_domain_ancillaries(f).items()
        ):
            self._write_domain_ancillary(f, key, anc)

        # ------------------------------------------------------------
        # Create dataset variables from cell measures
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
        # Create formula_terms dataset attributes from vertical
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

                    ncvar = self._write_scalar_data(f, value, ncvar=term)

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

                    # Get the dataset variable name for the domain
                    # ancillary and add it to the formula_terms
                    # attribute
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
                        self._set_attributes(
                            {"formula_terms": formula_terms}, ncvar
                        )
                    except KeyError:
                        pass  # TODO convert to 'raise' via fixes upstream

                logger.info(
                    "    Writing formula_terms attribute to variable "
                    f"{ncvar}: {formula_terms!r}"
                )  # pragma: no cover

                # Add the formula_terms attribute to the parent
                # coordinate bounds variable
                bounds_ncvar = g["bounds"].get(ncvar)
                if bounds_ncvar is not None:
                    bounds_formula_terms = " ".join(bounds_formula_terms)
                    if not g["dry_run"] and not g["post_dry_run"]:
                        try:
                            self._set_attributes(
                                {"formula_terms": bounds_formula_terms},
                                bounds_ncvar,
                            )
                        except KeyError:
                            pass  # TODO convert to 'raise' via fixes upstream

                    logger.info(
                        "    Writing formula_terms to bounds variable "
                        f"{bounds_ncvar}: {bounds_formula_terms!r}"
                    )  # pragma: no cover

            # Deal with a vertical datum
            if owning_coord_key is not None:
                self._create_vertical_datum(ref, owning_coord_key)

        # ------------------------------------------------------------
        # Create dataset grid mapping variables
        # ------------------------------------------------------------
        multiple_grid_mappings = len(g["grid_mapping_refs"]) > 1

        grid_mapping = [
            self._write_grid_mapping(f, ref, multiple_grid_mappings)
            for ref in g["grid_mapping_refs"]
        ]

        # ------------------------------------------------------------
        # Field ancillary variables
        #
        # Create the 'ancillary_variables' CF attribute and create the
        # referenced dataset ancillary variables
        # ------------------------------------------------------------
        if field:
            ancillary_variables = [
                self._write_field_ancillary(f, key, anc)
                for key, anc in self.implementation.get_field_ancillaries(
                    f
                ).items()
            ]

        # ------------------------------------------------------------
        # Create the data/domain dataset variable
        # ------------------------------------------------------------
        if field:
            default = "data"
        else:
            default = "domain"

        ncvar = self._create_variable_name(f, default=default)

        ncdimensions = data_ncdimensions

        extra = {}

        # Cell measures
        if cell_measures:
            cell_measures = " ".join(cell_measures)
            logger.debug(
                "    Writing cell_measures attribute to "
                f"variable {ncvar}: {cell_measures!r}"
            )  # pragma: no cover

            extra["cell_measures"] = cell_measures

        # Auxiliary/scalar coordinates
        if coordinates:
            coordinates = " ".join(coordinates)
            logger.info(
                "    Writing coordinates attribute to "
                f"variable {ncvar}: {coordinates!r}"
            )  # pragma: no cover

            extra["coordinates"] = coordinates

        # Grid mapping
        if grid_mapping:
            grid_mapping = " ".join(grid_mapping)
            logger.info(
                "    Writing grid_mapping attribute to "
                f"variable {ncvar}: {grid_mapping!r}"
            )  # pragma: no cover

            extra["grid_mapping"] = grid_mapping

        # Ancillary variables
        if field and ancillary_variables:
            ancillary_variables = " ".join(ancillary_variables)
            ancillary_variables = re.sub(r"\s+", " ", ancillary_variables)
            logger.info(
                "    Writing ancillary_variables attribute to "
                f"variable {ncvar}: {ancillary_variables!r}"
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
                            f"Can't write {org_f!r}: Unknown cell method "
                            f"property: {cm.properties()!r}"
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
                    f"variable {ncvar}: {cell_methods}"
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
        # Create a new data/domain dataset variable
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
            # Include the dimensions attribute on domain
            # variables. CF-1.9
            extra["dimensions"] = " ".join(sorted(ncdimensions))

        # Note that for domain variables the ncdimensions parameter is
        # automatically changed to () within the
        # _write_netcdf_variable method. CF-1.9
        self._write_netcdf_variable(
            ncvar,
            ncdimensions,
            f,
            self.implementation.get_data_axes(f, None),
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

        .. versionaddedd:: (cfdm) 1.7.0

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
                    # A flat dataset has been requested, so strip off
                    # any group structure from the name.
                    ncvar = self._remove_group_structure(ncvar)

                self.implementation.nc_set_variable(new_grid_mapping, ncvar)

            g["grid_mapping_refs"].append(new_grid_mapping)

    def _unlimited(self, field, axis):
        """Whether an axis is unlimited.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            field: `Field` or `Domain`

            axis: `str`
                Domain axis construct identifier,
                e.g. ``'domainaxis1'``.

        :Returns:

            `bool`

        """
        return self.implementation.nc_is_unlimited_axis(field, axis)

    def _write_group_attributes(self, fields):
        """Writes the group-level attributes to the dataset.

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
            # Write the group-level attributes to the dataset
            # --------------------------------------------------------
            # Replace None values with actual values
            for attr, value in this_group_attributes.items():
                if value is not None:
                    continue

                this_group_attributes[attr] = self.implementation.get_property(
                    f0, attr
                )

            nc = self._get_group(g["dataset"], groups)

            if not g["dry_run"]:
                self._set_attributes(this_group_attributes, group=nc)

            group_attributes[groups] = tuple(this_group_attributes)

        g["group_attributes"] = group_attributes

    def _get_group(self, parent, groups):
        """Get the group of *parent* defined by *groups*.

        The group will be created if it doesn't already exist.

        .. versionadded:: (cfdm) NEXTVERSION

        :Parameters:

            parent: `netCDF4.Dateset` or `netCDF4.Group` or `Zarr.Group`
                The group in which to find or create new group.

            groups: sequence of `str`
                The group defined by the sequence of its subgroups
                relative to *parent*, e.g. ``('forecast', 'model')``.

        :Returns:

            `netCDF4.Group` or `Zarr.Group`
                The group.

        """
        match self.write_vars["backend"]:
            case "netCDF4":
                for group in groups:
                    if group in parent.groups:
                        parent = parent.groups[group]
                    else:
                        parent = self._createGroup(parent, group)

            case "zarr":
                group = "/".join(groups)
                if group in parent:
                    parent = parent[group]
                else:
                    parent = self._createGroup(parent, group)

        return parent

    def _write_global_attributes(self, fields):
        """Writes all global properties to the dataset.

        Specifically, finds the global properties from all of the
        input fields and writes them to the root group of the dataset.

        :Parameters:

            fields : `list` of field constructs

        :Returns:

            `None`

        """
        import re

        g = self.write_vars

        # ------------------------------------------------------------
        # Initialise the global attributes with those requested to be
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
        # Write the Conventions global attribute to the dataset
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
            attrs = {"Conventions": delimiter.join(g["Conventions"])}

            # ------------------------------------------------------------
            # Write the file descriptors to the dataset
            # ------------------------------------------------------------
            attrs.update(g["file_descriptors"])

            # ------------------------------------------------------------
            # Write other global attributes to the dataset
            # ------------------------------------------------------------
            attrs.update(
                {
                    attr: self.implementation.get_property(f0, attr)
                    for attr in global_attributes - set(("Conventions",))
                }
            )

            # ------------------------------------------------------------
            # Write "forced" global attributes to the dataset
            # ------------------------------------------------------------
            attrs.update(force_global)

            self._set_attributes(attrs, group=g["dataset"])

        g["global_attributes"] = global_attributes

    def dataset_exists(self, dataset):
        """Whether or not a dataset exists on disk.

        .. versionadded:: (cfdm) NEXTVERSION

        :Parameters:

            dataset: `str`
                The name of the dataset.

        :Returns:

            `bool`
                Whether or not the dataset exists on disk.

        """
        match self.write_vars["dataset_type"]:
            case "file":
                return os.path.isfile(dataset)

            case "directory":
                return os.path.isdir(dataset)

    def dataset_remove(self):
        """Remove the dataset that is being created.

        .. note:: If the dataset is a directory, then it is silently
                  not removed. To do so could be very dangerous (what
                  if it were your home space?).

        .. versionadded:: (cfdm) NEXTVERSION

        :Returns:

            `None`

        """
        g = self.write_vars
        match g["dataset_type"]:
            case "file":
                os.remove(g["dataset_name"])
            case "directory":
                pass

    def dataset_close(self):
        """Close the dataset that has been written.

        .. versionadded:: (cfdm) 1.7.0

        :Returns:

            `None`

        """
        g = self.write_vars
        if g["backend"] == "netCDF4":
            g["dataset"].close()

    def dataset_open(self, dataset_name, mode, fmt, fields):
        """Open the dataset for writing.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            dataset_name: `str`
                The dataset to open.

            mode: `str`
                As for the *mode* parameter for initialising a
                `netCDF4.Dataset` instance.

            fmt: `str`
                As for the *format* parameter for initialising a
                `netCDF4.Dataset` instance. Ignored for Zarr datasets.

            fields: sequence of `Field` or `Domain`
                The constructs to be written to the dataset. Note that
                these constructs are only used to ascertain if any
                data to be written is in *dataset_name*. If this is
                the case and mode is "w" then an exception is raised
                to prevent *dataset_name* from being deleted.

        :Returns:

            `netCDF.Dataset` or `zarr.Group`

        """
        import netCDF4

        if fields and mode == "w":
            dataset_name = os.path.abspath(dataset_name)
            for f in fields:
                if dataset_name in self.implementation.get_original_filenames(
                    f
                ):
                    raise ValueError(
                        "Can't write with mode 'w' to a dataset that contains "
                        f"data which needs to be read: {f!r} uses "
                        f"{dataset_name}"
                    )

        g = self.write_vars

        # mode == 'w' is safer than != 'a' in case of a typo (the
        # letters are neighbours on a QWERTY keyboard) since 'w' is
        # destructive. Note that for append ('a') mode the original
        # dataset is never wiped.
        if mode == "w" and g["overwrite"]:
            self.dataset_remove()

        match g["backend"]:
            case "netCDF4":
                try:
                    nc = netCDF4.Dataset(dataset_name, mode, format=fmt)
                except RuntimeError as error:
                    raise RuntimeError(f"{error}: {dataset_name}")

            case "zarr":
                try:
                    import zarr
                except ModuleNotFoundError as error:
                    error.msg += (
                        ". Install the 'zarr' package "
                        "(https://pypi.org/project/zarr) to read Zarr datasets"
                    )
                    raise

                nc = zarr.create_group(
                    dataset_name,
                    overwrite=g["overwrite"],
                    zarr_format=3,
                    storage_options=g.get("storage_options"),
                )

        return nc

    @_manage_log_level_via_verbosity
    def write(
        self,
        fields,
        dataset_name,
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
        chunk_cache=None,
        endian="native",
        compress=4,
        fletcher32=False,
        shuffle=True,
        scalar=True,
        string=True,
        extra_write_vars=None,
        verbose=None,
        warn_valid=True,
        group=True,
        coordinates=False,
        omit_data=None,
        dataset_chunks="4MiB",
        dataset_shards=None,
        cfa="auto",
        reference_datetime=None,
    ):
        """Write field and domain constructs to a dataset.

        Output global properties are those which occur in the set of
        CF global properties and non-standard data variable properties
        and which have equal values across all input fields.

        Logically identical field components are only written to the
        datset once, apart from when they need to fulfil both
        dimension coordinate and auxiliary coordinate roles for
        different data variables.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            fields : (sequence of) `cfdm.Field`
                The field or fields to write to the dataset.

                See `cfdm.write` for details.

            dataset_name: str
                The output dataset.

                See `cfdm.write` for details.

            mode: `str`, optional
                Specify the mode of write access for the output
                dataset. One of:

                ========  =================================================
                *mode*    Description
                ========  =================================================

                ``'w'``   Open a new dataset for writing to. If it
                          exists and *overwrite* is True then the
                          dataset is deleted prior to being recreated.

                ``'a'``   Open an existing dataset for appending new
                          information to. The new information will be
                          incorporated whilst the original contents of the
                          dataset will be preserved.

                          In practice this means that new fields will be
                          created, whilst the original fields will not be
                          edited at all. Coordinates on the fields, where
                          equal, will be shared as standard.

                          For append mode, note the following:

                          * Global attributes on the dataset
                            will remain the same as they were originally,
                            so will become inaccurate where appended fields
                            have incompatible attributes. To rectify this,
                            manually inspect and edit them as appropriate
                            after the append operation using methods such as
                            `nc_clear_global_attributes` and
                            `nc_set_global_attribute`.

                          * Fields with incompatible ``featureType`` to
                            the original dataset cannot be appended.

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

                By default the dataset is opened with write access
                mode ``'w'``.

            overwrite: bool, optional
                If False then raise an exception if the output dataset
                pre-exists. By default a pre-existing output dataset
                is over written.

                See `cfdm.write` for details.

            verbose: bool, optional
                See `cfdm.write` for details.

            file_descriptors: `dict`, optional
                Create description of dataset contents netCDF global
                attributes from the specified attributes and their
                values.

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
                Write metadata constructs that have data and are
                marked as external to the named external
                dataset. Ignored if there are no such constructs.

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
                The endian-ness of the output dataset. Ignored for
                Zarr datasets.

                See `cfdm.write` for details.

            compress: `int`, optional
                Regulate the speed and efficiency of compression.

                See `cfdm.write` for details.

            least_significant_digit: `int`, optional
                Truncate the input field construct data arrays, but
                not the data arrays of metadata constructs. Ignored
                for Zarr datasets.

                See `cfdm.write` for details.

            chunk_cache: `int` or `None`, optional
                The amount of memory (in bytes) used in each HDF5
                variable's chunk cache. Ignored for Zarr datasets.

                See `cfdm.write` for details.

                .. versionadded:: (cfdm) 1.12.2.0

            fletcher32: `bool`, optional
                If True then the Fletcher-32 HDF5 checksum algorithm is
                activated to detect compression errors. Ignored if
                *compress* is ``0``. Ignored for Zarr datasets.

                See `cfdm.write` for details.

            shuffle: `bool`, optional
                If True (the default) then the HDF5 shuffle filter
                (which de-interlaces a block of data before
                compression by reordering the bytes by storing the
                first byte of all of a variable's values in the chunk
                contiguously, followed by all the second bytes, and so
                on) is turned off. Ignored for Zarr datasets.

                See `cfdm.write` for details.

            string: `bool`, optional
                By default string-valued construct data are written as
                netCDF arrays of type string if the output dataset
                format is ``'NETCDF4'`` or ``'ZARR3'``, or of type
                char with an extra dimension denoting the maximum
                string length for any other output dataset format (see
                the *fmt* parameter). If *string* is False then
                string-valued construct data are written as netCDF
                arrays of type char with an extra dimension denoting
                the maximum string length, regardless of the selected
                output dataset format.

                See `cfdm.write` for details.

                .. versionadded:: (cfdm) 1.8.0

            warn_valid: `bool`, optional
                If True (the default) then print a warning when writing
                "out-of-range" data, as indicated by the values, if
                present, of any of the ``valid_min``, ``valid_max`` or
                ``valid_range`` properties on field and metadata
                constructs that have data. If False the warning
                is not printed.

                The consequence of writing out-of-range data values is
                that, by default, these values will be masked when the
                dataset is subsequently read.

                *Parameter example:*
                  If a construct has ``valid_max`` property with value
                  ``100`` and data with maximum value ``999``, then the
                  resulting warning may be suppressed by setting
                  ``warn_valid=False``.

                .. versionadded:: (cfdm) 1.8.3

            group: `bool`, optional
                If False then create a "flat" netCDF dataset, i.e. one
                with only the root group, regardless of any group
                structure specified by the field constructs.

                See `cfdm.write` for details.

                .. versionadded:: (cfdm) 1.8.6.0

            coordinates: `bool`, optional
                If True then include CF-netCDF coordinate variable names
                in the 'coordinates' attribute of output data
                variables.

                See `cfdm.write` for details.

                .. versionadded:: (cfdm) 1.8.7.0

            omit_data: (sequence of) `str`, optional
                Do not write the data of the named construct types.

                See `cfdm.write` for details.

                .. versionadded:: (cfdm) 1.10.0.1

            dataset_chunks: `str`, `int`, or `float`, optional
                The dataset chunking strategy. The default value is
                "4MiB". See `cfdm.write` for details.

            dataset_shards: `int` or `None`, optional
                The Zarr dataset sharding strategy. The default value
                is `None`. See `cfdm.write` for details.

                .. versionadded:: (cfdm) NEXTVERSION

            cfa: `dict` or `None`, optional
                Configure the creation of aggregation variables. See
                `cfdm.write` for details.

                .. versionadded:: (cfdm) 1.11.2.0

        :Returns:

            `None`

        **Examples**

        See `cfdm.write` for examples.

        """
        from packaging.version import Version

        logger.info(f"Writing to {fmt}")  # pragma: no cover

        # Expand dataset name
        dataset_name = os.path.expanduser(os.path.expandvars(dataset_name))
        dataset_name = abspath(dataset_name)

        # Parse the 'omit_data' parameter
        if omit_data is None:
            omit_data = ()
        elif isinstance(omit_data, str):
            omit_data = (omit_data,)

        if "all" in omit_data:
            omit_data = (
                "field",
                "field_ancillary",
                "domain_ancillary",
                "auxiliary_coordinate",
                "cell_measure",
                "dimension_coordinate",
            )

        # ------------------------------------------------------------
        # Initialise netCDF write parameters
        # ------------------------------------------------------------
        self.write_vars = {
            "dataset_name": dataset_name,
            # Format of output dataset
            "fmt": None,
            # Backend for writing to the dataset
            "backend": None,
            # Whether the output datset is a file or a directory
            "dataset_type": None,
            # netCDF4.Dataset instance
            #            "netcdf": None,
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
            "chunk_cache": None,
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
            # Whether or not to write string data-types to the output
            # dataset (as opposed to char data-types).
            "string": string,
            # Conventions
            "Conventions": Conventions,
            "ncdim_size_to_spanning_constructs": [],
            "count_variable_sample_dimension": {},
            "index_variable_sample_dimension": {},
            "external_variables": set(),
            "external_fields": [],
            "geometry_containers": {},
            "geometry_encoding": {},
            "geometry_dimensions": set(),
            "dimensions_with_role": {},
            "dimensions": set(),
            "unlimited_dimensions": set(),
            "latest_version": Version(self.implementation.get_cf_version()),
            "version": {},
            # Warn for the presence of out-of-range data with of
            # valid_[min|max|range] attributes?
            "warn_valid": bool(warn_valid),
            "valid_properties": set(("valid_min", "valid_max", "valid_range")),
            # Whether or not to name dimension coordinates in the
            # 'coordinates' attribute
            "coordinates": bool(coordinates),
            # Dictionary of netCDF variable names and netCDF
            # dimensions keyed by items of the field (such as a
            # coordinate or a coordinate reference)
            "seen": {},
            # Dry run: populate 'seen' dict without actually writing
            # to dataset.
            "dry_run": False,
            # To indicate if the previous iteration was a dry run:
            #
            # Note: need write_vars keys to specify dry runs (iterations)
            # and subsequent runs despite them being implied by the mode ('r'
            # and 'a' for dry_run and post_dry_run respectively) so that the
            # mode does not need to be passed to various methods, where a
            # pair of such keys seem clearer than one "effective mode" key.
            "post_dry_run": False,
            # Do not write the data of the named construct types.
            "omit_data": omit_data,
            # Change the units of a reference date-time.
            "reference_datetime": reference_datetime,
            # --------------------------------------------------------
            # CF Aggregation variables
            # --------------------------------------------------------
            # Configuration options for writing aggregation variables
            "cfa": None,
            # The directory of the aggregation dataset
            "aggregation_file_directory": None,
            # Cache the CF aggregation variable write status for each
            # dataset variable
            "cfa_write_status": {},
            # --------------------------------------------------------
            # Dataset chunking and sharding stategy
            # --------------------------------------------------------
            "dataset_chunks": dataset_chunks,
            "dataset_shards": dataset_shards,
            # --------------------------------------------------------
            # Quantization: Store unique Quantization objects, keyed
            #               by their output dataset variable names.
            # --------------------------------------------------------
            "quantization": {},
        }

        if mode not in ("w", "a", "r+"):
            raise ValueError(
                "cfdm.write mode parameter must be one of 'w', 'a' or 'r+', "
                f"but got '{mode}'"
            )
        elif mode == "r+":  # support alias used by netCDF4.Dataset mode
            mode = "a"

        self.write_vars["mode"] = mode

        # Parse the 'dataset_chunks' parameter
        if dataset_chunks != "contiguous":
            from dask.utils import parse_bytes

            try:
                self.write_vars["dataset_chunks"] = parse_bytes(dataset_chunks)
            except (ValueError, AttributeError):
                raise ValueError(
                    "Invalid value for the 'dataset_chunks' keyword: "
                    f"{dataset_chunks!r}."
                )

        # Parse the 'dataset_shards' parameter
        if dataset_shards is not None:
            if not isinstance(dataset_shards, Integral) or dataset_shards < 1:
                raise ValueError(
                    f"Invalid value for 'dataset_shards' keyword: "
                    f"{dataset_shards!r}."
                )

        # ------------------------------------------------------------
        # Parse the 'cfa' keyword
        # ------------------------------------------------------------
        if cfa is None:
            cfa = {"constructs": None}
        elif isinstance(cfa, str):
            cfa = {"constructs": cfa}
        elif isinstance(cfa, dict):
            keys = ("constructs", "uri", "strict")
            if not set(cfa).issubset(keys):
                raise ValueError(
                    f"Invalid dictionary key to the 'cfa' keyword: {cfa!r}. "
                    f"Valid keys are {keys}"
                )

            valid_uri = ("default", "absolute", "relative")
            if cfa.get("uri", "default") not in valid_uri:
                raise ValueError(
                    "Invalid value for the 'uri' keyword of the 'cfa' "
                    f"parameter: {cfa!r}. Expected one of {valid_uri}"
                )

            cfa = cfa.copy()
        else:
            raise ValueError(
                f"Invalid value for the 'cfa' keyword: {cfa!r}. "
                "Should be a string, a dictionary, or None"
            )

        cfa.setdefault("constructs", "auto")
        cfa.setdefault("uri", "default")
        cfa.setdefault("strict", True)

        constructs = cfa["constructs"]
        if isinstance(constructs, dict):
            cfa["constructs"] = constructs.copy()
        elif constructs is not None:
            # Convert a (sequence of) `str` to a `dict`
            if isinstance(constructs, str):
                constructs = (constructs,)

            cfa["constructs"] = {c: None for c in constructs}

        self.write_vars["cfa"] = cfa

        effective_mode = mode  # actual mode to use for the first IO iteration
        effective_fields = fields

        if mode == "a":
            # First read in the fields from the existing dataset:
            effective_fields = self._NetCDFRead(self.implementation).read(
                dataset_name, netcdf_backend="netCDF4"
            )

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
                    "global attribute to the original dataset."
                )

        self._file_io_iteration(
            mode=effective_mode,
            overwrite=overwrite,
            fields=effective_fields,
            dataset_name=dataset_name,
            fmt=fmt,
            global_attributes=global_attributes,
            variable_attributes=variable_attributes,
            file_descriptors=file_descriptors,
            external=external,
            Conventions=Conventions,
            datatype=datatype,
            least_significant_digit=least_significant_digit,
            chunk_cache=chunk_cache,
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
                dataset_name=dataset_name,
                fmt=fmt,
                global_attributes=global_attributes,
                variable_attributes=variable_attributes,
                file_descriptors=file_descriptors,
                external=external,
                Conventions=Conventions,
                datatype=datatype,
                least_significant_digit=least_significant_digit,
                chunk_cache=chunk_cache,
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
        dataset_name,
        fmt,
        global_attributes,
        variable_attributes,
        file_descriptors,
        external,
        Conventions,
        datatype,
        least_significant_digit,
        chunk_cache,
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
        """Perform a dataset-writing iteration."""
        from packaging.version import Version

        # ------------------------------------------------------------
        # Initiate dataset IO with given write variables
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
        for version in ("1.6", "1.7", "1.8", "1.9", "1.10", "1.11", "1.12"):
            g["CF-" + version] = Version(version)

        if extra_write_vars:
            g.update(copy.deepcopy(extra_write_vars))

        # Customise the write parameters
        self._customise_write_vars()

        compress = int(compress)
        if compress:
            compression = "zlib"
        else:
            compression = None

        if fmt in NETCDF3_FMTS:
            if compress:
                # Can't compress a netCDF-3 format file
                compress = 0

            if group:
                # Can't write groups to a netCDF-3 file
                g["group"] = False
        elif fmt not in NETCDF4_FMTS + ZARR_FMTS:
            raise ValueError(
                f"Unknown output dataset format: {fmt!r}. "
                f"Valid formats are {NETCDF4_FMTS + NETCDF3_FMTS + ZARR_FMTS}"
            )

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
                    f"a CF global variable: {variable_attributes}"
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
            np.dtype(bool): np.dtype("int32"),
            np.dtype(object): np.dtype(float),
        }
        if datatype:
            dtype_conversions.update(datatype)

        g["datatype"].update(dtype_conversions)

        # -------------------------------------------------------
        # Compression/endian
        # -------------------------------------------------------
        g["netcdf_compression"].update(
            {
                "compression": compression,
                "complevel": compress,
                "fletcher32": bool(fletcher32),
                "shuffle": bool(shuffle),
            }
        )
        g["endian"] = endian
        g["least_significant_digit"] = least_significant_digit

        g["fmt"] = fmt
        match fmt:
            case "ZARR3":
                g["backend"] = "zarr"
                g["dataset_type"] = "directory"
            case _:
                g["backend"] = "netCDF4"
                g["dataset_type"] = "file"

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
        # Open the output dataset
        # ------------------------------------------------------------
        if self.dataset_exists(dataset_name):
            if mode == "w" and not overwrite:
                raise IOError(
                    f"Can't write with mode {mode!r} to existing dataset "
                    f"{os.path.abspath(dataset_name)} unless overwrite=True"
                )

            if not os.access(dataset_name, os.W_OK):
                raise IOError(
                    "Can't write to existing dataset "
                    f"{os.path.abspath(dataset_name)} without permission"
                )
        else:
            g["overwrite"] = False

        g["dataset_name"] = dataset_name
        g["dataset"] = self.dataset_open(dataset_name, mode, fmt, fields)

        if not g["dry_run"]:
            # --------------------------------------------------------
            # Write global properties to the dataset first. This is
            # important as doing it later could slow things down
            # enormously. This function also creates the
            # g['global_attributes'] set, which is used in the
            # `_write_field_or_domain` method.
            # --------------------------------------------------------
            self._write_global_attributes(fields)

            # --------------------------------------------------------
            # Write group-level properties to the dataset next
            # --------------------------------------------------------
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
            if os.path.realpath(external) == os.path.realpath(dataset_name):
                raise ValueError(
                    "Can't set 'dataset_name' and 'external' to the same path"
                )

        g["external_dataset"] = external

        # ------------------------------------------------------------
        # Write each field construct
        # ------------------------------------------------------------
        for f in fields:
            self._write_field_or_domain(f)

        # ------------------------------------------------------------
        # Write all of the buffered data to disk
        # ------------------------------------------------------------
        # For append mode, it is cleaner code-wise to close the
        # dataset on the read iteration and re-open it for the append
        # iteration. So we always close it here.
        self.dataset_close()

        # ------------------------------------------------------------
        # Write external fields to the external dataset
        # ------------------------------------------------------------
        if g["external_fields"] and g["external_dataset"] is not None:
            self.write(
                fields=g["external_fields"],
                dataset_name=g["external_dataset"],
                fmt=fmt,
                overwrite=overwrite,
                datatype=datatype,
                endian=endian,
                compress=compress,
                fletcher32=fletcher32,
                shuffle=shuffle,
                extra_write_vars=extra_write_vars,
                chunk_cache=chunk_cache,
                dataset_chunks=g["dataset_chunks"],
                dataset_shards=g["dataset_shards"],
            )

    def _int32(self, array):
        """Cast an array to 32-bit integers.

        This saves space and allows the variables to be written to
        CLASSIC files.

        If the input array already contins 32-bit integers then it is
        returned unchanged.

        If the input array is not of integer kind then an exception is
        raised.

        .. versionadded:: (cfdm) 1.9.0.1

        :Parameters:

            array: `numpy.ndarray`
                The array to be recast.

        :Returns:

            `numpy.ndarray`
                The array recast to 32-bit integers.

        """
        if array.dtype.kind != "i":
            raise TypeError(
                f"Won't cast array from {array.dtype.base} to dtype('int32')"
            )

        if array.max() <= np.iinfo("int32").max:
            array = array.astype("int32", casting="same_kind")

        return array

    def _dimension_in_subgroup(self, v, ncdim):
        """Return True if the dimension is in a valid group.

        Returns True if the dimension is in the same group, or a
        parent group, as the group defined by the construct. Otherwise
        return False.

        .. versionadded:: (cfdm) 1.9.0.3

        :Parameters:

            v: Construct

            ncdim: `str`
                The dataset dimension name.

                *Parameter example:*
                  ``'lat'``

                *Parameter example:*
                  ``'/group1/lat'``

        :Returns:

            `bool`
                Whether or not the dimension is in a valid group.

        """
        v_groups = self.implementation.nc_get_variable_groups(v)
        v_groups = "/" + "/".join(v_groups)

        ncdim_groups = self._groups(ncdim)

        return v_groups.startswith(ncdim_groups)

    def _customise_write_vars(self):
        """Customise the write parameters.

        This method is primarily aimed at providing a customisation
        entry point for subclasses.

        .. versionadded:: (cfdm) 1.10.1.0

        """
        pass

    def _chunking_parameters(self, data, ncdimensions):
        """Set chunking parameters for a dataset variable.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            data: `Data` or `None`
                The data being written.

            ncdimensions: `tuple`
                The dataset dimensions of the data.

        :Returns:

            3-tuple
                The 'contiguous', 'chunksizes', and 'shards'
                parameters for `_createVariable`.

        """
        if data is None:
            return False, None, None

        g = self.write_vars

        # ------------------------------------------------------------
        # Dataset chunk strategy: Either use that provided on the
        # data, or else work it out.
        # ------------------------------------------------------------
        # Get the chunking strategy defined by the data itself
        chunksizes = self.implementation.nc_get_dataset_chunksizes(data)
        shards = self.implementation.nc_get_dataset_shards(data)

        if chunksizes == "contiguous":
            # Contiguous as defined by 'data'
            return True, None, None

        # Still here?
        if shards is None:
            shards = g["dataset_shards"]

        dataset_chunks = g["dataset_chunks"]
        if isinstance(chunksizes, int):
            # Reset dataset chunks to the integer given by 'data'
            dataset_chunks = chunksizes
        elif chunksizes is not None:
            # Chunked as defined by the tuple of int given by 'data'
            return False, chunksizes, shards

        # Still here? Then work out the chunking strategy from the
        # dataset_chunks
        if dataset_chunks == "contiguous":
            # Contiguous as defined by 'dataset_chunks'
            return True, None, None

        # Still here? Then work out the chunks from both the
        # size-in-bytes given by dataset_chunks (e.g. 1024, or '1
        # KiB'), and the data shape (e.g. (12, 73, 96)).
        if self._compressed_data(ncdimensions):
            # Base the dataset chunks on the compressed data that is
            # going into the dataset
            d = self.implementation.get_compressed_array(data)
        else:
            d = data

        d_dtype = d.dtype
        dtype = g["datatype"].get(d_dtype, d_dtype)

        from dask import config as dask_config
        from dask.array.core import normalize_chunks

        with dask_config.set({"array.chunk-size": dataset_chunks}):
            chunksizes = normalize_chunks("auto", shape=d.shape, dtype=dtype)

        if chunksizes:
            # 'chunksizes' looks something like ((96, 96, 96, 50),
            # (250, 250, 4)). However, we only want one number per
            # dimension, so we choose the largest: [96, 250].
            chunksizes = [max(c) for c in chunksizes]
            return False, chunksizes, shards
        else:
            # The data is scalar, so 'chunksizes' is () => write the
            # data contiguously.
            return True, None, None

    def _compressed_data(self, ncdimensions):
        """Whether or not the data is being written in compressed form.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            ncdimensions: `sequence` of `str`
                The ordered dataset dimension names of the data. These
                are the dimensions going into the dataset, and if the
                data is compressed will differ from the dimensions
                implied by the data in memory.

        :Returns:

            `bool`
                `True` if the data is being written in a compressed
                form, otherwise `False`.

        """
        return bool(
            set(ncdimensions).intersection(
                self.write_vars["sample_ncdim"].values()
            )
        )

    def _change_reference_datetime(self, coord):
        """Change the units of a reference date-time.

        .. versionadded:: (cfdm) 1.12.0.0

        :Parameters:

            coord: `Coordinate`
                The time coordinates.

        :Returns:

                A new coordinate construct with changed units.

        """
        reference_datetime = self.write_vars["reference_datetime"]
        if not reference_datetime or not coord.Units.isreftime:
            return coord

        if not hasattr(coord, "reference_datetime"):
            raise ValueError(
                "Can't override time coordinate reference date-time "
                f"for {coord.__class__} objects."
            )

        coord = coord.copy()
        try:
            coord.reference_datetime = reference_datetime
        except ValueError:
            raise ValueError(
                "Can't override time coordinate reference date-time "
                f"{coord.reference_datetime!r} with {reference_datetime!r}"
            )
        else:
            return coord

    def _cfa_write_status(self, ncvar, cfvar, construct_type, domain_axes):
        """The aggregation write status of the data.

        A necessary and sufficient condition for writing the data as
        aggregated data is that this method returns `True` and
        `_cfa_aggregation_instructions` returns a `dict`.

        .. versionadded:: (cfdm) 1.12.0.0

        :Parameters:

            cfvar:
                Construct (e.g. `DimensionCoordinate`), or construct
                component e.g. (`Bounds`) that contains the data.

            construct_type: `str`
                The construct type of the *cfvar*, or of its parent if
                *cfvar* is a construct component.

            domain_axes: `None`, or `tuple` of `str`
                The domain axis construct identifiers for *cfvar*.

        :Returns:

            `bool`
                True if the variable is to be written as an
                aggregation variable.

        """
        g = self.write_vars

        cfa_write_status = g["cfa_write_status"].get(ncvar)
        if cfa_write_status is not None:
            return cfa_write_status

        if construct_type is None:
            # This prevents recursion whilst writing fragment array
            # variables.
            g["cfa_write_status"][ncvar] = False
            return False

        data = self.implementation.get_data(cfvar, None)
        if data is None:
            # Can't write as an aggregation variable when there is no
            # data
            g["cfa_write_status"][ncvar] = False
            return False

        constructs = g["cfa"].get("constructs")
        if constructs is None:
            # Nothing gets written as an aggregation variable when
            # 'constructs' is set to None
            g["cfa_write_status"][ncvar] = False
            return False

        for c in (construct_type, "all"):
            if c in constructs:
                ndim = constructs[c]
                if ndim is None or ndim == len(domain_axes):
                    g["cfa_write_status"][ncvar] = True
                    return True

                g["cfa_write_status"][ncvar] = False
                return False

        if "auto" in constructs:
            if not data.nc_get_aggregated_data():
                g["cfa_write_status"][ncvar] = False
                return False

            ndim = constructs["auto"]
            if ndim is None or ndim == len(domain_axes):
                g["cfa_write_status"][ncvar] = True
                return True

        g["cfa_write_status"][ncvar] = False
        return False

    def _cfa_create_data(self, cfa, ncvar, ncdimensions, data, cfvar):
        """Write an aggregation variable to the dataset.

        .. versionadded:: (cfdm) 1.12.0.0

        :Parameters:

            cfa: `dict`
                A dictionary containing the fragment array variables'
                data.

            ncvar: `str`
                The dataset xname for the variable.

            ncdimensions: sequence of `str`

            netcdf_attrs: `dict`

            data: `Data`

        :Returns:

            `True`

        """
        g = self.write_vars

        # ------------------------------------------------------------
        # Write the fragment array variables to the dataset
        # ------------------------------------------------------------
        aggregated_data = data.nc_get_aggregated_data()
        aggregated_data_attr = []

        all_dimensions = g["dimensions"]
        all_unlimited_dimensions = g["unlimited_dimensions"]

        # ------------------------------------------------------------
        # Map
        # ------------------------------------------------------------
        feature = "map"
        f_map = cfa[feature]

        chunking = None

        # Get the shape netCDF dimensions from the 'map' fragment
        # array variable.
        map_ncdimensions = []
        dim = "j"
        for size in f_map.shape:
            cfa_ncdim = f"a_map_{dim}{size}"
            if dim == "i" and all_unlimited_dimensions.intersection(
                ncdimensions
            ):
                unlimited = True
                # Append a "u" to the dimension name to allow there to
                # fixed and unlimited dimensions with the same size
                cfa_ncdim += "u"
            else:
                unlimited = False

            if cfa_ncdim not in all_dimensions:
                # Create a new location dimension
                self._write_dimension(
                    cfa_ncdim, None, unlimited=unlimited, size=size
                )

            map_ncdimensions.append(cfa_ncdim)
            dim = "i"

        map_ncdimensions = tuple(map_ncdimensions)

        #        # Write the fragment array variable to the netCDF dataset
        #        if ncdimensions[0].startswith('time'):
        #            chunking=(False, (f_map.shape[0], f_map.shape[1] * 85*12))

        feature_ncvar = self._cfa_write_fragment_array_variable(
            f_map,
            aggregated_data.get(feature, f"fragment_{feature}"),
            map_ncdimensions,
            chunking=chunking,
        )
        aggregated_data_attr.append(f"{feature}: {feature_ncvar}")

        if "uris" in cfa:
            # --------------------------------------------------------
            # URIs
            # --------------------------------------------------------
            feature = "uris"
            f_uris = cfa[feature]

            chunking = None

            # Get the fragment array dataset dimensions from the
            # 'location' fragment array variable.
            location_ncdimensions = []
            for ncdim, size in zip(ncdimensions, f_uris.shape):
                cfa_ncdim = f"a_{ncdim}"
                if cfa_ncdim not in all_dimensions:
                    # Create a new fragment array dimension
                    unlimited = ncdim in all_unlimited_dimensions
                    # unlimited = ncdim in g[
                    #    "unlimited_dimensions"
                    # ] and ncdim.startswith("time")
                    self._write_dimension(
                        cfa_ncdim, None, unlimited=unlimited, size=size
                    )

                location_ncdimensions.append(cfa_ncdim)

            location_ncdimensions = tuple(location_ncdimensions)

            #            # Write the fragment array variable to the netCDF dataset
            #            if ncdimensions[0].startswith('time'):
            #                chunking = (False, ((85*12,) + f_uris.shape[1:]))
            #            else:
            chunking = None
            feature_ncvar = self._cfa_write_fragment_array_variable(
                f_uris,
                aggregated_data.get(feature, f"fragment_{feature}"),
                location_ncdimensions,
                chunking=chunking,
            )
            aggregated_data_attr.append(f"{feature}: {feature_ncvar}")

            # --------------------------------------------------------
            # Identifiers
            # --------------------------------------------------------
            feature = "identifiers"

            # Attempt to reduce variable names to a common scalar
            # value
            u = cfa[feature].unique().compressed().persist()
            if u.size == 1:
                cfa[feature] = u.squeeze()
                variable_ncdimensions = ()
            else:
                variable_ncdimensions = location_ncdimensions

            f_identifiers = cfa[feature]

            # Write the fragment array variable to the netCDF dataset
            feature_ncvar = self._cfa_write_fragment_array_variable(
                f_identifiers,
                aggregated_data.get(feature, f"fragment_{feature}"),
                variable_ncdimensions,
            )
            aggregated_data_attr.append(f"{feature}: {feature_ncvar}")
        else:
            # --------------------------------------------------------
            # Unique values
            # --------------------------------------------------------
            feature = "unique_values"
            f_unique_value = cfa[feature]

            # Get the fragment array dimensions from the 'value'
            # fragment array variable.
            unique_value_ncdimensions = []
            for ncdim, size in zip(ncdimensions, f_unique_value.shape):
                cfa_ncdim = f"a_{ncdim}"
                if cfa_ncdim not in g["dimensions"]:
                    # Create a new fragment array dimension
                    self._write_dimension(cfa_ncdim, None, size=size)

                unique_value_ncdimensions.append(cfa_ncdim)

            unique_value_ncdimensions = tuple(unique_value_ncdimensions)

            # Write the fragment array variable to the dataset
            feature_ncvar = self._cfa_write_fragment_array_variable(
                f_unique_value,
                aggregated_data.get(feature, f"fragment_{feature}"),
                unique_value_ncdimensions,
            )
            aggregated_data_attr.append(f"{feature}: {feature_ncvar}")

        # ------------------------------------------------------------
        # Add the aggregation variable attributes
        # ------------------------------------------------------------
        self._write_variable_attributes(
            None,
            ncvar,
            extra={
                "aggregated_dimensions": " ".join(ncdimensions),
                "aggregated_data": " ".join(sorted(aggregated_data_attr)),
            },
        )

        g["cfa_write_status"][ncvar] = True
        return True

    def _filled_string_array(self, array, fill_value=""):
        """Fill a string array.

        .. versionadded:: (cfdm) 1.12.0.0

        :Parameters:

            array: `numpy.ndarray`
                The `numpy` array with string (byte or unicode) data
                type.

        :Returns:

            `numpy.ndarray`
                The string array with any missing data replaced
                by the fill value.

        """
        if np.ma.isMA(array):
            return array.filled(fill_value)

        return array

    def _cfa_write_fragment_array_variable(
        self, data, ncvar, ncdimensions, attributes=None, chunking=None
    ):
        """Write an aggregation fragment array variable.

        .. versionadded:: (cfdm) 1.12.0.0

        :Parameters:

            data `Data`
                The data to write.

            ncvar: `str`
                The dataset variable name.

            ncdimensions: `tuple` of `str`
                The fragment array variable's dataset dimensions.

            attributes: `dict`, optional
                Any attributes to attach to the variable.

            chunking: sequence, optional
                Set `_createVariable` 'contiguous', 'chunksizes', and
                'shards' parameters (in that order) for the fragment
                array variable. If `None` (the default), then these
                parameters are inferred from the data.

        :Returns:

            `str`
                The name of the fragment array dataset variable.

        """
        create = not self._already_in_file(data, ncdimensions)

        if create:
            # Create a new fragment array variable in the dataset,
            # with 'contiguous' chunking
            ncvar = self._name(ncvar)
            self._write_netcdf_variable(
                ncvar,
                ncdimensions,
                data,
                None,
                extra=attributes,
                chunking=chunking,
            )
        else:
            # This fragment array variable has already been written to
            # the dataset
            ncvar = self.write_vars["seen"][id(data)]["ncvar"]

        return ncvar

    @classmethod
    def _cfa_unique_value(cls, a, strict=True):
        """Return the unique value of an array.

        If there are multiple unique values then missing data is
        returned.

        .. versionadded:: (cfdm) 1.12.0.0

        :Parameters:

             a: `numpy.ndarray`
                The array.

             strict: `bool`, optional
                 If True then raise an exception if there is more than
                 one unique value. If False then a unique value of
                 missing data will be returned in this case.

        :Returns:

            `numpy.ndarray`
                A size 1 array containing the unique value, or missing
                data if there is not a unique value.

        """
        a = cfdm_to_memory(a)

        out_shape = (1,) * a.ndim
        a = np.unique(a)
        if a.size == 1:
            return a.reshape(out_shape)

        if strict:
            raise AggregationError(str(a))

        return np.ma.masked_all(out_shape, dtype=a.dtype)

    def _cfa_fragment_array_variables(self, data, cfvar):
        """Convert data to aggregated_data terms.

        .. versionadded:: (cfdm) 1.12.0.0

        :Parameters:

            data: `Data`
                The data to be converted.

            cfvar: construct
                The construct that contains the *data*.

        :Returns:

            `dict`
                A dictionary whose keys are the standardised
                aggregation_data terms, with values of `Data`
                instances containing the corresponding variables.

        **Examples**

        >>> n._cfa_fragment_array_variables(data, cfvar)
        {'shape': <Data(2, 1): [[5, 8]]>,
         'location': <Data(1, 1): [[file:///home/file.nc]]>,
         'variable': <Data(1, 1): [[q]]>}

        """
        from os.path import relpath

        g = self.write_vars

        if not data.nc_get_aggregation_write_status():
            raise AggregationError(
                f"Can't write {cfvar!r} as a CF aggregation variable. "
                "This is could be "
                "because some fragment values in memory have been "
                "changed relative to those in the fragment datasets, "
                "or a Dask rechunking has occured, etc."
            )

        # ------------------------------------------------------------
        # Create the 'map' array
        # ------------------------------------------------------------
        a_shape = data.numblocks
        if a_shape:
            ndim = data.ndim
            aggregation_shape = np.ma.masked_all(
                (ndim, max(a_shape)), dtype=integer_dtype(max(data.chunksize))
            )
            for i, chunks in enumerate(data.chunks):
                aggregation_shape[i, : len(chunks)] = chunks
        else:
            # Scalar 'shape' fragment array variable
            aggregation_shape = np.ones((), dtype=np.dtype("int32"))

        out = {"map": type(data)(aggregation_shape)}

        if data.nc_get_aggregation_fragment_type() == "uri":
            from uritools import uricompose, urisplit

            # --------------------------------------------------------
            # Create 'uris' and 'idenftifiers' arrays
            # --------------------------------------------------------
            uri_default = g["cfa"].get("uri", "default") == "default"
            uri_relative = (
                not uri_default
                and g["cfa"].get("uri", "relative") == "relative"
            )
            normalise = not uri_default

            if uri_relative:
                # Get the aggregation dataset directory as an absolute
                # URI
                aggregation_file_directory = g["aggregation_file_directory"]
                if aggregation_file_directory is None:
                    uri = urisplit(dirname(g["dataset_name"]))
                    if uri.isuri():
                        aggregation_file_scheme = uri.scheme
                        aggregation_file_directory = uri.geturi()
                    else:
                        aggregation_file_scheme = "file"
                        aggregation_file_directory = uricompose(
                            scheme=aggregation_file_scheme,
                            authority="",
                            path=uri.path,
                        )
                        uri_fragment = uri.fragment
                        if uri_fragment is not None:
                            # Append a URI fragment. Do this with a
                            # string-append, rather than via
                            # `uricompose` in case the fragment
                            # contains more than one # character.
                            aggregation_file_directory += f"#{uri_fragment}"

                    g["aggregation_file_directory"] = (
                        aggregation_file_directory
                    )
                    g["aggregation_file_scheme"] = aggregation_file_scheme

                aggregation_file_scheme = g["aggregation_file_scheme"]

            aggregation_uris = []
            aggregation_identifiers = []
            for index, position in zip(
                data.chunk_indices(), data.chunk_positions()
            ):
                # Try to get this Dask chunk's data as a reference to
                # fragment dataset
                fragment = data[index].compute(_force_to_memory=False)
                try:
                    dataset_name, address, is_subspace, f_index = (
                        fragment.get_filename(normalise=normalise),
                        fragment.get_address(),
                        fragment.is_subspace(),
                        fragment.index(),
                    )
                except (AttributeError, TypeError):
                    # This Dask chunk's data is not a reference to
                    # fragment file
                    raise AggregationError(
                        f"Can't write {cfvar!r} as a CF "
                        "aggregation variable: "
                        f"The Dask chunk in position {position} "
                        f"(defined by data index {index!r}) does not "
                        "reference a unique fragment dataset. This is could "
                        "be because some fragment values in memory have been "
                        "changed relative to those in the fragment datasets, "
                        "or a Dask rechunking has occured, etc."
                    )

                if is_subspace:
                    # This Dask chunk's data is a reference to
                    # fragment dataset, but only to a subspace of it.
                    raise AggregationError(
                        f"Can't write {cfvar!r} as a CF "
                        "aggregation variable: "
                        f"The Dask chunk in position {position} "
                        f"(defined by data index {index!r}) references "
                        f"a subspace ({f_index!r}) of the fragment dataset "
                        f"{fragment!r}. This might be fixable by setting "
                        "the 'cfa_write' keyword in the 'read' function."
                    )

                uri = urisplit(dataset_name)
                if uri_relative and uri.isrelpath():
                    dataset_name = abspath(dataset_name)

                if uri.isabspath():
                    # Dataset name is an absolute-path URI reference
                    dataset_name = uricompose(
                        scheme="file",
                        authority="",
                        path=uri.path,
                    )
                    uri_fragment = uri.fragment
                    if uri_fragment is not None:
                        # Append a URI fragment. Do this with a
                        # string-append, rather than via `uricompose`
                        # in case the fragment contains more than one
                        # # character.
                        dataset_name += f"#{uri_fragment}"

                if uri_relative:
                    scheme = uri.scheme
                    if not scheme:
                        scheme = "file"

                    if scheme != aggregation_file_scheme:
                        raise AggregationError(
                            f"Can't write {cfvar!r} as a CF "
                            "aggregation variable: "
                            "Attempting to create a relative-path URI "
                            f"reference for the fragment dataset {fragment}, "
                            "referenced by the Dask chunk in position "
                            f"{position} (defined by data index {index!r}), "
                            "but the aggregation dataset URI scheme "
                            f"({aggregation_file_scheme}:) is incompatible."
                        )

                    dataset_name = relpath(
                        dataset_name, start=aggregation_file_directory
                    )

                aggregation_uris.append(dataset_name)
                aggregation_identifiers.append(address)

            # Reshape the 1-d aggregation instruction arrays to span
            # the data dimensions, plus the extra trailing dimension
            # if there is one.
            aggregation_uris = np.array(aggregation_uris).reshape(a_shape)
            aggregation_identifiers = np.array(
                aggregation_identifiers
            ).reshape(a_shape)

            out["uris"] = type(data)(aggregation_uris)
            out["identifiers"] = type(data)(aggregation_identifiers)
        else:
            # ------------------------------------------------------------
            # Create a 'unique_values' array
            # ------------------------------------------------------------
            # Transform the data so that it spans the fragment
            # dimensions with one value per fragment. If a chunk has
            # more than one unique value then the fragment's value is
            # missing data.
            import dask.array as da

            dx = data.to_dask_array(
                _force_mask_hardness=False, _force_to_memory=False
            )
            dx_ind = tuple(range(dx.ndim))
            out_ind = dx_ind
            dx = da.blockwise(
                self._cfa_unique_value,
                out_ind,
                dx,
                dx_ind,
                adjust_chunks={i: 1 for i in out_ind},
                meta=np.array((), dx.dtype),
                strict=g["cfa"]["strict"],
            )
            d = type(data)(dx)

            try:
                d.persist(inplace=True)
            except AggregationError as error:
                raise AggregationError(
                    f"Can't write {cfvar!r} as a CF aggregation "
                    "variable. "
                    "At least one Dask chunk has more than one unique value: "
                    f"{error}. "
                    "Set the 'strict' keyword of the 'cfa' parameter to True "
                    "to use a unique value of missing data in this case."
                )

            out["unique_values"] = d

        # Return the dictionary of Data objects
        return out

    def _write_quantization_container(self, quantization):
        """Write a CF quantization container variable.

        .. note:: It is assumed, but not checked, that the
                  per-variable parameters (such as "quantization_nsd"
                  or "_QuantizeBitRoundNumberOfSignificantBits") have
                  been already been removed from *quantization*.

         .. versionadded:: (cfdm) 1.12.2.0

        :Parameters:

            quantization: `Quantization`
                The Quantization metadata to be written.

        :Returns:

            `str`
                The dataset variable name for the quantization
                container.

        """
        g = self.write_vars

        for ncvar, q in g["quantization"].items():
            if self.implementation.equal_components(quantization, q):
                # Use this existing quantization container
                return ncvar

        # Create a new quantization container variable
        ncvar = self._create_variable_name(
            quantization, default="quantization"
        )

        logger.info(
            f"    Writing {quantization!r} to variable: {ncvar}"
        )  # pragma: no cover

        kwargs = {
            "varname": ncvar,
            "datatype": "S1",
            "endian": g["endian"],
        }
        kwargs.update(g["netcdf_compression"])

        if not g["dry_run"]:
            # Create the variable
            self._createVariable(**kwargs)
            self._set_attributes(
                self.implementation.parameters(quantization), ncvar
            )

        # Update the quantization dictionary
        g["quantization"][ncvar] = quantization

        return ncvar

    def _missing_value(self, x, datatype):
        """Get the missing value.

         .. versionadded:: (cfdm) NEXTVERSION

        :Parameters:

            x: construct or `Data`
                The data for which to get the missing value.

            datatype: `str` or str
                The data type, e.g. ``'S1'``, ``'f4'``, `str`.  Used
                to get the netCDF default fill value, but only when a
                missing value can't be found from the attributes of
                *x*.

        :Returns:

                The missing value, or `None` if no missing value could
                be found.

        """
        try:
            # Try 'x' as a construct
            mv = x.get_property("_FillValue", None)
            if mv is None:
                mv = x.get_property("missing_value", None)
        except AttributeError:
            try:
                # Try 'x' as a `Data` object
                mv = getattr(x, "fill_value", None)
            except AttributeError:
                mv = None

        if mv is None:
            # Try to get the netCDF default fill value
            import netCDF4

            mv = netCDF4.default_fillvals.get(datatype)
            if mv is None and datatype is str:
                mv = ""

        return mv
