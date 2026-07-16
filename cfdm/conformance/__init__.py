from .checker import FieldChecker, Report
from .datamodel import (
    AttributeNonConformance,
    DimensionNonConformance,
    NonConformanceCase,
    VariableNonConformance,
)

# Allow users to access TODO though not yet advertised (i.e. in the API ref)
# - wait until conformance work is more mature before doing this
from .standardnames import (
    get_all_current_standard_names,
)

# Eventually structure as with individual modules per class, something like:
# from .attributeconformance import AttributeNonConformance
# from .variableconformance import VariableNonConformance
# from .dimensionconformance import DimensionNonConformance
# from .nonconformance import NonConformanceCase
