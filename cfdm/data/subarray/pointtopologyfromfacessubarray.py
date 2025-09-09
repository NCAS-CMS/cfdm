import numpy as np

from .abstract import MeshSubarray
from .mixin import PointTopology


class PointTopologyFromFacesSubarray(PointTopology, MeshSubarray):
    """A subarray of a point topology array compressed by UGRID faces.

    A subarray describes a unique part of the uncompressed array.

    .. versionadded:: (cfdm) 1.11.0.0

    """

    @classmethod
    def _connected_nodes(self, node, node_connectivity, masked, edges=False):
        """Return nodes that are joined to *node* by face edges.

        The input *node* is included at the start of the returned
        list.

        .. versionadded:: (cfdm) 1.11.0.0

        :Parameters:

            node: `int`
                A node identifier.

            node_connectivity: `numpy.ndarray`
                A UGRID "face_node_connectivity" array.

            masked: `bool`
                Whether or not *node_connectivity* has masked
                elements.

            edges: `bool`, optional
                By default *edges* is False and a flat list of nodes,
                including *node* itself at the start, is returned. If
                True then a list of edge definitions (i.e. a list of
                sorted, hashable tuple pairs of nodes) is returned
                instead.

                .. versionadded:: (cfdm) NEXTVERSION

        :Returns:

            `list`
                All nodes that are joined to *node*, including *node*
                itself at the start.


        **Examples**

        >>> p._connected_nodes(7, nc)
        [7, 2, 1, 9]
        >>> p._connected_nodes(2, nc)
        [2, 8, 7]

        >>> p._connected_nodes(7, nc, edges=True)
        [(2, 7), (1, 7), (7, 9)]
        >>> p._connected_nodes(2, nc, edges=True)
        [(2, 8), (2, 7)]

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
            else:
                face_nodes = face_nodes.flatten()

            face_nodes = face_nodes.tolist()

            # Find the position of 'node' in the face, and get it's
            # neighbours.
            index = face_nodes.index(node)
            if not index:
                # 'node' is in position 0
                nodes_extend((face_nodes[-1], face_nodes[1]))
            elif index == len(face_nodes) - 1:
                # 'node' is in position -1
                nodes_extend((face_nodes[-2], face_nodes[0]))
            else:
                # 'node' is in any other position
                nodes_extend((face_nodes[index - 1], face_nodes[index + 1]))

        nodes = list(set(nodes))

        if edges:
            # Return a list of ordered edge definitions
            nodes = [(node, n) if node < n else (n, node) for n in nodes]
        else:
            # Return a flat list of nodes, including 'node' at the
            # start.
            nodes.insert(0, node)

        return nodes
