import numpy as np

from .abstract import CompressedArray
from .mixin import Subsampled
from .subarray import SubsampledBiLinearSubarray


class SubsampledBiLinearArray(Subsampled, CompressedArray):
    """A subsampled array with bi-linear interpolation.

    The information needed to uncompress the data is stored in a tie
    point index variable that defines the relationship between the
    indices of the subsampled dimensions and the indices of the
    corresponding interpolated dimensions.

    **Cell boundaries**

    If the subsampled array represents cell boundaries, then the
    *shape*, *ndim* and *size* parameters that describe the
    uncompressed array will include the required trailing size 2
    dimension.

    .. versionadded:: (cfdm) 1.9.TODO.0

    """

    def __new__(cls, *args, **kwargs):
        """Store component classes.

        .. note:: If a child class requires different component
                  classes than the ones defined here, then they must
                  be redefined in the __new__ method of the child
                  class.

        """
        instance = super().__new__(cls)
        instance._Subarray = SubsampledBiLinearSubarray
        return instance

    def __init__(
        self,
        compressed_array=None,
        shape=None,
        size=None,
        ndim=None,
        interpolation_description=None,
        computational_precision=None,
        tie_point_indices={},
    ):
        """**Initialisation**

        :Parameters:

            compressed_array: `Data`
                The tie points array.

            shape: `tuple`
                The uncompressed array dimension sizes.

            size: `int`
                Number of elements in the uncompressed array.

            ndim: `int`
                The number of uncompressed array dimensions.

            tie_point_indices: `dict`
                The tie point index variable for each subsampled
                dimension. A key indentifies a subsampled dimension by
                its integer position in the compressed array, and its
                value is a `TiePointIndex` variable.

                *Parameter example:*
                  ``tie_point_indices={0: cfdm.TiePointIndex(data=[0, 16]), 2: cfdm.TiePointIndex(data=[0, 20, 20])}``

            computational_precision: `str`, optional
                The floating-point arithmetic precision used during
                the preparation and validation of the compressed
                coordinates.

                *Parameter example:*
                  ``computational_precision='64'``

        """
        super().__init__(
            compressed_array=compressed_array,
            shape=shape,
            size=size,
            ndim=ndim,
            compression_type="subsampled",
            interpolation_name="bi_linear",
            tie_point_indices=tie_point_indices.copy(),
            computational_precision=computational_precision,
            compressed_dimensions=tuple(sorted(tie_point_indices)),
            one_to_one=True,
        )

#   def __getitem__(self, indices):
#       """Return a subspace of the uncompressed data.
#
#       x.__getitem__(indices) <==> x[indices]
#
#       Returns a subspace of the uncompressed data as an independent
#       numpy array.
#
#       .. versionadded:: (cfdm) TODO
#
#       """
#       # If the first or last element is requested then we don't need
#       # to interpolate
#       try:
#           return self._first_or_last_index(indices)
#       except IndexError:
#           pass
#
#       # ------------------------------------------------------------
#       # Method: Uncompress the entire array and then subspace it
#       # ------------------------------------------------------------
#       subsampled_dimensions = self.compressed_dimensions()
#
#       tie_points = self._get_compressed_Array()
#           
#       # Initialise the un-sliced uncompressed array
#       uarray = np.ma.masked_all(self.shape, dtype=np.dtype(float))
#
#       for u_indices, tp_indices, subarea_shape, first, _ in zip(
#           *self._interpolation_subareas()
#       ):
#           subarray = self._SubsampledBiLinearSubarray(
#               tie_points=tie_points,
#               tp_indices=tp_indices,
#               subsampled_dimensions=subsampled_dimensions,
#               shape=subarea_shape,
#               first=first
#           )
#           uarray[u_indices] = subarray[...]
#
#       return self.get_subspace(uarray, indices, copy=True)
    
