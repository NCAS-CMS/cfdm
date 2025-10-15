"""`cfdm.core`, the core reference implementation of the CF data model.

It is a stand-alone core implementation that includes no functionality
beyond that mandated by the CF data model (and therefore excludes any
information about the netCDF encoding of constructs).

The core implementation provides the basis (via inheritance) for the
`cfdm` package that provides further practical functionality in
addition, for example enabling the reading and writing of netCDF
datasets and the inspection of CF data model constructs.

"""

__date__ = "2025-10-15"
__cf_version__ = "1.12"
__version__ = "1.12.3.1"

from platform import python_version

_requires = ("numpy", "packaging")
_error0 = f"cfdm.core requires the modules {', '.join(_requires)}. "

# Check the version of packaging
try:
    import packaging
    from packaging.version import Version
except ImportError as error1:
    raise ImportError(_error0 + str(error1))
else:
    _minimum_vn = "20.0"
    if Version(packaging.__version__) < Version(_minimum_vn):
        raise RuntimeError(
            f"Bad packaging version: cf requires packaging>={_minimum_vn}. "
            f"Got {packaging.__version__} at {packaging.__file__}"
        )

# Check the version of python
_minimum_vn = "3.10.0"
if Version(python_version()) < Version(_minimum_vn):
    raise ValueError(
        f"Bad python version: cfdm.core requires python>={_minimum_vn}. "
        f"Got {python_version()}"
    )

# Check the version of numpy
try:
    import numpy as np
except ImportError as error1:
    raise ImportError(_error0 + str(error1))
else:
    _minimum_vn = "2.0.0"
    if Version(np.__version__) < Version(_minimum_vn):
        raise ValueError(
            f"Bad numpy version: cfdm.core requires numpy>={_minimum_vn}. "
            f"Got {np.__version__} at {np.__file__}"
        )

del _minimum_vn

from .constructs import Constructs

from .functions import CF, environment

from .data import Data, Array, NumpyArray

from .bounds import Bounds
from .coordinateconversion import CoordinateConversion
from .datum import Datum
from .domain import Domain
from .interiorring import InteriorRing

from .auxiliarycoordinate import AuxiliaryCoordinate
from .cellconnectivity import CellConnectivity
from .cellmeasure import CellMeasure
from .cellmethod import CellMethod
from .coordinatereference import CoordinateReference
from .dimensioncoordinate import DimensionCoordinate
from .domainancillary import DomainAncillary
from .domainaxis import DomainAxis
from .domaintopology import DomainTopology
from .field import Field
from .fieldancillary import FieldAncillary

from .abstract import (
    Container,
    Properties,
    PropertiesData,
    PropertiesDataBounds,
    Coordinate,
    Parameters,
    ParametersDomainAncillaries,
    Topology,
)

from .meta import DocstringRewriteMeta
