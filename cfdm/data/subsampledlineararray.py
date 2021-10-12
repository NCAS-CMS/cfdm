import numpy as np

from .subsampledgeneralarray import SubsampledGeneralArray


class SubsampledLinearArray(SubsampledGeneralArray):
    """TODO.

    .. versionadded:: (cfdm) 1.9.TODO.0

    """
    
    def __init__(
            self, 
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
            interpolation_name="linear",
            tie_point_indices=tie_point_indices,
            interpolation_description=interpolation_description,
            computational_precision=computational_precision,            
        )
        
    def __getitem__(self, indices):
        """x.__getitem__(indices) <==> x[indices]

        Returns a subspace of the array as an independent numpy array.

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        try:
            super().__getitem__(indices)
        except IndexError:
            pass
#        try:
#            # If exactly the first or last element is requested then
#            # we don't need to interpolate
#            return self._first_or_last_index(indices)
#        except IndexError:
#            pass

        # ------------------------------------------------------------
        # Method: Uncompress the entire array and then subspace it
        # ------------------------------------------------------------
        (d0,) = self.get_compressed_axes()

        tie_points = self.get_tie_points()

        # Initialise the un-sliced uncompressed array
        uarray = np.ma.masked_all(self.shape, dtype=float)

        # Interpolate the tie points according to CF appendix J
        for u_indices, tp_indices, subarea_shape, first, _ in zip(
            *self.interpolation_subareas()
        ):
            ua = self._select_tie_points(tie_points, tp_indices, {d0: 0})
            ub = self._select_tie_points(tie_points, tp_indices, {d0: 1})
            u = self._linear_interpolation(
                ua, ub, d0, subarea_shape, first
            )
            uarray[u_indices] = u

        self._s.cache_clear()

        return self.get_subspace(uarray, indices, copy=True)

    def _linear_interpolation(self, ua, ub, d0, shape, first):
        """Interpolate linearly between pairs of tie points.
        
        This is the function ``fl()`` defined in CF appendix J:

        u = fl(ua, ub, s) = ua + s*(ub-ua)
                          = ua*(1-s) + ub*s

        .. versionadded:: (cfdm) 1.9.TODO.0
        
        :Parameters:

            ua, ub: array_like
               The arrays containing the points for pair-wise
               interpolation along dimension *d0*.
 
            d0: `int`
                The position of a subsampled dimension in the tie
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
        # Get the interpolation coefficents
        s, one_minus_s = self._s(d0, shape[d0])
 
        # Interpolate
        u = ua * one_minus_s + ub * s
 
        if not first[d0]:
            # Remove the first point of the interpolation subarea if
            # it is not the first (in index space) of a continuous
            # area. This is beacuse this value in the uncompressed
            # data has already been calculated from the previous (in
            # index space) interpolation subarea.
            indices = [slice(None)] * u.ndim
            indices[d0] = slice(1, None)
            u = u[tuple(indices)]
 
        return u
