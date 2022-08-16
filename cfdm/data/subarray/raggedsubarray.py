import numpy as np

from .abstract import Subarray


class RaggedSubarray(Subarray):
    """A subarray of a compressed ragged array.

    A subarray describes a unique part of the uncompressed array.

    See CF section 9 "Discrete Sampling Geometries".

    .. versionadded:: (cfdm) 1.10.0.0

    """

    def __getitem__(self, indices):
        """Return a subspace of the uncompressed subarray.

        x.__getitem__(indices) <==> x[indices]

        Returns a subspace of the uncompressed subarray as an
        independent numpy array.

        .. versionadded:: (cfdm) 1.10.0.0

        """
        d1, u_dims = self.compressed_dimensions().popitem()
        uncompressed_shape = self.shape

        data = self._select_data(check_mask=False)

        if data.size:
            shape = list(data.shape)
            u_indices0 = [slice(None)] * data.ndim

            u_indices0[d1] = slice(0, shape[d1])
            shape[d1] = uncompressed_shape[u_dims[-1]]

            u = np.ma.masked_all(shape, dtype=self.dtype)

            u[tuple(u_indices0)] = data

            u = u.reshape(uncompressed_shape)
        else:
            # This subarray contains no elements of the compressed
            # data
            u = np.ma.masked_all(uncompressed_shape, dtype=self.dtype)

        if indices is Ellipsis:
            return u

        return u[indices]

    @property
    def dtype(self):
        """The data-type of the uncompressed data.

        .. versionadded:: (cfdm) 1.10.0.0

        """
        return self.data.dtype
