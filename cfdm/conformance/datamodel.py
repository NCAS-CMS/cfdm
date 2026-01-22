class NonConformance:
    """Represents a case of CF Conventions non-conformance with description."""

    def __init__(self, reason, code):
        if (
                not reason or not code or not isinstance(reason, str) or not
                isinstance(code, int)
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


class Attribute:
    """Non-conformances related to a netCDF attribute."""

    def __init__(self, name, value=None, non_conformances=None):
        if not name and not isinstance(name, str):
            raise ValueError("Attribute name (a string) is required.")

        self.name = name
        self.value = value

        # Must be a non-empty list of NonConformance objects
        if (
                not isinstance(non_conformances, list) or
                not non_conformances or
                not all(
                    isinstance(nc, NonConformance) for nc in non_conformances)
        ):
                raise TypeError(
                    f"Parameter 'non_conformances' for Dimension {name} "
                    "must be a non-empty list of NonConformance instances."
            )

        # UML associations
        self.variables = []
        self.dimensions = []

    def as_report_fragment(self):
        """Report the attribute non-compliance in dictionary fragment form."""
        return {
            "value": self.value,
            "non-conformance": self.non_conformances,
        }


class Dimension:
    """Non-conformances related to a netCDF dimension."""

    def __init__(self, name, size=None, non_conformances=None):
        if not name and not isinstance(name, str):
            raise ValueError("Dimension name (a string) is required.")

        self.name = name
        self.size = size

        # UML: 1..* Non-conformance
        self.non_conformances = non_conformances or []

        # Must be a non-empty list of NonConformance objects
        if (
                not isinstance(non_conformances, list) or
                not non_conformances or
                not all(
                    isinstance(nc, NonConformance) for nc in non_conformances)
        ):
                raise TypeError(
                    f"Parameter 'non_conformances' for Dimension {name} "
                    "must be a non-empty list of NonConformance instances."
            )

        # UML associations
        self.variables = []

    def as_report_fragment(self):
        """Report the dimension non-compliance in dictionary fragment form."""
        return {
            "size": self.size,
            "non-conformance": self.non_conformances,
        }


class Variable:
    """Non-conformances related to a netCDF variable."""

    def __init__(
        self, name, attributes=None, dimensions=None, non_conformances=None
    ):
        if not name and not isinstance(name, str):
            raise ValueError("Variable name (a string) is required.")

        self.name = name
        self.non_conformances = non_conformances or []  # optional for a var

        self.attributes = attributes or []
        self.dimensions = dimensions or []

        # Establish bi-directional links between the netCDF components
        for attribute in self.attributes:
            attribute.variables.append(self)

        for dimension in self.dimensions:
            dimension.variables.append(self)

    def as_report_fragment(self):
        """Report the variable non-compliance in dictionary fragment form."""
        return {
            "non-conformance": self.non_conformances,
        }


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
