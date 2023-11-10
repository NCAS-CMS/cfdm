from .abstract import MeshArray
from .subarray import BoundsFromNodesSubarray


class BoundsFromNodesArray(MeshArray):
    """An array of cell bounds defined by UGRID node coordinates.

    The UGRID node coordinates contain the locations of the nodes of
    the domain topology. In UGRID, the bounds of edge or face cells
    may be defined by the these locations in conjunction with a
    mapping from from each cell boundary vertex to its corresponding
    coordinate value.

    .. versionadded:: (cfdm) UGRIDVER

    .. seealso:: `BoundsFromNodesSubarray`

    """

    def __new__(cls, *args, **kwargs):
        """Store subarray classes.

        .. versionadded:: (cfdm) UGRIDVER

        """
        instance = super().__new__(cls)
        instance._Subarray = {"bounds from nodes": BoundsFromNodesSubarray}
        return instance

    def __init__(
        self,
        node_connectivity=None,
        shape=None,
        start_index=None,
        cell_dimension=None,
        node_coordinates=None,
        source=None,
        copy=True,
    ):
        """**Initialisation**

        :Parameters:

            node_connectivity: array_like
                A 2-d integer array that contains indices which map
                each cell boundary vertex to its corresponding
                position in the 1-d *node_coordinates* array, as found
                in a UGRID "edge _node_connectivty" or
                "face_node_connectivty" variable.

            shape: `tuple`
                The shape of the bounds array.

            {{init start_index: `int`}}

            {{init cell_dimension: `int`}}

            node_coordinates: array_like
                A 1-d array that contains a coordinate location for
                each mesh node, as found in a UGRID "node_coordinates"
                variable.

            {{init source: optional}}

            {{init copy: `bool`, optional}}

        """
        if shape is None and node_connectivity is not None:
            shape = node_connectivity.shape

        # Note: Setting compressed_dimensions={1: (1,)} means that
        #       only one subarray will ever span the trailing
        #       dimension of the 'node_connectivity' array, but the
        #       leading dimension may be chunked.
        super().__init__(
            connectivity=node_connectivity,
            shape=shape,
            start_index=start_index,
            cell_dimension=cell_dimension,
            compressed_dimensions={1: (1,)},
            compression_type="bounds from nodes",
            source=source,
            copy=copy,
        )

        if source is not None:
            try:
                node_coordinates = source.get_node_coordinates(None)
            except AttributeError:
                node_coordinates = None

        if node_coordinates is not None:
            self._set_component(
                "node_coordinates", node_coordinates, copy=copy
            )

    @property
    def dtype(self):
        """The data-type of the uncompressed data.

        .. versionadded:: (cfdm) UGRIDVER

        """
        return self.get_node_coordinates().dtype

    def conformed_data(self):
        """The conformed node connectivity and node coordinate data.

        The conformed data arrays are mutually consistent and are
        suitable fo use in `Subarray` classes.

        .. versionadded:: (cfdm) UGRIDVER

        :Returns:

            `dict`
                The node connectivty data, with the key ``'data'``,
                and the node coordinate data with the key
                ``'node_coordinates'``.

        """
        out = super().conformed_data()
        out["node_coordinates"] = self.get_node_coordinates()
        return out

    def get_node_coordinates(self, default=ValueError()):
        """The coordinates representing the node locations.

        .. versionadded:: (cfdm) UGRIDVER

        :Parameters:

            default: optional
                Return the value of the *default* parameter if node
                coordinates indices have not been set.

                {{default Exception}}

        :Returns:

                The node coordinates.

        """
        return self._get_component("node_coordinates", default=default)

    def to_memory(self):
        """Bring data on disk into memory.

        There is no change to data that is already in memory.

        .. versionadded:: (cfdm) UGRIDVER

        :Returns:

            `{{class}}`
                A copy of the array with all of its data in memory.

        """
        a = super().to_memory()

        node_coordinates = self.get_node_coordinates(None)
        if node_coordinates is not None:
            try:
                a._set_component(
                    "node_coordinates",
                    node_coordinates.to_memory(),
                    copy=False,
                )
            except AttributeError:
                pass

        return a
