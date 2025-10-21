import time
s = time.time()
print('0 data/__init__')

#from .abstract import Array, CompressedArray, MeshArray, RaggedArray

from .abstract import Array


from .abstract import CompressedArray


from .abstract import MeshArray


from .abstract import RaggedArray


from .subarray import (
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
)


from .subarray.abstract import MeshSubarray, Subarray, SubsampledSubarray

from .aggregatedarray import AggregatedArray
from .boundsfromnodesarray import BoundsFromNodesArray
from .cellconnectivityarray import CellConnectivityArray
from .gatheredarray import GatheredArray
from .fullarray import FullArray
from .h5netcdfarray import H5netcdfArray
from .netcdfarray import NetCDFArray
from .netcdf4array import NetCDF4Array
from .netcdfindexer import netcdf_indexer
from .numpyarray import NumpyArray
from .pointtopologyarray import PointTopologyArray
from .raggedcontiguousarray import RaggedContiguousArray
from .raggedindexedarray import RaggedIndexedArray
from .raggedindexedcontiguousarray import RaggedIndexedContiguousArray
from .sparsearray import SparseArray
from .subsampledarray import SubsampledArray
from .zarrarray import ZarrArray

from .data import Data

print('  9 data/__init__', time.time()-s)
