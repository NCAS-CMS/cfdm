from functools import lru_cache
from itertools import product

import numpy as np

from .abstract import CompressedArray
from .mixin import SubsampledArray


class SubsampledGeneralArray(SubsampledArray, CompressedArray):
    """TODO.

    .. versionadded:: (cfdm) 1.9.TODO.0

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
        interpolation_parameters={},
        parameter_dimensions={},
        interpolation_name=None,
        interpolation_description=None,
        computational_precision=None,
        bounds=False,
        interpolation_variable=None,
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
                dimension. An integer key indentifies a subsampled
                dimensions by its position in the tie points array,
                and the value is a `TiePointIndex` variable.

            interpolation_parameters: `dict`
                TODO

            parameter_dimensions: `dict`
                TODO

            computational_precision: `str`, optional
                The floating-point arithmetic precision used during
                the preparation and validation of the compressed
                coordinates.

                *Parameter example:*
                  ``computational_precision='64'``

            bounds: `bool`, optional
                If True then the tie points represent coordinate
                bounds. In this case the uncompressed data has an
                extra trailing dimension in addition to the tie point
                dimensions. See CF section 8.3.9 "Interpolation of
                Cell Boundaries".

             interpolation_variable: `Interpolation`

        """
        super().__init__(
            compressed_array=compressed_array,
            shape=shape,
            size=size,
            ndim=ndim,
            compressed_dimension=tuple(sorted(compressed_axes)),
            compression_type="subsampled",
            tie_point_indices=tie_point_indices.copy(),
            interpolation_parameters=interpolation_parameters.copy(),
            parameter_dimensions=parameter_dimensions.copy(),
            #            interpolation_name=interpolation_name,
            #            interpolation_description=interpolation_description,
            #            computational_precision=computational_precision,
            #            bounds=bounds,
            interpolation_variable=interpolation_variable,
        )

        if dtype is None:
            dtype = self._default_dtype

        self.dtype = dtype

    def __getitem__(self, indices):
        """x.__getitem__(indices) <==> x[indices]

        Returns a subspace of the array as an independent numpy array.

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        # If exactly the first or last element is requested then we
        # don't need to interpolate
        try:
            return self._first_or_last_index(indices)
        except IndexError:
            raise IndexError("Don't know how to uncompress {self!r}")
