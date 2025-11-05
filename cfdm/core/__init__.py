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

# Count the number of docstrings (first element), and the number which
# have docstring substitutions applied to them (second element).
_docstring_substitutions = [0, 0]

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
