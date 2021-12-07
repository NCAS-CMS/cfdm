from .abstract import CompressedArray

from .abstract import CompressedArray
from .mixin import Subsampled
from .subarray import SubsampledBiQuadraticLatitudeLongitudeSubarray


class SubsampledBiQuadraticLatitudeLongitudeArray(Subsampled, CompressedArray):
    """A subsampled array with bi-quadratic latitude-longitude
    interpolation.

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
        instance._Subarray = SubsampledBiQuadraticLatitudeLongitudeSubarray
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
        parameters={},
        parameter_dimensions={},
        dependent_tie_points={},
        dependent_tie_point_dimensions={},
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

            compressed_axes: sequence of `int`
                The position of the compressed axis in the tie points
                array.

                *Parameter example:*
                  ``compressed_axes=[1]``

            tie_point_indices: `dict`, optional
                TODO

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
            interpolation_name="bi_quadratic_latitude_longitude",
            computational_precision=computational_precision,
            tie_point_indices=tie_point_indices.copy(),
            parameters=parameters.copy(),
            parameter_dimensions=parameter_dimensions.copy(),
            dependent_tie_points=dependent_tie_points.copy(),
            dependent_tie_point_dimensions=dependent_tie_point_dimensions.copy(),
            compressed_dimensions=tuple(tie_point_indices),
            one_to_one=True,
        )

#    def __getitem__(self, indices):
#        """Return a subspace of the uncompressed data.
#
#        x.__getitem__(indices) <==> x[indices]
#
#        Returns a subspace of the uncompressed data as an independent
#        numpy array.
#
#        .. versionadded:: (cfdm) 1.9.TODO.0
#
#        """
#        # If the first or last element is requested then we don't need
#        # to interpolate
#        try:
#            return self._first_or_last_index(indices)
#        except IndexError:
#            pass
#
#        # ------------------------------------------------------------
#        # Method: Uncompress the entire array and then subspace it
#        # ------------------------------------------------------------
#        subsampled_dimensions = tuple(self.compressed_dimensions())
#
#        tie_points = self._get_compressed_Array()
#      
#        self.conform()
#        parameters = self.get_parameters()
#        dependent_tie_points = self.get_dependent_tie_points()
#        
#        # Initialise the un-sliced uncompressed array
#        uarray = np.ma.masked_all(self.shape, dtype=np.dtype(float))
#
#        for u_indices, tp_indices, subarea_shape, first, subarea_indices in (
#                zip(*self._interpolation_subareas())
#        ):
#            subarray = self._Subarray(
#                tie_points=tie_points,
#                tp_indices=tp_indices,
#                subsampled_dimensions=subsampled_dimensions,
#                shape=subarea_shape,
#                first=first,
#                subarea_indices=subarea_indices,
#                parameters=parameters,
#                dependent_tie_points=dependent_tie_points,
#            )
#            uarray[u_indices] = subarray[...]
#
#        return self.get_subspace(uarray, indices, copy=True)
