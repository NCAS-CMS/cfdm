import logging

from .datamodel import NonConformance, Attribute, Variable

# TODO yet to incorporate dimensions (from .datamodel import Dimension) into
# the reporting, since the initial scope is to report issues with standard
# names. However the Conformance Data Model has set up the class Dimension
# which is trivial to associate with Variable and Attribute objects below,
# as appropriate.

logger = logging.getLogger(__name__)


class Report:
    """Reporting of CF Compliance non-conformance for field creation from netCDF.

    Holds methods for reporting about non-compliance.
    """

    def __init__(self):
        self.read_vars = {}  # intended to be overloaded by NetCDFRead
        self.dataset_compliance = {}
        self.variable_report = []

    def _process_dimension_sizes(self, ncvar):
        """Process dimension sizes to report in issues with dimensions."""
        # NOTE: not actually used yet, but will be when issues with Dimensions
        # are incorporated into the new Conformance Data Model.
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

        attribute_key = next(iter(attribute))
        higher_attr_value, attribute_name = attribute_key.split(":")
        attribute_value = attribute[attribute_key]

        # Potentially still a dict from init a dict so set here for now -
        # ugrid cases only seemingly hit this. How to avoid, and ensure that
        # the top-most Variable is the one corresponding to the field? May
        # at present be subject to _add_message call order which is bad.
        if self.dataset_compliance == {}:
            self.dataset_compliance = Variable(top_ancestor_ncvar)

        # 1. Create the relevant non-compliance objects
        # a) Non-conformance description for the message in question
        nc = [
            NonConformance(message, code),
        ]

        # b) Attributes of relevance - direct attribute and associated
        attr_lowest_nc = Attribute(
            attribute_name, value=higher_attr_value, non_conformances=nc
        )
        attr_highest_nc = Attribute(
            attribute_name, value=attribute_value, non_conformances=nc
        )

        # c) Variables of relevance - direct variable and those in association
        # If exist already, add to existing report. Note we also create
        # a direct_parent_ncvar_nc if appropriate, below.
        ncvar_nc = self._get_variable_non_compliance(ncvar)
        top_parent_ncvar_nc = self._get_variable_non_compliance(
            top_ancestor_ncvar
        )

        # 2. Make associations as appropriate
        if direct_parent_ncvar:
            direct_parent_ncvar_nc = self._get_variable_non_compliance(
                direct_parent_ncvar
            )

            # Dicts are optimised for key-value lookup, but this requires
            # value-key lookup - find a better way to get relevant attr using
            # functionality in this module
            varattrs = g["variable_attributes"][direct_parent_ncvar]
            reverse_varattrs = {v: k for k, v in varattrs.items()}
            store_attr = reverse_varattrs[ncvar]
            # Attribute value is same as the variable name in these cases
            store_attr_nc = Attribute(
                store_attr,
                value=ncvar,
                variables=[
                    ncvar_nc,
                ],
            )

            ncvar_nc.add_attribute(attr_highest_nc)
            store_attr_nc.add_variable(ncvar_nc)
            direct_parent_ncvar_nc.add_attribute(store_attr_nc)
            attr_lowest_nc.add_variable(direct_parent_ncvar_nc)
        else:
            # NO need to use copies here to avoid same attributes object
            # being included in the wrong places due to referencing. Don't
            # think deep copies are required but review that assumption.
            top_parent_ncvar_nc.add_attribute(attr_highest_nc)
            attr_lowest_nc.add_variable(top_parent_ncvar_nc)

        self.dataset_compliance.add_attribute(attr_highest_nc)

        if dimensions is None:  # pragma: no cover
            dimensions = ""  # pragma: no cover
        else:  # pragma: no cover
            dimensions = "(" + ", ".join(dimensions) + ")"  # pragma: no cover

        logger.info(
            "    Error processing netCDF variable "
            f"{ncvar}{dimensions}: {message}"
        )  # pragma: no cover

    def _include_component_report(
        self, parent_ncvar, ncvar, attribute, dimensions=None
    ):
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
        component_report = self._get_variable_non_compliance_report(
            parent_ncvar
        )
        # Unlike for 'attribute' input to _add_message, this 'attribute' is the
        # the attribute_name only and not "var_name:attribute_name" to split
        if component_report:
            ncvar_nc = self._get_variable_non_compliance(ncvar)

            # Attribute value is same as the variable name in these cases
            attr_nc = Attribute(attribute, value=ncvar)
            attr_nc.add_variable(ncvar_nc)
            self.dataset_compliance.add_attribute(attr_nc)

    def _get_variable_non_compliance_report(self, var):
        """Return if present a Variable NonCompliance stored in the report."""
        for variable in self.variable_report:
            if variable.name == var:
                return variable

        return False

    def _get_variable_non_compliance(self, var):
        """Return an existing else new Variable NonCompliance for a variable."""
        var_nc = self._get_variable_non_compliance_report(var)

        if not var_nc:
            var_nc = Variable(var)
            self.variable_report.append(var_nc)

        return var_nc
