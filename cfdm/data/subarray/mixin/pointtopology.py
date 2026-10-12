import numpy as np


class PointTopology:
    """Mixin class for point topology array compressed by UGRID.

    Subclasses must also inherit from `MeshSubarray`.

    .. versionadded:: (cfdm) 1.11.0.0

    """

    @staticmethod
    def _point_point_connectivity(src_neighbours, dst_neighbours):
        """Worker method for `__getitem__`.

        Returns the full point-point connectivity array derived from
        an edge-node or face-node connectivity array.

        :Parameters:

            src_neighbours: `numpy.ndarray`
                A flattened array of the node indices for both ends of
                each edge of the parent cells. The 1-d array will have
                the same number of elements as the *node_connectivity*
                array (which is defined in the calling `__getitem__`
                method).

                When the *node_connectivity* array contains missing
                values (represented by `-1`), these are treated in
                *src_neighbours* as if they were edge node indices.

                E.g. If the parent cells comprise 9 edges then
                     *src_neighbours* will have 2 * 9 = 18 elements.

                E.g. If the parent cells comprise 3 faces (2 squares
                     and one triangle) then *src_neighbours* will have
                     2 * (3 * 4) = 24 elements.

            dst_neighbours: `numpy.ndarray`
                Similar to *src_neighbours*. The indices at position N
                in both arrays define the two nodes at either end of
                the same edge.

                However, when the *node_connectivity* array contains
                missing values (represented by `-1`) then to ensure
                that every edge is represented by two real node
                indices at least one position N in the
                *src_neighbours* and *dst_neighbours* arrays,
                erstwhile `-1` values in *dst_neighbours* will have to
                be replaced with real node indices.

        :Returns:

            `numpy.ndarray`
                The point-point connectivity array.

        .. versionadded:: (cfdm) 1.13.3.0

        """
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
        #
        # src_neighbours = [1 6 3 6 3 1 0 1 2 0 2 3 2 4 5 4 3 5]
        # dst_neighbours = [6 1 6 3 1 3 1 0 0 2 3 2 4 2 4 5 5 3]
        # ------------------------------------------------------------

        # ------------------------------------------------------------
        # E.g. Two quadrilaterals and one triangle:
        #
        # node_connectivity = [[2 3 1 0]
        #                      [4 5 3 2]
        #                      [6 1 3 --]]
        #
        # src_neighbours = [2 3 1 0 4 5 3 2 6 1 3 -1 2 3 1 0 4 5 3 2  6 1 3 -1]
        # dst_neighbours = [3 1 0 2 5 3 2 4 1 3 6  6 0 2 3 1 2 4 5 3 -1 6 1  3]
        # ------------------------------------------------------------

        from cfdm.functions import integer_dtype

        # ------------------------------------------------------------
        # Remove bad edges
        # ------------------------------------------------------------
        valid = (
            (src_neighbours >= 0)
            & (dst_neighbours >= 0)
            & (src_neighbours != dst_neighbours)
        )
        src_neighbours = src_neighbours[valid]
        dst_neighbours = dst_neighbours[valid]
        del valid

        # ------------------------------------------------------------
        # De-duplication of edges
        # ------------------------------------------------------------
        n_edges = len(src_neighbours)
        edges = np.empty((n_edges, 2), dtype=src_neighbours.dtype)
        edges[:, 0] = src_neighbours
        edges[:, 1] = dst_neighbours

        unique_edges = np.unique(edges, axis=0)
        del edges

        src_uniq = unique_edges[:, 0]
        dst_uniq = unique_edges[:, 1]
        all_nodes = np.unique(unique_edges)
        del unique_edges

        # ------------------------------------------------------------
        # Fast lexicographical sort (src_node primary, dst_node
        # secondary)
        # ------------------------------------------------------------
        sort_idx = np.lexsort((dst_uniq, src_uniq))
        src_sorted = src_uniq[sort_idx]
        dst_sorted = dst_uniq[sort_idx]
        del src_uniq, dst_uniq, sort_idx

        # ------------------------------------------------------------
        # Group boundaries and node offsets: Calculate neighbour
        # counts per unique src_node
        # ------------------------------------------------------------
        uniq_src_nodes, src_start_idx, neighbour_counts = np.unique(
            src_sorted, return_index=True, return_counts=True
        )

        # ------------------------------------------------------------
        # Initialise the output matrix, 'u', filled with -1
        # ------------------------------------------------------------
        num_unique_nodes = len(all_nodes)
        max_degree = neighbour_counts.max() + 1
        largest_node_id = all_nodes[-1]  # all_nodes is sorted from np.unique
        dtype = integer_dtype(largest_node_id)
        u = np.full((num_unique_nodes, max_degree), -1, dtype=dtype)

        # Place the self-node at column 0 of every row
        u[:, 0] = all_nodes

        # Build the column indices for neighbours (columns
        # 1..K).
        cols_offset = (
            np.arange(len(src_sorted))
            - np.repeat(src_start_idx, neighbour_counts)
            + 1
        )
        del src_sorted, src_start_idx

        # Find which rows in 'u' correspond to nodes that actually
        # have neighbours
        node_to_row = np.searchsorted(all_nodes, uniq_src_nodes)
        del all_nodes, uniq_src_nodes
        rows_offset = np.repeat(node_to_row, neighbour_counts)
        del node_to_row, neighbour_counts

        # Insert neighbour IDs directly into 'u'
        u[rows_offset, cols_offset] = dst_sorted
        del rows_offset, cols_offset, dst_sorted

        # ------------------------------------------------------------
        # Both of the examples above give a point-point connectivity
        # array of:
        #
        # u = [[ 0  1  2 -1 -1]
        #      [ 1  0  3  6 -1]
        #      [ 2  0  3  4 -1]
        #      [ 3  1  2  5  6]
        #      [ 4  2  5 -1 -1]
        #      [ 5  3  4 -1 -1]
        #      [ 6  1  3 -1 -1]]
        # ------------------------------------------------------------
        return u
