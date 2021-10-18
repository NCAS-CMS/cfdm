from functools import lru_cache
from itertools import product

import numpy as np

from .abstract import CompressedArray
from .mixin import SubsampledArray


class SubsampledGeneralArray(SubsampledArray, CompressedArray):
    """TODO.

    **Cell boundaries**

    If the subsampled array contains cell boundaries, then the
    *shape*, *ndim* and *size* parameters that describe the
    uncompressed array will include the required trailing size 2
    dimension.

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
            interpolation_name=interpolation_name,
            interpolation_description=interpolation_description,
            computational_precision=computational_precision,
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
