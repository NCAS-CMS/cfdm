import numpy as np

from ...functions import integer_dtype
from .abstract import MeshSubarray


class CellConnectivitySubarray(MeshSubarray):
    """A cell connectivity subarray defined by UGRID connectivity.

    A subarray describes a unique part of the uncompressed array.

    A UGRID connectivity variable contains indices which map each cell
    to its neighbours, as found in a UGRID "face_face_connectivty"
    variable.

    .. versionadded:: (cfdm) UGRIDVER

    .. seealso:: `CellConnectivityArray`

    """

    def __getitem__(self, indices):
        """Return a subspace of the uncompressed data.

        x.__getitem__(indices) <==> x[indices]

        Returns a subspace of the uncompressed data as an independent
        numpy array.

        .. versionadded:: (cfdm) UGRIDVER

        """
        start_index = self.start_index
        shape = self.shape
        start = 0
        stop = shape[0]
        if start_index:
            start += 1
            stop += 1

        data = self._select_data(check_mask=True)
        if np.ma.isMA(data):
            empty = np.ma.empty
        else:
            empty = np.empty

        dtype = integer_dtype(stop - 1)
        u = empty(shape, dtype=dtype)

        # Store the cell identifiers in the first column
        u[:, 0] = np.arange(start, stop, dtype=dtype)
        # Store the identifiers of the connected cells in the other
        # columns
        u[:, 1:] = data

        if indices is not Ellipsis:
            u = u[indices]

        # Make sure that the values are zero-based
        if start_index:
            u -= 1

        return u
