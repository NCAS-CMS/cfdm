import numpy as np

from . import core, mixin
from .decorators import _inplace_enabled, _inplace_enabled_define_and_cleanup


class DomainTopology(
    mixin.NetCDFVariable,
    mixin.NetCDFConnectivityDimension,
    mixin.Topology,
    mixin.PropertiesData,
    mixin.Files,
    core.DomainTopology,
):
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

    In CF-netCDF a domain topology construct can only be provided for
    a UGRID mesh topology variable. The information in the construct
    array is supplied by the UGRID "edge_nodes_connectivity" variable
    (for edge cells) or "face_nodes_connectivity" variable (for face
    cells). The topology for node cells may be provided by any of
    these three UGRID variables. The integer indices contained in the
    UGRID variable may be used as the mesh node identities, although
    the CF data model attaches no significance to the values other
    than the fact that some values are the same as others. The spatial
    dimensionality property is provided by the "location" attribute of
    a variable that references the UGRID mesh topology variable,
    i.e. a data variable or a UGRID location index set variable.

    A single UGRID mesh topology defines multiple domain constructs
    and defines how they relate to each other. For instance, when
    "face_node_connectivity" and "edge_node_connectivity" variables
    are both present there are three implied domain constructs - one
    each for face, edge and point cells - all of which have the same
    mesh and so are explicitly linked (e.g. it is known which edge
    cells define each face cell). The CF data model has no mechanism
    for explicitly recording such relationships between multiple
    domain constructs, however whether or not two domains have the
    same mesh may be reliably determined by inspection, thereby
    allowing the creation of netCDF datasets containing UGRID mesh
    topology variables.

    The restrictions on the type of mesh that may be used with a given
    cell spatial dimensionality excludes some meshes which can be
    described by an undirected graph, but is consistent with UGRID
    encoding within CF-netCDF. UGRID also describes meshes for
    three-dimensional volume cells that correspond to a volume
    enclosed by a set of faces, but how the nodes relate to volume
    boundary vertices is undefined and so volume cells are currently
    omitted from the CF data model.

    See CF Appendix I "The CF Data Model".

    **NetCDF interface**

    The netCDF variable name of the UGRID mesh topology variable may
    be accessed with the `nc_set_variable`, `nc_get_variable`,
    `nc_del_variable`, and `nc_has_variable` methods.

    {{netCDF dataset chunks}}

    .. versionadded:: (cfdm) 1.11.0.0

    """

    def creation_commands(
        self,
        representative_data=False,
        namespace=None,
        indent=0,
        string=True,
        name="c",
        data_name="data",
        header=True,
    ):
        """Returns the commands to create the domain topology construct.

        .. versionadded:: (cfdm) 1.11.0.0

        .. seealso:: `{{package}}.Data.creation_commands`,
                     `{{package}}.Field.creation_commands`

        :Parameters:

            {{representative_data: `bool`, optional}}

            {{namespace: `str`, optional}}

            {{indent: `int`, optional}}

            {{string: `bool`, optional}}

            {{name: `str`, optional}}

            {{data_name: `str`, optional}}

            {{header: `bool`, optional}}

        :Returns:

            {{returns creation_commands}}

        """
        out = super().creation_commands(
            representative_data=representative_data,
            indent=indent,
            namespace=namespace,
            string=False,
            name=name,
            data_name=data_name,
            header=header,
        )

        cell = self.get_cell(None)
        if cell is not None:
            out.append(f"{name}.set_cell({cell!r})")

        if string:
            indent = " " * indent
            out[0] = indent + out[0]
            out = ("\n" + indent).join(out)

        return out

    def dump(
        self,
        display=True,
        _omit_properties=None,
        _key=None,
        _level=0,
        _title=None,
        _axes=None,
        _axis_names=None,
    ):
        """A full description of the domain topology construct.

        Returns a description of all properties, including those of
        components, and provides selected values of all data arrays.

        .. versionadded:: (cfdm) 1.11.0.0

        :Parameters:

            display: `bool`, optional
                If False then return the description as a string. By
                default the description is printed.

        :Returns:

            {{returns dump}}

        """
        if _title is None:
            _title = "Domain Topology: " + self.identity(default="")

        return super().dump(
            display=display,
            _key=_key,
            _omit_properties=_omit_properties,
            _level=_level,
            _title=_title,
            _axes=_axes,
            _axis_names=_axis_names,
        )

    def identity(self, default=""):
        """Return the canonical identity.

        By default the identity is the first found of the following:

        * The cell type, preceded by ``'cell:'``.
        * The ``standard_name`` property.
        * The ``cf_role`` property, preceded by 'cf_role='.
        * The ``long_name`` property, preceded by 'long_name='.
        * The netCDF variable name, preceded by 'ncvar%'.
        * The value of the default parameter.

        .. versionadded:: (cfdm) 1.11.0.0

        .. seealso:: `identities`

        :Parameters:

            default: optional
                If no identity can be found then return the value of the
                default parameter.

        :Returns:

                The identity.

        """
        n = self.get_cell(None)
        if n is not None:
            return f"cell:{n}"

        n = self.get_property("standard_name", None)
        if n is not None:
            return n

        for prop in ("cf_role", "long_name"):
            n = self.get_property(prop, None)
            if n is not None:
                return f"{prop}={n}"

        n = self.nc_get_variable(None)
        if n is not None:
            return f"ncvar%{n}"

        return default

    def identities(self, generator=False, **kwargs):
        """Return all possible identities.

        The identities comprise:

        * The cell type type, preceded by ``'cell:'``.
        * The ``standard_name`` property.
        * All properties, preceded by the property name and a colon,
          e.g. ``'long_name:Air temperature'``.
        * The netCDF variable name, preceded by ``'ncvar%'``.

        .. versionadded:: (cfdm) 1.11.0.0

        .. seealso:: `identity`

        :Parameters:

            generator: `bool`, optional
                If True then return a generator for the identities,
                rather than a list.

            kwargs: optional
                Additional configuration parameters that may be used
                by subclasses.

        :Returns:

            `list` or generator
                The identities.

        """
        n = self.get_cell(None)
        if n is not None:
            pre = ((f"cell:{n}",),)
            pre0 = kwargs.pop("pre", None)
            if pre0:
                pre = tuple(pre0) + pre

            kwargs["pre"] = pre

        return super().identities(generator=generator, **kwargs)

    @_inplace_enabled(default=False)
    def normalise(
        self, start_index=0, remove_empty_columns=False, inplace=False
    ):
        """Normalise the data values.

        Normalised data is in a form that is suitable for creating a
        CF-netCDF UGRID "edge_node_connectivity" or
        "face_node_connectivity" variable.

        Normalisation does not change the logical content of the
        data. It converts the data so that the set of values comprises
        all of the integers in the range ``[0, N-1]`` (if the
        *start_index* parameter is ``0``), or ``[1, N]`` (if
        *start_index* is ``1``), where ``N`` is the number of mesh
        nodes.

        .. versionadded:: (cfdm) 1.11.0.0

        .. seealso:: `sort`, `to_edge`

        :Parameters:

            start_index: `int`, optional
                The start index for the data values in the normalised
                data. Must be ``0`` (the default) or ``1`` for zero-
                or one-based indices respectively.

            remove_empty_columns: `bool`, optional
                If True then remove any array columns that are
                entirely missing data. By default these are retained.

            {{inplace: `bool`, optional}}

        :Returns:

            `{{class}}` or `None`
                The normalised domain topology construct, or `None` if
                the operation was in-place.

        **Examples*

        Face cells (similarly for edge cells):

        >>> data = {{package}}.Data(
        ...   [[1, 4, 5, 2], [4, 10, 1, -99], [122, 123, 106, 105]],
        ...   mask_value=-99
        ... )
        >>> d = {{package}}.{{class}}(cell='face', data=data)
        >>> print(d.array)
        [[1 4 5 2]
         [4 10 1 --]
         [122 123 106 105]]
        >>> d0 = d.normalise()
        >>> print(c.array)
        [[0 2 3 1]
         [2 4 0 --]
         [7 8 6 5]]
        >>> (d0.array == d.normalise().array).all()
        True
        >>> d1 = d.normalise(start_index=1)
        >>> print(d1.array)
        [[1 3 4 2]
         [3 5 1 --]
         [8 9 7 6]]
        >>> (d1.array == d0.array + 1).all()
        True

        Point cells:

        >>> data = {{package}}.Data(
        ...   [[4, 1, 10, 125], [1, 4, -99, -99], [125, 4, -99, -99]],
        ...   mask_value=-99
        ... )
        >>> d = {{package}}.{{class}}(cell='point', data=data)
        >>> print(d.array)
        [[4 1 10 125]
         [1 4 -- --]
         [125 4 -- --]]
        >>> print(d.normalise().array)
        [[0 1 2]
         [1 0 --]
         [2 0 --]]
        >>> print(d.normalise(start_index=1).array)
        [[1 2 3]
         [2 1 --]
         [3 1 --]]

        """
        import numpy as np

        if start_index not in (0, 1):
            raise ValueError("The 'start_index' parameter must be 0 or 1")

        cell = self.get_cell(None)
        if cell is None:
            raise ValueError(
                f"Can't normalise {self!r} with unknown cell type"
            )

        d = _inplace_enabled_define_and_cleanup(self)
        data = d.array

        if cell in ("edge", "face"):
            # Normalise node ids for edge or face cells.
            mask = np.ma.getmaskarray(data)
            n, b = np.where(~mask)
            data[n, b] = np.unique(data[n, b], return_inverse=True)[1]

            if remove_empty_columns:
                # Discard columns that are all missing data
                data = self._remove_empty_columns(data)

            if start_index:
                data += 1
        elif cell == "point":
            # Normalise cell ids for point cells
            data = self._normalise_cell_ids(
                data, start_index, remove_empty_columns
            )
        else:
            raise ValueError(
                f"Can't normalise {self!r}: Unknown cell type {cell!r}"
            )

        d.set_data(data, copy=False)
        return d

    def sort(self):
        """Sort the domain topology node ids.

        Only edge and point domain topologies can be sorted.

        Sorting is across both dimensions. In general, dimension 1 is
        sorted first, and then dimension 0 is sort by its first
        column.

        For an edge domain topology, column 1 is also sorted within
        each unique column 0 value.

        For a point dimension topology, column 0 is omitted from the
        dimension 1 sort (because it contains the node id
        definition for each row).
        
        .. note:: The purpose of this method is to facilitate the
                  comparison of normalised domain topologies, to see
                  if they belong to the same UGRID mesh. The sorted
                  domain topology will, in general, be inconsistent
                  with other metadata, such as the node geo-locations
                  stored as domain cell coordinates or cell bounds.

        .. versionadded:: (cfdm) NEXTVERSION

        .. seealso:: `normalise`, `to_edge`

        :Returns:

            `{{class}}`
                The sorted domain topology construct.

        **Examples**

        >>> f= {{package}}.example_field(9)
        >>> print(f)
        Field: northward_wind (ncvar%v)
        -------------------------------
        Data            : northward_wind(time(2), ncdim%nMesh2_edge(9)) ms-1
        Cell methods    : time(2): point (interval: 3600 s)
        Dimension coords: time(2) = [2016-01-02 01:00:00, 2016-01-02 11:00:00] gregorian
        Auxiliary coords: longitude(ncdim%nMesh2_edge(9)) = [-41.5, ..., -43.0] degrees_east
                        : latitude(ncdim%nMesh2_edge(9)) = [34.5, ..., 32.0] degrees_north
        Topologies      : cell:edge(ncdim%nMesh2_edge(9), 2) = [[1, ..., 5]]
        Connectivities  : connectivity:node(ncdim%nMesh2_edge(9), 6) = [[0, ..., --]]
        >>> dt = f.domain_topology()
        >>> print(dt.array)
        [[1 6]
         [3 6]
         [3 1]
         [0 1]
         [2 0]
         [2 3]
         [2 4]
         [5 4]
         [3 5]]
        >>> print(dt.sort().array)
        [[0 1]
         [0 2]
         [1 3]
         [1 6]
         [2 3]
         [2 4]
         [3 5]
         [3 6]
         [4 5]]

        >>> f= {{package}}.example_field(10)
        >>> print(f)
        Field: air_pressure (ncvar%pa)
        ------------------------------
        Data            : air_pressure(time(2), ncdim%nMesh2_node(7)) hPa
        Cell methods    : time(2): point (interval: 3600 s)
        Dimension coords: time(2) = [2016-01-02 01:00:00, 2016-01-02 11:00:00] gregorian
        Auxiliary coords: longitude(ncdim%nMesh2_node(7)) = [-45.0, ..., -40.0] degrees_east
                        : latitude(ncdim%nMesh2_node(7)) = [35.0, ..., 34.0] degrees_north
        Topologies      : cell:point(ncdim%nMesh2_node(7), 5) = [[0, ..., --]]
        >>> print(f.domain_topology().array)
        >>> dt = f.domain_topology()
        >>> dt = dt[::-1]
        >>> print(dt.array)
        [[6 3 1 -- --]
         [5 4 3 -- --]
         [4 2 5 -- --]
         [3 2 1 5 6]
         [2 0 3 4 --]
         [1 6 0 3 --]
         [0 1 2 -- --]]
        >>> print(dt.sort().array)
        [[0 1 2 -- --]
         [1 0 3 6 --]
         [2 0 3 4 --]
         [3 1 2 5 6]
         [4 2 5 -- --]
         [5 3 4 -- --]
         [6 1 3 -- --]]

        """
        cell = self.get_cell(None)
        if cell not in ("edge", "point"):
            raise ValueError(f"Can't sort {self!r} with {cell} cells")

        data = self.array

        if cell == "edge":
            # Sort within each row
            data.sort(axis=1)
            # Sort over rows
            data = sorted(data.tolist())

        elif cell == "point":
            # Sort within each row from column 1
            data[:, 1:] = np.ma.sort(data[:, 1:], axis=1, endwith=True)
            # Sort over rows by value in column 0
            data = data[data[:, 0].argsort()]

        data = self._Data(data, dtype=self.dtype, chunks=self.data.chunks)

        d = self.copy()
        d.set_data(data, copy=False)

        return d

    def to_edge(self, sort=False, face_nodes=None):
        """Create a domain topology of edges.

        .. versionadded:: (cfdm) NEXTVERSION

        .. seealso:: `normalise`, `sort`

        :Parameters:

            sort: `bool`
                If True then sort output edges. This is equivalent to,
                but faster than, setting *sort* to False and sorting
                the returned `{{class}}` with its `sort` method.

            face_nodes: `None` or sequence of `int`, optional
                The unique node ids for 'face' cells. If `None` (the
                default) then the node ids will be inferred from the
                data, at some computational expense. The order of the
                nodes is immaterial.

                .. note:: No checks are carried out to ensure that the
                          given *face_nodes* match the actual node ids
                          stored in the data, and a mis-match will
                          result in an incorrect result.

        :Returns:

            `{{class}}`
                The domain topology construct of unique edges.

        **Examples**

        >>> f= {{package}}.example_field(8)
        >>> print(f)
        Field: air_temperature (ncvar%ta)
        ---------------------------------
        Data            : air_temperature(time(2), ncdim%nMesh2_face(3)) K
        Cell methods    : time(2): point (interval: 3600 s)
        Dimension coords: time(2) = [2016-01-02 01:00:00, 2016-01-02 11:00:00] gregorian
        Auxiliary coords: longitude(ncdim%nMesh2_face(3)) = [-44.0, -44.0, -42.0] degrees_east
                        : latitude(ncdim%nMesh2_face(3)) = [34.0, 32.0, 34.0] degrees_north
        Topologies      : cell:face(ncdim%nMesh2_face(3), 4) = [[2, ..., --]]
        Connectivities  : connectivity:edge(ncdim%nMesh2_face(3), 5) = [[0, ..., --]]
        >>> dt = f[0].domain_topology()
        >>> print(dt.array)
        [[2 3 1 0]
         [4 5 3 2]
         [6 1 3 --]]
        >>> dt.to_edge()
        <DomainTopology: cell:edge(9, 2) >
        >>> print(dt.to_edge().array)
        [[0 1]
         [2 4]
         [2 3]
         [0 2]
         [4 5]
         [3 6]
         [1 6]
         [1 3]
         [3 5]]
        >>> print(dt.to_edge(sort=True).array)
        [[0 1]
         [0 2]
         [1 3]
         [1 6]
         [2 3]
         [2 4]
         [3 5]
         [3 6]
         [4 5]]

        >>> f= {{package}}.example_field(10)
        >>> print(f)
        Field: air_pressure (ncvar%pa)
        ------------------------------
        Data            : air_pressure(time(2), ncdim%nMesh2_node(7)) hPa
        Cell methods    : time(2): point (interval: 3600 s)
        Dimension coords: time(2) = [2016-01-02 01:00:00, 2016-01-02 11:00:00] gregorian
        Auxiliary coords: longitude(ncdim%nMesh2_node(7)) = [-45.0, ..., -40.0] degrees_east
                        : latitude(ncdim%nMesh2_node(7)) = [35.0, ..., 34.0] degrees_north
        Topologies      : cell:point(ncdim%nMesh2_node(7), 5) = [[0, ..., --]]
        >>> dt = f[0].domain_topology()
        >>> print(dt.array)
        [[0 1 2 -- --]
         [1 6 0 3 --]
         [2 0 3 4 --]
         [3 2 1 5 6]
         [4 2 5 -- --]
         [5 4 3 -- --]
         [6 3 1 -- --]]
        >>> dt.to_edge()
        <DomainTopology: cell:edge(9, 2) >
        >>> print(dt.to_edge(sort=True).array)
        [[0 1]
         [0 2]
         [1 3]
         [1 6]
         [2 3]
         [2 4]
         [3 5]
         [3 6]
         [4 5]]

        """
        edges = []
        edges_extend = edges.extend

        cell = self.get_cell(None)
        if face_nodes is not None and cell != "face":
            raise ValueError(
                "Can't set 'face_nodes' for {self!r} with {cell} cells"
            )

        # Deal with simple "edge" case first
        if cell == "edge":
            if sort:
                edges = self.sort()
            else:
                edges = self.copy()

            return edges

        # Still here? Then deal with the other cell types.
        if cell == "point":
            points = self.array
            masked = np.ma.is_masked(points)

            # Loop round the nodes, finding the node-pairs that define
            # the edges.
            for row in points:
                if masked:
                    row = row.compressed()

                node = row[0]
                row = row[1:].tolist()
                edges_extend(
                    [(node, n) if node < n else (n, node) for n in row]
                )

            del points, row

        elif cell == "face":
            from cfdm.data.subarray import PointTopologyFromFacesSubarray

            connected_nodes = PointTopologyFromFacesSubarray._connected_nodes

            faces = self.array
            masked = np.ma.is_masked(faces)

            if face_nodes is None:
                # Find the unique node ids
                face_nodes = np.unique(faces).tolist()
                if masked:
                    face_nodes = face_nodes[:-1]

            # Loop round the face nodes, finding the node-pairs that
            # define the edges.
            for n in face_nodes:
                edges_extend(connected_nodes(n, faces, masked, edges=True))

            del faces, face_nodes

        else:
            raise NotImplementedError(
                f"Can't get edges from {self!r} with {cell} cells"
            )

        # Remove duplicates to get the set of unique edges.
        #
        # Every edge currently appears twice in the 'face_edges'
        # list. E.g. edge (1, 5) will appear once from processing node
        # 1, and once from processing node 5.
        edges = set(edges)

        if sort:
            edges = sorted(edges)
        else:
            edges = list(edges)

        edges = self._Data(edges, dtype=self.dtype)

        out = self.copy()
        out.set_cell("edge")
        out.set_data(edges, copy=False)

        return out
