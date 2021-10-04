import numpy as np

from .abstract import Subsampledrray


class SampledLinearArray(Subsampledrray):
    """TODO.

    .. versionadded:: (cfdm) 1.9.TODO.0

    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_component("interpolation_name", "linear", copy=False)
        
    def __getitem__(self, indices):
        """x.__getitem__(indices) <==> x[indices]

        Returns a subspace of the array as an independent numpy array.

        The indices that define the subspace must be either `Ellipsis`
        or a sequence that contains an index for each dimension. In
        the latter case, each dimension's index must either be a
        `slice` object or a sequence of two or more integers.

        Indexing is similar to numpy indexing. The only difference to
        numpy indexing (given the restrictions on the type of indices
        allowed) is:

          * When two or more dimension's indices are sequences of
            integers then these indices work independently along each
            dimension (similar to the way vector subscripts work in
            Fortran).

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        super().__getitem__(indices)

        # ------------------------------------------------------------
        # Method: Uncompress the entire array and then subspace it
        # ------------------------------------------------------------
        (d0,) = self.get_source_compressed_axes()

        tie_points = self.get_tie_points()

        # Initialise the un-sliced uncompressed array
        uarray = np.ma.masked_all(self.shape, dtype=float)

        # Interpolate the tie points according to by CF appendix J
        for tp_indices, u_indices, new_area in zip(
            *self._interpolation_subareas()
        ):
            tp_index0 = list(tp_indices)
            tp_index1 = tp_index0[:]
            tp_index0[d0] = tp_index0[d0][:1]
            tp_index1[d0] = tp_index1[d0][1:]

            s, one_minus_s = self._calculate_s(d, u_slice.stop - u_slice.start)

            a0 = tie_points[tuple(tp_index0)].array
            a1 = tie_points[tuple(tp_index1)].array

            u = a0 * one_minus_s + a1 * s
            
            if not new_area:
                # Remove the first point of an interpolation subarea
                # if it is not the first (in index space) of a new
                # continuous area. This is beacuse this value in the
                # uncompressed data has already been calculated from
                # the previous (in index space) interpolation subarea.
                indices = [slice(None)] * u.ndim
                indices[d] = slice(1, None)
                u = u[tuple(indices)]
                
            uarray[u_indices] = u
            #self._linear_interpolation(
             #   d0,
             #   u_indices[d0],
             #   new_area[d0],
             #   tie_points[tuple(tp_index0)].array,
             #   tie_points[tuple(tp_index1)].array,
            #)

        self._calculate_s.cache_clear()

        return self.get_subspace(uarray, indices, copy=True)

#   def _linear_interpolation(self, d, u_slice, new_area, a0, a1):
#       """Uncompress an interpolation subarea
#
#       .. versionadded:: (cfdm) 1.9.TODO.0
#
#       :Parameters:
#
#           d: `int`
#               The position of a subsampled dimension in the tie
#               point array.
#
#           u_slice: `slice`
#
#           new_area: `bool`
#               True if the interpolation subarea is the first (in
#               index space) of a new continuous area, otherwise
#               False.
#
#           a0, a1: array_like
#              The arrays containing the points for pair-wise
#              interpolation along dimension *d*.
#
#       :Returns:
#
#           `numpy` array
#
#       """
#       s, one_minus_s = self._calculate_s(d, u_slice.stop - u_slice.start)
#
#       u = a0 * one_minus_s + a1 * s
#
#       if not new_area:
#           # Remove the first point of an interpolation subarea if it
#           # is not the first (in index space) of a new continuous
#           # area. This is beacuse this value in the uncompressed
#           # data has already been calculated from the previous
#           # interpolation subarea.
#           indices = [slice(None)] * u.ndim
#           indices[d] = slice(1, None)
#           u = u[tuple(indices)]
#
#       return u
