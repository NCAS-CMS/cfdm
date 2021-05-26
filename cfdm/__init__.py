"""cfdm is a reference implementation of the CF data model.

It identifies the fundamental elements of the CF conventions and
shows how they relate to each other, independently of the netCDF
encoding.

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

    * read field constructs from netCDF and CDL datasets,
    * create new field constructs in memory,
    * write and append field constructs to netCDF datasets on disk,
    * read, write, and create datasets containing hierarchical groups,
    * read, write, and create coordinates defined by geometry cells,
    * inspect field constructs,
    * test whether two field constructs are the same,
    * modify field construct metadata and data,
    * create subspaces of field constructs,
    * incorporate, and create, metadata stored in external files, and
    * read, write, and create data that have been compressed by
      convention (i.e. ragged or gathered arrays), whilst presenting a
      view of the data in its uncompressed form.

Note that cfdm enables the creation of CF field constructs, but it's
up to the user to use them in a CF-compliant way.

"""
import logging
import sys

from distutils.version import LooseVersion

from . import core

__date__ = core.__date__
__cf_version__ = core.__cf_version__
__version__ = core.__version__

_requires = ("cftime", "netcdf_flattener")

_error0 = f"cfdm requires the modules {', '.join(_requires)}. "

try:
    import cftime
except ImportError as error1:
    raise ImportError(_error0 + str(error1))

# Check the version of cftime
_minimum_vn = "1.5.0"
if LooseVersion(cftime.__version__) < LooseVersion(_minimum_vn):
    raise ValueError(
        f"Bad cftime version: cfdm requires cftime>={_minimum_vn}. "
        f"Got {cftime.__version__} at {cftime.__file__}"
    )

try:
    import netcdf_flattener
except ImportError as error1:
    raise ImportError(_error0 + str(error1))

# Check the version of netcdf_flattener
_minimum_vn = "1.2.0"
if LooseVersion(netcdf_flattener.__version__) < LooseVersion(_minimum_vn):
    raise ValueError(
        f"Bad netcdf_flattener version: cfdm requires "
        f"netcdf_flattener>={_minimum_vn}. Got {netcdf_flattener.__version__} "
        f"at {netcdf_flattener.__file__}"
    )

from .constants import masked

# Internal ones passed on so they can be used in cf-python (see
# comment below)
from .functions import (
    ATOL,
    CF,
    LOG_LEVEL,
    RTOL,
    abspath,
    atol,
    configuration,
    environment,
    log_level,
    rtol,
    unique_constructs,
    _disable_logging,
    _reset_log_emergence_level,
    _is_valid_log_level_int,
    Configuration,
    Constant,
    ConstantAccess,
    is_log_level_debug,
    is_log_level_detail,
    is_log_level_info,
)

# Though these are internal-use methods, include them in the namespace
# (without documenting them) so that cf-python can use them internally
# too:
from .decorators import (
    _inplace_enabled,
    _inplace_enabled_define_and_cleanup,
    _manage_log_level_via_verbosity,
    _display_or_return,
)

from .constructs import Constructs

from .data import (
    Data,
    Array,
    CompressedArray,
    NumpyArray,
    NetCDFArray,
    GatheredArray,
    RaggedContiguousArray,
    RaggedIndexedArray,
    RaggedIndexedContiguousArray,
)

from .count import Count
from .index import Index
from .list import List
from .nodecountproperties import NodeCountProperties
from .partnodecountproperties import PartNodeCountProperties

from .bounds import Bounds
from .coordinateconversion import CoordinateConversion
from .datum import Datum
from .domain import Domain
from .interiorring import InteriorRing

from .auxiliarycoordinate import AuxiliaryCoordinate
from .cellmeasure import CellMeasure
from .cellmethod import CellMethod
from .coordinatereference import CoordinateReference
from .dimensioncoordinate import DimensionCoordinate
from .domainancillary import DomainAncillary
from .domainaxis import DomainAxis
from .field import Field
from .fieldancillary import FieldAncillary

from .abstract import Implementation
from .cfdmimplementation import CFDMImplementation, implementation

from .read_write import read, write

from .examplefield import example_field, example_fields, example_domain

from .abstract import Container

# --------------------------------------------------------------------
# Set up basic logging for the full project with a root logger
# --------------------------------------------------------------------
# Configure the root logger which all module loggers inherit from:
logging.basicConfig(
    stream=sys.stdout,
    style="{",  # default is old style ('%') string formatting
    format="{message}",  # no module names or datetimes etc. for basic case
    level=logging.WARNING,  # default but change level via log_level()
)

# And create custom level inbetween 'INFO' & 'DEBUG', to understand
# value see:
# https://docs.python.org/3.8/howto/logging.html#logging-levels
logging.DETAIL = 15  # set value as an attribute as done for built-in levels
logging.addLevelName(logging.DETAIL, "DETAIL")


def detail(self, message, *args, **kwargs):
    """Sets up a custom logging level named 'detail'."""
    if self.isEnabledFor(logging.DETAIL):
        self._log(logging.DETAIL, message, args, **kwargs)


logging.Logger.detail = detail
