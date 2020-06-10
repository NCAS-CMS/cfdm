'''

'''

__author__       = 'David Hassell'
__date__         = '2020-06-10'
__cf_version__   = '1.8'
__version__      = '1.8.5'

from distutils.version import LooseVersion
import platform

_requires = ('numpy',
             'netCDF4',
             'future')

_error0 = 'cfdm.core requires the modules {}. '.format(', '.join(_requires))

try:
    import netCDF4
except ImportError as error1:
    raise ImportError(_error0+str(error1))

try:
    import numpy
except ImportError as error1:
    raise ImportError(_error0+str(error1))

try:
    import future
except ImportError as error1:
    raise ImportError(_error0+str(error1))

# Check the version of python
_minimum_vn = '2.7.0'
if LooseVersion(platform.python_version()) < LooseVersion(_minimum_vn):
    raise ValueError(
        "Bad python version: cfdm.core requires python>={}. "
        "Got {}".format(
            _minimum_vn,  platform.python_version()))

# Check the version of netCDF4
minimum_vn = '1.5.3'
if LooseVersion(netCDF4.__version__) < LooseVersion(minimum_vn):
    raise ValueError(
        "Bad netCDF4 version: cfdm.core requires netCDF4>={}. "
        "Got {} at {}".format(
            minimum_vn, netCDF4.__version__, netCDF4.__file__))

# Check the version of numpy
minimum_vn = '1.15'
if LooseVersion(numpy.__version__) < LooseVersion(minimum_vn):
    raise ValueError(
        "Bad numpy version: cfdm.core requires numpy>={}. "
        "Got {} at {}".format(
            minimum_vn, numpy.__version__, numpy.__file__))

from .constructs import Constructs

from .functions import (CF,
                        environment)

from .data import (Data,
                   Array,
                   NumpyArray)

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
