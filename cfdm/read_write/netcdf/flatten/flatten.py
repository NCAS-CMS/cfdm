"""Create a flattened version of a grouped netCDF dataset.

Portions of this code were adapted from the `netcdf_flattener`
library, which carries the following Apache 2.0 Licence:

Copyright (c) 2020 EUMETSAT

Licensed to the Apache Software Foundation (ASF) under one or more
contributor license agreements. The ASF licenses this file to you
under the Apache License, Version 2.0 (the "License"); you may not use
this file except in compliance with the License. You may obtain a copy
of the License at http://www.apache.org/licenses/LICENSE-2.0.

"""

import hashlib
import logging
import re
import warnings

from ....functions import is_log_level_debug
from .config import (
    flattener_attribute_map,
    flattener_dimension_map,
    flattener_separator,
    flattener_variable_map,
    flattening_rules,
    group_separator,
    max_name_len,
    ref_not_found_error,
)

logger = logging.getLogger(__name__)

# Mapping from numpy dtype endian format to that expected by netCDF4
_dtype_endian_lookup = {
    "=": "native",
    ">": "big",
    "<": "little",
    "|": "native",
    None: "native",
}

# Set of netCDF attributes that contain references to dimensions or
# variables
referencing_attributes = set(flattening_rules)


def netcdf_flatten(
    input_ds,
    output_ds,
    strict=True,
    omit_data=False,
    write_chunksize=134217728,
):
    """Create a flattened version of a grouped dataset.

    **CF-netCDF coordinate variables**

    When a CF-netCDF coordinate variable in the input dataset is in a
    different group to its corresponding dimension, the same variable
    in the output flattened dataset will no longer be a CF-netCDF
    coordinate variable, as its name will be prefixed with a different
    group identifier than its dimension.

    In such cases it is up to the user to apply the proximal and
    lateral search algorithms to the flattened dataset returned by
    `netcdf_flatten`, in conjunction with the mappings defined in the
    newly created global attributes ``_flattener_variable_map`` and
    ``_flattener_dimension_map``, to find which netCDF variables are
    acting as CF coordinate variables in the flattened dataset. See
    https://cfconventions.org/cf-conventions/cf-conventions.html#groups
    for details.

    For example, if an input dataset has dimension ``lat`` in the root
    group and coordinate variable ``lat(lat)`` in group ``/group1``,
    then the flattened dataset will contain dimension ``lat`` and
    variable ``group1__lat(lat)``, both in its root group. In this
    case, the ``_flattener_variable_map`` global attribute of the
    flattened dataset will contain the mapping ``'group1__lat:
    /group1/lat'``, and the ``_flattener_dimension_map`` global
    attribute will contain the mapping ``'lat: /lat'``.

    .. versionadded:: (cfdm) 1.11.2.0

    :Parameters:

        input_ds:
            The dataset to be flattened, that has the same API as
            `netCDF4.Dataset`, `h5netcdf.File`, or `zarr.Group`

        output_ds: `netCDF4.Dataset`
            A container for the flattened dataset.

        strict: `bool`, optional
            If True, the default, then failing to resolve a reference
            raises an exception. If False, a warning is issued and
            flattening is continued.

        omit_data: `bool`, optional
            If True then do not copy the data of any variables from
            *input_ds* to *output_ds*. This does not affect the amount
            of netCDF variables and dimensions that are written to the
            file, nor the netCDF variables' attributes, but for all
            variables it does not create data on disk or in
            memory. The resulting dataset will be smaller than it
            otherwise would have been, and when the new dataset is
            accessed the data of these variables will be represented
            by an array of all missing data. If False, the default,
            then all data arrays are copied.

        write_chunksize: `int`, optional
            When *omit_data* is False, the copying of data is done
            piecewise to keep memory usage down. *write_chunksize* is
            the size in bytes of how much data is copied from
            *input_ds* to *output_ds* for each piece. Ignored if
            *omit_data* is True.

    """
    _Flattener(
        input_ds,
        output_ds,
        strict,
        omit_data=omit_data,
        write_chunksize=write_chunksize,
    ).flatten()


def parse_attribute(name, attribute):
    """Parse variable attribute of any form into a dict:

     * 'time' -> {'time': []}
     * 'lat lon' -> {'lat': [], 'lon': []}
     * 'area: time volume: lat lon' -> {'area': ['time'], 'volume':
       ['lat', 'lon']}

    .. versionadded:: (cfdm) 1.11.2.0

    :Parameters:

        name: `str`
            The attribute name (e.g. ``'cell_methods'``).

        attribute: `str`
            The attribute value to parse.

    :Returns:

        `dict`
            The parsed string.

    """

    def subst(s):
        """Substitute tokens for WORD and SEP."""
        return s.replace("WORD", r"[A-Za-z0-9_#/.\(\)]+").replace(
            "SEP", r"(\s+|$)"
        )

    # Regex for 'dict form': "k1: v1 v2 k2: v3"
    pat_value = subst(r"(?P<value>WORD)SEP")
    pat_values = f"({pat_value})*"
    pat_mapping = subst(rf"(?P<mapping_name>WORD):SEP(?P<values>{pat_values})")
    pat_mapping_list = f"({pat_mapping})+"

    # Regex for 'list form': "v1 v2 v3" (including single-item form)
    pat_list_item = subst(r"(?P<list_item>WORD)SEP")
    pat_list = f"({pat_list_item})+"

    # Regex for any form:
    pat_all = subst(
        rf"((?P<list>{pat_list})|(?P<mapping_list>{pat_mapping_list}))$"
    )

    m = re.match(pat_all, attribute)

    # Output is always a dict. If input form is a list, dict values
    # are set as empty lists
    out = {}

    if m is not None:
        list_match = m.group("list")
        # Parse as a list
        if list_match:
            for mapping in re.finditer(pat_list_item, list_match):
                item = mapping.group("list_item")
                out[item] = None

        # Parse as a dict:
        else:
            mapping_list = m.group("mapping_list")
            for mapping in re.finditer(pat_mapping, mapping_list):
                term = mapping.group("mapping_name")
                values = [
                    value.group("value")
                    for value in re.finditer(
                        pat_value, mapping.group("values")
                    )
                ]
                out[term] = values
    else:
        raise AttributeParsingException(
            f"Error parsing {name!r} attribute with value {attribute!r}"
        )

    return out


def generate_var_attr_str(d):
    """Re-generate the attribute string from a dictionary.

    .. versionadded:: (cfdm) 1.11.2.0

    :Parameters:

        d: `dict`
            A resolved and parsed attribute.

    :Returns:

        `str`
            The flattened attribute value.

    """
    parsed_list = []
    for k, v in d.items():
        if v is None:
            parsed_list.append(k)
        elif not v:
            parsed_list.append(f"{k}:")
        else:
            parsed_list.append(f"{k}: {' '.join(v)}")

    return " ".join(parsed_list)


class _Flattener:
    """Information and methods needed to flatten a dataset.

    Contains the input file, the output file being flattened, and all
    the logic of the flattening process.

    .. versionadded:: (cfdm) 1.11.2.0

    """

    def __init__(
        self,
        input_ds,
        output_ds,
        strict=True,
        omit_data=False,
        write_chunksize=134217728,
    ):
        """**Initialisation**

        :Parameters:

            input_ds:
                The dataset to be flattened, that has the same API as
                `netCDF4.Dataset`, `h5netcdf.File`, or `zarr.Group`.

            output_ds: `netCDF4.Dataset`
                A container for the flattened dataset.

            strict: `bool`, optional
                See `netcdf_flatten`.

            omit_data: `bool`, optional
                See `netcdf_flatten`.

            write_chunksize: `int`, optional
                See `netcdf_flatten`.

        """
        # Mapping of flattened attribute names to their full-path
        # counterparts.
        #
        # E.g. ['Conventions: /Conventions']
        self._attr_map_value = []

        # Mapping of flattened dimension names to their full-path
        # counterparts
        #
        # E.g. ['bounds2: /bounds2',
        #       'x: /x',
        #       'forecast__y: /forecast/y']
        self._dim_map_value = []

        # Mapping of flattened variable names to their full-path
        # counterparts
        #
        # E.g. ['x_bnds: /x_bnds',
        #       'x: /x',
        #       'b_bounds: /b_bounds',
        #       'b: /b',
        #       'latitude_longitude: /latitude_longitude',
        #       'forecast__y: /forecast/y']
        self._var_map_value = []

        # Mapping of full-path dimension names to their flattened
        # counterparts
        #
        # E.g. {'/bounds2': 'bounds2',
        #       '/x': 'x',
        #       '/forecast/y': 'forecast__y'}
        self._dim_map = {}

        # Mapping of full-path variable names to their flattened
        # counterparts
        #
        # E.g. {'/x_bnds': 'x_bnds',
        #       '/x': 'x',
        #       '/b_bounds': 'b_bounds',
        #       '/b': 'b',
        #       '/latitude_longitude': 'latitude_longitude',
        #       '/forecast/y': 'forecast__y'}
        self._var_map = {}

        # Mapping of full-path group names to the dimensions defined
        # therein
        #
        # E.g. {'/': {'feature': <ZarrDimension: feature, size(58)>,
        #             'station': <ZarrDimension: station, size(3)>},
        #       '/forecast': {'element': <ZarrDimension: element, size(118)>},
        #       '/forecast/model': {}}
        self._group_to_dims = {}

        # Mapping of variable names to their Dimension objects.
        #
        # E.g. {'x': [<ZarrDimension: x, size(9)>],
        #       'x_bnds': [<ZarrDimension: x, size(9)>,
        #                  <ZarrDimension: bounds2, size(2)>],
        #       'latitude_longitude': [],
        #       'forecast/y': [<ZarrDimension: y, size(10)>]}
        self._var_to_dims = {}

        self._input_ds = input_ds
        self._output_ds = output_ds

        # Record the backend that defines 'input_ds'
        if hasattr(input_ds, "_h5file"):
            self._input_ds_backend = "h5netcdf"
        elif hasattr(input_ds, "data_model"):
            self._input_ds_backend = "netCDF4"
        elif hasattr(input_ds, "store"):
            self._input_ds_backend = "zarr"
        else:
            raise ValueError(
                "Unknown type of 'input_ds'. Must be one of h5netcdf.File, "
                f"netCDF4.Dataset, or zarr.Group. Got {type(input_ds)}"
            )

        self._strict = bool(strict)
        self._omit_data = bool(omit_data)
        self._write_chunksize = write_chunksize

        if (
            output_ds == input_ds
            or output_ds.filepath() == self.filepath(input_ds)
            or output_ds.data_model != "NETCDF4"
        ):
            raise ValueError(
                "Invalid inputs. Input and output datasets should "
                "be different, and output should be of the 'NETCDF4' format."
            )

        self._debug = is_log_level_debug(logger)

    def attrs(self, variable, dataset=None):
        """Return the variable attributes.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            variable:
                The variable object.

        :Returns:

            `dict`
                A dictionary of the attribute values keyed by their
                names.

        """
        match self._backend(dataset):
            case "netCDF4":
                return {
                    attr: variable.getncattr(attr)
                    for attr in variable.ncattrs()
                }

            case "h5netcdf" | "zarr":
                return dict(variable.attrs)

    def chunksizes(self, variable):
        """Return the variable chunk sizes.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            variable:
                The variable object.

        :Returns:

            `None` or sequence of `int`
                The chunksizes, or `None` if the variable is not
                chunked.

        **Examples**

        >>> f.chunksizes(variable)
        [1, 324, 432]

        >>> f.chunksizes(variable)
        None

        """
        match self._backend():
            case "h5netcdf" | "zarr":
                return variable.chunks

            case "netCDF4":
                chunking = variable.chunking()
                if chunking == "contiguous":
                    return

                return chunking

    def contiguous(self, variable):
        """Whether or not the variable data is contiguous on disk.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            variable:
                The variable object.

        :Returns:

            `bool`
                 `True` if the variable data is contiguous on disk,
                 otherwise `False`.

        **Examples**

        >>> f.contiguous(variable)
        False

        """
        match self._backend():
            case "h5netcdf" | "zarr":
                return variable.chunks is None

            case "netCDF4":
                return variable.chunking() == "contiguous"

    def dtype(self, variable):
        """Return the data type of a variable.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            variable:
                The variable object.

        :Returns:

            `numpy.dtype` or `str`
                 The data type.

        **Examples**

        >>> f.dtype(variable)
        dtype('<f8')

        >>> f.dtype(variable)
        str

        """
        from numpy.dtypes import StringDType

        out = variable.dtype
        if out in ("O", StringDType()):
            out = str

        return out

    def endian(self, variable):
        """Return the endian-ness of a variable.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            variable:
                The variable object.

        :Returns:

            `str`
                 The endian-ness (``'little'``, ``'big'``, or
                 ``'native'``) of the variable.

        **Examples**

        >>> f.endian(variable)
        'native'

        """
        match self._backend():
            case "h5netcdf" | "zarr":
                dtype = variable.dtype
                return _dtype_endian_lookup[getattr(dtype, "byteorder", None)]

            case "netCDF4":
                return variable.endian()

    def filepath(self, dataset):
        """Return the file path for the dataset.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            dataset:
                The dataset.

        :Returns:

            `str`
                The file system path, or the OPeNDAP URL, for the
                dataset.

        **Examples**

        >>> f.filepath(dataset)
        '/home/data/file.nc'

        """
        match self._backend():
            case "h5netcdf":
                return dataset.filename

            case "netCDF4":
                return dataset.filepath()

            case "zarr":
                return str(dataset.store_path)

    def get_dims(self, variable):
        """Return the dimensions associated with a variable.

        .. versionadded:: (cfdm) 1.11.2.0

        :Returns:

            `list` of dimension objects

        """
        match self._backend():
            case "netCDF4":
                return variable.get_dims()

            case "h5netcdf":
                dims = {}
                dimension_names = list(variable.dimensions)
                group = variable._parent
                for name, dim in group.dims.items():
                    if name in dimension_names:
                        dims[name] = dim
                        dimension_names.remove(name)

                group = group.parent
                while group is not None and dimension_names:
                    for name, dim in group.dims.items():
                        if name in dimension_names:
                            dims[name] = dim
                            dimension_names.remove(name)

                    group = group.parent

                return [dims[name] for name in variable.dimensions]

            case "zarr":
                return tuple(self._var_to_dims[variable.name])

    def getncattr(self, x, attr):
        """Retrieve a netCDF attribute.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            x: variable, group, or dataset

            attr: `str`

        :Returns:

        """
        match self._backend():
            case "h5netcdf" | "zarr":
                return x.attrs[attr]

            case "netCDF4":
                return getattr(x, attr)

    def group(self, x):
        """Return the group that a variable or dimension belongs to.

        .. versionadded:: (cfdm) 1.11.2.0

        :Returns:

            `Group`

        """
        match self._backend():
            case "netCDF4":
                return x.group()

            case "h5netcdf":
                return x._parent

            case "zarr":
                try:
                    # Variable
                    group_name = group_separator.join(
                        x.path.split(group_separator)[:-1]
                    )
                    return self._input_ds[group_name]
                except AttributeError:
                    # Dimension
                    return x.group()

    def name(self, x, dataset=None):
        """Return the netCDF name, without its groups.

        .. versionadded:: (cfdm) 1.11.2.0

        :Returns:

            `str`

        """
        match self._backend(dataset):
            case "h5netcdf" | "netCDF4":
                return x.name.split(group_separator)[-1]

            case "zarr":
                try:
                    # Variable
                    return x.path.split(group_separator)[-1]
                except AttributeError:
                    # Dimension
                    return x.name.split(group_separator)[-1]

    def ncattrs(self, x):
        """Return netCDF attribute names.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            x: variable, group, or dataset

        :Returns:

            `list`

        """
        match self._backend():
            case "h5netcdf" | "zarr":
                return list(x.attrs)

            case "netCDF4":
                return x.ncattrs()

    def parent(self, group):
        """Return the parent group.

        .. versionadded:: (cfdm) 1.11.2.0

        :Returns:

            `Group` or `None`
                The parent group, or `None` if *group* is the root
                group (and so has no parent).

        """
        match self._backend():
            case "h5netcdf" | "netCDF4":
                return group.parent

            case "zarr":
                name = group.name
                if name == group_separator:
                    return

                return self._input_ds[
                    group_separator.join(name.split(group_separator)[:-1])
                ]

    def path(self, group):
        """Return a simulated unix directory path to a group.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            group:
                The group object.

        :Returns:

            `str`

        """
        match self._backend():
            case "h5netcdf" | "zarr":
                try:
                    return group.name
                except AttributeError:
                    return group_separator

            case "netCDF4":
                return group.path

    def flatten(self):
        """Flattens and writes to output file.

        .. versionadded:: (cfdm) 1.11.2.0

        :Return:

            `None`

        """
        input_ds = self._input_ds
        output_ds = self._output_ds

        if self._debug:
            logger.debug(
                f"Flattening the groups of {self.filepath(input_ds)}"
            )  # pragma: no cover

        # Flatten product
        self.process_group(input_ds)

        # Add name mapping attributes
        output_ds.setncattr(flattener_attribute_map, self._attr_map_value)
        output_ds.setncattr(flattener_dimension_map, self._dim_map_value)
        output_ds.setncattr(flattener_variable_map, self._var_map_value)

        # Browse flattened variables to rename references:
        if self._debug:
            logger.debug(
                "    Browsing flattened variables to rename references "
                "in attributes"
            )  # pragma: no cover

        for var in output_ds.variables.values():
            self.adapt_references(var)

    def process_group(self, input_group):
        """Flattens a given group to the output file.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            input_group:
                The group object to flatten.

        :Returns:

            `None`

        """
        if self._debug:
            logger.debug(
                f"    Browsing group {self.path(input_group)}"
            )  # pragma: no cover

        for attr_name in self.ncattrs(input_group):
            self.flatten_attribute(input_group, attr_name)

        #        for dim in input_group.dimensions.values():
        #            self.flatten_dimension(dim)

        for dim in self._dimensions(input_group).values():
            self.flatten_dimension(dim)
        #        for var in input_group.variables.values():
        #            self.flatten_variable(var)

        for var in self._variables(input_group).values():
            self.flatten_variable(var)

        #        for child_group in input_group.groups.values():
        #            self.process_group(child_group)

        for child_group in self._child_groups(input_group).values():
            self.process_group(child_group)

    def flatten_attribute(self, input_group, attr_name):
        """Flattens a given attribute from a group to the output file.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            input_group:
                The group object containing the attribute to flatten.

            attr_name: `str`
                The name of the attribute.

        :Returns:

            `None`

        """
        # Create new name
        new_attr_name = self.generate_flattened_name(input_group, attr_name)

        if self._debug:
            logger.debug(
                f"        Creating global attribute {new_attr_name!r} from "
                f"group {self.path(input_group)}"
            )  # pragma: no cover

        # Write attribute
        self._output_ds.setncattr(
            new_attr_name, self.getncattr(input_group, attr_name)
        )

        # Store new naming for later and in mapping attribute
        self._attr_map_value.append(
            self.generate_mapping_str(input_group, attr_name, new_attr_name)
        )

    def flatten_dimension(self, dim):
        """Flattens a given dimension to the output file.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            dim:
                The dimension object to flatten.

        :Returns:

            `None`

        """
        # logger.debug(
        #    f"    Creating dimension {self.name(dim)!r} from "
        #    f"group {self.path(self.group(dim))} to root"
        # )

        # Create new name
        group = self.group(dim)
        name = self.name(dim)
        new_name = self.generate_flattened_name(group, name)

        if self._debug:
            logger.debug(
                f"        Creating dimension {new_name!r} from "
                f"group {self.path(group)!r}"
            )  # pragma: no cover

        # Write dimension
        self._output_ds.createDimension(
            new_name, (len(dim), None)[dim.isunlimited()]
        )

        # Store new name in dict for resolving references later
        self._dim_map[self.pathname(group, name)] = new_name

        # Add to name mapping attribute
        self._dim_map_value.append(
            self.generate_mapping_str(group, name, new_name)
        )

    def flatten_variable(self, var):
        """Flattens a given variable to the output file.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            var:
                The variable object.

        :Returns:

            `None`

        """
        # logger.debug(
        #    f"    Copying variable {self.name(var)!r} from "
        #    f"group {self.path(self.group(var))} to root"
        # )

        # Create new name
        new_name = self.generate_flattened_name(
            self.group(var), self.name(var)
        )

        # Replace old by new dimension names
        new_dims = list(
            map(
                lambda x: self._dim_map[
                    self.pathname(self.group(x), self.name(x))
                ],
                self.get_dims(var),
            )
        )

        # Write variable
        if self._debug:
            logger.debug(
                f"        Creating variable {new_name!r} from "
                f"{self.pathname(self.group(var), self.name(var))!r}"
            )  # pragma: no cover

        attributes = self.attrs(var)

        omit_data = self._omit_data
        if omit_data:
            fill_value = False
        else:
            fill_value = attributes.pop("_FillValue", None)

        #        print ( new_name, self.get_dims(var), new_dims, self.chunksizes(var))
        new_var = self._output_ds.createVariable(
            new_name,
            self.dtype(var),
            new_dims,
            zlib=False,
            complevel=4,
            shuffle=True,
            fletcher32=False,
            contiguous=self.contiguous(var),
            chunksizes=self.chunksizes(var),
            endian=self.endian(var),
            least_significant_digit=None,
            fill_value=fill_value,
        )

        if not omit_data:
            self.write_data_in_chunks(var, new_var)

        # Copy attributes
        new_var.setncatts(attributes)

        # Store new name in dict for resolving references later
        self._var_map[self.pathname(self.group(var), self.name(var))] = (
            new_name
        )

        # Add to name mapping attribute
        self._var_map_value.append(
            self.generate_mapping_str(
                self.group(var), self.name(var), new_name
            )
        )

        # Resolve references in variable attributes and replace by
        # absolute path
        self.resolve_references(new_var, var)

    def increment_pos(self, pos, dim, copy_slice_shape, var_shape):
        """Increment position.

        Increment position vector in a variable along a dimension by
        the matching slice length along that dimension. If end of the
        dimension is reached, recursively increment the next
        dimensions until a valid position is found.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            pos: `list`
                The current slice position along each dimension of the
                array.

            dim: `int`
                The position of the array dimension to be incremented.

            copy_slice_shape: `list`
                The shape of the copy slice.

            var_shape: `tuple`
                The shape of the whole variable.

        :Returns:

            `bool`
                `True` if a valid position is found within the
                variable, `False` otherwise.

        """
        # Try to increment dimension
        pos[dim] += copy_slice_shape[dim]

        # Test new position
        dim_end_reached = pos[dim] > var_shape[dim]
        var_end_reached = (dim + 1) >= len(copy_slice_shape)

        # End of this dimension not reached yet
        if not dim_end_reached:
            return True

        # End of this dimension reached. Reset to 0 and try increment
        # next one recursively
        elif dim_end_reached and not var_end_reached:
            pos[: dim + 1] = [0 for j in range(dim + 1)]
            return self.increment_pos(
                pos, dim + 1, copy_slice_shape, var_shape
            )

        else:
            # End of this dimension reached, and no dimension to
            # increment. Finish.
            return False

    def write_data_in_chunks(self, old_var, new_var):
        """Copy the data of a variable to a new one by slice.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            old_var:
                The variable object where the data should be copied
                from.

            new_var:
                The new variable object in which to copy the data.

        :Returns:

            `None`

        """
        ndim = old_var.ndim
        shape = old_var.shape
        chunk_shape = (
            (self.write_chunksize // (old_var.dtype.itemsize * ndim)),
        ) * ndim

        if self._debug:
            logger.debug(
                f"        Copying {self.name(old_var)!r} data in chunks of "
                f"{chunk_shape}"
            )  # pragma: no cover

        # Initial position vector
        pos = [0] * ndim

        # Copy in slices until end reached
        var_end_reached = False
        while not var_end_reached:
            # Create current slice
            current_slice = tuple(
                slice(pos[dim_i], min(shape[dim_i], pos[dim_i] + dim_l))
                for dim_i, dim_l in enumerate(chunk_shape)
            )

            # Copy data in slice
            new_var[current_slice] = old_var[current_slice]

            # Get next position
            var_end_reached = not self.increment_pos(
                pos, 0, chunk_shape, shape
            )

    def resolve_reference(self, orig_ref, orig_var, rules):
        """Resolve a reference.

        Resolves the absolute path to a coordinate variable within the
        group structure.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            orig_ref: `str`
                The reference to resolve.

            orig_var:
                The original variable object containing the reference.

            rules: `FlatteningRules`
                The flattening rules that apply to the reference.

        :Returns:

            `str`
                The absolute path to the reference.

        """
        ref = orig_ref
        absolute_ref = None
        ref_type = ""

        ref_to_dim = rules.ref_to_dim
        ref_to_var = rules.ref_to_var

        # Resolve first as dim (True), or var (False)
        resolve_dim_or_var = ref_to_dim > ref_to_var

        # Resolve var (resp. dim) if resolving as dim (resp. var) failed
        resolve_alt = ref_to_dim and ref_to_var

        # Reference is already given by absolute path
        if ref.startswith(group_separator):
            method = "Absolute"
            absolute_ref = ref

        # Reference is given by relative path
        elif group_separator in ref:
            method = "Relative"

            # First tentative as dim OR var
            if resolve_dim_or_var:
                ref_type = "dimension"
            else:
                ref_type = "variable"

            absolute_ref = self.search_by_relative_path(
                orig_ref, self.group(orig_var), resolve_dim_or_var
            )

            # If failed and alternative possible, second tentative
            if absolute_ref is None and resolve_alt:
                if resolve_dim_or_var:
                    ref_type = "variable"
                else:
                    ref_type = "dimension"

                absolute_ref = self.search_by_relative_path(
                    orig_ref, self.groupp(orig_var), not resolve_dim_or_var
                )

        # Reference is to be searched by proximity
        else:
            method = "Proximity"
            absolute_ref, ref_type = self.resolve_reference_proximity(
                ref,
                resolve_dim_or_var,
                resolve_alt,
                orig_var,
                rules,
            )

        # Post-search checks and return result
        return self.resolve_reference_post_processing(
            absolute_ref,
            orig_ref,
            orig_var,
            rules,
            ref_type,
            method,
        )

    def resolve_reference_proximity(
        self, ref, resolve_dim_or_var, resolve_alt, orig_var, rules
    ):
        """Resolve reference: search by proximity.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            ref: `str`
                The reference to resolve.

            resolve_dim_or_var: `bool`
                Try to resolve first as dimension (True), or else as
                variable (False).

            resolve_alt: `bool`
                Resolve as variable if resolving as dimension failed,
                and vice versa.

            orig_var:
                The original variable object containing the reference.

            rules: `FlatteningRules`
                The flattening rules that apply to the reference.

        :Returns:

            (`str` or `None, str)
                The resolved reference (or `None` if unresolved), and
                the type of reference (either ``'dimension'`` or
                ``'variable'``).

        """
        # First tentative as dim OR var
        if resolve_dim_or_var:
            ref_type = "dimension"
        else:
            ref_type = "variable"

        stop_at_local_apex = rules.stop_at_local_apex

        resolved_var = self.search_by_proximity(
            ref,
            self.group(orig_var),
            resolve_dim_or_var,
            False,
            stop_at_local_apex,
        )

        # If failed and alternative possible, second tentative
        if resolved_var is None and resolve_alt:
            if resolve_dim_or_var:
                ref_type = "variable"
            else:
                ref_type = "dimension"

            resolved_var = self.search_by_proximity(
                ref,
                self.group(orig_var),
                not resolve_dim_or_var,
                False,
                stop_at_local_apex,
            )

        # If found, create ref string
        if resolved_var is not None:
            return (
                self.pathname(
                    self.group(resolved_var), self.name(resolved_var)
                ),
                ref_type,
            )

        # Unresolved
        return None, ""

    def resolve_reference_post_processing(
        self, absolute_ref, orig_ref, orig_var, rules, ref_type, method
    ):
        """Post-processing operations after resolving reference.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            absolute_ref: `str`
                The absolute path of the reference.

            orig_ref: `str`
                The original reference.

            orig_var:
                The original variable object containing the reference.

            rules: `FlatteningRules`
                The flattening rules that apply to the reference.

            ref_type: `str`
                the type of reference (either ``'dimension'`` or
                ``'variable'``).

            method: `str`
                The method of reference resolution (either
                ``'proximity'`` or ``'absolute'``).

        :Returns:

            `str`
                The absolute reference.

        """
        # If not found and accept standard name, assume standard name
        if absolute_ref is None and rules.accept_standard_names:
            if self._debug:
                logger.debug(
                    f"            Reference to {orig_ref!r} not "
                    "resolved. Assumed to be a standard name."
                )  # pragma: no cover

            ref_type = "standard_name"
            absolute_ref = orig_ref
        elif absolute_ref is None:
            # Not found, so raise exception.
            absolute_ref = self.handle_reference_error(
                rules.name, orig_ref, self.path(self.group(orig_var))
            )
        else:
            # Found
            if self._debug:
                logger.debug(
                    f"            {method} reference to {ref_type} "
                    f"{orig_ref!r} resolved as {absolute_ref!r}"
                )  # pragma: no cover

        # If variables refs are limited to coordinate variable,
        # additional check
        if (
            ref_type == "variable"
            and rules.limit_to_scalar_coordinates
            and (
                (
                    "coordinates" not in self.ncattrs(orig_var)
                    or orig_ref not in self.getncattr(orig_var, "coordinates")
                )
                or self._input_ds[absolute_ref].ndim > 0
            )
        ):
            if self._debug:
                logger.debug(
                    f"            Reference to {orig_ref!r} is not a scalar "
                    "coordinate variable. Assumed to be a standard name."
                )  # pragma: no cover

            absolute_ref = orig_ref

        # Return result
        return absolute_ref

    def search_by_relative_path(self, ref, current_group, search_dim):
        """Search by relative path.

        Resolves the absolute path to a reference within the group
        structure, using search by relative path.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            ref: `str`
                The reference to resolve.

            current_group:
                The current group object of the reference.

            search_dim: `bool`
                If True then search for a dimension, otherwise a
                variable.

        :Returns:

            `str`
                The absolute path to the variable.

        """
        # Go up parent groups
        while ref.startswith(f"..{group_separator}"):
            parent = self.parent(current_group)
            if parent is None:
                return

            ref = ref[3:]
            current_group = parent

        # Go down child groups
        ref_split = ref.split(group_separator)
        for g in ref_split[:-1]:
            try:
                current_group = self._child_groups(current_group)[g]
            except KeyError:
                return

        # Get variable or dimension
        if search_dim:
            elt = tuple(self._dimensions(current_group))[ref_split[-1]]

        else:
            elt = tuple(self._variables(current_group))[ref_split[-1]]

        # Get absolute reference
        return self.pathname(self.group(elt), self.name(elt))

    def search_by_proximity(
        self,
        ref,
        current_group,
        search_dim,
        local_apex_reached,
        is_coordinate_variable,
    ):
        """Search by proximity.

        Resolves the absolute path to a reference within the group
        structure, using search by proximity.

        First search up in the hierarchy for the reference, until root
        group is reached. If coordinate variable, search until local
        apex is reached, then search down in siblings.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            ref: `str`
                The reference to resolve.

            current_group:
                The current group object where searching.

            search_dim: `bool`
                If True then search for a dimension, otherwise a
                variable.

            local_apex_reached: `bool`
                Whether or not the apex has previously been reached.

            is_coordinate_variable: `bool`
                Whether the search is for a coordiante variable.

        :Returns:

            `str` or `None`
                The absolute path to the variable, if found, otherwise
                `None`.

        """
        if search_dim:
            #            dims_or_vars = current_group.dimensions # TODOZARR
            dims_or_vars = self._dimensions(current_group)
        else:
            #            dims_or_vars = current_group.variables
            dims_or_vars = self._variables(current_group)

        # Found in current group
        if ref in dims_or_vars:  # .keys():
            return dims_or_vars[ref]

        local_apex_reached = (
            # local_apex_reached or ref in current_group.dimensions.keys()
            local_apex_reached
            or ref
            in dims_or_vars  # TODOZARR self._dimensions(current_group).keys()
        )

        # Check if have to continue looking in parent group
        # - normal search: continue until root is reached
        # - coordinate variable: continue until local apex is reached
        parent_group = self.parent(current_group)
        if is_coordinate_variable:
            #            top_reached = local_apex_reached or current_group.parent is None
            top_reached = local_apex_reached or parent_group is None
        else:
            #            top_reached = current_group.parent is None
            top_reached = parent_group is None

        # Search up
        if not top_reached:
            return self.search_by_proximity(
                ref,
                parent_group,
                search_dim,
                local_apex_reached,
                is_coordinate_variable,
            )

        elif is_coordinate_variable and local_apex_reached:
            # Coordinate variable and local apex reached, so search
            # down in siblings.
            found_elt = None
            #            for child_group in current_group.groups.values():
            for child_group in self._child_groups(current_group).values():
                found_elt = self.search_by_proximity(
                    ref,
                    child_group,
                    search_dim,
                    local_apex_reached,
                    is_coordinate_variable,
                )
                if found_elt is not None:
                    break

            return found_elt

        # Did not find
        return

    def resolve_references(self, var, old_var):
        """Resolve references.

        In a given variable, replace all references to other variables
        in its attributes by absolute references.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            var:
                The flattened variable object in which references
                should be renamed with absolute references.

            old_var:
                The original variable object (in group structure).

        :Returns:

            `None`

        """
        var_attrs = self.attrs(var, "output")
        for name in referencing_attributes.intersection(var_attrs):
            # Parse attribute value
            parsed_attribute = parse_attribute(name, var_attrs[name])

            # Resolved references in parsed as required by attribute
            # properties
            resolved_parsed_attr = {}

            rules = flattening_rules[name]
            resolve_key = rules.resolve_key
            resolve_value = rules.resolve_value

            for k, v in parsed_attribute.items():
                if resolve_key:
                    k = self.resolve_reference(k, old_var, rules)

                if resolve_value and v is not None:
                    v = [self.resolve_reference(x, old_var, rules) for x in v]

                resolved_parsed_attr[k] = v

            # Re-generate attribute value string with resolved
            # references
            var.setncattr(name, generate_var_attr_str(resolved_parsed_attr))

    def adapt_references(self, var):
        """Adapt references.

        In a given variable, replace all references to variables in
        attributes by references to the new names in the flattened
        netCDF. All references have to be already resolved as absolute
        references.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            var:
                The flattened variable object in which references
                should be renamed with new names.

        :Returns:

            `None`

        """
        var_attrs = self.attrs(var, "output")
        for name in referencing_attributes.intersection(var_attrs):
            # Parse attribute value
            value = var_attrs[name]
            parsed_attribute = parse_attribute(name, value)

            adapted_parsed_attr = {}

            rules = flattening_rules[name]
            resolve_key = rules.resolve_key
            resolve_value = rules.resolve_value

            for k, v in parsed_attribute.items():
                if resolve_key:
                    k = self.adapt_name(k, rules)

                if resolve_value and v is not None:
                    v = [self.adapt_name(x, rules) for x in v]

                adapted_parsed_attr[k] = v

            new_attr_value = generate_var_attr_str(adapted_parsed_attr)
            var.setncattr(name, new_attr_value)

            if self._debug:
                logger.debug(
                    "        Value of attribute "
                    f"{self.name(var, 'output')}.{name} "
                    f"changed from {value!r} to {new_attr_value!r}"
                )  # pragma: no cover

    def adapt_name(self, resolved_ref, rules):
        """Apapt the name.

        Return name of flattened reference. If not found, raise
        exception or continue with a warning.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            resolved_ref: `str`
                The resolved reference.

            rules: `FlatteningRules`
                The flattening rules that apply to the reference.

        :Returns:

            `str`
                The adapted reference.

        """
        # If ref contains Error message, leave as such
        if ref_not_found_error in resolved_ref:
            return resolved_ref

        ref_to_dim = rules.ref_to_dim
        ref_to_var = rules.ref_to_var

        # Select highest priority map
        if ref_to_dim > ref_to_var:
            name_mapping = self._dim_map

        if ref_to_dim < ref_to_var:
            name_mapping = self._var_map

        # Try to find mapping
        try:
            return name_mapping[resolved_ref]

        # If not found, look in other map if allowed
        except KeyError:
            if ref_to_dim and ref_to_var:
                if ref_to_dim < ref_to_var:
                    name_mapping = self._dim_map
                else:
                    name_mapping = self._var_map

                try:
                    return name_mapping[resolved_ref]
                except KeyError:
                    pass

        # If still not found, check if any standard name is allowed
        if rules.accept_standard_names:
            return resolved_ref

        else:
            # If not found, raise exception
            return self.handle_reference_error(rules.name, resolved_ref)

    def pathname(self, group, name=None):
        """Compose full path name to an element in a group structure.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            current_group:
                The group object containing the dimension or variable.

            name: `str`
                The name of the dimension or variable.

        :Returns:

            `str`
                The absolute path to the dimension or variable

        """
        if self.parent(group) is None:
            return group_separator + name

        return group_separator.join((self.path(group), name))

    def generate_mapping_str(self, input_group, name, new_name):
        """Generate string mapping.

        Generates a string representing the name mapping of an element
        before and after flattening.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            input_group:
                The group object containing the non-flattened
                dimension or variable.

            name: `str`
                The name of the non-flattened dimension or variable.

            new_name: `str`
                The name of the flattened dimension or variable.

        :Returns:

            `str`
                A string representing the name mapping for the
                dimension or variable.

        """
        original_pathname = self.pathname(input_group, name)
        return f"{new_name}: {original_pathname}"

    def convert_path_to_valid_name(self, pathname):
        """Generate valid name from path.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            pathname: `str`
                The non-flattened namepath to a dimension or variable.

            new_name: `str`
                A flattened version of *pathname*.
        :Returns:

            `str`
                The valid netCDF name.

        """
        return pathname.replace(group_separator, "", 1).replace(
            group_separator, flattener_separator
        )

    def generate_flattened_name(self, input_group, orig_name):
        """Convert full path of an element to a valid NetCDF name.

        * The name of an element is the concatenation of its
          containing group and its name;

        * replaces ``/`` from paths (forbidden as NetCDF name);

        * if name is longer than 255 characters, replace path to group
          by hash;

        * if name is still too long, replace complete name by hash.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            input_group:
                The group object containing the dimension or variable.

            orig_name: `str`
                The original name of the dimension or variable.

        :Returns:

            `str`
                The new valid name of the dimension or variable.

        """
        # If element is at root: no change
        if self.parent(input_group) is None:
            new_name = orig_name

        # If element in child group, concatenate group path and
        # element name
        else:
            full_name = (
                self.convert_path_to_valid_name(self.path(input_group))
                + flattener_separator
                + orig_name
            )
            new_name = full_name

            # If resulting name is too long, hash group path
            if len(new_name) >= max_name_len:
                group_hash = hashlib.sha1(
                    self.path(input_group).encode("UTF-8")
                ).hexdigest()
                new_name = group_hash + flattener_separator + orig_name

                # If resulting name still too long, hash everything
                if len(new_name) >= max_name_len:
                    new_name = hashlib.sha1(
                        full_name.encode("UTF-8")
                    ).hexdigest()

        return new_name

    def handle_reference_error(self, role, ref, context=None):
        """Handle reference error.

        Depending on the `_strict` mode, either raise an exception or
        log a warning. If not strict then a reference placeholder is
        returned.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            role: `str`
                The CF role of the reference,
                e.g. ``'instance_dimension'``, ``'cell_measures'``.

            ref: `str`
                The reference.

            context: `str`
                Additional context information to add to message.

        :Returns:

            `str`
                The error message, or if `_strict` is `True` then an
                `UnresolvedReferenceException` is raised.

        """
        message = f"{role} reference {ref!r} could not be resolved"
        if context is not None:
            message = f"{message} from {context}"

        if self._strict:
            raise UnresolvedReferenceException(message)

        warnings.warn(message)
        return f"{ref_not_found_error}_{ref}"

    def _dimensions(self, group):
        """Return dimensions that are defined in this group.

        .. versionadded:: (cfdm) NEXTVERSION

        :Parameters:

            group:
                The group object.

        :Returns:

            `dict`-like
                The dimensions defined in the group, keyed by the
                group name.

        """
        match self._backend():
            case "h5netcdf" | "netCDF4":
                return group.dimensions

            case "zarr":
                group_name = self.path(group)
                if group_name not in self._group_to_dims:
                    # Populate the `_group_to_dims` dictionary (we
                    # should only to this once per call of `flatten`)
                    self._populate_group_to_dims(group)

                return self._group_to_dims[group_name]

    def _variables(self, group):
        """Return variables that are defined in this group.

        .. versionadded:: (cfdm) NEXTVERSION

        :Parameters:

            group:
                The group object.

        :Returns:

            `dict`-like
                The variables, keyed by their names.

        """
        match self._backend():
            case "h5netcdf" | "netCDF4":
                return group.variables

            case "zarr":
                return dict(group.arrays())

    def _populate_group_to_dims(self, group):
        """Populate the `self._group_to_dims` dictionary.

        For the given group and all of its child groups, a mapping of
        full-path group names to the unique dimensions implied by the
        varibles therein will be added to `self._group_to_dims`. For
        instance::

           {'/': {'feature': <ZarrDimension: feature, size(58)>,
                  'station': <ZarrDimension: station, size(3)>},
            '/forecast': {'element': <ZarrDimension: element, size(118)>},
            '/forecast/model': {}}

        **Zarr**

        This is only required for a Zarr grouped dataset, for which
        this information is not explicitly defined in the format's
        data model (unlike for netCDF-3 and netCDF-4 datasets).

        To create the mapping, we need to impose an understanding of
        CF dimensions and groups onto the contents of the Zarr
        dataset:

        * A dimension name which contains no '/' (group separator)
          characters is assumed assumed to be the same logical
          dimension object as one with the same name and same size in
          one of its parent groups, if one exists. When multiple
          parents contain the dimension name, the parent closest to
          the root dimension is used.

        * An exception is raised if a dimension name ends with '/'.

        .. versionadded:: (cfdm) NEXTVERSION

        :Parameters:

            group:
                The group object.

        :Returns:

            `None`

        """
        from ..zarr import ZarrDimension

        group_name = self.path(group)

        input_ds = self._input_ds
        var_to_dims = self._var_to_dims

        group_to_dims = self._group_to_dims
        group_to_dims.setdefault(group_name, {})

        # Loop over variables in this group, sorted by variable name.
        for v in dict(sorted(group.arrays())).values():
            dimension_names = v.metadata.dimension_names
            if dimension_names is None:
                # Scalar variable has no dimensions
                var_to_dims[v.name] = []
                continue

            # Loop over this variable's dimension names
            for name, size in zip(dimension_names, v.shape):
                name_split = name.split(group_separator)
                basename = name_split[-1]

                if group_separator not in name:
                    # ------------------------------------------------
                    # Relative path dimension name which contains no
                    # '/' characters and which has no upward path
                    # traversals
                    #
                    # E.g. "dim"
                    #
                    # We're looking for a dimension with the same name
                    # and same size in one of its parent groups, if
                    # one exists. If multiple parents contain it, the
                    # parent closest to the root dimension is chosen.
                    # ------------------------------------------------
                    found_dim_in_parent = False
                    group_split = group_name.split(group_separator)
                    for n in range(1, len(group_split)):
                        parent_group = input_ds[
                            group_separator.join(group_split)[:n]
                        ]
                        g = self.path(parent_group)
                        # Loop over variables in the parent group,
                        # sorted by variable name.
                        for parent_v in dict(
                            sorted(parent_group.arrays())
                        ).values():
                            dimensions2 = parent_v.metadata.dimension_names
                            if dimensions2 is None or name not in dimensions2:
                                continue

                            zd = group_to_dims[g].get(basename)
                            if zd is not None and zd.size == size:
                                # Dimension 'basename' is already
                                # defined in 'parent_group'
                                found_dim_in_parent = True
                                break

                        if found_dim_in_parent:
                            # Dimension 'basename' is already defined
                            # in a parent group
                            break

                    if not found_dim_in_parent:
                        # Dimension 'basename' could not be matched to
                        # any parent group dimensions, so it needs to
                        # be defined in 'group'.
                        g = group_name

                else:
                    g = group_separator.join(name_split[:-1])
                    if name.startswith(group_separator):
                        # --------------------------------------------
                        # Absolute path dimension name
                        #
                        # E.g. "/group1/group2/dim"
                        # E.g. "/dim"
                        # --------------------------------------------
                        if g == "":
                            g = group_separator

                    elif name.startswith(f"..{group_separator}"):
                        # --------------------------------------------
                        # Relative path dimension name with upward
                        # path traversals at the start of the name
                        #
                        # E.g. "../group1/group2/dim"
                        # E.g. "../../group1/group2/dim"
                        # --------------------------------------------
                        current_group = group
                        while g.startswith(f"..{group_separator}"):
                            parent_group = self.parent(current_group)
                            current_group = parent_group
                            g = g[3:]
                            if parent_group is None:
                                # We've gone beyond the root group!
                                raise DimensionParsingException(
                                    "Unresolvable upward path traversals "
                                    f"in dimension name: {name!r} "
                                    f"(group {group_name!r}, "
                                    f"variable {v.name!r})"
                                )

                        g = group_separator.join((self.path(current_group), g))

                    elif name.endswith(group_separator):
                        # --------------------------------------------
                        # E.g. g = "/group1/group2/"
                        # --------------------------------------------
                        raise DimensionParsingException(
                            "Dimension names can not end with the group "
                            f"separator {group_separator!r}: {name!r} "
                            f"(group {group_name!r}, variable {v.name!r})"
                        )

                    elif f"..{group_separator}" in name:
                        # --------------------------------------------
                        # Relative path dimension name with upward
                        # path traversals not at the start of the name
                        #
                        # E.g. "/group1/../group2/dim"
                        # E.g. "../group1/../group2/dim"
                        # --------------------------------------------
                        raise DimensionParsingException(
                            "In Zarr datasets, can't yet deal with a "
                            "relative path dimension name with upward path "
                            f"traversals in middle of the name: {name!r} "
                            f"(group {group_name!r}, variable {v.name!r}). "
                            "Please raise an issue at "
                            "https://github.com/NCAS-CMS/cfdm/issues "
                            "if you really do need this feature."
                        )

                    else:
                        # --------------------------------------------
                        # Relative path dimension name which contain
                        # '/' and which has no upward path traversals
                        #
                        # E.g. "group2/group3"
                        # --------------------------------------------
                        g = group_separator.join((group_name, g))

                if g in group_to_dims:
                    zd = group_to_dims[g].get(basename)
                    if zd is not None:
                        # Dimension 'basename' is already defined
                        if zd.size != size:
                            raise DimensionParsingException(
                                f"Dimension {name!r} of variable {v.name!r} "
                                f"has the wrong size ({size!r}). It should "
                                f"match the size of dimension {basename!r} "
                                f"in group {group_name!r} ({zd.size})"
                            )

                        var_to_dims.setdefault(v.name, []).append(zd)
                        continue
                else:
                    group_to_dims[g] = {}

                # Still here? Then we're ready to define dimension
                # 'basename'
                zd = ZarrDimension(basename, size, input_ds[g])
                var_to_dims.setdefault(v.name, []).append(zd)
                group_to_dims[g][basename] = zd

        # Recursively scan all child groups
        for g in group.group_values():
            self._populate_group_to_dims(g)

    def _child_groups(self, group):
        """Return groups that are defined in this group.

        .. versionadded:: (cfdm) NEXTVERSION

        :Parameters:

            group:
                The group object.

        :Returns:

            `dict`-like
                The groups, keyed by their names.

        """
        match self._backend():
            case "h5netcdf" | "netCDF4":
                return group.groups

            case "zarr":
                return dict(group.groups())

    def _backend(self, dataset=None):
        """Return the name of the backend that defines a dataset.

        .. versionadded:: (cfdm) NEXTVERSION

        :Parameters:

            dataset: `str` or `None`
                If set to ``'output'`` then the name of the output
                dateset backend will be returned. If `None` (the
                default) then the name of backend that defines the
                input dataset is returned.

        :Returns:

            `str`
                The backend name.

        """
        if dataset is None:
            return self._input_ds_backend

        if dataset == "output":
            return "netCDF4"

        raise ("Bad value of 'dataset'")


class AttributeParsingException(Exception):
    """Exception for unparsable attribute.

    .. versionadded:: (cfdm) 1.11.2.0

    """

    pass


class DimensionParsingException(Exception):
    """Exception for unparsable dimension.

    .. versionadded:: (cfdm) NEXTVERSION

    """

    pass


class UnresolvedReferenceException(Exception):
    """Exception for unresolvable references in attributes.

    .. versionadded:: (cfdm) 1.11.2.0

    """

    pass
