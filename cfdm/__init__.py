'''cfdm is a complete implementation of the CF data model, that
identifies the fundamental elements of the CF conventions and shows
how they relate to each other, independently of the netCDF encoding.

The central element defined by the CF data model is the field
construct, which corresponds to a CF-netCDF data variable with all of
its metadata.

The cfdm package can

    * read field constructs from netCDF datasets,
    * create new field constructs in memory,
    * inspect field constructs,
    * test whether two field constructs are the same,
    * modify field construct metadata and data,
    * create subspaces of field constructs,
    * write field constructs to netCDF datasets on disk,
    * incorporate, and create, metadata stored in external files, and
    * read, write, and create data that have been compressed by
      convention (i.e. ragged or gathered arrays), whilst presenting a
      view of the data in its uncompressed form.

'''

__author__       = 'David Hassell'
__date__         = '2018-11-28'
__cf_version__   = '1.7'
__version__      = '1.7b7'

from distutils.version import StrictVersion
import platform

# Check the version of python
if StrictVersion(platform.python_version()) < StrictVersion('2.7.0'):
    raise ValueError(
        "Bad python version: cfdm requires python 2.7 or later. Got {}".format(
        platform.python_version()))

from .constants        import *
from .constructs       import Constructs

from .data import (Data,
                   Array,
                   CompressedArray,
                   NumpyArray,
                   NetCDFArray,
                   GatheredArray,
                   RaggedContiguousArray,
                   RaggedIndexedArray,
                   RaggedIndexedContiguousArray)

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

from .io import (read, write)


    
