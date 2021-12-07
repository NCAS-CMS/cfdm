from .abstract import CompressedArray
from .mixin import Subsampled


class SubsampledGeneralArray(Subsampled, CompressedArray):
    """A subsampled array with non-standardised interpolation.

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
        instance._Subarray = None
        return instance

    def __init__(
        self,
        compressed_array=None,
        shape=None,
        size=None,
        ndim=None,
        interpolation_name=None,
        interpolation_description=None,
        computational_precision=None,
        tie_point_indices={},
        parameters={},
        parameter_dimensions={},
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
                The positions of the subsampled dimensions in the tie
                points array.

                *Parameter example:*
                  ``compressed_axes=[1]``

                *Parameter example:*
                  ``compressed_axes=(1, 2)``

            interpolation_name: `str`, optional
                The interpolation method used to uncompress the
                coordinates values.

                *Parameter example:*
                  ``interpolation_name='linear'``

            interpolation_description: `str`, optional
                A non-standardized description of the interpolation
                method used to uncompress the coordinates values.

            tie_point_indices: `dict`
                The tie point index variable for each subsampled
                dimension. A key indentifies a subsampled dimension by
                its integer position in the compressed array, and its
                value is a `TiePointIndex` variable.

                *Parameter example:*
                  ``tie_point_indices={1: cfdm.TiePointIndex(data=[0, 16])}``

            parameters: `dict`
                TODO

            parameter_dimensions: `dict`
                TODO

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
            tie_point_indices=tie_point_indices.copy(),
            parameters=parameters.copy(),
            parameter_dimensions=parameter_dimensions.copy(),
            interpolation_description=interpolation_description,
            computational_precision=computational_precision,
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
#        # If exactly the first or last element is requested then we
#        # don't need to interpolate
#        try:
#            return self._first_or_last_index(indices)
#        except IndexError:
#            raise IndexError(
#                "Can't subspace subsampled data with a non-standardised "
#                "interpolation method"
#            )
