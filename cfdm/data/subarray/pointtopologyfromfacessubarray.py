import numpy as np

from .abstract import MeshSubarray
from .mixin import PointTopology


class PointTopologyFromFacesSubarray(PointTopology, MeshSubarray):
    """A subarray of an point topology array compressed by UGRID faces.

    A subarray describes a unique part of the uncompressed array.

    .. versionadded:: (cfdm) UGRIDVER

    """

    def _connected_nodes(self, node, node_connectivity, masked):
        """Return nodes that are joined to *node* by face edges.

        The input *node* is included at the start of the returned
        list.

        .. versionadded:: (cfdm) UGRIDVER

        :Parameters:

            node: `int`
                A node identifier.

            node_connectivity: `numpy.ndarray`
                A UGRID "face_node_connectivity" array.

            masked: `bool`
                Whether or not *node_connectivity* has masked
                elements.

        :Returns:

            `list`
                All nodes that are joined to *node*, including *node*
                itself at the start.

        """
        if masked:
            where = np.ma.where
        else:
            where = np.where

        # Find the faces that contain this node:
        faces = where(node_connectivity == node)[0]

        nodes = []
        nodes_extend = nodes.extend

        # For each face, find which two of its nodes are neighbours to
        # 'node'.
        for face_nodes in node_connectivity[faces]:
            if masked:
                face_nodes = face_nodes.compressed()

            face_nodes = face_nodes.tolist()
            face_nodes.append(face_nodes[0])
            nodes_extend(
                [
                    m
                    for m, n in zip(face_nodes[:-1], face_nodes[1:])
                    if n == node
                ]
            )

        nodes = list(set(nodes))

        # Insert 'node' at the front of the list
        nodes.insert(0, node)

        return nodes
