from . import core, mixin
from .decorators import _inplace_enabled, _inplace_enabled_define_and_cleanup


class DomainTopology(
    mixin.NetCDFVariable,
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
    same mesh may be reliably deternined by inspection, thereby
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
            cell=cell,
            properties=properties,
            data=data,
            source=source,
            copy=copy,
            _use_data=_use_data,
        )

        self._initialise_netcdf(source)
        self._initialise_original_filenames(source)

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

        .. versionadded:: (cfdm) UGRIDVER

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
            indent=0,
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

        .. versionadded:: (cfdm) UGRIDVER

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

        .. versionadded:: (cfdm) UGRIDVER

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

        .. versionadded:: (cfdm) UGRIDVER

        .. seealso:: `identity`

        :Parameters:

            generator: `bool`, optional
                If True then return a generator for the identities,
                rather than a list.

            kwargs: optional
                Additional configuration parameters. Currently
                none. Unrecognised parameters are ignored.

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
        data. It converts the data so that the set of unique values
        comprises all of the integers in the range ``[0, N-1]`` (if
        the *start_index* parameter is ``0``), or ``[1, N]`` (if
        *start_index* is ``1``), where ``N`` is the number of mesh
        nodes.

        .. versionadded:: (cfdm) UGRIDVER

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
                f"Can't normalise {self.__class__.__name__} with unknown "
                "cell type"
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
            raise ValueError(f"Can't normalise: Unknown cell type {cell!r}")

        d.set_data(data, copy=False)
        return d
