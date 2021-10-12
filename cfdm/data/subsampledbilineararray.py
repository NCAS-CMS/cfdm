import numpy as np

from .subsampledlineararray import SubsampledLinearArray


class SubsampledBilinearArray(SubsampledLinearArray):
    """TODO.

    .. versionadded:: (cfdm) TODO

    """

    def __init__(self, 
        compressed_array=None,
        shape=None,
        size=None,
        ndim=None,
        compressed_axes=None,
        tie_point_indices=None,
        interpolation_description=None,
        computational_precision=None,
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

            compressed_axes: sequence of `int`
                The position of the compressed axis in the tie points
                array.

                *Parameter example:*
                  ``compressed_axes=[1]``

            tie_point_indices: `dict`, optional
                TODO

        """
        super().__init__(
            compressed_array=compressed_array,
            shape=shape,
            size=size,
            ndim=ndim,
            compressed_axes=compressed_axes,
            interpolation_name="bilinear",
            tie_point_indices=tie_point_indices,
            interpolation_description=interpolation_description,
        )
        
    def __getitem__(self, indices):
        """x.__getitem__(indices) <==> x[indices]

        Returns a subspace of the array as an independent numpy array.

        .. versionadded:: (cfdm) TODO

        """
        try:
            # If the first or last element is requested then we don't
            # need to interpolate
            return self._first_or_last_index(indices)
        except IndexError:
            pass

        # ------------------------------------------------------------
        # Method: Uncompress the entire array and then subspace it
        # ------------------------------------------------------------
        d0, d1 = self.get_source_compressed_axes()

        tie_points = self.get_tie_points()

        # Initialise the un-sliced uncompressed array
        uarray = np.ma.masked_all(self.shape, dtype=float)

        for u_indices, tp_indices, subarea_size, first, _ in zip(
                *self.interpolation_subareas()
        ):
            ua = self._select_tie_points(tie_points, tp_indices,
                                         {d0: 0, d1: 0})       
            uc = self._select_tie_points(tie_points, tp_indices,
                                         {d0: 1, d1: 0})
            ub = self._select_tie_points(tie_points, tp_indices,
                                         {d0: 0, d1: 1})
            ud = self._select_tie_points(tie_points, tp_indices,
                                         {d0: 1, d1: 1})
            u = self._bilinear_interpolation(ua, uc, ub, ud, d0, d1,
                                             subarea_shape, first)
                       
            uarray[u_indices] = u

        self._s.cache_clear()

        return self.get_subspace(uarray, indices, copy=True)

    def _bilinear_interpolation(self, ua, uc, ub, ud, d0, d1,
                                subarea_shape, first):
        """Interpolate quadratically pairs of tie points.
        
        Computes the function` defined in CF appendix J:

        uac = fl(ua, uc, s(ia2, ic2, i2))
        ubd = fl(ub, ud, s(ia2, ic2, i2))
        u(i2, i1) = fl(uac, ubd, s(ia1, ib1, i1))

        .. versionadded:: (cfdm) 1.9.TODO.0
        
        .. seealso:: `_linear_interpolation`
        
        :Parameters:

            ua, uc, ub, ud: array_like
               The arrays containing the points for bilinear
               interpolation along dimensions *d0* and *d1*.

            d0, d1: `int`
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
        uac = self._linear_interpolation(ua, uc, d0, subarea_shape, first)
        ubd = self._linear_interpolation(ub, ud, d0, subarea_shape, first)
        u = self._linear_interpolation(uac, ubd, d1, subarea_shape, first)

        return u
