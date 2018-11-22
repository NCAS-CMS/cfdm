'''

'''

__Conventions__  = '1.8'
__author__       = 'David Hassell'
__date__         = '2018-06-26'
__version__      = '1.6beta'

from distutils.version import LooseVersion
import platform

# Check the version of python
if LooseVersion(platform.python_version()) < LooseVersion('2.7.0'):
    raise ValueError(
        "cfdm requires python version >= 2.7. Got python version {}".format(
        platform.python_version()))

from .bounds               import Bounds
from .constructs           import Constructs
from .coordinateconversion import CoordinateConversion

#from .data.data            import Data
#from .data.numpyarray      import NumpyArray
from .data                import (Data,
                                  Array,
                                  NumpyArray)

from .datum               import Datum
from .domain              import Domain
from .interiorring        import InteriorRing

from .auxiliarycoordinate import AuxiliaryCoordinate
from .cellmeasure         import CellMeasure
from .cellmethod          import CellMethod
from .coordinatereference import CoordinateReference
from .dimensioncoordinate import DimensionCoordinate
from .domainancillary     import DomainAncillary
from .domainaxis          import DomainAxis
from .field               import Field
from .fieldancillary      import FieldAncillary





    
