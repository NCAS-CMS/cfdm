from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4
from math import nan

import logging

logger = logging.getLogger(__name__)

import numpy as np

from ..read_write.netcdf.constants import CF_QUANTIZATION_PARAMETERS
from .reporting import Report
from .standardnames import get_all_current_standard_names


# NOTE SLB: this Mesh object doesn't really belong in the conformance module
# according to context, but it is only usde by the UGRID checker methods
# therefore it should be accessible for this module. (Can't put it in the
# netcdfread module since then we will have circular importing.)
@dataclass()
class Mesh:
    """A UGRID mesh defintion.

    .. versionadded:: (cfdm) 1.11.0.0

    """

    # The netCDF name of the mesh topology variable. E.g. 'Mesh2d'
    mesh_ncvar: Any = None
    # The attributes of the netCDF mesh topology variable.
    # E.g. {'cf_role': 'mesh_topology'}
    mesh_attributes: dict = field(default_factory=dict)
    # The netCDF variable names of the coordinates for each location
    # E.g. {'node': ['node_lat', 'node_lon']}
    coordinates_ncvar: dict = field(default_factory=dict)
    # The netCDF name of the location index set variable.
    # E.g. 'Mesh1_set'
    location_index_set_ncvar: Any = None
    # The attributes of the location index set variable.
    # E.g. {'location': 'node'}
    location_index_set_attributes: dict = field(default_factory=dict)
    # The location of the location index set. E.g. 'edge'
    location: Any = None
    # The zero-based indices of the location index set.
    # E.g. <CF Data(13243): >
    index_set: Any = None
    # The domain topology construct for each location.
    # E.g. {'face': <CF DomainTopology(13243, 4) >}
    domain_topologies: dict = field(default_factory=dict)
    # Cell connectivity constructs for each location.
    # E.g. {'face': [<CF CellConnectivity(13243, 4) >]}
    cell_connectivities: dict = field(default_factory=dict)
    # Auxiliary coordinate constructs for each location.
    # E.g. {'face': [<CF AxuxiliaryCoordinate(13243) >,
    #                <CF AxuxiliaryCoordinate(13243) >]}
    auxiliary_coordinates: dict = field(default_factory=dict)
    # The netCDF dimension spanned by the cells for each
    # location. E.g. {'node': 'nNodes', 'edge': 'nEdges'}
    ncdim: dict = field(default_factory=dict)
    # A unique identifier for the mesh. E.g. 'df10184d806ef1a10f5035e'
    mesh_id: Any = None


class Checker(Report):
    """Contains checks of CF Compliance for Field instantiation from netCDF.

    Holds methods for checking CF compliance. These methods (whose names
    all start with "_check") check the minimum required for mapping the
    file to CFDM structural elements.

    General CF compliance is not checked (e.g. whether or
    not grid mapping variable has a grid_mapping_name attribute)
    except for the case of (so far):
      * whether (computed_)standard_name values are valid according
        to specified criteria under Section 3.3. of the Conformance
        document.

    """

    def _check_standard_names(
        self,
        top_ancestor_ncvar,
        ncvar,
        ncvar_attrs,
        direct_parent_ncvar=None,
        check_is_string=True,
        check_is_in_table=True,
        check_is_in_custom_list=False,
    ):
        """Check the `(computed_)standard_name` attribute for validity.

        Checks performed depend on the `check_*` input flags to enable
        or disable given checks and can include a type check and a
        check as to whether the name is contained in the current
        version of the CF Conventions standard name table, else some
        custom list which is expected to be a small subset of names
        from the table.

        These checks are in the context of the variable and at least
        one parent variable (though the parent can be set at the variable
        itself should no parent exist or be relevant).

        .. versionadded:: NEXTVERSION

        :Parameters:

            top_ancestor_ncvar: `str`
                The netCDF variable name of the ancestor variable
                under which to register the bad standard name at
                the top level.

                This is usually the parent variable of the variable
                `ncvar` which has the component problem, but may be
                a higher parent e.g. grandparent variable, when there is
                an intermediate parent variable in which the problem
                should also be registered using `direct_parent_ncvar`,
                or `ncvar` itself, where no parent variable exists or
                is relevant.

            ncvar: `str`
                The netCDF variable name with the component that
                has the bad standard name.

            ncvar_attrs: `str`
                The variable attributes for the netCDF variable, as
                stored in the 'read_vars' dictionary under the
                'variable_attributes' key.

            direct_parent_ncvar: `str` or `None`, optional
                The netCDF variable name of the variable which is the
                direct parent of the variable `ncvar` which has the
                bad standard name, *only to be provided* if a higher
                parent such as a grandparent variable is set as
                the `top_ancestor_ncvar` where it is also important
                to register the problem on the direct parent.

                If `None`, the default, then the bad standard name
                is not not registered for any further (parent)
                variable than `top_ancestor_ncvar`.

            check_is_string: `bool`
                Whether or not to check if the type of the attribute
                value is a string type. By default this is checked.

            check_is_in_table: `bool`
                Whether or not to check if the attribute value is
                identical to one of the names contained in the
                current version of the CF Conventions standard name
                table (as processed from the canonical XML). By
                default this is checked.

            check_is_in_custom_list: `list`
                Whether or not to check if the attribute value is
                identical to one of the names contained in a list
                of custom values specified. Set to `False` to
                disable this check, else a list of names which is
                a small subset of those in the CF Conventions
                standard name is expected.

                .. note:: If a list is provided for
                          `check_is_in_custom_list` it becomes
                          redundant to check agaist the entire
                          table, therefore `check_is_in_table`
                          must be `False` else a `ValueError`
                          will be raised to reiterate this.

        :Returns:

            `bool` or `None`
                The outcome of the check, where `True` means
                standard name(s) exist and are (all) valid against
                the configured checks, `False` means standard
                name(s) exist but at least one is invalid
                according to those checks, and `None` means no
                (computed_)standard_name was found.

        """
        logger.debug(f"Running _check_standard_names() for: {ncvar}")

        if check_is_in_custom_list and check_is_in_table:
            raise ValueError(
                "Can't set both 'check_is_in_custom_list' and "
                "'check_is_in_table'. The former is expected "
                "to check a subset of the full table hence renders the "
                "latter redundant - set it to False with a custom list."
            )

        any_sn_found = False
        invalid_sn_found = False
        for sn_attr in ("standard_name", "computed_standard_name"):
            # 1. Check if there is a (computed_)standard_name property
            sn_value = ncvar_attrs.get(sn_attr)
            attribute_value = {f"{ncvar}:{sn_attr}": sn_value}
            logger.debug(f"Found a {sn_attr} of '{sn_value}' on {ncvar}")

            if not sn_value:
                continue

            any_sn_found = True
            # 2. Check, if requested, if name is a native or numpy string type
            if check_is_string and not (
                isinstance(sn_value, (str, np.str_, np.bytes_))
            ):
                invalid_sn_found = True
                self._add_message(
                    top_ancestor_ncvar,
                    ncvar,
                    attribute=attribute_value,
                    message=(
                        f"{sn_attr} attribute",
                        "has a value that is not a string",
                    ),
                    conformance="3.3.requirement.1",
                    direct_parent_ncvar=direct_parent_ncvar,
                )

            # 3. Check, if requested, that the SN is in the custom list given
            elif (
                check_is_in_custom_list
                and sn_value not in check_is_in_custom_list
            ):
                invalid_sn_found = True
                self._add_message(
                    top_ancestor_ncvar,
                    ncvar,
                    attribute=attribute_value,
                    message=(
                        f"{sn_attr} attribute",
                        "has a value that is not appropriate to "
                        "the context of the variable in question",
                    ),
                    direct_parent_ncvar=direct_parent_ncvar,
                )

            # 4. Check, if requested, if string is in the list of valid names
            elif (
                check_is_in_table
                and sn_value not in get_all_current_standard_names()
            ):
                invalid_sn_found = True
                logger.warning(
                    f"Detected invalid standard name: '{sn_attr}' of "
                    f"'{sn_value}' for {ncvar}"
                )
                self._add_message(
                    top_ancestor_ncvar,
                    ncvar,
                    message=(
                        f"{sn_attr} attribute",
                        "has a value that is not a valid name contained "
                        "in the current standard name table",
                    ),
                    attribute=attribute_value,
                    conformance="3.3.requirement.2",
                    direct_parent_ncvar=direct_parent_ncvar,
                )

        # Three possible return signatures to cover existence and validity:
        if not any_sn_found:  # no (computed_)standard_name found
            return
        elif invalid_sn_found:  # found at least one invalid standard name
            return False
        else:  # found at least one and all are valid standard names
            return True

    def _check_bounds(
        self, parent_ncvar, coord_ncvar, attribute, bounds_ncvar
    ):
        """Check a bounds variable spans the correct dimensions.

        .. versionadded:: (cfdm) 1.7.0

        Checks that

        * The bounds variable has exactly one more dimension than the
          parent coordinate variable

        * The bounds variable's dimensions, other than the trailing
          dimension are the same, and in the same order, as the parent
          coordinate variable's dimensions.

        :Parameters:

            parent_ncvar: `str`
                The netCDF variable name of the parent that contains
                the coordinates.

            nc: `netCDF4.Dataset`
                The netCDF dataset object.

            coord_ncvar: `str`
                The netCDF variable name of the coordinate variable.

            bounds_ncvar: `str`
                The netCDF variable name of the bounds.

        :Returns:

            `bool`

        """
        attribute = {coord_ncvar + ":" + attribute: bounds_ncvar}

        if attribute == "bounds_tie_points":
            variable_type = "Bounds tie points variable"
        else:
            variable_type = "Bounds variable"

        incorrect_dimensions = (variable_type, "spans incorrect dimensions")

        g = self.read_vars

        bounds_ncvar_attrs = g["variable_attributes"][bounds_ncvar]
        self._check_standard_names(
            parent_ncvar,
            bounds_ncvar,
            bounds_ncvar_attrs,
        )

        if bounds_ncvar not in g["internal_variables"]:
            bounds_ncvar, message = self._missing_variable(
                bounds_ncvar, variable_type
            )
            self._add_message(
                parent_ncvar,
                bounds_ncvar,
                message=message,
                attribute=attribute,
                direct_parent_ncvar=coord_ncvar,
            )
            return False

        ok = True

        c_ncdims = self._ncdimensions(coord_ncvar, parent_ncvar=parent_ncvar)
        b_ncdims = self._ncdimensions(bounds_ncvar, parent_ncvar=parent_ncvar)

        if len(b_ncdims) == len(c_ncdims) + 1:
            if c_ncdims != b_ncdims[:-1]:
                self._add_message(
                    parent_ncvar,
                    bounds_ncvar,
                    message=incorrect_dimensions,
                    attribute=attribute,
                    dimensions=g["variable_dimensions"][bounds_ncvar],
                    direct_parent_ncvar=coord_ncvar,
                )
                ok = False

        else:
            self._add_message(
                parent_ncvar,
                bounds_ncvar,
                message=incorrect_dimensions,
                attribute=attribute,
                dimensions=g["variable_dimensions"][bounds_ncvar],
                direct_parent_ncvar=coord_ncvar,
            )
            ok = False

        return ok

    def _check_geometry_node_coordinates(
        self, field_ncvar, node_ncvar, geometry
    ):
        """Check a geometry node coordinate variable.

        .. versionadded:: (cfdm) 1.8.6

        :Parameters:

            field_ncvar: `str`
                The netCDF variable name of the parent data variable.

            node_ncvar: `str`
                The netCDF variable name of the node coordinate variable.

            geometry: `dict`

        :Returns:

            `bool`

        """
        g = self.read_vars

        geometry_ncvar = g["variable_geometry"].get(field_ncvar)

        geometry_ncvar_attrs = g["variable_attributes"][geometry_ncvar]
        self._check_standard_names(
            node_ncvar,
            geometry_ncvar,
            geometry_ncvar_attrs,
        )

        attribute = {
            field_ncvar
            + ":"
            + geometry_ncvar: " ".join(geometry["node_coordinates"])
        }

        if node_ncvar not in g["internal_variables"]:
            node_ncvar, message = self._missing_variable(
                node_ncvar, "Node coordinate variable"
            )
            self._add_message(
                field_ncvar,
                node_ncvar,
                message=message,
                attribute=attribute,
                direct_parent_ncvar=field_ncvar,
            )
            return False

        ok = True

        if node_ncvar not in geometry.get("node_coordinates", ()):
            self._add_message(
                field_ncvar,
                node_ncvar,
                message=(
                    "Node coordinate variable",
                    "not in node_coordinates",
                ),
                attribute=attribute,
                direct_parent_ncvar=field_ncvar,
            )
            ok = False

        return ok

    def _check_cell_measures(self, field_ncvar, string, parsed_string):
        """Checks requirements.

        * 7.2.requirement.1
        * 7.2.requirement.3
        * 7.2.requirement.4

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            field_ncvar: `str`

            string: `str`
                The value of the netCDF cell_measures attribute.

            parsed_string: `list`

        :Returns:

            `bool`

        """
        attribute = {field_ncvar + ":cell_measures": string}

        incorrectly_formatted = (
            "cell_measures attribute",
            "is incorrectly formatted",
        )
        incorrect_dimensions = (
            "Cell measures variable",
            "spans incorrect dimensions",
        )
        missing_variable = (
            "Cell measures variable",
            "is not in file nor referenced by the external_variables "
            "global attribute",
        )

        g = self.read_vars

        if not parsed_string:
            self._add_message(
                field_ncvar,
                field_ncvar,
                message=incorrectly_formatted,
                attribute=attribute,
                conformance="7.2.requirement.1",
            )
            return False

        parent_dimensions = self._ncdimensions(field_ncvar)
        external_variables = g["external_variables"]

        ok = True
        for x in parsed_string:
            measure, values = list(x.items())[0]
            if len(values) != 1:
                self._add_message(
                    field_ncvar,
                    field_ncvar,
                    message=incorrectly_formatted,
                    attribute=attribute,
                    conformance="7.2.requirement.1",
                )
                ok = False
                continue

            ncvar = values[0]

            # For external variables, the variable will not be in covered
            # in read_vars["variable_attributes"], so in this case we
            # can't rely on the ncvar key being present, hence get().
            # Note that at present this is an outlier since only cell
            # measures can be external (but consult
            # https://cfconventions.org/cf-conventions/
            # cf-conventions.html#external-variables in case this changes).
            ncvar_attrs = g["variable_attributes"].get(ncvar)
            if ncvar_attrs:
                self._check_standard_names(
                    field_ncvar,
                    ncvar,
                    ncvar_attrs,
                )

            unknown_external = ncvar in external_variables

            # Check that the variable exists in the file, or if not
            # that it is listed in the 'external_variables' global
            # file attribute.
            if not unknown_external and ncvar not in g["variables"]:
                self._add_message(
                    field_ncvar,
                    ncvar,
                    message=missing_variable,
                    attribute=attribute,
                    conformance="7.2.requirement.3",
                )
                ok = False
                continue

            if not unknown_external:
                dimensions = self._ncdimensions(ncvar)
                if not unknown_external and not self._dimensions_are_subset(
                    ncvar, dimensions, parent_dimensions
                ):
                    # The cell measure variable's dimensions do NOT span a
                    # subset of the parent variable's dimensions.
                    self._add_message(
                        field_ncvar,
                        ncvar,
                        message=incorrect_dimensions,
                        attribute=attribute,
                        dimensions=g["variable_dimensions"][ncvar],
                        conformance="7.2.requirement.4",
                    )
                    ok = False

        return ok

    def _check_geometry_attribute(self, parent_ncvar, string, parsed_string):
        """Checks requirements.

        .. versionadded:: (cfdm) 1.8.0

        :Parameters:

            parent_ncvar: `str`
                The netCDF variable name of the parent data variable.

            string: `str`
                The value of the netCDF geometry attribute.

            parsed_string: `list`

        :Returns:

            `bool`

        """
        attribute = {parent_ncvar + ":geometry": string}

        incorrectly_formatted = (
            "geometry attribute",
            "is incorrectly formatted",
        )

        g = self.read_vars

        if len(parsed_string) != 1:
            self._add_message(
                parent_ncvar,
                parent_ncvar,
                message=incorrectly_formatted,
                attribute=attribute,
                conformance="?",
            )
            return False

        for ncvar in parsed_string:
            ncvar_attrs = g["variable_attributes"][ncvar]
            self._check_standard_names(
                parent_ncvar,
                ncvar,
                ncvar_attrs,
            )

            # Check that the geometry variable exists in the file
            if ncvar not in g["variables"]:
                ncvar, message = self._missing_variable(
                    ncvar, "Geometry variable"
                )
                self._add_message(
                    parent_ncvar,
                    ncvar,
                    message=message,
                    attribute=attribute,
                    conformance="?",
                )
                return False

        return True

    def _check_ancillary_variables(self, field_ncvar, string, parsed_string):
        """Checks requirements.

        :Parameters:

            field_ncvar: `str`

            ancillary_variables: `str`
                The value of the netCDF ancillary_variables attribute.

            parsed_ancillary_variables: `list`

        :Returns:

            `bool`

        """
        attribute = {field_ncvar + ":ancillary_variables": string}

        incorrectly_formatted = (
            "ancillary_variables attribute",
            "is incorrectly formatted",
        )
        incorrect_dimensions = (
            "Ancillary variable",
            "spans incorrect dimensions",
        )

        g = self.read_vars

        if not parsed_string:
            d = self._add_message(
                field_ncvar,
                field_ncvar,
                message=incorrectly_formatted,
                attribute=attribute,
            )

            # Though an error of sorts, set as debug level message;
            # read not terminated
            if g["debug"]:
                logger.debug(
                    f"    Error processing netCDF variable {field_ncvar}: "
                    f"{d['reason']}"
                )  # pragma: no cover

            return False

        parent_dimensions = self._ncdimensions(field_ncvar)

        ok = True
        for ncvar in parsed_string:
            ncvar_attrs = g["variable_attributes"][ncvar]
            self._check_standard_names(
                field_ncvar,
                ncvar,
                ncvar_attrs,
            )

            # Check that the variable exists in the file
            if ncvar not in g["internal_variables"]:
                ncvar, message = self._missing_variable(
                    ncvar, "Ancillary variable"
                )
                self._add_message(
                    field_ncvar, ncvar, message=message, attribute=attribute
                )
                return False

            if not self._dimensions_are_subset(
                ncvar, self._ncdimensions(ncvar), parent_dimensions
            ):
                # The ancillary variable's dimensions do NOT span a
                # subset of the parent variable's dimensions
                self._add_message(
                    field_ncvar,
                    ncvar,
                    message=incorrect_dimensions,
                    attribute=attribute,
                    dimensions=g["variable_dimensions"][ncvar],
                )
                ok = False

        return ok

    def _check_auxiliary_or_scalar_coordinate(
        self, parent_ncvar, coord_ncvar, string
    ):
        """Checks requirements.

          * 5.requirement.5
          * 5.requirement.6

        :Parameters:

        parent_ncvar: `str`
            NetCDF name of parent data or domain variable.

        :Returns:

            `bool`

        """
        attribute = {parent_ncvar + ":coordinates": string}

        incorrect_dimensions = (
            "Auxiliary/scalar coordinate variable",
            "spans incorrect dimensions",
        )

        g = self.read_vars

        coord_ncvar_attrs = g["variable_attributes"][coord_ncvar]
        self._check_standard_names(
            parent_ncvar,
            coord_ncvar,
            coord_ncvar_attrs,
        )

        if coord_ncvar not in g["internal_variables"]:
            coord_ncvar, message = self._missing_variable(
                coord_ncvar, "Auxiliary/scalar coordinate variable"
            )
            self._add_message(
                parent_ncvar,
                coord_ncvar,
                message=message,
                attribute=attribute,
                conformance="5.requirement.5",
            )
            self._add_message(
                parent_ncvar,
                coord_ncvar,
                message=message,
                attribute=attribute,
                conformance="5.requirement.5",
            )
            return False

        # Check that the variable's dimensions span a subset of the
        # parent variable's dimensions (allowing for char variables
        # with a trailing dimension)
        if not self._dimensions_are_subset(
            coord_ncvar,
            self._ncdimensions(coord_ncvar, parent_ncvar=parent_ncvar),
            self._ncdimensions(parent_ncvar),
        ):
            self._add_message(
                parent_ncvar,
                coord_ncvar,
                message=incorrect_dimensions,
                attribute=attribute,
                dimensions=g["variable_dimensions"][coord_ncvar],
                conformance="5.requirement.6",
            )
            return False

        return True

    def _check_tie_point_coordinates(
        self, parent_ncvar, tie_point_ncvar, string
    ):
        """Checks requirements.

        * 8.3.requirement.1
        * 8.3.requirement.5

        :Parameters:

        parent_ncvar: `str`
            NetCDF name of parent data or domain variable.

        :Returns:

            `bool`

        """
        attribute = {parent_ncvar + ":coordinate_interpolation": string}

        incorrect_dimensions = (
            "Tie point coordinate variable",
            "spans incorrect dimensions",
        )

        g = self.read_vars

        tie_point_ncvar_attrs = g["variable_attributes"][tie_point_ncvar]
        self._check_standard_names(
            parent_ncvar,
            tie_point_ncvar,
            tie_point_ncvar_attrs,
        )

        if tie_point_ncvar not in g["internal_variables"]:
            ncvar, message = self._missing_variable(
                tie_point_ncvar, "Tie point coordinate variable"
            )
            self._add_message(
                parent_ncvar,
                ncvar,
                message=message,
                attribute=attribute,
                conformance="8.3.requirement.1",
            )
            return False

        # Check that the variable's dimensions span a subset of the
        # parent variable's dimensions (allowing for char variables
        # with a trailing dimension)
        if not self._dimensions_are_subset(
            tie_point_ncvar,
            self._ncdimensions(tie_point_ncvar, parent_ncvar=parent_ncvar),
            self._ncdimensions(parent_ncvar),
        ):
            self._add_message(
                parent_ncvar,
                tie_point_ncvar,
                message=incorrect_dimensions,
                attribute=attribute,
                dimensions=g["variable_dimensions"][tie_point_ncvar],
                conformance="8.3.requirement.5",
            )
            return False

        return True

    def _dimensions_are_subset(self, ncvar, dimensions, parent_dimensions):
        """True if dimensions are a subset of the parent dimensions."""
        if not set(dimensions).issubset(parent_dimensions):
            if not (
                self._is_char(ncvar)
                and set(dimensions[:-1]).issubset(parent_dimensions)
            ):
                return False

        return True

    def _check_grid_mapping(
        self, parent_ncvar, grid_mapping, parsed_grid_mapping
    ):
        """Checks requirements.

          * 5.6.requirement.1
          * 5.6.requirement.2
          * 5.6.requirement.3

        :Parameters:

        parent_ncvar: `str`
            NetCDF name of parent data or domain variable.

            grid_mapping: `str`

            parsed_grid_mapping: `dict`

        :Returns:

            `bool`

        """
        attribute = {parent_ncvar + ":grid_mapping": grid_mapping}

        incorrectly_formatted = (
            "grid_mapping attribute",
            "is incorrectly formatted",
        )

        g = self.read_vars

        # Note: we don't call _check_standard_names for the grid mapping
        # check because in this case the standard_name is not standardised

        if not parsed_grid_mapping:
            self._add_message(
                parent_ncvar,
                parent_ncvar,
                message=incorrectly_formatted,
                attribute=attribute,
                conformance="5.6.requirement.1",
            )
            return False

        ok = True
        for x in parsed_grid_mapping:
            grid_mapping_ncvar, values = list(x.items())[0]
            if grid_mapping_ncvar not in g["internal_variables"]:
                ok = False
                grid_mapping_ncvar, message = self._missing_variable(
                    grid_mapping_ncvar, "Grid mapping variable"
                )
                self._add_message(
                    parent_ncvar,
                    grid_mapping_ncvar,
                    message=message,
                    attribute=attribute,
                    conformance="5.6.requirement.2",
                )
                self._add_message(
                    parent_ncvar,
                    grid_mapping_ncvar,
                    message=message,
                    attribute=attribute,
                    conformance="5.6.requirement.2",
                )

            for coord_ncvar in values:
                if coord_ncvar not in g["internal_variables"]:
                    ok = False
                    coord_ncvar, message = self._missing_variable(
                        coord_ncvar, "Grid mapping coordinate variable"
                    )
                    self._add_message(
                        parent_ncvar,
                        coord_ncvar,
                        message=message,
                        attribute=attribute,
                        conformance="5.6.requirement.3",
                    )
                    self._add_message(
                        parent_ncvar,
                        coord_ncvar,
                        message=message,
                        attribute=attribute,
                        conformance="5.6.requirement.3",
                    )

        if not ok:
            return False

        return True

    def _check_compress(self, parent_ncvar, compress, parsed_compress):
        """Check a compressed dimension is valid and in the file."""
        attribute = {parent_ncvar + ":compress": compress}

        incorrectly_formatted = (
            "compress attribute",
            "is incorrectly formatted",
        )
        missing_dimension = ("Compressed dimension", "is not in file")

        if not parsed_compress:
            self._add_message(
                None,
                parent_ncvar,
                message=incorrectly_formatted,
                attribute=attribute,
            )
            return False

        ok = True

        dimensions = self.read_vars["internal_dimension_sizes"]

        for ncdim in parsed_compress:
            if ncdim not in dimensions:
                self._add_message(
                    None,
                    parent_ncvar,
                    message=missing_dimension,
                    attribute=attribute,
                )
                ok = False

        return ok

    def _check_node_coordinates(
        self,
        field_ncvar,
        geometry_ncvar,
        node_coordinates,
        parsed_node_coordinates,
    ):
        """Check node coordinate variables are valid and in the file."""
        attribute = {geometry_ncvar + ":node_coordinates": node_coordinates}

        g = self.read_vars

        # TODO is this necessary for the geometry_ncvar too? Note could
        # call this in one of many methods directly below instead, so where
        # is best to place it if needed? Investigate.
        geometry_ncvar_attrs = g["variable_attributes"][geometry_ncvar]
        self._check_standard_names(
            field_ncvar,
            geometry_ncvar,
            geometry_ncvar_attrs,
        )

        incorrectly_formatted = (
            "node_coordinates attribute",
            "is incorrectly formatted",
        )
        missing_attribute = ("node_coordinates attribute", "is missing")

        if node_coordinates is None:
            self._add_message(
                field_ncvar,
                geometry_ncvar,
                message=missing_attribute,
                attribute=attribute,
            )
            return False

        if not parsed_node_coordinates:
            # There should be at least one node coordinate variable
            self._add_message(
                field_ncvar,
                geometry_ncvar,
                message=incorrectly_formatted,
                attribute=attribute,
            )
            return False

        ok = True

        for ncvar in parsed_node_coordinates:
            # Check that the node coordinate variable exists in the
            # file
            if ncvar not in g["internal_variables"]:
                ncvar_attrs = g["variable_attributes"][ncvar]
                self._check_standard_names(
                    field_ncvar,
                    ncvar,
                    ncvar_attrs,
                )

                ncvar, message = self._missing_variable(
                    ncvar, "Node coordinate variable"
                )
                self._add_message(
                    field_ncvar, ncvar, message=message, attribute=attribute
                )
                ok = False

        return ok

    def _check_node_count(
        self, field_ncvar, geometry_ncvar, node_count, parsed_node_count
    ):
        """Check node count variable is valid and exists in the file."""
        attribute = {geometry_ncvar + ":node_count": node_count}

        g = self.read_vars

        if node_count is None:
            return True

        incorrectly_formatted = (
            "node_count attribute",
            "is incorrectly formatted",
        )

        if len(parsed_node_count) != 1:
            self._add_message(
                field_ncvar,
                geometry_ncvar,
                message=incorrectly_formatted,
                attribute=attribute,
            )
            return False

        ok = True

        for ncvar in parsed_node_count:
            ncvar_attrs = g["variable_attributes"][ncvar]
            self._check_standard_names(
                field_ncvar,
                ncvar,
                ncvar_attrs,
            )

            # Check that the node count variable exists in the file
            if ncvar not in g["internal_variables"]:
                ncvar, message = self._missing_variable(
                    ncvar, "Node count variable"
                )
                self._add_message(
                    field_ncvar, ncvar, message=message, attribute=attribute
                )
                ok = False

        return ok

    def _check_part_node_count(
        self,
        field_ncvar,
        geometry_ncvar,
        part_node_count,
        parsed_part_node_count,
    ):
        """Check part node count variable is valid and in the file."""
        if part_node_count is None:
            return True

        attribute = {geometry_ncvar + ":part_node_count": part_node_count}

        g = self.read_vars

        incorrectly_formatted = (
            "part_node_count attribute",
            "is incorrectly formatted",
        )

        if len(parsed_part_node_count) != 1:
            self._add_message(
                field_ncvar,
                geometry_ncvar,
                message=incorrectly_formatted,
                attribute=attribute,
            )
            return False

        ok = True

        for ncvar in parsed_part_node_count:
            ncvar_attrs = g["variable_attributes"][ncvar]
            self._check_standard_names(
                field_ncvar,
                ncvar,
                ncvar_attrs,
            )

            # Check that the variable exists in the file
            if ncvar not in g["internal_variables"]:
                ncvar, message = self._missing_variable(
                    ncvar, "Part node count variable"
                )
                self._add_message(
                    field_ncvar, ncvar, message=message, attribute=attribute
                )
                ok = False

        return ok

    def _check_interior_ring(
        self, field_ncvar, geometry_ncvar, interior_ring, parsed_interior_ring
    ):
        """Check all interior ring variables exist in the file.

        :Returns:

            `bool`

        """
        if interior_ring is None:
            return True

        attribute = {geometry_ncvar + ":interior_ring": interior_ring}

        g = self.read_vars

        incorrectly_formatted = (
            "interior_ring attribute",
            "is incorrectly formatted",
        )

        if not parsed_interior_ring:
            self._add_message(
                field_ncvar,
                geometry_ncvar,
                message=incorrectly_formatted,
                attribute=attribute,
            )
            return False

        ok = True

        if len(parsed_interior_ring) != 1:
            self._add_message(
                field_ncvar,
                geometry_ncvar,
                message=incorrectly_formatted,
                attribute=attribute,
            )
            return False

        for ncvar in parsed_interior_ring:
            ncvar_attrs = g["variable_attributes"][ncvar]
            self._check_standard_names(
                field_ncvar,
                ncvar,
                ncvar_attrs,
            )

            # Check that the variable exists in the file
            if ncvar not in g["internal_variables"]:
                ncvar, message = self._missing_variable(
                    ncvar, "Interior ring variable"
                )
                self._add_message(
                    field_ncvar, ncvar, message=message, attribute=attribute
                )
                ok = False

        return ok

    def _check_instance_dimension(self, parent_ncvar, instance_dimension):
        """Check that the instance dimension name is a netCDF dimension.

        .. versionadded:: (cfdm) 1.7.0

        CF-1.7 Appendix A

        * instance_dimension: An attribute which identifies an index
                              variable and names the instance dimension to
                              which it applies. The index variable
                              indicates that the indexed ragged array
                              representation is being used for a
                              collection of features.

        """
        attribute = {parent_ncvar + ":instance_dimension": instance_dimension}

        missing_dimension = ("Instance dimension", "is not in file")

        if (
            instance_dimension
            not in self.read_vars["internal_dimension_sizes"]
        ):
            self._add_message(
                None,
                parent_ncvar,
                message=missing_dimension,
                attribute=attribute,
            )
            return False

        return True

    def _check_sample_dimension(self, parent_ncvar, sample_dimension):
        """Check that the sample dimension name is a netCDF dimension.

        .. versionadded:: (cfdm) 1.7.0

        CF-1.7 Appendix A

        * sample_dimension: An attribute which identifies a count variable
                            and names the sample dimension to which it
                            applies. The count variable indicates that the
                            contiguous ragged array representation is
                            being used for a collection of features.

        """
        return sample_dimension in self.read_vars["internal_dimension_sizes"]

    def _check_coordinate_interpolation(
        self,
        parent_ncvar,
        coordinate_interpolation,
        parsed_coordinate_interpolation,
    ):
        """Check a TODO.

        .. versionadded:: (cfdm) 1.10.0.0

        :Parameters:

            parent_ncvar: `str`

            coordinate_interpolation: `str`
                A CF coordinate_interpolation attribute string.

            parsed_coordinate_interpolation: `dict`

        :Returns:

            `bool`

        """
        if not parsed_coordinate_interpolation:
            return True

        attribute = {
            parent_ncvar
            + ":coordinate_interpolation": coordinate_interpolation
        }

        g = self.read_vars

        incorrectly_formatted = (
            "coordinate_interpolation attribute",
            "is incorrectly formatted",
        )

        if not parsed_coordinate_interpolation:
            self._add_message(
                parent_ncvar,
                parent_ncvar,
                message=incorrectly_formatted,
                attribute=attribute,
                conformance="TODO",
            )
            return False

        ok = True

        for interp_ncvar, coords in parsed_coordinate_interpolation.items():
            interp_ncvar_attrs = g["variable_attributes"][interp_ncvar]
            self._check_standard_names(
                parent_ncvar,
                interp_ncvar,
                interp_ncvar_attrs,
            )

            # Check that the interpolation variable exists in the file
            if interp_ncvar not in g["internal_variables"]:
                ncvar, message = self._missing_variable(
                    interp_ncvar, "Interpolation variable"
                )
                self._add_message(
                    parent_ncvar, ncvar, message=message, attribute=attribute
                )
                ok = False

            attrs = g["variable_attributes"][interp_ncvar]
            if "tie_point_mapping" not in attrs:
                self._add_message(
                    parent_ncvar,
                    interp_ncvar,
                    message=(
                        "Interpolation variable",
                        "has no tie_point_mapping attribute",
                    ),
                    attribute=attribute,
                )
                ok = False

            # Check that the tie point coordinate variables exist in
            # the file
            for tie_point_ncvar in coords:
                # TODO: is this necessary or is it covered by the interp_ncvar
                # standard name check already?
                tie_point_interp_ncvar_attrs = g["variable_attributes"][
                    tie_point_ncvar
                ]
                self._check_standard_names(
                    parent_ncvar,
                    tie_point_ncvar,
                    tie_point_interp_ncvar_attrs,
                )

                if tie_point_ncvar not in g["internal_variables"]:
                    ncvar, message = self._missing_variable(
                        tie_point_ncvar, "Tie point coordinate variable"
                    )
                    self._add_message(
                        parent_ncvar,
                        ncvar,
                        message=message,
                        attribute=attribute,
                    )
                    ok = False

        # TODO check tie point variable dimensions

        return ok

    def _check_quantization(self, parent_ncvar, ncvar):
        """Check a quantization container variable.

        .. versionadded:: (cfdm) 1.12.2.0

        :Parameters:

            parent_ncvar: `str`
                The netCDF variable name of the parent variable.

            ncvar: `str`
                The netCDF variable name of the quantization variable.

        :Returns:

            `bool`

        """
        attribute = {parent_ncvar + ":quantization": ncvar}

        g = self.read_vars

        ok = True

        ncvar_attrs = g["variable_attributes"][ncvar]
        self._check_standard_names(
            parent_ncvar,
            ncvar,
            ncvar_attrs,
        )

        # Check that the quantization variable exists in the file
        if ncvar not in g["internal_variables"]:
            ncvar, message = self._missing_variable(
                ncvar, "Quantization variable"
            )
            self._add_message(
                parent_ncvar,
                ncvar,
                message=message,
                attribute=attribute,
            )
            ok = False

        attributes = g["variable_attributes"][ncvar]

        implementation = attributes.get("implementation")
        if implementation is None:
            self._add_message(
                parent_ncvar,
                ncvar,
                message=("implementation attribute", "is missing"),
            )
            ok = False

        algorithm = attributes.get("algorithm")
        if algorithm is None:
            self._add_message(
                parent_ncvar,
                ncvar,
                message=("algorithm attribute", "is missing"),
            )
            ok = False

        parameter = CF_QUANTIZATION_PARAMETERS.get(algorithm)
        if parameter is None:
            self._add_message(
                parent_ncvar,
                ncvar,
                message=(
                    "algorithm attribute",
                    f"has non-standardised value: {algorithm!r}",
                ),
            )
            ok = False

        if parameter not in g["variable_attributes"][parent_ncvar]:
            self._add_message(
                parent_ncvar,
                parent_ncvar,
                message=(f"{parameter} attribute", "is missing"),
            )
            ok = False

        return ok

    def _check_valid(self, field, construct):
        """Warns when valid_[min|max|range] properties exist on data.

        Issue a warning if a construct with data has
        valid_[min|max|range] properties.

        .. versionadded:: (cfdm) 1.8.3

        :Parameters:

            field: `Field`
                The parent field construct.

            construct: Construct or Bounds
                The construct that may have valid_[min|max|range]
                properties. May also be the parent field construct or
                Bounds.

        :Returns:

            `None`

        """
        # Check the bounds, if any.
        if self.implementation.has_bounds(construct):
            bounds = self.implementation.get_bounds(construct)
            self._check_valid(field, bounds)

        x = sorted(
            self.read_vars["valid_properties"].intersection(
                self.implementation.get_properties(construct)
            )
        )
        if not x:
            return

        # Still here?
        if self.implementation.is_field(construct):
            construct = ""
        else:
            construct = f" {construct!r} with"

        message = (
            f"WARNING: {field!r} has {construct} {', '.join(x)} "
            "{self._plural(x, 'property')}. "
        )
        print(message)

    def _check_external_variables(
        self, external_variables, parsed_external_variables
    ):
        """Check that named external variables do not exist in the file.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            external_variables: `str`
                The external_variables attribute as found in the file.

            parsed_external_variables: `list`
                The external_variables attribute parsed into a list of
                external variable names.

        :Returns:

            `list`
                The external variable names, less those which are also
                netCDF variables in the file.

        """
        g = self.read_vars

        attribute = {"external_variables": external_variables}
        message = ("External variable", "exists in the file")

        out = []

        for ncvar in parsed_external_variables:
            if ncvar not in g["internal_variables"]:
                out.append(ncvar)
            else:
                self._add_message(
                    None, ncvar, message=message, attribute=attribute
                )

        return out

    def _check_formula_terms(
        self, field_ncvar, coord_ncvar, formula_terms, z_ncdim=None
    ):
        """Check formula_terms for CF-compliance.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            field_ncvar: `str`

            coord_ncvar: `str`

            formula_terms: `str`
                A CF-netCDF formula_terms attribute.

        """
        # ============================================================
        # CF-1.7 7.1. Cell Boundaries
        #
        # If a parametric coordinate variable with a formula_terms
        # attribute (section 4.3.2) also has a bounds attribute, its
        # boundary variable must have a formula_terms attribute
        # too. In this case the same terms would appear in both (as
        # specified in Appendix D), since the transformation from the
        # parametric coordinate values to physical space is realised
        # through the same formula.  For any term that depends on the
        # vertical dimension, however, the variable names appearing in
        # the formula terms would differ from those found in the
        # formula_terms attribute of the coordinate variable itself
        # because the boundary variables for formula terms are
        # two-dimensional while the formula terms themselves are
        # one-dimensional.
        #
        # Whenever a formula_terms attribute is attached to a boundary
        # variable, the formula terms may additionally be identified
        # using a second method: variables appearing in the vertical
        # coordinates' formula_terms may be declared to be coordinate,
        # scalar coordinate or auxiliary coordinate variables, and
        # those coordinates may have bounds attributes that identify
        # their boundary variables. In that case, the bounds attribute
        # of a formula terms variable must be consistent with the
        # formula_terms attribute of the boundary variable. Software
        # digesting legacy datasets (constructed prior to version 1.7
        # of this standard) may have to rely in some cases on the
        # first method of identifying the formula term variables and
        # in other cases, on the second. Starting from version 1.7,
        # however, the first method will be sufficient.
        # ============================================================

        g = self.read_vars

        attribute = {coord_ncvar + ":formula_terms": formula_terms}

        g["formula_terms"].setdefault(coord_ncvar, {"coord": {}, "bounds": {}})

        parsed_formula_terms = self._parse_x(coord_ncvar, formula_terms)

        incorrectly_formatted = (
            "formula_terms attribute",
            "is incorrectly formatted",
        )

        if not parsed_formula_terms:
            self._add_message(
                field_ncvar,
                coord_ncvar,
                message=incorrectly_formatted,
                attribute=attribute,
            )
            return False

        self._ncdimensions(field_ncvar)

        for x in parsed_formula_terms:
            term, values = list(x.items())[0]

            g["formula_terms"][coord_ncvar]["coord"][term] = None

            if len(values) != 1:
                self._add_message(
                    field_ncvar,
                    coord_ncvar,
                    message=incorrectly_formatted,
                    attribute=attribute,
                )
                continue

            ncvar = values[0]

            if ncvar not in g["internal_variables"]:
                ncvar, message = self._missing_variable(
                    ncvar, "Formula terms variable"
                )

                self._add_message(
                    field_ncvar, ncvar, message=message, attribute=attribute
                )
                continue

            g["formula_terms"][coord_ncvar]["coord"][term] = ncvar

        bounds_ncvar = g["variable_attributes"][coord_ncvar].get("bounds")

        if bounds_ncvar is None:
            # --------------------------------------------------------
            # Parametric Z coordinate does not have bounds
            # --------------------------------------------------------
            for term in g["formula_terms"][coord_ncvar]["coord"]:
                g["formula_terms"][coord_ncvar]["bounds"][term] = None
        else:
            # --------------------------------------------------------
            # Parametric Z coordinate has bounds
            # --------------------------------------------------------
            bounds_formula_terms = g["variable_attributes"][bounds_ncvar].get(
                "formula_terms"
            )
            if bounds_formula_terms is not None:
                # ----------------------------------------------------
                # Parametric Z coordinate has bounds, and the bounds
                # variable has a formula_terms attribute
                # ----------------------------------------------------
                bounds_attribute = {
                    bounds_ncvar + ":formula_terms": bounds_formula_terms
                }

                parsed_bounds_formula_terms = self._parse_x(
                    bounds_ncvar, bounds_formula_terms
                )

                if not parsed_bounds_formula_terms:
                    self._add_message(
                        field_ncvar,
                        bounds_ncvar,
                        message=(
                            "Bounds formula_terms attribute",
                            "is incorrectly formatted",
                        ),
                        attribute=attribute,
                        direct_parent_ncvar=coord_ncvar,
                    )

                for x in parsed_bounds_formula_terms:
                    term, values = list(x.items())[0]

                    g["formula_terms"][coord_ncvar]["bounds"][term] = None

                    if len(values) != 1:
                        self._add_message(
                            field_ncvar,
                            bounds_ncvar,
                            message=(
                                "Bounds formula_terms attribute",
                                "is incorrectly formatted",
                            ),
                            attribute=bounds_attribute,
                            direct_parent_ncvar=coord_ncvar,
                        )
                        continue

                    ncvar = values[0]

                    if ncvar not in g["internal_variables"]:
                        ncvar, message = self._missing_variable(
                            ncvar, "Bounds formula terms variable"
                        )

                        self._add_message(
                            field_ncvar,
                            ncvar,
                            message=message,
                            attribute=bounds_attribute,
                            direct_parent_ncvar=coord_ncvar,
                        )
                        continue

                    if term not in g["formula_terms"][coord_ncvar]["coord"]:
                        self._add_message(
                            field_ncvar,
                            bounds_ncvar,
                            message=(
                                "Bounds formula_terms attribute",
                                "has incompatible terms",
                            ),
                            attribute=bounds_attribute,
                            direct_parent_ncvar=coord_ncvar,
                        )
                        continue

                    parent_ncvar = g["formula_terms"][coord_ncvar]["coord"][
                        term
                    ]

                    d_ncdims = g["variable_dimensions"][parent_ncvar]
                    dimensions = g["variable_dimensions"][ncvar]

                    if z_ncdim not in d_ncdims:
                        if ncvar != parent_ncvar:
                            self._add_message(
                                field_ncvar,
                                bounds_ncvar,
                                message=(
                                    "Bounds formula terms variable",
                                    "that does not span the vertical "
                                    "dimension is inconsistent with the "
                                    "formula_terms of the parametric "
                                    "coordinate variable",
                                ),
                                attribute=bounds_attribute,
                                direct_parent_ncvar=coord_ncvar,
                            )
                            continue

                    elif len(dimensions) != len(d_ncdims) + 1:
                        self._add_message(
                            field_ncvar,
                            bounds_ncvar,
                            message=(
                                "Bounds formula terms variable",
                                "spans incorrect dimensions",
                            ),
                            attribute=bounds_attribute,
                            dimensions=dimensions,
                            direct_parent_ncvar=coord_ncvar,
                        )
                        continue
                    # WRONG - need to account for char arrays:
                    elif d_ncdims != dimensions[:-1]:
                        self._add_message(
                            field_ncvar,
                            bounds_ncvar,
                            message=(
                                "Bounds formula terms variable",
                                "spans incorrect dimensions",
                            ),
                            attribute=bounds_attribute,
                            dimensions=dimensions,
                            direct_parent_ncvar=coord_ncvar,
                        )
                        continue

                    # Still here?
                    g["formula_terms"][coord_ncvar]["bounds"][term] = ncvar

                if set(g["formula_terms"][coord_ncvar]["coord"]) != set(
                    g["formula_terms"][coord_ncvar]["bounds"]
                ):
                    self._add_message(
                        field_ncvar,
                        bounds_ncvar,
                        message=(
                            "Bounds formula_terms attribute",
                            "has incompatible terms",
                        ),
                        attribute=bounds_attribute,
                        direct_parent_ncvar=coord_ncvar,
                    )

            else:
                # ----------------------------------------------------
                # Parametric Z coordinate has bounds, but the bounds
                # variable does not have a formula_terms attribute =>
                # Infer the formula terms bounds variables from the
                # coordinates
                # ----------------------------------------------------
                for term, ncvar in g["formula_terms"][coord_ncvar][
                    "coord"
                ].items():
                    g["formula_terms"][coord_ncvar]["bounds"][term] = None

                    if z_ncdim not in self._ncdimensions(ncvar):
                        g["formula_terms"][coord_ncvar]["bounds"][term] = ncvar
                        continue

                    is_coordinate_with_bounds = False
                    for c_ncvar in g["coordinates"][field_ncvar]:
                        if ncvar != c_ncvar:
                            continue

                        is_coordinate_with_bounds = True

                        if z_ncdim not in g["variable_dimensions"][c_ncvar]:
                            # Coordinates do not span the Z dimension
                            g["formula_terms"][coord_ncvar]["bounds"][
                                term
                            ] = ncvar
                        else:
                            # Coordinates span the Z dimension
                            b = g["bounds"][field_ncvar].get(ncvar)
                            if b is not None:
                                g["formula_terms"][coord_ncvar]["bounds"][
                                    term
                                ] = b
                            else:
                                is_coordinate_with_bounds = False

                        break

                    if not is_coordinate_with_bounds:
                        self._add_message(
                            field_ncvar,
                            ncvar,
                            message=(
                                "Formula terms variable",
                                "that spans the vertical dimension "
                                "has no bounds",
                            ),
                            attribute=attribute,
                            direct_parent_ncvar=coord_ncvar,
                        )

    def _ugrid_parse_mesh_topology(self, mesh_ncvar, attributes):
        """Parse a UGRID mesh topology or location index set variable.

        Adds a new entry to ``self.read_vars['mesh']``. Adds a
        *location_index_set variable* to
        ``self.read_vars["do_not_create_field"]``.

        .. versionadded:: (cfdm) 1.11.0.0

        :Parameters:

            mesh_ncvar: `str`, optional
                The netCDF name of a netCDF that might be a mesh
                topology variable.

            attributes: `dict`
                The netCDF attributes of *ncvar*.

        :Returns:

            `None`

        """
        g = self.read_vars
        if not self._ugrid_check_mesh_topology(mesh_ncvar):
            return

        # Do not attempt to create a field or domain construct from a
        # mesh topology variable, nor mesh topology connectivity
        # variables.
        do_not_create_field = g["do_not_create_field"]
        if not g["domain"]:
            do_not_create_field.add(mesh_ncvar)

        for attr, value in attributes.items():
            if attr in (
                "face_node_connectivity",
                "face_face_connectivity",
                "face_edge_connectivity",
                "edge_node_connectivity",
                "edge_face_connectivity",
                "volume_node_connectivity",
                "volume_edge_connectivity",
                "volume_face_connectivity",
                "volume_volume_connectivity",
                "volume_shape_type",
            ):
                do_not_create_field.add(value)

        # ------------------------------------------------------------
        # Initialise the Mesh instance
        # ------------------------------------------------------------
        mesh = Mesh(
            mesh_ncvar=mesh_ncvar,
            mesh_attributes=attributes,
            mesh_id=uuid4().hex,
        )

        locations = ("node", "edge", "face")

        # ------------------------------------------------------------
        # Find the discrete axis for each location of the mesh
        # topology
        # ------------------------------------------------------------
        mesh_ncdim = {}
        for location in locations:
            if location == "node":
                node_coordinates = self._split_string_by_white_space(
                    None, attributes["node_coordinates"], variables=True
                )
                ncvar = node_coordinates[0]
            else:
                ncvar = attributes.get(f"{location}_node_connectivity")

            ncvar_attrs = g["variable_attributes"][ncvar]
            self._check_standard_names(
                mesh_ncvar,
                ncvar,
                ncvar_attrs,
            )

            ncdim = self.read_vars["variable_dimensions"].get(ncvar)
            if ncdim is None:
                continue

            if len(ncdim) == 1:
                # Node
                i = 0
            else:
                # Edge or face
                i = self._ugrid_cell_dimension(location, ncvar, mesh)

            mesh_ncdim[location] = ncdim[i]

        mesh.ncdim = mesh_ncdim

        # ------------------------------------------------------------
        # Find the netCDF variable names of the coordinates for each
        # location
        # ------------------------------------------------------------
        coordinates_ncvar = {}
        for location in locations:
            coords_ncvar = attributes.get(f"{location}_coordinates", "")
            coords_ncvar = self._split_string_by_white_space(
                None, coords_ncvar, variables=True
            )
            coordinates_ncvar[location] = coords_ncvar
            for ncvar in coords_ncvar:
                do_not_create_field.add(ncvar)

        mesh.coordinates_ncvar = coordinates_ncvar

        # ------------------------------------------------------------
        # Create auxiliary coordinate constructs for each location
        # ------------------------------------------------------------
        auxiliary_coordinates = {}
        for location in locations:
            auxs = self._ugrid_create_auxiliary_coordinates(
                mesh_ncvar, None, mesh, location
            )
            if auxs:
                auxiliary_coordinates[location] = auxs

        mesh.auxiliary_coordinates = auxiliary_coordinates

        # ------------------------------------------------------------
        # Create the domain topology construct for each location
        # ------------------------------------------------------------
        domain_topologies = {}
        for location in locations:
            domain_topology = self._ugrid_create_domain_topology(
                mesh_ncvar, None, mesh, location
            )
            if domain_topology is not None:
                domain_topologies[location] = domain_topology

        mesh.domain_topologies = domain_topologies

        # ------------------------------------------------------------
        # Create cell connectivity constructs for each location
        # ------------------------------------------------------------
        cell_connectivites = {}
        for location in locations:
            conns = self._ugrid_create_cell_connectivities(
                mesh_ncvar, None, mesh, location
            )
            if conns:
                cell_connectivites[location] = conns

        mesh.cell_connectivities = cell_connectivites

        g["mesh"][mesh_ncvar] = mesh

    def _ugrid_parse_location_index_set(self, parent_attributes):
        """Parse a UGRID location index set variable.

        Adds a new entry to ``self.read_vars['mesh']``. Adds a
        *location_index_set* variable to
        ``self.read_vars["do_not_create_field"]``.

        .. versionadded:: (cfdm) 1.11.0.0

        :Parameters:

            parent_attributes: `dict`
                The attributes of a netCDF variable that include
                "location_index_set" attribute.

        :Returns:

            `None`

        """
        g = self.read_vars

        location_index_set_ncvar = parent_attributes["location_index_set"]
        if location_index_set_ncvar in g["mesh"]:
            # The location index set has already been parsed
            return

        ncvar_attrs = g["variable_attributes"][location_index_set_ncvar]
        self._check_standard_names(
            location_index_set_ncvar,
            location_index_set_ncvar,
            ncvar_attrs,
        )

        if not self._ugrid_check_location_index_set(location_index_set_ncvar):
            return

        location_index_set_attributes = g["variable_attributes"][
            location_index_set_ncvar
        ]
        location = location_index_set_attributes["location"]
        mesh_ncvar = location_index_set_attributes["mesh"]
        attributes = g["variable_attributes"][mesh_ncvar]

        index_set = self._create_data(location_index_set_ncvar)
        start_index = location_index_set_attributes.get("start_index", 0)
        if start_index:
            index_set -= start_index

        # Do not attempt to create a field or domain construct from a
        # location index set variable
        g["do_not_create_field"].add(location_index_set_ncvar)

        g["mesh"][location_index_set_ncvar] = Mesh(
            mesh_ncvar=mesh_ncvar,
            mesh_attributes=attributes,
            location_index_set_ncvar=location_index_set_ncvar,
            location_index_set_attributes=location_index_set_attributes,
            location=location,
            index_set=index_set,
            mesh_id=uuid4().hex,
        )

    def _ugrid_create_auxiliary_coordinates(
        self,
        parent_ncvar,
        f,
        mesh,
        location,
    ):
        """Create auxiliary coordinate constructs from a UGRID mesh.

        .. versionadded:: (cfdm) 1.11.0.0

        :Parameters:

            parent_ncvar: `str`
                The netCDF variable name of the parent field construct.

            f: `Field`
                The parent field construct.

            mesh: `Mesh`
                The mesh description, as stored in
                ``self.read_vars['mesh']``.

            location: `str`
                The location of the cells in the mesh topology. One of
                ``'node'``, ``'edge'``, ``'face'``, ``'volume'``.

        :Returns:

            `list` of `AuxiliaryCoordinate`
                The auxiliary coordinates, with bounds, for the UGRID
                cells. May be an empty list.

        """
        if location not in mesh.ncdim:
            return []

        # Get the netCDF variable names of the node
        # coordinates. E.g. ("Mesh2_node_x", "Mesh2_node_y")
        nodes_ncvar = mesh.coordinates_ncvar["node"]

        # Get the netCDF variable names of the cell
        # coordinates. E.g. ("Mesh1_face_x", "Mesh1_face_y"), or None
        # if there aren't any.
        coords_ncvar = mesh.coordinates_ncvar.get(location)

        auxs = []
        if coords_ncvar:
            # There are cell coordinates, so turn them into
            # auxiliary coordinate constructs
            #
            # Note: We are assuming that the node coordinates are
            # ordered identically to the [edge|face|volume]
            # coordinates
            # (https://github.com/ugrid-conventions/ugrid-conventions/issues/67)
            for coord_ncvar, node_ncvar in zip(coords_ncvar, nodes_ncvar):
                # This auxiliary coordinate needs creating from
                # a [node|edge|face|volume]_coordinate variable.
                aux = self._create_auxiliary_coordinate(
                    parent_ncvar, coord_ncvar, None
                )
                if location != "node" and not self.implementation.has_bounds(
                    aux
                ):
                    # These auxiliary [edge|face] coordinates don't
                    # have bounds => create bounds from the mesh
                    # nodes.
                    aux = self._ugrid_create_bounds_from_nodes(
                        parent_ncvar,
                        node_ncvar,
                        f,
                        mesh,
                        location,
                        aux=aux,
                    )

                self.implementation.nc_set_node_coordinate_variable(
                    aux, node_ncvar
                )
                auxs.append(aux)

        elif nodes_ncvar:
            # There are no cell coordinates, so create auxiliary
            # coordinate constructs that are derived from an
            # [edge|face|volume]_node_connectivity variable. These
            # will contain only bounds, with no coordinate values.
            for node_ncvar in nodes_ncvar:
                aux = self._ugrid_create_bounds_from_nodes(
                    parent_ncvar,
                    node_ncvar,
                    f,
                    mesh,
                    location,
                )
                g = self.read_vars
                ncvar_attrs = g["variable_attributes"][node_ncvar]
                self._check_standard_names(
                    parent_ncvar,
                    node_ncvar,
                    ncvar_attrs,
                )

                self.implementation.nc_set_node_coordinate_variable(
                    aux, node_ncvar
                )
                auxs.append(aux)

        # Apply a location index set
        index_set = mesh.index_set
        if index_set is not None:
            auxs = [aux[index_set] for aux in auxs]

        mesh.auxiliary_coordinates[location] = auxs
        return auxs

    def _ugrid_create_bounds_from_nodes(
        self,
        parent_ncvar,
        node_ncvar,
        f,
        mesh,
        location,
        aux=None,
    ):
        """Create coordinate bounds from UGRID nodes.

        .. versionadded:: (cfdm) 1.11.0.0

        :Parameters:

            parent_ncvar: `str`
                The netCDF variable name of the parent field construct.

            node_ncvar: `str`
                The netCDF variable name of the UGRID node coordinate
                variable.

            f: `Field`
                The parent field construct.

            mesh: `Mesh`
                The mesh description, as stored in
                ``self.read_vars['mesh']``.

            location: `str`
                The location of the cells in the mesh topology. One of
                ``'edge'``, ``'face'``, or ``'volume'``.

            aux: `AuxiliaryCoordinate`, optional
                An existing auxiliary coordinate construct that
                contains the cell coordinates, but has no bounds. By
                default a new auxiliary coordinate construct is
                created that has no coordinates.

        :Returns:

            `AuxiliaryCoordinate`
                The auxiliary coordinate construct, with bounds, for
                the UGRID cells.

        """
        if location not in mesh.ncdim:
            return aux

        g = self.read_vars

        properties = g["variable_attributes"][node_ncvar].copy()
        properties.pop("formula_terms", None)

        bounds = self.implementation.initialise_Bounds()
        if aux is None:
            aux = self.implementation.initialise_AuxiliaryCoordinate()
            self.implementation.set_properties(aux, properties)

        if not g["mask"]:
            self._set_default_FillValue(bounds, node_ncvar)

        connectivity_attr = f"{location}_node_connectivity"
        connectivity_ncvar = mesh.mesh_attributes[connectivity_attr]
        node_connectivity = self._create_data(
            connectivity_ncvar,
            uncompress_override=True,
            compression_index=True,
        )
        node_coordinates = self._create_data(
            node_ncvar, compression_index=True
        )
        start_index = g["variable_attributes"][connectivity_ncvar].get(
            "start_index", 0
        )
        cell_dimension = self._ugrid_cell_dimension(
            location, connectivity_ncvar, mesh
        )

        shape = node_connectivity.shape
        if cell_dimension == 1:
            shape = shape[::-1]

        # Create and set the bounds data
        array = self.implementation.initialise_BoundsFromNodesArray(
            node_connectivity=node_connectivity,
            shape=shape,
            node_coordinates=node_coordinates,
            start_index=start_index,
            cell_dimension=cell_dimension,
            copy=False,
        )
        bounds_data = self._create_Data(
            array,
            units=properties.get("units"),
            calendar=properties.get("calendar"),
            ncvar=node_ncvar,
            compressed=True,
        )
        self.implementation.set_data(bounds, bounds_data, copy=False)

        # Set the original file names
        self.implementation.set_original_filenames(
            bounds, g["variable_datasetname"][node_ncvar]
        )

        error = self.implementation.set_bounds(aux, bounds, copy=False)
        if error:
            logger.warning(str(error))

        return aux

    def _ugrid_create_domain_topology(self, parent_ncvar, f, mesh, location):
        """Create a domain topology construct.

        .. versionadded:: (cfdm) 1.11.0.0

        :Parameters:

            parent_ncvar: `str`
                The netCDF variable name of the parent field construct.

            f: `Field`
                The parent field construct.

            mesh: `Mesh`
                The mesh description, as stored in
                ``self.read_vars['mesh']``.

            location: `str`
                The location of the cells in the mesh topology. One of
                ``'node'``, ``'edge'``, ``'face'``, ``'volume'``.

        :Returns:

            `DomainTopology` or `None`
                The domain topology construct, or `None` if it could
                not be created.

        """
        attributes = mesh.mesh_attributes

        if location == "node":
            cell = "point"
            connectivity_attr = None
            for loc in ("edge", "face", "volume"):
                connectivity_attr = f"{loc}_node_connectivity"
                if connectivity_attr in attributes:
                    break
        else:
            cell = location
            connectivity_attr = f"{location}_node_connectivity"
            loc = location

        connectivity_ncvar = attributes.get(connectivity_attr)
        if connectivity_ncvar is None:
            # Can't create a domain topology construct without an
            # appropriate connectivity attribute
            return

        g = self.read_vars
        ncvar_attrs = g["variable_attributes"][connectivity_ncvar]
        self._check_standard_names(
            parent_ncvar,
            connectivity_ncvar,
            ncvar_attrs,
        )

        if not self._ugrid_check_connectivity_variable(
            parent_ncvar,
            mesh.mesh_ncvar,
            connectivity_ncvar,
            connectivity_attr,
        ):
            return

        # Still here?

        # CF properties
        properties = self.read_vars["variable_attributes"][
            connectivity_ncvar
        ].copy()
        start_index = properties.pop("start_index", 0)
        cell_dimension = self._ugrid_cell_dimension(
            loc, connectivity_ncvar, mesh
        )

        # Create data
        if cell == "point":
            properties["long_name"] = (
                "Maps every point to its connected points"
            )
            indices, kwargs = self._create_netcdfarray(connectivity_ncvar)
            n_nodes = self.read_vars["internal_dimension_sizes"][
                mesh.ncdim[location]
            ]
            array = self.implementation.initialise_PointTopologyArray(
                shape=(n_nodes, nan),
                start_index=start_index,
                cell_dimension=cell_dimension,
                copy=False,
                **{connectivity_attr: indices},
            )
            attributes = kwargs["attributes"]
            data = self._create_Data(
                array,
                units=attributes.get("units"),
                calendar=attributes.get("calendar"),
                ncvar=connectivity_ncvar,
                compressed=True,
            )
        else:
            # Edge or face cells
            data = self._create_data(
                connectivity_ncvar, compression_index=True
            )
            if cell_dimension == 1:
                data = data.transpose()

        # Initialise the domain topology variable
        domain_topology = self.implementation.initialise_DomainTopology(
            cell=cell,
            properties=properties,
            data=data,
            copy=False,
        )

        # Set the netCDF variable name and the original file names
        self.implementation.nc_set_variable(
            domain_topology, connectivity_ncvar
        )
        self.implementation.set_original_filenames(
            domain_topology, self.read_vars["dataset"]
        )

        index_set = mesh.index_set
        if index_set is not None:
            # Apply a location index set
            domain_topology = domain_topology[index_set]

        return domain_topology

    def _ugrid_create_cell_connectivities(
        self, parent_ncvar, f, mesh, location
    ):
        """Create a cell connectivity construct.

        Only "face_face_connectivity" is supported.

        .. versionadded:: (cfdm) 1.11.0.0

        :Parameters:

            parent_ncvar: `str`
                The netCDF variable name of the parent field construct.

            f: `Field`
                The parent field construct.

            mesh: `Mesh`
                The mesh description, as stored in
                ``self.read_vars['mesh']``.

            location: `str`
                The location of the cells in the mesh topology. One of
                ``'node'``, ``'edge'``, ``'face'``, ``'volume'``.

        :Returns:

            `list`
                The cell connectivity constructs for this
                location. May be an empty list.

        """
        if location != "face":
            return []

        attributes = mesh.mesh_attributes
        connectivity_attr = f"{location}_{location}_connectivity"

        # Select the connectivity attribute that has the hightest
        # topology dimension
        connectivity_ncvar = attributes.get(connectivity_attr)
        if connectivity_ncvar is None:
            return []

        if not self._ugrid_check_connectivity_variable(
            parent_ncvar,
            mesh.mesh_ncvar,
            connectivity_ncvar,
            connectivity_attr,
        ):
            return []

        # CF properties
        properties = self.read_vars["variable_attributes"][connectivity_ncvar]
        start_index = properties.pop("start_index", 0)
        cell_dimension = self._ugrid_cell_dimension(
            location, connectivity_ncvar, mesh
        )

        # Connectivity data
        indices, kwargs = self._create_netcdfarray(connectivity_ncvar)

        array = self.implementation.initialise_CellConnectivityArray(
            cell_connectivity=indices,
            start_index=start_index,
            cell_dimension=cell_dimension,
            copy=False,
        )
        attributes = kwargs["attributes"]
        data = self._create_Data(
            array,
            units=attributes.get("units"),
            calendar=attributes.get("calendar"),
            ncvar=connectivity_ncvar,
            compressed=True,
        )

        # Initialise the cell connectivity construct
        connectivity = self.implementation.initialise_CellConnectivity(
            connectivity=self.ugrid_cell_connectivity_types()[
                connectivity_attr
            ],
            properties=properties,
            data=data,
            copy=False,
        )

        # Set the netCDF variable name and the original file names
        self.implementation.nc_set_variable(connectivity, connectivity_ncvar)
        self.implementation.set_original_filenames(
            connectivity, self.read_vars["dataset"]
        )

        index_set = mesh.index_set
        if index_set is not None:
            # Apply a location index set
            connectivity = connectivity[index_set]

        return [connectivity]

    def _ugrid_cell_dimension(self, location, connectivity_ncvar, mesh):
        """The connectivity variable dimension that indexes the cells.

        .. versionadded:: (cfdm) 1.11.0.0

        :Parameters:

            location: `str`
                The type of the connectivity variable, one of
                ``'node'``, ``'edge'``, ``'face'``, ``'volume'``.

            connectivity_ncvar: `str`
                The netCDF variable name of the UGRID connectivity
                variable.

            mesh: `Mesh`
                The UGRID mesh defintion.

        :Returns:

            `int`
                The position of the dimension of the connectivity
                variable that indexes the cells. Either ``0`` or
                ``1``.

        """
        ncdim = mesh.mesh_attributes.get(f"{location}_dimension")
        if ncdim is None:
            return 0

        try:
            cell_dim = self._ncdimensions(connectivity_ncvar).index(ncdim)
        except IndexError:
            cell_dim = 0

        return cell_dim

    def _ugrid_check_mesh_topology(self, mesh_ncvar):
        """Check a UGRID mesh topology variable.

        These checks are independent of any parent data variable.

        .. versionadded:: (cfdm) 1.11.0.0

        :Parameters:

            mesh_ncvar: `str`
                The name of the netCDF mesh topology variable.

        :Returns:

            `bool`
                Whether or not the mesh topology variable adheres to
                the CF conventions.

        """
        g = self.read_vars

        ok = True

        mesh_ncvar_attrs = g["variable_attributes"][mesh_ncvar]
        self._check_standard_names(
            mesh_ncvar,
            mesh_ncvar,
            mesh_ncvar_attrs,
        )

        if mesh_ncvar not in g["internal_variables"]:
            mesh_ncvar, message = self._missing_variable(
                mesh_ncvar, "Mesh topology variable"
            )
            self._add_message(
                mesh_ncvar,
                mesh_ncvar,
                message=message,
                attribute={f"{mesh_ncvar}:mesh": mesh_ncvar},
            )
            ok = False
            return ok

        attributes = g["variable_attributes"][mesh_ncvar]

        node_coordinates = attributes.get("node_coordinates")
        if node_coordinates is None:
            self._add_message(
                mesh_ncvar,
                mesh_ncvar,
                message=("node_coordinates attribute", "is missing"),
            )
            ok = False

        # Check coordinate variables
        for attr in (
            "node_coordinates",
            "edge_coordinates",
            "face_coordinates",
            "volume_coordinates",
        ):
            if attr not in attributes:
                continue

            coordinates = self._split_string_by_white_space(
                None, attributes[attr], variables=True
            )

            n_coordinates = len(coordinates)
            if attr == "node_coordinates":
                n_nodes = n_coordinates
            elif n_coordinates != n_nodes:
                self._add_message(
                    mesh_ncvar,
                    mesh_ncvar,
                    message=(
                        f"{attr} variable",
                        "contains wrong number of variables",
                    ),
                    attribute=attr,
                )
                ok = False

            dims = []
            for ncvar in coordinates:
                if ncvar not in g["internal_variables"]:
                    ncvar, message = self._missing_variable(
                        mesh_ncvar, f"{attr} variable"
                    )
                    self._add_message(
                        mesh_ncvar,
                        ncvar,
                        message=message,
                        attribute=attr,
                    )
                    ok = False
                else:
                    ncvar_attrs = g["variable_attributes"][ncvar]
                    self._check_standard_names(
                        mesh_ncvar,
                        ncvar,
                        ncvar_attrs,
                    )

                    dims = []
                    ncdims = self._ncdimensions(ncvar)
                    if len(ncdims) != 1:
                        self._add_message(
                            mesh_ncvar,
                            ncvar,
                            message=(
                                f"{attr} variable",
                                "spans incorrect dimensions",
                            ),
                            attribute=attr,
                            dimensions=g["variable_dimensions"][ncvar],
                        )
                        ok = False

                    dims.extend(ncdims)

                if len(set(dims)) > 1:
                    self._add_message(
                        mesh_ncvar,
                        ncvar,
                        message=(
                            f"{attr} variables",
                            "span different dimensions",
                        ),
                        attribute=attr,
                    )
                    ok = False

        # Check connectivity variables
        topology_dimension = attributes.get("topology_dimension")
        if topology_dimension is None:
            self._add_message(
                mesh_ncvar,
                mesh_ncvar,
                message=("topology_dimension attribute", "is missing"),
            )
            ok = False
        elif topology_dimension == 2:
            ncvar = attributes.get("face_node_connectivity")

            if ncvar is None:
                self._add_message(
                    mesh_ncvar,
                    ncvar,
                    message=("face_node_connectivity attribute", "is missing"),
                    attribute="face_node_connectivity",
                )
                ok = False
            elif ncvar not in g["internal_variables"]:
                ncvar, message = self._missing_variable(
                    ncvar, "Face node connectivity variable"
                )
                self._add_message(
                    mesh_ncvar,
                    ncvar,
                    message=message,
                    attribute={f"{mesh_ncvar}:face_node_connectivity": ncvar},
                )
                ok = False
            else:
                ncvar_attrs = g["variable_attributes"][ncvar]
                self._check_standard_names(
                    mesh_ncvar,
                    ncvar,
                    ncvar_attrs,
                )

        elif topology_dimension == 1:
            ncvar = attributes.get("edge_node_connectivity")

            if ncvar is None:
                self._add_message(
                    mesh_ncvar,
                    mesh_ncvar,
                    message=("edge_node_connectivity attribute", "is missing"),
                    attribute="edge_node_connectivity",
                )
                ok = False
            elif ncvar not in g["internal_variables"]:
                ncvar, message = self._missing_variable(
                    ncvar, "Edge node connectivity variable"
                )
                self._add_message(
                    mesh_ncvar,
                    ncvar,
                    message=message,
                    attribute={f"{mesh_ncvar}:edge_node_connectivity": ncvar},
                )
                ok = False
            else:
                ncvar_attrs = g["variable_attributes"][ncvar]
                self._check_standard_names(
                    mesh_ncvar,
                    ncvar,
                    ncvar_attrs,
                )

        elif topology_dimension == 3:
            ncvar = attributes.get("volume_node_connectivity")
            if ncvar is None:
                self._add_message(
                    mesh_ncvar,
                    mesh_ncvar,
                    message=(
                        "volume_node_connectivity attribute",
                        "is missing",
                    ),
                    attribute="volume_node_connectivity",
                )
                ok = False
            elif ncvar not in g["internal_variables"]:
                ncvar, message = self._missing_variable(
                    ncvar, "Volume node connectivity variable"
                )
                self._add_message(
                    mesh_ncvar,
                    ncvar,
                    message=message,
                    attribute={
                        f"{mesh_ncvar}:volume_node_connectivity": ncvar
                    },
                )
                ok = False
            else:
                ncvar_attrs = g["variable_attributes"][ncvar]
                self._check_standard_names(
                    mesh_ncvar,
                    ncvar,
                    ncvar_attrs,
                )

            ncvar = attributes.get("volume_shape_type")
            if ncvar is None:
                self._add_message(
                    mesh_ncvar,
                    mesh_ncvar,
                    message=("volume_shape_type attribute", "is missing"),
                )
                ok = False
            else:
                ncvar_attrs = g["variable_attributes"][ncvar]
                self._check_standard_names(
                    mesh_ncvar,
                    ncvar,
                    ncvar_attrs,
                )
        else:
            self._add_message(
                mesh_ncvar,
                mesh_ncvar,
                message=("topology_dimension attribute", "has invalid value"),
                attribute={f"{ncvar}:topology_dimension": topology_dimension},
            )
            ok = False

        return ok

    def _ugrid_check_location_index_set(
        self,
        location_index_set_ncvar,
    ):
        """Check a UGRID location index set variable.

        These checks are independent of any parent variable.

        .. versionadded:: (cfdm) 1.11.0.0

        :Parameters:

            location_index_set_ncvar: `str`
                The name of the UGRID location index set netCDF
                variable.

        :Returns:

            `bool`
                Whether or not the location index set variable adheres
                to the CF conventions.

        """
        g = self.read_vars

        ok = True

        if location_index_set_ncvar not in g["internal_variables"]:
            location_index_set_ncvar, message = self._missing_variable(
                location_index_set_ncvar, "Location index set variable"
            )
            self._add_message(
                location_index_set_ncvar,
                location_index_set_ncvar,
                message=message,
            )
            return False
        else:
            ncvar_attrs = g["variable_attributes"][location_index_set_ncvar]
            self._check_standard_names(
                location_index_set_ncvar,
                location_index_set_ncvar,
                ncvar_attrs,
            )

        location_index_set_attributes = g["variable_attributes"][
            location_index_set_ncvar
        ]

        location = location_index_set_attributes.get("location")
        if location is None:
            self._add_message(
                location_index_set_ncvar,
                location_index_set_ncvar,
                message=("location attribute", "is missing"),
            )
            ok = False
        elif location not in ("node", "edge", "face", "volume"):
            self._add_message(
                location_index_set_ncvar,
                location_index_set_ncvar,
                message=("location attribute", "has invalid value"),
                attribute={f"{location_index_set_ncvar}:location": location},
            )
            ok = False

        mesh_ncvar = location_index_set_attributes.get("mesh")
        if mesh_ncvar is None:
            self._add_message(
                location_index_set_ncvar,
                location_index_set_ncvar,
                message=("mesh attribute", "is missing"),
            )
            ok = False
        elif mesh_ncvar not in g["internal_variables"]:
            mesh_ncvar, message = self._missing_variable(
                mesh_ncvar, "Mesh topology variable"
            )
            self._add_message(
                location_index_set_ncvar,
                mesh_ncvar,
                message=message,
                attribute={f"{location_index_set_ncvar}:mesh": mesh_ncvar},
                direct_parent_ncvar=location_index_set_ncvar,
            )
            ok = False
        elif mesh_ncvar not in g["mesh"]:
            self._add_message(
                location_index_set_ncvar,
                mesh_ncvar,
                message=("Mesh attribute", "is not a mesh topology variable"),
                attribute={f"{location_index_set_ncvar}:mesh": mesh_ncvar},
            )
            ok = False
        else:
            mesh_ncvar_attrs = g["variable_attributes"][mesh_ncvar]
            self._check_standard_names(
                location_index_set_ncvar,
                mesh_ncvar,
                mesh_ncvar_attrs,
            )

        return ok

    def _ugrid_check_field_location_index_set(
        self,
        parent_ncvar,
        location_index_set_ncvar,
    ):
        """Check a UGRID location index set variable.

        These checks are in the context of a parent variable.

        .. versionadded:: (cfdm) 1.11.0.0

        :Parameters:

            parent_ncvar: `str`
                The netCDF variable name of the parent field or domain
                construct.

            location_index_set_ncvar: `str`
                The name of the UGRID location index set netCDF
                variable.

        :Returns:

            `bool`
                Whether or not the location index set variable of a
                field or domain variable adheres to the CF
                conventions.

        """
        g = self.read_vars

        ok = True

        if "mesh" in g["variable_attributes"][parent_ncvar]:
            self._add_message(
                parent_ncvar,
                parent_ncvar,
                ("Location index set variable", "is referenced incorrectly"),
            )
            return False

        if location_index_set_ncvar not in g["internal_variables"]:
            location_index_set_ncvar, message = self._missing_variable(
                location_index_set_ncvar, "Location index set variable"
            )
            self._add_message(
                parent_ncvar,
                location_index_set_ncvar,
                message=message,
                attribute={
                    f"{parent_ncvar}:location_index_set": location_index_set_ncvar
                },
            )
            return False
        else:
            ncvar_attrs = g["variable_attributes"][location_index_set_ncvar]
            self._check_standard_names(
                parent_ncvar,
                location_index_set_ncvar,
                ncvar_attrs,
            )

        location_index_set_attributes = g["variable_attributes"][
            location_index_set_ncvar
        ]

        location = location_index_set_attributes.get("location")
        if location is None:
            self._add_message(
                parent_ncvar,
                location_index_set_ncvar,
                message=("location attribute", "is missing"),
            )
            ok = False
        elif location not in ("node", "edge", "face", "volume"):
            self._add_message(
                parent_ncvar,
                location_index_set_ncvar,
                message=("location attribute", "has invalid value"),
                attribute={f"{location_index_set_ncvar}:location": location},
            )
            ok = False

        mesh_ncvar = location_index_set_attributes.get("mesh")
        if mesh_ncvar is None:
            self._add_message(
                parent_ncvar,
                location_index_set_ncvar,
                message=("mesh attribute", "is missing"),
            )
            ok = False
        elif mesh_ncvar not in g["internal_variables"]:
            mesh_ncvar, message = self._missing_variable(
                mesh_ncvar, "Mesh topology variable"
            )
            self._add_message(
                parent_ncvar,
                mesh_ncvar,
                message=message,
                attribute={f"{location_index_set_ncvar}:mesh": mesh_ncvar},
                direct_parent_ncvar=location_index_set_ncvar,
            )
            ok = False
        elif mesh_ncvar not in g["mesh"]:
            self._add_message(
                parent_ncvar,
                mesh_ncvar,
                message=("Mesh attribute", "is not a mesh topology variable"),
                attribute={f"{location_index_set_ncvar}:mesh": mesh_ncvar},
            )
            ok = False
        else:
            mesh_ncvar_attrs = g["variable_attributes"][mesh_ncvar]
            self._check_standard_names(
                parent_ncvar,
                mesh_ncvar,
                mesh_ncvar_attrs,
            )

        parent_ncdims = self._ncdimensions(parent_ncvar)
        lis_ncdims = self._ncdimensions(location_index_set_ncvar)
        if not set(lis_ncdims).issubset(parent_ncdims):
            self._add_message(
                parent_ncvar,
                location_index_set_ncvar,
                message=(
                    "Location index set variable",
                    "spans incorrect dimensions",
                ),
                attribute="location_index_set",
                dimensions=g["variable_dimensions"][location_index_set_ncvar],
            )
            ok = False

        # SLB check attribute in question is always "location_index_set" here
        # an verify whether dimensions should be registered here
        self._include_component_report(
            parent_ncvar,
            location_index_set_ncvar,
            "location_index_set",
            dimensions=g["variable_dimensions"][location_index_set_ncvar],
        )
        return ok

    def _ugrid_check_field_mesh(
        self,
        parent_ncvar,
        mesh_ncvar,
    ):
        """Check a UGRID mesh topology variable.

        These checks are in the context of a parent variable.

        .. versionadded:: (cfdm) 1.11.0.0

        :Parameters:

            parent_ncvar: `str`
                The netCDF variable name of the parent field or domain
                construct.

        :Returns:

            `bool`
                Whether or not the mesh topology variable of a field
                or domain variable adheres to the CF conventions.

        """
        g = self.read_vars

        ok = True

        parent_attributes = g["variable_attributes"][parent_ncvar]
        if "location_index_set" in parent_attributes:
            self._add_message(
                parent_ncvar,
                parent_ncvar,
                ("Mesh topology variable", "is referenced incorrectly"),
            )
            return False

        if mesh_ncvar not in g["mesh"]:
            self._add_message(
                parent_ncvar,
                parent_ncvar,
                message=(
                    "mesh attribute",
                    "is not a mesh topology variable",
                ),
                attribute={f"{parent_ncvar}:mesh": mesh_ncvar},
            )
            return False
        else:
            mesh_ncvar_attrs = g["variable_attributes"][mesh_ncvar]
            self._check_standard_names(
                parent_ncvar,
                mesh_ncvar,
                mesh_ncvar_attrs,
            )

        location = parent_attributes.get("location")
        if location is None:
            self._add_message(
                parent_ncvar,
                parent_ncvar,
                message=("location attribute", "is missing"),
            )
            ok = False
        elif location not in ("node", "edge", "face", "volume"):
            self._add_message(
                parent_ncvar,
                parent_ncvar,
                message=("location attribute", "has invalid value"),
                attribute={f"{parent_ncvar}:location": location},
            )
            ok = False
        elif location not in g["mesh"][mesh_ncvar].domain_topologies:
            self._add_message(
                parent_ncvar,
                mesh_ncvar,
                message=(
                    "Couldn't create domain topology construct",
                    "from UGRID mesh topology variable",
                ),
                attribute={f"{parent_ncvar}:mesh": mesh_ncvar},
            )
            ok = False

        # SLB check attribute in question is always "mesh" here ->
        # looks like it could be "location" in some cases? No dims it seems?
        self._include_component_report(parent_ncvar, mesh_ncvar, "mesh")
        return ok

    def _ugrid_check_connectivity_variable(
        self, parent_ncvar, mesh_ncvar, connectivity_ncvar, connectivity_attr
    ):
        """Check a UGRID connectivity variable.

        .. versionadded:: (cfdm) 1.11.0.0

        :Parameters:

            parent_ncvar: `str`
                The netCDF variable name of the parent field
                construct.

            mesh_ncvar: `str`
                The netCDF variable name of the UGRID mesh topology
                variable.

            connectivity_ncvar: `str`
                The netCDF variable name of the UGRID connectivity
                variable.

            connectivity_attr: `str`
                The name of the UGRID connectivity attribute,
                e.g. ``'face_face_connectivity'``.

        :Returns:

            `bool`
                Whether or not the connectivity variable adheres to
                the CF conventions.

        """
        g = self.read_vars

        ok = True
        if connectivity_ncvar is None:
            self._add_message(
                parent_ncvar,
                connectivity_ncvar,
                message=(f"{connectivity_attr} attribute", "is missing"),
                direct_parent_ncvar=mesh_ncvar,
            )
            return False
        elif connectivity_ncvar not in g["internal_variables"]:
            connectivity_ncvar, message = self._missing_variable(
                connectivity_ncvar, f"{connectivity_attr} variable"
            )
            self._add_message(
                parent_ncvar,
                connectivity_ncvar,
                message=message,
                attribute={
                    f"{mesh_ncvar}:{connectivity_attr}": connectivity_ncvar
                },
                direct_parent_ncvar=mesh_ncvar,
            )
            return False
        else:
            ncvar_attrs = g["variable_attributes"][connectivity_ncvar]
            self._check_standard_names(
                parent_ncvar,
                connectivity_ncvar,
                ncvar_attrs,
                direct_parent_ncvar=mesh_ncvar,
            )

        parent_ncdims = self._ncdimensions(parent_ncvar)
        connectivity_ncdims = self._ncdimensions(connectivity_ncvar)[0]
        if not connectivity_ncdims[0] not in parent_ncdims:
            self._add_message(
                parent_ncvar,
                mesh_ncvar,
                message=(
                    f"UGRID {connectivity_attr} variable",
                    "spans incorrect dimensions",
                ),
                attribute={
                    f"mesh:{connectivity_attr}": f"{connectivity_ncvar}"
                },
                dimensions=g["variable_dimensions"][connectivity_ncvar],
            )
            ok = False

        return ok
