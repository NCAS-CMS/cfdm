"""Functions for resolving references inside `xnetcdf` CF attributes."""

from dataclasses import dataclass
from typing import Callable


def resolve_references(dataset):
    """Resolve all references in a dataset.

    A reference comprises the name of a variable or dimension within a
    string-valued attribute.

    .. versionadded:: (cfdm) 1.13.3.0

    :Parameters:

        dataset: `xnetcdf.Dataset`
            The dataset, which will have its attribute dictionaries
            updated in-place.

    :Returns:

        `None`

    """
    for variable in dataset.all_variables.values():
        attrs = variable.attrs
        for name in set(attrs).intersection(resolvable_attributes):
            attrs[name] = resolve_attribute(name, attrs[name], variable)


def resolve_attribute(name, attr_value, variable):
    """Resolve all references in an attribute.

    A reference comprises the name of a variable or dimension within a
    string-valued attribute.

    .. versionadded:: (cfdm) 1.13.3.0

    :Parameters:

        name: `str`
            The attribute name.

        attr_value:
            The attribute value.

        variable: `xnetcdf.Variable`
            The parent variable.

    :Returns:

            The resolved attribute.

    """
    resolve = resolvable_attributes[name]
    if resolve.name != name:
        raise ValueError("Wrong ResolveAttribute!")

    return resolve.resolver(attr_value, variable, coord=resolve.coord)


def resolve_reference(
    ref, variable, dim=False, var=False, dim_then_var=True, coord=False
):
    """Resolve a single reference within an attribute.

    Resolves the absolute path to a coordinate variable within the
    group structure.

    .. versionadded:: (cfdm) 1.13.3.0

    :Parameters:

        ref: `str`
            The reference to resolve.

        variable: `xnetcdf.`Variable`
            The original variable object that has the attribute that
            contains the reference.

        dim: `bool`, optional
            True if the reference is a dimension.

        var: `bool`, optional
            True if the reference is a variable.

        dim_then_var: `bool`, optional
            If *dim* and *var* are both True, then *dim_then_var*
            being True (the default) means try to resolve a dimension
            first, and if that's not possible then as a variable; and
            vice versa for *dim_then_var* being False.

        coord: `bool`, optional
            If True then the reference is for a Unidata coordinate
            variable.

    :Returns:

        `str`
            The absolute path to the reference.

    """
    second_search = None
    if dim:
        if var:
            first_search = "dim" if dim_then_var else "var"
            second_search = "var" if first_search == "dim" else "dim"
        else:
            first_search = "dim"
    else:
        first_search = "var"

    resolved_ref = None
    if "/" in ref:
        # Reference is to be searched by absolute or relative path
        resolved_ref = search_by_absolute_or_relative_path(
            ref, variable, first_search
        )
        if resolved_ref is None and second_search:
            resolved_ref = search_by_absolute_or_relative_path(
                ref, variable, second_search
            )
    else:
        # Reference is to be searched by proximity
        resolved_ref = search_by_proximity(
            ref, variable, first_search, coord=coord
        )
        if resolved_ref is None and second_search:
            resolved_ref = search_by_proximity(
                ref, variable, second_search, coord=coord
            )

    if resolved_ref is not None:
        # Return the resoved reference
        return resolved_ref

    # Reference couldn't be resolved, so return it unchanged. This
    # could be the case for an external variable (e.g. the 'areacello'
    # in cell_measures attribute 'area: areacello'; the 'sea' in the
    # cell_methods attribute 'maximum where sea').
    return ref


def search_by_absolute_or_relative_path(ref, variable, search_type):
    """Search for reference targets by absolute or relative path.

    Find the target of a reference that is defined by an absolute path
    (one that starts with '/') or a relative path (one that contains,
    but does not start with, '/').

    .. versionadded:: (cfdm) 1.13.3.0

    :Parameters:

        ref: `str`
            The reference to be searched for.

        variable: `xnetcdf.Variable`
            The parent variable.

        search_type: `str`
            The type of variable being searched for. Either ``'dim'``
            or ``'var'``.

    :Returns:

            The resolved attribute.

    """
    g = variable.parent
    parts = ref.split("/")
    path = "/".join(parts[:-1])
    try:
        g = g[path]
    except KeyError:
        #
        return

    name = parts[-1]

    if search_type == "dim":
        x = g.dimensions.get(name)
    else:
        x = g.variables.get(name)

    if x is not None:
        return x.path


def search_by_proximity(ref, variable, search_type, coord=False):
    """Search for reference targets by proximity.

    The reference contains no '/' characters and is searched for in
    the direct ancestors of the current group in which the variable is
    defined.

    Coordinate variable references that cannot be found by proximity
    are searched for laterally (see `coordinate_lateral_search`).

    .. versionadded:: (cfdm) 1.13.3.0

    :Parameters:

        ref: `str`
            The reference to be searched for.

        variable: `xnetcdf.Variable`
            The parent variable.

        search_type: `str`
            The type of variable being searched for. Either ``'dim'``
            or ``'var'``.

        coord: `bool`, optional
            True if the reference is a Unidata coordinate variable.

    :Returns:

         `str` or `None`

    """
    local_apex_group = None

    coord = coord and search_type == "var" and ref in variable.dimensions
    if coord:
        # Find the local apex group
        g = variable.parent
        dim = None
        depth = 0
        while g is not None:
            dim = g.dimensions.get(ref)
            if dim is not None:
                break

            depth += 1
            g = g.parent

        local_apex_group = g

    g = variable.parent
    while g is not None:
        if search_type == "dim":
            x = g.dimensions.get(ref)
        else:
            x = g.variables.get(ref)

        if coord:
            if x is not None and x.dimensions == (ref,):
                return x.path
        elif x is not None:
            return x.path

        if g is local_apex_group:
            break

        g = g.parent

    if local_apex_group is None:
        return

    # Still here? Then 'ref' is a coordinate variable, so do a lateral
    #             search from the local apex group.
    return coordinate_lateral_search(ref, local_apex_group, depth)


def coordinate_lateral_search(ref, group, depth):
    """Search for coordinate variable reference targets by laterally.

    Performs a lateral search starting in *group* and proceeding to
    *depth* layers of sub-groups. If *depth* is 0, only *group* is
    searched; if *depth* is 1 then direct sub-groups are also searched;
    if *depth* is 2 then direct sub-groups of those sub-groups are also
    searched; etc.

    If *depth* is less than 0 then no search is done.

    .. versionadded:: (cfdm) 1.13.3.0

    :Parameters:

        ref: `str`
            The name of the reference to be resolved (e.g. ``'lat'``).

        group: `xnetcdf.Group`
            The group containing the variable that has the attribute
            which contains the reference.

        depth: `int`


    :Returns:

        `str` or `None`
            The resolved reference (e.g. ``'/lat'``). If the reference
            could not be resolved, then `None` is returned.

    """
    if depth < 0:
        # Not found in the tree from 'group' down to the given depth
        return

    var = group.variables.get(ref)
    if var is not None and var.dimensions == (ref,):
        # Found
        return var.path

    if not depth:
        return

    for g in group.groups.values():
        var = g.variables.get(ref)
        if var is not None and var.dimensions == (ref,):
            # Found
            return var.path

        path = coordinate_lateral_search(ref, g, depth - 1)
        if path is not None:
            # Found
            return path


def resolve_pattern_1(value, variable, coord=False):
    """Resolve references in a pattern 1 attribute.

    Resolve references in an attribute whose value has one of the
    following patterns:

    * ''
    * 'var1'
    * 'var1 var2'

    E.g. ``coordinates``, ``ancillary_variables``,
    ``edge_node_connectivity``

    .. versionadded:: (cfdm) 1.13.3.0

    """
    try:
        resolved = [
            resolve_reference(x, variable, var=True, coord=coord)
            for x in value.split()
        ]
    except AttributeError:
        # 'value' is not a string
        return value
    else:
        return " ".join(resolved)


def resolve_pattern_2(value, variable, coord=False):
    """Resolve references in a pattern 2 attribute.

    Resolve references in an attribute whose value has one of the
    following patterns:

    * ''
    * 'dim1'
    * 'dim1 dim2'

    E.g. ``dimensions``, ``face_dimension``

    .. versionadded:: (cfdm) 1.13.3.0

    """
    try:
        resolved = [
            resolve_reference(x, variable, dim=True) for x in value.split()
        ]
    except AttributeError:
        # 'value' is not a string
        return value
    else:
        return " ".join(resolved)


def resolve_pattern_3(value, variable, coord=False):
    """Resolve references in a pattern 3 attribute.

    Resolve references in an attribute whose value has one of the
    following patterns:

    * ''
    * 'key1: var1'
    * 'key1: var1 key2: var2'
    * 'key1: var1 var2'
    * 'key1: var1 var2 key2: var3'

    E.g. ``cell_measures``, ``aggregated_data``, ``formula_terms``,
    ``interpolation_parameters``

    .. versionadded:: (cfdm) 1.13.3.0

    """
    try:
        resolved = []
        for ref in value.split():
            if not ref.endswith(":"):
                ref = resolve_reference(ref, variable, var=True, coord=coord)

            resolved.append(ref)

    except AttributeError:
        return value
    else:
        return " ".join(resolved)


def resolve_pattern_4(value, variable, coord=False):
    """Resolve references in a pattern 4 attribute.

    Resolve references in an attribute whose value has one of the
    following patterns:

    * ''
    * 'var1: var2'
    * 'var1: var2 var3'
    * 'var1: var2 var3: var4 var5'
    * 'var1: var2 var3 var4: var5 var6'
    * 'var1: var2: var3"
    * 'var1: var2: var3 var4: var5"

    E.g. ``grid_mapping``, ``coordinate_interpolation``

    .. versionadded:: (cfdm) 1.13.3.0

    :Returns:

        `str`
             The resolved string. If *value* was not a string, then it
             is returned unchanged.

    """
    try:
        resolved = []
        for ref in value.split():
            if ref.endswith(":"):
                ref = resolve_reference(
                    ref[:-1], variable, var=True, coord=coord
                )
                ref += ":"
            else:
                ref = resolve_reference(ref, variable, var=True, coord=coord)

            resolved.append(ref)
    except AttributeError:
        # 'value' is not a string
        return value
    else:
        return " ".join(resolved)


def resolve_pattern_5(value, variable, coord=False):
    """Resolve references in a pattern 5 attribute.

    Resolve references in a cell_methods attribute.

    .. versionadded:: (cfdm) 1.13.3.0

    :Parameters:

    :Returns:

        `str`

    """
    import re

    resolved = []
    # ------------------------------------------------------------
    # Split the cell_methods string into a list of strings ready
    # for parsing. For example:
    #
    #   'lat: lon: mean (interval: 1 hour) time: max'
    #
    # would be split up into:
    #
    #   ['lat:', 'lon:', 'mean', '(interval: 1 hour)', 'time:', 'max']
    # ------------------------------------------------------------
    try:
        cell_methods = re.findall(r"\([^)]*\)|\S+", value)
    except TypeError:
        # 'value' is not a string
        return value

    previous_ref = None
    for ref in cell_methods:
        if ref.endswith(":"):
            ref = resolve_reference(
                ref[:-1],
                variable,
                dim=True,
                var=True,
                dim_then_var=True,
                coord=coord,
            )
            resolved.append(ref + ":")
            previous_ref = "axis"
            continue

        if previous_ref == "axis":
            resolved.append(ref)
            previous_ref = "method"
            continue

        if previous_ref == "method":
            if ref == "within":
                resolved.append(ref)
                previous_ref = "climatological within"
                continue

            if ref == "where":
                resolved.append(ref)
                previous_ref = "where"
                continue

        if previous_ref == "climatological within":
            resolved.append(ref)
            previous_ref = "years|days"
            continue

        if previous_ref == "years|days" and ref == "over":
            resolved.append(ref)
            previous_ref = "climatological over"
            continue

        if previous_ref == "climatological over":
            resolved.append(ref)
            previous_ref = "years|days"
            continue

        if previous_ref == "where":
            ref = resolve_reference(ref, variable, var=True, coord=coord)
            resolved.append(ref)
            previous_ref = "type1"
            continue

        if previous_ref == "type1" and ref == "over":
            resolved.append(ref)
            previous_ref = "over"
            continue

        if previous_ref == "over":
            ref = resolve_reference(ref, variable, var=True, coord=coord)
            resolved.append(ref)
            previous_ref = "type2"
            continue

        # Still here?
        resolved.append(ref)
        previous_ref = None

    return " ".join(resolved)


def resolve_pattern_6(value, variable, coord=False):
    """Resolve references in a pattern 6 attribute.

    Resolve references in an attribute whose value has one of the
    following patterns:

    * ''
    * 'dim1: var1 dim2'
    * 'dim1: var1 dim2 dim3: var2 dim4'
    * 'dim1: var1 dim2 dim3 dim4: var2 dim5 dim6'

    E.g. ``tie_point_mapping``

    .. versionadded:: (cfdm) 1.13.3.0

    """
    try:
        resolved = []
        next_ref = None
        for ref in value.split():
            if ref.endswith(":"):
                ref = resolve_reference(ref[:-1], variable, dim=True)
                ref += ":"
                next_ref = "variable"
            elif next_ref == "variable":
                ref = resolve_reference(ref, variable, var=True, coord=coord)
                next_ref = "dimension"
            elif next_ref == "dimension":
                ref = resolve_reference(ref, variable, dim=True)
                next_ref = "dimension"

            resolved.append(ref)
    except AttributeError:
        # 'value' is not a string
        return value
    else:
        return " ".join(resolved)


@dataclass
class ResolveAttribute:
    """How to resolve references in an attribute.

    .. versionadded:: (cfdm) 1.13.3.0

    """

    # name: The name of attribute containing the references to be
    #       resolved
    name: str
    # resolver: The function that will do the reference resolving
    resolver: Callable
    # coord: True if the references are Unidata coordinate variables
    coord: bool = False


# ====================================================================
# Define the reference-resolving strategies for each atribute type
# ====================================================================
resolvable_attributes = {
    attr.name: attr
    for attr in (
        # ------------------------------------------------------------
        # Coordinates
        # ------------------------------------------------------------
        ResolveAttribute(
            name="coordinates", resolver=resolve_pattern_1, coord=True
        ),
        # ------------------------------------------------------------
        # Bounds
        # ------------------------------------------------------------
        ResolveAttribute(name="bounds", resolver=resolve_pattern_1),
        ResolveAttribute(name="climatology", resolver=resolve_pattern_1),
        # ------------------------------------------------------------
        # Cell methods
        # ------------------------------------------------------------
        ResolveAttribute(name="cell_methods", resolver=resolve_pattern_5),
        # ------------------------------------------------------------
        # Cell measures
        # ------------------------------------------------------------
        ResolveAttribute(name="cell_measures", resolver=resolve_pattern_3),
        # ------------------------------------------------------------
        # Coordinate references
        # ------------------------------------------------------------
        ResolveAttribute(name="formula_terms", resolver=resolve_pattern_3),
        ResolveAttribute(name="grid_mapping", resolver=resolve_pattern_4),
        # ------------------------------------------------------------
        # Ancillary variables
        # ------------------------------------------------------------
        ResolveAttribute(
            name="ancillary_variables", resolver=resolve_pattern_1
        ),
        # ------------------------------------------------------------
        # Compression by gathering
        # ------------------------------------------------------------
        ResolveAttribute(name="compress", resolver=resolve_pattern_2),
        # ------------------------------------------------------------
        # Discrete sampling geometries
        # ------------------------------------------------------------
        ResolveAttribute(
            name="instance_dimension", resolver=resolve_pattern_2
        ),
        ResolveAttribute(name="sample_dimension", resolver=resolve_pattern_2),
        # ------------------------------------------------------------
        # Domain variables
        # ------------------------------------------------------------
        ResolveAttribute(name="dimensions", resolver=resolve_pattern_2),
        # ------------------------------------------------------------
        # Aggregation variables
        # ------------------------------------------------------------
        ResolveAttribute(
            name="aggregated_dimensions", resolver=resolve_pattern_2
        ),
        ResolveAttribute(name="aggregated_data", resolver=resolve_pattern_3),
        # ------------------------------------------------------------
        # Cell geometries
        # ------------------------------------------------------------
        ResolveAttribute(name="geometry", resolver=resolve_pattern_1),
        ResolveAttribute(name="interior_ring", resolver=resolve_pattern_1),
        ResolveAttribute(name="node_coordinates", resolver=resolve_pattern_1),
        ResolveAttribute(name="node_count", resolver=resolve_pattern_1),
        ResolveAttribute(name="nodes", resolver=resolve_pattern_1),
        ResolveAttribute(name="part_node_count", resolver=resolve_pattern_1),
        # ------------------------------------------------------------
        # UGRID variables
        # ------------------------------------------------------------
        ResolveAttribute(name="mesh", resolver=resolve_pattern_1),
        ResolveAttribute(name="node_coordinates", resolver=resolve_pattern_1),
        ResolveAttribute(name="edge_coordinates", resolver=resolve_pattern_1),
        ResolveAttribute(name="face_coordinates", resolver=resolve_pattern_1),
        ResolveAttribute(
            name="edge_node_connectivity", resolver=resolve_pattern_1
        ),
        ResolveAttribute(
            name="edge_edge_connectivity", resolver=resolve_pattern_1
        ),
        ResolveAttribute(
            name="edge_face_connectivity", resolver=resolve_pattern_1
        ),
        ResolveAttribute(
            name="face_node_connectivity", resolver=resolve_pattern_1
        ),
        ResolveAttribute(
            name="face_edge_connectivity", resolver=resolve_pattern_1
        ),
        ResolveAttribute(
            name="face_face_connectivity", resolver=resolve_pattern_1
        ),
        ResolveAttribute(name="edge_dimension", resolver=resolve_pattern_2),
        ResolveAttribute(name="face_dimension", resolver=resolve_pattern_2),
        # ------------------------------------------------------------
        # Compression by coordinate subsampling
        # ------------------------------------------------------------
        ResolveAttribute(
            name="coordinate_interpolation", resolver=resolve_pattern_4
        ),
        ResolveAttribute(name="tie_point_mapping", resolver=resolve_pattern_6),
        ResolveAttribute(
            name="interpolation_parameters", resolver=resolve_pattern_3
        ),
        ResolveAttribute(name="bounds_tie_points", resolver=resolve_pattern_1),
        # ------------------------------------------------------------
        # Quantization
        # ------------------------------------------------------------
        ResolveAttribute(name="quantization", resolver=resolve_pattern_1),
    )
}
