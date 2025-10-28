import logging

import numpy as np

logger = logging.getLogger(__name__)


class NetCDFWriteUgrid:
    """Mixin class for writing UGRID meshes to a dataset.

    .. versionadded: (cfdm) NEXTVERSION

    """

    def _ugrid_write_domain_topology(self, parent, key, domain_topology):
        """Write a domain topology to a *_node_connectivity variable.

        If an equal domain topology has already been written to the
        dataset then it is not re-written.

        .. versionadded: (cfdm) NEXTVERSION

        :Parameters:

            parent: `Field` or `Domain` or `None`
                The parent Field or Domain. Set to `None` if there is
                no parent (as could occur when for an "edge"
                `domain_topology` that is derived from point-cell
                domain topology).

            key: `str` or `None`
                The internal identifier of the domain topology
                construct. Set to `None` if *parent* is `None`.

            domain_topology: `DomainTopology`
                The Domain Topology construct to be written.

        :Returns:

            `str` or `None`
                The dataset variable name of the domain topology
                object, or `None` if one wasn't written.

        **Examples**

        >>> ncvar = n._ugrid_write_domain_topology(f, 'domaintopology0', dt)

        """
        from cfdm.functions import integer_dtype

        g = self.write_vars

        # Normalise the array, so that its N node ids are 0, ..., N-1

        domain_topology.normalise(inplace=True)
        if key is not None:
            g["normalised_domain_topologies"][key] = domain_topology

        cell = domain_topology.get_cell(None)
        if cell == "point":
            # There's no corresponding UGRID variable for "point"
            # cells, so just return.
            return None

        if cell == "volume":
            # Placeholder exception to remind us to do some work,
            # should volume cells ever make it into CF.
            raise NotImplementedError(
                f"Can't write a UGRID mesh of volume cells for {parent!r}"
            )

        if cell not in ("face", "edge"):
            raise ValueError(
                f"{parent!r} has unknown domain topology cell type: "
                f"{domain_topology!r}"
            )

        # Get the netCDF dimensions
        size0, size1 = domain_topology.data.shape
        if parent is not None:
            # Get the number-of-cells dimension name from the parent
            cells_ncdim = self._dataset_dimensions(
                parent, key, domain_topology
            )
            cells_ncdim = cells_ncdim[0]
        else:
            # Get the number-of-cells dimension name without reference
            # to a parent
            cells_ncdim = self._name(
                f"{cell}s", dimsize=size0, role=f"ugrid_{cell}"
            )

        # Get the connectivity dimension name from the DomainTopology
        connectivity_ncdim = domain_topology.nc_get_connectivity_dimension(
            f"connectivity{size1}"
        )
        connectivity_ncdim = self._name(
            connectivity_ncdim, dimsize=size1, role="ugrid_connectivity"
        )

        ncdimensions = (cells_ncdim, connectivity_ncdim)

        if self._already_in_file(domain_topology, ncdimensions):
            # This domain topology variable has been previously
            # created, so no need to do so again.
            ncvar = g["seen"][id(domain_topology)]["ncvar"]
        else:
            # This domain topology variable has not been previously
            # created, so create it now.

            if cells_ncdim not in g["ncdim_to_size"]:
                # Create a new number-of-cells netCDF dimension
                self._write_dimension(cells_ncdim, parent, size=size0)

            if connectivity_ncdim not in g["ncdim_to_size"]:
                # Create a new connectivity netCDF dimension
                self._write_dimension(connectivity_ncdim, parent, size=size1)

            ncvar = self._create_variable_name(
                domain_topology, default=f"{cell}_node_connectivity"
            )

            # Write as 32-bit integers if possible
            dtype = integer_dtype(domain_topology.data.size)
            domain_topology.data.dtype = dtype

            if parent is not None:
                # Get domain axis keys from the parent
                domain_axes = self.implementation.get_data_axes(parent, key)
            else:
                domain_axes = None

            self._write_netcdf_variable(
                ncvar,
                ncdimensions,
                domain_topology,
                domain_axes,
            )

        g["key_to_ncvar"][key] = ncvar
        g["key_to_ncdims"][key] = ncdimensions

        return ncvar

    def _ugrid_write_cell_connectivity(self, f, key, cell_connectivity):
        """Write a cell connectivity to a *_*_connectivity variable.

        If an equal cell connectivity has already been written to the
        dataset then it is not re-written.

        .. versionadded: (cfdm) NEXTVERSION

        :Parameters:

            f: `Field` or `Domain`
                The parent Field or Domain.

            key: `str`
                The internal identifier of the cell connectivity
                construct.

            cell_connectivity: `CellConnectivity`
                The Cell Connectivity construct to be written.

        :Returns:

            `str`
                The dataset variable name of the cell connectivity
                object.

        **Examples**

        >>> ncvar = n._ugrid_write_cell_connectivity(f, 'cellconn0', cc)

        """
        from cfdm.functions import integer_dtype

        g = self.write_vars

        # Normalise the array, so that its N cell ids are 0, ..., N-1
        cell_connectivity.normalise(inplace=True)
        g["normalised_cell_connectivities"][key] = cell_connectivity

        # Remove the first column, which (now that the array has been
        # normalised) just contains the index of each row (0, ...,
        # N-1) and is not stored in the dataset.
        cell_connectivity = cell_connectivity[:, 1:]

        # Get the netCDF dimensions
        size = cell_connectivity.data.shape[-1]
        ncdimensions = self._dataset_dimensions(f, key, cell_connectivity)
        connectivity_ncdim = cell_connectivity.nc_get_connectivity_dimension(
            f"connectivity{size}"
        )
        connectivity_ncdim = self._name(
            connectivity_ncdim, dimsize=size, role="ugrid_connectivity"
        )
        ncdimensions = ncdimensions + (connectivity_ncdim,)

        if self._already_in_file(cell_connectivity, ncdimensions):
            # This cell_connectivity variable has been previously
            # created, so no need to do so again.
            ncvar = g["seen"][id(cell_connectivity)]["ncvar"]
        else:
            # This cell_connectivity variable has not been previously
            # created, so create it now.
            if connectivity_ncdim not in g["ncdim_to_size"]:
                self._write_dimension(connectivity_ncdim, f, size=size)

            match cell_connectivity.get_connectivity("cell"):
                case "edge":
                    cell = "face"
                case "node":
                    cell = "edge"
                case "face":
                    cell = "volume"

            ncvar = self._create_variable_name(
                cell_connectivity, default=f"{cell}_{cell}_connectivity"
            )

            # Write as 32-bit integers if possible
            dtype = integer_dtype(cell_connectivity.shape[0])
            cell_connectivity.data.dtype = dtype

            self._write_netcdf_variable(
                ncvar,
                ncdimensions,
                cell_connectivity,
                self.implementation.get_data_axes(f, key),
            )

        g["key_to_ncvar"][key] = ncvar
        g["key_to_ncdims"][key] = ncdimensions

        return ncvar

    def _ugrid_write_node_coordinate(self, node_coord, ncdimensions):
        """Write UGRID node coordinates to the dataset.

        .. versionadded:: (cfdm) NEXTVERSION

        :Parameters:

            node_coord: `AuxiliaryCoordinate`
                The node coordinates to be written.

            ncdimensions: sequence of `str`
                The netCDF dimension name of the node coordinates
                dimension, e.g. ``('n_nodes',)``.

        :Returns:

            `str`
                The netCDF variable name of the dateset node
                coordinates variable.

        """
        g = self.write_vars

        already_in_file = self._already_in_file(node_coord, ncdimensions)

        if already_in_file:
            ncvar = g["seen"][id(node_coord)]["ncvar"]
        else:
            ncvar = self._create_variable_name(
                node_coord, default="node_coordinates"
            )

            # Create a new UGRID node coordinate variable
            if self.implementation.get_data(node_coord, None) is not None:
                self._write_netcdf_variable(
                    ncvar,
                    ncdimensions,
                    node_coord,
                    None,
                )

        return ncvar

    def _ugrid_get_mesh_ncvar(self, parent):
        """Get the name of the netCDF mesh variable.

        .. versionadded:: (cfdm) NEXTVERSION

        :Parameters:

            parent: `Field` or `Domain`
                 The parent Field or Domain from which to get the mesh
                 description.

        :Returns:

            `str` or `None`
                The name of the netCDF mesh variable that will store
                the parent's UGRID mesh, or `None` if the parent is
                not UGRID.

        """
        g = self.write_vars

        # Create a new mesh description for this parent
        ncvar_new, mesh_new = self._ugrid_create_mesh(parent)

        if ncvar_new is None:
            # Parent is not UGRID
            return

        for ncvar, mesh in g["meshes"].items():
            if self._ugrid_linked_meshes(mesh, mesh_new):
                # The mesh is either A) identical to another parent's
                # mesh, or B) represents a different location (node,
                # edge, face, or volume) of another parent's mesh.
                #
                # In both cases we can assign that other parent's mesh
                # to the current parent; but in case B), we first
                # update the other parent's mesh to include the new
                # location. In case A), `_ugrid_update_mesh` makes no
                # change to the other parent's mesh.
                self._ugrid_update_mesh(mesh, mesh_new)
                return ncvar

        # Still here? Then this parent's UGRID mesh is not the same
        # as, nor linked to, any other parent's mesh, so we save save
        # it as a new mesh.
        g["meshes"][ncvar_new] = mesh_new

        return ncvar_new

    def _ugrid_create_mesh(self, parent):
        """Create a mesh description from a parent Field or Domain.

        The mesh description is a dictionary that always has the
        keys::

           'attributes'
           'topology_dimension'
           'node_coordinates'
           'sorted_edges'

        as well as some subset of the keys::

           'edge_coordinates'
           'face_coordinates'
           'volume_coordinates'
           'edge_node_connectivity'
           'face_node_connectivity'
           'volume_node_connectivity'
           'edge_edge_connectivity'
           'face_face_connectivity'
           'volume_volume_connectivity'

        E.g. the mesh description for the UGRID mesh topology of face
             cells taken from ``cfdm.example_field(8)``. In this case
             the 'node_coordinates' Auxiliary Coordinates are derived
             from the face cell bounds::

           {'attributes':
                {'face_coordinates': ['Mesh2_face_x', 'Mesh2_face_y'],
                 'face_face_connectivity': ['Mesh2_face_links'],
                 'face_node_connectivity': ['Mesh2_face_nodes']},
            'face_coordinates':
                [<AuxiliaryCoordinate: longitude(3) degrees_east>,
                 <AuxiliaryCoordinate: latitude(3) degrees_north>],
            'face_face_connectivity':
                [<CellConnectivity: connectivity:edge(3, 5) >],
            'face_node_connectivity':
                [<DomainTopology: cell:face(3, 4) >],
            'node_coordinates':
                [<AuxiliaryCoordinate: longitude(7) degrees_east>,
                 <AuxiliaryCoordinate: latitude(7) degrees_north>],
            'sorted_edges':
                {},
            'topology_dimension':
                2
           }

        E.g. the mesh description for the UGRID mesh topology of edge
             cells taken from ``cfdm.example_field(9)``. In this case
             the 'node_coordinates' Auxiliary Coordinates are derived
             from the edge cell bounds::

           {'attributes':
                {'edge_coordinates': ['Mesh2_edge_x', 'Mesh2_edge_y'],
                 'edge_edge_connectivity': ['Mesh2_edge_links'],
                 'edge_node_connectivity': ['Mesh2_edge_nodes']},
            'edge_coordinates':
                [<AuxiliaryCoordinate: longitude(9) degrees_east>,
                 <AuxiliaryCoordinate: latitude(9) degrees_north>],
            'edge_edge_connectivity':
                [<CellConnectivity: connectivity:node(9, 6) >],
            'edge_node_connectivity':
                [<DomainTopology: cell:edge(9, 2) >],
            'node_coordinates':
                [<AuxiliaryCoordinate: longitude(7) degrees_east>,
                 <AuxiliaryCoordinate: latitude(7) degrees_north>],
            'sorted_edges':
                {},
            'topology_dimension':
                1
           }

        E.g. the mesh description for the UGRID mesh topology of point
             cells taken from ``cfdm.example_field(10)``. In this case
             the 'node_coordinates' Auxiliary Coordinates are
             explicitly defined by the point cell locations::

           {'attributes':
                {'edge_node_connectivity': [],
                 'node_coordinates': ['Mesh2_node_x', 'Mesh2_node_y'],
                 'node_node_connectivity': []},
            'node_coordinates':
                [<AuxiliaryCoordinate: longitude(7) degrees_east>,
                 <AuxiliaryCoordinate: latitude(7) degrees_north>],
            'node_node_connectivity':
                [<DomainTopology: cell:point(7, 5) >],
            'sorted_edges':
                {},
            'topology_dimension':
                0
           }

        More keys might get added later on by `_ugrid_update_mesh`.

        .. versionadded:: (cfdm) NEXTVERSION

        :Parameters:

            parent: `Field` or `Domain`
                The parent Field or Domain from which to create the
                mesh description.

        :Returns:

            (`str`, `dict`) or (`None`, `None`)
                The name of the netCDF mesh variable that will store
                the parent's UGRID mesh, and the mesh description
                itself. If the parent is not UGRID, then both are
                returned as `None`.

        """
        g = self.write_vars

        # Get the dictionary of normalised domain topology constructs
        domain_topologies = g["normalised_domain_topologies"]
        if not domain_topologies:
            # Not UGRID
            return None, None

        # Initialise the mesh description.
        #
        # This always includes the sub-dictionary 'attributes', which
        # contains the netCDF names of mesh-related variables; and the
        # sub-dictionary 'sorted_edges', which is a cache of the
        # sorted unique edges implied by the domain topologies.
        mesh = {"attributes": {}, "sorted_edges": {}}

        if len(domain_topologies) > 1:
            raise ValueError(
                f"Can't write a UGRID mesh for {parent!r} that has multiple "
                "domain topology constructs: "
                f"{tuple(domain_topologies.values())}"
            )

        # Get the UGRID domain axis
        key, domain_topology = domain_topologies.popitem()

        ugrid_axis = self.implementation.get_data_axes(parent, key)[0]

        # Get the dataset variable name of the domain topology
        # construct
        ncvar_cell_node_connectivity = g["key_to_ncvar"].get(key, [])
        if ncvar_cell_node_connectivity != []:
            ncvar_cell_node_connectivity = [ncvar_cell_node_connectivity]

        # Get the 1-d auxiliary coordinates that span the UGRID axis,
        # and their dataset variable names
        cell_coordinates = self.implementation.get_auxiliary_coordinates(
            parent, axes=(ugrid_axis,), exact=True
        )
        ncvar_cell_coordinates = [
            g["key_to_ncvar"][key] for key in cell_coordinates
        ]

        # ------------------------------------------------------------
        # Populate the output mesh description
        # ------------------------------------------------------------
        cell = domain_topology.get_cell(None)
        if cell == "point":
            mesh.update(
                {
                    "topology_dimension": 0,
                    "node_coordinates": list(cell_coordinates.values()),
                    "node_node_connectivity": [domain_topology],
                }
            )
            mesh["attributes"].update(
                {
                    "node_coordinates": ncvar_cell_coordinates,
                    "edge_node_connectivity": ncvar_cell_node_connectivity,
                    "node_node_connectivity": [],
                }
            )
        else:
            match cell:
                case "face":
                    topology_dimension = 2
                case "edge":
                    topology_dimension = 1
                case "volume":
                    topology_dimension = 3
                    # Placeholder exception to remind us to do some
                    # work, should volume cells ever make it into CF.
                    raise NotImplementedError(
                        "Can't write a UGRID mesh of volume cells for "
                        f"{parent!r}"
                    )
                case _:
                    raise ValueError(
                        f"{parent!r} has unknown domain topology cell type: "
                        f"{domain_topology!r}"
                    )

            node_coordinates = []
            index = None
            for key, c in cell_coordinates.items():
                bounds = c.get_bounds(None)
                if bounds is None or bounds.get_data(None) is None:
                    raise ValueError(
                        f"Can't write a UGRID mesh of {cell} cells for "
                        f"{parent!r} when {c!r} has no coordinate bounds data"
                    )

                if index is None:
                    # Create the array index that will extract, in the
                    # correct order, the node coordinates from the
                    # flattened cell bounds, i.e. so that the first
                    # node coordinate has node id 0, the second has
                    # node id 1, etc.
                    node_ids, index = np.unique(
                        domain_topology, return_index=True
                    )
                    if node_ids[-1] is np.ma.masked:
                        # Remove the element that corresponds to
                        # missing data (which is always at the end of
                        # the `np.unique` outputs)
                        index = index[:-1]

                # Create, from the cell bounds, an Auxiliary
                # Coordinate that contains the unique node
                # coordinates.
                coords = self.implementation.initialise_AuxiliaryCoordinate(
                    data=bounds.data.flatten()[index],
                    properties=c.properties(),
                )

                # Persist the node coordinates into memory, because
                # it's possible that we'll need to compare them more
                # than once with the node coordinates of other mesh
                # descriptions (in `_ugrid_linked_meshes`), in
                # addition to writing the coordinate themselves to
                # disk.
                coords.persist(inplace=True)

                node_coordinates.append(coords)

            del index

            mesh.update(
                {
                    "topology_dimension": topology_dimension,
                    "node_coordinates": node_coordinates,
                    f"{cell}_coordinates": list(cell_coordinates.values()),
                    f"{cell}_node_connectivity": [domain_topology],
                }
            )
            mesh["attributes"].update(
                {
                    f"{cell}_coordinates": ncvar_cell_coordinates,
                    f"{cell}_node_connectivity": ncvar_cell_node_connectivity,
                }
            )

        # Add mesh description keys for normalised cell connectivities
        for cc_key, cell_connectivity in g[
            "normalised_cell_connectivities"
        ].items():
            connectivity = cell_connectivity.get_connectivity(None)
            if not (
                (connectivity, cell) == ("edge", "face")
                or (connectivity, cell) == ("node", "edge")
                or (connectivity, cell) == ("face", "volume")
            ):
                raise ValueError(
                    f"{parent!r} has invalid UGRID cell connectivity type "
                    f"for {cell!r} cells: {cell_connectivity!r}"
                )

            key = f"{cell}_{cell}_connectivity"
            mesh[key] = [cell_connectivity]
            mesh["attributes"][key] = [g["key_to_ncvar"][cc_key]]

        # Get the dataset mesh variable name
        ncvar = parent.nc_get_mesh_variable("mesh")
        ncvar = self._name(ncvar)

        return ncvar, mesh

    def _ugrid_linked_meshes(self, mesh, mesh1):
        """Ascertain if two meshes are linked.

        Meshes are linked if they represent different locations of the
        same UGRID mesh.

        .. versionadded:: (cfdm) NEXTVERSION

        :Parameters:

            mesh: `dict`
                The two mesh dictionaries to be compared.

            mesh1: `dict`
                The two mesh dictionaries to be compared.

        :Returns:

            `bool`

        """
        # Find the relevant keys that are common to both meshes
        keys = (
            "node_coordinates",
            "edge_coordinates",
            "face_coordinates",
            "volume_coordinates",
            "node_node_connectivity",
            "edge_node_connectivity",
            "face_node_connectivity",
            "volume_node_connectivity",
            "edge_edge_connectivity",
            "face_face_connectivity",
            "volume_volume_connectivity",
        )
        common_keys = [k for k in keys if k in mesh and k in mesh1]

        # Check the common keys for equality
        #
        # A necessary condition for meshes being linked is that these
        # common keys have identical values.
        for key in common_keys:
            if len(mesh[key]) != len(mesh1[key]):
                # Different numbers of constructs for the same key =>
                # the meshes are not linked
                return False

            mesh1_key = mesh1[key][:]
            for c in mesh[key]:
                found_match = False
                for i, c1 in enumerate(mesh1_key):
                    if c.equals(c1):
                        # Matching construct pair
                        found_match = True
                        mesh1_key.pop(i)
                        break

                if not found_match:
                    # A 'mesh1' construct is different to all those in
                    # 'mesh' => the meshes are not linked
                    return False

        # Still here? Then all of the keys common to both meshes have
        # equal values.

        # Now check the non-common connectivity keys for consistency
        # (as opposed to equality)
        locations = ("edge", "node", "face", "volume")
        location_mesh = {}
        for location in locations:
            key = f"{location}_node_connectivity"
            if key in common_keys:
                continue

            if key in mesh1:
                location_mesh[location] = mesh1
                break

        for location in locations:
            key = f"{location}_node_connectivity"
            if key in common_keys or key in location_mesh:
                continue

            if key in mesh:
                location_mesh[location] = mesh
                break

        if len(location_mesh) == 2:
            # 'location_mesh' has two keys, one for each mesh, and
            # each key represents a domain topology that is not
            # present in the other mesh.
            #
            # Each pair of domain topology cell types needs special
            # treatment.
            if set(location_mesh) == set(("edge", "face")):
                if not self._ugrid_check_edge_face(**location_mesh):
                    return False

            elif set(location_mesh) == set(("node", "edge")):
                if not self._ugrid_check_node_edge(**location_mesh):
                    return False

            elif set(location_mesh) == set(("node", "face")):
                if not self._ugrid_check_node_face(**location_mesh):
                    return False

            elif "volume" in location_mesh:
                # Placeholder exception to remind us to do some work,
                # should volume cells ever make it into CF.
                raise NotImplementedError(
                    "Can't write a UGRID mesh of volume cells"
                )

        # Still here? Then 'mesh' and 'mesh1' are parts of the same
        # uber-mesh.
        return True

    def _ugrid_check_node_edge(self, node=None, edge=None):
        """Whether or not nodes imply edges, and vice versa.

        .. versionadded:: (cfdm) NEXTVERSION

        :Parameters:

            node: `dict`
                The mesh dictionary of the nodes.

            edge: `dict`
                The mesh dictionary of the edges.

        :Returns:

            `bool`
                The result.

        """
        # Find the set of unique edges that are implied by the nodes
        node_edges = node["sorted_edges"].get("node_node_connectivity")
        if node_edges is None:
            node_edges = node["node_node_connectivity"][0].to_edge(sort=True)
            node["sorted_edges"]["node_node_connectivity"] = node_edges
            node["sorted_edges"]["edge_node_connectivity"] = node_edges

        edges = edge["sorted_edges"].get("edge_node_connectivity")
        if edges is None:
            edges = edge["edge_node_connectivity"][0].sort()
            edge["sorted_edges"]["edge_node_connectivity"] = edges

        # Return True if the unique edges of the faces are identical
        # to the given edges
        if node_edges.data.shape != edges.data.shape:
            return False

        return bool((node_edges.data == edges.data).all())

    def _ugrid_check_edge_face(self, edge=None, face=None):
        """Whether or not edges imply faces, and vice versa.

        .. versionadded:: (cfdm) NEXTVERSION

        :Parameters:

            edge: `dict`
                The mesh dictionary of the edges.

            face: `dict`
                The mesh dictionary of the faces.

        :Returns:

            `bool`
                The result.

        """
        # Fast checks that are sufficient (but not necessary)
        # conditions for the edges and faces being incompatible
        edges = edge["edge_node_connectivity"][0]
        faces = face["face_node_connectivity"][0]
        if edges.size > faces.data.size:
            # There are more edges than the maximum that could be
            # defined by the faces
            return False

        if edges.size < faces.size + 2:
            # There are fewer edges than the minimum that could be
            # defined by the faces
            return False

        # Still here?
        edges = edge["sorted_edges"].get("edge_node_connectivity")
        if edges is None:
            edges = edge["edge_node_connectivity"][0].sort()
            edge["sorted_edges"]["edge_node_connectivity"] = edges

        # Find the set of unique edges that are implied by the faces
        face_edges = face["sorted_edges"].get("face_node_connectivity")
        if face_edges is None:
            n_nodes = face["node_coordinates"][0].size
            face_edges = face["face_node_connectivity"][0].to_edge(
                sort=True, face_nodes=range(n_nodes)
            )
            face["sorted_edges"]["face_node_connectivity"] = face_edges
            face["sorted_edges"]["edge_node_connectivity"] = face_edges

        # Return True if the unique edges of the faces are identical
        # to the given edges
        if face_edges.data.shape != edges.data.shape:
            return False

        return bool((face_edges.data == edges.data).all())

    def _ugrid_check_node_face(self, node=None, face=None):
        """Whether or not nodes imply faces, and vice versa.

        .. versionadded:: (cfdm) NEXTVERSION

        :Parameters:

            node: `dict`
                The mesh dictionary of the nodes.

            face: `dict`
                The mesh dictionary of the faces.

        :Returns:

            `bool`
                The result.

        """
        # Find the set of unique edges that are implied by the nodes
        node_edges = node["sorted_edges"].get("node_node_connectivity")
        if node_edges is None:
            node_edges = node["node_node_connectivity"][0].to_edge(sort=True)
            node["sorted_edges"]["node_node_connectivity"] = node_edges
            node["sorted_edges"]["edge_node_connectivity"] = node_edges

        # Find the set of unique edges that are implied by the faces
        face_edges = face["sorted_edges"].get("face_node_connectivity")
        if face_edges is None:
            n_nodes = face["node_coordinates"][0].size
            face_edges = face["face_node_connectivity"][0].to_edge(
                face_nodes=range(n_nodes), sort=True
            )
            face["sorted_edges"]["face_node_connectivity"] = face_edges
            face["sorted_edges"]["edge_node_connectivity"] = face_edges

        # Return True if the unique edges of the faces are identical
        # to the given edges
        if face_edges.data.shape != node_edges.data.shape:
            return False

        return bool((face_edges.data == node_edges.data).all())

    def _ugrid_update_mesh(self, mesh, mesh1):
        """Update an original mesh with a linked mesh.

        Elements of the linked mesh which are not in the original mesh
        are copied to the original mesh.

        The `_ugrid_linked_meshes` method is used to ascertain if two
        meshes are linked.

        .. versionadded:: (cfdm) NEXTVERSION

        :Parameters:

            mesh: `dict`
                The original mesh to be updated in-place. If `mesh`
                and `mesh1` are identical then `mesh` is unchanged.

            mesh1: `dict`
                The linked mesh to update from.

        :Returns:

            `None`

        """
        # Update the topology dimension
        mesh["topology_dimension"] = max(
            mesh["topology_dimension"], mesh1["topology_dimension"]
        )

        for key, value in mesh1.items():
            if key not in mesh:
                # This 'mesh1' key is not in 'mesh', so copy it from
                # 'mesh1'.
                #
                # Note: any such key will always have a `list` value.
                mesh[key] = value.copy()
                mesh["attributes"][key] = mesh1["attributes"][key].copy()

        for key, value in mesh1["sorted_edges"].items():
            if key not in mesh["sorted_edges"]:
                # This mesh1["sorted_edges"] key is not in
                # mesh["sorted_edges"], so copy it from
                # mesh1["sorted_edges"].
                #
                # Note: any such key will always have a
                # `DomainTopology` value.
                mesh["sorted_edges"][key] = value.copy()

        # If applicable, make sure that the node coordinates and their
        # netCDF variable names are defined by the point-cell domain,
        # rather than being inferred by one of the
        # edge/face/volume-cell domains.
        if "node_node_connectivity" in mesh1:
            key = "node_coordinates"
            mesh[key] = mesh1[key].copy()
            mesh["attributes"][key] = mesh1["attributes"][key].copy()

    def _ugrid_write_mesh_variables(self):
        """Write mesh variables to the dataset.

        This is done after all Fields and Domains have been written to
        the dataset.

        All UGRID CF-netCDF data and domain variables in the dataset
        will already have the correct mesh variable name stored in
        their 'mesh' attributes.

        The mesh variables are defined by `self.write_vars['meshes']`.

        .. versionadded:: (cfdm) NEXTVERSION

        :Returns:

            `None`

        """
        g = self.write_vars

        for mesh_ncvar, mesh in g["meshes"].items():
            # --------------------------------------------------------
            # Create the mesh variable attributes.
            #
            # E.g. the 'mesh' dictionary
            #
            # {'attributes':
            #      {'face_coordinates': ['Mesh2_face_x', 'Mesh2_face_y'],
            #       'face_face_connectivity': ['Mesh2_face_links'],
            #       'face_node_connectivity': ['Mesh2_face_nodes']},
            #  'topology_dimension':
            #      2,
            #  'face_coordinates':
            #      [<AuxiliaryCoordinate: longitude(3) degrees_east>,
            #       <AuxiliaryCoordinate: latitude(3) degrees_north>],
            #  'face_node_connectivity':
            #      [<DomainTopology: cell:face(3, 4) >],
            #  'node_coordinates':
            #      [<AuxiliaryCoordinate: longitude(7) degrees_east>,
            #       <AuxiliaryCoordinate: latitude(7) degrees_north>]}
            #
            # could give mesh variable attributes:
            #
            # {'topology_dimension': 2,
            #  'node_coordinates': 'longitude latitude',
            #  'face_coordinates': 'Mesh2_face_x Mesh2_face_y',
            #  'face_node_connectivity': 'Mesh2_face_nodes'}
            # --------------------------------------------------------
            attributes = {
                "cf_role": "mesh_topology",
                "topology_dimension": mesh["topology_dimension"],
            }

            # Convert non-empty lists of constructs to a
            # space-separated dataset variable name string
            #
            # E.g. [<construct>] -> 'Mesh2_face_links'
            # E.g. [<construct>, <construct>] -> 'x y'
            for key, value in mesh["attributes"].items():
                if value:
                    attributes[key] = " ".join(value)

            # If the dataset variable names for the node coordinates
            # (which have to exist for all meshes) have not been
            # defined, then it's because the node coordinates have not
            # yet been written to the dataset (which in turn is
            # because there were no node-location field or domain
            # constructs being written). So, let's write them now, and
            # get their variable names.
            if "node_coordinates" not in attributes:
                # Create a new node dimension in the same group as the
                # mesh variable
                ncdim = "nodes"
                mesh_group = self._groups(mesh_ncvar)
                if mesh_group:
                    ncdim = mesh_group + ncdim

                n_nodes = mesh["node_coordinates"][0].size
                ncdim = self._name(ncdim, dimsize=n_nodes, role="nodes")
                if ncdim not in g["ncdim_to_size"]:
                    self._write_dimension(ncdim, None, size=n_nodes)

                # Write the node coordinates to the dataset
                ncvars = [
                    self._ugrid_write_node_coordinate(nc, (ncdim,))
                    for nc in mesh["node_coordinates"]
                ]
                attributes["node_coordinates"] = " ".join(ncvars)

            # For a point-cell domain topology
            # (i.e. 'topology_dimension' is currently 0), write the
            # implied edge_node_connectivity variable to the dataset.
            if not mesh["topology_dimension"]:
                edges = mesh["sorted_edges"].get("node_node_connectivity")
                if edges is None:
                    edges = mesh["node_node_connectivity"][0].to_edge(
                        sort=True
                    )

                ncvar = self._ugrid_write_domain_topology(None, None, edges)
                if ncvar is not None:
                    attributes["edge_node_connectivity"] = ncvar

                    # Set topology dimension to 1, now that we've
                    # included an edge_node_connectivity.
                    attributes["topology_dimension"] = 1

            # --------------------------------------------------------
            # Create the mesh variable and set its attributes
            # --------------------------------------------------------
            logger.debug(
                f"    Writing UGRID mesh variable: {mesh_ncvar}\n"
                f"        {mesh}"
            )  # pragma: no cover

            kwargs = {
                "varname": mesh_ncvar,
                "datatype": "S1",
                "endian": g["endian"],
            }
            kwargs.update(g["netcdf_compression"])

            self._createVariable(**kwargs)
            self._set_attributes(attributes, mesh_ncvar)
