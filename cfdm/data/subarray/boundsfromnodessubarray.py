import numpy as np

from .abstract import MeshSubarray


class BoundsFromNodesSubarray(MeshSubarray):
    """A subarray of cell bounds defined by UGRID node coordinates.

    A subarray describes a unique part of the uncompressed array.

    The UGRID node coordinates contain the locations of the nodes of
    the domain topology. In UGRID, the bounds of edge or face cells
    may be defined by the these locations in conjunction with a
    mapping from from each cell boundary vertex to its corresponding
    coordinate value.

    .. versionadded:: (cfdm) UGRIDVER

    .. seealso:: `BoundsFromNodesArray`

    """

    def __init__(
        self,
        data=None,
        indices=None,
        shape=None,
        compressed_dimensions=None,
        node_coordinates=None,
        start_index=None,
        cell_dimension=None,
        source=None,
        copy=True,
        context_manager=None,
    ):
        """**Initialisation**

        :Parameters:

            data: array_like
                A 2-d integer array that contains indices that map
                each cell boundary vertex to its corresponding
                position in the 1-d *node_coordinates* array, as found
                in a UGRID "edge_node_connectivty" or
                "face_node_connectivty" variable. This array contains
                the mapping for all subarrays.

            indices: `tuple` of `slice`
                The indices of *data* that define this subarray.

            shape: `tuple` of `int`
                The shape of the uncompressed subarray.

            {{init compressed_dimensions: `dict`}}

                *Parameter example:*
                  ``{1: (1,)}``

            node_coordinates: array_like
                A 1-d array that contains a coordinate location for
                each mesh node, as found in a UGRID "node_coordinates"
                variable. This array contains the node coordinates for
                all subarrays.

            {{init start_index: `int`}}

            {{init cell_dimension: `int`}}

            {{init source: optional}}

            {{init copy: `bool`, optional}}

            context_manager: function, optional
                A context manager that provides a runtime context for
                the conversion of *data* and *node_coordinates* to
                `numpy` arrays.

        """
        super().__init__(
            data=data,
            indices=indices,
            shape=shape,
            compressed_dimensions=compressed_dimensions,
            start_index=start_index,
            cell_dimension=cell_dimension,
            source=source,
            copy=copy,
            context_manager=context_manager,
        )

        if source is not None:
            try:
                node_coordinates = source._get_component(
                    "node_coordinates", None
                )
            except AttributeError:
                node_coordinates = None

        if node_coordinates is not None:
            self._set_component(
                "node_coordinates", node_coordinates, copy=False
            )

    def __getitem__(self, indices):
        """Return a subspace of the uncompressed data.

        x.__getitem__(indices) <==> x[indices]

        Returns a subspace of the uncompressed data as an independent
        numpy array.

        .. versionadded:: (cfdm) UGRIDVER

        """
        node_connectivity = self._select_data(check_mask=True)

        if np.ma.isMA(node_connectivity):
            node_indices = node_connectivity.compressed()
            u = np.ma.masked_all(self.shape, dtype=self.dtype)
            u[~node_connectivity.mask] = self._select_node_coordinates(
                node_indices
            )
        else:
            node_indices = node_connectivity.flatten()
            u = self._select_node_coordinates(node_indices)
            u = u.reshape(self.shape)

        if indices is Ellipsis:
            return u

        return u[indices]

    def _select_node_coordinates(self, node_indices):
        """Select node coordinates.

        .. versionadded:: (cfdm) UGRIDVER

        .. seealso:: `_select_data`

        :Parameters:

            node_indices: `numpy.array`
                Indices to the node coordinates array. Must be a 1-d
                integer array. `start_index` will be automatically
                subtracted from the indices prior to the selection of
                node coordinates.

        :Returns:

           `numpy.ndarray`
               The node coordinates that correspond to the
               *node_indices*.

        """
        start_index = self.start_index
        if start_index:
            node_indices = node_indices - start_index

        return self._asanyarray(
            self.node_coordinates, node_indices, check_mask=False
        )

    @property
    def dtype(self):
        """The data-type of the uncompressed data.

        .. versionadded:: (cfdm) UGRIDVER

        """
        return self.node_coordinates.dtype

    @property
    def node_coordinates(self):
        """The coordinates representing the node locations.

        .. versionadded:: (cfdm) UGRIDVER

        """
        return self._get_component("node_coordinates")
