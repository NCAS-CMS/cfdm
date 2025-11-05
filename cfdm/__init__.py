"""Cfdm is a reference implementation of the CF data model.

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

The cfdm package can:

    * read field constructs from netCDF, CDL, and Zarr datasets,
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

from . import core

__date__ = core.__date__
__cf_version__ = core.__cf_version__
__version__ = core.__version__

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
    chunksize,
    configuration,
    dirname,
    environment,
    integer_dtype,
    log_level,
    parse_indices,
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
    netcdf_flatten,
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
    Array,
    AggregatedArray,
    BoundsFromNodesArray,
    CellConnectivityArray,
    CompressedArray,
    Data,
    FullArray,
    GatheredArray,
    H5netcdfArray,
    NetCDFArray,
    NetCDF4Array,
    netcdf_indexer,
    NumpyArray,
    PointTopologyArray,
    RaggedArray,
    RaggedContiguousArray,
    RaggedIndexedArray,
    RaggedIndexedContiguousArray,
    SparseArray,
    SubsampledArray,
    ZarrArray,
)

from .data import (
    BiLinearSubarray,
    BiQuadraticLatitudeLongitudeSubarray,
    BoundsFromNodesSubarray,
    CellConnectivitySubarray,
    GatheredSubarray,
    InterpolationSubarray,
    LinearSubarray,
    QuadraticLatitudeLongitudeSubarray,
    QuadraticSubarray,
    RaggedSubarray,
    Subarray,
    SubsampledSubarray,
)

from .count import Count
from .index import Index
from .interpolationparameter import InterpolationParameter
from .list import List
from .nodecountproperties import NodeCountProperties
from .partnodecountproperties import PartNodeCountProperties
from .tiepointindex import TiePointIndex

from .bounds import Bounds
from .coordinateconversion import CoordinateConversion
from .datum import Datum
from .interiorring import InteriorRing
from .quantization import Quantization

from .units import Units

from .auxiliarycoordinate import AuxiliaryCoordinate
from .cellconnectivity import CellConnectivity
from .cellmeasure import CellMeasure
from .cellmethod import CellMethod
from .coordinatereference import CoordinateReference
from .dimensioncoordinate import DimensionCoordinate
from .domain import Domain
from .domainancillary import DomainAncillary
from .domainaxis import DomainAxis
from .domaintopology import DomainTopology
from .field import Field
from .fieldancillary import FieldAncillary

from .abstract import Implementation
from .cfdmimplementation import CFDMImplementation, implementation

from .read_write import read, write
from .read_write.netcdf.flatten import dataset_flatten

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
