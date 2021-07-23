""""""

__date__ = "2021-05-25"
__cf_version__ = "1.8"
__version__ = "1.8.9.0"

import platform
from distutils.version import LooseVersion

_requires = (
    "numpy",
    "netCDF4",
)

_error0 = f"cfdm.core requires the modules {', '.join(_requires)}. "

try:
    import netCDF4
except ImportError as error1:
    raise ImportError(_error0 + str(error1))

try:
    import numpy
except ImportError as error1:
    raise ImportError(_error0 + str(error1))

# Check the version of python
_minimum_vn = "3.6.0"
if LooseVersion(platform.python_version()) < LooseVersion(_minimum_vn):
    raise ValueError(
        f"Bad python version: cfdm.core requires python>={_minimum_vn}. "
        f"Got {platform.python_version()}"
    )

# Check the version of netCDF4
_minimum_vn = "1.5.4"
if LooseVersion(netCDF4.__version__) < LooseVersion(_minimum_vn):
    raise ValueError(
        f"Bad netCDF4 version: cfdm.core requires netCDF4>={_minimum_vn}. "
        f"Got {netCDF4.__version__} at {netCDF4.__file__}"
    )

# Check the version of numpy
_minimum_vn = "1.15"
if LooseVersion(numpy.__version__) < LooseVersion(_minimum_vn):
    raise ValueError(
        f"Bad numpy version: cfdm.core requires numpy>={_minimum_vn}. "
        f"Got {numpy.__version__} at {numpy.__file__}"
    )

from .abstract import (Container, Coordinate, Parameters,
                       ParametersDomainAncillaries, Properties, PropertiesData,
                       PropertiesDataBounds)
from .auxiliarycoordinate import AuxiliaryCoordinate
from .bounds import Bounds
from .cellmeasure import CellMeasure
from .cellmethod import CellMethod
from .constructs import Constructs
from .coordinateconversion import CoordinateConversion
from .coordinatereference import CoordinateReference
from .data import Array, Data, NumpyArray
from .datum import Datum
from .dimensioncoordinate import DimensionCoordinate
from .domain import Domain
from .domainancillary import DomainAncillary
from .domainaxis import DomainAxis
from .field import Field
from .fieldancillary import FieldAncillary
from .functions import CF, environment
from .interiorring import InteriorRing
from .meta import DocstringRewriteMeta
