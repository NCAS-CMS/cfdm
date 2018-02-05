'''

`CF <http://cfconventions.org/>`_ is a `netCDF
<http://www.unidata.ucar.edu/software/netcdf>`_ convention which is in
wide and growing use for the storage of model-generated and
observational data relating to the atmosphere, ocean and Earth system.

This package is an implementation of the `CF data model
<http://cf-trac.llnl.gov/trac/ticket/95>`_, and as such it is an API
allows for the full scope of data and metadata interactions described
by the CF conventions.

With this package you can:

  * Read `CF-netCDF <http://cfconventions.org/>`_ files.
  
  * Create CF fields.

  * Write fields to CF-netCDF and CFA-netCDF files on disk.

  * Create, delete and modify a field's data and metadata.

  * Select fields according to their metadata.

  * Subspace fields

  * Sensibly deal with date-time data.

  * Read discrete sampling geometry datasets.

  * Read variables that have been compressed by gathering.

'''

__Conventions__  = 'CF-1.6'
__author__       = 'David Hassell'
__date__         = '2017-09-26'
__version__      = '0.1'

from distutils.version import StrictVersion
import platform

# Check the version of python
if not (StrictVersion('2.7.0')
        <= StrictVersion(platform.python_version())
        < StrictVersion('3.0.0')):
    raise ValueError(
        "Bad python version: cfdm requires 2.7 <= python < 3.0. Got {}".format(
        platform.python_version()))

import structure

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
from .read.read           import read
from .write.write         import write
from .units               import Units
from .cfdatetime          import Datetime, dt
from .data.data           import Data
from .data.array          import NetCDFArray
from .flags               import Flags
from .cellmethod          import CellMethod
#from .netcdf.read         import netcdf_read
from .constants           import *
from .functions           import *
#from .functions           import _open_netcdf_file



    
