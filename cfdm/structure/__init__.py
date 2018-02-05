'''

'''

__Conventions__  = 'CF-1.7'
__author__       = 'David Hassell'
__date__         = '2018-02-01'
__version__      = '1.7'

from distutils.version import StrictVersion
import platform

# Check the version of python
if not (StrictVersion('2.7.0')
        <= StrictVersion(platform.python_version())
        < StrictVersion('3.0.0')):
    raise ValueError(
        "Bad python version: cfdm requires 2.7 <= python < 3.0. Got {}".format(
        platform.python_version()))

from .bounds              import Bounds
from .constructs          import Constructs
from .coordinate          import Coordinate
from .coordinateancillary import CoordinateAncillary
from .data.data           import Data
from .data.array          import NetCDFArray
from .domain              import Domain

from .auxiliarycoordinate import AuxiliaryCoordinate
from .cellmeasure         import CellMeasure
from .cellmethod          import CellMethod
from .coordinatereference import CoordinateReference
from .dimensioncoordinate import DimensionCoordinate
from .domainancillary     import DomainAncillary
from .domainaxis          import DomainAxis
from .field               import Field
from .fieldancillary      import FieldAncillary





    
