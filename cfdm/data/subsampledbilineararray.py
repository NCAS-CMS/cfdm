import numpy as np

from .abstract import CompressedArray
from .mixin import LinearInterpolation, SubsampledArray


class SubsampledBilinearArray(
    LinearInterpolation, SubsampledArray, CompressedArray
):
    """TODO.

    **Cell boundaries**

    If the subsampled array contains cell boundaries, then the
    *shape*, *ndim* and *size* parameters that describe the
    uncompressed array will include the required trailing size 2
    dimension.

    .. versionadded:: (cfdm) TODO

    """

    def __init__(
        self,
        compressed_array=None,
        shape=None,
        size=None,
        ndim=None,
#        dtype=None,
        tie_point_indices={},
        interpolation_description=None,
        computational_precision=None,
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

#            dtype: data-type, optional
#               The data-type for the uncompressed array. This datatype
#               type is also used in all interpolation calculations. By
#               default, the data-type is double precision float.

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
            compressed_dimensions=tuple(tie_point_indices),
            one_to_one=True,
        )

#        if dtype is not None:
#            self.dtype = dtype

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
        (d0, d1) = sorted(self.compressed_dimensions())

        tie_points = self._get_compressed_Array()

        # Interpolate the tie points for each interpolation subarea
        uarray = np.ma.masked_all(self.shape, dtype=np.dtype(float))

        for u_indices, tp_indices, subarea_shape, first, _ in zip(
            *self._interpolation_subareas()
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

            self._set_interpolated_values(uarray, u, u_indices, (d0, d1))

        self._s.cache_clear()

        return self.get_subspace(uarray, indices, copy=True)

    def _bilinear_interpolation(
        self,
        ua,
        uc,
        ub,
        ud,
        subsampled_dimensions,
        subarea_shape,
        first,
        trim=True,
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
                The positions of the subsampled dimensions in the
                compressed data.

            subarea_shape: `tuple` of `int`
                The shape of the interpolation subararea, including
                all tie points.

            first: `tuple`
                For each dimension, True if the interpolation subarea
                is the first (in index space) of a new continuous
                area, otherwise False.

            trim: `bool`, optional
                For each subsampled dimension, remove the first point
                of the interpolation subarea when it is not the first
                (in index space) of a continuous area, and when the
                compressed data are not bounds tie points.

        :Returns:

            `numpy.ndarray`

        """
        (d0, d1) = subsampled_dimensions

        uac = self._linear_interpolation(
            ua, uc, d0, subarea_shape, first, trim=trim
        )
        ubd = self._linear_interpolation(
            ub, ud, d0, subarea_shape, first, trim=trim
        )
        u = self._linear_interpolation(
            uac, ubd, d1, subarea_shape, first, trim=trim
        )

        return u
