'''

'''

__Conventions__  = 'CF-1.6'
__author__       = 'David Hassell'
__date__         = '2017-09-26'
__version__      = '0.1'

from .variable            import Variable
from .boundedvariable     import BoundedVariable
from .bounds              import Bounds
from .coordinate          import Coordinate
from .auxiliarycoordinate import AuxiliaryCoordinate
from .dimensioncoordinate import DimensionCoordinate
from .coordinatereference import CoordinateReference
from .cellmeasure         import CellMeasure
from .domainancillary     import DomainAncillary
from .domainaxis          import DomainAxis
from .domain              import Domain
from .field               import Field
from .fieldancillary      import FieldAncillary
from .data.data           import Data
from .data.array          import NetCDFArray
from .cellmethod          import CellMethod



    
