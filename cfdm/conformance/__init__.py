from .checker import Checker

from .standardnames import (
    get_all_current_standard_names,
    # Intended for internal use but used in testing, so need exposing:
    _extract_names_from_xml,
    _STD_NAME_CURRENT_XML_URL
)

# Eventually structure as with individual modules per class, like:
# from .domainvariable import DomainVariable
# from .ncattribute import NetCDFAttribute
# from .ncvariable import NetCDFVariable
# from .ncdimension import NetCDFDimension
# from .nonconformance import NonConformanceReport
