from functools import reduce
from operator import mul

import numpy as np

from ....abstract import Container


class Subarray(Container):
    """Abstract base class for a subarray of compressed array.

    Each subarray of the compressed array describes a unique part of
    the uncompressed array defined by the *indices* parameter.

    When an instance is indexed, the subarray is first uncompressed
    into a `numpy.ndarray` whose shape is given by the *shape*
    parameter, which is the indexed as requested.

    The decompression method must be defined in subclasses by
    overriding the `__getitem__` method.

    .. versionadded:: (cfdm) 1.9.TODO.0

    """

    def __init__(
        self,
        data=None,
        indices=None,
        shape=None,
        compressed_dimensions={},
    ):
        """**Initialisation**

        :Parameters:

            data: array_like
                The full compressed array spanning all subarrays, from
                which the elements for this subarray are defined by
                the *indices* indices.

            indices: `tuple`
                For each dimension of the *data* array, the index that
                defines the elements needed to uncompress this
                subarray

            shape: `tuple` of `int`
                The shape of the uncompressed array.

            compressed_dimensions: `dict`
                Mapping of compressed to uncompressed dimensions.

                A dictionary key is a position of a dimension in the
                compressed data, with a value of the positions of the
                corresponding dimensions in the uncompressed
                data. Compressed array dimensions that are not
                compressed must be omitted from the mapping.

                *Parameter example:*
                  ``{0: (0, 1)}``

                *Parameter example:*
                  ``{0: (0, 1, 2)}``

                *Parameter example:*
                  ``{2: (2, 3)}``

                *Parameter example:*
                  ``{1: (1,)}``

                *Parameter example:*
                  ``{0: (0,), 2: (2,)}``

        """
        super().__init__()

        self.data = data
        self.indices = indices
        self.shape = shape
        self.compressed_dimensions = compressed_dimensions.copy()

    def __getitem__(self, indices):
        """Return a subspace of the uncompressed data.

        x.__getitem__(indices) <==> x[indices]

        Returns a subspace of the uncompressed subarray as an
        independent numpy array.

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        raise NotImplementedError(
            "Must implement __getitem__ in subclasses"
        )  # pragma: no cover

    def _select_data(self, data=None):
        """Select compressed array elements that correspond to this subarray.

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Parameters:

            data: array_like or `None`
                A full compressed array spanning all subarrays, from
                which the elements for this subarray will be
                returned. By default, or if `None` then the `data`
                array is used.

        :Returns:

            `numpy.ndarray`
                Values of the compressed array that correspond to this
                subarray.

        """
        if data is None:
            data = self.data

        return np.asanyarray(data[self.indices])

    @property
    def dtype(self):
        """The data-type of the uncompressed data.

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        raise NotImplementedError(
            "Must implement dtype in subclasses"
        )  # pragma: no cover

    @property
    def ndim(self):
        """The number of dimensions of the uncompressed data.

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        return len(self.shape)

    @property
    def size(self):
        """The size of the uncompressed data.

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        return reduce(mul, self.shape, 1)
