"""Configuration for netCDF group flattening.

.. versionadded:: (cfdm) HDFVER

"""
from dataclasses import dataclass

# Maximum length of name after which it is replaced with its hash
max_name_len = 256

# Separator for groups in the input dataset
group_separator = "/"

# Replacment for 'group_separator' in flattened names
flattener_separator = "__"

# Name prefix when reference can't be resolved. Only used if
# 'lax_mode=True' in `flatten`.
ref_not_found_error = "REF_NOT_FOUND"

# Default size, in bytes, of slice to use when copying data arrays
default_copy_slice_size = 134217728

# NetCDF global attribute containing the mapping of flattened
# attribute names to grouped attribute names
flattener_attribute_map = "__flattener_attribute_map"

# NetCDF global attribute containing the mapping of flattened
# dimension names to grouped attribute names
flattener_dimension_map = "__flattener_dimension_map"

# NetCDF global attribute containing the mapping of flattened
# variable names to grouped attribute names
flattener_variable_map = "__flattener_variable_map"


@dataclass()
class AttributeFeatures:
    """Data class that defines attribute flattening features.

    For a named netCDF attribute, the features a define how the
    contents of the attribute are flattened.

    .. versionadded:: (cfdm) HDFVER

    """

    # name: The attribute name
    name: str
    # ref_to_dim: Positive integer if contains references to
    #             dimensions (highest int have priority)
    ref_to_dim: int = 0
    # ref_to_var: Positive integer if contains references to variables
    #             (highest int have priority)
    ref_to_var: int = 0
    # resolve_key: True if 'keys' have to be resolved in 'key1: value1
    #              key2: value2 value3' or 'key1 key2'
    resolve_key: bool = False
    # resolve_value: True if 'values' have to be resolved in 'key1:
    #                value1 key2: value2 value3'
    resolve_value: bool = False
    # stop_at_local_apex: True if upward research in the hierarchy has
    #                     to stop at local apex
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
# Set flattening features for named CF attributes
# --------------------------------------------------------------------
attribute_features = {
    attr.name: attr
    for attr in (
        # Coordinates
        AttributeFeatures(
            name="coordinates",
            ref_to_var=1,
            resolve_key=True,
            stop_at_local_apex=True,
        ),
        AttributeFeatures(
            name="ancillary_variables", ref_to_var=1, resolve_key=True
        ),
        AttributeFeatures(name="climatology", ref_to_var=1, resolve_key=True),
        # Cell measures
        AttributeFeatures(
            name="cell_measures", ref_to_var=1, resolve_value=True
        ),
        # Coordinate references
        AttributeFeatures(
            name="formula_terms", ref_to_var=1, resolve_value=True
        ),
        AttributeFeatures(
            name="grid_mapping",
            ref_to_var=1,
            resolve_key=True,
            resolve_value=True,
        ),
        AttributeFeatures(name="geometry", ref_to_var=1, resolve_key=True),
        AttributeFeatures(
            name="interior_ring", ref_to_var=1, resolve_key=True
        ),
        AttributeFeatures(
            name="node_coordinates", ref_to_var=1, resolve_key=True
        ),
        AttributeFeatures(name="node_count", ref_to_var=1, resolve_key=True),
        AttributeFeatures(name="nodes", ref_to_var=1, resolve_key=True),
        AttributeFeatures(
            name="part_node_count", ref_to_var=1, resolve_key=True
        ),
        # Compression by gathering
        AttributeFeatures(name="compress", ref_to_dim=1, resolve_key=True),
        # Discrete sampling geometries
        AttributeFeatures(
            name="instance_dimension", ref_to_dim=1, resolve_key=True
        ),
        AttributeFeatures(
            name="sample_dimension", ref_to_dim=1, resolve_key=True
        ),
        # Cell methods
        AttributeFeatures(
            name="cell_methods",
            ref_to_dim=2,
            ref_to_var=1,
            resolve_key=True,
            accept_standard_names=True,
            limit_to_scalar_coordinates=True,
        ),
        # Domain variables
        AttributeFeatures(name="dimensions", ref_to_dim=1, resolve_key=True),
        # Aggregation variables
        AttributeFeatures(
            name="aggregated_dimensions", ref_to_dim=1, resolve_key=True
        ),
        AttributeFeatures(
            name="aggregated_data", ref_to_var=1, resolve_value=True
        ),
        # UGRID variables
        AttributeFeatures(name="mesh", ref_to_var=1, resolve_key=True),
        AttributeFeatures(
            name="edge_coordinates", ref_to_var=1, resolve_key=True
        ),
        AttributeFeatures(
            name="face_coordinates", ref_to_var=1, resolve_key=True
        ),
        AttributeFeatures(
            name="edge_node_connectivity", ref_to_var=1, resolve_key=True
        ),
        AttributeFeatures(
            name="face_node_connectivity", ref_to_var=1, resolve_key=True
        ),
        AttributeFeatures(
            name="face_face_connectivity", ref_to_var=1, resolve_key=True
        ),
        AttributeFeatures(
            name="edge_face_connectivity", ref_to_var=1, resolve_key=True
        ),
        AttributeFeatures(
            name="face_edge_connectivity", ref_to_var=1, resolve_key=True
        ),
        AttributeFeatures(
            name="edge_dimension", ref_to_dim=1, resolve_key=True
        ),
        AttributeFeatures(
            name="face_dimension", ref_to_dim=1, resolve_key=True
        ),
    )
}
