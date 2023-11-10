import numpy as np

from .abstract import MeshSubarray
from .mixin import PointTopology


class PointTopologyFromEdgesSubarray(PointTopology, MeshSubarray):
    """A subarray of an point topology array compressed by UGRID edges.

    A subarray describes a unique part of the uncompressed array.

    .. versionadded:: (cfdm) UGRIDVER

    """

    def _connected_nodes(self, node, node_connectivity, masked):
        """Return the nodes that are joined to *node* by edges.

        The input *node* is included at the start of the returned
        list.

        .. versionadded:: (cfdm) UGRIDVER

        :Parameters:

            node: `int`
                A node identifier.

            node_connectivity: `numpy.ndarray`
                A UGRID "edge_node_connectivity" array.

            masked: `bool`, optional
                Whether or not *node_connectivity* has masked
                elements.

        :Returns:

            `list`
                All nodes that are joined to *node*, including *node*
                itself at the start.

        """
        nodes = sorted(
            set(
                node_connectivity[np.where(node_connectivity == node)[0]]
                .flatten()
                .tolist()
            )
        )

        # Move 'node' to the front of the list
        nodes.remove(node)
        nodes.insert(0, node)

        return nodes
