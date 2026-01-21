# TODO move all _check methods from netcdfread to here! For now, only
# include new classes for PR #373 to make reviewing simpler.

import logging
logger = logging.getLogger(__name__)

import numpy as np

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
                        f"has a value that is not a string",
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
                        f"has a value that is not appropriate to "
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
