import numpy as np

from .abstract import MeshSubarray
from .mixin import PointTopology


class PointTopologyFromEdgesSubarray(PointTopology, MeshSubarray):
    """A subarray of a point topology array compressed by UGRID edges.

    A subarray describes a unique part of the uncompressed array.

    .. versionadded:: (cfdm) 1.11.0.0

    """

    def __getitem__(self, indices):
        """Return a subspace of the uncompressed data."""
        from math import isnan

        # ------------------------------------------------------------
        # E.g. Nine edges:
        #
        # node_connectivity = [[1 6]
        #                      [3 6]
        #                      [3 1]
        #                      [0 1]
        #                      [2 0]
        #                      [2 3]
        #                      [2 4]
        #                      [5 4]
        #                      [3 5]]
        # ------------------------------------------------------------
        node_connectivity = self._select_data(check_mask=True)

        # Construct bi-directional edge pairs (n1 -> n2 and n2 -> n1)
        src_neighbours = node_connectivity.ravel()
        dst_neighbours = node_connectivity[:, ::-1].ravel()
        del node_connectivity

        # ------------------------------------------------------------
        # src_neighbours = [1 6 3 6 3 1 0 1 2 0 2 3 2 4 5 4 3 5]
        # dst_neighbours = [6 1 6 3 1 3 1 0 0 2 3 2 4 2 4 5 5 3]
        # ------------------------------------------------------------

        # Create the full point_point_connectivity matrix (padded with -1)
        u = self._point_point_connectivity(src_neighbours, dst_neighbours)
        del src_neighbours, dst_neighbours

        if any(map(isnan, self.shape)):
            # Store the shape, now that it is known.
            self._set_component("shape", u.shape, copy=False)

        # Subspace the full point connectivity matrix
        if indices is not Ellipsis:
            u = u[indices]

        # Mask padding values in-place (-1)
        u = np.ma.masked_equal(u, -1, copy=False)

        # ------------------------------------------------------------
        # u = [[0 1 2 -- --]
        #      [1 0 3 6 --]
        #      [2 0 3 4 --]
        #      [3 1 2 5 6]
        #      [4 2 5 -- --]
        #      [5 3 4 -- --]
        #      [6 1 3 -- --]]
        # ------------------------------------------------------------
        return u
