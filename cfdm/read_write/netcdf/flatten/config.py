"""Configuration for netCDF group flattening.

.. versionadded:: (cfdm) 1.11.2.0

Portions of this code were adapted from the `netcdf_flattener`
library, which carries the following Apache 2.0 License:

Copyright (c) 2020 EUMETSAT

Licensed to the Apache Software Foundation (ASF) under one or more
contributor license agreements. The ASF licenses this file to you
under the Apache License, Version 2.0 (the "License"); you may not use
this file except in compliance with the License. You may obtain a copy
of the License at http://www.apache.org/licenses/LICENSE-2.0.

"""

from dataclasses import dataclass

# Maximum length of name after which it is replaced with its hash
max_name_len = 256

# Separator for groups in the input dataset
group_separator = "/"

# Replacement for 'group_separator' in flattened names
flattener_separator = "__"

# Name prefix when reference can't be resolved. Only used if
# 'lax_mode=True' in `flatten`.
ref_not_found_error = "REF_NOT_FOUND"

# NetCDF global attribute in the flattened dataset containing the
# mapping of flattened attribute names to grouped attribute names
flattener_attribute_map = "_flattener_attribute_map"

# NetCDF global attribute in the flattened dataset containing the
# mapping of flattened dimension names to grouped attribute names
flattener_dimension_map = "_flattener_dimension_map"

# NetCDF global attribute in the flattened dataset containing the
# mapping of flattened variable names to grouped attribute names
flattener_variable_map = "_flattener_variable_map"


@dataclass()
class FlatteningRules:
    """Define the flattening rules for a netCDF attribute.

    For a named netCDF attribute, the rules a define how the contents
    of the attribute are flattened. For instance, it has to be defined
    that the ``ancillary_variables`` attribute contains the names of
    other netCDF variables.

    .. versionadded:: (cfdm) 1.11.2.0

    """

    # name: The name of attribute containing the reference to be
    #       flattened
    name: str
    # ref_to_dim: Positive integer if contains references to
    #             dimensions. If ref_to_dim and ref_to_var are both
    #             positive then the rule with the greater value is
    #             tested first.
    ref_to_dim: int = 0
    # ref_to_var: Positive integer if contains references to
    #             variables. If ref_to_dim and ref_to_var are both
    #             positive then the rule with the greater value is
    #             tested first.
    ref_to_var: int = 0
    # resolve_key: True if 'keys' have to be resolved in 'key1: value1
    #              key2: value2 value3' or 'key1 key2'
    resolve_key: bool = False
    # resolve_value: True if 'values' have to be resolved in 'key1:
    #                value1 key2: value2 value3'
    resolve_value: bool = False
    # stop_at_local_apex: True if upward research in the hierarchy has
    #                     to stop at local apex.
    stop_at_local_apex: bool = False
    # accept_standard_names: True if any standard name is valid in
    #                        place of references (in which case no
    #                        exception is raised if a reference cannot
    #                        be resolved, and the standard name is
    #                        used in place)
    accept_standard_names: bool = False
    # limit_to_scalar_coordinates: True if references to variables are
    #                              only resolved if present as well in
    #                              the 'coordinates' attributes of the
    #                              variable, and they are scalar.
    limit_to_scalar_coordinates: bool = False


# --------------------------------------------------------------------
# Define the flattening rules for named CF attributes
# --------------------------------------------------------------------
flattening_rules = {
    attr.name: attr
    for attr in (
        # ------------------------------------------------------------
        # Coordinates
        # ------------------------------------------------------------
        FlatteningRules(
            name="coordinates",
            ref_to_var=1,
            resolve_key=True,
            stop_at_local_apex=True,
        ),
        FlatteningRules(name="bounds", ref_to_var=1, resolve_key=True),
        FlatteningRules(name="climatology", ref_to_var=1, resolve_key=True),
        # ------------------------------------------------------------
        # Cell methods
        # ------------------------------------------------------------
        FlatteningRules(
            name="cell_methods",
            ref_to_dim=2,
            ref_to_var=1,
            resolve_key=True,
            accept_standard_names=True,
            limit_to_scalar_coordinates=True,
        ),
        # ------------------------------------------------------------
        # Cell measures
        # ------------------------------------------------------------
        FlatteningRules(
            name="cell_measures", ref_to_var=1, resolve_value=True
        ),
        # ------------------------------------------------------------
        # Coordinate references
        # ------------------------------------------------------------
        FlatteningRules(
            name="formula_terms", ref_to_var=1, resolve_value=True
        ),
        FlatteningRules(
            name="grid_mapping",
            ref_to_var=1,
            resolve_key=True,
            resolve_value=True,
        ),
        # ------------------------------------------------------------
        # Ancillary variables
        # ------------------------------------------------------------
        FlatteningRules(
            name="ancillary_variables", ref_to_var=1, resolve_key=True
        ),
        # ------------------------------------------------------------
        # Compression by gathering
        # ------------------------------------------------------------
        FlatteningRules(name="compress", ref_to_dim=1, resolve_key=True),
        # ------------------------------------------------------------
        # Discrete sampling geometries
        # ------------------------------------------------------------
        FlatteningRules(
            name="instance_dimension", ref_to_dim=1, resolve_key=True
        ),
        FlatteningRules(
            name="sample_dimension", ref_to_dim=1, resolve_key=True
        ),
        # ------------------------------------------------------------
        # Domain variables
        # ------------------------------------------------------------
        FlatteningRules(name="dimensions", ref_to_dim=1, resolve_key=True),
        # ------------------------------------------------------------
        # Aggregation variables
        # ------------------------------------------------------------
        FlatteningRules(
            name="aggregated_dimensions", ref_to_dim=1, resolve_key=True
        ),
        FlatteningRules(
            name="aggregated_data", ref_to_var=1, resolve_value=True
        ),
        # ------------------------------------------------------------
        # Cell geometries
        # ------------------------------------------------------------
        FlatteningRules(name="geometry", ref_to_var=1, resolve_key=True),
        FlatteningRules(name="interior_ring", ref_to_var=1, resolve_key=True),
        FlatteningRules(
            name="node_coordinates", ref_to_var=1, resolve_key=True
        ),
        FlatteningRules(name="node_count", ref_to_var=1, resolve_key=True),
        FlatteningRules(name="nodes", ref_to_var=1, resolve_key=True),
        FlatteningRules(
            name="part_node_count", ref_to_var=1, resolve_key=True
        ),
        # ------------------------------------------------------------
        # UGRID variables
        # ------------------------------------------------------------
        FlatteningRules(name="mesh", ref_to_var=1, resolve_key=True),
        FlatteningRules(
            name="edge_coordinates", ref_to_var=1, resolve_key=True
        ),
        FlatteningRules(
            name="face_coordinates", ref_to_var=1, resolve_key=True
        ),
        FlatteningRules(
            name="edge_node_connectivity", ref_to_var=1, resolve_key=True
        ),
        FlatteningRules(
            name="face_node_connectivity", ref_to_var=1, resolve_key=True
        ),
        FlatteningRules(
            name="face_face_connectivity", ref_to_var=1, resolve_key=True
        ),
        FlatteningRules(
            name="edge_face_connectivity", ref_to_var=1, resolve_key=True
        ),
        FlatteningRules(
            name="face_edge_connectivity", ref_to_var=1, resolve_key=True
        ),
        FlatteningRules(name="edge_dimension", ref_to_dim=1, resolve_key=True),
        FlatteningRules(name="face_dimension", ref_to_dim=1, resolve_key=True),
        # ------------------------------------------------------------
        # Compression by coordinate subsampling
        # ------------------------------------------------------------
        FlatteningRules(
            name="coordinate_interpolation",
            ref_to_var=1,
            resolve_key=True,
            resolve_value=True,
        ),
        FlatteningRules(
            name="tie_point_mapping",
            ref_to_dim=2,
            ref_to_var=1,
            resolve_key=True,
            resolve_value=True,
        ),
        FlatteningRules(
            name="interpolation_parameters", ref_to_var=1, resolve_value=True
        ),
        # ------------------------------------------------------------
        # Quantization
        # ------------------------------------------------------------
        FlatteningRules(name="quantization", ref_to_var=1, resolve_key=True),
    )
}
