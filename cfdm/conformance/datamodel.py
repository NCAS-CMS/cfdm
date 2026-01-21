class NonConformance:
    """Represents a case of CF Conventions non-conformance with description."""

    def __init__(self, description):
        if not description:
            raise ValueError("Non-conformance description is required.")
        self.description = description


class Attribute:
    """Non-conformances related to a netCDF attribute."""

    def __init__(self, name, value=None, non_conformances=None):
        if not name:
            raise ValueError("Attribute name is required.")

        self.name = name
        self.value = value

        # UML: 1..* Non-conformance
        self.non_conformances = non_conformances or []
        if not self.non_conformances:
            raise ValueError(
                "Attribute must have at least one NonConformance."
            )

        # UML associations
        self.variables = []
        self.dimensions = []


class Dimension:
    """Non-conformances related to a netCDF dimension."""

    def __init__(self, name, size=None, non_conformances=None):
        if not name:
            raise ValueError("Dimension name is required.")

        self.name = name
        self.size = size

        # UML: 1..* Non-conformance
        self.non_conformances = non_conformances or []
        if not self.non_conformances:
            raise ValueError(
                "Dimension must have at least one NonConformance."
            )

        # UML associations
        self.variables = []


class Variable:
    """Non-conformances related to a netCDF variable."""

    def __init__(
        self, name, attributes=None, dimensions=None, non_conformances=None
    ):
        if not name:
            raise ValueError("Variable name is required.")

        self.name = name
        self.attributes = attributes or []
        self.dimensions = dimensions or []
        self.non_conformances = non_conformances or []

        # Establish bi-directional links
        for attribute in self.attributes:
            attribute.variables.append(self)

        for dimension in self.dimensions:
            dimension.variables.append(self)


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
