import numpy as np

from . import SampledLinearArray


class SampledBiLinearArray(SampledLinearArray):
    """TODO.

    .. versionadded:: (cfdm) TODO

    """

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

        .. versionadded:: (cfdm) TODO

        """
        # ------------------------------------------------------------
        # Method: Uncompress the entire array and then subspace it
        # ------------------------------------------------------------
        d0, d1 = self.get_source_compressed_axes()

        tie_points = self.get_tie_points()

        # Initialise the un-sliced uncompressed array
        uarray = np.ma.masked_all(self.shape, dtype=float)

        for tp_indices, u_indices, new_area in zip(
            *self._interpolation_zones()
        ):

            index = list(tp_indices)
            index[d1] = tp_index[d1][:1]

            index0 = list(tp_indices)
            index0[d1] = tp_index[d1][:1]
            index0[d0] = tp_index[d0][:1]

            index1 = index0[:]
            index1[d0] = tp_index[d0][1:]

            u_slice = u_indices[d0]
            new_area = new_area[d0]

            x = self._linear_interpolation(
                d0,
                u_slice,
                new_area,
                tie_points[tuple(index0)].array,
                tie_points[tuple(index1)].array,
            )

            index0[d1] = tp_index[d1][1:]
            index1[d1] = index0[d1]

            y = self._linear_interpolation(
                d0,
                u_slice,
                new_area,
                tie_points[tuple(index0)].array,
                tie_points[tuple(index1)].array,
            )

            uarray[u_indices] = self._linear_interpolation(
                d1, u_indices[d1], new_area[d1], x, y
            )

        self._calculate_s.cache_clear()

        return self.get_subspace(uarray, indices, copy=True)

    # ----------------------------------------------------------------
    # Attributes
    # ----------------------------------------------------------------
    @property
    def interpolation(self):
        """The description of the interpolation method."""
        return "bi_linear"
