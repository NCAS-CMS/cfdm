from .abstract import MeshArray
from .subarray import CellConnectivitySubarray


class CellConnectivityArray(MeshArray):
    """A connectivity array derived from a UGRID connectivity variable.

    A UGRID connectivity variable contains indices which map each cell
    to its neighbours, as found in a UGRID "face_face_connectivty" or
    "volume_volume_connectivty" variable.

    The connectivity array has one more column than the corresponding
    UGRID variable. The extra column, in the first position, contains
    the identifier for each cell.

    .. versionadded:: (cfdm) UGRIDVER

    .. seealso:: `CellConnectivitySubarray`

    """

    def __new__(cls, *args, **kwargs):
        """Store subarray classes.

        If a child class requires different subarray classes than the
        ones defined here, then they must be defined in the __new__
        method of the child class.

        .. versionadded:: (cfdm) UGRIDVER

        """
        instance = super().__new__(cls)
        instance._Subarray = {"cell connectivity": CellConnectivitySubarray}
        return instance

    def __init__(
        self,
        cell_connectivity=None,
        start_index=None,
        cell_dimension=None,
        source=None,
        copy=True,
    ):
        """**Initialisation**

        :Parameters:

            cell_connectivity: array_like
                A 2-d integer array that contains indices which map
                each cell to its neighbours, as found in a UGRID
                "face_face_connectivty", or
                "volume_volume_connectivty" variable.

            {{init start_index: `int`}}

            {{init cell_dimension: `int`}}

            {{init source: optional}}

            {{init copy: `bool`, optional}}

        """
        if cell_connectivity is None:
            shape = None
        else:
            shape = cell_connectivity.shape
            if cell_dimension == 1:
                shape = shape[::-1]

            shape = (shape[0], shape[1] + 1)

        # Note: Setting compressed_dimensions={1: (1,)} means that
        #       only one subarray will ever span the trailing
        #       dimension of the 'cell_connectivity' array, but the
        #       leading dimension may be chunked.
        super().__init__(
            connectivity=cell_connectivity,
            shape=shape,
            compressed_dimensions={1: (1,)},
            start_index=start_index,
            cell_dimension=cell_dimension,
            compression_type="cell connectivity",
            source=source,
            copy=copy,
        )
