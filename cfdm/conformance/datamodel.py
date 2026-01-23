class NonConformance:
    """Represents a case of CF Conventions non-conformance with description."""

    def __init__(self, reason, code):
        if (
            not reason
            or not code
            or not isinstance(reason, str)
            or not isinstance(code, int)
        ):
            raise ValueError(
                "Non-conformance object requires a string reason and an "
                "integer code."
            )
        self.reason = reason
        self.code = code

    def as_report_fragment(self):
        """Report the non-conformance in dictionary fragment form."""
        return {
            "reason": self.reason,
            "code": self.code,
        }

    def __repr__(self):
        """Called by the `repr` built-in function.

        x.__repr__() <==> repr(x)
        """
        return str(self.as_report_fragment())


class Attribute:
    """Non-conformances related to a netCDF attribute."""

    def __init__(
        self,
        name,
        value=None,
        non_conformances=None,
        variables=None,
        dimensions=None,
    ):
        if not name and not isinstance(name, str):
            raise ValueError("Attribute name (a string) is required.")

        self.name = name
        self.value = value

        # Must be a non-empty list of NonConformance objects
        # if (
        #     not isinstance(non_conformances, list)
        #     or not non_conformances
        #     or not all(
        #         isinstance(nc, NonConformance) for nc in non_conformances
        #     )
        # ):
        #     raise TypeError(
        #         f"Parameter 'non_conformances' for Dimension {name} "
        #         "must be a non-empty list of NonConformance instances."
        #     )

        # UML: 1..* Non-conformance
        self.non_conformances = non_conformances or []

        # UML associations
        self.variables = variables or []
        self.dimensions = dimensions or []

    def set_variables(self, variables):
        """Set variables associated with the attribute's non-compliance."""
        self.variables = variables

    def set_dimensions(self, dimensions):
        """Set dimensions associated with the attribute's non-compliance."""
        self.dimensions = dimensions

    def add_variable(self, var):
        """Append a variable relating to the attribute's non-compliance."""
        # Check if already there first
        for vari in self.variables:
            if vari.equals(var):
                print("VAR already exists!, COMBINING")
                # Need to combine components
                var.combine(vari)
                return vari

        self.variables.append(var)
        return var

    def add_dimension(self, dim):
        """Append a dimension relating to the attribute's non-compliance."""
        self.dimensions.append(dim)

    def as_report_fragment(self):
        """Report the attribute non-compliance in dictionary form.

        For a more concise dict with class-based value representation,
        see repr().
        """
        return {
            "value": self.value,
            "variables": {
                var_nc.name: var_nc.as_report_fragment()
                for var_nc in self.variables
            },
            "dimensions": {
                dim_nc.name: dim_nc.as_report_fragment()
                for dim_nc in self.dimensions
            },
            "non-conformance": [
                nc.as_report_fragment() for nc in self.non_conformances
            ],
        }

        def __repr__(self):
            """Called by the `repr` built-in function.

            x.__repr__() <==> repr(x)
            """
            return str({
                "value": self.value,
                "variables": self.variables,
                "dimensions": self.dimensions,
                "non-conformance": self.non_conformances,
            })

    def equals(self, other):
        """Equality checking between same class."""
        return self.name == other.name

    def combine(self, other):
        """Combine one Attribute object with another when they represent the
        same underlying netCDF attribute.

        Returns the self object where the other should be discarded.

        TODO shorten summary line to one line.
        """
        # Need to combine components
        old_vars = self.variables
        old_dims = self.dimensions
        self.set_variables(old_vars + other.variables)
        self.set_dimensions(old_dims + other.dimensions)

        return self


class Dimension:
    """Non-conformances related to a netCDF dimension."""

    def __init__(self, name, size=None, non_conformances=None, variables=None):
        if not name and not isinstance(name, str):
            raise ValueError("Dimension name (a string) is required.")

        self.name = name
        self.size = size

        # UML: 1..* Non-conformance
        self.non_conformances = non_conformances or []

        # Must be a non-empty list of NonConformance objects
        # if (
        #     not isinstance(non_conformances, list)
        #     or not non_conformances
        #     or not all(
        #         isinstance(nc, NonConformance) for nc in non_conformances
        #     )
        # ):
        #     raise TypeError(
        #         f"Parameter 'non_conformances' for Dimension {name} "
        #         "must be a non-empty list of NonConformance instances."
        #     )

        # UML associations
        self.variables = variables or []

    def set_variables(self, variables):
        """Set variables associated with the dimension's non-compliance."""
        self.variables = variables

    def add_variable(self, attr):
        """Append a variable relating to the dimension's non-compliance."""
        self.variables.append(attr)

    def as_report_fragment(self):
        """Report the dimension non-compliance in dictionary form.

        For a more concise dict with class-based value representation,
        see repr().
        """
        return {
            "size": self.size,
            "variables": {
                var_nc.name: var_nc.as_report_fragment()
                for var_nc in self.variables
            },
            "non-conformance": [
                nc.as_report_fragment() for nc in self.non_conformances
            ],
        }

    def __repr__(self):
        """Called by the `repr` built-in function.

        x.__repr__() <==> repr(x)
        """
        return str({
            "size": self.size,
            "variables": self.variables,
            "non-conformance": self.non_conformances,
        })

    def equals(self, other):
        """Equality checking between same class."""
        return self.name == other.name

    def combine(self, other):
        """Combine one Dimension object with another when they represent the
        same underlying netCDF dimension.

        Returns the self object where the other should be discarded.

        TODO shorten summary line to one line.
        """
        # Need to combine components
        old_vars = self.variables
        self.set_variables(old_vars + other.variables)

        return self


class Variable:
    """Non-conformances related to a netCDF variable."""

    def __init__(
        self,
        name,
        non_conformances=None,
        attributes=None,
        dimensions=None,
    ):
        if not name and not isinstance(name, str):
            raise ValueError("Variable name (a string) is required.")

        self.name = name
        self.non_conformances = non_conformances or []  # optional for a var

        self.attributes = attributes or []
        self.dimensions = dimensions or []

    def set_attributes(self, attributes):
        """Set attributes associated with the variable's non-compliance."""
        self.attributes = attributes

    def set_dimensions(self, dimensions):
        """Set dimensions associated with the variable's non-compliance."""
        self.dimensions = dimensions

    def add_attribute(self, attr):
        """Append an attribute relating to the variable's non-compliance."""
        # Check if already there first
        for attrib in self.attributes:
            if attrib.equals(attr):
                print("ATTR already exists!, COMBINING")
                # Need to combine components
                attr.combine(attrib)

                # NOW REMOVE OTHER FROM LIST!
                return attrib

        self.attributes.append(attr)
        return attr

    def add_dimension(self, dim):
        """Append a dimension relating to the variable's non-compliance."""
        self.dimensions.append(dim)

    def as_report_fragment(self):
        """Report the variable non-compliance in dictionary fragment form.

        For a more concise dict with class-based value representation,
        see repr().
        """
        fragment = {
            "attributes": {
                attr_nc.name: attr_nc.as_report_fragment()
                for attr_nc in self.attributes
            },
            "dimensions": {
                dim_nc.name: dim_nc.as_report_fragment()
                for dim_nc in self.dimensions
            },
        }
        if self.non_conformances:
            fragment["non-conformance"] = [
                nc.as_report_fragment() for nc in self.non_conformances
            ]
        return fragment

    def __repr__(self):
        """Called by the `repr` built-in function.

        x.__repr__() <==> repr(x)
        """
        return str({
            "attributes": self.attributes,
            "dimensions": self.dimensions,
            "non-conformance": self.non_conformances,
        })

    def get_variable(self, var_name):
        """Fetch a child variable connected via an attribute, else is False."""
        count = []
        for attr in self.attributes:
            for var in attr.variables:
                if var.name == var_name:
                    count.append(var)

        print("COUNT IS", len(count))
        if count:
            return count[0]

        return False

    def equals(self, other):
        """Equality checking between same class."""
        return self.name == other.name

    def combine(self, other):
        """Combine one Variable object with another when they represent the
        same underlying netCDF variable.

        Returns the self object where the other should be discarded.

        TODO shorten summary line to one line.
        """
        # Need to combine components
        old_dims = self.dimensions
        old_attrs = self.attributes
        self.set_dimensions(old_dims + other.dimensions)
        self.set_attributes(old_attrs + other.attributes)

        return self


class DataDomainVariable(Variable):
    """A data or domain variable with associated conventions."""

    def __init__(
        self,
        name,
        conventions,
        attributes=None,
        dimensions=None,
        non_conformances=None,
    ):
        if not conventions:
            raise ValueError("Conventions are required.")

        super().__init__(
            name=name,
            attributes=attributes,
            dimensions=dimensions,
            non_conformances=non_conformances,
        )

        self.conventions = conventions
