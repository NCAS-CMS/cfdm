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
    * incorporate, and create, metadata stored in external files,
    * read, write, and create data that have been compressed by
      convention (i.e. ragged or gathered arrays), whilst presenting a
      view of the data in its uncompressed form, and
    * read, write, and create coordinates defined by geometry cells
      (new in version 1.8.0).

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
_minimum_vn = '1.1.3'
if LooseVersion(cftime.__version__) < LooseVersion(_minimum_vn):
    raise ValueError(
        "Bad cftime version: cfdm requires cftime>={}. "
        "Got {} at {}".format(
            _minimum_vn, cftime.__version__, cftime.__file__))

from .constants import masked

# Internal ones passed on so they can be used in cf-python (see comment below)
from .functions import (
    ATOL,
    RTOL,
    CF,
    LOG_LEVEL,
    abspath,
    environment,
    _log_level,
    _disable_logging,
    _reset_log_emergence_level,
)

# Though these are internal-use methods, include them in the namespace
# (without documenting them) so that cf-python can use them internally too:
from .decorators import (
    _inplace_enabled,
    _inplace_enabled_define_and_cleanup,
    _manage_log_level_via_verbosity,
)


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


# Set up basic logging for the full project with a root logger
import logging
import sys

# Configure the root logger which all module loggers inherit from:
logging.basicConfig(
    stream=sys.stdout,
    style='{',              # default is old style ('%') string formatting
    format='{message}',     # no module names or datetimes etc. for basic case
    level=logging.WARNING,  # default but change level via LOG_LEVEL()
)

# And create custom level inbetween 'INFO' & 'DEBUG', to understand
# value see:
# https://docs.python.org/3.8/howto/logging.html#logging-levels
logging.DETAIL = 15  # set value as an attribute as done for built-in levels
logging.addLevelName(logging.DETAIL, 'DETAIL')

def detail(self, message, *args, **kwargs):
    if self.isEnabledFor(logging.DETAIL):
        self._log(logging.DETAIL, message, args, **kwargs)

logging.Logger.detail = detail
