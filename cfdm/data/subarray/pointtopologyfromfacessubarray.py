import numpy as np

from .abstract import MeshSubarray
from .mixin import PointTopology


class PointTopologyFromFacesSubarray(PointTopology, MeshSubarray):
    """A subarray of a point topology array compressed by UGRID faces.

    A subarray describes a unique part of the uncompressed array.

    .. versionadded:: (cfdm) 1.11.0.0

    """

    def __getitem__(self, indices):
        """Return a subspace of the uncompressed data."""
        from math import isnan

        # ------------------------------------------------------------
        # E.g. Two quadrilaterals and one triangle:
        #
        # node_connectivity = [[2 3 1 0]
        #                      [4 5 3 2]
        #                      [6 1 3 --]]
        # ------------------------------------------------------------
        node_connectivity = self._select_data(check_mask=True)
        is_masked = np.ma.is_masked(node_connectivity)

        if not is_masked:
            # No masked elements in 'node_connectivity'
            nc_ravel = node_connectivity.ravel()
            src_neighbours = np.tile(nc_ravel, 2)
            del nc_ravel

            # Left roll: [1, 2, ..., N, 0]
            # Right roll: [N, 0, 1, ..., N-1]
            cols = node_connectivity.shape[1]
            left_idx = np.arange(cols)
            right_idx = np.roll(left_idx, 1)
            left_idx = np.roll(left_idx, -1)

            left = node_connectivity[:, left_idx].ravel()
            right = node_connectivity[:, right_idx].ravel()
            del node_connectivity, left_idx, right_idx

            dst_neighbours = np.concatenate([left, right])
            del left, right

        else:
            # Masked elements in 'node_connectivity'
            node_connectivity = node_connectivity.filled(-1)
            cols = node_connectivity.shape[1]

            # Shift columns left (right neighbours) & right (left
            # neighbours)
            v_right = np.empty_like(node_connectivity)
            v_right[:, :-1] = node_connectivity[:, 1:]
            v_right[:, -1] = node_connectivity[:, 0]

            # Repair wrapped -1 entries in right neighbours back to
            # col 0
            masked_right = v_right == -1
            if np.any(masked_right):
                col_0 = node_connectivity[:, 0]
                # Broadcast col_0 across rows where right neighbour is
                # missing
                v_right = np.where(masked_right, col_0[:, None], v_right)
                del col_0

            del masked_right

            v_left = np.empty_like(node_connectivity)
            v_left[:, 1:] = node_connectivity[:, :-1]
            v_left[:, 0] = node_connectivity[:, -1]

            # Flatten and build src/dst pairs directly
            u_col = node_connectivity.ravel()
            del node_connectivity

            v_r_flat = v_right.ravel()
            del v_right
            v_l_flat = v_left.ravel()
            del v_left

            # Concatenate twice for forward and backward directions
            src_neighbours = np.tile(u_col, 2)
            del u_col

            dst_neighbours = np.concatenate([v_r_flat, v_l_flat])
            del v_r_flat, v_l_flat

        # ------------------------------------------------------------
        # src_neighbours = [2 3 1 0 4 5 3 2 6 1 3 -1 2 3 1 0 4 5 3 2  6 1 3 -1]
        # dst_neighbours = [3 1 0 2 5 3 2 4 1 3 6  6 0 2 3 1 2 4 5 3 -1 6 1  3]
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
