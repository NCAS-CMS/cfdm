"""Project: NetCDF Flattener
Copyright (c) 2020 EUMETSAT
License: Apache License 2.0

Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied.  See the License for the
specific language governing permissions and limitations
under the License.
"""

import collections
import hashlib
import logging
import os
import re
import warnings
from enum import Enum

#from netCDF4 import Dataset
from h5netcdf import File as Dataset



def flatten(input_ds, output_ds, lax_mode=False, _copy_data=True, copy_slices=None):
    """Flatten an input NetCDF dataset and write the result in an output NetCDF dataset.

    For variable that are too big to fit in memory, the optional "copy_slices" input allows to copy some or all of the
    variables in slices.

    :param input_ds: input netcdf4 dataset
    :param output_ds: output netcdf4 dataset
    :param lax_mode: if false (default), not resolving a reference halts the execution. If true, continue with warning.
    :param _copy_data: if true (default), then all data arrays are copied from the input to the output dataset.
                       If false, then this does not happen.
                       Use this option *only* if the data arrays of the flattened dataset are never to be accessed.
                       If false then consider setting the fill mode for the output netcd4 dataset to "off" for improved performance.
    :param copy_slices: dictionary containing variable_name: shape pairs, where variable_name is the path to the
        variable name in the original Dataset (for instance /group1/group2/my_variable), and shape is either None for
        using default slice value, or a custom slicing shap in the form of a tuple of the same dimension as the variable
        (for instance (1000,2000,1500,) for a 3-dimensional variable). If a variable from the Dataset is not contained
        in the dict, it will not be sliced and copied normally.
    """
    _Flattener(input_ds, lax_mode, _copy_data=_copy_data, copy_slices=copy_slices).flatten(output_ds)


def parse_var_attr(input_str):
    """Parse variable attribute of any form into a dict:

    * 'time' -> OrderedDict([('time', [])])
    * 'lat lon' -> OrderedDict([('lat', []), ('lon', [])])
    * 'area: time volume: lat lon' -> OrderedDict([('area', ['time']), ('volume', ['lat', 'lon'])])

   :param input_str: string to parse
   :return: parsed string in an OrderedDict
    """

    def subst(s):
        """substitute tokens for WORD and SEP (space or end of string)"""
        return s.replace('WORD', r'[A-Za-z0-9_#/.\(\)]+').replace(
            'SEP', r'(\s+|$)')

    # Regex for 'dict form': "k1: v1 v2 k2: v3"
    pat_value = subst('(?P<value>WORD)SEP')
    pat_values = '({})*'.format(pat_value)
    pat_mapping = (subst('(?P<mapping_name>WORD):SEP(?P<values>{})'.format(pat_values)))
    pat_mapping_list = '({})+'.format(pat_mapping)

    # Regex for 'list form': "v1 v2 v3" (including single-item form)
    pat_list_item = (subst('(?P<list_item>WORD)SEP'))
    pat_list = '({})+'.format(pat_list_item)

    # Regex for any form:
    pat_all = (subst('((?P<list>{})|(?P<mapping_list>{}))$'.format(pat_list, pat_mapping_list)))

    m = re.match(pat_all, input_str)

    # Output is always a dict. If input form is a list, dict values are set as empty lists
    out = collections.OrderedDict()

    if m is not None:
        list_match = m.group('list')
        # Parse as a list
        if list_match:
            for mapping in re.finditer(pat_list_item, list_match):
                item = mapping.group('list_item')
                out[item] = None
        # Parse as a dict:
        else:
            mapping_list = m.group('mapping_list')
            for mapping in re.finditer(pat_mapping, mapping_list):
                term = mapping.group('mapping_name')
                values = [value.group('value') for value in re.finditer(pat_value, mapping.group('values'))]
                out[term] = values
    else:
        raise ReferenceException("Error while parsing attribute value: '{}'".format(input_str))

    return out


def generate_var_attr_str(d):
    """Re-generate the attribute string from a dictionary.

    :param d: dictionary
    :return: valid attribute string
    """
    parsed_list = []
    for k, v in d.items():
        if v is None:
            parsed_list.append(k)
        elif not v:
            parsed_list.append("{}:".format(k))
        else:
            parsed_list.append(k + ': ' + (' '.join(v)))
    return ' '.join(parsed_list)


class _AttributeProperties(Enum):
    """"Utility class containing the properties for each type of variable attribute, defining how contained references
    to dimensions and variables should be parsed and processed."""
    ancillary_variables = (0, (False, True, True, False, False, False, False))
    bounds = (1, (False, True, True, False, False, False, False))
    cell_measures = (2, (False, True, False, True, False, False, False))
    climatology = (3, (False, True, True, False, False, False, False))
    coordinates = (4, (False, True, True, False, True, False, False))
    formula_terms = (5, (False, True, False, True, False, False, False))
    geometry = (6, (False, True, True, False, False, False, False))
    grid_mapping = (7, (False, True, True, True, False, False, False))
    interior_ring = (8, (False, True, True, False, False, False, False))
    node_coordinates = (9, (False, True, True, False, False, False, False))
    node_count = (10, (False, True, True, False, False, False, False))
    nodes = (11, (False, True, True, False, False, False, False))
    part_node_count = (12, (False, True, True, False, False, False, False))
    compress = (13, (True, False, True, False, False, False, False))
    instance_dimension = (14, (True, False, True, False, False, False, False))
    sample_dimension = (15, (True, False, True, False, False, False, False))
    cell_methods = (16, (2, 1, True, False, False, True, True))

    def __init__(self, n, props):
        """_AttributeProperties enum constructor

        :param n: enum id
        :param props: a tuple containing the attribute's properties (ref_to_dim, ref_to_var, resolve_key, resolve_value,
            stop_at_local_apex, accept_standard_names, limit_to_scalar_coordinates):
                * ref_to_dim: True or integer if contains references to dimensions (highest int have priority)
                * ref_to_var: True or integer if contains references to variables (highest int have priority)
                * resolve_key: True if 'keys' have to be resolved in 'key1: value1 key2: value2 value3' or 'key1 key2'
                * resolve_value:  True if 'values' have to be resolved in 'key1: value1 key2: value2 value3'
                * stop_at_local_apex: True if upward research in the hierarchy has to stop at local apex
                * accept_standard_names: True if any standard name is valid in place of references (in which case no
                  exception is raised if a reference cannot be resolved, and the standard name is used in place)
                * limit_to_scalar_coordinates: True if references to variables are only resolved if present as well in
                  the 'coordinates' attributes of the variable, and they are scalar.
        """
        self.id = n
        self.ref_to_dim = props[0]
        self.ref_to_var = props[1]
        self.resolve_key = props[2]
        self.resolve_value = props[3]
        self.stop_at_local_apex = props[4]
        self.accept_standard_names = props[5]
        self.limit_to_scalar_coordinates = props[6]


class _Flattener:
    """Utility class contained the input file, the output file being flattened, and all the logic of the flattening
    process.
    """
    __max_name_len = 256
    __default_separator = '/'
    __new_separator = '__'
    __pathname_format = "{}/{}"
    __mapping_str_format = "{}: {}"
    __ref_not_found_error = "REF_NOT_FOUND"
    __default_copy_slice_size = 200000000

    # name of the attributes used to store the mapping between original and flattened names
    __attr_map_name = "__flattener_name_mapping_attributes"
    __dim_map_name = "__flattener_name_mapping_dimensions"
    __var_map_name = "__flattener_name_mapping_variables"

    def __init__(self, input_ds, lax_mode, _copy_data=True, copy_slices=None):
        """Constructor. Initializes the Flattener class given the input file.

        :param input_ds: input netcdf dataset
        :param lax_mode: if false (default), not resolving a reference halts the execution. If true, continue with warning.
        :param _copy_data: if true (default), then all data arrays are copied from the input to the output dataset
                           If false, then this does not happen.
                           Use this option *only* if the data arrays of the flattened dataset are never to be accessed.
        :param copy_slices: dictionary containing variable_name: shape pairs, where variable_name is the path to the
            variable name in the original Dataset (for instance /group1/group2/my_variable), and shape is either None
            for using default slice value, or a custom slicing shape in the form of a tuple of the same dimension as the
            variable (for instance (1000,2000,1500,) for a 3-dimensional variable). If a variable from the Dataset is
            not contained in the dict, it will not be sliced and copied normally.
        """

        self.__attr_map_value = []
        self.__dim_map_value = []
        self.__var_map_value = []

        self.__dim_map = dict()
        self.__var_map = dict()

        self.__lax_mode = lax_mode

        self.__copy_data = _copy_data
        self.__copy_slices = copy_slices

        self.__input_file = input_ds
        self.__output_file = None

    def filepath(self, ds):
        try:
            # netCDF4
            return ds.filepath()
        except AttributeError:
            # h5netcdf
            return ds.filename
        
    def data_model(self, ds):
        try:
            # netCDF4
            return ds.data_model
        except AttributeError:
            # h5netcdf
            return 'NETCDF4'
        
    def path(self, group):
        try:
            # netCDF4
            return group.path
        except AttributeError:
            # h5netcdf
            return group.name
        
    def ncattrs(self, yyy):
        try:
            # netCDF4
            return yyy.ncattrs()
        except AttributeError:
            # h5netcdf
            return tuple(yyy.attrs)
        
    def getncattr(self, yyy, attr):
        try:
            # netCDF4
            return getattr(yyy, attr)
        except AttributeError:
            # h5netcdf
            return yyy.attrs[attr]
        
    def flatten(self, output_ds):
        """Flattens and write to output file

        :param output_ds: The dataset in which to store the flattened result.
        """
#                or output_ds.filepath() == self.__input_file.filepath() \
#                or output_ds.data_model != 'NETCDF4':
        if output_ds == self.__input_file \
           or self.filepath(output_ds) == self.filepath(self.__input_file) \
           or self.data_model(output_ds) != 'NETCDF4':
            raise ValueError("Invalid inputs. Input and output datasets should be different, and output should be of "
                             "the 'NETCDF4' format.")

        self.__output_file = output_ds

        # Flatten product
        self.process_group(self.__input_file)

        # Add name mapping attributes
        self.__output_file.setncattr(self.__attr_map_name, self.__attr_map_value)
        self.__output_file.setncattr(self.__dim_map_name, self.__dim_map_value)
        self.__output_file.setncattr(self.__var_map_name, self.__var_map_value)

        # Browse flattened variables to rename references:
        logging.info("Browsing flattened variables to rename references in attributes:")
        for var in self.__output_file.variables.values():
            self.adapt_references(var)

    def process_group(self, input_group):
        """Flattens a given group to the output file.

        :param input_group: group to flatten
        """
#        logging.info("Browsing group " + input_group.path)
        logging.info("Browsing group " + self.path(input_group))
#        for attr_name in input_group.ncattrs():
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

        :param input_group: group containing the attribute to flatten
        :param attr_name: name of the attribute to flatten
        """
#        logging.info("   Copying attribute {} from group {} to root".format(attr_name, input_group.path))
        logging.info("   Copying attribute {} from group {} to root".format(attr_name, self.path(input_group)))

        # Create new name
        new_attr_name = self.generate_flattened_name(input_group, attr_name)

        # Write attribute
#        self.__output_file.setncattr(new_attr_name, input_group.getncattr(attr_name))
        self.__output_file.setncattr(new_attr_name, self.getncattr(input_group, attr_name))

        # Store new naming for later and in mapping attribute
        self.__attr_map_value.append(self.generate_mapping_str(input_group, attr_name, new_attr_name))

    def flatten_dimension(self, dim):
        """Flattens a given dimension to the output file.

        :param dim: dimension to flatten
        """
#        logging.info("   Copying dimension {} from group {} to root".format(dim.name, dim.group().path))
        logging.info("   Copying dimension {} from group {} to root".format(dim.name, self.path(dim.group())))

        # Create new name
        new_name = self.generate_flattened_name(dim.group(), dim.name)
        
        # Write dimension
        self.__output_file.createDimension(new_name, (len(dim), None)[dim.isunlimited()])

        # Store new name in dict for resolving references later
        self.__dim_map[self.pathname(dim.group(), dim.name)] = new_name

        # Add to name mapping attribute
        self.__dim_map_value.append(self.generate_mapping_str(dim.group(), dim.name, new_name))

    def flatten_variable(self, var):
        """Flattens a given variable to the output file.

        :param var: variable to flatten
        """
#        logging.info("   Copying variable {} from group {} to root".format(var.name, var.group().path))
        logging.info("   Copying variable {} from group {} to root".format(var.name, self.path(var.group())))

        # Create new name
        new_name = self.generate_flattened_name(var.group(), var.name)

        # Replace old by new dimension names
        new_dims = list(map(lambda x: self.__dim_map[self.pathname(x.group(), x.name)], var.get_dims()))

        # Write variable
        fullname = self.pathname(var.group(), var.name)
        logging.info("create variable {} from {}".format(new_name, fullname))

        new_var = self.__output_file.createVariable(
            new_name,
            var.dtype,
            new_dims,
            zlib=False,
            complevel=4,
            shuffle=True,
            fletcher32=False,
            contiguous=var.chunking() == "contiguous",
            chunksizes=var.chunking() if var.chunking() != "contiguous" else None,
            endian=var.endian(),
            least_significant_digit=None,
            fill_value=None)

        if self.__copy_data:
            # Find out slice method for variable and copy data
            if self.__copy_slices is None or fullname not in self.__copy_slices:
                # Copy data as a whole
                new_var[:] = var[:]
            elif self.__copy_slices[fullname] is None:
                # Copy with default slice size
                copy_slice = tuple(self.__default_copy_slice_size // len(var.shape) for _ in range(len(var.shape)))
                self.copy_var_by_slices(new_var, var, copy_slice)
            else:
                # Copy in slices
                copy_slice = self.__copy_slices[fullname]
                self.copy_var_by_slices(new_var, var, copy_slice)

        # Copy attributes
        new_var.setncatts(var.__dict__)

        # Store new name in dict for resolving references later
        self.__var_map[self.pathname(var.group(), var.name)] = new_name

        # Add to name mapping attribute
        self.__var_map_value.append(self.generate_mapping_str(var.group(), var.name, new_name))

        # Resolve references in variable attributes and replace by absolute path:
        self.resolve_references(new_var, var)

    def increment_pos(self, pos, dim, copy_slice_shape, var_shape):
        """Increment position vector in a variable along a dimension by the matching slice length along than dimension.
        If end of the dimension is reached, recursively increment the next dimensions until a valid position is found.

        :param pos: current position
        :param dim: dimension to be incremented
        :param copy_slice_shape: shape of the slice
        :param var_shape: shape of the variable
        :return True if a valid position is found within the variable, False otherwise
        """
        # Try to increment dimension
        pos[dim] += copy_slice_shape[dim]

        # Test new position
        dim_end_reached = pos[dim] > var_shape[dim]
        var_end_reached = (dim + 1) >= len(copy_slice_shape)

        # End of this dimension not reached yet
        if not dim_end_reached:
            return True
        # End of this dimension reached. Reset to 0 and try increment next one recursively
        elif dim_end_reached and not var_end_reached:
            pos[:dim + 1] = [0 for j in range(dim + 1)]
            return self.increment_pos(pos, dim + 1, copy_slice_shape, var_shape)
        # End of this dimension reached, and no dimension to increment. Finish.
        else:
            return False

    def copy_var_by_slices(self, new_var, old_var, copy_slice_shape):
        """Copy the data of a variable to a new one by slice.

        :param new_var: new variable where to copy data
        :param old_var: variable where data should be copied from
        :param copy_slice_shape: shape of the slice
        """
        logging.info("   copying data of {} in {} slices".format(old_var.name, copy_slice_shape))

        # Initial position vector
        pos = [0 for _ in range(len(copy_slice_shape))]

        # Copy in slices until end reached
        var_end_reached = False
        while not var_end_reached:
            # Create current slice
            current_slice = tuple(slice(pos[dim_i], min(old_var.shape[dim_i], pos[dim_i] + dim_l)) for dim_i, dim_l in
                                  enumerate(copy_slice_shape))

            # Copy data in slice
            new_var[current_slice] = old_var[current_slice]

            # Get next position
            var_end_reached = not self.increment_pos(pos, 0, copy_slice_shape, old_var.shape)

    def resolve_reference(self, orig_ref, orig_var, attr):
        """Resolve the absolute path to a coordinate variable within the group structure.

        :param orig_ref: reference to resolve
        :param orig_var: variable originally containing the reference
        :param attr: _AttributeProperties object enum item to know if ref to dim or var
        :return: absolute path to the reference
        """
        ref = orig_ref
        absolute_ref = None
        ref_type = ""

        # Resolve first as dim (True), or var (False)
        resolve_dim_or_var = attr.ref_to_dim > attr.ref_to_var

        # Resolve var (resp. dim) if resolving as dim (resp. var) failed
        resolve_alt = (attr.ref_to_dim and attr.ref_to_var)

        # Reference is already given by absolute path
        if ref.startswith(self.__default_separator):
            method = "absolute"
            absolute_ref = ref

        # Reference is given by relative path
        elif self.__default_separator in ref:
            method = " relative"

            # First tentative as dim OR var
            ref_type = "dimension" if resolve_dim_or_var else "variable"
            absolute_ref = self.search_by_relative_path(orig_ref, orig_var.group(), resolve_dim_or_var)

            # If failed and alternative possible, second tentative
            if absolute_ref is None and resolve_alt:
                ref_type = "dimension" if not resolve_dim_or_var else "variable"
                absolute_ref = self.search_by_relative_path(orig_ref, orig_var.group(), not resolve_dim_or_var)

        # Reference is to be searched by proximity
        else:
            method = " proximity"
            absolute_ref, ref_type = self.resolve_reference_proximity(ref, resolve_dim_or_var, resolve_alt, orig_var,
                                                                      attr)

        # Post-search checks and return result
        return self.resolve_reference_post_processing(absolute_ref, orig_ref, orig_var, attr, ref_type, method)

    def resolve_reference_proximity(self, ref, resolve_dim_or_var, resolve_alt, orig_var, attr):
        """Resolve reference: search by proximity
        """
        # First tentative as dim OR var
        ref_type = "dimension" if resolve_dim_or_var else "variable"
        resolved_var = self.search_by_proximity(ref, orig_var.group(), resolve_dim_or_var, False,
                                                attr.stop_at_local_apex)

        # If failed and alternative possible, second tentative
        if resolved_var is None and resolve_alt:
            ref_type = "dimension" if not resolve_dim_or_var else "variable"
            resolved_var = self.search_by_proximity(ref, orig_var.group(), not resolve_dim_or_var, False,
                                                    attr.stop_at_local_apex)

        # If found, create ref string
        if resolved_var is not None:
            return self.pathname(resolved_var.group(), resolved_var.name), ref_type
        else:
            return None, ""

    def resolve_reference_post_processing(self, absolute_ref, orig_ref, orig_var, attr, ref_type, method):
        """Post-processing operations after resolving reference
        """
        # If not found and accept standard name, assume standard name
        if absolute_ref is None and attr.accept_standard_names:
            logging.info("      coordinate reference to '{}' not resolved. Assumed to be a standard name.".format(orig_ref))
            ref_type = "standard_name"
            absolute_ref = orig_ref
        # Else if not found, raise exception
        elif absolute_ref is None:
#            absolute_ref = self.handle_reference_error(orig_ref, orig_var.group().path)
            absolute_ref = self.handle_reference_error(orig_ref, self.path(orig_var.group()))
        # If found:
        else:
            logging.info("      {} coordinate reference to {} '{}' resolved as '{}'"
                  .format(method, ref_type, orig_ref, absolute_ref))

        # If variables refs are limited to coordinate variable, additional check
#                and (("coordinates" not in orig_var.ncattrs() or orig_ref not in orig_var.coordinates)
        if ref_type == "variable" and attr.limit_to_scalar_coordinates \
           and (("coordinates" not in self.ncattrs(orig_var) or orig_ref not in self.attr(orig_var, coordinates))
                or self._Flattener__input_file[absolute_ref].ndim > 0):
            logging.info("      coordinate reference to '{}' is not a SCALAR COORDINATE variable. "
                  "Assumed to be a standard name.".format(orig_ref))
            absolute_ref = orig_ref

        # Return result
        return absolute_ref

    def search_by_relative_path(self, ref, current_group, search_dim):
        """Resolve the absolute path to a reference within the group structure, using search by relative path.

        :param ref: reference to resolve
        :param current_group: current group where searching
        :param search_dim: if true, search references to dimensions, if false, search references to variables
        :return: absolute path to the coordinate
        """
        # Go up parent groups
        while ref.startswith("../"):
            if current_group.parent is None:
                return None
            ref = ref[3:]
            current_group = current_group.parent

        # Go down child groups
        ref_split = ref.split(self.__default_separator)
        for g in ref_split[:-1]:
            try:
                current_group = current_group.groups[g]
            except KeyError:
                return None

        # Get variable or dimension
        elt = current_group.dimensions[ref_split[-1]] if search_dim else current_group.variables[ref_split[-1]]

        # Get absolute reference
        return self.pathname(elt.group(), elt.name)

    def search_by_proximity(self, ref, current_group, search_dim, local_apex_reached, is_coordinate_variable):
        """Resolve the absolute path to a reference within the group structure, using search by proximity.

        First search up in the hierarchy for the reference, until root group is reached. If coordinate variable, search
        until local apex is reached, Then search down in siblings.

        :param ref: reference to resolve
        :param current_group: current group where searching
        :param search_dim: if true, search references to dimensions, if false, search references to variables
        :param local_apex_reached: False initially, until apex is reached.
        :param is_coordinate_variable: true, if looking for a coordinate variable
        :return: absolute path to the coordinate
        """
        dims_or_vars = current_group.dimensions if search_dim else current_group.variables

        # Found in current group
        if ref in dims_or_vars.keys():
            return dims_or_vars[ref]

        local_apex_reached = local_apex_reached or ref in current_group.dimensions.keys()

        # Check if has to continue looking in parent group
        # - normal search: continue until root is reached
        # - coordinate variable: continue until local apex is reached
        if is_coordinate_variable:
            top_reached = local_apex_reached or current_group.parent is None
        else:
            top_reached = current_group.parent is None

        # Search up
        if not top_reached:
            return self.search_by_proximity(ref, current_group.parent, search_dim, local_apex_reached,
                                            is_coordinate_variable)

        # If coordinate variable and local apex reached, search down in siblings
        elif is_coordinate_variable and local_apex_reached:
            found_elt = None
            for child_group in current_group.groups.values():
                found_elt = self.search_by_proximity(ref, child_group, search_dim, local_apex_reached,
                                                     is_coordinate_variable)
                if found_elt is not None:
                    break
            return found_elt

        # If here, did not find
        else:
            return None

    def __escape_index_error(self, match, group_name):
        """Return the group in a match if it exists, an empty string otherwise.

        :param match: regex match
        :param group_name: group name
        :return: match group
        """
        try:
            return match.group(group_name)
        except IndexError:
            return ""

    def resolve_references(self, var, old_var):
        """In a given variable, replace all references to other variables in its attributes by absolute references.

        :param var: flattened variable in which references should be renamed with absolute references
        :param old_var: original variable (in group structure)
        """
        print(_AttributeProperties)
        for attr in _AttributeProperties:
            if attr.name in var.__dict__:
#                attr_value = var.getncattr(attr.name)
                attr_value = self.getncattr(var, attr.name)
                # Parse attribute value
                parsed_attr = parse_var_attr(attr_value)

                # Resolved references in parsed as required by attribute properties
                resolved_parsed_attr = collections.OrderedDict()

                for k, v in parsed_attr.items():
                    new_k = self.resolve_reference(k, old_var, attr) if attr.resolve_key else k

                    new_v = ([self.resolve_reference(x, old_var, attr) for x in parsed_attr[k]]
                             if attr.resolve_value and parsed_attr[k] is not None else parsed_attr[k])

                    resolved_parsed_attr[new_k] = new_v

                # Re-generate attribute value string with resolved references
                var.setncattr(attr.name, generate_var_attr_str(resolved_parsed_attr))

    def adapt_references(self, var):
        """In a given variable, replace all references to variables in attributes by references to the new names in the
        flattened NetCDF. All references have to be already resolved as absolute references.

        :param var: flattened variable in which references should be renamed with new names
        """
        for attr in _AttributeProperties:
            if attr.name in var.__dict__:
                #attr_value = var.getncattr(attr.name)
                attr_value = self.getncattr(var, attr.name)
                # Parse attribute value
                parsed_attr = parse_var_attr(attr_value)

                adapted_parsed_attr = collections.OrderedDict()

                for k, v in parsed_attr.items():
                    new_k = self.adapt_name(k, attr) if attr.resolve_key else k

                    new_v = ([self.adapt_name(x, attr) for x in parsed_attr[k]]
                             if attr.resolve_value and parsed_attr[k] is not None else parsed_attr[k])

                    adapted_parsed_attr[new_k] = new_v

                new_attr_value = generate_var_attr_str(adapted_parsed_attr)
                var.setncattr(attr.name, new_attr_value)

                logging.info("   attribute '{}'  in '{}': references '{}' renamed as '{}'"
                      .format(attr.name, var.name, attr_value, new_attr_value))

    def adapt_name(self, resolved_ref, attr):
        """Return name of flattened reference. If not found, raise exception or continue warning.

        :param resolved_ref: resolved reference to adapt
        :param attr: _AttributeProperties object enum item to know in which dict to look for name mapping
        :return: adapted reference
        """
        # If ref contains Error message, leave as such
        if self.__ref_not_found_error in resolved_ref:
            return resolved_ref

        # Select highest priority map
        if attr.ref_to_dim > attr.ref_to_var:
            name_mapping = self.__dim_map
        if attr.ref_to_dim < attr.ref_to_var:
            name_mapping = self.__var_map

        # Try to find mapping
        try:
            return name_mapping[resolved_ref]

        # If not found, look in other map if allowed
        except KeyError:

            if attr.ref_to_dim and attr.ref_to_var:
                name_mapping = self.__dim_map if attr.ref_to_dim < attr.ref_to_var else self.__var_map
                try:
                    return name_mapping[resolved_ref]
                except KeyError:
                    pass

        # If still not found, check if any standard name is allowed
        if attr.accept_standard_names:
            return resolved_ref
        # If not, raise exception
        else:
            return self.handle_reference_error(resolved_ref)

    def pathname(self, group, name):
        """Compose full path name to an element in a group structure: /path/to/group/elt

        :param group: group containing element
        :param name: name of the element
        :return: pathname
        """
        if group.parent is None:
            return self.__default_separator + name
        else:
#            return self.__pathname_format.format(group.path, name)
            return self.__pathname_format.format(self.path(group), name)

    def generate_mapping_str(self, input_group, name, new_name):
        """Generate a string representing the name mapping of an element before and after flattening.

        :param input_group: group containing the non-flattened element
        :param name: name of the non-flattened element
        :param new_name: name of the flattened element
        :return: string representing the name mapping for the element
        """
        original_pathname = self.pathname(input_group, name)
        mapping_str = self.__mapping_str_format.format(new_name, original_pathname)
        return mapping_str

    def convert_path_to_valid_name(self, pathname):
        """Generate valid name from path.

        :param pathname: pathname
        :return: valid NetCDF name
        """
        return pathname.replace(self.__default_separator, '', 1).replace(self.__default_separator, self.__new_separator)

    def generate_flattened_name(self, input_group, orig_name):
        """Convert full path of an element to a valid NetCDF name:
            - the name of an element is the concatenation of its containing group and its name,
            - replaces / from paths (forbidden as NetCDF name),
            - if name is longer than 255 characters, replace path to group by hash,
            - if name is still too long, replace complete name by hash.

        :param input_group: group containing element
        :param orig_name: original name of the element
        :return: new valid name of the element
        """
        # If element is at root: no change
        if input_group.parent is None:
            new_name = orig_name

        # If element in child group, concatenate group path and element name
        else:
            full_name = self.convert_path_to_valid_name(input_group.path) + self.__new_separator + orig_name
            new_name = full_name

            # If resulting name is too long, hash group path
            if len(new_name) >= self.__max_name_len:
#                group_hash = hashlib.sha1(input_group.path.encode("UTF-8")).hexdigest()
                group_hash = hashlib.sha1(self.path(input_group).encode("UTF-8")).hexdigest()
                new_name = group_hash + self.__new_separator + orig_name

                # If resulting name still too long, hash everything
                if len(new_name) >= self.__max_name_len:
                    new_name = hashlib.sha1(full_name.encode("UTF-8")).hexdigest()
        return new_name

    def handle_reference_error(self, ref, context=None):
        """Depending on lax/strict mode, either raise exception or log warning. If lax, return reference placeholder.

        :param ref: reference
        :param context: additional context info to add to message
        :return: if continue with warning, error replacement name for reference
        """
        message = "Reference '{}' could not be resolved".format(ref)
        if context is not None:
            message = message + " from {}".format(context)
        if self.__lax_mode:
            warnings.warn(message)
            return self.__ref_not_found_error + "_" + ref
        else:
            raise ReferenceException(message)


class ReferenceException(Exception):
    """Exception raised when references in attributes cannot be resolved.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        super().__init__(message)
