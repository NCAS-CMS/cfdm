from functools import reduce
from operator import mul

import numpy as np

from ....abstract import Container


class Subarray(Container):
    """TODO

    .. versionadded:: (cfdm) 1.9.TODO.0

    """

    def __init__(
        self,
        data=None,
        indices=None,
        shape=None,
        compressed_dimensions=None,
    ):
        """**Initialisation**

        :Parameters:

            data: array_like
                The full compressed array for all subarareas. The
                applicable elements are defined by the *indices*
                parameter.

            indices: `tuple`
                For each dimension of the *data* array, the index that
                defines the location the elements needed to uncompress
                this subrarea.

            shape: `tuple` of `int`
                The shape of the uncompressed array.

            compressed_dimensions: sequence of `int`
                The positions of the compressed dimensions in the
                *data* array.

        """
        super().__init__()

        self.data = data
        self.indices = indices
        self.shape = shape
        self.compressed_dimensions = compressed_dimensions

    def __getitem__(self, indices):
        """Return a subspace of the uncompressed data.

        x.__getitem__(indices) <==> x[indices]

        Returns a subspace of the uncompressed array as an independent
        numpy array.

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        raise NotImplementedError("Must implement __getitem__ in subclasses")

    def _post_process(self, u):
        """TODO

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Parameters:

            u: `numpy.ndarray`
               TODO

        :Returns:

            `numpy.ndarray`

        """
        raise NotImplementedError("Must implement _post_process in subclasses")

    def _select_data(self, data=None):
        """Select TODO subarea

        .. versionadded:: (cfdm) 1.9.TODO.0

        :Parameters:

            data: array_like or `None`
                The full compressed array. If `None` then the `data`
                array is used.

        :Returns:

            `numpy.ndarray`
                The selected values.

        """
        if data is None:
            data = self.data

        return np.asanyarray(data[self.indices])

    @property
    def dtype(self):
        """The data-type of the uncompressed data.

        .. versionadded:: (cfdm) 1.9.TODO.0

        """
        raise NotImplementedError("Must implement dtype in subclasses")

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
