from . import abstract


class DomainTopology(abstract.Topology):
    """A domain topology construct of the CF data model.

    A domain topology construct defines the geospatial topology of
    cells arranged in two or three dimensions in real space but
    indexed by a single (discrete) domain axis construct, and at most
    one domain topology construct may be associated with any such
    domain axis. The topology describes topological relationships
    between the cells - spatial relationships which do not depend on
    the cell locations - and is represented by an undirected graph,
    i.e. a mesh in which pairs of nodes are connected by links. Each
    node has a unique arbitrary identity that is independent of its
    spatial location, and different nodes may be spatially co-located.

    The topology may only describe cells that have a common spatial
    dimensionality, one of:

    * Point: A point is zero-dimensional and has no boundary vertices.
    * Edge: An edge is one-dimensional and corresponds to a line
            connecting two boundary vertices.
    * Face: A face is two-dimensional and corresponds to a surface
            enclosed by a set of edges.

    Each type of cell implies a restricted topology for which only
    some kinds of mesh are allowed. For point cells, every node
    corresponds to exactly one cell; and two cells have a topological
    relationship if and only if their nodes are connected by a mesh
    link. For edge and face cells, every node corresponds to a
    boundary vertex of a cell; the same node can represent vertices in
    multiple cells; every link in the mesh connects two cell boundary
    vertices; and two cells have a topological relationship if and
    only if they share at least one node.

    A domain topology construct contains an array defining the mesh,
    and properties to describe it. There must be a property indicating
    the spatial dimensionality of the cells. The array values comprise
    the node identities, and all array elements that refer to the same
    node must contain the same value, which must differ from any other
    value in the array. The array spans the domain axis construct and
    also has a ragged dimension, whose function depends on the spatial
    dimensionality of the cells.

    For each point cell, the first element along the ragged dimension
    contains the node identity of the cell, and the following elements
    contain in arbitrary order the identities of all the cells to
    which it is connected by a mesh link.

    For each edge or face cell, the elements along the ragged
    dimension contain the node identities of the boundary vertices of
    the cell, in the same order that the boundary vertices are stored
    by the auxiliary coordinate constructs. Each boundary vertex
    except the last is connected by a mesh link to the next vertex
    along the ragged dimension, and the last vertex is connected to
    the first.

    When a domain topology construct is present it is considered to be
    definitive and must be used in preference to the topology implied
    by inspection of any other constructs, which is not guaranteed to
    be the same.

    See CF Appendix I "The CF Data Model".

    .. versionadded:: (cfdm) UGRIDVER

    """

    def __init__(
        self,
        cell=None,
        properties=None,
        data=None,
        source=None,
        copy=True,
        _use_data=True,
    ):
        """**Initialisation**

        :Parameters:

            {{init cell: `str`, optional}}

            {{init properties: `dict`, optional}}

                *Parameter example:*
                  ``properties={'long_name': 'face to node mapping'}``

            {{init data: data_like, optional}}

            {{init source: optional}}

            {{init copy: `bool`, optional}}

        """
        super().__init__(
            properties=properties,
            source=source,
            data=data,
            copy=copy,
            _use_data=_use_data,
        )

        if source is not None:
            try:
                cell = source.get_cell(None)
            except AttributeError:
                cell = None

        if cell is not None:
            self.set_cell(cell)

    @property
    def construct_type(self):
        """Return a description of the construct type.

        .. versionadded:: (cfdm) UGRIDVER

        :Returns:

            `str`
                The construct type.

        **Examples:**

        >>> d = {{package}}.{{class}}()
        >>> d.construct_type
        'domain_topology'

        """
        return "domain_topology"

    def del_cell(self, default=ValueError()):
        """Remove the cell type.

        {{cell type}}

        .. versionadded:: (cfdm) UGRIDVER

        .. seealso:: `get_cell`, `has_cell`, `set_cell`

        :Parameters:

            default: optional
                Return the value of the *default* parameter if the
                cell type has not been set.

                {{default Exception}}

        :Returns:

                The removed cell type.

        **Examples**

        >>> d = {{package}}.{{class}}()
        >>> d.has_cell()
        False
        >>> d.set_cell('face')
        >>> d.has_cell()
        True
        >>> d.get_cell()
        'face'
        >>> d.del_cell()
        'face'
        >>> d.get_cell()
        Traceback (most recent call last):
            ...
        ValueError: {{class}} has no 'cell' component
        >>> print(d.get_cell(None))
        None

        """
        return self._del_component("cell", default=default)

    def get_cell(self, default=ValueError()):
        """Return the cell type.

        {{cell type}}

        .. versionadded:: (cfdm) UGRIDVER

        .. seealso:: `del_cell`, `has_cell`, `set_cell`

        :Parameters:

            default: optional
                Return the value of the *default* parameter if the
                cell type has not been set.

                {{default Exception}}

        :Returns:

                The value of the cell type.

        **Examples**

        >>> d = {{package}}.{{class}}()
        >>> d.has_cell()
        False
        >>> d.set_cell('face')
        >>> d.has_cell()
        True
        >>> d.get_cell()
        'face'
        >>> d.del_cell()
        'face'
        >>> d.get_cell()
        Traceback (most recent call last):
            ...
        ValueError: {{class}} has no 'cell' component
        >>> print(d.get_cell(None))
        None

        """
        return self._get_component("cell", default=default)

    def has_cell(self):
        """Whether the cell type has been set.

        {{cell type}}

        .. versionadded:: (cfdm) UGRIDVER

        .. seealso:: `del_cell`, `get_cell`, `set_cell`

        :Returns:

            `bool`
                `True` if the cell type has been set, otherwise
                `False`.

        **Examples**

        >>> d = {{package}}.{{class}}()
        >>> d.has_cell()
        False
        >>> d.set_cell('face')
        >>> d.has_cell()
        True
        >>> d.get_cell()
        'face'
        >>> d.del_cell()
        'face'
        >>> d.get_cell()
        Traceback (most recent call last):
            ...
        ValueError: {{class}} has no 'cell' component
        >>> print(d.get_cell(None))
        None

        """
        return self._has_component("cell")

    def set_cell(self, cell):
        """Set the cell type type.

        {{cell type}}

        .. versionadded:: (cfdm) UGRIDVER

        .. seealso:: `del_cell`, `get_cell`, `has_cell`

        :Parameters:

            cell: `str`
                The value for the cell type.

        :Returns:

             `None`

        **Examples**

        >>> d = {{package}}.{{class}}()
        >>> d.has_cell()
        False
        >>> d.set_cell('face')
        >>> d.has_cell()
        True
        >>> d.get_cell()
        'face'
        >>> d.del_cell()
        'face'
        >>> d.get_cell()
        Traceback (most recent call last):
            ...
        ValueError: {{class}} has no 'cell' component
        >>> print(d.get_cell(None))
        None

        """
        cell_types = ("point", "edge", "face")
        if cell not in cell_types:
            raise ValueError(
                f"Can't set cell type of {cell!r}. "
                f"Must be one of {cell_types}"
            )

        self._set_component("cell", cell, copy=False)
