from .abstract import MeshArray
from .subarray import (
    PointTopologyFromEdgesSubarray,
    PointTopologyFromFacesSubarray,
)


class PointTopologyArray(MeshArray):
    """A point cell domain topology array derived from a UGRID variable.

    A point cell domain topology array derived from an underlying
    UGRID "edge_node_connectivity" or UGRID "face_node_connectivity"
    array.

    .. versionadded:: (cfdm) UGRIDVER

    """

    def __new__(cls, *args, **kwargs):
        """Store subarray classes.

        If a child class requires different subarray classes than the
        ones defined here, then they must be defined in the __new__
        method of the child class.

        .. versionadded:: (cfdm) UGRIDVER

        """
        instance = super().__new__(cls)
        instance._Subarray = {
            "point topology from edges": PointTopologyFromEdgesSubarray,
            "point topology from faces": PointTopologyFromFacesSubarray,
        }
        return instance

    def __init__(
        self,
        edge_node_connectivity=None,
        face_node_connectivity=None,
        shape=None,
        start_index=None,
        cell_dimension=None,
        source=None,
        copy=True,
    ):
        """**Initialisation**

        :Parameters:

            edge_node_connectivity: array_like, optional
                A 2-d integer array of indices that corresponds to a
                UGRID "edge_node_connectivity" variable.

            face_node_connectivity: array_like, optional
                A 2-d integer array of indices that corresponds to a
                UGRID "face_node_connectivity" variable.

            shape: `tuple`, optional
                The shape of the point cell domain topology array. If
                the shape is unknown (beacuse the connectivity array
                has not been read yet) then set to `None`, which will
                result in a shape of ``(nan, nan)``.

            {{init start_index: `int`}}

            {{init cell_dimension: `int`}}

            {{init source: optional}}

            {{init copy: `bool`, optional}}

        """
        if edge_node_connectivity is not None:
            node_connectivity = edge_node_connectivity
            compression_type = "point topology from edges"
            if face_node_connectivity is not None:
                raise ValueError(
                    "Can't set both the 'edge_node_connectivity' and "
                    "'face_node_connectivity' parameters"
                )
        elif face_node_connectivity is not None:
            node_connectivity = face_node_connectivity
            compression_type = "point topology from faces"
        else:
            node_connectivity = None
            compression_type = None

        if shape is None:
            from math import nan

            shape = (nan, nan)

        # Note: Setting compressed_dimensions={0: (0,), 1: (1,)} means
        #       that only one subarray will ever span each of the two
        #       dimensions of the 'node_connectivity' array.
        super().__init__(
            connectivity=node_connectivity,
            shape=shape,
            compressed_dimensions={0: (0,), 1: (1,)},
            compression_type=compression_type,
            start_index=start_index,
            cell_dimension=cell_dimension,
            source=source,
            copy=copy,
        )
