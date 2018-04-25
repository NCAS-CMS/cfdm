'''

`CF <http://cfconventions.org/>`_ is a `netCDF
<http://www.unidata.ucar.edu/software/netcdf>`_ convention which is in
wide and growing use for the storage of model-generated and
observational data relating to the atmosphere, ocean and Earth system.

This package is an implementation of the CF data model

'''

__Conventions__  = 'CF-1.6'
__author__       = 'David Hassell'
__date__         = '2018-03-01'
__version__      = '1.6'

from distutils.version import StrictVersion
import platform

# Check the version of python
if not (StrictVersion('2.7.0')
        <= StrictVersion(platform.python_version())
        < StrictVersion('3.0.0')):
    raise ValueError(
        "Bad python version: cfdm requires 2.7 <= python < 3.0. Got {}".format(
        platform.python_version()))

from .bounds               import Bounds
from .cellextent           import CellExtent
from .coordinateconversion import CoordinateConversion
from .constants            import *
from .data.data            import Data
from .data.netcdfarray     import NetCDF
from .datum                import Datum
from .functions            import *
from .io.read              import read
from .io.write             import write

from .auxiliarycoordinate import AuxiliaryCoordinate
from .cellmeasure         import CellMeasure
from .cellmethod          import CellMethod
from .coordinatereference import CoordinateReference
from .dimensioncoordinate import DimensionCoordinate
from .domainancillary     import DomainAncillary
from .domainaxis          import DomainAxis
from .domain              import Domain
from .field               import Field
from .fieldancillary      import FieldAncillary



    
