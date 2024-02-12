"""Flatten NetCDF groups.

Portions of this code were adapted from the `netcdf_flattener`
library, which carries the Apache 2.0 License:

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
    default_copy_slice_size,
    flattener_attribute_map,
    flattener_dimension_map,
    flattener_separator,
    flattener_variable_map,
    flattening_rules,
    group_separator,
    max_name_len,
    ref_not_found_error,
)

# Mapping from numpy dtype endian format to what we expect
_dtype_endian_lookup = {
    "=": "native",
    ">": "big",
    "<": "little",
    "|": "native",
    None: "native",
}

# Set of netCDF attributes that may contain references to dimensions
# or variables
special_attributes = set(flattening_rules)


def netcdf_flatten(
    input_ds, output_ds, lax_mode=False, copy_data=True, copy_slices=None
):
    """Create a flattened version of a netCDF dataset.

    For variable that are too big to fit in memory, the optional
    "copy_slices" input allows to copy some or all of the variables in
    slices.

    .. versionadded:: (cfdm) 1.11.1.0

    :Parameters:

        input_ds: `netCDF4.Dataset` or `h5netcdf.File`
            The dataset to be falttened.

        output_ds: `netCDF4.Dataset`
            A container for the flattened dataset.

        lax_mode: `bool`, optional
            If False, the default, the not resolving a reference
            halts the execution. If True, then continue with a
            warning.

        copy_data: `bool`, optional
            If True, the default, then all data arrays are copied
            from the input to the output dataset. If False, then
            this does not happen. Use this option only if the data
            arrays of the flattened dataset are never to be
            accessed.

        copy_slices: `dict`, optional
            Dictionary containing variable_name/shape key/value
            pairs, where variable_name is the path to the variable
            name in the original dataset (for instance
            ``/group1/group2/my_variable``), and shape is either
            `None` for using default slice value, or a custom
            slicing shape in the form of a tuple of the same
            dimension as the variable (for instance ``(1000, 2000,
            1500)`` for a 3-dimensional variable). If a variable
            from the dataset is not contained in the dictionary
            then it will not be sliced and copied normally.

    """
    _Flattener(
        input_ds, lax_mode, copy_data=copy_data, copy_slices=copy_slices
    ).flatten(output_ds)


def parse_var_attr(attribute):
    """Parse variable attribute of any form into a dict:

     * 'time' -> {'time': []}

     * 'lat lon' -> {'lat': [], 'lon': []}

     * 'area: time volume: lat lon' -> {'area': ['time'], 'volume':
       ['lat', 'lon']}

    .. versionadded:: (cfdm) 1.11.1.0

    :Parameters:

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
    pat_value = subst("(?P<value>WORD)SEP")
    pat_values = "({})*".format(pat_value)
    pat_mapping = subst(
        "(?P<mapping_name>WORD):SEP(?P<values>{})".format(pat_values)
    )
    pat_mapping_list = "({})+".format(pat_mapping)

    # Regex for 'list form': "v1 v2 v3" (including single-item form)
    pat_list_item = subst("(?P<list_item>WORD)SEP")
    pat_list = "({})+".format(pat_list_item)

    # Regex for any form:
    pat_all = subst(
        "((?P<list>{})|(?P<mapping_list>{}))$".format(
            pat_list, pat_mapping_list
        )
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
        raise ReferenceException(
            f"Error while parsing attribute value: {attribute!r}"
        )

    return out


def generate_var_attr_str(d):
    """Re-generate the attribute string from a dictionary.

    .. versionadded:: (cfdm) 1.11.1.0

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

    .. versionadded:: (cfdm) 1.11.1.0

    """

    def __init__(self, input_ds, lax_mode, copy_data=True, copy_slices=None):
        """**Initialisation**

        :Parameters:

            input_ds: `netCDF4.Dataset` or `h5netcdf.File`
                The dataset to be falttened.

            lax_mode: `bool`, optional
                If False, the default, the not resolving a reference
                halts the execution. If True, then continue with a
                warning.

            copy_data: `bool`, optional
                If True, the default, then all data arrays are copied
                from the input to the output dataset. If False, then
                this does not happen. Use this option only if the data
                arrays of the flattened dataset are never to be
                accessed.

            copy_slices: `dict`, optional
                Dictionary containing variable_name/shape key/value
                pairs, where variable_name is the path to the variable
                name in the original dataset (for instance
                ``/group1/group2/my_variable``), and shape is either
                `None` for using default slice value, or a custom
                slicing shape in the form of a tuple of the same
                dimension as the variable (for instance ``(1000, 2000,
                1500)`` for a 3-dimensional variable). If a variable
                from the dataset is not contained in the dictionary
                then it will not be sliced and copied normally.

        """
        self.__attr_map_value = []
        self.__dim_map_value = []
        self.__var_map_value = []

        self.__dim_map = {}
        self.__var_map = {}

        self.__lax_mode = lax_mode

        self.__copy_data = copy_data
        self.__copy_slices = copy_slices

        self.__input_file = input_ds
        self.__output_file = None

    def attrs(self, variable):
        """TODOHDF."""
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

        .. versionadded:: (cfdm) 1.11.1.0

        :Parameters:

            variable:
                The dataset variable.

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

        .. versionadded:: (cfdm) 1.11.1.0

        :Parameters:

            variable: `netCDF4.Variable` or `h5netcdf.Variable`
                The variable.

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

        .. versionadded:: (cfdm) 1.11.1.0

        :Parameters:

            variable:
                The dataset variable.

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

        .. versionadded:: (cfdm) 1.11.1.0

        :Parameters:

            variable: `netCDF4.Variable` or `h5netcdf.Variable`
                The variable.

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

        .. versionadded:: (cfdm) 1.11.1.0

        :Parameters:

            dataset: `netCDF4.Dataset` or `h5netcdf.File`
                The dataset.

        :Returns:

            `str`
                The file system path, or the opendap URL, for the
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
        """Return.

        .. versionadded:: (cfdm) 1.11.1.0

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

        .. versionadded:: (cfdm) 1.11.1.0

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
        """Return a.

        .. versionadded:: (cfdm) 1.11.1.0

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

        .. versionadded:: (cfdm) 1.11.1.0

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

        .. versionadded:: (cfdm) 1.11.1.0

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
        """Return a simulated unix directory path to a group.

        .. versionadded:: (cfdm) 1.11.1.0

        :Returns:

            `str`

        """
        try:
            return group.parent
        except AttributeError:
            return

    def path(self, group):
        """Return a simulated unix directory path to a group.

        .. versionadded:: (cfdm) 1.11.1.0

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

    def flatten(self, output_ds):
        """Flattens and write to output file.

        .. versionadded:: (cfdm) 1.11.1.0

        :Parameters:

            output_ds: `netCDF4.Dataset`
                A container for the flattened dataset.

        :Return:

            `None`

        """
        logging.info(
            f"Flattening the groups of {self.filepath(self.__input_file)}"
        )

        if (
            output_ds == self.__input_file
            or output_ds.filepath() == self.filepath(self.__input_file)
            or output_ds.data_model != "NETCDF4"
        ):
            raise ValueError(
                "Invalid inputs. Input and output datasets should "
                "be different, and output should be of the 'NETCDF4' format."
            )

        self.__output_file = output_ds

        # Flatten product
        self.process_group(self.__input_file)

        # Add name mapping attributes
        self.__output_file.setncattr(
            flattener_attribute_map, self.__attr_map_value
        )
        self.__output_file.setncattr(
            flattener_dimension_map, self.__dim_map_value
        )
        self.__output_file.setncattr(
            flattener_variable_map, self.__var_map_value
        )

        # Browse flattened variables to rename references:
        logging.info(
            "    Browsing flattened variables to rename references "
            "in attributes"
        )
        for var in self.__output_file.variables.values():
            self.adapt_references(var)

    def process_group(self, input_group):
        """Flattens a given group to the output file.

        .. versionadded:: (cfdm) 1.11.1.0

        :Parameters:

            input_group: `str`
                The group to faltten.

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

        .. versionadded:: (cfdm) 1.11.1.0

        :Parameters:

            input_group: `str`
                The group containing the attribute to flatten.

            attr_name: `str`
                The anme of the attribute.

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
        self.__output_file.setncattr(
            new_attr_name, self.getncattr(input_group, attr_name)
        )

        # Store new naming for later and in mapping attribute
        self.__attr_map_value.append(
            self.generate_mapping_str(input_group, attr_name, new_attr_name)
        )

    def flatten_dimension(self, dim):
        """Flattens a given dimension to the output file.

        .. versionadded:: (cfdm) 1.11.1.0

        :Parameters:

            dim: `netCDF4.Dimension` or `h5netcdf.Dimension`
                The dimension to flatten.

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
        self.__output_file.createDimension(
            new_name, (len(dim), None)[dim.isunlimited()]
        )

        # Store new name in dict for resolving references later
        self.__dim_map[
            self.pathname(self.group(dim), self.name(dim))
        ] = new_name

        # Add to name mapping attribute
        self.__dim_map_value.append(
            self.generate_mapping_str(
                self.group(dim), self.name(dim), new_name
            )
        )

    def flatten_variable(self, var):
        """Flattens a given variable to the output file.

        .. versionadded:: (cfdm) 1.11.1.0

        :Parameters:

            var: `netCDF4.Variable` or `h5netcdf.Variable`
                The variable to flatten.

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
                lambda x: self.__dim_map[
                    self.pathname(self.group(x), self.name(x))
                ],
                self.get_dims(var),
            )
        )

        # Write variable
        fullname = self.pathname(self.group(var), self.name(var))
        logging.info(f"        Creating variable {new_name} from {fullname}")

        attributes = self.attrs(var)

        copy_data = self.__copy_data
        if copy_data:
            fill_value = attributes.pop("_FillValue", None)
        else:
            fill_value = False

        new_var = self.__output_file.createVariable(
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

        if copy_data:
            # Find out slice method for variable and copy data
            copy_slices = self.__copy_slices
            if copy_slices is None or fullname not in copy_slices:
                # Copy data as a whole
                new_var[...] = var[...]
            elif copy_slices[fullname] is None:
                # Copy with default slice size
                copy_slice = tuple(
                    default_copy_slice_size // len(var.shape)
                    for _ in range(len(var.shape))
                )
                self.copy_var_by_slices(new_var, var, copy_slice)
            else:
                # Copy in slices
                copy_slice = copy_slices[fullname]
                self.copy_var_by_slices(new_var, var, copy_slice)

        # Copy attributes
        new_var.setncatts(attributes)

        # Store new name in dict for resolving references later
        self.__var_map[
            self.pathname(self.group(var), self.name(var))
        ] = new_name

        # Add to name mapping attribute
        self.__var_map_value.append(
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
        the matching slice length along than dimension. If end of the
        dimension is reached, recursively increment the next
        dimensions until a valid position is found.

        .. versionadded:: (cfdm) 1.11.1.0

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

    def copy_var_by_slices(self, new_var, old_var, copy_slice_shape):
        """Copy the data of a variable to a new one by slice.

        .. versionadded:: (cfdm) 1.11.1.0

        :Parameters:

            new_var: `netCDF4.Variable`
                The new variable where to copy dataf.

            old_var: `netCDF4.Variable` or `h5netcdf.Variable`
                The variable where data should be copied from.

            copy_slice_shape: `tuple`
                The shape of the slice

        :Returns:

            `None`

        """
        logging.info(
            f"        Copying data of {self.name(old_var)} in "
            f"{copy_slice_shape} slices"
        )

        # Initial position vector
        pos = [0 for _ in range(len(copy_slice_shape))]

        # Copy in slices until end reached
        var_end_reached = False
        while not var_end_reached:
            # Create current slice
            current_slice = tuple(
                slice(
                    pos[dim_i], min(old_var.shape[dim_i], pos[dim_i] + dim_l)
                )
                for dim_i, dim_l in enumerate(copy_slice_shape)
            )

            # Copy data in slice
            new_var[current_slice] = old_var[current_slice]

            # Get next position
            var_end_reached = not self.increment_pos(
                pos, 0, copy_slice_shape, old_var.shape
            )

    def resolve_reference(self, orig_ref, orig_var, rules):
        """Resolve a refrence.

        Resolves the absolute path to a coordinate variable within the
        group structure.

        .. versionadded:: (cfdm) 1.11.1.0

        :Parameters:

            orig_ref: `str`
                The reference to resolve.

            orig_var: `netCDF4.Variable` or `h5netcdf.Variable`
                The original variable containing the reference.

            rules: `FlatteningRules`
                The flattening rules that apply to the reference.

        :Returns:

            `str`
                The absolute path to the reference.

        """
        ref = orig_ref
        absolute_ref = None
        ref_type = ""

        # Resolve first as dim (True), or var (False)
        resolve_dim_or_var = rules.ref_to_dim > rules.ref_to_var

        # Resolve var (resp. dim) if resolving as dim (resp. var) failed
        resolve_alt = rules.ref_to_dim and rules.ref_to_var

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

        .. versionadded:: (cfdm) 1.11.1.0

        :Parameters:

            ref: `str`
                The reference to resolve.

            resolve_dim_or_var: `bool`
                Try to resolve first as dimension (True), or else as
                variable (False).

            resolve_alt: `bool`
                Resolve as variable if resolving as dimension failed,
                and vice versa.

            orig_var: `netCDF4.Variable` or `h5netcdf.Variable`
                The original variable containing the reference.

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

        resolved_var = self.search_by_proximity(
            ref,
            self.group(orig_var),
            resolve_dim_or_var,
            False,
            rules.stop_at_local_apex,
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
                rules.stop_at_local_apex,
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

        .. versionadded:: (cfdm) 1.11.1.0

        :Parameters:

            absolute_ref: `str`
                The absolute path of the reference.

            orig_ref: `str`
                The original reference.

            orig_var: `netCDF4.Variable` or `h5netcdf.Variable`
                The original variable containing the reference.

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
                or self._Flattener__input_file[absolute_ref].ndim > 0
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

        .. versionadded:: (cfdm) 1.11.1.0

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
        apex is reached, Then search down in siblings.

        .. versionadded:: (cfdm) 1.11.1.0

        :Parameters:

            ref: `str`
                The reference to resolve.

            current_group:
                The current group where searching.

            search_dim: `bool`
                If True then search for a dimension, otherwise a
                variable.

            local_apex_reached: `bool`
                Whether or not the apex is previously been reached.

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

        # Check if has to continue looking in parent group
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

        .. versionadded:: (cfdm) 1.11.1.0

        :Parameters:

            var: `netCDF4.Variable` or `h5netcdf.Variable`
                The flattened variable in which references should be
                renamed with absolute references.

            old_var: `netCDF4.Variable` or `h5netcdf.Variable`
                The original variable (in group structure).

        :Returns:

            `None`

        """
        var_attrs = self.attrs(var)
        for name in special_attributes.intersection(var_attrs):
            # Parse attribute value
            parsed_attr = parse_var_attr(var_attrs[name])

            # Resolved references in parsed as required by attribute
            # properties
            resolved_parsed_attr = {}

            rules = flattening_rules.get(name)
            for k, v in parsed_attr.items():
                if rules.resolve_key:
                    k = self.resolve_reference(k, old_var, rules)

                if rules.resolve_value and v is not None:
                    v = [self.resolve_reference(x, old_var, rules) for x in v]

                resolved_parsed_attr[k] = v

            # Re-generate attribute value string with resolved
            # references
            var.setncattr(
                rules.name, generate_var_attr_str(resolved_parsed_attr)
            )

    def adapt_references(self, var):
        """Adapt references.

        In a given variable, replace all references to variables in
        attributes by references to the new names in the flattened
        netCDF. All references have to be already resolved as absolute
        references.

        .. versionadded:: (cfdm) 1.11.1.0

        :Parameters:

            var: `netCDF4.Variable` or `h5netcdf.Variable`
                The flattened variable in which references should be
                renamed with new names.

        :Returns:

            `None`

        """
        var_attrs = self.attrs(var)
        for name in special_attributes.intersection(var_attrs):
            # Parse attribute value
            attr_value = var_attrs[name]
            parsed_attr = parse_var_attr(attr_value)

            adapted_parsed_attr = {}

            rules = flattening_rules.get(name)
            for k, v in parsed_attr.items():
                if rules.resolve_key:
                    k = self.adapt_name(k, rules)

                if rules.resolve_value and v is not None:
                    v = [self.adapt_name(x, rules) for x in v]

                adapted_parsed_attr[k] = v

            new_attr_value = generate_var_attr_str(adapted_parsed_attr)
            var.setncattr(rules.name, new_attr_value)

            logging.info(
                f"        Value of {self.name(var)}.{rules.name} changed "
                f"from {attr_value!r} to {new_attr_value!r}"
            )

    def adapt_name(self, resolved_ref, rules):
        """Apapt the name.

        Return name of flattened reference. If not found, raise
        exception or continue warning.

        .. versionadded:: (cfdm) 1.11.1.0

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

        # Select highest priority map
        if rules.ref_to_dim > rules.ref_to_var:
            name_mapping = self.__dim_map

        if rules.ref_to_dim < rules.ref_to_var:
            name_mapping = self.__var_map

        # Try to find mapping
        try:
            return name_mapping[resolved_ref]

        # If not found, look in other map if allowed
        except KeyError:
            if rules.ref_to_dim and rules.ref_to_var:
                if rules.ref_to_dim < rules.ref_to_var:
                    name_mapping = self.__dim_map
                else:
                    name_mapping = self.__var_map

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
        """Compose full path name to an element in a group structure:

        .. versionadded:: (cfdm) 1.11.1.0

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

        .. versionadded:: (cfdm) 1.11.1.0

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

        .. versionadded:: (cfdm) 1.11.1.0

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

        .. versionadded:: (cfdm) 1.11.1.0

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

        Depending on lax/strict mode, either raise exception or log
        warning. If lax, return reference placeholder.

        .. versionadded:: (cfdm) 1.11.1.0

        :Parameters:

            ref: `str`
                The reference

            context: `str`
                Additional context information to add to message.

        :Returns:

            `str`
                The error message, or if *lax_mode* is True then a
                `ReferenceException` is raised.

        """
        message = f"Reference {ref!r} could not be resolved"
        if context is not None:
            message = f"{message} from {context}"

        if self.__lax_mode:
            warnings.warn(message)
            return f"{ref_not_found_error}_{ref}"
        else:
            raise ReferenceException(message)


class ReferenceException(Exception):
    """Exception for unresolvable references in attributes.

    .. versionadded:: (cfdm) 1.11.1.0

    """

    pass
