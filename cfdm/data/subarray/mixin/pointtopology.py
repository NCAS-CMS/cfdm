import numpy as np


class PointTopology:
    """Mixin class for point topology array compressed by UGRID.

    Subclasses must also inherit from `MeshSubarray`.

    .. versionadded:: (cfdm) 1.11.0.0

    """

    def __getitem__(self, indices):
        """Return a subspace of the uncompressed data.

        x.__getitem__(indices) <==> x[indices]

        .. versionadded:: (cfdm) 1.11.0.0

        """
        from math import isnan

        from scipy.sparse import csr_array

        from cfdm.functions import integer_dtype

        start_index = self.start_index
        node_connectivity = self._select_data(check_mask=True)

        # ------------------------------------------------------------
        # E.g. For faces, 'node_connectivity' might be (two
        # quadrilaterals and one triangle):
        #
        #      [[3 4 2 1 ]
        #       [5 6 4 3 ]
        #       [7 2 4 --]]
        #
        # E.g. For the nine edges of the above faces,
        #      'node_connectivity' could be:
        #
        #      [[2 7]
        #       [4 7]
        #       [4 2]
        #       [1 2]
        #       [3 1]
        #       [3 4]
        #       [3 5]
        #       [6 5]
        #       [4 6]]
        # ------------------------------------------------------------

        masked = np.ma.isMA(node_connectivity)

        largest_node_id = node_connectivity.max()
        if not start_index:
            # Add 1 to remove all zeros (0 is the fill value in the
            # sparse array), first making sure that the datatpe can
            # handle it.
            if largest_node_id == np.iinfo(node_connectivity.dtype).max:
                node_connectivity = node_connectivity.astype(int, copy=False)

            node_connectivity = node_connectivity + 1
            largest_node_id = largest_node_id + 1

        p = 0
        pointers = [0]
        cols = []
        u = []

        pointers_append = pointers.append
        cols_extend = cols.extend
        u_extend = u.extend

        unique_nodes = np.unique(node_connectivity)
        if masked:
            # Remove the missing value from unique nodes
            unique_nodes = unique_nodes[:-1]

        unique_nodes = unique_nodes.tolist()

        # WARNING (TODO): This loop is a potential performance bottleneck.
        for node in unique_nodes:
            # Find the collection of all nodes that are joined to this
            # node via links in the mesh, including this node itself
            # (which will be at the start of the list).
            nodes = self._connected_nodes(node, node_connectivity, masked)

            n_nodes = len(nodes)
            p += n_nodes
            pointers_append(p)
            cols_extend(range(n_nodes))
            u_extend(nodes)

        del unique_nodes

        u = np.array(u, dtype=integer_dtype(largest_node_id))
        u = csr_array((u, cols, pointers))
        u = u.toarray()
        if any(map(isnan, self.shape)):
            # Store the shape, now that is it known.
            self._set_component("shape", u.shape, copy=False)

        if indices is not Ellipsis:
            u = u[indices]

        # Mask all zeros
        u = np.ma.where(u == 0, np.ma.masked, u)

        # ------------------------------------------------------------
        # E.g. For either of the face and edge examples above, 'u'
        #      would now be:
        #
        #      [[1 2 3 -- --]
        #       [2 1 4  7 --]
        #       [3 1 4  5 --]
        #       [4 2 3  6  7]
        #       [5 3 6 -- --]
        #       [6 4 5 -- --]
        #       [7 2 4 -- --]]
        #
        # ------------------------------------------------------------

        if not start_index:
            # Subtract 1 to get back to zero-based node identities
            u -= 1

        return u
