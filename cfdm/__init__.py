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
__date__         = '2019-01-22'
__cf_version__   = '1.7'
__version__      = '1.7.0b13'

requires = ('numpy',
            'netCDF4',
            'cftime',
            'future')

error0 = 'cfdm requires the modules {}. '.format(', '.join(requires))

from distutils.version import LooseVersion
import platform

# Check the version of python
min_vn = '2.7.0'
if LooseVersion(platform.python_version()) < LooseVersion(min_vn):
    raise ValueError(
        "Bad python version: cfdm requires python version {} or later. Got {}".format(
            min_vn,  platform.python_version()))

try:
    import netCDF4
except ImportError as error1:
    raise ImportError(error0+str(error1))

try:
    import numpy
except ImportError as error1:
    raise ImportError(error0+str(error1))

try:
    import cftime
except ImportError as error1:
    raise ImportError(error0+str(error1))

try:
    import future
except ImportError as error1:
    raise ImportError(error0+str(error1))

# Check the version of netCDF4
min_vn = '1.4.0'
if LooseVersion(netCDF4.__version__) < LooseVersion(min_vn):
    raise ValueError(
        "Bad netCDF4 version: cfdm requires netCDF4 version {} or later. Got {}".format(
            min_vn, netCDF4.__version__))

from .constants  import *
from .constructs import Constructs

from .data import (Data,
                   Array,
                   CompressedArray,
                   NumpyArray,
                   NetCDFArray,
                   GatheredArray,
                   RaggedContiguousArray,
                   RaggedIndexedArray,
                   RaggedIndexedContiguousArray)

from .functions import (CF,
                        environment,
                        ATOL,
                        RTOL)

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

from .read_write import (read,
                         write,
                         implementation,
                         CFDMImplementation)




    
