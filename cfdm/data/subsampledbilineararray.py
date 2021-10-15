import numpy as np

from .abstract import CompressedArray
from .mixin import LinearInterpolation, SubsampledArray


class SubsampledBilinearArray(
    LinearInterpolation, SubsampledArray, CompressedArray
):
    """TODO.

    .. versionadded:: (cfdm) TODO

    """

    def __init__(
        self,
        compressed_array=None,
        shape=None,
        size=None,
        ndim=None,
        dtype=None,
        compressed_axes=None,
        tie_point_indices=None,
        interpolation_description=None,
        computational_precision=None,
#        interpolation_variable=None,
    ):
        """Initialisation.

        :Parameters:

            compressed_array: `Data`
                The tie points array.

            shape: `tuple`
                The uncompressed array dimension sizes.

            size: `int`
                Number of elements in the uncompressed array.

            ndim: `int`
                The number of uncompressed array dimensions.

            dtype: data-type, optional
               The data-type for the uncompressed array. This datatype
               type is also used in all interpolation calculations. By
               default, the data-type is double precision float.

            compressed_axes: sequence of `int`
                The positions of the subsampled dimensions in the tie
                points array.

                *Parameter example:*
                  ``compressed_axes=[1, 2]``

            tie_point_indices: `dict`, optional
                The tie point index variable for each subsampled
                dimension. An integer key indentifies a subsampled
                dimensions by its position in the tie points array,
                and the value is a `TiePointIndex` variable.

            computational_precision: `str`, optional
                The floating-point arithmetic precision used during
                the preparation and validation of the compressed
                coordinates.

                *Parameter example:*
                  ``computational_precision='64'``

#             interpolation_variable: `Interpolation`

        """
        super().__init__(
            compressed_array=compressed_array,
            shape=shape,
            size=size,
            ndim=ndim,
            compressed_dimension=tuple(compressed_axes),
            compression_type="subsampled",
            interpolation_name="bilinear",
            tie_point_indices=tie_point_indices.copy(),
            computational_precision=computational_precision,
#            interpolation_variable=interpolation_variable,
        )

        if dtype is None:
            dtype = self._default_dtype

        self.dtype = dtype

    def __getitem__(self, indices):
        """x.__getitem__(indices) <==> x[indices]

        Returns a subspace of the array as an independent numpy array.

        .. versionadded:: (cfdm) TODO

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
        (d0, d1) = self.get_compressed_axes()

        tie_points = self.get_tie_points()

        # Interpolate the tie points for each interpolation subarea
        uarray = np.ma.masked_all(self.shape, dtype=self.dtype)

        for u_indices, tp_indices, subarea_shape, first, _ in zip(
            *self.interpolation_subareas()
        ):
            ua = self._select_tie_points(
                tie_points, tp_indices, {d0: 0, d1: 0}
            )
            uc = self._select_tie_points(
                tie_points, tp_indices, {d0: 1, d1: 0}
            )
            ub = self._select_tie_points(
                tie_points, tp_indices, {d0: 0, d1: 1}
            )
            ud = self._select_tie_points(
                tie_points, tp_indices, {d0: 1, d1: 1}
            )
            u = self._bilinear_interpolation(
                ua, uc, ub, ud, (d0, d1), subarea_shape, first
            )

            self._set_interpolated_values(uarray, u_indices, (d0, d1), u)

        self._s.cache_clear()

        return self.get_subspace(uarray, indices, copy=True)

    def _bilinear_interpolation(
        self, ua, uc, ub, ud, subsampled_dimensions, subarea_shape, first
    ):
        """Interpolate bilinearly between pairs of tie points.

        Computes the function defined in CF appendix J, where ``fl``
        is the linear interpolation operator:

        uac = fl(ua, uc, s(ia2, ic2, i2))
        ubd = fl(ub, ud, s(ia2, ic2, i2))
        u(i2, i1) = fl(uac, ubd, s(ia1, ib1, i1))

        .. versionadded:: (cfdm) 1.9.TODO.0

        .. seealso:: `_linear_interpolation`

        :Parameters:

            ua, uc, ub, ud: array_like
               The arrays containing the points for bilinear
               interpolation along dimensions *d0* and *d1*.

            subsampled_dimensions: 2-`tuple` of `int`
                The positions of the subsampled dimensions in the tie
                points array.

            subarea_shape: `tuple` of `int`
                The shape of the interpolation subararea, including
                all tie points.

            first: `tuple`
                For each dimension, True if the interpolation subarea
                is the first (in index space) of a new continuous
                area, otherwise False.

        :Returns:

            `numpy.ndarray`

        """
        (d0, d1) = subsampled_dimensions

        uac = self._linear_interpolation(ua, uc, (d0,), subarea_shape, first)
        ubd = self._linear_interpolation(ub, ud, (d0,), subarea_shape, first)
        u = self._linear_interpolation(uac, ubd, (d1,), subarea_shape, first)

        return u
