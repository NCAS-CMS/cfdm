import numpy as np

from ....functions import integer_dtype


class PointTopology:
    """Mixin class for point topology array compressed by UGRID.

    Subclasses must also inherit from `MeshSubarray`.

    .. versionadded:: (cfdm) UGRIDVER

    """

    def __getitem__(self, indices):
        """Return a subspace of the uncompressed data.

        x.__getitem__(indices) <==> x[indices]

        .. versionadded:: (cfdm) UGRIDVER

        """
        from math import isnan

        from scipy.sparse import csr_array

        start_index = self.start_index
        node_connectivity = self._select_data(check_mask=False)

        masked = np.ma.isMA(node_connectivity)

        largest_node_id = node_connectivity.max()
        if not start_index:
            # Add 1 to remove all zeros (0 is the fill value in the
            # sparse array), first making sure that the datatpe can
            # handle it.
            if largest_node_id == np.iinfo(node_connectivity.dtype).max:
                node_connectivity = node_connectivity.astype(int, copy=False)

            node_connectivity = node_connectivity + 1
            largest_node_id += 1

        p = 0
        pointers = [0]
        cols = []
        u = []

        pointers_append = pointers.append
        cols_extend = cols.extend
        u_extend = u.extend

        # WARNING: This loop is a potential performance bottleneck
        for node in np.unique(node_connectivity).tolist():
            # Find the collection of all nodes that are joined to this
            # node via links in the mesh, including this node itself
            # (which will be at the start of the list).
            nodes = self._connected_nodes(node, node_connectivity, masked)

            n_nodes = len(nodes)
            p += n_nodes
            pointers_append(p)
            cols_extend(range(n_nodes))
            u_extend(nodes)

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

        if not start_index:
            # Subtract 1 to get back to zero-based node identities
            u -= 1

        return u
