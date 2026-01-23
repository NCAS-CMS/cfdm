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

        # TODO need better way to access this - inefficient, should be able to
        # use an in-built function!
        attribute_key = next(iter(attribute))
        # TODO tidy below into one call to split
        var_name, attribute_name = attribute_key.split(":")
        if var_name != ncvar:
            print("Different var name and ncvar!")
        # print("HAVE FOR ATTRS SOMETHINGS", attribute_key.split(":"))
        attribute_value = attribute[attribute_key]

        print(
            "HAVE", var_name, attribute_name, attribute_value, ncvar,
            top_ancestor_ncvar, direct_parent_ncvar
        )
        # print("ALL OF G IS, looking for pa -> mesh -> Mesh2 \n\n\n\n")
        # pprint(g)

        # Potentially still a dict from init a dict so set here for now -
        # ugrid cases only seemingly hit this
        if g["dataset_compliance"] == {}:
            print("DC NOT SET!")
            g["dataset_compliance"] = Variable(top_ancestor_ncvar)
        if g["component_report"] == {}:
            print("CR NOT SET!")
            g["component_report"] = Variable(top_ancestor_ncvar)

        # if is_ugrid:
        #     attr_01 = "mesh"
        # else:
        #     attr_01 = "?var?"
        # attr_01_nc = Attribute(attr_01, value="???")
        # g["dataset_compliance"].add_attribute(attr_01_nc)
        # g["component_report"].add_attribute(attr_01_nc)
        # Now do variables nested!

        nc = [NonConformance(message, code),]

        attr_01_nc = Attribute(
            attribute_name, value=attribute_value, non_conformances=nc)
        var_01_nc = g["dataset_compliance"].get_variable(top_ancestor_ncvar)
        if not var_01_nc:
            print("NEW CREATE 01")
            var_01_nc = Variable(top_ancestor_ncvar)
        else:
            print("USING EXISTING 01!")

        # NOTE: ncvar == var_name still unused! Use below
        if direct_parent_ncvar:
            # Dicts are optimised for key-value lookup, but this requires
            # value-key lookup - find a better way to get relevant attr using
            # functionality in this module
            varattrs = g["variable_attributes"][direct_parent_ncvar]
            reverse_varattrs = {v: k for k, v in varattrs.items()}
            store_attr = reverse_varattrs[ncvar]
            print("HAVE STORE ATTR OF", store_attr)
            store_attr_nc = Attribute(store_attr, value="???")

            # In thise case, can join to ncvar via the direct parent
            var_03_nc = g["dataset_compliance"].get_variable(ncvar)
            if not var_03_nc:
                print("NEW CREATE 03")
                var_03_nc = Variable(ncvar)
            else:
                print("USING EXISTING 03!")
            store_attr_nc.add_variable(var_03_nc)
            var_01_nc.add_attribute(store_attr_nc)

        attr_01_nc.add_variable(var_01_nc)
        g["dataset_compliance"].add_attribute(attr_01_nc)
        g["component_report"].add_attribute(attr_01_nc)

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
        if g["dataset_compliance"] == {}:
            return
            # g["dataset_compliance"] = Variable(parent_ncvar)
        if g["component_report"] == {}:
            return
            # print("CR WAS DICT")
            # g["component_report"] = Variable(parent_ncvar)

        component_report = g["component_report"].get_variable(ncvar)
        print("COMPONENT REPORT IS", type(component_report))

        # Unlike for 'attribute' input to _add_message, this 'attribute' is the
        # the attribute_name only and not "var_name:attribute_name" to split
        if component_report:
            var_nc = g["dataset_compliance"].get_variable(ncvar)
            if not var_nc:
                var_nc = Variable(ncvar)

            par_var_nc = g["dataset_compliance"].get_variable(parent_ncvar)
            if not par_var_nc:
                par_var_nc = Variable(parent_ncvar)

            attr_nc = Attribute(attribute, value="????")
            attr_nc.add_variable(var_nc)
            attr_nc.add_variable(par_var_nc)

            g["dataset_compliance"].add_attribute(attr_nc)
            # g["component_report"].add_attribute(attr_nc)

    def _create_var_nc(
            self, nc, ncvar, attribute_name, attribute_value, dimensions=None):
        """Create NonCompliance for a variable and associated attribute."""
        g = self.read_vars

        attr_nc = Attribute(
            attribute_name, value=attribute_value,
            non_conformances=nc,
        )

        dim_nc_list = []
        if dimensions is not None:
            for dim in dimensions:
                dim_nc_list.append(
                    Dimension(dim, size=g["internal_dimension_sizes"][dim]),
                )

        var_nc = Variable(
            ncvar, attributes=[attr_nc,], dimensions=dim_nc_list)

        return var_nc, attr_nc
