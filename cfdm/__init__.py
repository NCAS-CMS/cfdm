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

_requires = ('cftime',)

_error0 = 'cfdm requires the modules {}. '.format(', '.join(_requires))

from distutils.version import LooseVersion
import platform


try:
    import cftime
except ImportError as error1:
    raise ImportError(_error0+str(error1))

# Check the version of cftime
_minimum_vn = '1.1.1'
if LooseVersion(cftime.__version__) < LooseVersion(_minimum_vn):
    raise ValueError(
        "Bad cftime version: cfdm requires cftime version {} or later. Got {} at {}".format(
            _minimum_vn, cftime.__version__, cftime.__file__))

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

from .count                   import Count
from .index                   import Index
from .list                    import List
from .nodecountproperties     import NodeCountProperties
from .partnodecountproperties import PartNodeCountProperties

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

from .abstract           import Implementation
from .cfdmimplementation import (CFDMImplementation,
                                 implementation)

from .read_write import (read,
                         write)

from .examplefield import example_field


    
    
