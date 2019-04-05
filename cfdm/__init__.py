'''cfdm is a complete implementation of the CF data model, that
identifies the fundamental elements of the CF conventions and shows
how they relate to each other, independently of the netCDF encoding.

The central element defined by the CF data model is the field
construct, which corresponds to a CF-netCDF data variable with all of
its metadata.

The cfdm package implements the CF data model for its internal data
structures and so is able to process any CF-compliant dataset. It is
not strict about CF-compliance, however, so that partially conformant
datasets may be modified in memory, as well as ingested from existing
datasets and written to new datasets. This is so that datasets which
are partially conformant may nonetheless be modified in memory and
written to new datasets.

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

Note that cfdm enables the creation of CF field constructs, but it's
up to the user to use them in a CF-compliant way.

'''

from . import core

__author__       = core.__author__
__date__         = core.__date__
__cf_version__   = core.__cf_version__
__version__      = core.__version__

requires = ('numpy',
            'netCDF4',
            'cftime',
            'future')

error0 = 'cfdm requires the modules {}. '.format(', '.join(requires))

from distutils.version import LooseVersion
import platform

# Check the version of python
minimum_vn = '2.7.0'
if LooseVersion(platform.python_version()) < LooseVersion(minimum_vn):
    raise ValueError(
        "Bad python version: cfdm requires python version {} or later. Got {}".format(
            minimum_vn,  platform.python_version()))

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
minimum_vn = '1.4.0'
if LooseVersion(netCDF4.__version__) < LooseVersion(minimum_vn):
    raise ValueError(
        "Bad netCDF4 version: cfdm requires netCDF4 version {} or later. Got {} at {}".format(
            minimum_vn, netCDF4.__version__, netCDF4.__file__))

# Check the version of numpy
minimum_vn = '1.15'
if LooseVersion(numpy.__version__) < LooseVersion(minimum_vn):
    raise ValueError(
        "Bad numpy version: cfdm requires numpy version {} or later. Got {} at {}".format(
            minimum_vn, numpy.__version__, numpy.__file__))

from .constants  import masked

from .functions import (CF,
                        environment,
                        ATOL,
                        RTOL)

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

from .count         import Count
from .index         import Index
from .list          import List
from .nodecount     import NodeCount
from .partnodecount import PartNodeCount

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




    
