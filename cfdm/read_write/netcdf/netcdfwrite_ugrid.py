import logging

import numpy as np

logger = logging.getLogger(__name__)


class NetCDFWriteUrid:
    """Mixin class for writing UGRID meshes to a dataset.

    .. versionadded: (cfdm) NEXTVERSION

    """

    def _write_domain_topology(self, parent, key, domain_topology):
        """Write a domain topology to a *_node_connectivity variable.

        If an equal domain topology has already been written to the
        dataset then it is not re-written.

        .. versionadded: (cfdm) NEXTVERSION

        :Parameters:

            parent : `Field` or `Domain`
                The parent Field or Domain.

            key : `str`
                The internal identifier of the domain topology
                construct.

            domain_topology : `DomainTopology`
                The Domain Topology construct to be written.

        :Returns:

            `str` or `None`
                The dataset variable name of the domain topology
                object, or `None` if one wasn't written.

        **Examples**

        >>> ncvar = _write_domain_topology(f, 'domaintopology0', dt)

        """
        from cfdm.functions import integer_dtype

        g = self.write_vars

        # Normalise the array, so that its N node ids are 0, ..., N-1
        domain_topology.normalise(inplace=True)
        g["domain_topologies"][key] = domain_topology

        cell = domain_topology.get_cell(None)
        if cell == "point":
            # There's no corresponding UGRID variable for "point"
            # cells, so just return.
            return None

        if cell == "volume":
            # Placeholder exception to remind us to do some work,
            # should volume cells ever make it into CF.
            raise NotImplementedError(
                "Can't write a UGRID mesh of volume cells for {parent!r}"
            )
            
        if cell not in ("face", "edge"):
            raise ValueError(
                f"{parent!r} has unknown domain topology cell type: "
                f"{domain_topology!r}"
            )
                    
        # Get the netCDF dimensions
        size = domain_topology.data.shape[-1]
        ncdimensions = self._dataset_dimensions(parent, key, domain_topology)
        connectivity_ncdim = domain_topology.nc_get_connectivity_dimension(
            f"connectivity{size}"
        )
        connectivity_ncdim = self._name(
            connectivity_ncdim, dimsize=size, role="ugrid_connectivity"
        )
        ncdimensions = ncdimensions + (connectivity_ncdim,)

        if self._already_in_file(domain_topology, ncdimensions):
            # This domain topology variable has been previously
            # created, so no need to do so again.
            ncvar = g["seen"][id(domain_topology)]["ncvar"]
        else:
            # This domain topology variable has not been previously
            # created, so create it now.
            if connectivity_ncdim not in g["ncdim_to_size"]:
                self._write_dimension(connectivity_ncdim, parent, size=size)

            ncvar = self._create_variable_name(
                domain_topology, default=f"{cell}_node_connectivity"
            )

            # Write as 32-bit integers if possible
            dtype = integer_dtype(domain_topology.data.size)
            domain_topology.data.dtype = dtype

            self._write_netcdf_variable(
                ncvar,
                ncdimensions,
                domain_topology,
                self.implementation.get_data_axes(parent, key),
            )

        g["key_to_ncvar"][key] = ncvar
        g["key_to_ncdims"][key] = ncdimensions

        return ncvar

    def _write_cell_connectivity(self, f, key, cell_connectivity):
        """Write a cell connectivity to a *_*_connectivity variable.

        If an equal cell connectivity has already been written to the
        dataset then it is not re-written.

        .. versionadded: (cfdm) NEXTVERSION

        :Parameters:

            f : `Field` or `Domain`
                The parent Field or Domain.

            key : `str`
                The internal identifier of the cell connectivity
                construct.

            cell_connectivity : `CellConnectivity`
                The Cell Connectivity construct to be written.

        :Returns:

            `str`
                The dataset variable name of the cell connectivity
                object.

        **Examples**

        >>> ncvar = _write_cell_connectivity(f, 'cellconnectivity0', cc)

        """
        from cfdm.functions import integer_dtype

        g = self.write_vars

        # Normalise the array, so that its N cell ids are 0, ..., N-1
        cell_connectivity.normalise(inplace=True)
        g["cell_connectivities"][key] = cell_connectivity

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
            ncvar = self._create_variable_name(node_coord,
                                               default="node_coordinates")

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
                 The prent Field or Domain from which to get the mesh
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
                # change to the other paren't mesh.
                self._ugrid_update_mesh(mesh, mesh_new)
                return ncvar

        # Still here? Then this parent's UGRID mesh is not the same
        # as, nor linked to, any other parent's mesh, so we save save
        # it as a new mesh.
        g["meshes"][ncvar_new] = mesh_new

        return ncvar_new

    def _ugrid_create_mesh(self, parent):
        """Create a mesh description from a parent Field or Daomin.

        The mesh description is a dictionary with some subset of the
        following keys::

           'attributes'
           'topology_dimension'
           'node_coordinates'
           'edge_coordinates'
           'face_coordinates'
           'volume_coordinates'
           'edge_node_connectivity'
           'face_node_connectivity'
           'volume_node_connectivity'
           'edge_edge_connectivity'
           'face_face_connectivity'
           'volume_volume_connectivity'

        of which 'attributes', 'topology_dimension', and
        'node_coordinates' will always be present.

        E.g. the mesh description for the UGRID mesh topology of face
             cells taken from ``cfdm.example_field(8)``::

           {'attributes':
                {'face_coordinates': ['Mesh2_face_x', 'Mesh2_face_y'],
                 'face_face_connectivity': ['Mesh2_face_links'],
                 'face_node_connectivity': ['Mesh2_face_nodes']},
            'topology_dimension':
                2,
            'node_coordinates':
                [<AuxiliaryCoordinate: longitude(7) degrees_east>,
                 <AuxiliaryCoordinate: latitude(7) degrees_north>],
            'face_coordinates':
                [<AuxiliaryCoordinate: longitude(3) degrees_east>,
                 <AuxiliaryCoordinate: latitude(3) degrees_north>],
            'face_node_connectivity':
                [<DomainTopology: cell:face(3, 4)>]}
            'face_face_connectivity':
                [<CellConnectivity: connectivity:edge(3, 5)>]}

        E.g. the mesh description for the UGRID mesh topology of edge
             cells taken from ``cfdm.example_field(9)``::

           {'attributes':
                {'edge_coordinates': ['Mesh2_edge_x', 'Mesh2_edge_y'],
                 'edge_node_connectivity': ['Mesh2_edge_nodes']},
            'topology_dimension':
                1,
            'node_coordinates':
                [<AuxiliaryCoordinate: longitude(7) degrees_east>,
                 <AuxiliaryCoordinate: latitude(7) degrees_north>],
            'edge_coordinates':
                [<AuxiliaryCoordinate: longitude(9) degrees_east>,
                 <AuxiliaryCoordinate: latitude(9) degrees_north>],
            'edge_node_connectivity':
                [<DomainTopology: cell:point(9, 6)>]}

        E.g. the mesh description for the UGRID mesh topology of point
             cells taken from ``cfdm.example_field(10)``::

           {'attributes':
                {'node_coordinates': ['Mesh2_node_x', 'Mesh2_node_y'],
                 'edge_node_connectivity': ['Mesh2_edge_nodes']},
            'topology_dimension':
                0,
            'node_coordinates':
                [<AuxiliaryCoordinate: longitude(7) degrees_east>,
                 <AuxiliaryCoordinate: latitude(7) degrees_north>],
            'edge_node_connectivity':
                [<DomainTopology: cell:point(7, 5)>]}

        Later on, more keys might get added by `_ugrid_update_mesh`.

        .. versionadded:: (cfdm) NEXTVERSION

        :Parameters:

            parent: `Field` or `Domain`
                 The prent Field or Domain for which to create the
                 mesh description.

        :Returns:

            (`str`, `dict`) or (`None`, `None`)
                The name of the netCDF mesh variable that will store
                the parent's UGRID mesh, and the mesh description
                itself. If the parent is not UGRID, then both are
                returned as `None`.

        """
        g = self.write_vars

        # Get the dictionary of *normalised* domain topology
        # constructs
        domain_topologies = g["domain_topologies"]
        if not domain_topologies:
            # Not UGRID
            return None, None

        # Initialise the output mesh description
        mesh = {"attributes": {}}

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
            ncvar_cell_node_connectivity = [ ncvar_cell_node_connectivity ]
            
        # Get the 1-d auxiliary coordinates that span the UGID axis,
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
                #
                # Persist the node coordinates into memory because
                # it's likely that we'll need to compare them with the
                # node coordinates of other mesh descriptions (in
                # `ugrid_linked_meshes`).
                coords = self.implementation.initialise_AuxiliaryCoordinate(
                    data=bounds.data.flatten()[index],
                    properties=c.properties(),
                )
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
        for cc_key, cell_connectivity in g["cell_connectivities"].items():
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
        """TODOUGRID.

        .. versionadded:: (cfdm) NEXTVERSION

        :Returns:

            `bool`

        """
        # Find the keys that are common to both meshes
        keys = [
            "node_coordinates",
            "edge_coordinates",
            "face_coordinates",
            "volume_coordinates",
            "edge_node_connectivity",
            "face_node_connectivity",
            "volume_node_connectivity",
            "edge_edge_connectivity",
            "face_face_connectivity",
            "volume_volume_connectivity",
        ]
        keys = [k for k in keys if k in mesh and k in mesh1]

        # Check the common keys for equality
        for key in keys:
            if len(mesh[key]) != len(mesh1[key]):
                # Different numbers of constructs, so the meshes are
                # not linked
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
                    # No constructs match, so the meshes are not
                    # linked
                    return False

        # Still here? Then all of the keys common to both meshes are
        # the same. Now check the non-common keys for consistency.
        #
        # If the two meshes have different types of domain topolgies
        # (e.g. edge and face), then check that each one implies the
        # other.
        for cell in ("face", "node"):
            edges = mesh.get("edge_node_connectivity")
            cells = mesh.get(f"{cell}_node_connectivity")
            if edges and cells:
                # Already got both cell types
                continue
            
            if edges and not cells:
                cells = mesh1.get(f"{cell}_node_connectivity")
            elif cells and not edges:
                edges = mesh1.get("edge_node_connectivity")
                
            if edges and cells:
                # 'face_node_connectivity' and
                # 'edge_node_connectivity' are defined in the separate
                # meshes, so check them for consistency.
                n_nodes = mesh["node_coordinates"][0].size
                if not self._ugrid_check_edges(
                        "cell", n_nodes, edges[0], cells[0]
                ):
                    return False
                
        
        edges = mesh.get("edge_node_connectivity")
        faces = mesh.get("face_node_connectivity")
        if not (edges and faces):
            if edges and not faces:
                faces = mesh1.get("face_node_connectivity")
            elif faces and not edges:
                edges = mesh1.get("edge_node_connectivity")

            if edges and faces:
                # 'face_node_connectivity' and
                # 'edge_node_connectivity' are defined in the separate
                # meshes, so check them for consistency.
                n_nodes = mesh["node_coordinates"][0].size
                if not self._ugrid_check_edges_and_faces(
                    n_nodes, edges[0], faces[0]
                ):
                    return False

        # If the two meshes have different types of domain topolgies
        # (e.g. edge and face), then check that each one implies the
        # other.
        edges = mesh.get("edge_node_connectivity")
        points = mesh.get("node_node_connectivity")
        if not (edges and points):
            if edges and not points:
                points = mesh1.get("node_node_connectivity")
            elif nodes and not edges:
                edges = mesh1.get("edge_node_connectivity")

            if (edges
                and points
                and not self._ugrid_check_edges_and_points(
                    edges[0], points[0])
                ):
                    return False

        # If the two meshes have different types of domain topolgies
        # (e.g. edge and face), then check that each one implies the
        # other.
        faces = mesh.get("face_node_connectivity")
        points = mesh.get("node_node_connectivity")
        if not (faces and points):
            if faces and not nodes:
                points = mesh1.get("node_node_connectivity")
            elif nodes and not faces:
                faces = mesh1.get("face_node_connectivity")

            if faces and points:
                n_nodes = mesh["node_coordinates"][0].size
                if not self._ugrid_check_points_and_faces(
                    n_nodes, edges[0], points[0]
                ):
                    return False

        volumes = mesh.get("volume_node_connectivity")
        if volumes:
            # Placeholder exception to remind us to do some work,
            # should volume cells ever make it into CF.
            raise NotImplementedError(
                "Can't write a UGRID mesh of volume cells"
            )

        # Still here? Then 'mesh' and 'mesh1' are part of the same
        # uber-mesh.
        return True

    def _ugrid_check_edges_and_faces(
        self, n_nodes, edge_node_connectivity, face_node_connectivity
    ):
        """Whether or not edges imply faces, and vice versa.

        .. versionadded:: (cfdm) NEXTVERSION

        :Parameters:

            n_node: `int`
                The number of unique nodes.

            edge_node_connectivity: `DomainTopology`
                The "edge" domain topology.

            face_node_connectivity: `DomainTopology`
                The "face" domain topology.

        :Returns:

            `bool`
                True if the edges imply the faces, and the faces imply
                the edges.

        """
        # Fast checks that are sufficient (but not necessary)
        # conditions for the edges and faces being incompatible
        if edge_node_connectivity.size > face_node_connectivity.data.size:
            # There are more given edges than can possibly by defined
            # by the faces
            return False

        if edge_node_connectivity.size < face_node_connectivity.size + 2:
            # There are fewer given edges than can possibly by defined
            # by the faces
            return False

        # Still here? Find the set of unique edges that are implied by
        # the faces
        face_edges = face_node_connectivity.to_edge(
            nodes=range(n_nodes), sort=True
        )
        edges = edge_node_connectivity.sort(inplace=False)

        # Return True if the unique edges of the faces are identical
        # to the given edges
        if face_edges.data.shape != edges.data.shape:
            return False
        
        return bool((face_edges.data == edges.data).all())

    def _ugrid_check_edges_and_points(
        self, edge_node_connectivity, node_node_connectivity
    ):
        """Whether or not edges imply nodes, and vice versa.

        .. versionadded:: (cfdm) NEXTVERSION

        :Parameters:

            edge_node_connectivity: `DomainTopology`
                The "edge" domain topology.

            node_node_connectivity: `DomainTopology`
                The "point" domain topology.

        :Returns:

            `bool`
                True if the edges imply the nodes, and the nodes imply
                the edges.

        """
        # Find the set of unique edges that are implied by the nodes
        point_edges = node_node_connectivity.to_edge(sort=True)
        edges = edge_node_connectivity.sort(inplace=False)

        # Return True if the unique edges of the faces are identical
        # to the given edges
        if node_edges.data.shape != edges.data.shape:
            return False
        
        return bool((node_edges.data == edges.data).all())

    def _ugrid_update_mesh(self, mesh, mesh1):
        """Update mesh wit h a linked mesh TODOUGRID.

        .. versionadded:: (cfdm) NEXTVERSION

        :Returns:

            `None`

        """
        mesh["topology_dimension"] = max(
            mesh["topology_dimension"], mesh1["topology_dimension"]
        )

        for key, value in mesh1.items():
            if key not in mesh:
                # This key is not in for 'mesh', so copy it from
                # 'mesh1'. Note: any such key will have a `list`
                # value.
                mesh[key] = value.copy()
                mesh["attributes"][key] = mesh1["attributes"][key].copy()

        key = 'node_coordinates'        
        if  key in mesh1["attributes"] and key not in mesh["attributes"]:
            mesh["attributes"][key] = mesh1["attributes"][key].copy()
              
    def _ugrid_write_mesh_variables(self):
        """Write any mesh variables to the dataset.

        This is done after all Fields and Domains have been written to
        the dataset.

        All CF data and domain variables in the dataset already have
        the correct mesh varibale name stored in their 'mesh'
        attributes.

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
            # E.g. internal mesh dictionary
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
            #       <AuxiliaryCoordinate: latitude(7) degrees_north>]
            #  }
            #
            # could give dataset variable attributes:
            #
            # {'topology_dimension': 2,
            #  'node_coordinates': 'longitude latitude',
            #  'face_coordinates': 'Mesh2_face_x Mesh2_face_y',
            #  'face_node_connectivity': 'Mesh2_face_nodes'}
            # --------------------------------------------------------
            attributes = {"topology_dimension": mesh["topology_dimension"]}

            # Convert non-empty lists of constructs to space-separated
            # variable names
            #
            # E.g. [<construct>] -> 'Mesh2_face_links'
            # E.g. [<construct>, <construct>] -> 'x y'
            for key, value in mesh["attributes"].items():
                if value:
                    attributes[key] = " ".join(value)

            # If the dataset variable names for node coordinates have
            # not been defined, then it's because the node coordinates
            # have not yet been written to the dataset (which in turn
            # is because there were no node-location field or domain
            # constructs being written). So let's write them now, and
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
