# TODO move all _check methods from netcdfread to here! For now, only
# include new classes for PR #373 to make reviewing simpler.

import logging
logger = logging.getLogger(__name__)

import numpy as np

from ..read_write.netcdf.constants import CF_QUANTIZATION_PARAMETERS
from .standardnames import get_all_current_standard_names


class Checker():
    """Contains checks of CF Compliance for Field instantiation from netCDF."""

    def _check_standard_names(
            self, top_ancestor_ncvar,
            ncvar, ncvar_attrs, direct_parent_ncvar=None,
            check_is_string=True, check_is_in_table=True,
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
            attribute_value = {
                f"{ncvar}:{sn_attr}": sn_value
            }
            logger.debug(
                f"Found a {sn_attr} of '{sn_value}' on {ncvar}"
            )

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
                    check_is_in_custom_list and sn_value not in
                    check_is_in_custom_list
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
                    check_is_in_table and sn_value not in
                    get_all_current_standard_names()
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

    # ================================================================
    # Methods for checking CF compliance
    #
    # These methods (whose names all start with "_check") check the
    # minimum required for mapping the file to CFDM structural
    # elements.
    #
    # General CF compliance is not checked (e.g. whether or
    # not grid mapping variable has a grid_mapping_name attribute)
    # except for the case of (so far):
    #   * whether (computed_)standard_name values are valid according
    #     to specified criteria under Section 3.3. of the Conformance
    #     document.
    # ================================================================

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
                tie_point_interp_ncvar_attrs = g[
                    "variable_attributes"][tie_point_ncvar]
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
