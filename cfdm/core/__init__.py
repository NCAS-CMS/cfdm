'''

'''

__author__       = 'David Hassell'
__date__         = '2019-04-05'
__cf_version__   = '1.7'
__version__      = '1.7.2'

from distutils.version import LooseVersion
import platform

# Check the version of python
if LooseVersion(platform.python_version()) < LooseVersion('2.7.0'):
    raise ValueError(
        "cfdm requires python version >= 2.7. Got python version {}".format(
        platform.python_version()))

from .constructs import Constructs

from .functions import (CF,
                        environment)

from .data import (Data,
                   Array,
                   NumpyArray)

from .bounds               import Bounds
from .coordinateconversion import CoordinateConversion
from .datum                import Datum
from .domain               import Domain
from .interiorring         import InteriorRing

from .auxiliarycoordinate import AuxiliaryCoordinate
from .cellmeasure         import CellMeasure
from .cellmethod          import CellMethod
from .coordinatereference import CoordinateReference
from .dimensioncoordinate import DimensionCoordinate
from .domainancillary     import DomainAncillary
from .domainaxis          import DomainAxis
from .field               import Field
from .fieldancillary      import FieldAncillary





    
