import logging
from pprint import pprint

from .datamodel import NonConformance, Attribute, Dimension, Variable

logger = logging.getLogger(__name__)


class Report():
    """Reporting of CF Compliance non-conformance for field creation from netCDF.

    Holds methods for reporting about non-compliance.
    """

    def _process_dimension_sizes(self, ncvar):
        """Process dimension sizes."""
        g = self.read_vars

        var_dims = g["variable_dimensions"][ncvar]
        return {
            dim: {"size": g["internal_dimension_sizes"][dim]}
            # Here the 'or []' addition ensures var_dims of None -> {} output
            for dim in (var_dims or [])
        }

    def _add_message(
        self,
        top_ancestor_ncvar,
        ncvar,
        direct_parent_ncvar=None,
        message=None,
        attribute=None,
        dimensions=None,
        conformance=None,
        # is_ugrid=False,
    ):
        """Stores and logs a message about an issue with a field.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            top_ancestor_ncvar: `str`
                The netCDF variable name of the ancestor variable
                under which to register the component problem at the
                top level.

                This is usually the parent variable of the variable
                `ncvar` which has the component problem, but may be
                a higher parent e.g. grandparent variable, when there is
                an intermediate parent variable in which the problem
                should also be registered using `direct_parent_ncvar`,
                or `ncvar` itself, where no parent variable exists or
                is relevant.

                *Parameter example:*
                  ``'tas'``

            ncvar: `str`
                The netCDF variable name with the component that
                has the problem.

                *Parameter example:*
                  ``'rotated_latitude_longitude'``

            direct_parent_ncvar: `str` or `None`, optional
                The netCDF variable name of the variable which is the
                direct parent of the variable `ncvar` which has the
                component problem, *only to be provided* if a higher
                parent such as a grandparent variable is set as
                the `top_ancestor_ncvar` where it is also important
                to register the problem on the direct parent.

                If `None`, the default, then the problem is not
                not registered for any further (parent) variable
                than `top_ancestor_ncvar`.

                *Parameter example:*
                  ``'time'``

            message: (`str`, `str`), optional

            attribute: `dict`, optional
                The name and value of the netCDF attribute that has a problem.

                *Parameter example:*
                  ``attribute={'tas:cell_measures': 'area: areacella'}``

            dimensions: sequence of `str`, optional
                The netCDF dimensions of the variable that has a problem.

                *Parameter example:*
                  ``dimensions=('lat', 'lon')``

        """
        g = self.read_vars

        if message is not None:
            try:
                code = self._code0[message[0]] * 1000 + self._code1[message[1]]
            except KeyError:
                code = None

            message = " ".join(message)
        else:
            code = None

        # OLD
        # TODO need better way to access this - inefficient, should be able to
        # use an in-built function!
        attribute_key = next(iter(attribute))
        higher_attr_value, attribute_name = attribute_key.split(":")
        #if var_name != ncvar:
        #    print("Different var name and ncvar!")
        attribute_value = attribute[attribute_key]

        print(
            "£££££" * 10,
            "HAVE", higher_attr_value, attribute_name, attribute_value, ncvar,
            top_ancestor_ncvar, direct_parent_ncvar
        )
        # print("ALL OF G IS, looking for pa -> mesh -> Mesh2 \n\n\n\n")
        # pprint(g)

        # if is_ugrid:
        #     attr_01 = "mesh"
        # else:
        #     attr_01 = "?var?"
        # attr_01_nc = Attribute(attr_01, value="???")
        # g["dataset_compliance"].add_attribute(attr_01_nc)
        # g["component_report"].add_attribute(attr_01_nc)
        # Now do variables nested!

        # Potentially still a dict from init a dict so set here for now -
        # ugrid cases only seemingly hit this
        if g["dataset_compliance"] == {}:
            print("DC NOT SET!")
            g["dataset_compliance"] = Variable(top_ancestor_ncvar)
        if g["component_report"] == {}:
            print("CR NOT SET!")
            g["component_report"] = Variable(top_ancestor_ncvar)

        # 1. Create the relevant non-compliance objects
        # a) Non-conformance description for the message in question
        nc = [NonConformance(message, code),]

        # b) Attributes of relevance - direct attribute and associated
        attr_lowest_nc = Attribute(
            attribute_name, value=attribute_value, non_conformances=nc)
        attr_highest_nc = Attribute(
            attribute_name, value=higher_attr_value, non_conformances=nc)

        # c) Variables of relevance - direct variable and those in association
        # If exist already, add to existing report. Note we also create
        # a direct_parent_ncvar_nc if appropriate, below.
        ncvar_nc = self._get_variable_non_compliance(ncvar)
        top_parent_ncvar_nc = self._get_variable_non_compliance(
            top_ancestor_ncvar)

        # 2. Make associations as appropriate
        # * If direct parent, connect DC - > top -> parent -> direct
        #   variable via the intermediate attribute connecting them,
        # * If no direct parent, connect DC -> top -> direct variable
        #   via: DC -> highest attr -> top ncvar -> lowest attr -> ncvar
        if direct_parent_ncvar:
            direct_parent_ncvar_nc = self._get_variable_non_compliance(
                direct_parent_ncvar)

            # Dicts are optimised for key-value lookup, but this requires
            # value-key lookup - find a better way to get relevant attr using
            # functionality in this module
            varattrs = g["variable_attributes"][direct_parent_ncvar]
            reverse_varattrs = {v: k for k, v in varattrs.items()}
            store_attr = reverse_varattrs[ncvar]
            print("HAVE STORE ATTR OF", store_attr)
            # Attribute value is same as the variable name in these cases
            store_attr_nc = Attribute(
                store_attr, value=ncvar, non_conformances=nc)

            ncvar_nc.add_attribute(attr_highest_nc)
            store_attr_nc.add_variable(ncvar_nc)
            direct_parent_ncvar_nc.add_attribute(store_attr_nc)
            attr_lowest_nc.add_variable(direct_parent_ncvar_nc)
        else:
            attr_highest_nc.add_variable(ncvar_nc)
            top_parent_ncvar_nc.add_attribute(attr_highest_nc)
            attr_lowest_nc.add_variable(top_parent_ncvar_nc)

        # GOOD WORKING WELL ENOUGH BELOW

        g["dataset_compliance"].add_attribute(attr_lowest_nc)
        g["component_report"].add_attribute(attr_lowest_nc)


        if dimensions is None:  # pragma: no cover
            dimensions = ""  # pragma: no cover
        else:  # pragma: no cover
            dimensions = "(" + ", ".join(dimensions) + ")"  # pragma: no cover

        logger.info(
            "    Error processing netCDF variable "
            f"{ncvar}{dimensions}: {message}"
        )  # pragma: no cover

    def _include_component_report(
            self, parent_ncvar, ncvar, attribute, dimensions=None):
        """Include a component in the dataset compliance report.

        .. versionadded:: (cfdm) 1.11.0.0

        :Parameters:

            parent_ncvar: `str`
                The netCDF variable name of the parent variable.

                *Parameter example:*
                  ``'tas'``

            ncvar: `str`
                The netCDF variable name of the variable with
                the component that has the problem.

            attribute: `dict`
                The name and value of the netCDF attribute that has a problem.

                *Parameter example:*
                  ``attribute={'tas:cell_measures': 'area: areacella'}``

            dimensions: sequence of `str`, optional
                The netCDF dimensions of the variable that has a problem.

                *Parameter example:*
                  ``dimensions=('lat', 'lon')``

        :Returns:

            `None`

        """
        g = self.read_vars

        # Potentially still a dict from init a dict so set here for now -
        # ugrid cases only seemingly hit this
        if g["component_report"] == {}:
            print("CR WAS DICT")
            g["component_report"] = Variable(ncvar)

        component_report = g["component_report"].get_variable(ncvar)
        print("COMPONENT REPORT IS", type(component_report))

        # Unlike for 'attribute' input to _add_message, this 'attribute' is the
        # the attribute_name only and not "var_name:attribute_name" to split
        if component_report:
            ncvar_nc = self._get_variable_non_compliance(ncvar)
            parent_ncvar_nc = self._get_variable_non_compliance(ncvar)

            # Attribute value is same as the variable name in these cases
            attr_nc = Attribute(attribute, value=ncvar)
            attr_nc.add_variable(ncvar_nc)
            attr_nc.add_variable(parent_ncvar_nc)

            g["dataset_compliance"].add_attribute(attr_nc)
            # g["component_report"].add_attribute(attr_nc)

    def _get_variable_non_compliance(self, var):
        """Get a variable's NonCompliance stored in the dataset compliance."""
        g = self.read_vars

        var_nc = g["dataset_compliance"].get_variable(var)
        if not var_nc:
            print(f"New, creating: {var}")
            print("COMP REPORT IS",g["component_report"])
            var_nc = Variable(var)
        else:
            print(f"Using existing NC for {var}: {var_nc}")

        return var_nc
