import numpy as np

from .sampledlineararray import SampledLinearArray


class SampledBiLinearArray(SampledLinearArray):
    """TODO.

    .. versionadded:: (cfdm) TODO

    """

    def __init__(self, 
        compressed_array=None,
        shape=None,
        size=None,
        ndim=None,
        compressed_axes=None,
        tie_point_indices={},
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
            interpolation_name="bilinear"
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

        for tp_indices, u_indices, subarea_size, new_area in zip(
            *self.interpolation_subareas()
        ):
            index = list(tp_indices)
            index[d1] = tp_index[d1][:1]

            index0 = list(tp_indices)
            index0[d1] = tp_index[d1][:1]
            index0[d0] = tp_index[d0][:1]

            index1 = index0[:]
            index1[d0] = tp_index[d0][1:]
            ua =  tie_points[tuple(index0)].array
            uc = tie_points[tuple(index1)].array
            
            uac = self._linear_interpolation(
                ua,
                uc,
                d0,
                subarea_size[d0],
                new_area[d0],
            )

            index0[d1] = tp_index[d1][1:]
            index1[d1] = index0[d1]
            ub = tie_points[tuple(index0)].array
            ud = tie_points[tuple(index1)].array
            
            ubd = self._linear_interpolation(
                ub,
                ud,
                d0,
                subarea_size[d0],
                new_area[d0],
            )

            uarray[u_indices] = self._linear_interpolation(
                uac,
                ubd,
                d1,
                subarea_size[d1],
                new_area[d1],
            )

        self._s.cache_clear()

        return self.get_subspace(uarray, indices, copy=True)
