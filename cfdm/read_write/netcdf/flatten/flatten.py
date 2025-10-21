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
    """Create a flattened version of a grouped netCDF dataset.

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
            `netCDF4.Dataset` or `h5netcdf.File`.

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
    """Information and methods needed to flatten a netCDF dataset.

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
                `netCDF4.Dataset` or `h5netcdf.File`.

            output_ds: `netCDF4.Dataset`
                A container for the flattened dataset.

            strict: `bool`, optional
                See `netcdf_flatten`.

            omit_data: `bool`, optional
                See `netcdf_flatten`.

            write_chunksize: `int`, optional
                See `netcdf_flatten`.

        """
        self._attr_map_value = []
        self._dim_map_value = []
        self._var_map_value = []

        self._dim_map = {}
        self._var_map = {}

        self._input_ds = input_ds
        self._output_ds = output_ds
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

    def attrs(self, variable):
        """Return the variable attributes.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            variable:
                The variable, that has the same API as
                `netCDF4.Variable` or `h5netcdf.Variable`.

        :Returns:

            `dict`
                A dictionary of the attribute values keyed by their
                names.

        """
        try:
            # h5netcdf
            return dict(variable.attrs)
        except AttributeError:
            # netCDF4
            return {
                attr: variable.getncattr(attr) for attr in variable.ncattrs()
            }

    def chunksizes(self, variable):
        """Return the variable chunk sizes.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            variable:
                The variable, that has the same API as
                `netCDF4.Variable` or `h5netcdf.Variable`.

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
        try:
            # netCDF4
            chunking = variable.chunking()
            if chunking == "contiguous":
                return None

            return chunking
        except AttributeError:
            # h5netcdf
            return variable.chunks

    def contiguous(self, variable):
        """Whether or not the variable data is contiguous on disk.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            variable:
                The variable, that has the same API as
                `netCDF4.Variable` or `h5netcdf.Variable`.

        :Returns:

            `bool`
                 `True` if the variable data is contiguous on disk,
                 otherwise `False`.

        **Examples**

        >>> f.contiguous(variable)
        False

        """
        try:
            # netCDF4
            return variable.chunking() == "contiguous"
        except AttributeError:
            # h5netcdf
            return variable.chunks is None

    def dtype(self, variable):
        """Return the data type of a variable.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            variable:
                The variable, that has the same API as
                `netCDF4.Variable` or `h5netcdf.Variable`.

        :Returns:

            `numpy.dtype` or `str`
                 The data type.

        **Examples**

        >>> f.dtype(variable)
        dtype('<f8')

        >>> f.dtype(variable)
        str

        """
        out = variable.dtype
        if out == "O":
            out = str

        return out

    def endian(self, variable):
        """Return the endian-ness of a variable.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            variable:
                The variable, that has the same API as
                `netCDF4.Variable` or `h5netcdf.Variable`.

        :Returns:

            `str`
                 The endian-ness (``'little'``, ``'big'``, or
                 ``'native'``) of the variable.

        **Examples**

        >>> f.endian(variable)
        'native'

        """
        try:
            # netCDF4
            return variable.endian()
        except AttributeError:
            # h5netcdf
            dtype = variable.dtype
            return _dtype_endian_lookup[getattr(dtype, "byteorder", None)]

    def filepath(self, dataset):
        """Return the file path for the dataset.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            dataset:
                The dataset, that has the same API as
                `netCDF4.Dataset` or `h5netcdf.File`.

        :Returns:

            `str`
                The file system path, or the OPeNDAP URL, for the
                dataset.

        **Examples**

        >>> f.filepath(dataset)
        '/home/data/file.nc'

        """
        try:
            # netCDF4
            return dataset.filepath()
        except AttributeError:
            # h5netcdf
            return dataset.filename

    def get_dims(self, variable):
        """Return the dimensions associated with a variable.

        .. versionadded:: (cfdm) 1.11.2.0

        :Returns:

            `list`

        """
        try:
            # netCDF4
            return variable.get_dims()
        except AttributeError:
            # h5netcdf
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

    def getncattr(self, x, attr):
        """Retrieve a netCDF attribute.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            x: variable, group, or dataset

            attr: `str`

        :Returns:

        """
        try:
            # netCDF4
            return getattr(x, attr)
        except AttributeError:
            # h5netcdf
            return x.attrs[attr]

    def group(self, x):
        """Return the group that a variable belongs to.

        .. versionadded:: (cfdm) 1.11.2.0

        :Returns:

            `Group`

        """
        try:
            # netCDF4
            return x.group()
        except AttributeError:
            # h5netcdf
            return x._parent

    def name(self, x):
        """Return the netCDF name, without its groups.

        .. versionadded:: (cfdm) 1.11.2.0

        :Returns:

            `str`

        """
        out = x.name
        if group_separator in out:
            # h5netcdf
            out = x.name.split(group_separator)[-1]

        return out

    def ncattrs(self, x):
        """Return netCDF attribute names.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            x: variable, group, or dataset

        :Returns:

            `list`

        """
        try:
            # netCDF4
            return x.ncattrs()
        except AttributeError:
            # h5netcdf
            return list(x.attrs)

    def parent(self, group):
        """Return a simulated unix parent group.

        .. versionadded:: (cfdm) 1.11.2.0

        :Returns:

            `str`

        """
        try:
            return group.parent
        except AttributeError:
            return

    def path(self, group):
        """Return a simulated unix directory path to a group.

        .. versionadded:: (cfdm) 1.11.2.0

        :Returns:

            `str`

        """
        try:
            # netCDF4
            return group.path
        except AttributeError:
            # h5netcdf
            try:
                return group.name
            except AttributeError:
                return group_separator

    def flatten(self):
        """Flattens and writes to output file.

        .. versionadded:: (cfdm) 1.11.2.0

        :Return:

            `None`

        """
        input_ds = self._input_ds
        output_ds = self._output_ds

        logging.info(f"Flattening the groups of {self.filepath(input_ds)}")

        # Flatten product
        self.process_group(input_ds)

        # Add name mapping attributes
        output_ds.setncattr(flattener_attribute_map, self._attr_map_value)
        output_ds.setncattr(flattener_dimension_map, self._dim_map_value)
        output_ds.setncattr(flattener_variable_map, self._var_map_value)

        # Browse flattened variables to rename references:
        logging.info(
            "    Browsing flattened variables to rename references "
            "in attributes"
        )
        for var in output_ds.variables.values():
            self.adapt_references(var)

    def process_group(self, input_group):
        """Flattens a given group to the output file.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            input_group: `str`
                The group to flatten.

        :Returns:

            `None`

        """
        logging.info(f"    Browsing group {self.path(input_group)}")

        for attr_name in self.ncattrs(input_group):
            self.flatten_attribute(input_group, attr_name)

        for dim in input_group.dimensions.values():
            self.flatten_dimension(dim)

        for var in input_group.variables.values():
            self.flatten_variable(var)

        for child_group in input_group.groups.values():
            self.process_group(child_group)

    def flatten_attribute(self, input_group, attr_name):
        """Flattens a given attribute from a group to the output file.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            input_group: `str`
                The group containing the attribute to flatten.

            attr_name: `str`
                The name of the attribute.

        :Returns:

            `None`

        """
        logging.info(
            f"        Copying attribute {attr_name} from "
            f"group {self.path(input_group)} to root"
        )

        # Create new name
        new_attr_name = self.generate_flattened_name(input_group, attr_name)

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
                The dimension to flatten, that has the same API as
                `netCDF4.Dimension` or `h5netcdf.Dimension`.

        :Returns:

            `None`

        """
        logging.info(
            f"    Copying dimension {self.name(dim)} from "
            f"group {self.path(self.group(dim))} to root"
        )

        # Create new name
        new_name = self.generate_flattened_name(
            self.group(dim), self.name(dim)
        )

        # Write dimension
        self._output_ds.createDimension(
            new_name, (len(dim), None)[dim.isunlimited()]
        )

        # Store new name in dict for resolving references later
        self._dim_map[self.pathname(self.group(dim), self.name(dim))] = (
            new_name
        )

        # Add to name mapping attribute
        self._dim_map_value.append(
            self.generate_mapping_str(
                self.group(dim), self.name(dim), new_name
            )
        )

    def flatten_variable(self, var):
        """Flattens a given variable to the output file.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            var:
                The variable, that has the same API as
                `netCDF4.Variable` or `h5netcdf.Variable`.

        :Returns:

            `None`

        """
        logging.info(
            f"        Copying variable {self.name(var)} from "
            f"group {self.path(self.group(var))} to root"
        )

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
        fullname = self.pathname(self.group(var), self.name(var))
        logging.info(f"        Creating variable {new_name} from {fullname}")

        attributes = self.attrs(var)

        omit_data = self._omit_data
        if omit_data:
            fill_value = False
        else:
            fill_value = attributes.pop("_FillValue", None)

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
                The variable where the data should be copied from,
                that has the same API as `netCDF4.Variable` or
                `h5netcdf.Variable`.

            new_var:
                The new variable in which to copy the data, that has the
                same API as `netCDF4.Variable` or `h5netcdf.Variable`.

        :Returns:

            `None`

        """
        ndim = old_var.ndim
        shape = old_var.shape
        chunk_shape = (
            (self.write_chunksize // (old_var.dtype.itemsize * ndim)),
        ) * ndim

        logging.info(
            f"        Copying {self.name(old_var)!r} data in chunks of "
            f"{chunk_shape}"
        )
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
                The original variable containing the reference, that
                has the same API as `netCDF4.Variable` or
                `h5netcdf.Variable`.

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
                The original variable containing the reference, that
                has the same API as `netCDF4.Variable` or
                `h5netcdf.Variable`.

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
        else:
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
                The original variable containing the reference, that
                has the same API as `netCDF4.Variable` or
                `h5netcdf.Variable`.

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
            logging.info(
                f"            Reference to {orig_ref!r} not "
                "resolved. Assumed to be a standard name."
            )
            ref_type = "standard_name"
            absolute_ref = orig_ref
        elif absolute_ref is None:
            # Not found, so raise exception.
            absolute_ref = self.handle_reference_error(
                orig_ref, self.path(self.group(orig_var))
            )
        else:
            # Found
            logging.info(
                f"            {method} reference to {ref_type} "
                f"{orig_ref!r} resolved as {absolute_ref!r}"
            )

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
            logging.info(
                f"            Reference to {orig_ref!r} is not a "
                "scalar coordinate variable. Assumed to be a standard name."
            )
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

            current_group: `str`
                The current group of the reference.

            search_dim: `bool`
                If True then search for a dimension, otherwise a
                variable.

        :Returns:

            `str`
                The absolute path to the variable.

        """
        # Go up parent groups
        while ref.startswith("../"):
            if current_group.parent is None:
                return None

            ref = ref[3:]
            current_group = current_group.parent

        # Go down child groups
        ref_split = ref.split(group_separator)
        for g in ref_split[:-1]:
            try:
                current_group = current_group.groups[g]
            except KeyError:
                return None

        # Get variable or dimension
        if search_dim:
            elt = current_group.dimensions[ref_split[-1]]
        else:
            elt = current_group.variables[ref_split[-1]]

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
                The current group where searching.

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
            dims_or_vars = current_group.dimensions
        else:
            dims_or_vars = current_group.variables

        # Found in current group
        if ref in dims_or_vars.keys():
            return dims_or_vars[ref]

        local_apex_reached = (
            local_apex_reached or ref in current_group.dimensions.keys()
        )

        # Check if have to continue looking in parent group
        # - normal search: continue until root is reached
        # - coordinate variable: continue until local apex is reached
        if is_coordinate_variable:
            top_reached = local_apex_reached or current_group.parent is None
        else:
            top_reached = current_group.parent is None

        # Search up
        if not top_reached:
            return self.search_by_proximity(
                ref,
                current_group.parent,
                search_dim,
                local_apex_reached,
                is_coordinate_variable,
            )

        elif is_coordinate_variable and local_apex_reached:
            # Coordinate variable and local apex reached, so search
            # down in siblings
            found_elt = None
            for child_group in current_group.groups.values():
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

        else:
            # Did not find
            return None

    def resolve_references(self, var, old_var):
        """Resolve references.

        In a given variable, replace all references to other variables
        in its attributes by absolute references.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            var:
                The flattened variable in which references should be
                renamed with absolute references, that has the same
                API as `netCDF4.Variable` or `h5netcdf.Variable`.

            old_var:
                The original variable (in group structure), that has
                the same API as `netCDF4.Variable` or
                `h5netcdf.Variable`.

        :Returns:

            `None`

        """
        var_attrs = self.attrs(var)
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
                The flattened variable in which references should be
                renamed with new names, that has the same API as
                `netCDF4.Variable` or `h5netcdf.Variable`.

        :Returns:

            `None`

        """
        var_attrs = self.attrs(var)
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

            logging.info(
                f"        Value of {self.name(var)}.{name} changed "
                f"from {value!r} to {new_attr_value!r}"
            )

    def adapt_name(self, resolved_ref, rules):
        """Apapt the name.

        Return name of flattened reference. If not found, raise
        exception or continue with a warning.

        .. versionadded:: (cfdm) 1.11.2.0

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
            return self.handle_reference_error(resolved_ref)

    def pathname(self, group, name):
        """Compose full path name to an element in a group structure.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            current_group:
                The group containing the dimension or variable.

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
                The group containing the non-flattened dimension or
                variable.

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
                The group containing the dimension or variable.

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

    def handle_reference_error(self, ref, context=None):
        """Handle reference error.

        Depending on the `_strict` mode, either raise an exception or
        log a warning. If not strict then a reference placeholder is
        returned.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            ref: `str`
                The reference

            context: `str`
                Additional context information to add to message.

        :Returns:

            `str`
                The error message, or if `_strict` is `True` then an
                `UnresolvedReferenceException` is raised.

        """
        message = f"Reference {ref!r} could not be resolved"
        if context is not None:
            message = f"{message} from {context}"

        if self._strict:
            raise UnresolvedReferenceException(message)

        warnings.warn(message)
        return f"{ref_not_found_error}_{ref}"


class AttributeParsingException(Exception):
    """Exception for unparsable attribute.

    .. versionadded:: (cfdm) 1.11.2.0

    """

    pass


class UnresolvedReferenceException(Exception):
    """Exception for unresolvable references in attributes.

    .. versionadded:: (cfdm) 1.11.2.0

    """

    pass
