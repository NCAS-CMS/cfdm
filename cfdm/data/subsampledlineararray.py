import numpy as np

from .abstract import CompressedArray
from .mixin import LinearInterpolation, SubsampledArray


class SubsampledLinearArray(
    LinearInterpolation, SubsampledArray, CompressedArray
):
    """An underlying subsampled array with linear interpolatin.

    The information needed to uncompress the data is stored in an tie
    point index variable that defines the relationship between the
    indices of the subsampled dimension and the indices of its
    corresponding interpolated dimension.

    >>> coords = cfdm.SubsampledLinearArray(
    ...     compressed_array=cfdm.Data([15, 135, 225, 255, 345]),
    ...     shape=(12,),
    ...     ndim=1,
    ...     size=12,
    ...     tie_point_indices={0: cfdm.TiePointIndex(data=[0, 4, 7, 8, 11])},
    ... )
    >>> print(coords[...])
    [15.0 45.0 75.0 105.0 135.0 165.0 195.0 225.0 255.0 285.0 315.0 345.0]

    **Cell boundaries**

    If the subsampled array contains cell boundaries, then the
    *shape*, *ndim* and *size* parameters that describe the
    uncompressed array will include the required trailing size 2
    dimension.

    >>> bounds = cfdm.SubsampledLinearArray(
        compressed_array=cfdm.Data([0, 150, 240, 240, 360]),
        shape=(12, 2),
        ndim=2,
        size=24,
        tie_point_indices={0: cfdm.TiePointIndex(data=[0, 4, 7, 8, 11])},
    )
    >>> print(bounds[...])
    [[0.0 30.0]
     [30.0 60.0]
     [60.0 90.00000000000001]
     [90.00000000000001 120.0]
     [120.0 150.0]
     [150.0 180.0]
     [180.0 210.0]
     [210.0 240.0]
     [240.0 270.0]
     [270.0 300.0]
     [300.0 330.0]
     [330.0 360.0]]

    .. versionadded:: (cfdm) 1.9.TODO.0

    """

    def __init__(
        self,
        compressed_array=None,
        shape=None,
        size=None,
        ndim=None,
#        dtype=None,
        tie_point_indices={},
        computational_precision=None,
    ):
        """**Initialisation**

        :Parameters:

            compressed_array: `Data`
                The subsampled array.

            shape: `tuple`
                The uncompressed array shape.

            size: `int`
                Number of elements in the uncompressed array, must be
                equal to the product of *shape*.

            ndim: `int`
                The number of uncompressed array dimensions, equal to
                the length of *shape*.

#            dtype: data-type, optional
#               The data-type for the uncompressed array. This datatype
#               type is also used in all interpolation calculations. By
#               default, the data-type is double precision float.

            compressed_axes: sequence of `int`
                The position of the compressed axis in the tie points
                array. Only one axis may be compressed.

                *Parameter example:*
                  ``compressed_axes=[1]``

            tie_point_indices: `dict`
                The tie point index variable for each subsampled
                dimension. A key indentifies a subsampled dimension by
                its integer position in the compressed array, and its
                value is a `TiePointIndex` variable.

                *Parameter example:*
                  ``tie_point_indices={1: cfdm.TiePointIndex(data=[0, 16])}``

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
            interpolation_name="linear",
            computational_precision=computational_precision,
            tie_point_indices=tie_point_indices.copy(),
            compressed_dimensions=tuple(tie_point_indices),
            one_to_one=True,
        )
        
#        if dtype is None:
#            dtype = self._default_dtype
#
#        self.dtype = dtype

    def __getitem__(self, indices):
        """x.__getitem__(indices) <==> x[indices]

        Returns a subspace of the uncompressed array as an independent
        numpy array.

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        # If the first or last element is requested then we don't need
        # to interpolate
        try:
            return self._first_or_last_index(indices)
        except IndexError:
            pass

        # ------------------------------------------------------------
        # Method: Uncompress the entire array and then subspace it
        # ------------------------------------------------------------
        (d0,) = tuple(self.compressed_dimensions())

        tie_points = self._get_compressed_Array()

        # Initialise the un-sliced uncompressed array
        uarray = np.ma.masked_all(self.shape, np.dtype(float))

        # Interpolate the tie points for each interpolation subarea
        for u_indices, tp_indices, subarea_shape, first, _ in zip(
            *self._interpolation_subareas()
        ):
            ua = self._select_tie_points(tie_points, tp_indices, {d0: 0})
            ub = self._select_tie_points(tie_points, tp_indices, {d0: 1})
            u = self._linear_interpolation(ua, ub, d0, subarea_shape, first)
            self._set_interpolated_values(uarray, u, u_indices, (d0,))

        self._s.cache_clear()

        return self.get_subspace(uarray, indices, copy=True)
