'''

`CF <http://cfconventions.org/>`_ is a `netCDF
<http://www.unidata.ucar.edu/software/netcdf>`_ convention which is in
wide and growing use for the storage of model-generated and
observational data relating to the atmosphere, ocean and Earth system.

This package is an implementation of the CF data model

'''

__author__       = 'David Hassell'
__date__         = '2018-11-27'
__cf_version__   = '1.7'
__version__      = '1.7b6'

from distutils.version import StrictVersion
import platform

# Check the version of python
if StrictVersion(platform.python_version()) < StrictVersion('2.7.0'):
    raise ValueError(
        "Bad python version: cfdm requires 2.7 <= python. Got {}".format(
        platform.python_version()))

from .constants        import *
from .constructs       import Constructs

#from .data.data                         import Data
#from .data.netcdfarray                  import NetCDFArray
from .data                              import (Data,
                                                Array,
                                                CompressedArray,
                                                NumpyArray,
                                                NetCDFArray,
                                                GatheredArray,
                                                RaggedContiguousArray,
                                                RaggedIndexedArray,
                                                RaggedIndexedContiguousArray)
#from .data.numpyarray                   import NumpyArray
#from .data.gatheredarray                import GatheredArray
#from .data.raggedcontiguousarray        import RaggedContiguousArray
#from .data.raggedindexedarray           import RaggedIndexedArray
#from .data.raggedindexedcontiguousarray import RaggedIndexedContiguousArray

#from .functions        import *
from .functions import (CF, environment, ATOL, RTOL)

from .count import Count
from .index import Index
from .list  import List

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

from .io import read, write


    
