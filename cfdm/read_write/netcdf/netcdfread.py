import logging
import operator
import os
import re
import struct
import subprocess
import tempfile
from ast import literal_eval
from copy import deepcopy
from dataclasses import dataclass, field
from functools import reduce
from math import nan
from typing import Any
from urllib.parse import urlparse
from uuid import uuid4

import netCDF4
import netcdf_flattener
import numpy
import numpy as np
from packaging.version import Version

from ...decorators import _manage_log_level_via_verbosity
from ...functions import is_log_level_debug
from .. import IORead

logger = logging.getLogger(__name__)

_cached_temporary_files = {}

_flattener_separator = netcdf_flattener._Flattener._Flattener__new_separator


@dataclass()
class Mesh:
    """A UGRID mesh defintion.

    .. versionadded:: (cfdm) UGRIDVER

    """

    # The netCDF name of the mesh topology variable. E.g. 'Mesh2d'
    mesh_ncvar: Any = None
    # The attributes of the netCDF mesh topology variable.
    # E.g. {'cf_role': 'mesh_topology'}
    mesh_attributes: dict = field(default_factory=dict)
    # The netCDF variable names of the coordinates for each location
    # E.g. {'node': ['node_lat', 'node_lon']}
    coordinates_ncvar: dict = field(default_factory=dict)
    # The netCDF name of the location index set variable.
    # E.g. 'Mesh1_set'
    location_index_set_ncvar: Any = None
    # The attributes of the location index set variable.
    # E.g. {'location': 'node'}
    location_index_set_attributes: dict = field(default_factory=dict)
    # The location of the location index set. E.g. 'edge'
    location: Any = None
    # The zero-based indices of the location index set.
    # E.g. <CF Data(13243): >
    index_set: Any = None
    # The domain topology construct for each location.
    # E.g. {'face': <CF DomainTopology(13243, 4) >}
    domain_topologies: dict = field(default_factory=dict)
    # Cell connectivity constructs for each location.
    # E.g. {'face': [<CF CellConnectivity(13243, 4) >]}
    cell_connectivities: dict = field(default_factory=dict)
    # Auxiliary coordinate constructs for each location.
    # E.g. {'face': [<CF AxuxiliaryCoordinate(13243) >,
    #                <CF AxuxiliaryCoordinate(13243) >]}
    auxiliary_coordinates: dict = field(default_factory=dict)
    # The netCDF dimension spanned by the cells for each
    # location. E.g. {'node': 'nNodes', 'edge': 'nEdges'}
    ncdim: dict = field(default_factory=dict)
    # A unique identifier for the mesh. E.g. 'df10184d806ef1a10f5035e'
    mesh_id: Any = None


class NetCDFRead(IORead):
    """A container for instantiating Fields from a netCDF dataset."""

    _code0 = {
        # Physically meaningful and corresponding to constructs
        "Cell measures variable": 100,
        "cell_measures attribute": 101,
        "Bounds variable": 200,
        "bounds attribute": 201,
        "Ancillary variable": 120,
        "ancillary_variables attribute": 121,
        "Formula terms variable": 130,
        "formula_terms attribute": 131,
        "Bounds formula terms variable": 132,
        "Bounds formula_terms attribute": 133,
        "Auxiliary/scalar coordinate variable": 140,
        "coordinates attribute": 141,
        "Grid mapping variable": 150,
        "grid_mapping attribute": 151,
        "Grid mapping coordinate variable": 152,
        "Cell method interval": 160,
        "External variable": 170,
        "Geometry variable": 180,
        "geometry attribute": 181,
        "Node coordinate variable": 190,
        "Tie points coordinate variable": 200,
        "Bounds tie points variable": 201,
        # Purely structural
        "Compressed dimension": 300,
        "compress attribute": 301,
        "Instance dimension": 310,
        "instance_dimension attribute": 311,
        "Count dimension": 320,
        "count_dimension attribute": 321,
    }

    _code1 = {
        "is incorrectly formatted": 2,
        "is not in file": 3,
        "spans incorrect dimensions": 4,
        (
            "is not in file nor referenced by the external_variables global "
            "attribute"
        ): 5,
        "has incompatible terms": 6,
        "that spans the vertical dimension has no bounds": 7,
        (
            "that does not span the vertical dimension is inconsistent with "
            "the formula_terms of the parametric coordinate variable"
        ): 8,
        "is not referenced in file": 9,
        "exists in the file": 10,
        "does not exist in file": 11,
        "exists in multiple external files": 12,
        "has incorrect size": 13,
        "is missing": 14,
        "is not used by data variable": 15,
        "not in node_coordinates": 16,
        "is not locatable in the group hierarchy": 17,
    }

    def cf_datum_parameters(self):
        """Datum-defining parameters names."""
        return (
            "earth_radius",
            "geographic_crs_name",
            "geoid_name",
            "geopotential_datum_name",
            "horizontal_datum_name",
            "inverse_flattening",
            "longitude_of_prime_meridian",
            "prime_meridian_name",
            "reference_ellipsoid_name",
            "semi_major_axis",
            "semi_minor_axis",
            "towgs84",
        )

    def cf_coordinate_reference_coordinates(self):
        """Maps canonical names to applicable coordinates.

        Specifically it is a mapping of each coordinate reference
        canonical name to the coordinates to which it applies. The
        coordinates are defined by their standard names.

        A coordinate reference canonical name is either the value of
        the grid_mapping_name attribute of a grid mapping variable
        (e.g.  'lambert_azimuthal_equal_area'), or the standard name
        of a vertical coordinate variable with a formula_terms
        attribute (e.g. 'ocean_sigma_coordinate').

        """
        return {
            "albers_conical_equal_area": (
                "projection_x_coordinate",
                "projection_y_coordinate",
                "latitude",
                "longitude",
            ),
            "azimuthal_equidistant": (
                "projection_x_coordinate",
                "projection_y_coordinate",
                "latitude",
                "longitude",
            ),
            "geostationary": (
                "projection_x_coordinate",
                "projection_y_coordinate",
                "latitude",
                "longitude",
            ),
            "lambert_azimuthal_equal_area": (
                "projection_x_coordinate",
                "projection_y_coordinate",
                "latitude",
                "longitude",
            ),
            "lambert_conformal_conic": (
                "projection_x_coordinate",
                "projection_y_coordinate",
                "latitude",
                "longitude",
            ),
            "lambert_cylindrical_equal_area": (
                "projection_x_coordinate",
                "projection_y_coordinate",
                "latitude",
                "longitude",
            ),
            "latitude_longitude": ("latitude", "longitude"),
            "mercator": (
                "projection_x_coordinate",
                "projection_y_coordinate",
                "latitude",
                "longitude",
            ),
            "orthographic": (
                "projection_x_coordinate",
                "projection_y_coordinate",
                "latitude",
                "longitude",
            ),
            "polar_stereographic": (
                "projection_x_coordinate",
                "projection_y_coordinate",
                "latitude",
                "longitude",
            ),
            "rotated_latitude_longitude": (
                "grid_latitude",
                "grid_longitude",
                "latitude",
                "longitude",
            ),
            "sinusoidal": (
                "projection_x_coordinate",
                "projection_y_coordinate",
                "latitude",
                "longitude",
            ),
            "stereographic": (
                "projection_x_coordinate",
                "projection_y_coordinate",
                "latitude",
                "longitude",
            ),
            "transverse_mercator": (
                "projection_x_coordinate",
                "projection_y_coordinate",
                "latitude",
                "longitude",
            ),
            "vertical_perspective": (
                "projection_x_coordinate",
                "projection_y_coordinate",
                "latitude",
                "longitude",
            ),
            "atmosphere_ln_pressure_coordinate": (
                "atmosphere_ln_pressure_coordinate",
            ),
            "atmosphere_sigma_coordinate": ("atmosphere_sigma_coordinate",),
            "atmosphere_hybrid_sigma_pressure_coordinate": (
                "atmosphere_hybrid_sigma_pressure_coordinate",
            ),
            "atmosphere_hybrid_height_coordinate": (
                "atmosphere_hybrid_height_coordinate",
            ),
            "atmosphere_sleve_coordinate": ("atmosphere_sleve_coordinate",),
            "ocean_sigma_coordinate": ("ocean_sigma_coordinate",),
            "ocean_s_coordinate": ("ocean_s_coordinate",),
            "ocean_sigma_z_coordinate": ("ocean_sigma_z_coordinate",),
            "ocean_double_sigma_coordinate": (
                "ocean_double_sigma_coordinate",
            ),
        }

    def cf_interpolation_names(self):
        """Interpolation method names.

        These are the allowed values of the ``interpolation_name``
        attribute of an interpolation variable.

        .. versionadded:: (cfdm) 1.10.0.0

        """
        return (
            "linear",
            "bi_linear",
            "quadratic",
            "quadratic_latitude_longitude",
            "bi_quadratic_latitude_longitude",
        )

    def cf_multivariate_interpolations(self):
        """The multivariate interpolation methods.

        .. versionadded:: (cfdm) 1.10.0.0

        :Returns:

            `dict`
               The subset of standardised interpolation methods that
               are multivariate, and the identities of their
               variables.

        """
        return {
            "quadratic_latitude_longitude": ("latitude", "longitude"),
            "bi_quadratic_latitude_longitude": ("latitude", "longitude"),
        }

    def ugrid_cell_connectivity_types(self):
        """Cell connectivity types.

        .. versionadded:: (cfdm) UGRIDVER

        :Returns:

            `dict`
               A mapping of netCDF UGRID mesh topology variable
               attributes to allowed cell connectivity construct
               "connectivity" types.

        """
        return {
            "face_face_connectivity": "edge",
        }

    def ugrid_mesh_topology_attributes(self):
        """The names of the non-metadata UGRID mesh topology attributes.

        .. versionadded:: (cfdm) UGRIDVER

        :Returns:

            `tuple`
                The attributes.

        """
        return (
            "topology_dimension",
            "node_coordinates",
            "edge_coordinates",
            "face_coordinates",
            "volume_coordinates",
            "edge_dimension",
            "face_dimension",
            "volume_dimension",
            "face_node_connectivity",
            "face_face_connectivity",
            "face_edge_connectivity",
            "edge_node_connectivity",
            "edge_face_connectivity",
            "volume_node_connectivity",
            "volume_edge_connectivity",
            "volume_face_connectivity",
            "volume_volume_connectivity",
            "volume_shape_type",
        )

    def _is_unreferenced(self, ncvar):
        """True if a netCDF variable is not referenced by another.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `_reference`

        :Parameters:

            ncvar: `str`
                The netCDF variable name.

        :Returns:

            `bool`
                Whether or this variable is referenced by any other.

        **Examples**

        >>> r._is_unreferenced('tas')
        False

        """
        return self.read_vars["references"].get(ncvar, 0) <= 0

    def _reference(self, ncvar, referencing_ncvar):
        """Increment the reference count of a netCDF variable.

        The reference count is the number of other variables which
        reference this one.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `_is_unreferenced`

        :Parameters:

            ncvar: `str` or `None`
                The netCDF variable name of the variable being
                referenced. If `None` then ``0`` is always returned.

            referencing_ncvar: `str`
                The netCDF name of the the variable that is doing the
                referencing.

                .. versionaddedd:: (cfdm) 1.8.6.0

        :Returns:

            `int`
                The new reference count.

        **Examples**

        >>> r._reference(None, 'tas')
        0
        >>> r._reference('longitude', 'tas')
        1
        >>> r._reference('longitude', 'pr')
        2
        >>> r.read_vars['references']['longitude']
        2
        >>> r.read_vars['referencers']
        {'tas', 'pr'}

        """
        if ncvar is None:
            return 0

        g = self.read_vars

        count = g["references"].setdefault(ncvar, 0) + 1
        g["references"][ncvar] = count

        # Keep a note of which variables are doing the referencing
        g["referencers"].setdefault(ncvar, set()).add(referencing_ncvar)

        return count

    def file_close(self):
        """Close all netCDF files that have been opened.

        Includes the input file being read, any external files, and any
        temporary flattened files.

        :Returns:

            `None`

        **Examples**

        >>> r.file_close()

        """
        for nc in self.read_vars["datasets"]:
            nc.close()

        # Close temporary flattened files
        for flat_file in self.read_vars["flat_files"]:
            flat_file.close()

        # Close the original grouped file (v1.8.8.1)
        if "nc_grouped" in self.read_vars:
            self.read_vars["nc_grouped"].close()

    def file_open(self, filename, flatten=True, verbose=None):
        """Open the netCDf file for reading.

        If the file has hierarchical groups then a flattened version of it
        is returned, and the original grouped file remains open.

        .. versionadded:: (cfdm) 1.7.0

        :Paramters:

            filename: `str`
                As for the *filename* parameter for initialising a
                `netCDF.Dataset` instance.

            flatten: `bool`, optional
                If True (the default) then flatten a grouped file.
                Ignored if the file has no groups.

                .. versionadded:: (cfdm) 1.8.6

        :Returns:

            `netCDF4.Dataset`
                A `netCDF4.Dataset` object for the file.

        **Examples**

        >>> r.file_open('file.nc')

        """
        try:
            nc = netCDF4.Dataset(filename, "r")
        except RuntimeError as error:
            raise RuntimeError(f"{error}: {filename}")

        # ------------------------------------------------------------
        # If the file has a group structure then flatten it (CF>=1.8)
        # ------------------------------------------------------------
        g = self.read_vars

        if flatten and nc.groups:
            # Create a diskless, non-persistent container for the
            # flattened file
            flat_file = tempfile.NamedTemporaryFile(
                mode="wb",
                dir=tempfile.gettempdir(),
                prefix="cfdm_flat_",
                suffix=".nc",
                delete=True,
            )

            flat_nc = netCDF4.Dataset(
                flat_file, "w", diskless=True, persist=False
            )
            flat_nc.set_fill_off()

            # Flatten the file
            netcdf_flattener.flatten(
                nc, flat_nc, lax_mode=True, _copy_data=False
            )

            # Store the original grouped file. This is primarily
            # because the unlimited dimensions in the flattened
            # dataset have size 0, since it contains no
            # data. (v1.8.8.1)
            g["nc_grouped"] = nc

            nc = flat_nc

            g["has_groups"] = True
            g["flat_files"].append(flat_file)

        g["nc"] = nc
        return nc

    @classmethod
    def cdl_to_netcdf(cls, filename):
        """Create a temporary netCDF-4 file from a CDL text file.

        :Parameters:

            filename: `str`
                The name of the CDL file.

        :Returns:

            `str`
                The name of the new netCDF file.

        """
        x = tempfile.NamedTemporaryFile(
            mode="wb", dir=tempfile.gettempdir(), prefix="cfdm_", suffix=".nc"
        )
        tmpfile = x.name

        # ----------------------------------------------------------------
        # Need to cache the TemporaryFile object so that it doesn't get
        # deleted too soon
        # ----------------------------------------------------------------
        _cached_temporary_files[tmpfile] = x

        try:
            subprocess.run(
                ["ncgen", "-knc4", "-o", tmpfile, filename], check=True
            )
        except subprocess.CalledProcessError as error:
            msg = str(error)
            if msg.startswith(
                "Command '['ncgen', '-knc4', '-o'"
            ) and msg.endswith("returned non-zero exit status 1."):
                raise ValueError(
                    "The CDL provided is invalid so cannot be converted "
                    "to netCDF."
                )
            else:
                raise

        return tmpfile

    @classmethod
    def is_netcdf_file(cls, filename):
        """Return `True` if the file is a netCDF file.

        The file type is determined by inspecting the file's contents
        and any file suffix is not not considered. However, file names
        starting ``https://`` or ``http://`` are assumed, without
        checking, to be netCDF files.

        :Parameters:

            filename: `str`
                The name of the file.

        :Returns:

            `bool`
                `True` if the file is netCDF, otherwise `False`

        **Examples**

        >>> {{package}}.{{class}}.is_netcdf_file('file.nc')
        True

        """
        # Assume that URLs are in netCDF format
        if filename.startswith("https://") or filename.startswith("http://"):
            return True

        # Read the magic number
        try:
            fh = open(filename, "rb")
            magic_number = struct.unpack("=L", fh.read(4))[0]
        except Exception:
            magic_number = None

        try:
            fh.close()
        except Exception:
            pass

        if magic_number in (
            21382211,
            1128547841,
            1178880137,
            38159427,
            88491075,
        ):
            return True
        else:
            return False

    def is_cdl_file(cls, filename):
        """True if the file is in CDL format.

        Return True if the file is a CDL text representation of a
        netCDF file.

        Note that the file type is determined by inspecting the file's
        contents and any file suffix is not not considered. The file is
        assumed to be a CDL file if it is a text file that starts with
        "netcdf ".

        .. versionaddedd:: (cfdm) 1.7.8

        :Parameters:

            filename: `str`
                The name of the file.

        :Returns:

            `bool`
                `True` if the file is CDL, otherwise `False`

        **Examples**

        >>> {{package}}.{{class}}.is_cdl_file('file.nc')
        False

        """
        # Read the magic number
        cdl = False
        try:
            fh = open(filename, "rt")
        except UnicodeDecodeError:
            pass
        except Exception:
            pass
        else:
            try:
                line = fh.readline()
                # Match comment and blank lines at the top of the file
                while re.match(r"^\s*//|^\s*$", line):
                    line = fh.readline()
                    if not line:
                        break

                if line.startswith("netcdf "):
                    cdl = True
            except UnicodeDecodeError:
                pass

        try:
            fh.close()
        except Exception:
            pass

        return cdl

    @classmethod
    def is_file(cls, filename):
        """Return `True` if *filename* is a file.

        Note that a remote URL starting with ``http://`` or
        ``https://`` is always considered as a file.

        .. versionadded:: (cfdm) 1.10.1.1

        :Parameters:

            filename: `str`
                The name of the file.

        :Returns:

            `bool`
                Whether or not *filename* is a file.

        **Examples**

        >>> {{package}}.{{class}}.is_file('file.nc')
        True
        >>> {{package}}.{{class}}.is_file('http://file.nc')
        True
        >>> {{package}}.{{class}}.is_file('https://file.nc')
        True

        """
        # Assume that URLs are files
        u = urlparse(filename)
        if u.scheme in ("http", "https"):
            return True

        return os.path.isfile(filename)

    @classmethod
    def is_dir(cls, filename):
        """Return `True` if *filename* is a directory.

        .. versionadded:: (cfdm) 1.10.1.1

        :Parameters:

            filename: `str`
                The name of the file.

        :Returns:

            `bool`
                Whether or not *filename* is a directory.

        **Examples**

        >>> {{package}}.{{class}}.is_dir('file.nc')
        False

        """
        return os.path.isdir(filename)

    def default_netCDF_fill_value(self, ncvar):
        """The default netCDF fill value for a variable.

        :Parameters:

            ncvar: `str`
                The netCDF variable name of the variable.

        :Returns:

                The default fill value for the netCDF variable.

        **Examples**

        >>> n.default_netCDF_fill_value('ua')
        9.969209968386869e+36

        """
        data_type = self.read_vars["variables"][ncvar].dtype.str[-2:]
        return netCDF4.default_fillvals[data_type]

    @_manage_log_level_via_verbosity
    def read(
        self,
        filename,
        extra=None,
        default_version=None,
        external=None,
        extra_read_vars=None,
        _scan_only=False,
        verbose=None,
        mask=True,
        warnings=True,
        warn_valid=False,
        domain=False,
    ):
        """Reads a netCDF dataset from file or OPenDAP URL.

        Read fields from a netCDF file on disk or from an OPeNDAP
        server location.

        The file may be big or little endian.

        NetCDF dimension names are stored in the `ncdim` attributes of the
        field's DomainAxis objects and netCDF variable names are stored in
        the `ncvar` attributes of the field and its components
        (coordinates, coordinate bounds, cell measures and coordinate
        references, domain ancillaries, field ancillaries).

        :Parameters:

            filename: `str`
                See `cfdm.read` for details

                .. versionadded:: (cfdm) 1.7.0

            extra: sequence of `str`, optional
                See `cfdm.read` for details

                .. versionadded:: (cfdm) 1.7.0

            warnings: `bool`, optional
                See `cfdm.read` for details

            mask: `bool`, optional
                See `cfdm.read` for details

                .. versionadded:: (cfdm) 1.8.2

            warn_valid: `bool`, optional
                See `cfdm.read` for details

                .. versionadded:: (cfdm) 1.8.3

            domain: `bool`, optional
                See `cfdm.read` for details

                .. versionadded:: (cfdm) 1.9.0.0

        :Returns:

            `list`
                The field or domain constructs in the file.

        """
        # ------------------------------------------------------------
        # Initialise netCDF read parameters
        # ------------------------------------------------------------
        self.read_vars = {
            "new_dimension_sizes": {},
            "formula_terms": {},
            "compression": {},
            # Verbose?
            "verbose": verbose,
            # Warnings?
            "warnings": warnings,
            "dataset_compliance": {None: {"non-compliance": {}}},
            "component_report": {},
            "auxiliary_coordinate": {},
            "cell_measure": {},
            "dimension_coordinate": {},
            "domain_ancillary": {},
            "domain_ancillary_key": None,
            "field_ancillary": {},
            "coordinates": {},
            "bounds": {},
            # --------------------------------------------------------
            # Geometry containers, keyed by their netCDF geometry
            # container variable names.
            # --------------------------------------------------------
            "geometries": {},
            # Map data variables to their geometry variable names
            "variable_geometry": {},
            "do_not_create_field": set(),
            "references": {},
            "referencers": {},
            # --------------------------------------------------------
            # External variables
            # --------------------------------------------------------
            # Variables listed by the global external_variables
            # attribute
            "external_variables": set(),
            # External variables that are actually referenced from
            # within the parent file
            "referenced_external_variables": set(),
            # --------------------------------------------------------
            # Coordinate references
            # --------------------------------------------------------
            # Grid mapping attributes that describe horizontal datum
            "datum_parameters": self.cf_datum_parameters(),
            # Vertical coordinate reference constructs, keyed by the
            # netCDF variable name of their parent parametric vertical
            # coordinate variable.
            #
            # E.g. {'ocean_s_coordinate':
            #        <CoordinateReference: ocean_s_coordinate>}
            "vertical_crs": {},
            #
            "version": {},
            # Auto mask?
            "mask": bool(mask),
            # Warn for the presence of valid_[min|max|range]
            # attributes?
            "warn_valid": bool(warn_valid),
            "valid_properties": set(("valid_min", "valid_max", "valid_range")),
            # Assume a priori that the dataset does not have a group
            # structure
            "has_groups": False,
            # Keep a list of flattened file names
            "flat_files": [],
            # --------------------------------------------------------
            # Domains (CF>=1.9)
            # --------------------------------------------------------
            "domain_ncdimensions": {},
            "domain": bool(domain),
            # --------------------------------------------------------
            # UGRID mesh topologies
            # --------------------------------------------------------
            # The UGRID version. May be set by the "Conventions"
            # attributes, or for CF>=1.11 defaults to to '1.0'.
            "UGRID_version": None,
            # Store each mesh topology
            "mesh": {},
            # --------------------------------------------------------
            # Compression by coordinate subsampling (CF>=1.9)
            # --------------------------------------------------------
            # NetCDF names of tie point coordinate variables
            "tie_point_ncvar": {},
            # Tie point index variables
            "tie_point_index": {},
            # Parsed contents of interpolation variables
            "interpolation": {},
            # Interpolation parameter variables
            "interpolation_parameter": {},
            # --------------------------------------------------------
            # CFA
            # --------------------------------------------------------
            "cfa": False,
        }

        g = self.read_vars

        # Set versions
        for version in ("1.6", "1.7", "1.8", "1.9", "1.10", "1.11"):
            g["version"][version] = Version(version)

        # ------------------------------------------------------------
        # Add custom read vars
        # ------------------------------------------------------------
        if extra_read_vars:
            g.update(deepcopy(extra_read_vars))

        # ------------------------------------------------------------
        # Parse field parameter
        # ------------------------------------------------------------
        g["get_constructs"] = {
            "auxiliary_coordinate": self.implementation.get_auxiliary_coordinates,
            "cell_measure": self.implementation.get_cell_measures,
            "dimension_coordinate": self.implementation.get_dimension_coordinates,
            "domain_ancillary": self.implementation.get_domain_ancillaries,
            "field_ancillary": self.implementation.get_field_ancillaries,
        }

        # Parse the 'external' keyword parameter
        if external:
            if isinstance(external, str):
                external = (external,)
        else:
            external = ()

        g["external_files"] = set(external)

        # Parse 'extra' keyword parameter
        if extra:
            if isinstance(extra, str):
                extra = (extra,)

            for f in extra:
                if f not in g["get_constructs"]:
                    raise ValueError(
                        f"Can't read: Bad parameter value: extra={extra!r}"
                    )

        g["extra"] = extra

        filename = os.path.expanduser(os.path.expandvars(filename))

        if self.is_dir(filename):
            raise IOError(f"Can't read directory {filename}")

        if not self.is_file(filename):
            raise IOError(f"Can't read non-existent file {filename}")

        g["filename"] = filename

        # ------------------------------------------------------------
        # Open the netCDF file to be read
        # ------------------------------------------------------------
        nc = self.file_open(filename, flatten=True, verbose=None)
        logger.info(f"Reading netCDF file: {filename}\n")  # pragma: no cover
        if is_log_level_debug(logger):
            logger.debug(
                f"    Input netCDF dataset:\n        {nc}\n"
            )  # pragma: no cover

        # ----------------------------------------------------------------
        # Put the file's global attributes into the global
        # 'global_attributes' dictionary
        # ----------------------------------------------------------------
        global_attributes = {}
        for attr in map(str, nc.ncattrs()):
            try:
                value = nc.getncattr(attr)
                if isinstance(value, str):
                    try:
                        global_attributes[attr] = str(value)
                    except UnicodeEncodeError:
                        global_attributes[attr] = value.encode(errors="ignore")
                else:
                    global_attributes[attr] = value
            except UnicodeDecodeError:
                pass

        g["global_attributes"] = global_attributes
        if is_log_level_debug(logger):
            logger.debug(
                f"    Global attributes:\n        {g['global_attributes']}"
            )  # pragma: no cover

        # ------------------------------------------------------------
        # Find the CF version for the file, and the CFA version.
        # ------------------------------------------------------------
        Conventions = g["global_attributes"].get("Conventions", "")

        # If the string contains any commas, it is assumed to be a
        # comma-separated list.
        all_conventions = re.split(",\s*", Conventions)
        if all_conventions[0] == Conventions:
            all_conventions = Conventions.split()

        file_version = None
        for c in all_conventions:
            if c.startswith("CF-"):
                file_version = c.replace("CF-", "", 1)
            elif c.startswith("UGRID-"):
                # Allow UGRID if it has been specified in Conventions,
                # regardless of the version of CF.
                g["UGRID_version"] = Version(c.replace("UGRID-", "", 1))
            elif c.startswith("CFA-"):
                g["cfa"] = True
                g["CFA_version"] = Version(c.replace("CFA-", "", 1))
            elif c == "CFA":
                g["cfa"] = True
                g["CFA_version"] = Version("0.4")

        if file_version is None:
            if default_version is not None:
                # Assume the default version provided by the user
                file_version = default_version
            else:
                # Assume the file has the same version of the CFDM
                # implementation
                file_version = self.implementation.get_cf_version()

        g["file_version"] = Version(file_version)

        # Set minimum/maximum versions
        for vn in ("1.6", "1.7", "1.8", "1.9", "1.10", "1.11"):
            g["CF>=" + vn] = g["file_version"] >= g["version"][vn]

        # From CF-1.11 we can assume UGRID-1.0
        if g["CF>=1.11"] and g["UGRID_version"] is None:
            g["UGRID_version"] = "1.0"

        # ------------------------------------------------------------
        # Create a dictionary keyed by netCDF variable names where
        # each key's value is a dictionary of that variable's netCDF
        # attributes. E.g. attributes['tas']['units']='K'
        # ------------------------------------------------------------
        variable_attributes = {}
        variable_dimensions = {}
        variable_dataset = {}
        variable_filename = {}
        variables = {}
        variable_groups = {}
        variable_group_attributes = {}
        variable_basename = {}
        variable_grouped_dataset = {}

        dimension_groups = {}
        dimension_basename = {}

        dimension_isunlimited = {}

        # ------------------------------------------------------------
        # For grouped files (CF>=1.8) map:
        #
        # * each flattened variable name to its absolute path
        # * each flattened dimension name to its absolute path
        # * each group to its group attributes
        #
        # ------------------------------------------------------------
        has_groups = g["has_groups"]

        flattener_variables = {}
        flattener_dimensions = {}
        flattener_attributes = {}

        if has_groups:
            flattener_name_mapping_variables = getattr(
                nc, "__flattener_name_mapping_variables", None
            )
            if flattener_name_mapping_variables is not None:
                if isinstance(flattener_name_mapping_variables, str):
                    flattener_name_mapping_variables = [
                        flattener_name_mapping_variables
                    ]
                flattener_variables = dict(
                    tuple(x.split(": "))
                    for x in flattener_name_mapping_variables
                )

            flattener_name_mapping_dimensions = getattr(
                nc, "__flattener_name_mapping_dimensions", None
            )
            if flattener_name_mapping_dimensions is not None:
                if isinstance(flattener_name_mapping_dimensions, str):
                    flattener_name_mapping_dimensions = [
                        flattener_name_mapping_dimensions
                    ]
                flattener_dimensions = dict(
                    tuple(x.split(": "))
                    for x in flattener_name_mapping_dimensions
                )

                # Remove a leading / (slash) from dimensions in the
                # root group
                for key, value in flattener_dimensions.items():
                    if value.startswith("/") and value.count("/") == 1:
                        flattener_dimensions[key] = value[1:]

            flattener_name_mapping_attributes = getattr(
                nc, "__flattener_name_mapping_attributes", None
            )
            if flattener_name_mapping_attributes is not None:
                if isinstance(flattener_name_mapping_attributes, str):
                    flattener_name_mapping_attributes = [
                        flattener_name_mapping_attributes
                    ]
                flattener_attributes = dict(
                    tuple(x.split(": "))
                    for x in flattener_name_mapping_attributes
                )

                # Remove group attributes from the global attributes,
                # and vice versa.
                for flat_attr in flattener_attributes.copy():
                    attr = flattener_attributes.pop(flat_attr)

                    x = attr.split("/")
                    groups = x[1:-1]

                    if groups:
                        g["global_attributes"].pop(flat_attr)

                        group_attr = x[-1]
                        flattener_attributes.setdefault(tuple(groups), {})[
                            group_attr
                        ] = nc.getncattr(flat_attr)

            # Remove flattener attributes from the global attributes
            for attr in (
                "__flattener_name_mapping_variables",
                "__flattener_name_mapping_dimensions",
                "__flattener_name_mapping_attributes",
            ):
                g["global_attributes"].pop(attr, None)

        for ncvar in nc.variables:
            ncvar_basename = ncvar
            groups = ()
            group_attributes = {}

            variable = nc.variables[ncvar]

            # --------------------------------------------------------
            # Specify the group structure for each variable (CF>=1.8)
            # TODO
            # If the file only has the root group then this dictionary
            # will be empty. Variables in the root group when there
            # are sub-groups will have dictionary values of None.
            # --------------------------------------------------------
            if has_groups:
                # Replace the flattened variable name with its
                # absolute path.
                ncvar_flat = ncvar
                ncvar = flattener_variables[ncvar]

                groups = tuple(ncvar.split("/")[1:-1])

                if groups:
                    # This variable is in a group. Remove the group
                    # structure that was prepended to the netCDF
                    # variable name by the netCDF flattener.
                    ncvar_basename = re.sub(
                        f"^{_flattener_separator.join(groups)}{_flattener_separator}",
                        "",
                        ncvar_flat,
                    )

                    # ------------------------------------------------
                    # Group attributes. Note that, currently,
                    # sub-group attributes supercede all parent group
                    # attributes (but not global attributes).
                    # ------------------------------------------------
                    group_attributes = {}
                    for i in range(1, len(groups) + 1):
                        hierarchy = groups[:i]
                        if hierarchy not in flattener_attributes:
                            continue

                        group_attributes.update(
                            flattener_attributes[hierarchy]
                        )
                else:
                    # Remove the leading / from the absolute netCDF
                    # variable path
                    ncvar = ncvar[1:]
                    flattener_variables[ncvar] = ncvar

                variable_grouped_dataset[ncvar] = g["nc_grouped"]

            variable_attributes[ncvar] = {}
            for attr in map(str, variable.ncattrs()):
                try:
                    variable_attributes[ncvar][attr] = variable.getncattr(attr)
                    if isinstance(variable_attributes[ncvar][attr], str):
                        try:
                            variable_attributes[ncvar][attr] = str(
                                variable_attributes[ncvar][attr]
                            )
                        except UnicodeEncodeError:
                            variable_attributes[ncvar][
                                attr
                            ] = variable_attributes[ncvar][attr].encode(
                                errors="ignore"
                            )
                except UnicodeDecodeError:
                    pass

            variable_dimensions[ncvar] = tuple(variable.dimensions)
            variable_dataset[ncvar] = nc
            variable_filename[ncvar] = g["filename"]
            variables[ncvar] = variable

            variable_basename[ncvar] = ncvar_basename
            variable_groups[ncvar] = groups
            variable_group_attributes[ncvar] = group_attributes

        # Populate dimensions_groups abd dimension_basename
        # dictionaries
        for ncdim in nc.dimensions:
            ncdim_org = ncdim
            ncdim_basename = ncdim
            groups = ()
            ncdim_basename = ncdim

            if has_groups:
                # Replace the flattened variable name with its
                # absolute path.
                ncdim_flat = ncdim
                ncdim = flattener_dimensions[ncdim_flat]

                groups = tuple(ncdim.split("/")[1:-1])

                if groups:
                    # This dimension is in a group.
                    ncdim_basename = re.sub(
                        "^{_flattener_separator.join(groups)}{_flattener_separator}",
                        "",
                        ncdim_flat,
                    )

            dimension_groups[ncdim] = groups
            dimension_basename[ncdim] = ncdim_basename

            dimension_isunlimited[ncdim] = nc.dimensions[
                ncdim_org
            ].isunlimited()

        if has_groups:
            variable_dimensions = {
                name: tuple([flattener_dimensions[ncdim] for ncdim in value])
                for name, value in variable_dimensions.items()
            }

        if is_log_level_debug(logger):
            logger.debug(
                "    General read variables:\n"
                "        read_vars['variable_dimensions'] =\n"
                f"            {variable_dimensions}"
            )  # pragma: no cover

        # The netCDF attributes for each variable
        #
        # E.g. {'grid_lon': {'standard_name': 'grid_longitude'}}
        g["variable_attributes"] = variable_attributes

        # The netCDF dimensions for each variable
        #
        # E.g. {'grid_lon_bounds': ('grid_longitude', 'bounds2')}
        g["variable_dimensions"] = variable_dimensions

        # The netCDF4 dataset object for each variable
        g["variable_dataset"] = variable_dataset

        # The original gouped dataset for each variable (empty if the
        # original dataset is not grouped) v1.8.8.1
        g["variable_grouped_dataset"] = variable_grouped_dataset

        # The name of the file containing the each variable
        g["variable_filename"] = variable_filename

        # The netCDF4 variable object for each variable
        g["variables"] = variables

        # The netCDF4 dataset objects that have been opened (i.e. the
        # for parent file and any external files)
        g["datasets"] = [nc]

        # The names of the variable in the parent files
        # (i.e. excluding any external variables)
        g["internal_variables"] = set(variables)

        # The netCDF dimensions of the parent file
        internal_dimension_sizes = {}
        for name, dimension in nc.dimensions.items():
            if (
                has_groups
                and dimension_isunlimited[flattener_dimensions[name]]
            ):
                # For grouped datasets, get the unlimited dimension
                # size from the original grouped dataset, because
                # unlimited dimensions have size 0 in the flattened
                # dataset (because it contains no data) (v1.8.8.1)
                group, ncdim = self._netCDF4_group(
                    g["nc_grouped"], flattener_dimensions[name]
                )
                internal_dimension_sizes[name] = group.dimensions[ncdim].size
            else:
                internal_dimension_sizes[name] = dimension.size

        if g["has_groups"]:
            internal_dimension_sizes = {
                flattener_dimensions[name]: value
                for name, value in internal_dimension_sizes.items()
            }

        g["internal_dimension_sizes"] = internal_dimension_sizes

        # The group structure for each variable. Variables in the root
        # group have a group structure of ().
        #
        # E.g. {'lat': (),
        #       '/forecasts/lon': ('forecasts',)
        #       '/forecasts/model/t': 'forecasts', 'model')}
        g["variable_groups"] = variable_groups

        # The group attributes that apply to each variable
        #
        # E.g. {'latitude': {},
        #       'eastward_wind': {'model': 'climate1'}}
        g["variable_group_attributes"] = variable_group_attributes

        # Mapped components of a flattened version of the netCDF file
        g["flattener_variables"] = flattener_variables
        g["flattener_dimensions"] = flattener_dimensions
        g["flattener_attributes"] = flattener_attributes

        # The basename of each variable. I.e. the dimension name
        # without its prefixed group structure.
        #
        # E.g. {'lat': 'lat',
        #       '/forecasts/lon': 'lon',
        #       '/forecasts/model/t': 't'}
        g["variable_basename"] = variable_basename

        # The unlimited status of each dimension
        #
        # E.g. {'/forecast/lat': False, 'bounds2': False, 'lon':
        #       False}
        g["dimension_isunlimited"] = dimension_isunlimited

        # The group structure for each dimension. Dimensions in the
        # root group have a group structure of ().
        #
        # E.g. {'lat': (),
        #       '/forecasts/lon': ('forecasts',)
        #       '/forecasts/model/t': 9'forecasts', 'model')}
        g["dimension_groups"] = dimension_groups

        # The basename of each dimension. I.e. the dimension name
        # without its prefixed group structure.
        #
        # E.g. {'lat': 'lat',
        #       '/forecasts/lon': 'lon',
        #       '/forecasts/model/t': 't'}
        g["dimension_basename"] = dimension_basename

        if is_log_level_debug(logger):
            logger.debug(
                "        read_vars['dimension_isunlimited'] =\n"
                f"            {g['dimension_isunlimited']}\n"
                "        read_vars['internal_dimension_sizes'] =\n"
                f"            {g['internal_dimension_sizes']}\n"
                "    Groups read vars:\n"
                "        read_vars['variable_groups'] =\n"
                f"            {g['variable_groups']}\n"
                "        read_vars['variable_basename'] =\n"
                f"            {variable_basename}\n"
                "        read_vars['dimension_groups'] =\n"
                f"            {g['dimension_groups']}\n"
                "        read_vars['dimension_basename'] =\n"
                f"            {g['dimension_basename']}\n"
                "        read_vars['flattener_variables'] =\n"
                f"            {g['flattener_variables']}\n"
                "        read_vars['flattener_dimensions'] =\n"
                f"            {g['flattener_dimensions']}\n"
                "        read_vars['flattener_attributes'] =\n"
                f"            {g['flattener_attributes']}\n"
                f"   netCDF dimensions: {internal_dimension_sizes}"
            )  # pragma: no cover

        # Now that all of the variables have been scanned, customise
        # the read parameters.
        self._customise_read_vars()

        # ------------------------------------------------------------
        # List variables
        #
        # Identify and parse all list variables
        # ------------------------------------------------------------
        for ncvar, dimensions in variable_dimensions.items():
            if dimensions != (ncvar,):
                continue

            # This variable is a Unidata coordinate variable
            compress = variable_attributes[ncvar].get("compress")
            if compress is None:
                continue

            # This variable is a list variable for gathering
            # arrays
            self._parse_compression_gathered(ncvar, compress)

            # Do not attempt to create a field from a list
            # variable
            g["do_not_create_field"].add(ncvar)

        # ------------------------------------------------------------
        # DSG variables (CF>=1.6)
        #
        # Identify and parse all DSG count and DSG index variables
        # ------------------------------------------------------------
        if g["CF>=1.6"]:
            featureType = g["global_attributes"].get("featureType")
            if featureType is not None:
                g["featureType"] = featureType

                sample_dimension = None
                for ncvar, attributes in variable_attributes.items():
                    if "sample_dimension" not in attributes:
                        continue

                    # ------------------------------------------------
                    # This variable is a count variable for DSG
                    # contiguous ragged arrays
                    # ------------------------------------------------
                    sample_dimension = attributes["sample_dimension"]

                    if has_groups:
                        sample_dimension = g["flattener_dimensions"].get(
                            sample_dimension, sample_dimension
                        )

                    cf_compliant = self._check_sample_dimension(
                        ncvar, sample_dimension
                    )
                    if not cf_compliant:
                        sample_dimension = None
                    else:
                        self._parse_ragged_contiguous_compression(
                            ncvar, sample_dimension
                        )

                        # Do not attempt to create a field from a
                        # count variable
                        g["do_not_create_field"].add(ncvar)

                instance_dimension = None
                for ncvar, attributes in variable_attributes.items():
                    if "instance_dimension" not in attributes:
                        continue

                    # ------------------------------------------------
                    # This variable is an index variable for DSG
                    # indexed ragged arrays
                    # ------------------------------------------------
                    instance_dimension = attributes["instance_dimension"]

                    if has_groups:
                        instance_dimension = g["flattener_dimensions"].get(
                            instance_dimension, instance_dimension
                        )

                    cf_compliant = self._check_instance_dimension(
                        ncvar, instance_dimension
                    )
                    if not cf_compliant:
                        instance_dimension = None
                    else:
                        self._parse_indexed_compression(
                            ncvar, instance_dimension
                        )

                        # Do not attempt to create a field from a
                        # index variable
                        g["do_not_create_field"].add(ncvar)

                if (
                    sample_dimension is not None
                    and instance_dimension is not None
                ):
                    # ------------------------------------------------
                    # There are DSG indexed contiguous ragged arrays
                    # ------------------------------------------------
                    self._parse_indexed_contiguous_compression(
                        sample_dimension, instance_dimension
                    )

        # ------------------------------------------------------------
        # Identify and parse all geometry container variables
        # (CF>=1.8)
        # ------------------------------------------------------------
        if g["CF>=1.8"]:
            for ncvar, attributes in variable_attributes.items():
                if "geometry" not in attributes:
                    # This data variable does not have a geometry
                    # container
                    continue

                geometry_ncvar = self._parse_geometry(
                    ncvar, variable_attributes
                )

                if not geometry_ncvar:
                    # The geometry container has already been parsed,
                    # or a sufficiently compliant geometry container
                    # could not be found.
                    continue

                # Do not attempt to create a field construct from a
                # node coordinate variable
                g["do_not_create_field"].add(geometry_ncvar)

        if is_log_level_debug(logger):
            logger.debug(
                "    Compression read vars:\n"
                "        read_vars['compression'] =\n"
                f"            {g['compression']}"
            )  # pragma: no cover

        # ------------------------------------------------------------
        # Parse external variables (CF>=1.7)
        # ------------------------------------------------------------
        if g["CF>=1.7"]:
            netcdf_external_variables = global_attributes.pop(
                "external_variables", None
            )
            parsed_external_variables = self._split_string_by_white_space(
                None, netcdf_external_variables
            )
            parsed_external_variables = self._check_external_variables(
                netcdf_external_variables, parsed_external_variables
            )
            g["external_variables"] = set(parsed_external_variables)

        # ------------------------------------------------------------
        # Compression by coordinate subsampling (CF>=1.9)
        # ------------------------------------------------------------
        if g["CF>=1.9"]:
            for ncvar, attributes in variable_attributes.items():
                if "coordinate_interpolation" not in attributes:
                    # This variable does not have any subsampled
                    # coordinates
                    continue

                self._parse_coordinate_interpolation(
                    attributes["coordinate_interpolation"], ncvar
                )

        # ------------------------------------------------------------
        # Parse UGRID mesh topologies
        # ------------------------------------------------------------
        if g["UGRID_version"] is not None:
            for ncvar, attributes in variable_attributes.items():
                if "topology_dimension" in attributes:
                    # This variable is a mesh topology
                    self._ugrid_parse_mesh_topology(ncvar, attributes)

            for ncvar, attributes in variable_attributes.items():
                if "location_index_set" in attributes:
                    # This data variable has a domain defined by a
                    # location_index_set
                    self._ugrid_parse_location_index_set(attributes)

            if is_log_level_debug(logger):
                logger.debug("    UGRID meshes:\n" f"       {g['mesh']}")

        if _scan_only:
            return self.read_vars

        # ------------------------------------------------------------
        # Get external variables (CF>=1.7)
        # ------------------------------------------------------------
        if g["CF>=1.7"]:
            logger.info(
                f"    External variables: {g['external_variables']}\n"
                f"    External files    : {g['external_files']}"
            )  # pragma: no cover

            if g["external_files"] and g["external_variables"]:
                self._get_variables_from_external_files(
                    netcdf_external_variables
                )

        # ------------------------------------------------------------
        # Create a field/domain from every netCDF variable (apart from
        # special variables that have already been identified as such)
        # ------------------------------------------------------------
        if g["domain"]:
            logger.info(
                "    Reading CF-netCDF domain variables only "
                "(ignoring CF-netCDF data variables)"
            )  # pragma: no cover
        else:
            logger.info(
                "    Reading CF-netCDF data variables only "
                "(ignoring CF-netCDF domain variables)"
            )  # pragma: no cover

        all_fields_or_domains = {}
        domain = g["domain"]
        for ncvar in g["variables"]:
            if ncvar in g["do_not_create_field"] or ncvar in g["mesh"]:
                continue

            field_or_domain = self._create_field_or_domain(
                ncvar, domain=domain
            )
            if field_or_domain is not None:
                all_fields_or_domains[ncvar] = field_or_domain

        # ------------------------------------------------------------
        # Create domain constructs from UGRID mesh topology variables
        # ------------------------------------------------------------
        if domain and g["UGRID_version"] is not None:
            locations = ("node", "edge", "face")
            for ncvar in g["variables"]:
                if ncvar not in g["mesh"]:
                    continue

                for location in locations:
                    mesh_domain = self._create_field_or_domain(
                        ncvar,
                        domain=domain,
                        location=location,
                    )
                    if mesh_domain is None:
                        continue

                    all_fields_or_domains[f"{ncvar} {location}"] = mesh_domain

        # ------------------------------------------------------------
        # Check for unreferenced external variables (CF>=1.7)
        # ------------------------------------------------------------
        if g["CF>=1.7"]:
            unreferenced_external_variables = g[
                "external_variables"
            ].difference(g["referenced_external_variables"])
            for ncvar in unreferenced_external_variables:
                self._add_message(
                    None,
                    ncvar,
                    message=("External variable", "is not referenced in file"),
                    attribute={
                        "external_variables": netcdf_external_variables
                    },
                )

        if is_log_level_debug(logger):
            logger.debug(
                "    Reference read vars:\n"
                "        read_vars['references'] =\n"
                f"            {g['references']}\n"
                "        read_vars['referencers'] =\n"
                f"            {g['referencers']}"
            )  # pragma: no cover

        # ------------------------------------------------------------
        # Discard fields/domains created from netCDF variables that
        # are referenced by other netCDF variables
        # ------------------------------------------------------------
        fields_or_domains = {}
        for ncvar, f in all_fields_or_domains.items():
            if self._is_unreferenced(ncvar):
                fields_or_domains[ncvar] = f

        referenced_variables = [
            ncvar
            for ncvar in sorted(all_fields_or_domains)
            if not self._is_unreferenced(ncvar)
        ]
        unreferenced_variables = [
            ncvar
            for ncvar in sorted(all_fields_or_domains)
            if self._is_unreferenced(ncvar)
        ]

        for ncvar in referenced_variables[:]:
            if all(
                referencer in referenced_variables
                for referencer in g["referencers"][ncvar]
            ):
                referenced_variables.remove(ncvar)
                unreferenced_variables.append(ncvar)
                fields_or_domains[ncvar] = all_fields_or_domains[ncvar]

        logger.info(
            "    Referenced netCDF variables:"
            + "\n        ".join(referenced_variables)
        )  # pragma: no cover
        if g["do_not_create_field"]:
            logger.info(
                "        "
                + "\n        ".join(
                    [ncvar for ncvar in sorted(g["do_not_create_field"])]
                )
            )  # pragma: no cover
        logger.info(
            "    Unreferenced netCDF variables:\n        "
            + "\n        ".join(unreferenced_variables)
        )  # pragma: no cover

        # ------------------------------------------------------------
        # If requested, reinstate fields/domains created from netCDF
        # variables that are referenced by other netCDF variables.
        # ------------------------------------------------------------
        self_referenced = {}
        if g["extra"] and not g["domain"]:
            fields_or_domains0 = list(fields_or_domains.values())
            for construct_type in g["extra"]:
                for f in fields_or_domains0:
                    for construct in g["get_constructs"][construct_type](
                        f
                    ).values():
                        ncvar = self.implementation.nc_get_variable(construct)
                        if ncvar not in all_fields_or_domains:
                            continue

                        if ncvar not in fields_or_domains:
                            fields_or_domains[ncvar] = all_fields_or_domains[
                                ncvar
                            ]
                        else:
                            self_referenced[ncvar] = all_fields_or_domains[
                                ncvar
                            ]

        if not self_referenced:
            items = fields_or_domains.items()
        else:
            items = tuple(fields_or_domains.items()) + tuple(
                self_referenced.items()
            )

        out = [x[1] for x in sorted(items)]

        if warnings:
            for x in out:
                qq = x.dataset_compliance()
                if qq:
                    logger.warning(
                        f"WARNING: {x.__class__.__name__} incomplete due to "
                        f"non-CF-compliant dataset. Report:\n{qq}"
                    )  # pragma: no cover

        if warn_valid and not g["domain"]:
            # --------------------------------------------------------
            # Warn for the presence of field 'valid_min',
            # 'valid_max'or 'valid_range' properties. (Introduced at
            # v1.8.3)
            # --------------------------------------------------------
            for f in out:
                # Check field constructs
                self._check_valid(f, f)

                # Check constructs with data
                for c in self.implementation.get_constructs(
                    f, data=True
                ).values():
                    self._check_valid(f, c)

        # ------------------------------------------------------------
        # Close all opened netCDF files
        # ------------------------------------------------------------
        self.file_close()

        # ------------------------------------------------------------
        # Return the fields/domains
        # ------------------------------------------------------------
        return out

    def _check_valid(self, field, construct):
        """Warns when valid_[min|max|range] properties exist on data.

        Issue a warning if a construct with data has
        valid_[min|max|range] properties.

        .. versionadded:: (cfdm) 1.8.3

        :Parameters:

            field: `Field`
                The parent field construct.

            construct: Construct or Bounds
                The construct that may have valid_[min|max|range]
                properties. May also be the parent field construct or
                Bounds.

        :Returns:

            `None`

        """
        # Check the bounds, if any.
        if self.implementation.has_bounds(construct):
            bounds = self.implementation.get_bounds(construct)
            self._check_valid(field, bounds)

        x = sorted(
            self.read_vars["valid_properties"].intersection(
                self.implementation.get_properties(construct)
            )
        )
        if not x:
            return

        # Still here?
        if self.implementation.is_field(construct):
            construct = ""
        else:
            construct = f" {construct!r} with"

        message = (
            f"WARNING: {field!r} has {construct} {', '.join(x)} "
            "{self._plural(x, 'property')}. "
        )
        print(message)

    def _plural(self, x, singular):
        """Pluralises a singular word if *x* is not of length one.

        Return the plural of a word if *x* has zero elements or more
        than one element, otherwise return the word unchanged.

        :Parameters:

            x: sequence

            singular: `str`
                The word in it's singular form.

        :Returns:

            `str`
                The word in its singular or plural form.

        **Examples**

        >>> n._plural([1, 2], 'property')
        'properties'
        >>> n._plural([1], 'property')
        'property'
        >>> n._plural([], 'property')
        'properties'

        """
        if len(x) == 1:
            return singular

        if singular[-1] == "y":
            return singular[:-1] + "ies"

        raise ValueError(f"Can't pluralise {singular}")

    def _set_default_FillValue(self, construct, ncvar):
        """Ensure there is a fill value recorded on the construct.

        The motivation for this is that masking can later be
        applied manually on the construct after the masking has
        been turned off.

        .. versionadded:: (cfdm) 1.8.3

        """
        _FillValue = self.implementation.get_property(
            construct, "_FillValue", None
        )
        if _FillValue is None:
            self.implementation.set_properties(
                construct,
                {"_FillValue": self.default_netCDF_fill_value(ncvar)},
            )

    def _customise_auxiliary_coordinates(self, parent_ncvar, f):
        """Create extra auxiliary coordinate constructs.

        This method is primarily aimed at providing a customisation
        entry point for subclasses. It is assumed that any new
        constructs are set on the parent field or domain construct
        inside this method.

        .. versionadded:: (cfdm) 1.10.1.0

        :Parameters:

            parent_ncvar: `str`
                The netCDF variable name of the parent variable.

            f: `Field` or `Domain`
                The parent field or domain construct.

        :Returns:

            `dict`
                A mapping of netCDF variable names to newly-created
                construct identifiers.

        **Examples**

        >>> n._customise_auxiliary_coordinates('tas', f)
        {}

        >>> n._customise_auxiliary_coordinates('pr', f)
        {'tracking_id': 'auxiliarycoordinate0'}

        """
        return {}

    def _customise_field_ancillaries(self, parent_ncvar, f):
        """Create extra field ancillary constructs.

        This method is primarily aimed at providing a customisation
        entry point for subclasses. It is assumed that any new
        constructs are set on the parent field construct inside this
        method.

        .. versionadded:: (cfdm) 1.10.1.0

        :Parameters:

            parent_ncvar: `str`
                The netCDF variable name of the parent variable.

            f: `Field`
                The parent field construct.

        :Returns:

            `dict`
                A mapping of netCDF variable names to newly-created
                construct identifiers.

        **Examples**

        >>> n._customise_field_ancillaries('tas', f)
        {}

        >>> n._customise_field_ancillaries('pr', f)
        {'tracking_id': 'fieldancillary1'}

        """
        return {}

    def _customise_read_vars(self):
        """Customise the read parameters.

        This method is primarily aimed at providing a customisation
        entry point for subclasses.

        .. versionadded:: (cfdm) 1.7.3

        """
        pass

    def _get_variables_from_external_files(self, netcdf_external_variables):
        """Get external variables from external files.

        ..versionadded:: (cfdm) 1.7.0

        :Parameters:

            netcdf_external_variables: `str`
                The un-parsed netCDF external_variables attribute in
                the parent file.

                *Parmaeter example:*
                  ``external_variables='areacello'``

        :Returns:

            `None`
                The following are updated in-place:
                ``read_vars["external_variables"]``,
                ``read_vars["datasets"]``

        """
        attribute = {"external_variables": netcdf_external_variables}

        read_vars = self.read_vars.copy()
        verbose = read_vars["verbose"]

        external_variables = read_vars["external_variables"]
        external_files = read_vars["external_files"]
        datasets = read_vars["datasets"]
        parent_dimension_sizes = read_vars["internal_dimension_sizes"]

        keys = (
            "variable_attributes",
            "variable_dimensions",
            "variable_dataset",
            "variable_filename",
            "variable_groups",
            "variable_group_attributes",
            "variable_basename",
            "variables",
        )

        found = []

        for external_file in external_files:
            logger.info(
                "\nScanning external file:\n-----------------------"
            )  # pragma: no cover

            external_read_vars = self.read(
                external_file, _scan_only=True, verbose=verbose
            )

            logger.info(
                "Finished scanning external file\n"
            )  # pragma: no cover

            # Reset self.read_vars
            self.read_vars = read_vars

            datasets.append(external_read_vars["nc"])

            for ncvar in external_variables.copy():
                if ncvar not in external_read_vars["internal_variables"]:
                    # The external variable name is not in this
                    # external file
                    continue

                if ncvar in found:
                    # Error: The external variable exists in more than
                    # one external file
                    external_variables.add(ncvar)
                    for key in keys:
                        self.read_vars[key].pop(ncvar)

                    self._add_message(
                        None,
                        ncvar,
                        message=(
                            "External variable",
                            "exists in multiple external files",
                        ),
                        attribute=attribute,
                    )
                    continue

                # Still here? Then the external variable exists in
                # this external file
                found.append(ncvar)

                # Check that the external variable dimensions exist in
                # parent file, with the same sizes.
                ok = True
                for d in external_read_vars["variable_dimensions"][ncvar]:
                    size = parent_dimension_sizes.get(d)
                    if size is None:
                        ok = False
                        self._add_message(
                            None,
                            ncvar,
                            message=(
                                "External variable dimension",
                                "does not exist in file",
                            ),
                            attribute=attribute,
                        )
                    elif (
                        external_read_vars["internal_dimension_sizes"][d]
                        != size
                    ):
                        ok = False
                        self._add_message(
                            None,
                            ncvar,
                            message=(
                                "External variable dimension",
                                "has incorrect size",
                            ),
                            attribute=attribute,
                        )
                    else:
                        continue

                if ok:
                    # Update the read parameters so that this external
                    # variable looks like it is an internal variable
                    for key in keys:
                        self.read_vars[key][ncvar] = external_read_vars[key][
                            ncvar
                        ]

                    # Remove this ncvar from the set of external variables
                    external_variables.remove(ncvar)

    def _parse_compression_gathered(self, ncvar, compress):
        """Parse a list variable for compressing arrays by gathering."""
        g = self.read_vars

        logger.info(
            f"        List variable: compress = {compress}"
        )  # pragma: no cover

        gathered_ncdimension = g["variable_dimensions"][ncvar][0]

        parsed_compress = self._split_string_by_white_space(
            ncvar, compress, variables=True
        )
        cf_compliant = self._check_compress(ncvar, compress, parsed_compress)
        if not cf_compliant:
            return

        list_variable = self._create_List(ncvar)

        g["compression"][gathered_ncdimension] = {
            "gathered": {
                "list_variable": list_variable,
                "implied_ncdimensions": parsed_compress,
                "sample_dimension": gathered_ncdimension,
            }
        }

    def _parse_ragged_contiguous_compression(self, ncvar, sample_dimension):
        """Parse a count variable for DSG contiguous ragged arrays.

        :Parameters:

            ncvar: `str`
                The netCDF variable name of the count variable (section
                9.3.3).

            sample_dimension: `str`
                The netCDF dimension name of the sample dimension (section
                9.3.3).

        :Returns:

            `str`
                The made-up netCDF dimension name of the element dimension.

        """
        g = self.read_vars

        logger.info(
            f"    count variable: sample_dimension = {sample_dimension}"
        )  # pragma: no cover

        instance_dimension = g["variable_dimensions"][ncvar][0]

        elements_per_instance = self._create_Count(
            ncvar=ncvar, ncdim=instance_dimension
        )

        # Make up a netCDF dimension name for the element dimension
        featureType = g["featureType"].lower()
        if featureType in ("timeseries", "trajectory", "profile"):
            element_dimension = featureType
        elif featureType == "timeseriesprofile":
            element_dimension = "profile"
        elif featureType == "trajectoryprofile":
            element_dimension = "profile"
        else:
            element_dimension = "element"

        logger.info(
            f"    featureType = {g['featureType']}"
        )  # pragma: no cover

        element_dimension = self._set_ragged_contiguous_parameters(
            elements_per_instance=elements_per_instance,
            sample_dimension=sample_dimension,
            element_dimension=element_dimension,
            instance_dimension=instance_dimension,
        )

        return element_dimension

    def _parse_indexed_compression(self, ncvar, instance_dimension):
        """Parse an index variable for DSG indexed ragged arrays.

        The CF-netCDF index variable contains the zero-based index of the
        feature to which each element belongs. It is identifiable by the
        presence of an attribute, "instance_dimension", which names the
        dimension of the instance variables. For those indices of the
        sample dimension into which data have not yet been written, the
        index variable should be pre-filled with missing values.

        :Parameters:

            ncvar: `str`
                The netCDF variable name of the index variable.

            instance_dimension: `str`
                The netCDF variable name of the instance dimension.

        :Returns:

            `str`
                An invented netCDF name for the element dimension,
                e.g. ``'timeseriesprofile'``.

        """
        g = self.read_vars

        # Read the data of the index variable
        ncdim = g["variable_dimensions"][ncvar][0]

        index = self._create_Index(ncvar, ncdim=ncdim)

        # Make up a netCDF dimension name for the element dimension
        featureType = g["featureType"].lower()
        if featureType in ("timeseries", "trajectory", "profile"):
            element_dimension = featureType.lower()
        elif featureType == "timeseriesprofile":
            element_dimension = "timeseries"
        elif featureType == "trajectoryprofile":
            element_dimension = "trajectory"
        else:
            element_dimension = "element"

        logger.info(
            f"    featureType = {g['featureType']}"
        )  # pragma: no cover

        element_dimension = self._set_ragged_indexed_parameters(
            index=index,
            indexed_sample_dimension=g["variable_dimensions"][ncvar][0],
            element_dimension=element_dimension,
            instance_dimension=instance_dimension,
        )

        return element_dimension

    def _parse_indexed_contiguous_compression(
        self, sample_dimension, instance_dimension
    ):
        """Parse an index variable for indexed contiguous ragged arrays.

        :Parameters:

            sample_dimension: `str`
                The netCDF dimension name of the sample dimension.

            element_dimension_1: `str`
                The name of the implied element dimension whose size is the
                maximum number of sub-features in any instance.

        """
        g = self.read_vars

        profile_dimension = g["compression"][sample_dimension][
            "ragged_contiguous"
        ]["profile_dimension"]

        if is_log_level_debug(logger):
            logger.debug(
                "    Pre-processing indexed and contiguous compression "
                f"for instance dimension: {instance_dimension}\n"
                f"        sample_dimension  : {sample_dimension}\n"
                f"        instance_dimension: {instance_dimension}\n"
                f"        profile_dimension : {profile_dimension}"
            )  # pragma: no cover

        contiguous = g["compression"][sample_dimension]["ragged_contiguous"]
        indexed = g["compression"][profile_dimension]["ragged_indexed"]

        # The indices of the sample dimension which define the start
        # positions of each instances profiles
        profile_indices = indexed["index_variable"]

        # profiles_per_instance is a numpy array
        profiles_per_instance = indexed["elements_per_instance"]

        elements_per_profile = contiguous["count_variable"]

        instance_dimension_size = indexed["instance_dimension_size"]
        element_dimension_1_size = int(profiles_per_instance.max())
        element_dimension_2_size = int(
            self.implementation.get_data_maximum(elements_per_profile)
        )

        g["compression"][sample_dimension]["ragged_indexed_contiguous"] = {
            "count_variable": elements_per_profile,
            "index_variable": profile_indices,
            "implied_ncdimensions": (
                instance_dimension,
                indexed["element_dimension"],
                contiguous["element_dimension"],
            ),
            "instance_dimension_size": instance_dimension_size,
            "element_dimension_1_size": element_dimension_1_size,
            "element_dimension_2_size": element_dimension_2_size,
        }

        del g["compression"][sample_dimension]["ragged_contiguous"]

        if is_log_level_debug(logger):
            logger.debug(
                f"    Created read_vars['compression'][{sample_dimension!r}]"
                "['ragged_indexed_contiguous']\n"
                f"    Implied dimensions: {sample_dimension} -> "
                f"{g['compression'][sample_dimension]['ragged_indexed_contiguous']['implied_ncdimensions']}\n"
                "    Removed "
                f"read_vars['compression'][{sample_dimension!r}]['ragged_contiguous']"
            )  # pragma: no cover

    def _parse_geometry(self, parent_ncvar, attributes):
        """Parse a geometry container variable.

        .. versionadded:: (cfdm) 1.8.0

        :Parameters:

            parent_ncvar: `str`
                The netCDF variable name of the parent data variable.

            attributes: `dict`
                All attributes of *all* netCDF variables, keyed by netCDF
                variable name.

        :Returns:

            `str` or `None`
                 The new geometry netCDF variable name, or `None` if a)
                 the container has already been parsed or b) a
                 sufficiently compliant geometry container could not be
                 found.

        """
        g = self.read_vars

        geometry_attribute = attributes[parent_ncvar]["geometry"]

        parsed_geometry = self._split_string_by_white_space(
            parent_ncvar, geometry_attribute, variables=True
        )

        cf_compliant = self._check_geometry_attribute(
            parent_ncvar, geometry_attribute, parsed_geometry
        )
        if not cf_compliant:
            return

        geometry_ncvar = parsed_geometry[0]

        if geometry_ncvar in g["geometries"]:
            # We've already parsed this geometry container, so record
            # the fact that this parent netCDF variable has this
            # geometry variable and return.
            g["variable_geometry"][parent_ncvar] = geometry_ncvar
            return

        logger.info(
            f"    Geometry container = {geometry_ncvar!r}\n"
            f"        netCDF attributes: {attributes[geometry_ncvar]}"
        )  # pragma: no cover

        geometry_type = attributes[geometry_ncvar].get("geometry_type")

        g["geometries"][geometry_ncvar] = {"geometry_type": geometry_type}

        node_coordinates = attributes[geometry_ncvar].get("node_coordinates")
        node_count = attributes[geometry_ncvar].get("node_count")
        part_node_count = attributes[geometry_ncvar].get("part_node_count")
        interior_ring = attributes[geometry_ncvar].get("interior_ring")

        parsed_node_coordinates = self._split_string_by_white_space(
            geometry_ncvar, node_coordinates, variables=True
        )
        parsed_interior_ring = self._split_string_by_white_space(
            geometry_ncvar, interior_ring, variables=True
        )
        parsed_node_count = self._split_string_by_white_space(
            geometry_ncvar, node_count, variables=True
        )
        parsed_part_node_count = self._split_string_by_white_space(
            geometry_ncvar, part_node_count, variables=True
        )

        logger.info(
            f"        parsed_node_coordinates = {parsed_node_coordinates}\n"
            f"        parsed_interior_ring    = {parsed_interior_ring}\n"
            f"        parsed_node_count       = {parsed_node_count}\n"
            f"        parsed_part_node_count  = {parsed_part_node_count}"
        )  # pragma: no cover

        cf_compliant = True

        if interior_ring is not None and part_node_count is None:
            attribute = {
                parent_ncvar
                + ":geometry": attributes[parent_ncvar]["geometry"]
            }
            self._add_message(
                parent_ncvar,
                geometry_ncvar,
                message=("part_node_count attribute", "is missing"),
                attribute=attribute,
            )
            cf_compliant = False

        cf_compliant = cf_compliant & self._check_node_coordinates(
            parent_ncvar,
            geometry_ncvar,
            node_coordinates,
            parsed_node_coordinates,
        )

        cf_compliant = cf_compliant & self._check_node_count(
            parent_ncvar, geometry_ncvar, node_count, parsed_node_count
        )

        cf_compliant = cf_compliant & self._check_part_node_count(
            parent_ncvar,
            geometry_ncvar,
            part_node_count,
            parsed_part_node_count,
        )

        cf_compliant = cf_compliant & self._check_interior_ring(
            parent_ncvar, geometry_ncvar, interior_ring, parsed_interior_ring
        )

        if not cf_compliant:
            return

        part_dimension = None

        # Find the netCDF dimension for the total number of nodes
        node_dimension = g["variable_dimensions"][parsed_node_coordinates[0]][
            0
        ]

        logger.info(
            f"        node_dimension = {node_dimension!r}"
        )  # pragma: no cover

        if node_count is None:
            # --------------------------------------------------------
            # There is no node_count variable, so all geometries must
            # be size 1 point geometries => we can create a node_count
            # variable in this case.
            # --------------------------------------------------------
            nodes_per_geometry = self.implementation.initialise_Count()
            size = g["nc"].dimensions[node_dimension].size
            ones = self.implementation.initialise_Data(
                array=np.ones((size,), dtype="int32"), copy=False
            )
            self.implementation.set_data(nodes_per_geometry, data=ones)

            # --------------------------------------------------------
            # Cell dimension can not be taken from the node_count
            # variable (because it doesn't exist), so it has to be
            # taken from one of the node_coordinate variables,
            # instead.
            # --------------------------------------------------------
            geometry_dimension = g["variable_dimensions"][
                parsed_node_coordinates[0]
            ][0]
        else:
            # Find the netCDF dimension for the total number of cells
            node_count = parsed_node_count[0]
            geometry_dimension = g["variable_dimensions"][node_count][0]

            nodes_per_geometry = self._create_Count(
                ncvar=node_count, ncdim=geometry_dimension
            )

            # --------------------------------------------------------
            # Create a node count variable (which does not contain any
            # data)
            # --------------------------------------------------------
            nc = self._create_NodeCountProperties(ncvar=node_count)
            g["geometries"][geometry_ncvar]["node_count"] = nc

            # Do not attempt to create a field construct from a
            # netCDF part node count variable
            g["do_not_create_field"].add(node_count)

        # Record the netCDF node dimension as the sample dimension of
        # the count variable
        self.implementation.nc_set_sample_dimension(
            nodes_per_geometry, self._ncdim_abspath(node_dimension)
        )

        if part_node_count is None:
            # --------------------------------------------------------
            # There is no part_count variable, i.e. cell has exactly
            # one part.
            #
            # => we can treat the nodes as a contiguous ragged array
            # --------------------------------------------------------
            self._set_ragged_contiguous_parameters(
                elements_per_instance=nodes_per_geometry,
                sample_dimension=node_dimension,
                element_dimension="node",
                instance_dimension=geometry_dimension,
            )
        else:
            # --------------------------------------------------------
            # There is a part node count variable.
            #
            # => we must treat the nodes as an indexed contiguous
            # ragged array
            # --------------------------------------------------------
            part_node_count = parsed_part_node_count[0]

            # Do not attempt to create a field construct from a
            # netCDF part node count variable
            g["do_not_create_field"].add(part_node_count)

            part_dimension = g["variable_dimensions"][part_node_count][0]
            g["geometries"][geometry_ncvar]["part_dimension"] = part_dimension

            parts = self._create_Count(
                ncvar=part_node_count, ncdim=part_dimension
            )

            total_number_of_parts = self.implementation.get_data_size(parts)

            parts_data = self.implementation.get_data(parts)

            nodes_per_geometry_data = self.implementation.get_data(
                nodes_per_geometry
            )

            index = self.implementation.initialise_Index()
            self.implementation.set_data(index, data=parts_data)

            # Store the original file names
            self.implementation.set_original_filenames(index, g["filename"])

            instance_index = 0
            i = 0
            for cell_no in range(
                self.implementation.get_data_size(nodes_per_geometry)
            ):
                n_nodes_in_this_cell = int(nodes_per_geometry_data[cell_no])

                # Initialise partial_node_count, a running count of
                # how many nodes there are in this geometry
                n_nodes = 0

                for k in range(i, total_number_of_parts):
                    index.data[k] = instance_index
                    n_nodes += int(parts_data[k])
                    if n_nodes >= n_nodes_in_this_cell:
                        instance_index += 1
                        i += k + 1
                        break

            self._set_ragged_contiguous_parameters(
                elements_per_instance=parts,
                sample_dimension=node_dimension,
                element_dimension="node",
                instance_dimension=part_dimension,
            )

            indexed_sample_dimension = g["variable_dimensions"][
                part_node_count
            ][0]

            self._set_ragged_indexed_parameters(
                index=index,
                indexed_sample_dimension=indexed_sample_dimension,
                element_dimension="part",
                instance_dimension=geometry_dimension,
            )

            self._parse_indexed_contiguous_compression(
                sample_dimension=node_dimension,
                instance_dimension=geometry_dimension,
            )

            # --------------------------------------------------------
            # Create a part node count variable (which does not
            # contain any data)
            # --------------------------------------------------------
            pnc = self._create_PartNodeCount(
                ncvar=part_node_count, ncdim=part_dimension
            )
            g["geometries"][geometry_ncvar]["part_node_count"] = pnc

            # Do not attempt to create a field construct from a
            # netCDF part node count variable
            g["do_not_create_field"].add(part_node_count)

            # --------------------------------------------------------
            # Create an interior ring variable (do this after setting
            # up the indexed ragged array compression parameters).
            # --------------------------------------------------------
            if parsed_interior_ring:
                interior_ring = parsed_interior_ring[0]
                part_dimension = g["variable_dimensions"][interior_ring][0]
                i_r = self._create_InteriorRing(
                    ncvar=interior_ring, ncdim=part_dimension
                )
                g["geometries"][geometry_ncvar]["interior_ring"] = i_r

                # Record that this netCDF interor ring variable spans
                # a compressed dimension
                g["compression"][indexed_sample_dimension].setdefault(
                    "netCDF_variables", set()
                ).update(parsed_interior_ring)

                # Do not attempt to create a field from an
                # interior ring variable
                g["do_not_create_field"].add(interior_ring)

        # Record which the netCDF node variables span the compressed
        # dimension
        g["compression"][node_dimension].setdefault(
            "netCDF_variables", set()
        ).update(parsed_node_coordinates)

        # Do not attempt to create field constructs from netCDF node
        # coordinate variables
        g["do_not_create_field"].update(parsed_node_coordinates)

        g["geometries"][geometry_ncvar].update(
            {
                "node_coordinates": parsed_node_coordinates,
                "geometry_dimension": geometry_dimension,
                "node_dimension": node_dimension,
            }
        )

        # Record the fact that this parent netCDF variable has a
        # geometry variable
        g["variable_geometry"][parent_ncvar] = geometry_ncvar

        return geometry_ncvar

    def _set_ragged_contiguous_parameters(
        self,
        elements_per_instance=None,
        sample_dimension=None,
        element_dimension=None,
        instance_dimension=None,
    ):
        """Set the DSG ragged contiguous compression global attributes.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            elements_per_instance: `Count`

            sample_dimension: `str`

            element_dimension: `str`

            instance_dimension: `str`

        :Returns:

            `str`
               The element dimension, possibly modified to make sure that it
               is unique.

        """
        g = self.read_vars

        instance_dimension_size = self.implementation.get_data_size(
            elements_per_instance
        )
        element_dimension_size = int(
            self.implementation.get_data_maximum(elements_per_instance)
        )

        # Make sure that the element dimension name is unique
        element_dimension = self._new_ncdimension(
            element_dimension, element_dimension_size
        )

        g["compression"].setdefault(sample_dimension, {})[
            "ragged_contiguous"
        ] = {
            "count_variable": elements_per_instance,
            "implied_ncdimensions": (instance_dimension, element_dimension),
            "profile_dimension": instance_dimension,
            "element_dimension": element_dimension,
            "element_dimension_size": element_dimension_size,
            "instance_dimension_size": instance_dimension_size,
        }

        return element_dimension

    def _set_ragged_indexed_parameters(
        self,
        index=None,
        indexed_sample_dimension=None,
        element_dimension=None,
        instance_dimension=None,
    ):
        """Set the DSG ragged indexed compression global attributes.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            index: `Index`

            element_dimension: `str`

            instance_dimension: `str`

        :Returns:

            `str`
               The element dimension, possibly modified to make sure that it
               is unique.

        """
        g = self.read_vars

        (_, count) = np.unique(index.data.array, return_counts=True)

        # The number of elements per instance. For the instances array
        # example above, the elements_per_instance array is [7, 5, 7].
        elements_per_instance = count  # self._create_Data(array=count)

        instance_dimension_size = g["internal_dimension_sizes"][
            instance_dimension
        ]

        element_dimension_size = int(elements_per_instance.max())
        element_dimension = self._new_ncdimension(
            element_dimension, element_dimension_size
        )

        g["compression"].setdefault(indexed_sample_dimension, {})[
            "ragged_indexed"
        ] = {
            "elements_per_instance": elements_per_instance,
            "index_variable": index,
            "implied_ncdimensions": (instance_dimension, element_dimension),
            "element_dimension": element_dimension,
            "instance_dimension_size": instance_dimension_size,
            "element_dimension_size": element_dimension_size,
        }

        if is_log_level_debug(logger):
            logger.debug(
                "    Created "
                f"read_vars['compression'][{indexed_sample_dimension!r}]['ragged_indexed']"
            )  # pragma: no cover

        return element_dimension

    def _check_external_variables(
        self, external_variables, parsed_external_variables
    ):
        """Check that named external variables do not exist in the file.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            external_variables: `str`
                The external_variables attribute as found in the file.

            parsed_external_variables: `list`
                The external_variables attribute parsed into a list of
                external variable names.

        :Returns:

            `list`
                The external variable names, less those which are also
                netCDF variables in the file.

        """
        g = self.read_vars

        attribute = {"external_variables": external_variables}
        message = ("External variable", "exists in the file")

        out = []

        for ncvar in parsed_external_variables:
            if ncvar not in g["internal_variables"]:
                out.append(ncvar)
            else:
                self._add_message(
                    None, ncvar, message=message, attribute=attribute
                )

        return out

    def _check_formula_terms(
        self, field_ncvar, coord_ncvar, formula_terms, z_ncdim=None
    ):
        """Check formula_terms for CF-compliance.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            field_ncvar: `str`

            coord_ncvar: `str`

            formula_terms: `str`
                A CF-netCDF formula_terms attribute.

        """
        # ============================================================
        # CF-1.7 7.1. Cell Boundaries
        #
        # If a parametric coordinate variable with a formula_terms
        # attribute (section 4.3.2) also has a bounds attribute, its
        # boundary variable must have a formula_terms attribute
        # too. In this case the same terms would appear in both (as
        # specified in Appendix D), since the transformation from the
        # parametric coordinate values to physical space is realised
        # through the same formula.  For any term that depends on the
        # vertical dimension, however, the variable names appearing in
        # the formula terms would differ from those found in the
        # formula_terms attribute of the coordinate variable itself
        # because the boundary variables for formula terms are
        # two-dimensional while the formula terms themselves are
        # one-dimensional.
        #
        # Whenever a formula_terms attribute is attached to a boundary
        # variable, the formula terms may additionally be identified
        # using a second method: variables appearing in the vertical
        # coordinates' formula_terms may be declared to be coordinate,
        # scalar coordinate or auxiliary coordinate variables, and
        # those coordinates may have bounds attributes that identify
        # their boundary variables. In that case, the bounds attribute
        # of a formula terms variable must be consistent with the
        # formula_terms attribute of the boundary variable. Software
        # digesting legacy datasets (constructed prior to version 1.7
        # of this standard) may have to rely in some cases on the
        # first method of identifying the formula term variables and
        # in other cases, on the second. Starting from version 1.7,
        # however, the first method will be sufficient.
        # ============================================================

        g = self.read_vars

        attribute = {coord_ncvar + ":formula_terms": formula_terms}

        g["formula_terms"].setdefault(coord_ncvar, {"coord": {}, "bounds": {}})

        parsed_formula_terms = self._parse_x(coord_ncvar, formula_terms)

        incorrectly_formatted = (
            "formula_terms attribute",
            "is incorrectly formatted",
        )

        if not parsed_formula_terms:
            self._add_message(
                field_ncvar,
                coord_ncvar,
                message=incorrectly_formatted,
                attribute=attribute,
            )
            return False

        self._ncdimensions(field_ncvar)

        for x in parsed_formula_terms:
            term, values = list(x.items())[0]

            g["formula_terms"][coord_ncvar]["coord"][term] = None

            if len(values) != 1:
                self._add_message(
                    field_ncvar,
                    coord_ncvar,
                    message=incorrectly_formatted,
                    attribute=attribute,
                )
                continue

            ncvar = values[0]

            if ncvar not in g["internal_variables"]:
                ncvar, message = self._missing_variable(
                    ncvar, "Formula terms variable"
                )

                self._add_message(
                    field_ncvar, ncvar, message=message, attribute=attribute
                )
                continue

            g["formula_terms"][coord_ncvar]["coord"][term] = ncvar

        bounds_ncvar = g["variable_attributes"][coord_ncvar].get("bounds")

        if bounds_ncvar is None:
            # --------------------------------------------------------
            # Parametric Z coordinate does not have bounds
            # --------------------------------------------------------
            for term in g["formula_terms"][coord_ncvar]["coord"]:
                g["formula_terms"][coord_ncvar]["bounds"][term] = None
        else:
            # --------------------------------------------------------
            # Parametric Z coordinate has bounds
            # --------------------------------------------------------
            bounds_formula_terms = g["variable_attributes"][bounds_ncvar].get(
                "formula_terms"
            )
            if bounds_formula_terms is not None:
                # ----------------------------------------------------
                # Parametric Z coordinate has bounds, and the bounds
                # variable has a formula_terms attribute
                # ----------------------------------------------------
                bounds_attribute = {
                    bounds_ncvar + ":formula_terms": bounds_formula_terms
                }

                parsed_bounds_formula_terms = self._parse_x(
                    bounds_ncvar, bounds_formula_terms
                )

                if not parsed_bounds_formula_terms:
                    self._add_message(
                        field_ncvar,
                        bounds_ncvar,
                        message=(
                            "Bounds formula_terms attribute",
                            "is incorrectly formatted",
                        ),
                        attribute=attribute,
                        variable=coord_ncvar,
                    )

                for x in parsed_bounds_formula_terms:
                    term, values = list(x.items())[0]

                    g["formula_terms"][coord_ncvar]["bounds"][term] = None

                    if len(values) != 1:
                        self._add_message(
                            field_ncvar,
                            bounds_ncvar,
                            message=(
                                "Bounds formula_terms attribute",
                                "is incorrectly formatted",
                            ),
                            attribute=bounds_attribute,
                            variable=coord_ncvar,
                        )
                        continue

                    ncvar = values[0]

                    if ncvar not in g["internal_variables"]:
                        ncvar, message = self._missing_variable(
                            ncvar, "Bounds formula terms variable"
                        )

                        self._add_message(
                            field_ncvar,
                            ncvar,
                            message=message,
                            attribute=bounds_attribute,
                            variable=coord_ncvar,
                        )
                        continue

                    if term not in g["formula_terms"][coord_ncvar]["coord"]:
                        self._add_message(
                            field_ncvar,
                            bounds_ncvar,
                            message=(
                                "Bounds formula_terms attribute",
                                "has incompatible terms",
                            ),
                            attribute=bounds_attribute,
                            variable=coord_ncvar,
                        )
                        continue

                    parent_ncvar = g["formula_terms"][coord_ncvar]["coord"][
                        term
                    ]

                    d_ncdims = g["variable_dimensions"][parent_ncvar]
                    dimensions = g["variable_dimensions"][ncvar]

                    if z_ncdim not in d_ncdims:
                        if ncvar != parent_ncvar:
                            self._add_message(
                                field_ncvar,
                                bounds_ncvar,
                                message=(
                                    "Bounds formula terms variable",
                                    "that does not span the vertical "
                                    "dimension is inconsistent with the "
                                    "formula_terms of the parametric "
                                    "coordinate variable",
                                ),
                                attribute=bounds_attribute,
                                variable=coord_ncvar,
                            )
                            continue

                    elif len(dimensions) != len(d_ncdims) + 1:
                        self._add_message(
                            field_ncvar,
                            bounds_ncvar,
                            message=(
                                "Bounds formula terms variable",
                                "spans incorrect dimensions",
                            ),
                            attribute=bounds_attribute,
                            dimensions=dimensions,
                            variable=coord_ncvar,
                        )
                        continue
                    # WRONG - need to account for char arrays:
                    elif d_ncdims != dimensions[:-1]:
                        self._add_message(
                            field_ncvar,
                            bounds_ncvar,
                            message=(
                                "Bounds formula terms variable",
                                "spans incorrect dimensions",
                            ),
                            attribute=bounds_attribute,
                            dimensions=dimensions,
                            variable=coord_ncvar,
                        )
                        continue

                    # Still here?
                    g["formula_terms"][coord_ncvar]["bounds"][term] = ncvar

                if set(g["formula_terms"][coord_ncvar]["coord"]) != set(
                    g["formula_terms"][coord_ncvar]["bounds"]
                ):
                    self._add_message(
                        field_ncvar,
                        bounds_ncvar,
                        message=(
                            "Bounds formula_terms attribute",
                            "has incompatible terms",
                        ),
                        attribute=bounds_attribute,
                        variable=coord_ncvar,
                    )

            else:
                # ----------------------------------------------------
                # Parametric Z coordinate has bounds, but the bounds
                # variable does not have a formula_terms attribute =>
                # Infer the formula terms bounds variables from the
                # coordinates
                # ----------------------------------------------------
                for term, ncvar in g["formula_terms"][coord_ncvar][
                    "coord"
                ].items():
                    g["formula_terms"][coord_ncvar]["bounds"][term] = None

                    if z_ncdim not in self._ncdimensions(ncvar):
                        g["formula_terms"][coord_ncvar]["bounds"][term] = ncvar
                        continue

                    is_coordinate_with_bounds = False
                    for c_ncvar in g["coordinates"][field_ncvar]:
                        if ncvar != c_ncvar:
                            continue

                        is_coordinate_with_bounds = True

                        if z_ncdim not in g["variable_dimensions"][c_ncvar]:
                            # Coordinates do not span the Z dimension
                            g["formula_terms"][coord_ncvar]["bounds"][
                                term
                            ] = ncvar
                        else:
                            # Coordinates span the Z dimension
                            b = g["bounds"][field_ncvar].get(ncvar)
                            if b is not None:
                                g["formula_terms"][coord_ncvar]["bounds"][
                                    term
                                ] = b
                            else:
                                is_coordinate_with_bounds = False

                        break

                    if not is_coordinate_with_bounds:
                        self._add_message(
                            field_ncvar,
                            ncvar,
                            message=(
                                "Formula terms variable",
                                "that spans the vertical dimension "
                                "has no bounds",
                            ),
                            attribute=attribute,
                            variable=coord_ncvar,
                        )

    def _missing_variable(self, ncvar, message0):
        """Return the name of a missing variable with a message.

        .. versionaddedd:: (cfdm) 1.8.6.0

         :Parameters:

             ncvar: `str`

             message0: `str`

         :Returns:

             `str`, `tuple`
                 The (possibly modified) netCDF variable name, and the
                 appropriate full message about it being missing.

        """
        if self.read_vars["has_groups"]:
            message = (message0, "is not locatable in the group hierarchy")
            if ncvar.startswith("REF_NOT_FOUND:_"):
                ncvar = ncvar.replace("REF_NOT_FOUND:_", "", 1)
        else:
            message = (message0, "is not in file")

        return ncvar, message

    def _create_field_or_domain(
        self, field_ncvar, domain=False, location=None
    ):
        """Create a field or domain for a given netCDF variable.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

        field_ncvar: `str`
            The name of the netCDF variable to be turned into a field
            or domain construct.

        domain: `bool`, otpional
            If True then only read and parse domain variables into
            domain consrtucts. By default only data variables are read
            and parsed into field constructs.

            .. versionadded:: (cfdm) 1.9.0.0

        location: `str`, otpional
            The location of cells on a UGRID mesh topology. Ignored
            unless *domain* is True.

            .. versionadded:: (cfdm) UGRIDVER

        :Returns:

            `Field` or `Domain`

        """
        g = self.read_vars

        field = not domain

        # Whether or not we're attempting to a create a domain
        # construct from a URGID mesh topology variable
        mesh_topology = domain and field_ncvar in g["mesh"]
        if mesh_topology and location is None:
            raise ValueError(
                "Must set 'location' to create a domain construct from "
                "a URGID mesh topology variable"
            )

        if field:
            construct_type = "Field"
        else:
            construct_type = "Domain"

        # Reset the dimensions of a domain variable
        g["domain_ncdimensions"] = {}

        # Reset 'domain_ancillary_key'
        g["domain_ancillary_key"] = {}

        dimensions = g["variable_dimensions"][field_ncvar]
        g["dataset_compliance"].setdefault(field_ncvar, {})
        g["dataset_compliance"][field_ncvar][
            "CF version"
        ] = self.implementation.get_cf_version()
        g["dataset_compliance"][field_ncvar]["dimensions"] = dimensions
        g["dataset_compliance"][field_ncvar].setdefault("non-compliance", {})

        logger.info(
            "    Converting netCDF variable "
            f"{field_ncvar}({', '.join(dimensions)}) to a {construct_type}:"
        )  # pragma: no cover

        # ------------------------------------------------------------
        # Combine the global and group properties with the data
        # variable properties, giving precedence to those of the data
        # variable and then those of any groups.
        # ------------------------------------------------------------
        field_properties = g["global_attributes"].copy()

        if g["has_groups"]:
            field_properties.update(
                g["variable_group_attributes"][field_ncvar]
            )

        field_properties.update(g["variable_attributes"][field_ncvar])

        if is_log_level_debug(logger):
            logger.debug(
                "        netCDF attributes:\n"
                f"            {field_properties}"
            )  # pragma: no cover

        if field:
            # Take cell_methods out of the data variable's properties
            # since it will need special processing once the domain
            # has been defined
            cell_methods_string = field_properties.pop("cell_methods", None)

            # Take add_offset and scale_factor out of the data
            # variable's properties since they will be dealt with by
            # the variable's Data object. Makes sure we note that they
            # were there so we can adjust the field's data type
            # accordingly.
            values = [
                field_properties.pop(k, None)
                for k in ("add_offset", "scale_factor")
            ]
            unpacked_dtype = values != [None, None]
            if unpacked_dtype:
                try:
                    values.remove(None)
                except ValueError:
                    pass

                unpacked_dtype = np.result_type(*values)

        # Initialise node_coordinates_as_bounds
        g["node_coordinates_as_bounds"] = set()

        # ------------------------------------------------------------
        # Initialise the field/domain
        # ------------------------------------------------------------
        if field:
            # Create a field construct
            f = self.implementation.initialise_Field()
        else:
            # Create a domain construct
            f = self.implementation.initialise_Domain()

        self.implementation.set_properties(f, field_properties, copy=True)

        if field and not g["mask"]:
            # --------------------------------------------------------
            # Masking has been turned off, so make sure that there is
            # a fill value recorded on the field so that masking may
            # later be applied manually, if required. (Introduced at
            # v1.8.2)
            # --------------------------------------------------------
            self._set_default_FillValue(f, field_ncvar)

        # Store the netCDF variable name of the field/domain
        self.implementation.nc_set_variable(f, field_ncvar)

        # ------------------------------------------------------------
        # Store the netCDF global attributes for the field/domain
        # ------------------------------------------------------------
        x = g["global_attributes"].copy()
        for k, v in g["global_attributes"].items():
            if (
                k not in g["variable_attributes"][field_ncvar]
                and k not in g["variable_group_attributes"][field_ncvar]
            ):
                x[k] = None

        self.implementation.nc_set_global_attributes(f, x)

        # ------------------------------------------------------------
        # Store the data/domain variable's group-level attributes
        # ------------------------------------------------------------
        if g["has_groups"]:
            x = g["variable_group_attributes"][field_ncvar].copy()
            for k, v in g["variable_group_attributes"][field_ncvar].items():
                if k not in g["variable_attributes"][field_ncvar]:
                    x[k] = None

            self.implementation.nc_set_group_attributes(f, x)

        # ------------------------------------------------------------
        # Remove the field/domain construct's "geometry" property,
        # saving its value
        # ------------------------------------------------------------
        if g["CF>=1.8"]:
            geometry = self.implementation.del_property(f, "geometry", None)
            if geometry is not None:
                self.implementation.nc_set_geometry_variable(f, geometry)

        # Map netCDF dimension names to domain axis identifiers.
        #
        # For example: {'lat': 'dim0', 'time': 'dim1'}
        ncdim_to_axis = {}
        g["ncdim_to_axis"] = ncdim_to_axis

        # Map domain axis identifiers to netCDF dimension names
        #
        # For example: {'dim0': 'lat', 'dim1': 'time'}
        axis_to_ncdim = {}
        g["axis_to_ncdim"] = axis_to_ncdim

        ncscalar_to_axis = {}

        # Map netCDF variable names to internal identifiers
        #
        # For example: {'dimensioncoordinate1': 'time'}
        ncvar_to_key = {}

        data_axes = []

        # ------------------------------------------------------------
        # Add axes and non-scalar dimension coordinates to the
        # field/domain
        # ------------------------------------------------------------
        has_dimensions_attr = self.implementation.has_property(f, "dimensions")
        ndim = g["variables"][field_ncvar].ndim

        if field:
            if g["CF>=1.9"] and has_dimensions_attr:
                # ----------------------------------------------------
                # This netCDF scalar variable has a 'dimensions'
                # attribute. Therefore it is a domain variable and is
                # to be ignored. CF>=1.9 (Introduced at v1.9.0.0)
                # ----------------------------------------------------
                logger.info(
                    f"        {field_ncvar} is a domain variable"
                )  # pragma: no cover

                return None

            ncdimensions = None
        else:
            if not mesh_topology and (
                not g["CF>=1.9"] or not has_dimensions_attr or ndim >= 1
            ):
                # ----------------------------------------------------
                # This netCDF variable (which is not a UGRID mesh
                # topology nor a location index set variable) is not
                # scalar, or does not have a 'dimensions'
                # attribute. Therefore it is not a domain variable and
                # is to be ignored. CF>=1.9 (Introduced at v1.9.0.0)
                # ----------------------------------------------------
                logger.info(
                    f"        {field_ncvar} is not a domain variable"
                )  # pragma: no cover

                return None

            # --------------------------------------------------------
            # Get the netCDF dimensions for the domain variable from
            # the 'dimensions' property. CF>=1.9. (Introduced at
            # v1.9.0.0)
            # --------------------------------------------------------
            domain_dimensions = self.implementation.del_property(
                f, "dimensions", None
            )

            ncdimensions = self._split_string_by_white_space(
                field_ncvar, domain_dimensions, variables=True
            )

        field_ncdimensions = self._ncdimensions(
            field_ncvar, ncdimensions=ncdimensions
        )

        field_groups = g["variable_groups"][field_ncvar]

        for ncdim in field_ncdimensions:
            ncvar, method = self._find_coordinate_variable(
                field_ncvar, field_groups, ncdim
            )

            if ncvar is not None:
                # There is a Unidata coordinate variable for this
                # dimension, so create a domain axis and dimension
                # coordinate
                if ncvar in g["dimension_coordinate"]:
                    coord = self._copy_construct(
                        "dimension_coordinate", field_ncvar, ncvar
                    )
                else:
                    coord = self._create_dimension_coordinate(
                        field_ncvar, ncvar, f
                    )
                    g["dimension_coordinate"][ncvar] = coord

                size = self.implementation.get_construct_data_size(coord)
                domain_axis = self._create_domain_axis(size, ncdim)

                logger.detail(
                    f"        [a] Inserting {domain_axis.__class__.__name__} "
                    "with size {size}"
                )  # pragma: no cover
                axis = self.implementation.set_domain_axis(
                    f, construct=domain_axis, copy=False
                )

                logger.detail(
                    f"        [b] Inserting {coord.__class__.__name__}"
                    f"{method} with size {coord.size}"
                )  # pragma: no cover
                dim = self.implementation.set_dimension_coordinate(
                    f, construct=coord, axes=[axis], copy=False
                )

                self._reference(ncvar, field_ncvar)
                if coord.has_bounds():
                    bounds = self.implementation.get_bounds(coord)
                    self._reference(
                        self.implementation.nc_get_variable(bounds),
                        field_ncvar,
                    )

                # Set unlimited status of axis
                #                if nc.dimensions[ncdim].isunlimited():
                if g["dimension_isunlimited"][ncdim]:
                    self.implementation.nc_set_unlimited_axis(f, axis)

                ncvar_to_key[ncvar] = dim
                g["coordinates"].setdefault(field_ncvar, []).append(ncvar)

            else:
                # There is no dimension coordinate for this dimension,
                # so just create a domain axis with the correct size.
                if ncdim in g["new_dimension_sizes"]:
                    size = g["new_dimension_sizes"][ncdim]
                else:
                    size = g["internal_dimension_sizes"][ncdim]

                domain_axis = self._create_domain_axis(size, ncdim)
                logger.detail(
                    f"        [c] Inserting {domain_axis.__class__.__name__} "
                    f"with size {size}"
                )  # pragma: no cover
                axis = self.implementation.set_domain_axis(
                    f, construct=domain_axis, copy=False
                )

                # Set unlimited status of axis
                try:
                    # if nc.dimensions[ncdim].isunlimited():
                    if g["dimension_isunlimited"][ncdim]:
                        self.implementation.nc_set_unlimited_axis(f, axis)
                except KeyError:
                    # This dimension is not in the netCDF file (as
                    # might be the case for an element dimension
                    # implied by a ragged array).
                    pass

            # Update data dimension name and set dimension size
            data_axes.append(axis)

            ncdim_to_axis[ncdim] = axis
            axis_to_ncdim[axis] = ncdim

        # ------------------------------------------------------------
        # Add the data to the field
        # ------------------------------------------------------------
        if field:
            data = self._create_data(
                field_ncvar, f, unpacked_dtype=unpacked_dtype
            )
            logger.detail(
                f"        [d] Inserting field {data.__class__.__name__}"
                f"{data.shape}"
            )  # pragma: no cover

            self.implementation.set_data(f, data, axes=data_axes, copy=False)

        # Store the original file names
        self.implementation.set_original_filenames(f, g["filename"])

        # ------------------------------------------------------------
        # Add auxiliary coordinate constructs derived from UGRID
        #
        # It is important to do this prior to creating auxiliary
        # coordinates from the "coordinates" attribute.
        # ------------------------------------------------------------
        ugrid = g["UGRID_version"] is not None
        if ugrid:
            if mesh_topology:
                # We are creating a UGRID domain construct, for which
                # 'location' has already been set as a keyword
                # parameter.
                mesh = g["mesh"][field_ncvar]
                mesh_ncvar = mesh.mesh_ncvar
                location_index_set_ncvar = mesh.location_index_set_ncvar
                ncdim = mesh.ncdim.get(location)
                if not ncdim:
                    return

                ugrid = True

                # Create the domain axis construct for this location
                # of the mesh topology
                if ncdim in g["new_dimension_sizes"]:
                    size = g["new_dimension_sizes"][ncdim]
                else:
                    size = g["internal_dimension_sizes"][ncdim]

                domain_axis = self._create_domain_axis(size, ncdim)
                logger.detail(
                    f"        [o] Inserting {domain_axis.__class__.__name__} "
                    f"with size {size}"
                )  # pragma: no cover
                axis = self.implementation.set_domain_axis(
                    f, construct=domain_axis, copy=False
                )
                ncdim_to_axis[ncdim] = axis
            else:
                # We are creating a field construct or a non-UGRID
                # domain construct
                mesh_ncvar = self.implementation.get_property(f, "mesh")
                location_index_set_ncvar = self.implementation.get_property(
                    f, "location_index_set"
                )
                ugrid = (
                    mesh_ncvar is not None
                    or location_index_set_ncvar is not None
                )

        ugrid_aux_ncvars = []
        if ugrid:
            if not mesh_topology:
                # Find the mesh defintion and location on the mesh
                ok = False
                if mesh_ncvar is not None:
                    ok = self._ugrid_check_field_mesh(
                        field_ncvar,
                        mesh_ncvar,
                    )

                    if ok:
                        mesh = g["mesh"][mesh_ncvar]
                        location = self.implementation.get_property(
                            f, "location"
                        )
                elif location_index_set_ncvar is not None:
                    ok = self._ugrid_check_field_location_index_set(
                        field_ncvar, location_index_set_ncvar
                    )
                    if ok:
                        mesh = g["mesh"][location_index_set_ncvar]
                        location = mesh.location

                if not ok:
                    # There's something wrong with the UGRID
                    # encoding. Set 'ugrid' to False so that no
                    # further UGRID related stuff occurs.
                    ugrid = False

            if ugrid:
                # The UGRID specification is OK, so get the auxiliary
                # coordinates.
                if location == "volume":
                    raise NotImplementedError(
                        "Can't read datasets with UGRID volume cells"
                    )

                # Remove mesh-related properties
                if mesh_topology:
                    if location_index_set_ncvar is not None:
                        attrs = ("mesh", "location")
                    else:
                        attrs = self.ugrid_mesh_topology_attributes()
                elif mesh_ncvar is not None:
                    attrs = ("mesh", "location")
                else:
                    attrs = ("location_index_set",)

                self.implementation.del_properties(f, attrs)

                # Find the discrete axis for the mesh topology
                ugrid_ncdim = mesh.ncdim.get(location)
                if ugrid_ncdim is None:
                    # We couldn't find the UGRID discrete axis, so
                    # there must be something wrong with the UGRID
                    # encoding. Set 'ugrid' to False so that no
                    # further UGRID related stuff occurs.
                    ugrid = False
                else:
                    # There is a UGRID discrete axis, so create
                    # auxiliary coordinate constructs derived from the
                    # mesh topology.
                    ugrid_axis = ncdim_to_axis[ugrid_ncdim]
                    for aux in mesh.auxiliary_coordinates.get(location, ()):
                        key = self.implementation.set_auxiliary_coordinate(
                            f,
                            aux,
                            axes=ugrid_axis,
                            copy=True,
                        )
                        ncvar = self.implementation.nc_get_variable(aux)

                        ugrid_aux_ncvars.append(ncvar)

                        g["auxiliary_coordinate"][ncvar] = aux
                        ncvar_to_key[ncvar] = key

                        self._reference(ncvar, field_ncvar)
                        if self.implementation.has_bounds(aux):
                            bounds = self.implementation.get_bounds(aux)
                            self._reference(
                                self.implementation.nc_get_variable(bounds),
                                field_ncvar,
                            )

        # ------------------------------------------------------------
        # Add scalar dimension coordinates and auxiliary coordinates
        # to the field/domain
        # ------------------------------------------------------------
        coordinates = self.implementation.del_property(f, "coordinates", None)

        parsed_coordinates = []
        if coordinates is not None:
            parsed_coordinates = self._split_string_by_white_space(
                field_ncvar, coordinates, variables=True
            )

            for ncvar in parsed_coordinates:
                # Skip dimension coordinates
                if ncvar in field_ncdimensions:
                    continue

                # Skip auxiliary coordinates that have already been
                # created from a UGRID mesh
                if ugrid and ncvar in ugrid_aux_ncvars:
                    continue

                cf_compliant = self._check_auxiliary_or_scalar_coordinate(
                    field_ncvar, ncvar, coordinates
                )
                if not cf_compliant:
                    continue

                # Set dimensions for this variable
                dimensions = self._get_domain_axes(
                    ncvar, parent_ncvar=field_ncvar
                )

                if ncvar in g["auxiliary_coordinate"]:
                    coord = g["auxiliary_coordinate"][ncvar].copy()
                else:
                    coord = self._create_auxiliary_coordinate(
                        field_ncvar, ncvar, f
                    )
                    g["auxiliary_coordinate"][ncvar] = coord

                # ----------------------------------------------------
                # Turn a
                # ----------------------------------------------------
                is_scalar_dimension_coordinate = False
                scalar = False
                if not dimensions:
                    scalar = True
                    if self._is_char_or_string(ncvar):
                        # String valued scalar coordinate. Turn it
                        # into a 1-d auxiliary coordinate construct.
                        domain_axis = self._create_domain_axis(1)
                        logger.detail(
                            "        [d] Inserting "
                            f"{domain_axis.__class__.__name__} with size 1"
                        )  # pragma: no cover
                        dim = self.implementation.set_domain_axis(
                            f, domain_axis
                        )

                        dimensions = [dim]

                        coord = self.implementation.construct_insert_dimension(
                            construct=coord, position=0
                        )
                        g["auxiliary_coordinate"][ncvar] = coord
                    else:
                        # Numeric valued scalar coordinate
                        is_scalar_dimension_coordinate = True

                if is_scalar_dimension_coordinate:
                    # Insert a domain axis and dimension coordinate
                    # derived from a numeric scalar auxiliary
                    # coordinate.

                    # First turn the scalar auxiliary corodinate into
                    # a 1-d auxiliary coordinate construct
                    coord = self.implementation.construct_insert_dimension(
                        construct=coord, position=0
                    )

                    # Now turn the 1-d size 1 auxiliary coordinate
                    # into a dimension coordinate
                    coord = self.implementation.initialise_DimensionCoordinate_from_AuxiliaryCoordinate(
                        auxiliary_coordinate=coord, copy=False
                    )

                    size = self.implementation.get_construct_data_size(coord)
                    domain_axis = self._create_domain_axis(size)
                    logger.detail(
                        "        [e] Inserting "
                        f"{domain_axis.__class__.__name__} with size {size}"
                    )  # pragma: no cover
                    axis = self.implementation.set_domain_axis(
                        f, construct=domain_axis, copy=False
                    )

                    logger.detail(
                        f"        [e] Inserting {coord.__class__.__name__} "
                        f"with size {coord.size}"
                    )  # pragma: no cover
                    dim = self.implementation.set_dimension_coordinate(
                        f, coord, axes=[axis], copy=False
                    )

                    self._reference(ncvar, field_ncvar)
                    if self.implementation.has_bounds(coord):
                        bounds = self.implementation.get_bounds(coord)
                        self._reference(
                            self.implementation.nc_get_variable(bounds),
                            field_ncvar,
                        )

                    dimensions = [axis]
                    ncvar_to_key[ncvar] = dim

                    g["dimension_coordinate"][ncvar] = coord
                    del g["auxiliary_coordinate"][ncvar]
                else:
                    # Insert auxiliary coordinate
                    logger.detail(
                        f"        [f] Inserting {coord.__class__.__name__} "
                        f"with size {coord.size}"
                    )  # pragma: no cover

                    aux = self.implementation.set_auxiliary_coordinate(
                        f, coord, axes=dimensions, copy=False
                    )

                    self._reference(ncvar, field_ncvar)
                    if self.implementation.has_bounds(coord):
                        bounds = self.implementation.get_bounds(coord)
                        self._reference(
                            self.implementation.nc_get_variable(bounds),
                            field_ncvar,
                        )

                    ncvar_to_key[ncvar] = aux

                if scalar:
                    ncscalar_to_axis[ncvar] = dimensions[0]

        # ------------------------------------------------------------
        # Add dimension or auxiliary coordinate constructs derived
        # from from tie point coordinate variables and bounds tie
        # point variables (CF>=1.9)
        #
        # Note on methodology: All of the coordinate constructs must
        #                      be created before any are set on the
        #                      parent field/domain construct. This is
        #                      so that constructs with multivariate
        #                      interpolation methods can be modified
        #                      to contain their dependent tie points.
        #
        # ------------------------------------------------------------
        string = self.implementation.del_property(
            f, "coordinate_interpolation", None
        )
        tie_point_ncvars = g["tie_point_ncvar"].get(field_ncvar, ())

        coordinates = {}
        for ncvar in tie_point_ncvars:
            ok = self._check_tie_point_coordinates(field_ncvar, ncvar, string)
            if not ok:
                continue

            # Find out if the coordinates are to be dimension or
            # auxiliary coordinate constructs
            axes = self._get_domain_axes(ncvar, parent_ncvar=field_ncvar)
            is_dimension_coordinate = len(axes) == 1 and ncvar == g[
                "axis_to_ncdim"
            ].get(axes[0])

            # Don't try to use an existing coordinate object derived
            # from this netCDF variable, since such an instance may
            # have been created from a different interpolation
            # variable (and therefore could have used different tie
            # point indices).
            if is_dimension_coordinate:
                coord = self._create_dimension_coordinate(
                    field_ncvar, ncvar, f
                )
            else:
                coord = self._create_auxiliary_coordinate(
                    field_ncvar, ncvar, f
                )

            coordinates[ncvar] = (coord, axes, is_dimension_coordinate)

        # Add any dependent tie points required for multivariate
        # interpolations. This allows each coordinate to be operated
        # on (e.g. subspaced, collapsed, etc.) independently.
        #
        # For example, when decompression is by the
        # quadratic_latitude_longitude method, the interpolation of
        # latitudes depends on the longitude, and vice verse -
        # e.g. uncompressed latitudes = f(subsampled latitudes,
        # subsampled longitudes). So that the latitude coordinate
        # construct can be accessed independently of the longitude
        # construct, the longitude tie points need to be stored within
        # the latitude coordinate construct.
        multivariate_interpolations = self.cf_multivariate_interpolations()
        for (
            ncvar,
            (coord, axes, is_dimension_coordinate),
        ) in coordinates.items():
            compression_type = self.implementation.get_compression_type(coord)
            if compression_type != "subsampled":
                continue

            interpolation_name = self.implementation.get_interpolation_name(
                coord
            )
            identities = multivariate_interpolations.get(interpolation_name)
            if not identities:
                continue

            bounds = self.implementation.get_bounds(coord, default=None)

            tp_dims = {}
            c_tp = {}
            b_tp = {}
            for n, (c, a, _) in coordinates.items():
                if n == ncvar:
                    continue

                if (
                    self.implementation.get_interpolation_name(c)
                    != interpolation_name
                ):
                    continue

                for identity in identities:
                    if not self._has_identity(c, identity):
                        continue

                    tp_dims[identity] = tuple([a.index(i) for i in axes])

                    c_tp[identity] = self.implementation.get_tie_points(c)
                    if bounds is None:
                        continue

                    b = self.implementation.get_bounds(c, None)
                    if b is None:
                        continue

                    b_tp[identity] = self.implementation.get_tie_points(b)
                    break

            self.implementation.set_dependent_tie_points(coord, c_tp, tp_dims)

            if bounds is not None:
                self.implementation.set_dependent_tie_points(
                    bounds, b_tp, tp_dims
                )

        # Set the coordinate constructs on the parent field/domain
        for (
            ncvar,
            (coord, axes, is_dimension_coordinate),
        ) in coordinates.items():
            logger.detail(
                f"        [k] Inserting {coord.__class__.__name__}"
            )  # pragma: no cover
            if is_dimension_coordinate:
                key = self.implementation.set_dimension_coordinate(
                    f, coord, axes=axes, copy=False
                )
            else:
                key = self.implementation.set_auxiliary_coordinate(
                    f, coord, axes=axes, copy=False
                )

            self._reference(ncvar, field_ncvar)
            if self.implementation.has_bounds(coord):
                bounds = self.implementation.get_bounds(coord)
                self._reference(
                    self.implementation.nc_get_variable(bounds), field_ncvar
                )

            ncvar_to_key[ncvar] = key

        # ------------------------------------------------------------
        # Add auxiliary coordinate constructs from geometry node
        # coordinates that are not already bounds of existing
        # auxiliary coordinate constructs (CF>=1.8)
        # ------------------------------------------------------------
        geometry = self._get_geometry(field_ncvar)
        if geometry is not None:
            for node_ncvar in geometry["node_coordinates"]:
                found = any(
                    [
                        self.implementation.get_bounds_ncvar(a) == node_ncvar
                        for a in self.implementation.get_auxiliary_coordinates(
                            f
                        ).values()
                    ]
                )
                # TODO: remove explicit API dependency:
                # f.auxiliary_coordinates.values()
                if found:
                    continue

                #
                if node_ncvar in g["auxiliary_coordinate"]:
                    coord = g["auxiliary_coordinate"][node_ncvar].copy()
                else:
                    coord = self._create_auxiliary_coordinate(
                        parent_ncvar=field_ncvar,
                        ncvar=None,
                        f=f,
                        bounds_ncvar=node_ncvar,
                        geometry_nodes=True,
                    )

                    geometry_type = geometry["geometry_type"]
                    if geometry_type is not None:
                        self.implementation.set_geometry(coord, geometry_type)

                    g["auxiliary_coordinate"][node_ncvar] = coord

                # Insert auxiliary coordinate
                logger.detail(
                    f"        [f] Inserting {coord.__class__.__name__}"
                )  # pragma: no cover

                # TODO check that geometry_dimension is a dimension of
                # the data variable
                geometry_dimension = geometry["geometry_dimension"]
                if geometry_dimension not in g["ncdim_to_axis"]:
                    raise ValueError(
                        f"Geometry dimension {geometry_dimension!r} is not in "
                        f"read_vars['ncdim_to_axis']: {g['ncdim_to_axis']}"
                    )

                aux = self.implementation.set_auxiliary_coordinate(
                    f,
                    coord,
                    axes=(g["ncdim_to_axis"][geometry_dimension],),
                    copy=False,
                )

                self._reference(node_ncvar, field_ncvar)
                ncvar_to_key[node_ncvar] = aux

        # ------------------------------------------------------------
        # Add custom auxiliary coordinate constructs defined by
        # subclasses
        # ------------------------------------------------------------
        extra_aux = self._customise_auxiliary_coordinates(field_ncvar, f)
        if extra_aux:
            ncvar_to_key.update(extra_aux)
            g["auxiliary_coordinate"].update(extra_aux)
            g["coordinates"][field_ncvar].extend(extra_aux)

            # Reference the netCDF variables
            coords = self.implementation.get_auxiliary_coordinates(f)
            for aux_ncvar, key in extra_aux.items():
                self._reference(aux_ncvar, field_ncvar)
                coord = coords[key]
                if self.implementation.has_bounds(coord):
                    bounds = self.implementation.get_bounds(coord)
                    self._reference(
                        self.implementation.nc_get_variable(bounds),
                        field_ncvar,
                    )

        # ------------------------------------------------------------
        # Add a domain topology construct derived from UGRID
        # ------------------------------------------------------------
        if ugrid:
            domain_topology = mesh.domain_topologies.get(location)
            if domain_topology is not None:
                logger.detail(
                    "        [m] Inserting "
                    f"{domain_topology.__class__.__name__} with data shape "
                    f"{self.implementation.get_data_shape(domain_topology)}"
                )  # pragma: no cover

                key = self.implementation.set_domain_topology(
                    f,
                    domain_topology,
                    axes=ugrid_axis,
                    copy=True,
                )
                self._reference(ncvar, field_ncvar)
                ncvar = self.implementation.nc_get_variable(domain_topology)
                ncvar_to_key[ncvar] = key

        # ------------------------------------------------------------
        # Add a cell connectivity construct derived from UGRID
        # ------------------------------------------------------------
        if ugrid:
            for cell_connectivity in mesh.cell_connectivities.get(
                location, ()
            ):
                logger.detail(
                    "        [n] Inserting "
                    f"{cell_connectivity.__class__.__name__} with data shape "
                    f"{self.implementation.get_data_shape(cell_connectivity)}"
                )  # pragma: no cover

                key = self.implementation.set_cell_connectivity(
                    f,
                    cell_connectivity,
                    axes=ugrid_axis,
                    copy=True,
                )
                self._reference(ncvar, field_ncvar)
                ncvar = self.implementation.nc_get_variable(cell_connectivity)
                ncvar_to_key[ncvar] = key

        if ugrid:
            # Set the mesh identifier
            self.implementation.set_mesh_id(f, mesh.mesh_id)

        # ------------------------------------------------------------
        # Add coordinate reference constructs from formula_terms
        # properties
        # ------------------------------------------------------------
        for key, coord in self.implementation.get_coordinates(f).items():
            coord_ncvar = self.implementation.nc_get_variable(coord)

            if coord_ncvar is None:
                # This might be the case if the coordinate construct
                # just contains geometry nodes
                continue

            formula_terms = g["variable_attributes"][coord_ncvar].get(
                "formula_terms"
            )
            if formula_terms is None:
                # This coordinate does not have a formula_terms
                # attribute
                continue

            if coord_ncvar not in g["formula_terms"]:
                self._check_formula_terms(
                    field_ncvar,
                    coord_ncvar,
                    formula_terms,
                    z_ncdim=g["variable_dimensions"][coord_ncvar][0],
                )

            ok = True
            domain_ancillaries = []
            for term, ncvar in g["formula_terms"][coord_ncvar][
                "coord"
            ].items():
                if ncvar is None:
                    continue

                # Set dimensions
                axes = self._get_domain_axes(ncvar)

                if ncvar in g["domain_ancillary"]:
                    domain_anc = self._copy_construct(
                        "domain_ancillary", field_ncvar, ncvar
                    )
                else:
                    bounds = g["formula_terms"][coord_ncvar]["bounds"].get(
                        term
                    )
                    if bounds == ncvar:
                        bounds = None

                    domain_anc = self._create_domain_ancillary(
                        field_ncvar, ncvar, f, bounds_ncvar=bounds
                    )

                if len(axes) == len(self._ncdimensions(ncvar)):
                    domain_ancillaries.append((ncvar, domain_anc, axes))
                else:
                    # The domain ancillary variable spans a dimension
                    # that is not spanned by its parent data variable
                    self._add_message(
                        field_ncvar,
                        ncvar,
                        message=(
                            "Formula terms variable",
                            "spans incorrect dimensions",
                        ),
                        attribute={
                            coord_ncvar + ":formula_terms": formula_terms
                        },
                        dimensions=g["variable_dimensions"][ncvar],
                    )
                    ok = False

            if not ok:
                # Move on to the next coordinate
                continue

            # Still here? Create a formula terms coordinate reference.
            for ncvar, domain_anc, axes in domain_ancillaries:
                logger.detail(
                    f"        [g] Inserting {domain_anc.__class__.__name__}"
                )  # pragma: no cover

                da_key = self.implementation.set_domain_ancillary(
                    f, construct=domain_anc, axes=axes, copy=False
                )

                self._reference(ncvar, field_ncvar)
                if self.implementation.has_bounds(domain_anc):
                    bounds = self.implementation.get_bounds(domain_anc)
                    self._reference(
                        self.implementation.nc_get_variable(bounds),
                        field_ncvar,
                    )

                if ncvar not in ncvar_to_key:
                    ncvar_to_key[ncvar] = da_key

                g["domain_ancillary"][ncvar] = domain_anc
                g["domain_ancillary_key"][ncvar] = da_key

            coordinate_reference = self._create_formula_terms_ref(
                f, key, coord, g["formula_terms"][coord_ncvar]["coord"]
            )

            self.implementation.set_coordinate_reference(
                f, construct=coordinate_reference, copy=False
            )

            logger.detail(
                f"        [l] Inserting {coordinate_reference.__class__.__name__}"
            )  # pragma: no cover

            g["vertical_crs"][key] = coordinate_reference

        # ------------------------------------------------------------
        # Add grid mapping coordinate references (do this after
        # formula terms)
        # ------------------------------------------------------------
        grid_mapping = self.implementation.del_property(
            f, "grid_mapping", None
        )
        if grid_mapping is not None:
            parsed_grid_mapping = self._parse_grid_mapping(
                field_ncvar, grid_mapping
            )

            cf_compliant = self._check_grid_mapping(
                field_ncvar, grid_mapping, parsed_grid_mapping
            )
            if not cf_compliant:
                logger.warning(
                    f"        Bad grid_mapping: {grid_mapping!r}"
                )  # pragma: no cover
            else:
                for x in parsed_grid_mapping:
                    grid_mapping_ncvar, coordinates = list(x.items())[0]

                    parameters = g["variable_attributes"][
                        grid_mapping_ncvar
                    ].copy()

                    # Convert netCDF variable names to internal identifiers
                    coordinates = [
                        ncvar_to_key[ncvar]
                        for ncvar in coordinates
                        if ncvar in ncvar_to_key
                    ]

                    # ------------------------------------------------
                    # Find the datum and coordinate conversion for the
                    # grid mapping
                    # ------------------------------------------------
                    datum_parameters = {}
                    coordinate_conversion_parameters = {}
                    for parameter, value in parameters.items():
                        if parameter in g["datum_parameters"]:
                            datum_parameters[parameter] = value
                        else:
                            coordinate_conversion_parameters[parameter] = value

                    datum = self.implementation.initialise_Datum(
                        parameters=datum_parameters
                    )

                    coordinate_conversion = (
                        self.implementation.initialise_CoordinateConversion(
                            parameters=coordinate_conversion_parameters
                        )
                    )

                    create_new = True

                    if not coordinates:
                        # DCH ALERT
                        # what to do about duplicate standard names? TODO
                        name = parameters.get("grid_mapping_name", None)
                        for (
                            n
                        ) in self.cf_coordinate_reference_coordinates().get(
                            name, ()
                        ):
                            for (
                                key,
                                coord,
                            ) in self.implementation.get_coordinates(
                                f
                            ).items():
                                if n == self.implementation.get_property(
                                    coord, "standard_name", None
                                ):
                                    coordinates.append(key)

                        # Add the datum to already existing vertical
                        # coordinate references
                        for vcr in g["vertical_crs"].values():
                            self.implementation.set_datum(
                                coordinate_reference=vcr, datum=datum
                            )
                    else:
                        for vcoord, vcr in g["vertical_crs"].items():
                            if vcoord in coordinates:
                                # Add the datum to an already existing
                                # vertical coordinate reference
                                logger.detail(
                                    "        [k] Inserting "
                                    f"{datum.__class__.__name__} into "
                                    f"{vcr.__class__.__name__}"
                                )  # pragma: no cover

                                self.implementation.set_datum(
                                    coordinate_reference=vcr, datum=datum
                                )
                                coordinates.remove(vcoord)
                                create_new = bool(coordinates)

                    if create_new:
                        coordref = (
                            self.implementation.initialise_CoordinateReference()
                        )

                        self.implementation.set_datum(
                            coordinate_reference=coordref, datum=datum
                        )

                        self.implementation.set_coordinate_conversion(
                            coordinate_reference=coordref,
                            coordinate_conversion=coordinate_conversion,
                        )

                        self.implementation.set_coordinate_reference_coordinates(
                            coordref, coordinates
                        )

                        self.implementation.nc_set_variable(
                            coordref, grid_mapping_ncvar
                        )

                        key = self.implementation.set_coordinate_reference(
                            f, construct=coordref, copy=False
                        )

                        logger.detail(
                            "        [l] Inserting "
                            f"{coordref.__class__.__name__}"
                        )  # pragma: no cover

                        self._reference(grid_mapping_ncvar, field_ncvar)
                        ncvar_to_key[grid_mapping_ncvar] = key

        # ------------------------------------------------------------
        # Add cell measures to the field/domain
        # ------------------------------------------------------------
        measures = self.implementation.del_property(f, "cell_measures", None)
        if measures is not None:
            parsed_cell_measures = self._parse_x(field_ncvar, measures)

            cf_compliant = self._check_cell_measures(
                field_ncvar, measures, parsed_cell_measures
            )
            if cf_compliant:
                for x in parsed_cell_measures:
                    measure, ncvars = list(x.items())[0]
                    ncvar = ncvars[0]

                    # Set the domain axes for the cell measure
                    axes = self._get_domain_axes(ncvar, allow_external=True)

                    if ncvar in g["cell_measure"]:
                        # Copy the cell measure from one that already
                        # exists
                        cell = g["cell_measure"][ncvar].copy()
                    else:
                        cell = self._create_cell_measure(measure, ncvar)
                        g["cell_measure"][ncvar] = cell

                    logger.detail(
                        f"        [h] Inserting {cell.__class__.__name__}"
                    )  # pragma: no cover

                    key = self.implementation.set_cell_measure(
                        f, construct=cell, axes=axes, copy=False
                    )

                    # Count a reference to the cell measure ...
                    if ncvar != field_ncvar:
                        # ... but only if it is not the same as its
                        # parent data variable (introduced at v1.8.6).
                        self._reference(ncvar, field_ncvar)

                    ncvar_to_key[ncvar] = key

                    if ncvar in g["external_variables"]:
                        g["referenced_external_variables"].add(ncvar)

        # ------------------------------------------------------------
        # Add cell methods to the field
        # ------------------------------------------------------------
        if field and cell_methods_string is not None:
            name_to_axis = ncdim_to_axis.copy()
            name_to_axis.update(ncscalar_to_axis)

            cell_methods = self._parse_cell_methods(
                cell_methods_string, field_ncvar
            )

            for properties in cell_methods:
                axes = properties.pop("axes")

                if g["has_groups"]:
                    # Replace flattened names with absolute names
                    axes = [
                        g["flattener_dimensions"].get(
                            axis, g["flattener_variables"].get(axis, axis)
                        )
                        for axis in axes
                    ]

                # Replace names with domain axis keys
                axes = [name_to_axis.get(axis, axis) for axis in axes]

                method = properties.pop("method", None)

                cell_method = self._create_cell_method(
                    axes, method, properties
                )

                logger.detail(
                    f"        [i] Inserting {method!r} "
                    f"{cell_method.__class__.__name__}"
                )  # pragma: no cover

                self.implementation.set_cell_method(
                    f, construct=cell_method, copy=False
                )

        # ------------------------------------------------------------
        # Add field ancillaries to the field
        # ------------------------------------------------------------
        if field:
            ancillary_variables = self.implementation.del_property(
                f, "ancillary_variables", None
            )
            if ancillary_variables is not None:
                parsed_ancillary_variables = self._split_string_by_white_space(
                    field_ncvar, ancillary_variables, variables=True
                )
                cf_compliant = self._check_ancillary_variables(
                    field_ncvar,
                    ancillary_variables,
                    parsed_ancillary_variables,
                )
                if not cf_compliant:
                    pass
                else:
                    for ncvar in parsed_ancillary_variables:
                        # Set dimensions
                        axes = self._get_domain_axes(ncvar)

                        if ncvar in g["field_ancillary"]:
                            field_anc = g["field_ancillary"][ncvar].copy()
                        else:
                            field_anc = self._create_field_ancillary(ncvar)
                            g["field_ancillary"][ncvar] = field_anc

                        # Insert the field ancillary
                        logger.detail(
                            f"        [j] Inserting {field_anc!r}"
                        )  # pragma: no cover
                        key = self.implementation.set_field_ancillary(
                            f, construct=field_anc, axes=axes, copy=False
                        )
                        self._reference(ncvar, field_ncvar)

                        ncvar_to_key[ncvar] = key

            # --------------------------------------------------------
            # Add extra field ancillary constructs defined by
            # subclasses
            # --------------------------------------------------------
            extra_anc = self._customise_field_ancillaries(field_ncvar, f)
            if extra_anc:
                ncvar_to_key.update(extra_anc)
                g["field_ancillary"].update(extra_anc)

                # Reference the netCDF variables
                for anc_ncvar in extra_anc:
                    self._reference(anc_ncvar, field_ncvar)

        # Add the structural read report to the field/domain
        dataset_compliance = g["dataset_compliance"][field_ncvar]
        components = dataset_compliance["non-compliance"]
        if components:
            dataset_compliance = {field_ncvar: dataset_compliance}
        else:
            dataset_compliance = {}

        self.implementation.set_dataset_compliance(f, dataset_compliance)

        # Return the finished field/domain
        return f

    def _find_coordinate_variable(self, field_ncvar, field_groups, ncdim):
        """Find a coordinate variable for a data-dimension combination.

        Find a Unidata coordinate variable for a particular CF-netCDF
        data variable and netCDF dimension combination.

        .. versionadded:: (cfdm) 1.8.6

        :Parameters:

            field_ncvar: `str`

            field_groups: `tuple`

            ncdim: `str`

        :Returns:

            (`str`, `str`) or (`None`, str`)
                The second item is a message saying how the coordinate
                variable was discovered.

        """
        g = self.read_vars

        ncdim_groups = g["dimension_groups"].get(ncdim, ())
        n_ncdim_groups = len(ncdim_groups)

        if g["variable_dimensions"].get(ncdim) == (ncdim,):
            # There is a Unidata coordinate variable for this
            # dimension, so create a domain axis and dimension
            # coordinate
            return ncdim, ""

        if not g["has_groups"]:
            # This file has no group structure and there is no
            # coordinate variable for this dimension
            return None, ""

        # ------------------------------------------------------------
        # File has groups. Look for a coordinate variable by proximal
        # and lateral search techniques
        # ------------------------------------------------------------
        proximal_candidates = {}
        lateral_candidates = {}

        for ncvar, ncdims in g["variable_dimensions"].items():
            if ncvar == field_ncvar:
                # A data variable can not be its own coordinate
                # variable
                continue

            if ncdims != (ncdim,):
                # This variable does not span the correct dimension
                continue

            if g["variable_basename"][ncvar] != g["dimension_basename"][ncdim]:
                # This variable does not have the same basename as the
                # dimension. E.g. if ncdim is '/forecast/lon' and
                # ncvar is '/forecast/model/lat' then their basenames
                # are 'lon' and 'lat' respectively.
                continue

            ncvar_groups = g["variable_groups"][ncvar]

            if ncvar_groups[:n_ncdim_groups] != ncdim_groups:
                # The variable's group is not the same as, nor a
                # subgroup of, the local apex group.
                continue

            if field_groups[: len(ncvar_groups)] == ncvar_groups:
                # Group is acceptable for proximal search
                proximal_candidates[ncvar] = ncvar_groups
            else:
                # Group is acceptable for lateral search
                lateral_candidates[ncvar] = ncvar_groups

        if proximal_candidates:
            # Choose the coordinate variable closest to the field by
            # proximal search
            ncvars = [
                k
                for k in sorted(
                    proximal_candidates.items(),
                    reverse=True,
                    key=lambda item: len(item[1]),
                )
            ]
            ncvar = ncvars[0][0]
            return ncvar, " (found by proximal search)"

        if lateral_candidates:
            # Choose the coordinate variable that is closest the local
            # apex group by proximal search. If more than one such
            # vaiable exists then lateral search has failed.
            ncvars = [
                k
                for k in sorted(
                    lateral_candidates.items(), key=lambda item: len(item[1])
                )
            ]
            ncvar, group = ncvars[0]

            if len(lateral_candidates) == 1:
                # There is a unique coordinate variable found by
                # lateral search that is closest to the local apex
                # group
                return ncvar, " (found by lateral serach)"
            else:
                group2 = ncvars[1][1]
                if len(group) < len(group2):
                    # There is a unique coordinate variable found by
                    # lateral search that is closest to the local apex
                    # group
                    return ncvar, " (found by lateral serach)"

                # Two coordinate variables found by lateral search are
                # the same distance from the local apex group
                lateral_candidates = []

        if lateral_candidates:
            self._add_message(
                field_ncvar,
                field_ncvar,
                message=(
                    "Multiple coordinate variable candidates",
                    "identified by lateral search",
                ),
                dimensions=g["variable_dimensions"][field_ncvar],
            )

        return None, ""

    def _is_char_or_string(self, ncvar):
        """True if the netCDf variable has string or char datatype.

        .. versionadded:: (cfdm) 1.8.0

        :Parameters:

            ncvar: `str`
                The name of the netCDF variable.

        :Returns:

            `bool`

        **Examples**

            >>> n._is_char_or_string('regions')
            True

        """
        datatype = self.read_vars["variables"][ncvar].dtype
        return datatype == str or datatype.kind in "SU"

    def _is_char(self, ncvar):
        """Return True if the netCDf variable has char datatype.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            ncvar: `str`
                The name of the netCDF variable.

        :Returns:

            `bool`

        **Examples**

            >>> n._is_char('regions')
            True

        """
        datatype = self.read_vars["variables"][ncvar].dtype
        return datatype != str and datatype.kind in "SU"

    def _has_identity(self, construct, identity):
        """TODO.

        .. versionadded:: (cfdm) 1.10.0.0

        """
        if identity == "latitude":
            return self._is_latitude(construct)

        if identity == "longitude":
            return self._is_longitude(construct)

        return False

    def _is_latitude(self, construct):
        """True if and only if the data are (grid) latitudes.

        .. versionadded:: (cfdm) 1.10.0.0

        .. seealso:: `_is_longitude`

        :Parameters:

            construct:

                The construct to test.

        :Returns:

            `bool`

        """
        units = construct.get_property("units", None)
        if not units:
            return False

        if units in (
            "degrees_north",
            "degree_north" "degree_N",
            "degrees_N",
            "degreeN",
            "degreesN",
        ):
            return True

        if units == "degrees":
            return (
                construct.get_property("standard_name", None)
                == "grid_latitude"
            )

        return False

    def _is_longitude(self, construct):
        """True if and only if the data are (grid) longitudes.

        .. versionadded:: (cfdm) 1.10.0.0

        .. seealso:: `_is_longitude`

        :Parameters:

            construct:

                The construct to test.

        :Returns:

            `bool`

        """
        units = construct.get_property("units", None)
        if not units:
            return False

        if units in (
            "degrees_east",
            "degree_east",
            "degree_E",
            "degrees_E",
            "degreeE",
            "degreesE",
        ):
            return True

        if units == "degrees":
            return (
                construct.get_property("standard_name", None)
                == "grid_longitude"
            )

        return False

    def _get_geometry(self, field_ncvar, return_ncvar=False):
        """Return a geometry container for this field construct.

        .. versionadded:: (cfdm) 1.8.0

        :Parameters:

            field_ncvar: `str`
                The netCDF varibale name for the field construct.

            return_ncvar: `bool`
                If True then return the netCDF variable name of the
                geometry instead.

        :Returns:

            `dict` or `str` or None`
                A `dict` containing geometry container information, or the
                netCDF geometry container name. If there is no geometry
                container for this data variable, or if the dataset
                version is CF<=1.7, then `None` is returned.

        """
        g = self.read_vars
        if g["CF>=1.8"]:
            geometry_ncvar = g["variable_geometry"].get(field_ncvar)
            if return_ncvar:
                if geometry_ncvar in g["geometries"]:
                    return geometry_ncvar

                return

            return g["geometries"].get(geometry_ncvar)

    def _add_message(
        self,
        parent_ncvar,
        ncvar,
        message=None,
        attribute=None,
        dimensions=None,
        variable=None,
        conformance=None,
    ):
        """Stores and logs a message about an issue with a field.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            parent_ncvar: `str`
                The netCDF variable name of the parent varable.

                *Parameter example:*
                  ``'tas'``

            ncvar: `str`
                The netCDF variable name of the parent component that
                has the problem.

                *Parameter example:*
                  ``'rotated_latitude_longitude'``

            message: (`str`, `str`), optional

            attribute: `dict`, optional
                The name and value of the netCDF attribute that has a problem.

                *Parameter example:*
                  ``attribute={'tas:cell_measures': 'area: areacella'}``

            dimensions: sequence of `str`, optional
                The netCDF dimensions of the variable that has a problem.

                *Parameter example:*
                  ``dimensions=('lat', 'lon')``

            variable: `str`, optional

        """
        g = self.read_vars

        if message is not None:
            try:
                code = self._code0[message[0]] * 1000 + self._code1[message[1]]
            except KeyError:
                code = None

            message = " ".join(message)
        else:
            code = None

        d = {"code": code, "attribute": attribute, "reason": message}

        if dimensions is not None:
            d["dimensions"] = dimensions

        if variable is None:
            variable = ncvar

        g["dataset_compliance"].setdefault(
            parent_ncvar,
            {
                "CF version": self.implementation.get_cf_version(),
                "non-compliance": {},
            },
        )
        g["dataset_compliance"][parent_ncvar]["non-compliance"].setdefault(
            ncvar, []
        ).append(d)

        e = g["component_report"].setdefault(variable, {})
        e.setdefault(ncvar, []).append(d)

        if dimensions is None:  # pragma: no cover
            dimensions = ""  # pragma: no cover
        else:  # pragma: no cover
            dimensions = "(" + ", ".join(dimensions) + ")"  # pragma: no cover

        logger.info(
            "    Error processing netCDF variable "
            f"{ncvar}{dimensions}: {d['reason']}"
        )  # pragma: no cover

        return d

    def _include_component_report(self, parent_ncvar, ncvar):
        """Include a component in the dataset compliance report.

        .. versionadded:: (cfdm) UGRIDVER

        :Parameters:

            parent_ncvar: `str`
                The netCDF variable name of the parent varable.

                *Parameter example:*
                  ``'tas'``

            ncvar: `str`
                The netCDF variable name of the parent component that
                has the problem.

        :Returns:

            `None`

        """
        g = self.read_vars
        component_report = g["component_report"].get(ncvar)
        if component_report:
            g["dataset_compliance"][parent_ncvar]["non-compliance"].setdefault(
                ncvar, []
            ).extend(component_report)

    def _get_domain_axes(self, ncvar, allow_external=False, parent_ncvar=None):
        """Find a domain axis identifier for the variable's dimensions.

        Return the domain axis identifiers that correspond to a
        netCDF variable's netCDF dimensions.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            ncvar: `str`
                The netCDF variable name.

            allow_external: `bool`
                If True and *ncvar* is an external variable then return an
                empty list.

            parent_ncvar: `str`, optional
                TODO

                .. versionadded:: (cfdm) 1.10.0.0

        :Returns:

            `list`

        **Examples**

        >>> r._get_domain_axes('areacello')
        ['domainaxis0', 'domainaxis1']

        >>> r._get_domain_axes('areacello', allow_external=True)
        []

        """
        g = self.read_vars

        if allow_external and ncvar in g["external_variables"]:
            axes = []
        else:
            ncdim_to_axis = g["ncdim_to_axis"]
            ncdimensions = self._ncdimensions(ncvar, parent_ncvar=parent_ncvar)
            axes = [
                ncdim_to_axis[ncdim]
                for ncdim in ncdimensions
                if ncdim in ncdim_to_axis
            ]

        return axes

    def _ncdim_abspath(self, ncdim):
        """Return the absolute path of the netCDF dimension name.

        If the file has no groups, then the netCDF dimension is returned
        unchanged.

        .. versionadded:: (cfdm) 1.8.6

        :Parameters:

            ncdim: `str` or `None`
                The (falttened) netCDF dimension name.

        :Returns:

            `str` or `None`
                The (absolute path of the) netCDF dimension name.

        """
        g = self.read_vars
        if ncdim is None or not g["has_groups"]:
            return ncdim

        # Replace the netCDF dimension name with its full group
        # path. E.g. if dimension 'time' is in group '/forecast' then
        # it will be renamed '/forecast/time'. (CF>=1.8)
        return g["flattener_dimensions"].get(ncdim, ncdim)

    def _create_auxiliary_coordinate(
        self,
        parent_ncvar,
        ncvar,
        f,
        bounds_ncvar=None,
        geometry_nodes=False,
    ):
        """Create an auxiliary coordinate construct.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            parent_ncvar: `str`
                The netCDF name of the parent variable that contains
                the auxiliary coordinate construct.

            ncvar: `str` or `None`
                The netCDF name of the variable to be converted to an
                auxiliary coordinate construct. See the
                *geometry_nodes* parameter.

            field: `Field` or `Domain`
                The parent construct.

            bounds_ncvar: `str`, optional
                The netCDF variable name of the coordinate bounds.

            geometry_nodes: `bool`
                Set to True only if and only if the coordinate construct
                is to be created with only bounds from a node coordinates
                variable, whose netCDF name is given by *bounds_ncvar*. In
                this case *ncvar* must be `None`.

        :Returns:

            `AuxiliaryCoordinate`

        """
        return self._create_bounded_construct(
            parent_ncvar=parent_ncvar,
            ncvar=ncvar,
            f=f,
            auxiliary=True,
            bounds_ncvar=bounds_ncvar,
            geometry_nodes=geometry_nodes,
        )

    def _create_dimension_coordinate(
        self, parent_ncvar, ncvar, f, bounds_ncvar=None
    ):
        """Create a dimension coordinate construct.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            parent_ncvar: `str`
                The netCDF name of the parent variable that contains
                the dimension coordinate construct.

            ncvar: `str`
                The netCDF name of the variable to be converted to a
                dimension coordinate construct.

            field: `Field` or `Domain`
                The parent construct.

            bounds_ncvar: `str`, optional
                The netCDF variable name of the coordinate bounds.

        :Returns:

            `DimensionCoordinate`

        """
        return self._create_bounded_construct(
            parent_ncvar=parent_ncvar,
            ncvar=ncvar,
            f=f,
            dimension=True,
            bounds_ncvar=bounds_ncvar,
        )

    def _create_domain_ancillary(
        self, parent_ncvar, ncvar, f, bounds_ncvar=None
    ):
        """Create a domain ancillary construct object.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            parent_ncvar: `str`
                The netCDF name of the parent variable that contains
                the domain ancillary construct.

            ncvar: `str` or `None`
                The netCDF name of the variable to be converted to a
                domain ancillary construct.

            field: `Field` or `Domain`
                The parent construct.

            bounds_ncvar: `str`, optional
                The netCDF variable name of the coordinate bounds.

        :Returns:

            `DomainAncillary`

        """
        return self._create_bounded_construct(
            parent_ncvar=parent_ncvar,
            ncvar=ncvar,
            f=f,
            domain_ancillary=True,
            bounds_ncvar=bounds_ncvar,
        )

    def _create_bounded_construct(
        self,
        parent_ncvar,
        ncvar,
        f,
        dimension=False,
        auxiliary=False,
        domain_ancillary=False,
        bounds_ncvar=None,
        has_coordinates=True,
        geometry_nodes=False,
    ):
        """Create a variable which might have bounds.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            parent_ncvar: `str`
                The netCDF name of the parent variable that contains
                the bounded construct.

            ncvar: `str` or `None`
                The netCDF name of the variable. See the
                *geometry_nodes* parameter.

            f: `Field` or `Domain`
                The parent construct.

            dimension: `bool`, optional
                If True then a dimension coordinate construct is created.

            auxiliary: `bool`, optional
                If True then an auxiliary coordinate consrtruct is created.

            domain_ancillary: `bool`, optional
                If True then a domain ancillary construct is created.

            geometry_nodes: `bool`
                Set to True only if and only if the coordinate
                construct is to be created with only bounds from a
                geometry node coordinates variable, whose netCDF name
                is given by *bounds_ncvar*. In this case *ncvar* must
                be `None`.

        :Returns:

            `DimensionCoordinate` or `AuxiliaryCoordinate` or `DomainAncillary`
                The new construct.

        """
        g = self.read_vars
        nc = g["nc"]

        g["bounds"][parent_ncvar] = {}
        g["coordinates"][parent_ncvar] = []

        if ncvar is not None:
            properties = g["variable_attributes"][ncvar].copy()
            properties.pop("formula_terms", None)
        else:
            properties = {}

        # Check for tie points
        tie_points = ncvar in g["tie_point_ncvar"].get(parent_ncvar, ())

        # Look for a geometry container
        geometry = self._get_geometry(parent_ncvar)

        attribute = "bounds"  # TODO Bad default? consider if bounds != None

        # If there are bounds then find the name of the attribute that
        # names them, and the netCDF variable name of the bounds.
        if bounds_ncvar is None:
            bounds_ncvar = properties.pop("bounds", None)
            if bounds_ncvar is None:
                bounds_ncvar = properties.pop("climatology", None)
                if bounds_ncvar is not None:
                    attribute = "climatology"
                elif geometry:
                    bounds_ncvar = properties.pop("nodes", None)
                    if bounds_ncvar is not None:
                        attribute = "nodes"
                elif tie_points:
                    # This construct is derived from a tie point
                    # coordinates variable (CF>=1.9)
                    bounds_ncvar = properties.pop("bounds_tie_points", None)
                    if bounds_ncvar is not None:
                        attribute = "bounds_tie_points"
        elif geometry_nodes:
            attribute = "nodes"

        # Make sure that the bounds attribute is removed
        properties.pop(attribute, None)

        if dimension:
            properties.pop("compress", None)
            c = self.implementation.initialise_DimensionCoordinate()
        elif auxiliary:
            c = self.implementation.initialise_AuxiliaryCoordinate()
        elif domain_ancillary:
            c = self.implementation.initialise_DomainAncillary()
        else:
            raise ValueError(
                "Must set exactly one of the dimension, auxiliary or "
                "domain_ancillary parameters to True"
            )

        self.implementation.set_properties(c, properties)

        if not g["mask"]:
            self._set_default_FillValue(c, ncvar)

        data = None
        if has_coordinates and ncvar is not None:
            data = self._create_data(ncvar, c, parent_ncvar=parent_ncvar)
            self.implementation.set_data(c, data, copy=False)

        # Store the original file names
        self.implementation.set_original_filenames(
            c, g["variable_filename"].get(ncvar, g["filename"])
        )

        # ------------------------------------------------------------
        # Add any bounds
        # ------------------------------------------------------------
        if bounds_ncvar:
            if g["has_groups"]:
                # Replace a flattened name with an absolute name
                # (CF>=1.8)
                bounds_ncvar = g["flattener_variables"].get(
                    bounds_ncvar, bounds_ncvar
                )

            if attribute == "nodes":
                # Check geometry node coordinate boounds (CF>=1.8)
                cf_compliant = self._check_geometry_node_coordinates(
                    parent_ncvar, bounds_ncvar, geometry
                )
            else:
                # Check other type of bounds
                cf_compliant = self._check_bounds(
                    parent_ncvar, ncvar, attribute, bounds_ncvar
                )

            if not cf_compliant:
                bounds_ncvar = None

        if bounds_ncvar:
            bounds = self.implementation.initialise_Bounds()

            bounds_properties = g["variable_attributes"][bounds_ncvar].copy()
            bounds_properties.pop("formula_terms", None)
            self.implementation.set_properties(bounds, bounds_properties)

            if not g["mask"]:
                self._set_default_FillValue(bounds, bounds_ncvar)

            bounds_data = self._create_data(
                bounds_ncvar,
                bounds,
                parent_ncvar=parent_ncvar,
                coord_ncvar=ncvar,
            )

            self.implementation.set_data(bounds, bounds_data, copy=False)

            # Store the original file names
            self.implementation.set_original_filenames(
                bounds, g["variable_filename"][bounds_ncvar]
            )
            # Store the netCDF variable name
            self.implementation.nc_set_variable(bounds, bounds_ncvar)

            # Store the netCDF bounds dimension name
            bounds_ncdim = self._ncdim_abspath(
                g["variable_dimensions"][bounds_ncvar][-1]
            )

            # Set the netCDF trailing bounds dimension name. (But not
            # if it is a dimension of its parent coordinate
            # variable. This can sometimes happen if the bounds are
            # node coordinates.)
            if bounds_ncdim not in g["variable_dimensions"].get(ncvar, ()):
                self.implementation.nc_set_dimension(bounds, bounds_ncdim)

            # Set the bounds on the parent construct
            error = self.implementation.set_bounds(c, bounds, copy=False)
            if error:
                logger.warning(f"WARNING: {error}")

            if not domain_ancillary:
                g["bounds"][parent_ncvar][ncvar] = bounds_ncvar

            if attribute == "climatology":
                try:
                    self.implementation.set_climatology(c)
                except ValueError as error:
                    # Warn about non-CF-compliant file
                    logger.warning(f"WARNING: {error} in file {g['filename']}")

            # --------------------------------------------------------
            # Geometries
            # --------------------------------------------------------
            if (
                geometry is not None
                and bounds_ncvar in geometry["node_coordinates"]
            ):
                # Record the netCDF node dimension name
                count = self.implementation.get_count(bounds)
                node_ncdim = self.implementation.nc_get_sample_dimension(count)

                self.implementation.nc_set_dimension(
                    bounds, self._ncdim_abspath(node_ncdim)
                )

                geometry_type = geometry["geometry_type"]
                if geometry_type is not None:
                    self.implementation.set_geometry(c, geometry_type)

                g["node_coordinates_as_bounds"].add(bounds_ncvar)

                if self.implementation.get_data_ndim(bounds) == 2:
                    # Insert a size 1 part dimension
                    bounds = self.implementation.bounds_insert_dimension(
                        bounds=bounds, position=1
                    )
                    self.implementation.set_bounds(c, bounds, copy=False)

                # Add a node count properties variable
                nc = geometry.get("node_count")
                if nc is not None:
                    self.implementation.set_node_count_properties(
                        parent=c, node_count=nc
                    )

                # Add a part node count properties variable
                pnc = geometry.get("part_node_count")
                if pnc is not None:
                    self.implementation.set_part_node_count_properties(
                        parent=c, part_node_count=pnc
                    )

                # Add an interior ring variable
                interior_ring = geometry.get("interior_ring")
                if interior_ring is not None:
                    self.implementation.set_interior_ring(
                        parent=c, interior_ring=interior_ring
                    )

        if tie_points:
            # Add interpolation variable properties (CF>=1.9)
            pass
        #            nc = geometry.get("node_count")
        #            if nc is not None:
        #               self.implementation.set_interpolation_properties(
        #                   parent=c, interpolation=i
        #               )

        # Store the netCDF variable name
        self.implementation.nc_set_variable(c, ncvar)

        if not domain_ancillary:
            g["coordinates"][parent_ncvar].append(ncvar)

        # ---------------------------------------------------------
        # Return the bounded variable
        # ---------------------------------------------------------
        return c

    def _create_cell_measure(self, measure, ncvar):
        """Create a cell measure object.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            measure: `str`
                The cell measure.

                *Parameter example:*
                   ``measure='area'``

            ncvar: `str`
                The netCDF name of the cell measure variable.

                *Parameter example:*
                   ``ncvar='areacello'``

        :Returns:

            `CellMeasure`
                The new item.

        """
        g = self.read_vars

        # Initialise the cell measure construct
        cell_measure = self.implementation.initialise_CellMeasure(
            measure=measure
        )

        # Store the netCDF variable name
        self.implementation.nc_set_variable(cell_measure, ncvar)
        if ncvar in g["external_variables"]:
            # The cell measure variable is in an unknown external file
            self.implementation.nc_set_external(construct=cell_measure)
        else:
            # The cell measure variable is in this file or in a known
            # external file
            self.implementation.set_properties(
                cell_measure, g["variable_attributes"][ncvar]
            )

            if not g["mask"]:
                self._set_default_FillValue(cell_measure, ncvar)

            data = self._create_data(ncvar, cell_measure)
            self.implementation.set_data(cell_measure, data, copy=False)

        # Store the original file names
        self.implementation.set_original_filenames(
            cell_measure, g["variable_filename"].get(ncvar)
        )

        return cell_measure

    def _create_interpolation_parameter(self, term, ncvar):
        """Create an interpolation parameter variable.

        .. versionadded:: (cfdm) 1.10.0.0

        :Parameters:

            term: `str`
                The interpolation parameter term name.

                *Parameter example:*
                  ``'ce'``

            ncvar: `str`
                The netCDF name of the interpolation parameter
                variable.

                *Parameter example:*
                  ``'ce'``

        :Returns:

            `InterpolationParameter`
                The new  interpolation parameter variable.

        """
        g = self.read_vars

        if ncvar not in g["variable_attributes"]:
            raise ValueError(
                "Can't initialise a subsampled coordinate with specified "
                f"interpolation parameter ({term}: {ncvar}) that is missing "
                "from the dataset"
            )

        # Initialise the interpolation parameter variable
        param = self.implementation.initialise_InterpolationParameter()

        # Store the netCDF variable name
        self.implementation.nc_set_variable(param, ncvar)

        self.implementation.set_properties(
            param, g["variable_attributes"][ncvar]
        )

        if not g["mask"]:
            self._set_default_FillValue(param, ncvar)

        data = self._create_data(ncvar, uncompress_override=True)
        self.implementation.set_data(param, data, copy=False)

        # Store the original file names
        self.implementation.set_original_filenames(
            param, g["variable_filename"][ncvar]
        )

        return param

    def _create_tie_point_index(self, ncvar, ncdim, subarea_ncdim=None):
        """Create a tie point index variable.

        .. versionadded:: (cfdm) 1.10.0.0

        :Parameters:

            ncvar: `str`
                The netCDF name of the tie point index variable.

                *Parameter example:*
                  ``ncvar='x_indices'``

            ncdim: `str`
                The netCDF name of the tie point index variable's
                subsampled dimension.

                *Parameter example:*
                  ``ncdim='tp_xc'``

            subarea_ncdim: `str`
                The netCDF name of the interpolation subarea dimension
                associated with the subsampled dimension.

                *Parameter example:*
                  ``subarea_ncdim='i_sub'``

        :Returns:

             `TiePointIndex`

        """
        g = self.read_vars

        # Initialise the tie point index variable
        variable = self.implementation.initialise_TiePointIndex()

        # Set the CF properties
        self.implementation.set_properties(
            variable, g["variable_attributes"][ncvar]
        )

        if not g["mask"]:
            self._set_default_FillValue(variable, ncvar)

        # Set the netCDF tie point index variable name
        self.implementation.nc_set_variable(variable, ncvar)

        # Set the name of netCDF subsampled dimension that is spanned
        # by the tie point index variable
        self.implementation.nc_set_subsampled_dimension(
            variable, self._ncdim_abspath(ncdim)
        )

        # Set the name of the netCDF interpolation subarea dimension
        # associated with the the subsampled dimension.
        if subarea_ncdim is not None:
            self.implementation.nc_set_interpolation_subarea_dimension(
                variable, self._ncdim_abspath(subarea_ncdim)
            )

        data = self._create_data(
            ncvar, uncompress_override=True, compression_index=True
        )

        self.implementation.set_data(variable, data, copy=False)

        # Store the original file names
        self.implementation.set_original_filenames(
            variable, g["variable_filename"][ncvar]
        )

        return variable

    def _create_Count(self, ncvar, ncdim):
        """Create a count variable.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            ncvar: `str`
                The name of the netCDF count variable.

                *Parameter example:*
                   ``ncvar='row_size'``

            ncdim: `str`
                The name of the count variable's netCDF dimension.

                *Parameter example:*
                   ``ncdim='profile'``

        :Returns:

                 Count variable instance

        """
        g = self.read_vars

        # Initialise the count variable
        variable = self.implementation.initialise_Count()

        # Set the CF properties
        properties = g["variable_attributes"][ncvar]
        sample_ncdim = properties.pop("sample_dimension", None)
        self.implementation.set_properties(variable, properties)

        if not g["mask"]:
            self._set_default_FillValue(variable, ncvar)

        # Set the netCDF variable name
        self.implementation.nc_set_variable(variable, ncvar)

        # Set the netCDF sample dimension name
        if sample_ncdim is not None:
            self.implementation.nc_set_sample_dimension(
                variable, self._ncdim_abspath(sample_ncdim)
            )

        # Set the name of the netCDF dimension spaned by the variable
        # (which, for indexed contiguous ragged arrays, will not be the
        # same as the netCDF instance dimension)
        self.implementation.nc_set_dimension(
            variable, self._ncdim_abspath(ncdim)
        )

        data = self._create_data(
            ncvar, variable, uncompress_override=True, compression_index=True
        )

        self.implementation.set_data(variable, data, copy=False)

        # Store the original file names
        self.implementation.set_original_filenames(
            variable, g["variable_filename"][ncvar]
        )

        return variable

    def _create_Index(self, ncvar, ncdim):
        """Create an index variable.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            ncvar: `str`
                The name of the netCDF index variable.

                *Parameter example:*
                  ``ncvar='landpoints'``

            ncdim: `str`
                The name of the index variable's netCDF dimension.

                *Parameter example:*
                  ``ncdim='profile'``

        :Returns:

            `Index`
                Index variable instance.

        """
        g = self.read_vars

        # Initialise the index variable
        variable = self.implementation.initialise_Index()

        # Set the CF properties
        properties = g["variable_attributes"][ncvar]
        properties.pop("instance_dimension", None)

        self.implementation.set_properties(variable, properties)

        if not g["mask"]:
            self._set_default_FillValue(variable, ncvar)

        # Set the netCDF variable name
        self.implementation.nc_set_variable(variable, ncvar)

        # Set the netCDF sample dimension name
        sample_ncdim = ncdim
        self.implementation.nc_set_sample_dimension(
            variable, self._ncdim_abspath(sample_ncdim)
        )

        # Set the name of the netCDF dimension spaned by the variable
        # (which, for indexed contiguous ragged arrays, will not be
        # the same as the netCDF sample dimension)
        self.implementation.nc_set_dimension(
            variable, self._ncdim_abspath(ncdim)
        )

        # Set the data
        data = self._create_data(
            ncvar, variable, uncompress_override=True, compression_index=True
        )
        self.implementation.set_data(variable, data, copy=False)

        # Store the original file names
        self.implementation.set_original_filenames(
            variable, g["variable_filename"][ncvar]
        )

        return variable

    def _create_InteriorRing(self, ncvar, ncdim):
        """Create an interior ring variable.

        .. versionadded:: (cfdm) 1.8.0

        :Parameters:

            ncvar: `str`
                The name of the netCDF interior ring variable.

                *Parameter example:*
                  ``ncvar='interior_ring'``

            ncdim: `str`
                The name of the part dimension.

                *Parameter example:*
                  ``ncdim='part'``

        :Returns:

                Interior ring variable instance

        """
        g = self.read_vars

        # Initialise the interior ring variable
        variable = self.implementation.initialise_InteriorRing()

        # Store the netCDF variable name
        self.implementation.nc_set_variable(variable, ncvar)
        self.implementation.nc_set_dimension(
            variable, self._ncdim_abspath(ncdim)
        )

        properties = g["variable_attributes"][ncvar]
        self.implementation.set_properties(variable, properties)

        if not g["mask"]:
            self._set_default_FillValue(variable, ncvar)

        data = self._create_data(ncvar, variable)
        self.implementation.set_data(variable, data, copy=False)

        # Store the original file names
        self.implementation.set_original_filenames(
            variable, g["variable_filename"][ncvar]
        )

        return variable

    def _create_List(self, ncvar):
        """Create a netCDF list variable (List).

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            ncvar: `str`
                The name of the netCDF list variable.

                *Parameter example:*
                   ``ncvar='landpoints'``

        :Returns:

            `List`

        """
        g = self.read_vars

        # Initialise the list variable
        variable = self.implementation.initialise_List()

        # Store the netCDF variable name
        self.implementation.nc_set_variable(variable, ncvar)

        properties = self.read_vars["variable_attributes"][ncvar]
        properties.pop("compress", None)
        self.implementation.set_properties(variable, properties)

        if not g["mask"]:
            self._set_default_FillValue(variable, ncvar)

        data = self._create_data(
            ncvar, variable, uncompress_override=True, compression_index=True
        )
        self.implementation.set_data(variable, data, copy=False)

        # Store the original file names
        self.implementation.set_original_filenames(
            variable, g["variable_filename"][ncvar]
        )

        return variable

    def _create_NodeCountProperties(self, ncvar):
        """Create a node count properties variable.

        .. versionadded:: (cfdm) 1.8.0

        :Parameters:

            ncvar: `str`
                The netCDF node count variable name.

                *Parameter example:*
                  ``ncvar='node_count'``

        :Returns:

                Node count variable instance

        """
        g = self.read_vars

        # Initialise the node count properites variable
        variable = self.implementation.initialise_NodeCountProperties()

        # Store the netCDF variable name
        self.implementation.nc_set_variable(variable, ncvar)

        properties = g["variable_attributes"][ncvar]
        self.implementation.set_properties(variable, properties)

        if not g["mask"]:
            self._set_default_FillValue(variable, ncvar)

        # Store the original file names
        self.implementation.set_original_filenames(
            variable, g["variable_filename"][ncvar]
        )

        return variable

    def _create_PartNodeCount(self, ncvar, ncdim):
        """Create a part node count variable.

        .. versionadded:: (cfdm) 1.8.0

        :Parameters:

            ncvar: `str`
                The name of the netCDF part node count variable.

                *Parameter example:*
                  ``ncvar='part_node_count'``

            ncdim: `str`
                The name of the part dimension.

                *Parameter example:*
                  ``ncdim='part'``

        :Returns:

                Part node count variable instance

        """
        g = self.read_vars

        # Initialise the part node count properties variable
        variable = self.implementation.initialise_PartNodeCount()

        # Store the netCDF variable name
        self.implementation.nc_set_variable(variable, ncvar)
        self.implementation.nc_set_dimension(
            variable, self._ncdim_abspath(ncdim)
        )

        properties = g["variable_attributes"][ncvar]
        self.implementation.set_properties(variable, properties)

        if not g["mask"]:
            self._set_default_FillValue(variable, ncvar)

        # Store the original file names
        self.implementation.set_original_filenames(
            variable, g["variable_filename"][ncvar]
        )

        return variable

    def _create_cell_method(self, axes, method, qualifiers):
        """Create a cell method object.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            axes: `tuple`

            method: 'str`

            properties: `dict`

        :Returns:

            `CellMethod`

        """
        return self.implementation.initialise_CellMethod(
            axes=axes, method=method, qualifiers=qualifiers
        )

    def _create_netcdfarray(
        self,
        ncvar,
        unpacked_dtype=False,
        coord_ncvar=None,
        return_kwargs_only=False,
    ):
        """Set the Data attribute of a variable.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            ncvar: `str`

            unpacked_dtype: `False` or `numpy.dtype`, optional

            coord_ncvar: `str`, optional

                .. versionadded:: (cfdm) 1.10.0.1

            return_kwargs_only: `bool`, optional
                Only return the kwargs dictionary, without
                instantiating a new `NetCDFArray`.

                .. versionadded:: (cfdm) 1.10.0.1

        :Returns:

            (`NetCDFArray`, `dict`) or (`None`, `dict`) or `dict`
                The new `NetCDFArray` instance and a dictionary of the
                kwargs used to create it. If the array could not be
                created then `None` is returned in its place. If
                *return_kwargs_only* then only the dictionary is
                returned.

        """
        g = self.read_vars

        if g["has_groups"]:
            # Get the variable from the original grouped file. This is
            # primarily so that unlimited dimensions don't come out
            # with size 0 (v1.8.8.1)
            group, name = self._netCDF4_group(
                g["variable_grouped_dataset"][ncvar], ncvar
            )
            variable = group.variables.get(name)
        else:
            variable = g["variables"].get(ncvar)

        if variable is None:
            return None

        dtype = variable.dtype
        if dtype is str:
            # netCDF string types have a dtype of `str`, which needs
            # to be reset as a numpy.dtype, but we don't know what
            # without reading the data, so set it to None for now.
            dtype = None

        if dtype is not None and unpacked_dtype is not False:
            dtype = np.result_type(dtype, unpacked_dtype)

        ndim = variable.ndim
        shape = variable.shape
        size = variable.size

        if size < 2:
            size = int(size)

        if self._is_char(ncvar) and ndim >= 1:
            # Has a trailing string-length dimension
            strlen = shape[-1]
            shape = shape[:-1]
            size /= strlen
            ndim -= 1
            dtype = np.dtype(f"U{strlen}")

        filename = g["variable_filename"][ncvar]

        # Get the units and calendar (before we overwrite ncvar)
        units = g["variable_attributes"][ncvar].get("units")
        calendar = g["variable_attributes"][ncvar].get("calendar")

        if coord_ncvar is not None:
            # Get the Units from the parent coordinate variable, if
            # they've not already been set.
            if units is None:
                units = g["variable_attributes"][coord_ncvar].get("units")

            if calendar is None:
                calendar = g["variable_attributes"][coord_ncvar].get(
                    "calendar"
                )

        # Store the missing value indicators
        missing_values = {}
        for attr in (
            "missing_value",
            "_FillValue",
            "valid_min",
            "valid_max",
            "valid_range",
        ):
            value = getattr(variable, attr, None)
            if value is not None:
                missing_values[attr] = value

        valid_range = missing_values.get("valid_range")
        if valid_range is not None:
            try:
                missing_values["valid_range"] = tuple(valid_range)
            except TypeError:
                pass

        kwargs = {
            "filename": filename,
            "address": ncvar,
            "shape": shape,
            "dtype": dtype,
            "mask": g["mask"],
            "units": units,
            "calendar": calendar,
            "missing_values": missing_values,
        }

        if return_kwargs_only:
            return kwargs

        array = self.implementation.initialise_NetCDFArray(**kwargs)

        return array, kwargs

    def _create_data(
        self,
        ncvar,
        construct=None,
        unpacked_dtype=False,
        uncompress_override=None,
        parent_ncvar=None,
        coord_ncvar=None,
        compression_index=False,
    ):
        """Create a data object (Data).

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            ncvar: `str`
                The name of the netCDF variable that contains the data.

            construct: optional

            unpacked_dtype: `False` or `numpy.dtype`, optional

            uncompress_override: `bool`, optional

            parent_ncvar: `str`, optional

            coord_ncvar: `str`, optional

                .. versionadded:: (cfdm) 1.10.0.0

           compression_index: `str`, optional
                True if the data being created are compression
                indices.

                .. versionadded:: (cfdm) 1.10.1.1

        :Returns:

            `Data`

        """
        g = self.read_vars

        array, kwargs = self._create_netcdfarray(
            ncvar, unpacked_dtype=unpacked_dtype, coord_ncvar=coord_ncvar
        )
        if array is None:
            return None

        filename = kwargs["filename"]
        units = kwargs["units"]
        calendar = kwargs["calendar"]

        compression = g["compression"]

        dimensions = g["variable_dimensions"][ncvar]

        if (
            (uncompress_override is not None and uncompress_override)
            or not compression
            or not set(compression).intersection(dimensions)
        ):
            # The array is not compressed (or is not to be
            # uncompressed)
            pass

        else:
            # The array might be compressed

            # Get the shape and ndim of the uncompressed data
            uncompressed_shape = tuple(
                self._dimension_sizes(ncvar, parent_ncvar=parent_ncvar)
            )

            ndim = array.ndim

            # Initialisations needed for subsampled coordinates
            subsampled = False
            tie_point_indices = {}
            interpolation_parameters = {}
            parameter_dimensions = {}

            # Loop round the dimensions of variable in the order
            # that they appear in the netCDF file
            for i, ncdim in enumerate(dimensions):
                if ncdim not in compression:
                    continue

                # This dimension represents two or more compressed
                # dimensions
                c = compression[ncdim]
                if ncvar not in c.get("netCDF_variables", (ncvar,)):
                    # This variable is not compressed, even though
                    # it spans a dimension that is compressed for
                    # some other variables For example, this sort
                    # of situation may arise with simple
                    # geometries.
                    continue

                if "gathered" in c:
                    # ------------------------------------------------
                    # Compression by gathering
                    # ------------------------------------------------
                    c = c["gathered"]

                    uncompressed_ndim = len(uncompressed_shape)
                    ndim = array.ndim

                    d = dimensions.index(ncdim)
                    compressed_dimensions = {
                        d: tuple(range(d, uncompressed_ndim - (ndim - d - 1)))
                    }

                    array = self._create_gathered_array(
                        gathered_array=self._create_Data(array, ncvar=ncvar),
                        uncompressed_shape=uncompressed_shape,
                        compressed_dimensions=compressed_dimensions,
                        list_variable=c["list_variable"],
                    )
                elif "ragged_indexed_contiguous" in c:
                    # ------------------------------------------------
                    # Contiguous indexed ragged array
                    # ------------------------------------------------
                    # Check this before ragged_indexed and
                    # ragged_contiguous because both of these will
                    # exist for an indexed and contiguous array.
                    c = c["ragged_indexed_contiguous"]

                    # i = dimensions.index(ncdim)
                    if dimensions.index(ncdim) != 0:
                        raise ValueError(
                            "Data can only be created when the netCDF "
                            "dimension spanned by the data variable is the "
                            "left-most dimension in the ragged array."
                        )

                    array = self._create_ragged_indexed_contiguous_array(
                        ragged_indexed_contiguous_array=self._create_Data(
                            array, ncvar=ncvar
                        ),
                        uncompressed_shape=uncompressed_shape,
                        count_variable=c["count_variable"],
                        index_variable=c["index_variable"],
                    )

                elif "ragged_contiguous" in c:
                    # ------------------------------------------------
                    # Contiguous ragged array
                    # ------------------------------------------------
                    c = c["ragged_contiguous"]

                    # i = dimensions.index(ncdim)
                    if dimensions.index(ncdim) != 0:
                        raise ValueError(
                            "Data can only be created when the netCDF "
                            "dimension spanned by the data variable is "
                            "the left-most dimension in the ragged array."
                        )

                    array = self._create_ragged_contiguous_array(
                        ragged_contiguous_array=self._create_Data(
                            array, ncvar=ncvar
                        ),
                        uncompressed_shape=uncompressed_shape,
                        count_variable=c["count_variable"],
                    )

                elif "ragged_indexed" in c:
                    # ------------------------------------------------
                    # Indexed ragged array
                    # ------------------------------------------------
                    c = c["ragged_indexed"]

                    # i = dimensions.index(ncdim)
                    if dimensions.index(ncdim) != 0:
                        raise ValueError(
                            "Data can only be created when the netCDF "
                            "dimension spanned by the data variable is "
                            "the left-most dimension in the ragged array."
                        )

                    array = self._create_ragged_indexed_array(
                        ragged_indexed_array=self._create_Data(
                            array, ncvar=ncvar
                        ),
                        uncompressed_shape=uncompressed_shape,
                        index_variable=c["index_variable"],
                    )

                elif (
                    parent_ncvar is not None
                    and f"subsampled {parent_ncvar} {ncvar}" in c
                ):
                    # ------------------------------------------------
                    # Subsampled array
                    # ------------------------------------------------
                    subsampled = True
                    c = c[f"subsampled {parent_ncvar} {ncvar}"]

                    rec = g["interpolation"][c["interpolation_ncvar"]]

                    tie_point_index_ncvar = rec["subsampled_ncdim"][ncdim][
                        "tie_point_index_ncvar"
                    ]
                    tie_point_indices[i] = self._copy_construct(
                        "tie_point_index", parent_ncvar, tie_point_index_ncvar
                    )

                    # Sort out interpolation parameters for all
                    # dimensions
                    if not interpolation_parameters:
                        for term, param_ncvar in rec[
                            "interpolation_parameters"
                        ].items():
                            interpolation_parameters[
                                term
                            ] = self._copy_construct(
                                "interpolation_parameter",
                                parent_ncvar,
                                param_ncvar,
                            )

                            # For each intepolation parameter, record
                            # the positions of its dimension positions
                            # relative to the order of the tie point
                            # dimensions.
                            positions = []
                            for dim in g["variable_dimensions"][param_ncvar]:
                                if dim in dimensions:
                                    # This interpolation parameter
                                    # dimension is either an
                                    # interpolated dimension or a
                                    # subsampled dimension
                                    positions.append(dimensions.index(dim))
                                else:
                                    # This interpolation parameter
                                    # dimension is an interpolation
                                    # subarea dimension
                                    for d, v in rec[
                                        "subsampled_ncdim"
                                    ].items():
                                        if dim != v["subarea_ncdim"]:
                                            continue

                                        positions.append(dimensions.index(d))
                                        break

                            parameter_dimensions[term] = tuple(positions)
                else:
                    # This compression type was no recognised, which
                    # could be a result of a non-compressed data
                    # variable spanning compressed dimensions.
                    break

            if subsampled:
                array = self._create_subsampled_array(
                    subsampled_array=self._create_Data(array, ncvar=ncvar),
                    uncompressed_shape=tuple(uncompressed_shape),
                    tie_point_indices=tie_point_indices,
                    parameters=interpolation_parameters.copy(),
                    parameter_dimensions=parameter_dimensions,
                    interpolation_name=rec["interpolation_name"],
                    interpolation_description=rec["interpolation_description"],
                    computational_precision=rec["computational_precision"],
                )

        data = self._create_Data(
            array,
            units=units,
            calendar=calendar,
            ncvar=ncvar,
        )
        data._original_filenames(define=filename)

        return data

    def _create_domain_axis(self, size, ncdim=None):
        """Create a domain axis construct.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            size: `int`

            ncdim: `str, optional

        :Returns:

            Domain axis construct

        """
        domain_axis = self.implementation.initialise_DomainAxis(size=size)
        self.implementation.nc_set_dimension(
            domain_axis, self._ncdim_abspath(ncdim)
        )

        return domain_axis

    def _create_field_ancillary(self, ncvar):
        """Create a field ancillary construct.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            ncvar: `str`
                The netCDF name of the field ancillary variable.

        :Returns:

            Field ancillary construct

        """
        g = self.read_vars

        # Create a field ancillary object
        field_ancillary = self.implementation.initialise_FieldAncillary()

        # Insert properties
        self.implementation.set_properties(
            field_ancillary,
            g["variable_attributes"][ncvar],
            copy=True,
        )

        if not self.read_vars["mask"]:
            self._set_default_FillValue(field_ancillary, ncvar)

        # Insert data
        data = self._create_data(ncvar, field_ancillary)
        self.implementation.set_data(field_ancillary, data, copy=False)

        # Store the netCDF variable name
        self.implementation.nc_set_variable(field_ancillary, ncvar)

        # Store the original file names
        self.implementation.set_original_filenames(
            field_ancillary, g["variable_filename"][ncvar]
        )

        return field_ancillary

    def _parse_cell_methods(self, cell_methods_string, field_ncvar=None):
        """Parse a CF cell_methods string.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            cell_methods_string: `str`
                A CF cell methods string.

            field_ncvar: `str`, optional
                The netCDF name of the data variable that contains the
                cell methods.

        :Returns:

            `list` of `dict`

        **Examples**

        >>> c = parse_cell_methods('t: minimum within years '
        ...                        't: mean over ENSO years)')

        """
        if field_ncvar:
            attribute = {field_ncvar + ":cell_methods": cell_methods_string}

        incorrect_interval = (
            "Cell method interval",
            "is incorrectly formatted",
        )

        out = []

        if not cell_methods_string:
            return out

        # ------------------------------------------------------------
        # Split the cell_methods string into a list of strings ready
        # for parsing. For example:
        #
        #   'lat: mean (interval: 1 hour)'
        #
        # would be split up into:
        #
        #   ['lat:', 'mean', '(', 'interval:', '1', 'hour', ')']
        # ------------------------------------------------------------
        cell_methods = re.sub(r"\((?=[^\s])", "( ", cell_methods_string)
        cell_methods = re.sub(r"(?<=[^\s])\)", " )", cell_methods).split()

        while cell_methods:
            cm = {}

            axes = []
            while cell_methods:
                if not cell_methods[0].endswith(":"):
                    break

                # TODO Check that "name" ends with colon? How? ('lat: mean
                #      (area-weighted) or lat: mean (interval: 1 degree_north comment:
                #      area-weighted)')

                axis = cell_methods.pop(0)[:-1]

                axes.append(axis)

            cm["axes"] = axes

            if not cell_methods:
                out.append(cm)
                break

            # Method
            cm["method"] = cell_methods.pop(0)

            if not cell_methods:
                out.append(cm)
                break

            # Climatological statistics, and statistics which apply to
            # portions of cells
            while cell_methods[0] in ("within", "where", "over"):
                attr = cell_methods.pop(0)
                cm[attr] = cell_methods.pop(0)
                if not cell_methods:
                    break

            if not cell_methods:
                out.append(cm)
                break

            # interval and comment
            intervals = []
            if cell_methods[0].endswith("("):
                cell_methods.pop(0)

                if not (re.search(r"^(interval|comment):$", cell_methods[0])):
                    cell_methods.insert(0, "comment:")

                while not re.search(r"^\)$", cell_methods[0]):
                    term = cell_methods.pop(0)[:-1]

                    if term == "interval":
                        interval = cell_methods.pop(0)
                        if cell_methods[0] != ")":
                            units = cell_methods.pop(0)
                        else:
                            units = None

                        try:
                            parsed_interval = literal_eval(interval)
                        except (SyntaxError, ValueError):
                            if not field_ncvar:
                                raise ValueError(incorrect_interval)

                            self._add_message(
                                field_ncvar,
                                field_ncvar,
                                message=incorrect_interval,
                            )
                            return []

                        try:
                            data = self.implementation.initialise_Data(
                                array=parsed_interval, units=units, copy=False
                            )
                        except Exception:
                            if not field_ncvar:
                                raise ValueError(incorrect_interval)

                            self._add_message(
                                field_ncvar,
                                field_ncvar,
                                message=incorrect_interval,
                                attribute=attribute,
                            )
                            return []

                        intervals.append(data)
                        continue

                    if term == "comment":
                        comment = []
                        while cell_methods:
                            if cell_methods[0].endswith(")"):
                                break
                            if cell_methods[0].endswith(":"):
                                break
                            comment.append(cell_methods.pop(0))

                        cm["comment"] = " ".join(comment)

                if cell_methods[0].endswith(")"):
                    cell_methods.pop(0)

            n_intervals = len(intervals)
            if n_intervals > 1 and n_intervals != len(axes):
                if not field_ncvar:
                    raise ValueError(incorrect_interval)

                self._add_message(
                    field_ncvar,
                    field_ncvar,
                    message=incorrect_interval,
                    attribute=attribute,
                )
                return []

            if intervals:
                cm["interval"] = intervals

            out.append(cm)

        return out

    def _parse_coordinate_interpolation(self, string, parent_ncvar):
        """Parse a CF coordinate_interpolation string.

        Populate the ``self.read_vars`` dictionary with information
        needed to create `Data` objects that represent uncompressed
        subsampled coordinates, and their bounds.

        .. versionadded:: (cfdm) 1.10.0.0

        :Parameters:

            string: `str`
                A coordinate_interpolation attribute string.

            parent_ncvar: `str`
                The netCDF name of the variable containing the
                ``coordinate_interpolation`` attribute.

        :Returns:

             `None`

        """
        g = self.read_vars

        # Separate the attribute string into components. E.g. "lat:
        # lon: bilinear time: linear" becomes ["lat:", "lon:",
        # "bilinear", "time:", "linear"]
        coordinate_interpolation = self._split_string_by_white_space(
            parent_ncvar, string, variables=True, trailing_colon=True
        )

        # Convert the components to a dictionary keyed by
        # interpolation variable name. E.g. ["lat:", "lon:",
        # "bilinear", "time:", "linear"] becomes {"bilinear": ["lat",
        # "lon"], "linear": ["time"]}
        c_i = {}
        coords = []
        tie_point_coordinates = []
        for x in coordinate_interpolation:
            if x.endswith(":"):
                # Strip the trailing colon from the tie point
                # coordinate variable name
                coords.append(x[:-1])
                continue

            c_i[x] = coords
            tie_point_coordinates.extend(coords)

            coords = []

        coordinate_interpolation = c_i

        ok = self._check_coordinate_interpolation(
            parent_ncvar, string, coordinate_interpolation
        )
        if not ok:
            return

        g["tie_point_ncvar"][parent_ncvar] = tie_point_coordinates

        # Record the interpolation variable contents
        for interpolation_ncvar, coords in coordinate_interpolation.items():
            if interpolation_ncvar in g["interpolation"]:
                # This interpolation variable has already been
                # recorded
                continue

            attrs = g["variable_attributes"][interpolation_ncvar].copy()
            record = {
                "interpolation_name": attrs.get("interpolation_name"),
                "interpolation_description": attrs.get(
                    "interpolation_description"
                ),
                "computational_precision": attrs.get(
                    "computational_precision"
                ),
                "subsampled_ncdim": {},
                "interpolation_parameters": {},
            }

            # Loop round interpolated dimensions
            tie_point_mappings = self._parse_x(
                parent_ncvar, attrs.pop("tie_point_mapping")
            )

            for tie_point_mapping in tie_point_mappings:
                for interpolated_ncdim, x in tie_point_mapping.items():
                    if len(x) < 2:
                        self._add_message(
                            parent_ncvar,
                            interpolation_ncvar,
                            message=(
                                "tie_point_mapping attribute",
                                "is incorrectly formatted",
                            ),
                            attribute={
                                interpolation_ncvar
                                + ":coordinate_interplation": coordinate_interpolation
                            },
                        )
                        continue

                    tie_point_index_ncvar, subsampled_ncdim = x[0:2]
                    if len(x) == 2:
                        subarea_ncdim = None
                    else:
                        subarea_ncdim = x[2]

                    record["subsampled_ncdim"][subsampled_ncdim] = {
                        "interpolated_ncdim": interpolated_ncdim,
                        "tie_point_index_ncvar": tie_point_index_ncvar,
                        "subarea_ncdim": subarea_ncdim,
                    }

                    # Do not create field constructs from
                    # interpolation variables
                    g["do_not_create_field"].add(interpolation_ncvar)

                    # Create the tie point index variable for this
                    # subsampled dimension
                    if tie_point_index_ncvar not in g["tie_point_index"]:
                        tpi = self._create_tie_point_index(
                            tie_point_index_ncvar,
                            subsampled_ncdim,
                            subarea_ncdim=subarea_ncdim,
                        )
                        g["tie_point_index"][tie_point_index_ncvar] = tpi

                        # Do not create field/domain constructs from
                        # tie point index variables
                        g["do_not_create_field"].add(tie_point_index_ncvar)

            # Create interpolation parameter variables
            interpolation_parameters = attrs.pop(
                "interpolation_parameters", None
            )
            if interpolation_parameters is not None:
                for y in self._parse_x(
                    interpolation_ncvar, interpolation_parameters
                ):
                    for term, param_ncvar in y.items():
                        param_ncvar = param_ncvar[0]
                        record["interpolation_parameters"][term] = param_ncvar

                        if param_ncvar in g["interpolation_parameter"]:
                            # The interpolation parameter variable has
                            # already been created
                            continue

                        # Create the interpolation parameter variable
                        p = self._create_interpolation_parameter(
                            term, param_ncvar
                        )
                        g["interpolation_parameter"][param_ncvar] = p

                        # Do not create field/domain constructs from
                        # interpolation parameter variables
                        g["do_not_create_field"].add(param_ncvar)

            g["interpolation"][interpolation_ncvar] = record

        # Record which tie point coordinate variables span this
        # subsampled dimension, and note the corresponding
        # interpolation variable and interpolated dimension.
        for interpolation_ncvar, coords in coordinate_interpolation.items():
            record = g["interpolation"][interpolation_ncvar]
            subsampled_ncdims = record["subsampled_ncdim"]

            for tp_ncvar in coords:
                coord_ncdims = g["variable_dimensions"][tp_ncvar]

                # Bounds tie points: Need to also record an implied
                # trailing bounds dimension.
                bounds_ncvar = g["variable_attributes"][tp_ncvar].get(
                    "bounds_tie_points"
                )
                if bounds_ncvar is not None:
                    n_subsampled_dims = len(
                        set(coord_ncdims).intersection(subsampled_ncdims)
                    )
                    size = n_subsampled_dims * 2
                    bounds_ncdim = self._new_ncdimension(
                        f"bounds{size}", size=size, use_existing_new=True
                    )

                for ncdim in coord_ncdims:
                    if ncdim not in subsampled_ncdims:
                        continue

                    # Still here? Then `ncdim` is a subsampled
                    # dimension.
                    interpolated_ncdim = subsampled_ncdims[ncdim][
                        "interpolated_ncdim"
                    ]

                    g["compression"].setdefault(ncdim, {})[
                        f"subsampled {parent_ncvar} {tp_ncvar}"
                    ] = {
                        "interpolation_ncvar": interpolation_ncvar,
                        "implied_ncdimensions": [interpolated_ncdim],
                    }

                    # Do not attempt to create field/domain constructs
                    # from tie point coordinate variables
                    g["do_not_create_field"].add(tp_ncvar)

                    # Bounds tie points
                    if bounds_ncvar is not None:
                        g["compression"][ncdim][
                            f"subsampled {parent_ncvar} {bounds_ncvar}"
                        ] = {
                            "interpolation_ncvar": interpolation_ncvar,
                            "implied_ncdimensions": [interpolated_ncdim],
                            "implied_bounds_ncdimensions": [bounds_ncdim],
                        }

                        # Do not create field/domain constructs from
                        # bounds tie point variables
                        g["do_not_create_field"].add(bounds_ncvar)

    def _create_formula_terms_ref(self, f, key, coord, formula_terms):
        """Create a formula terms coordinate reference.

        Specifically, create a coordinate reference of a netCDF
        formula terms attribute.

        .. versionadded:: (cfdm) 1.7.0

        If the coordinate object has properties 'standard_name' or
        'computed_standard_name' then they are copied to coordinate
        conversion parameters.

        :Parameters:

            f: `Field`

            key: `str`
                The internal identifier of the coordinate.

            coord: `Coordinate`

            formula_terms: `dict`
                The formula_terms attribute value from the netCDF file.

                *Parameter example:*
                  ``formula_terms={'a':'a','b':'b','orog':'surface_altitude'}``

        :Returns:

            `CoordinateReference`

        """
        g = self.read_vars

        domain_ancillaries = {}
        parameters = {}

        for term, ncvar in formula_terms.items():
            # The term's value is a domain ancillary of the field, so
            # we put its identifier into the coordinate reference.
            domain_ancillaries[term] = g["domain_ancillary_key"].get(ncvar)

        for name in ("standard_name", "computed_standard_name"):
            value = self.implementation.get_property(coord, name, None)
            if value is not None:
                parameters[name] = value

        datum_parameters = {}
        coordinate_conversion_parameters = {}
        for x, value in parameters.items():
            if x in g["datum_parameters"]:
                datum_parameters[x] = value
            else:
                coordinate_conversion_parameters[x] = value

        datum = self.implementation.initialise_Datum(
            parameters=datum_parameters
        )

        coordinate_conversion = (
            self.implementation.initialise_CoordinateConversion(
                parameters=coordinate_conversion_parameters,
                domain_ancillaries=domain_ancillaries,
            )
        )

        coordref = self.implementation.initialise_CoordinateReference()

        self.implementation.set_coordinate_reference_coordinates(
            coordinate_reference=coordref, coordinates=[key]
        )

        self.implementation.set_datum(
            coordinate_reference=coordref, datum=datum
        )

        self.implementation.set_coordinate_conversion(
            coordinate_reference=coordref,
            coordinate_conversion=coordinate_conversion,
        )

        return coordref

    def _new_ncdimension(self, ncdim, size=None, use_existing_new=False):
        """TODO.

        .. versionadded:: (cfdm) 1.10.0.0

        :Parameters:

            ncdim: `str
                The name for the new dimension. Might be modified if
                it already exists.

            size: `int`, optional
                The size of the new dimension, which will be set in
                ``self.read_vars["new_dimension_sizes"]``.

            use_existing_new: `bool`, optional
                Use an exising dimension name from
                ``self.read_vars["new_dimension_sizes"]``, if
                possible. When *use_existing_new* is True, *size* is
                silently ignored, i.e. the size may only be set for a
                new dimension that doesn't already exist in
                ``self.read_vars["new_dimension_sizes"]``.

        :Returns:

            `str`
                The new, possibly modified, netCDF dimension name.

        **Examples**

        >>> n._new_ncdimension('bounds2')
        'bounds2'
        >>> n._new_ncdimension('bounds2')
        'bounds2_1'
        >>> n._new_ncdimension('bounds2', use_existing_new=True)
        'bounds2'

        """
        g = self.read_vars
        new_dimension_sizes = g["new_dimension_sizes"]

        using_existing_new = False

        base = ncdim
        n = 0
        while (
            ncdim in g["internal_dimension_sizes"]
            or ncdim in new_dimension_sizes
            or ncdim in g["variables"]
        ):
            if use_existing_new and ncdim in new_dimension_sizes:
                using_existing_new = True
                break

            n += 1
            ncdim = f"{base}_{n}"

        if size is not None and not using_existing_new:
            new_dimension_sizes[ncdim] = size

        return ncdim

    def _dimension_sizes(self, ncvar, parent_ncvar=None):
        """Return the netCDF dimension sizes associated with a variable.

        If the variable has been compressed then it is the *implied
        uncompressed* dimension sizes that are returned.

        .. versionadded:: (cfdm) 1.10.0.0

        :Parameters:

            ncvar: `str`
                The netCDF variable name.

        :Returns:

            `list`
                The list of dimension sizes spanned by the netCDF
                variable.

        """
        g = self.read_vars

        sizes = []
        for ncdim in self._ncdimensions(ncvar, parent_ncvar=parent_ncvar):
            if ncdim in g["internal_dimension_sizes"]:
                sizes.append(g["internal_dimension_sizes"][ncdim])
            elif ncdim in g["new_dimension_sizes"]:
                sizes.append(g["new_dimension_sizes"][ncdim])
            else:
                raise ValueError(
                    f"Can't get the size of netCDF dimension {ncdim}"
                )

        return sizes

    def _ncdimensions(self, ncvar, ncdimensions=None, parent_ncvar=None):
        """Return the netCDF dimensions associated with a variable.

        If the variable has been compressed then it is the *implied
        uncompressed* dimensions that are returned.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            ncvar: `str`
                The netCDF variable name.

            ncdimensions: sequence of `str`, optional
                Use these netCDF dimensions, rather than retrieving
                them from the netCDF variable itself. This allows the
                dimensions of a domain variable to be parsed. Note
                that this parameter only needs to be used once because
                the parsed domain dimensions are automatically stored
                in `self.read_var["domain_ncdimensions"][ncvar]`.

                .. versionadded:: (cfdm) 1.9.0.0

            parent_ncvar: `str`, optional
                TODO

                .. versionadded:: (cfdm) 1.10.0.0

        :Returns:

            `list`
                The list of netCDF dimension names spanned by the
                netCDF variable.

        **Examples**

        >>> n._ncdimensions('humidity')
        ['time', 'lat', 'lon']

        For a variable compressed by gathering:

           dimensions:
             lat=73;
             lon=96;
             landpoint=2381;
             depth=4;
           variables:
             int landpoint(landpoint);
               landpoint:compress="lat lon";
             float landsoilt(depth,landpoint);
               landsoilt:long_name="soil temperature";
               landsoilt:units="K";

        we would have

        >>> n._ncdimensions('landsoilt')
        ['depth', 'lat', 'lon']

        """
        g = self.read_vars

        variable = g["variables"][ncvar]

        if ncdimensions is None:
            domain = False
            domain_ncdimensions = g["domain_ncdimensions"].get(ncvar)
            if domain_ncdimensions is None:
                # Get dimensions from the netCDF variable array
                ncdimensions = g["variable_dimensions"][ncvar]
            else:
                # Use the pre-recorded domain variable dimensions
                ncdimensions = domain_ncdimensions
                domain = True
        else:
            domain = True

        ncdimensions = list(ncdimensions)

        if self._is_char(ncvar) and variable.ndim >= 1:
            # Remove the trailing string-length dimension
            ncdimensions.pop()

        # Check for dimensions which have been compressed. If there
        # are any, then return the netCDF dimensions for the
        # uncompressed variable.
        compression = g["compression"]

        if compression and set(compression).intersection(ncdimensions):
            implied_bounds_ncdimensions = None

            for ncdim in ncdimensions:
                if ncdim not in compression:
                    continue

                c = compression[ncdim]

                if ncvar not in c.get("netCDF_variables", (ncvar,)):
                    # This variable is not compressed, even though it
                    # spans a dimension that is compressed for some
                    # other variables For example, this sort of
                    # situation may arise with simple geometries.
                    continue

                i = ncdimensions.index(ncdim)

                if "gathered" in c:
                    # Compression by gathering
                    ncdimensions[i : i + 1] = c["gathered"][
                        "implied_ncdimensions"
                    ]
                    break
                elif "ragged_indexed_contiguous" in c:
                    # Indexed contiguous ragged array.
                    #
                    # Check this before ragged_indexed and
                    # ragged_contiguous because both of these will
                    # exist for an array that is both indexed and
                    # contiguous.
                    ncdimensions[i : i + 1] = c["ragged_indexed_contiguous"][
                        "implied_ncdimensions"
                    ]
                    break
                elif "ragged_contiguous" in c:
                    # Contiguous ragged array
                    ncdimensions[i : i + 1] = c["ragged_contiguous"][
                        "implied_ncdimensions"
                    ]
                    break
                elif "ragged_indexed" in c:
                    # Indexed ragged array
                    ncdimensions[i : i + 1] = c["ragged_indexed"][
                        "implied_ncdimensions"
                    ]
                    break
                elif (
                    parent_ncvar is not None
                    and f"subsampled {parent_ncvar} {ncvar}" in c
                ):
                    # Subsampled array. Do not break here because
                    # subsampled variables can have more than one
                    # compressed dimension. (CF>=1.9)
                    c = c[f"subsampled {parent_ncvar} {ncvar}"]
                    ncdimensions[i : i + 1] = c["implied_ncdimensions"]
                    implied_bounds_ncdimensions = c.get(
                        "implied_bounds_ncdimensions"
                    )

            if implied_bounds_ncdimensions:
                # Add the implied bounds dimensions for bounds tie
                # points (CF>=1.9)
                ncdimensions.extend(implied_bounds_ncdimensions)

        out = list(map(str, ncdimensions))

        if domain:
            # Record the domain variable dimensions
            g["domain_ncdimensions"][ncvar] = out

        return out

    def _create_gathered_array(
        self,
        gathered_array=None,
        uncompressed_shape=None,
        compressed_dimensions=None,
        list_variable=None,
    ):
        """Creates Data for a compressed-by-gathering netCDF variable.

        Specifically, a `Data` object is created.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            gathered_array: `NetCDFArray`

            compressed_dimensions: sequence of `int`
                The position of the compressed dimension in the
                compressed array.

            list_variable: `List`

        :Returns:

            `GatheredAarray`

        """
        uncompressed_ndim = len(uncompressed_shape)
        uncompressed_size = int(reduce(operator.mul, uncompressed_shape, 1))

        return self.implementation.initialise_GatheredArray(
            compressed_array=gathered_array,
            ndim=uncompressed_ndim,
            shape=uncompressed_shape,
            size=uncompressed_size,
            compressed_dimensions=compressed_dimensions,
            list_variable=list_variable,
        )

    def _create_ragged_contiguous_array(
        self,
        ragged_contiguous_array,
        uncompressed_shape=None,
        count_variable=None,
    ):
        """Creates Data for a contiguous ragged array variable.

        Creates a `Data` object for a compressed-by-contiguous-ragged-
        array netCDF variable.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            ragged_contiguous_array: `Data`

            uncompressed_shape; `tuple`

            count_variable: `Count`

        :Returns:

            `RaggedContiguousArray`

        """
        #        uncompressed_ndim = len(uncompressed_shape)
        #        uncompressed_size = int(reduce(operator.mul, uncompressed_shape, 1))

        return self.implementation.initialise_RaggedContiguousArray(
            compressed_array=ragged_contiguous_array,
            #            ndim=uncompressed_ndim,
            shape=uncompressed_shape,
            #            size=uncompressed_size,
            count_variable=count_variable,
        )

    def _create_ragged_indexed_array(
        self,
        ragged_indexed_array,
        uncompressed_shape=None,
        index_variable=None,
    ):
        """Creates Data for an indexed ragged array variable.

        .. versionadded:: (cfdm) 1.7.0

        :Returns:

            `RaggedIndexedArray`

        """
        #        uncompressed_ndim = len(uncompressed_shape)
        #        uncompressed_size = int(reduce(operator.mul, uncompressed_shape, 1))

        return self.implementation.initialise_RaggedIndexedArray(
            compressed_array=ragged_indexed_array,
            #            ndim=uncompressed_ndim,
            shape=uncompressed_shape,
            #            size=uncompressed_size,
            index_variable=index_variable,
        )

    def _create_ragged_indexed_contiguous_array(
        self,
        ragged_indexed_contiguous_array,
        uncompressed_shape=None,
        count_variable=None,
        index_variable=None,
    ):
        """Creates Data for an indexed contiguous ragged array variable.

        .. versionadded:: (cfdm) 1.7.0

        :Returns:

            `RaggedIndexedContiguousArray`

        """
        #        uncompressed_ndim = len(uncompressed_shape)
        #        uncompressed_size = int(reduce(operator.mul, uncompressed_shape, 1))

        return self.implementation.initialise_RaggedIndexedContiguousArray(
            compressed_array=ragged_indexed_contiguous_array,
            #            ndim=uncompressed_ndim,
            shape=uncompressed_shape,
            #            size=uncompressed_size,
            count_variable=count_variable,
            index_variable=index_variable,
        )

    def _create_subsampled_array(
        self,
        interpolation_name=None,
        subsampled_array=None,
        uncompressed_shape=(),
        tie_point_indices=None,
        parameters=None,
        parameter_dimensions=None,
        interpolation_description=None,
        computational_precision=None,
    ):
        """Creates Data for a tie point coordinates variable.

        Note that dependent tie points are set elsewhere, if
        applicable.

        .. versionadded:: (cfdm) 1.10.0.0

        :Parameters:

            interpolation_name: `str`

            subsampled_array: optional

            shape: sequence of `int`, optional

            interpolation_description: `str`, optional

            computational_precision: `str`, optional
                The floating-point arithmetic precision used during
                the preparation and validation of the compressed
                coordinates.

            tie_point_indices: `dict`, optional

            parameters: `dict`, optional

            parameter_dimensions: `dict`, optional

        :Returns:

            A subsampled array.

        """
        return self.implementation.initialise_SubsampledArray(
            interpolation_name=interpolation_name,
            compressed_array=subsampled_array,
            shape=uncompressed_shape,
            tie_point_indices=tie_point_indices,
            interpolation_description=interpolation_description,
            computational_precision=computational_precision,
            parameters=parameters,
            parameter_dimensions=parameter_dimensions,
        )

    def _create_Data(
        self,
        array,
        ncvar,
        units=None,
        calendar=None,
        **kwargs,
    ):
        """Create a Data object from a netCDF variable.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            array: `Array`
                The file array.

            ncvar: `str`
                The name of the netCDF variable that contains the
                data.

                .. note:: Not currently used here, but must be
                          available to subclasses.

            units: `str`, optional
                The units of *array*. By default, or if `None`, it is
                assumed that there are no units.

            calendar: `str`, optional
                The calendar of *array*. By default, or if `None`, it is
                assumed that there is no calendar.

            kwargs: optional
                Extra parameters to pass to the initialisation of the
                returned `Data` object.

        :Returns:

            `Data`

        """
        data = self.implementation.initialise_Data(
            array=array,
            units=units,
            calendar=calendar,
            copy=False,
            **kwargs,
        )

        return data

    def _copy_construct(self, construct_type, parent_ncvar, ncvar):
        """Return a copy of an existing construct.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            construct_type: `str`
                E.g. 'dimension_coordinate'

            parent_ncvar: `str
                The netCDF variable name of the parent that will
                contain the copy of the construct.

            ncvar: `str`
                The netCDF variable name of the construct.

        :Returns:

                A copy of the construct.

        """
        g = self.read_vars

        component_report = g["component_report"].get(ncvar)

        if component_report is not None:
            for var, report in component_report.items():
                g["dataset_compliance"][parent_ncvar][
                    "non-compliance"
                ].setdefault(var, []).extend(report)

        return self.implementation.copy_construct(g[construct_type][ncvar])

    # ================================================================
    # Methods for checking CF compliance
    #
    # These methods (whose names all start with "_check") check the
    # minimum required for mapping the file to CFDM structural
    # elements. General CF compliance is not checked (e.g. whether or
    # not grid mapping variable has a grid_mapping_name attribute).
    # ================================================================
    def _check_bounds(
        self, parent_ncvar, coord_ncvar, attribute, bounds_ncvar
    ):
        """Check a bounds variable spans the correct dimensions.

        .. versionadded:: (cfdm) 1.7.0

        Checks that

        * The bounds variable has exactly one more dimension than the
          parent coordinate variable

        * The bounds variable's dimensions, other than the trailing
          dimension are the same, and in the same order, as the parent
          coordinate variable's dimensions.

        :Parameters:

            parent_ncvar: `str`
                The netCDF variable name of the parent that contains
                the coordinates.

            nc: `netCDF4.Dataset`
                The netCDF dataset object.

            coord_ncvar: `str`
                The netCDF variable name of the coordinate variable.

            bounds_ncvar: `str`
                The netCDF variable name of the bounds.

        :Returns:

            `bool`

        """
        attribute = {coord_ncvar + ":" + attribute: bounds_ncvar}

        if attribute == "bounds_tie_points":
            variable_type = "Bounds tie points variable"
        else:
            variable_type = "Bounds variable"

        incorrect_dimensions = (variable_type, "spans incorrect dimensions")

        g = self.read_vars

        if bounds_ncvar not in g["internal_variables"]:
            bounds_ncvar, message = self._missing_variable(
                bounds_ncvar, variable_type
            )
            self._add_message(
                parent_ncvar,
                bounds_ncvar,
                message=message,
                attribute=attribute,
                variable=coord_ncvar,
            )
            return False

        ok = True

        c_ncdims = self._ncdimensions(coord_ncvar, parent_ncvar=parent_ncvar)
        b_ncdims = self._ncdimensions(bounds_ncvar, parent_ncvar=parent_ncvar)

        if len(b_ncdims) == len(c_ncdims) + 1:
            if c_ncdims != b_ncdims[:-1]:
                self._add_message(
                    parent_ncvar,
                    bounds_ncvar,
                    message=incorrect_dimensions,
                    attribute=attribute,
                    dimensions=g["variable_dimensions"][bounds_ncvar],
                    variable=coord_ncvar,
                )
                ok = False

        else:
            self._add_message(
                parent_ncvar,
                bounds_ncvar,
                message=incorrect_dimensions,
                attribute=attribute,
                dimensions=g["variable_dimensions"][bounds_ncvar],
                variable=coord_ncvar,
            )
            ok = False

        return ok

    def _check_geometry_node_coordinates(
        self, field_ncvar, node_ncvar, geometry
    ):
        """Check a geometry node coordinate variable.

        .. versionadded:: (cfdm) 1.8.6

        :Parameters:

            field_ncvar: `str`
                The netCDF variable name of the parent data variable.

            node_ncvar: `str`
                The netCDF variable name of the node coordinate variable.

            geometry: `dict`

        :Returns:

            `bool`

        """
        g = self.read_vars

        geometry_ncvar = g["variable_geometry"].get(field_ncvar)

        attribute = {
            field_ncvar
            + ":"
            + geometry_ncvar: " ".join(geometry["node_coordinates"])
        }

        if node_ncvar not in g["internal_variables"]:
            node_ncvar, message = self._missing_variable(
                node_ncvar, "Node coordinate variable"
            )
            self._add_message(
                field_ncvar,
                node_ncvar,
                message=message,
                attribute=attribute,
                variable=field_ncvar,
            )
            return False

        ok = True

        if node_ncvar not in geometry.get("node_coordinates", ()):
            self._add_message(
                field_ncvar,
                node_ncvar,
                message=(
                    "Node coordinate variable",
                    "not in node_coordinates",
                ),
                attribute=attribute,
                variable=field_ncvar,
            )
            ok = False

        return ok

    def _check_cell_measures(self, field_ncvar, string, parsed_string):
        """Checks requirements.

        * 7.2.requirement.1
        * 7.2.requirement.3
        * 7.2.requirement.4

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            field_ncvar: `str`

            string: `str`
                The value of the netCDF cell_measures attribute.

            parsed_string: `list`

        :Returns:

            `bool`

        """
        attribute = {field_ncvar + ":cell_measures": string}

        incorrectly_formatted = (
            "cell_measures attribute",
            "is incorrectly formatted",
        )
        incorrect_dimensions = (
            "Cell measures variable",
            "spans incorrect dimensions",
        )
        missing_variable = (
            "Cell measures variable",
            "is not in file nor referenced by the external_variables "
            "global attribute",
        )

        g = self.read_vars

        if not parsed_string:
            self._add_message(
                field_ncvar,
                field_ncvar,
                message=incorrectly_formatted,
                attribute=attribute,
                conformance="7.2.requirement.1",
            )
            return False

        parent_dimensions = self._ncdimensions(field_ncvar)
        external_variables = g["external_variables"]

        ok = True
        for x in parsed_string:
            measure, values = list(x.items())[0]
            if len(values) != 1:
                self._add_message(
                    field_ncvar,
                    field_ncvar,
                    message=incorrectly_formatted,
                    attribute=attribute,
                    conformance="7.2.requirement.1",
                )
                ok = False
                continue

            ncvar = values[0]

            unknown_external = ncvar in external_variables

            # Check that the variable exists in the file, or if not
            # that it is listed in the 'external_variables' global
            # file attribute.
            if not unknown_external and ncvar not in g["variables"]:
                self._add_message(
                    field_ncvar,
                    ncvar,
                    message=missing_variable,
                    attribute=attribute,
                    conformance="7.2.requirement.3",
                )
                ok = False
                continue

            if not unknown_external:
                dimensions = self._ncdimensions(ncvar)
                if not unknown_external and not self._dimensions_are_subset(
                    ncvar, dimensions, parent_dimensions
                ):
                    # The cell measure variable's dimensions do NOT span a
                    # subset of the parent variable's dimensions.
                    self._add_message(
                        field_ncvar,
                        ncvar,
                        message=incorrect_dimensions,
                        attribute=attribute,
                        dimensions=g["variable_dimensions"][ncvar],
                        conformance="7.2.requirement.4",
                    )
                    ok = False

        return ok

    def _check_geometry_attribute(self, parent_ncvar, string, parsed_string):
        """Checks requirements.

        .. versionadded:: (cfdm) 1.8.0

        :Parameters:

            parent_ncvar: `str`
                The netCDF variable name of the parent data variable.

            string: `str`
                The value of the netCDF geometry attribute.

            parsed_string: `list`

        :Returns:

            `bool`

        """
        attribute = {parent_ncvar + ":geometry": string}

        incorrectly_formatted = (
            "geometry attribute",
            "is incorrectly formatted",
        )

        g = self.read_vars

        if len(parsed_string) != 1:
            self._add_message(
                parent_ncvar,
                parent_ncvar,
                message=incorrectly_formatted,
                attribute=attribute,
                conformance="?",
            )
            return False

        for ncvar in parsed_string:
            # Check that the geometry variable exists in the file
            if ncvar not in g["variables"]:
                ncvar, message = self._missing_variable(
                    ncvar, "Geometry variable"
                )
                self._add_message(
                    parent_ncvar,
                    ncvar,
                    message=message,
                    attribute=attribute,
                    conformance="?",
                )
                return False

        return True

    def _check_ancillary_variables(self, field_ncvar, string, parsed_string):
        """Checks requirements.

        :Parameters:

            field_ncvar: `str`

            ancillary_variables: `str`
                The value of the netCDF ancillary_variables attribute.

            parsed_ancillary_variables: `list`

        :Returns:

            `bool`

        """
        attribute = {field_ncvar + ":ancillary_variables": string}

        incorrectly_formatted = (
            "ancillary_variables attribute",
            "is incorrectly formatted",
        )
        incorrect_dimensions = (
            "Ancillary variable",
            "spans incorrect dimensions",
        )

        g = self.read_vars

        if not parsed_string:
            d = self._add_message(
                field_ncvar,
                field_ncvar,
                message=incorrectly_formatted,
                attribute=attribute,
            )

            # Though an error of sorts, set as debug level message;
            # read not terminated
            if is_log_level_debug(logger):
                logger.debug(
                    f"    Error processing netCDF variable {field_ncvar}: "
                    f"{d['reason']}"
                )  # pragma: no cover

            return False

        parent_dimensions = self._ncdimensions(field_ncvar)

        ok = True
        for ncvar in parsed_string:
            # Check that the variable exists in the file
            if ncvar not in g["internal_variables"]:
                ncvar, message = self._missing_variable(
                    ncvar, "Ancillary variable"
                )
                self._add_message(
                    field_ncvar, ncvar, message=message, attribute=attribute
                )
                return False

            if not self._dimensions_are_subset(
                ncvar, self._ncdimensions(ncvar), parent_dimensions
            ):
                # The ancillary variable's dimensions do NOT span a
                # subset of the parent variable's dimensions
                self._add_message(
                    field_ncvar,
                    ncvar,
                    message=incorrect_dimensions,
                    attribute=attribute,
                    dimensions=g["variable_dimensions"][ncvar],
                )
                ok = False

        return ok

    def _check_auxiliary_or_scalar_coordinate(
        self, parent_ncvar, coord_ncvar, string
    ):
        """Checks requirements.

          * 5.requirement.5
          * 5.requirement.6

        :Parameters:

        parent_ncvar: `str`
            NetCDF name of parent data or domain variable.

        :Returns:

            `bool`

        """
        attribute = {parent_ncvar + ":coordinates": string}

        incorrect_dimensions = (
            "Auxiliary/scalar coordinate variable",
            "spans incorrect dimensions",
        )

        g = self.read_vars

        if coord_ncvar not in g["internal_variables"]:
            coord_ncvar, message = self._missing_variable(
                coord_ncvar, "Auxiliary/scalar coordinate variable"
            )
            self._add_message(
                parent_ncvar,
                coord_ncvar,
                message=message,
                attribute=attribute,
                conformance="5.requirement.5",
            )
            self._add_message(
                parent_ncvar,
                coord_ncvar,
                message=message,
                attribute=attribute,
                conformance="5.requirement.5",
            )
            return False

        # Check that the variable's dimensions span a subset of the
        # parent variable's dimensions (allowing for char variables
        # with a trailing dimension)
        if not self._dimensions_are_subset(
            coord_ncvar,
            self._ncdimensions(coord_ncvar, parent_ncvar=parent_ncvar),
            self._ncdimensions(parent_ncvar),
        ):
            self._add_message(
                parent_ncvar,
                coord_ncvar,
                message=incorrect_dimensions,
                attribute=attribute,
                dimensions=g["variable_dimensions"][coord_ncvar],
                conformance="5.requirement.6",
            )
            return False

        return True

    def _check_tie_point_coordinates(
        self, parent_ncvar, tie_point_ncvar, string
    ):
        """Checks requirements.

        * 8.3.requirement.1
        * 8.3.requirement.5

        :Parameters:

        parent_ncvar: `str`
            NetCDF name of parent data or domain variable.

        :Returns:

            `bool`

        """
        attribute = {parent_ncvar + ":coordinate_interpolation": string}

        incorrect_dimensions = (
            "Tie point coordinate variable",
            "spans incorrect dimensions",
        )

        g = self.read_vars

        if tie_point_ncvar not in g["internal_variables"]:
            ncvar, message = self._missing_variable(
                tie_point_ncvar, "Tie point coordinate variable"
            )
            self._add_message(
                parent_ncvar,
                ncvar,
                message=message,
                attribute=attribute,
                conformance="8.3.requirement.1",
            )
            return False

        # Check that the variable's dimensions span a subset of the
        # parent variable's dimensions (allowing for char variables
        # with a trailing dimension)
        if not self._dimensions_are_subset(
            tie_point_ncvar,
            self._ncdimensions(tie_point_ncvar, parent_ncvar=parent_ncvar),
            self._ncdimensions(parent_ncvar),
        ):
            self._add_message(
                parent_ncvar,
                tie_point_ncvar,
                message=incorrect_dimensions,
                attribute=attribute,
                dimensions=g["variable_dimensions"][tie_point_ncvar],
                conformance="8.3.requirement.5",
            )
            return False

        return True

    def _dimensions_are_subset(self, ncvar, dimensions, parent_dimensions):
        """True if dimensions are a subset of the parent dimensions."""
        if not set(dimensions).issubset(parent_dimensions):
            if not (
                self._is_char(ncvar)
                and set(dimensions[:-1]).issubset(parent_dimensions)
            ):
                return False

        return True

    def _check_grid_mapping(
        self, parent_ncvar, grid_mapping, parsed_grid_mapping
    ):
        """Checks requirements.

          * 5.6.requirement.1
          * 5.6.requirement.2
          * 5.6.requirement.3

        :Parameters:

        parent_ncvar: `str`
            NetCDF name of parent data or domain variable.

            grid_mapping: `str`

            parsed_grid_mapping: `dict`

        :Returns:

            `bool`

        """
        attribute = {parent_ncvar + ":grid_mapping": grid_mapping}

        incorrectly_formatted = (
            "grid_mapping attribute",
            "is incorrectly formatted",
        )

        g = self.read_vars

        if not parsed_grid_mapping:
            self._add_message(
                parent_ncvar,
                parent_ncvar,
                message=incorrectly_formatted,
                attribute=attribute,
                conformance="5.6.requirement.1",
            )
            return False

        ok = True
        for x in parsed_grid_mapping:
            grid_mapping_ncvar, values = list(x.items())[0]
            if grid_mapping_ncvar not in g["internal_variables"]:
                ok = False
                grid_mapping_ncvar, message = self._missing_variable(
                    grid_mapping_ncvar, "Grid mapping variable"
                )
                self._add_message(
                    parent_ncvar,
                    grid_mapping_ncvar,
                    message=message,
                    attribute=attribute,
                    conformance="5.6.requirement.2",
                )
                self._add_message(
                    parent_ncvar,
                    grid_mapping_ncvar,
                    message=message,
                    attribute=attribute,
                    conformance="5.6.requirement.2",
                )

            for coord_ncvar in values:
                if coord_ncvar not in g["internal_variables"]:
                    ok = False
                    coord_ncvar, message = self._missing_variable(
                        coord_ncvar, "Grid mapping coordinate variable"
                    )
                    self._add_message(
                        parent_ncvar,
                        coord_ncvar,
                        message=message,
                        attribute=attribute,
                        conformance="5.6.requirement.3",
                    )
                    self._add_message(
                        parent_ncvar,
                        coord_ncvar,
                        message=message,
                        attribute=attribute,
                        conformance="5.6.requirement.3",
                    )

        if not ok:
            return False

        return True

    def _check_compress(self, parent_ncvar, compress, parsed_compress):
        """Check a compressed dimension is valid and in the file."""
        attribute = {parent_ncvar + ":compress": compress}

        incorrectly_formatted = (
            "compress attribute",
            "is incorrectly formatted",
        )
        missing_dimension = ("Compressed dimension", "is not in file")

        if not parsed_compress:
            self._add_message(
                None,
                parent_ncvar,
                message=incorrectly_formatted,
                attribute=attribute,
            )
            return False

        ok = True

        dimensions = self.read_vars["internal_dimension_sizes"]

        for ncdim in parsed_compress:
            if ncdim not in dimensions:
                self._add_message(
                    None,
                    parent_ncvar,
                    message=missing_dimension,
                    attribute=attribute,
                )
                ok = False

        return ok

    def _check_node_coordinates(
        self,
        field_ncvar,
        geometry_ncvar,
        node_coordinates,
        parsed_node_coordinates,
    ):
        """Check node coordinate variables are valid and in the file."""
        attribute = {geometry_ncvar + ":node_coordinates": node_coordinates}

        g = self.read_vars

        incorrectly_formatted = (
            "node_coordinates attribute",
            "is incorrectly formatted",
        )
        missing_attribute = ("node_coordinates attribute", "is missing")

        if node_coordinates is None:
            self._add_message(
                field_ncvar,
                geometry_ncvar,
                message=missing_attribute,
                attribute=attribute,
            )
            return False

        if not parsed_node_coordinates:
            # There should be at least one node coordinate variable
            self._add_message(
                field_ncvar,
                geometry_ncvar,
                message=incorrectly_formatted,
                attribute=attribute,
            )
            return False

        ok = True

        for ncvar in parsed_node_coordinates:
            # Check that the node coordinate variable exists in the
            # file
            if ncvar not in g["internal_variables"]:
                ncvar, message = self._missing_variable(
                    ncvar, "Node coordinate variable"
                )
                self._add_message(
                    field_ncvar, ncvar, message=message, attribute=attribute
                )
                ok = False

        return ok

    def _check_node_count(
        self, field_ncvar, geometry_ncvar, node_count, parsed_node_count
    ):
        """Check node count variable is valid and exists in the file."""
        attribute = {geometry_ncvar + ":node_count": node_count}

        g = self.read_vars

        if node_count is None:
            return True

        incorrectly_formatted = (
            "node_count attribute",
            "is incorrectly formatted",
        )

        if len(parsed_node_count) != 1:
            self._add_message(
                field_ncvar,
                geometry_ncvar,
                message=incorrectly_formatted,
                attribute=attribute,
            )
            return False

        ok = True

        for ncvar in parsed_node_count:
            # Check that the node count variable exists in the file
            if ncvar not in g["internal_variables"]:
                ncvar, message = self._missing_variable(
                    ncvar, "Node count variable"
                )
                self._add_message(
                    field_ncvar, ncvar, message=message, attribute=attribute
                )
                ok = False

        return ok

    def _check_part_node_count(
        self,
        field_ncvar,
        geometry_ncvar,
        part_node_count,
        parsed_part_node_count,
    ):
        """Check part node count variable is valid and in the file."""
        if part_node_count is None:
            return True

        attribute = {geometry_ncvar + ":part_node_count": part_node_count}

        g = self.read_vars

        incorrectly_formatted = (
            "part_node_count attribute",
            "is incorrectly formatted",
        )

        if len(parsed_part_node_count) != 1:
            self._add_message(
                field_ncvar,
                geometry_ncvar,
                message=incorrectly_formatted,
                attribute=attribute,
            )
            return False

        ok = True

        for ncvar in parsed_part_node_count:
            # Check that the variable exists in the file
            if ncvar not in g["internal_variables"]:
                ncvar, message = self._missing_variable(
                    ncvar, "Part node count variable"
                )
                self._add_message(
                    field_ncvar, ncvar, message=message, attribute=attribute
                )
                ok = False

        return ok

    def _check_interior_ring(
        self, field_ncvar, geometry_ncvar, interior_ring, parsed_interior_ring
    ):
        """Check all interior ring variables exist in the file.

        :Returns:

            `bool`

        """
        if interior_ring is None:
            return True

        attribute = {geometry_ncvar + ":interior_ring": interior_ring}

        g = self.read_vars

        incorrectly_formatted = (
            "interior_ring attribute",
            "is incorrectly formatted",
        )

        if not parsed_interior_ring:
            self._add_message(
                field_ncvar,
                geometry_ncvar,
                message=incorrectly_formatted,
                attribute=attribute,
            )
            return False

        ok = True

        if len(parsed_interior_ring) != 1:
            self._add_message(
                field_ncvar,
                geometry_ncvar,
                message=incorrectly_formatted,
                attribute=attribute,
            )
            return False

        for ncvar in parsed_interior_ring:
            # Check that the variable exists in the file
            if ncvar not in g["internal_variables"]:
                ncvar, message = self._missing_variable(
                    ncvar, "Interior ring variable"
                )
                self._add_message(
                    field_ncvar, ncvar, message=message, attribute=attribute
                )
                ok = False

        return ok

    def _check_instance_dimension(self, parent_ncvar, instance_dimension):
        """Check that the instance dimension name is a netCDF dimension.

        .. versionadded:: (cfdm) 1.7.0

        CF-1.7 Appendix A

        * instance_dimension: An attribute which identifies an index
                              variable and names the instance dimension to
                              which it applies. The index variable
                              indicates that the indexed ragged array
                              representation is being used for a
                              collection of features.

        """
        attribute = {parent_ncvar + ":instance_dimension": instance_dimension}

        missing_dimension = ("Instance dimension", "is not in file")

        if (
            instance_dimension
            not in self.read_vars["internal_dimension_sizes"]
        ):
            self._add_message(
                None,
                parent_ncvar,
                message=missing_dimension,
                attribute=attribute,
            )
            return False

        return True

    def _check_sample_dimension(self, parent_ncvar, sample_dimension):
        """Check that the sample dimension name is a netCDF dimension.

        .. versionadded:: (cfdm) 1.7.0

        CF-1.7 Appendix A

        * sample_dimension: An attribute which identifies a count variable
                            and names the sample dimension to which it
                            applies. The count variable indicates that the
                            contiguous ragged array representation is
                            being used for a collection of features.

        """
        return sample_dimension in self.read_vars["internal_dimension_sizes"]

    def _check_coordinate_interpolation(
        self,
        parent_ncvar,
        coordinate_interpolation,
        parsed_coordinate_interpolation,
    ):
        """Check a TODO.

        .. versionadded:: (cfdm) 1.10.0.0

        :Parameters:

            parent_ncvar: `str`

            coordinate_interpolation: `str`
                A CF coordinate_interpolation attribute string.

            parsed_coordinate_interpolation: `dict`

        :Returns:

            `bool`

        """
        if not parsed_coordinate_interpolation:
            return True

        attribute = {
            parent_ncvar + ":coordinate_interplation": coordinate_interpolation
        }

        g = self.read_vars

        incorrectly_formatted = (
            "coordinate_interpolation attribute",
            "is incorrectly formatted",
        )

        if not parsed_coordinate_interpolation:
            self._add_message(
                parent_ncvar,
                parent_ncvar,
                message=incorrectly_formatted,
                attribute=attribute,
                conformance="TODO",
            )
            return False

        ok = True

        for interp_ncvar, coords in parsed_coordinate_interpolation.items():
            # Check that the interpolation variable exists in the file
            if interp_ncvar not in g["internal_variables"]:
                ncvar, message = self._missing_variable(
                    interp_ncvar, "Interpolation variable"
                )
                self._add_message(
                    parent_ncvar, ncvar, message=message, attribute=attribute
                )
                ok = False

            attrs = g["variable_attributes"][interp_ncvar]
            if "tie_point_mapping" not in attrs:
                self._add_message(
                    parent_ncvar,
                    interp_ncvar,
                    message=(
                        "Interpolation variable",
                        "has no tie_point_mapping attribute",
                    ),
                    attribute=attribute,
                )
                ok = False

            # Check that the tie point coordinate variables exist in
            # the file
            for tie_point_ncvar in coords:
                if tie_point_ncvar not in g["internal_variables"]:
                    ncvar, message = self._missing_variable(
                        tie_point_ncvar, "Tie point coordinate variable"
                    )
                    self._add_message(
                        parent_ncvar,
                        ncvar,
                        message=message,
                        attribute=attribute,
                    )
                    ok = False

        # TODO check tie point variable dimensions

        return ok

    def _split_string_by_white_space(
        self, parent_ncvar, string, variables=False, trailing_colon=False
    ):
        """Split a string by white space.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            parent_ncvar: `str`
                Not used

            string: `str or `None`

            variables: `bool`
                If True then *string* contains internal netCDF variable
                names. (Not sure yet what to do about external names.)

                .. versionadded:: (cfdm) 1.8.6

            trailing_colon: `bool`
                If True then trailing colons are not part of the
                string components that are variable names. Ignored if
                *variables* is False.

                .. versionadded:: (cfdm) 1.10.0.0

        :Returns:

            `list`

        """
        if string is None:
            return []

        try:
            out = string.split()
        except AttributeError:
            out = []
        else:
            if variables and out and self.read_vars["has_groups"]:
                mapping = self.read_vars["flattener_variables"]
                if trailing_colon:
                    out = [
                        mapping[ncvar[:-1]] + ":"
                        if ncvar.endswith(":")
                        else mapping[ncvar]
                        for ncvar in out
                    ]
                else:
                    out = [mapping[ncvar] for ncvar in out]

        return out

    def _parse_grid_mapping(self, parent_ncvar, string):
        """Parse a netCDF grid_mapping attribute.

        .. versionadded:: (cfdm) 1.7.0

        """
        g = self.read_vars

        out = []

        if g["CF>=1.7"]:
            # The grid mapping attribute may point to a single netCDF
            # variable OR to multiple variables with associated
            # coordinate variables (CF>=1.7)
            out = self._parse_x(parent_ncvar, string, keys_are_variables=True)
        else:
            # The grid mapping attribute may only point to a single
            # netCDF variable (CF<=1.6)
            out = self._split_string_by_white_space(
                parent_ncvar, string, variables=True
            )

            if len(out) == 1:
                out = [{out[0]: []}]

        return out

    def _parse_x(
        self,
        parent_ncvar,
        string,
        keys_are_variables=False,
        keys_are_dimensions=False,
    ):
        """Parse CF-netCDF strings.

        Handling of CF-compliant strings:
        ---------------------------------

        'area: areacello' ->
            [{'area': ['areacello']}]

        'area: areacello volume: volumecello' ->
            [{'area': ['areacello']}, {'volume': ['volumecello']}]

        'rotated_latitude_longitude' ->
            [{'rotated_latitude_longitude': []}]

        'rotated_latitude_longitude: x y latitude_longitude: lat lon' ->
            [{'rotated_latitude_longitude': ['x', 'y']},
             {'latitude_longitude': ['lat', 'lon']}]

        'rotated_latitude_longitude: x latitude_longitude: lat lon' ->
            [{'rotated_latitude_longitude': ['x']},
             {'latitude_longitude': ['lat', 'lon']}]

        'a: A b: B orog: OROG' ->
            [{'a': ['A']}, {'b': ['B']}, {'orog': ['OROG']}]

        Handling of non-CF-compliant strings:
        -------------------------------------

        'area' ->
            [{'area': []}]

        'a: b: B orog: OROG' ->
            []

        'rotated_latitude_longitude:' ->
            []

        'rotated_latitude_longitude zzz' ->
            []

        .. versionadded:: (cfdm) 1.7.0

        """
        # ============================================================
        # Thanks to Alan Iwi for creating these regular expressions
        # ============================================================

        def subst(s):
            """Substitutes WORD and SEP tokens for regular expressions.

            All WORD tokens are replaced by the expression for a space
            and all SEP tokens are replaced by the expression for the
            end of string.

            """
            return s.replace("WORD", r"[A-Za-z0-9_#]+").replace(
                "SEP", r"(\s+|$)"
            )

        out = []

        pat_value = subst("(?P<value>WORD)SEP")
        pat_values = f"({pat_value})+"

        pat_mapping = subst(
            f"(?P<mapping_name>WORD):SEP(?P<values>{pat_values})"
        )
        pat_mapping_list = f"({pat_mapping})+"

        pat_all = subst(
            f"((?P<sole_mapping>WORD)|(?P<mapping_list>{pat_mapping_list}))$"
        )

        m = re.match(pat_all, string)
        if m is None:
            return []

        sole_mapping = m.group("sole_mapping")
        if sole_mapping:
            out.append({sole_mapping: []})
        else:
            mapping_list = m.group("mapping_list")
            for mapping in re.finditer(pat_mapping, mapping_list):
                term = mapping.group("mapping_name")
                values = [
                    value.group("value")
                    for value in re.finditer(
                        pat_value, mapping.group("values")
                    )
                ]
                out.append({term: values})

        # If there are groups then replace flattened variable names
        # with absolute path names (CF>=1.8)
        g = self.read_vars
        if g["has_groups"]:
            for x in out:
                for key, value in x.copy().items():
                    if keys_are_variables:
                        del x[key]
                        key = g["flattener_variables"][key]

                    x[key] = [
                        g["flattener_variables"][ncvar] for ncvar in value
                    ]

        return out

    def _netCDF4_group(self, nc, name):
        """Return the group of a variable or dimension in the dataset.

        Given a dataset and a variable or dimension name, return the
        group object for the name, and the name within the group.

        .. versionadded:: (cfdm) 1.8.8.1

        :Parameters:

            nc: `netCDF4._netCDF4.Dataset` or `netCDF4._netCDF4.Group`

            name: `str`

        :Returns:

            `netCDF4._netCDF4.Dataset` or `netCDF4._netCDF4.Group`, `str`

        **Examples**

        >>> group, name = n._netCDF4_group(nc, 'time')
        >>> group.name, name
        ('/', 'time')
        >>> group, name = n._netCDF4_group(nc, '/surfacelayer/Z')
        >>> group.name, name
        ('surfacelayer', 'Z')

        """
        group = nc
        path = name.split("/")
        for group_name in path[1:-1]:
            group = group[group_name]

        return group, path[-1]

    def _ugrid_parse_mesh_topology(self, mesh_ncvar, attributes):
        """Parse a UGRID mesh topology or location index set variable.

        Adds a new entry to ``self.read_vars['mesh']``. Adds a
        location_index_set variable to
        ``self.read_vars["do_not_create_field"]``.

        .. versionadded:: (cfdm) UGRIDVER

        :Parameters:

            mesh_ncvar: `str`, optional
                The netCDF name of a netCDF that might be a mesh
                topology variable.

            attributes: `dict`
                The netCDF attributes of *ncvar*.

        :Returns:

            `None`

        """
        g = self.read_vars
        if not self._ugrid_check_mesh_topology(mesh_ncvar):
            return

        # Do not attempt to create a field or domain construct from a
        # mesh topology variable, nor mesh topology connectivity
        # variables.
        do_not_create_field = g["do_not_create_field"]
        if not g["domain"]:
            do_not_create_field.add(mesh_ncvar)

        for attr, value in attributes.items():
            if attr in (
                "face_node_connectivity",
                "face_face_connectivity",
                "face_edge_connectivity",
                "edge_node_connectivity",
                "edge_face_connectivity",
                "volume_node_connectivity",
                "volume_edge_connectivity",
                "volume_face_connectivity",
                "volume_volume_connectivity",
                "volume_shape_type",
            ):
                do_not_create_field.add(value)

        # ------------------------------------------------------------
        # Initialise the Mesh instance
        # ------------------------------------------------------------
        mesh = Mesh(
            mesh_ncvar=mesh_ncvar,
            mesh_attributes=attributes,
            mesh_id=uuid4().hex,
        )

        locations = ("node", "edge", "face")

        # ------------------------------------------------------------
        # Find the discrete axis for each location of the mesh
        # topology
        # ------------------------------------------------------------
        mesh_ncdim = {}
        for location in locations:
            if location == "node":
                node_coordinates = self._split_string_by_white_space(
                    None, attributes["node_coordinates"], variables=True
                )
                ncvar = node_coordinates[0]
            else:
                ncvar = attributes.get(f"{location}_node_connectivity")

            ncdim = self.read_vars["variable_dimensions"].get(ncvar)
            if ncdim is None:
                continue

            if len(ncdim) == 1:
                # Node
                i = 0
            else:
                # Edge or face
                i = self._ugrid_cell_dimension(location, ncvar, mesh)

            mesh_ncdim[location] = ncdim[i]

        mesh.ncdim = mesh_ncdim

        # ------------------------------------------------------------
        # Find the netCDF variable names of the coordinates for each
        # location
        # ------------------------------------------------------------
        coordinates_ncvar = {}
        for location in locations:
            coords_ncvar = attributes.get(f"{location}_coordinates", "")
            coords_ncvar = self._split_string_by_white_space(
                None, coords_ncvar, variables=True
            )
            coordinates_ncvar[location] = coords_ncvar
            for ncvar in coords_ncvar:
                do_not_create_field.add(ncvar)

        mesh.coordinates_ncvar = coordinates_ncvar

        # ------------------------------------------------------------
        # Create auxiliary coordinate constructs for each location
        # ------------------------------------------------------------
        auxiliary_coordinates = {}
        for location in locations:
            auxs = self._ugrid_create_auxiliary_coordinates(
                mesh_ncvar, None, mesh, location
            )
            if auxs:
                auxiliary_coordinates[location] = auxs

        mesh.auxiliary_coordinates = auxiliary_coordinates

        # ------------------------------------------------------------
        # Create the domain topology construct for each location
        # ------------------------------------------------------------
        domain_topologies = {}
        for location in locations:
            domain_topology = self._ugrid_create_domain_topology(
                mesh_ncvar, None, mesh, location
            )
            if domain_topology is not None:
                domain_topologies[location] = domain_topology

        mesh.domain_topologies = domain_topologies

        # ------------------------------------------------------------
        # Create cell connectivit constructs for each location
        # ------------------------------------------------------------
        cell_connectivites = {}
        for location in locations:
            conns = self._ugrid_create_cell_connectivities(
                mesh_ncvar, None, mesh, location
            )
            if conns:
                cell_connectivites[location] = conns

        mesh.cell_connectivities = cell_connectivites

        g["mesh"][mesh_ncvar] = mesh

    def _ugrid_parse_location_index_set(self, parent_attributes):
        """Parse a UGRID location index set variable.

        Adds a new entry to ``self.read_vars['mesh']``. Adds a
        location_index_set variable to
        ``self.read_vars["do_not_create_field"]``.

        .. versionadded:: (cfdm) UGRIDVER

        :Parameters:

            parent_attributes: `dict`
                The attributes of a netCDF variable that include
                "location_index_set" attribute.

        :Returns:

            `None`

        """
        g = self.read_vars

        location_index_set_ncvar = parent_attributes["location_index_set"]
        if location_index_set_ncvar in g["mesh"]:
            # The location index set has already been parsed
            return

        if not self._ugrid_check_location_index_set(location_index_set_ncvar):
            return

        location_index_set_attributes = g["variable_attributes"][
            location_index_set_ncvar
        ]
        location = location_index_set_attributes["location"]
        mesh_ncvar = location_index_set_attributes["mesh"]
        attributes = g["variable_attributes"][mesh_ncvar]

        index_set = self._create_data(location_index_set_ncvar)
        start_index = location_index_set_attributes.get("start_index", 0)
        if start_index:
            index_set -= start_index

        # Do not attempt to create a field or domain construct from a
        # location index set variable
        g["do_not_create_field"].add(location_index_set_ncvar)

        g["mesh"][location_index_set_ncvar] = Mesh(
            mesh_ncvar=mesh_ncvar,
            mesh_attributes=attributes,
            location_index_set_ncvar=location_index_set_ncvar,
            location_index_set_attributes=location_index_set_attributes,
            location=location,
            index_set=index_set,
            mesh_id=uuid4().hex,
        )

    def _ugrid_create_auxiliary_coordinates(
        self,
        parent_ncvar,
        f,
        mesh,
        location,
    ):
        """Create auxiliary coordinate constructs from a UGRID mesh.

        .. versionadded:: (cfdm) UGRIDVER

        :Parameters:

            parent_ncvar: `str`
                The netCDF variable name of the parent field construct.

            f: `Field`
                The parent field construct.

            mesh: `Mesh`
                The mesh description, as stored in
                ``self.read_vars['mesh']``.

            location: `str`
                The location of the cells in the mesh topology. One of
                ``'node'``, ``'edge'``, ``'face'``, ``'volume'``.

        :Returns:

            `list` of `AuxiliaryCoordinate`
                The auxiliary coordinates, with bounds, for the UGRID
                cells. May be an empty list.

        """
        if location not in mesh.ncdim:
            return []

        # Get the netCDF variable names of the node
        # coordinates. E.g. ("Mesh2_node_x", "Mesh2_node_y")
        nodes_ncvar = mesh.coordinates_ncvar["node"]

        # Get the netCDF variable names of the cell
        # coordinates. E.g. ("Mesh1_face_x", "Mesh1_face_y"), or None
        # if there aren't any.
        coords_ncvar = mesh.coordinates_ncvar.get(location)

        auxs = []
        if coords_ncvar:
            # There are cell coordinates, so turn them into
            # auxiliary coordinate constructs
            #
            # Note: We are assuming that the node coordinates are
            # ordered identically to the [edge|face|volume]
            # coordinates
            # (https://github.com/ugrid-conventions/ugrid-conventions/issues/67)
            for coord_ncvar, node_ncvar in zip(coords_ncvar, nodes_ncvar):
                # This auxiliary coordinate needs creating from
                # a [node|edge|face|volume]_coordinate variable.
                aux = self._create_auxiliary_coordinate(
                    parent_ncvar, coord_ncvar, None
                )
                if location != "node" and not self.implementation.has_bounds(
                    aux
                ):
                    # These auxiliary [edge|face] coordinates don't
                    # have bounds => create bounds from the mesh
                    # nodes.
                    aux = self._ugrid_create_bounds_from_nodes(
                        parent_ncvar,
                        node_ncvar,
                        f,
                        mesh,
                        location,
                        aux=aux,
                    )

                self.implementation.nc_set_node_coordinate_variable(
                    aux, node_ncvar
                )
                auxs.append(aux)

        elif nodes_ncvar:
            # There are no cell coordinates, so create auxiliary
            # coordinate constructs that are derived from an
            # [edge|face|volume]_node_connectivity variable. These
            # will contain only bounds, with no coordinate values.
            for node_ncvar in nodes_ncvar:
                aux = self._ugrid_create_bounds_from_nodes(
                    parent_ncvar,
                    node_ncvar,
                    f,
                    mesh,
                    location,
                )

                self.implementation.nc_set_node_coordinate_variable(
                    aux, node_ncvar
                )
                auxs.append(aux)

        # Apply a location index set
        index_set = mesh.index_set
        if index_set is not None:
            # Apply a location index set
            auxs = [aux[index_set] for aux in auxs]

        mesh.auxiliary_coordinates[location] = auxs
        return auxs

    def _ugrid_create_bounds_from_nodes(
        self,
        parent_ncvar,
        node_ncvar,
        f,
        mesh,
        location,
        aux=None,
    ):
        """Create coordinate bounds from UGRID nodes.

        .. versionadded:: (cfdm) UGRIDVER

        :Parameters:

            parent_ncvar: `str`
                The netCDF variable name of the parent field construct.

            node_ncvar: `str`
                The netCDF variable name of the UGRID node coordinate
                variable.

            f: `Field`
                The parent field construct.

            mesh: `Mesh`
                The mesh description, as stored in
                ``self.read_vars['mesh']``.

            location: `str`
                The location of the cells in the mesh topology. One of
                ``'edge'``, ``'face'``, or ``'volume'``.

            aux: `AuxiliaryCoordinate`, optional
                An existing auxiliary coordinate construct that
                contains the cell coordinates, but has no bounds. By
                default a new auxiliary coordinate construct is
                created that has no coordinates.

        :Returns:

            `AuxiliaryCoordinate`
                The auxiliary coordinate construct, with bounds, for
                the UGRID cells.

        """
        if location not in mesh.ncdim:
            return aux

        g = self.read_vars

        properties = g["variable_attributes"][node_ncvar].copy()
        properties.pop("formula_terms", None)

        bounds = self.implementation.initialise_Bounds()
        if aux is None:
            aux = self.implementation.initialise_AuxiliaryCoordinate()
            self.implementation.set_properties(aux, properties)

        if not g["mask"]:
            self._set_default_FillValue(bounds, node_ncvar)

        connectivity_attr = f"{location}_node_connectivity"
        connectivity_ncvar = mesh.mesh_attributes[connectivity_attr]
        node_connectivity = self._create_data(
            connectivity_ncvar,
            uncompress_override=True,
            compression_index=True,
        )
        node_coordinates = self._create_data(
            node_ncvar, compression_index=True
        )
        start_index = g["variable_attributes"][connectivity_ncvar].get(
            "start_index", 0
        )
        cell_dimension = self._ugrid_cell_dimension(
            location, connectivity_ncvar, mesh
        )

        shape = node_connectivity.shape
        if cell_dimension == 1:
            shape = shape[::-1]

        # Create and set the bounds data
        array = self.implementation.initialise_BoundsFromNodesArray(
            node_connectivity=node_connectivity,
            shape=shape,
            node_coordinates=node_coordinates,
            start_index=start_index,
            cell_dimension=cell_dimension,
            copy=False,
        )
        bounds_data = self._create_Data(
            array,
            units=properties.get("units"),
            calendar=properties.get("calendar"),
            ncvar=node_ncvar,
        )
        self.implementation.set_data(bounds, bounds_data, copy=False)

        # Set the original file names
        self.implementation.set_original_filenames(
            bounds, g["variable_filename"][node_ncvar]
        )

        error = self.implementation.set_bounds(aux, bounds, copy=False)
        if error:
            logger.warning(f"WARNING: {error}")

        return aux

    def _ugrid_create_domain_topology(self, parent_ncvar, f, mesh, location):
        """Create a domain topology construct.

        .. versionadded:: (cfdm) UGRIDVER

        :Parameters:

            parent_ncvar: `str`
                The netCDF variable name of the parent field construct.

            f: `Field`
                The parent field construct.

            mesh: `Mesh`
                The mesh description, as stored in
                ``self.read_vars['mesh']``.

            location: `str`
                The location of the cells in the mesh topology. One of
                ``'node'``, ``'edge'``, ``'face'``, ``'volume'``.

        :Returns:

            `DomainTopology` or `None`
                The domain topology construct, or `None` if it could
                not be created.

        """
        attributes = mesh.mesh_attributes

        if location == "node":
            cell = "point"
            connectivity_attr = None
            for loc in ("edge", "face", "volume"):
                connectivity_attr = f"{loc}_node_connectivity"
                if connectivity_attr in attributes:
                    break
        else:
            cell = location
            connectivity_attr = f"{location}_node_connectivity"
            loc = location

        connectivity_ncvar = attributes.get(connectivity_attr)
        if connectivity_ncvar is None:
            # Can't create a domain topology construct without an
            # approrpriate connectivity attribute
            return

        if not self._ugrid_check_connectivity_variable(
            parent_ncvar,
            mesh.mesh_ncvar,
            connectivity_ncvar,
            connectivity_attr,
        ):
            return

        # Still here?

        # CF properties
        properties = self.read_vars["variable_attributes"][
            connectivity_ncvar
        ].copy()
        start_index = properties.pop("start_index", 0)
        cell_dimension = self._ugrid_cell_dimension(
            loc, connectivity_ncvar, mesh
        )

        # Create data
        if cell == "point":
            properties[
                "long_name"
            ] = "Maps every point to its connected points"
            indices, kwargs = self._create_netcdfarray(connectivity_ncvar)
            n_nodes = self.read_vars["internal_dimension_sizes"][
                mesh.ncdim[location]
            ]
            array = self.implementation.initialise_PointTopologyArray(
                shape=(n_nodes, nan),
                start_index=start_index,
                cell_dimension=cell_dimension,
                copy=False,
                **{connectivity_attr: indices},
            )
            data = self._create_Data(
                array,
                units=kwargs["units"],
                calendar=kwargs["calendar"],
                ncvar=connectivity_ncvar,
            )
        else:
            # Edge or face cells
            data = self._create_data(
                connectivity_ncvar, compression_index=True
            )
            if cell_dimension == 1:
                data = data.transpose()

        # Initialise the domain topology variable
        domain_topology = self.implementation.initialise_DomainTopology(
            cell=cell,
            properties=properties,
            data=data,
            copy=False,
        )

        # Set the netCDF variable name and the original file names
        self.implementation.nc_set_variable(
            domain_topology, connectivity_ncvar
        )
        self.implementation.set_original_filenames(
            domain_topology, self.read_vars["filename"]
        )

        index_set = mesh.index_set
        if index_set is not None:
            # Apply a location index set
            domain_topology = domain_topology[index_set]

        return domain_topology

    def _ugrid_create_cell_connectivities(
        self, parent_ncvar, f, mesh, location
    ):
        """Create a cell connectivity construct.

        Only "face_face_connectivty" is supported.

        .. versionadded:: (cfdm) UGRIDVER

        :Parameters:

            parent_ncvar: `str`
                The netCDF variable name of the parent field construct.

            f: `Field`
                The parent field construct.

            mesh: `Mesh`
                The mesh description, as stored in
                ``self.read_vars['mesh']``.

            location: `str`
                The location of the cells in the mesh topology. One of
                ``'node'``, ``'edge'``, ``'face'``, ``'volume'``.

        :Returns:

            `list`
                The cell connectivity constructs for this
                location. May be an empty list.

        """
        if location != "face":
            return []

        attributes = mesh.mesh_attributes
        connectivity_attr = f"{location}_{location}_connectivity"

        # Select the connectivity attribute that has the hightest
        # topology dimension
        connectivity_ncvar = attributes.get(connectivity_attr)
        if connectivity_ncvar is None:
            return []

        if not self._ugrid_check_connectivity_variable(
            parent_ncvar,
            mesh.mesh_ncvar,
            connectivity_ncvar,
            connectivity_attr,
        ):
            return []

        # CF properties
        properties = self.read_vars["variable_attributes"][connectivity_ncvar]
        start_index = properties.pop("start_index", 0)
        cell_dimension = self._ugrid_cell_dimension(
            location, connectivity_ncvar, mesh
        )

        # Connectivity data
        indices, kwargs = self._create_netcdfarray(connectivity_ncvar)

        array = self.implementation.initialise_CellConnectivityArray(
            cell_connectivity=indices,
            start_index=start_index,
            cell_dimension=cell_dimension,
            copy=False,
        )
        data = self._create_Data(
            array,
            units=kwargs["units"],
            calendar=kwargs["calendar"],
            ncvar=connectivity_ncvar,
        )

        # Initialise the cell connectivity construct
        connectivity = self.implementation.initialise_CellConnectivity(
            connectivity=self.ugrid_cell_connectivity_types()[
                connectivity_attr
            ],
            properties=properties,
            data=data,
            copy=False,
        )

        # Set the netCDF variable name and the original file names
        self.implementation.nc_set_variable(connectivity, connectivity_ncvar)
        self.implementation.set_original_filenames(
            connectivity, self.read_vars["filename"]
        )

        index_set = mesh.index_set
        if index_set is not None:
            # Apply a location index set
            connectivity = connectivity[index_set]

        return [connectivity]

    def _ugrid_cell_dimension(self, location, connectivity_ncvar, mesh):
        """The connectivity variable dimension that indexes the cells.

        .. versionadded:: (cfdm) UGRIDVER

        :Parameters:

            location: `str`
                The type of the connectivity variable, one of
                ``'node'``, ``'edge'``, ``'face'``, ``'volume'``.

            connectivity_ncvar: `str`
                The netCDF variable name of the UGRID connectivity
                variable.

            mesh: `Mesh`
                The UGRID mesh defintion.

        :Returns:

            `int`
                The position of the dimension of the connectivity
                variable that indexes the cells. Either ``0`` or
                ``1``.

        """
        ncdim = mesh.mesh_attributes.get(f"{location}_dimension")
        if ncdim is None:
            return 0

        try:
            cell_dim = self._ncdimensions(connectivity_ncvar).index(ncdim)
        except IndexError:
            cell_dim = 0

        return cell_dim

    def _ugrid_check_mesh_topology(self, mesh_ncvar):
        """Check a UGRID mesh topology variable.

        These checks are independent of any parent data variable.

        .. versionadded:: (cfdm) UGRIDVER

        :Parameters:

            mesh_ncvar: `str`
                The name of the netCDF mesh topology variable.

        :Returns:

            `bool`

        """
        g = self.read_vars

        ok = True

        if mesh_ncvar not in g["internal_variables"]:
            mesh_ncvar, message = self._missing_variable(
                mesh_ncvar, "Mesh topology variable"
            )
            self._add_message(
                mesh_ncvar,
                mesh_ncvar,
                message=message,
                attribute={f"{mesh_ncvar}:mesh": mesh_ncvar},
            )
            ok = False
            return ok

        attributes = g["variable_attributes"][mesh_ncvar]

        node_coordinates = attributes.get("node_coordinates")
        if node_coordinates is None:
            self._add_message(
                mesh_ncvar,
                mesh_ncvar,
                message=("node_coordinates attribute", "is missing"),
            )
            ok = False

        # Check coordinate variables
        for attr in (
            "node_coordinates",
            "edge_coordinates",
            "face_coordinates",
            "volume_coordinates",
        ):
            if attr not in attributes:
                continue

            coordinates = self._split_string_by_white_space(
                None, attributes[attr], variables=True
            )

            n_coordinates = len(coordinates)
            if attr == "node_coordinates":
                n_nodes = n_coordinates
            elif n_coordinates != n_nodes:
                self._add_message(
                    mesh_ncvar,
                    mesh_ncvar,
                    message=(
                        f"{attr} variable",
                        "contains wrong number of variables",
                    ),
                    attribute=attr,
                )
                ok = False

            dims = []
            for ncvar in coordinates:
                if ncvar not in g["internal_variables"]:
                    ncvar, message = self._missing_variable(
                        mesh_ncvar, f"{attr} variable"
                    )
                    self._add_message(
                        mesh_ncvar,
                        ncvar,
                        message=message,
                        attribute=attr,
                    )
                    ok = False
                else:
                    dims = []
                    ncdims = self._ncdimensions(ncvar)
                    if len(ncdims) != 1:
                        self._add_message(
                            mesh_ncvar,
                            ncvar,
                            message=(
                                f"{attr} variable",
                                "spans incorrect dimensions",
                            ),
                            attribute=attr,
                            dimensions=g["variable_dimensions"][ncvar],
                        )
                        ok = False

                    dims.extend(ncdims)

                if len(set(dims)) > 1:
                    self._add_message(
                        mesh_ncvar,
                        ncvar,
                        message=(
                            f"{attr} variables",
                            "span different dimensions",
                        ),
                        attribute=attr,
                    )
                    ok = False

        # Check connectivity variables
        topology_dimension = attributes.get("topology_dimension")
        if topology_dimension is None:
            self._add_message(
                mesh_ncvar,
                mesh_ncvar,
                message=("topology_dimension attribute", "is missing"),
            )
            ok = False
        elif topology_dimension == 2:
            ncvar = attributes.get("face_node_connectivity")
            if ncvar is None:
                self._add_message(
                    mesh_ncvar,
                    ncvar,
                    message=("face_node_connectivity attribute", "is missing"),
                    attribute="face_node_connectivity",
                )
                ok = False
            elif ncvar not in g["internal_variables"]:
                ncvar, message = self._missing_variable(
                    ncvar, "Face node connectivity variable"
                )
                self._add_message(
                    mesh_ncvar,
                    ncvar,
                    message=message,
                    attribute={f"{mesh_ncvar}:face_node_connectivity": ncvar},
                )
                ok = False
        elif topology_dimension == 1:
            ncvar = attributes.get("edge_node_connectivity")
            if ncvar is None:
                self._add_message(
                    mesh_ncvar,
                    mesh_ncvar,
                    message=("edge_node_connectivity attribute", "is missing"),
                    attribute="edge_node_connectivity",
                )
                ok = False
            elif ncvar not in g["internal_variables"]:
                ncvar, message = self._missing_variable(
                    ncvar, "Edge node connectivity variable"
                )
                self._add_message(
                    mesh_ncvar,
                    ncvar,
                    message=message,
                    attribute={f"{mesh_ncvar}:edge_node_connectivity": ncvar},
                )
                ok = False
        elif topology_dimension == 3:
            ncvar = attributes.get("volume_node_connectivity")
            if ncvar is None:
                self._add_message(
                    mesh_ncvar,
                    mesh_ncvar,
                    message=(
                        "volume_node_connectivity attribute",
                        "is missing",
                    ),
                    attribute="volume_node_connectivity",
                )
                ok = False
            elif ncvar not in g["internal_variables"]:
                ncvar, message = self._missing_variable(
                    ncvar, "Volume node connectivity variable"
                )
                self._add_message(
                    mesh_ncvar,
                    ncvar,
                    message=message,
                    attribute={
                        f"{mesh_ncvar}:volume_node_connectivity": ncvar
                    },
                )
                ok = False

            ncvar = attributes.get("volume_shape_type")
            if ncvar is None:
                self._add_message(
                    mesh_ncvar,
                    mesh_ncvar,
                    message=("volume_shape_type attribute", "is missing"),
                )
                ok = False
        else:
            self._add_message(
                mesh_ncvar,
                mesh_ncvar,
                message=("topology_dimension attribute", "has invalid value"),
                attribute={f"{ncvar}:topology_dimension": topology_dimension},
            )
            ok = False

        return ok

    def _ugrid_check_location_index_set(
        self,
        location_index_set_ncvar,
    ):
        """Check a UGRID location index set variable.

        These checks are independent of any parent data variable.

        .. versionadded:: (cfdm) UGRIDVER

        :Parameters:

            location_index_set_ncvar: `str`
                The name of the UGRID location index set netCDF
                variable.

        :Returns:

            `bool`

        """
        g = self.read_vars

        ok = True

        if location_index_set_ncvar not in g["internal_variables"]:
            location_index_set_ncvar, message = self._missing_variable(
                location_index_set_ncvar, "Location index set variable"
            )
            self._add_message(
                location_index_set_ncvar,
                location_index_set_ncvar,
                message=message,
            )
            ok = False
            return ok

        location_index_set_attributes = g["variable_attributes"][
            location_index_set_ncvar
        ]

        location = location_index_set_attributes.get("location")
        if location is None:
            self._add_message(
                location_index_set_ncvar,
                location_index_set_ncvar,
                message=("location attribute", "is missing"),
            )
            ok = False
        elif location not in ("node", "edge", "face", "volume"):
            self._add_message(
                location_index_set_ncvar,
                location_index_set_ncvar,
                message=("location attribute", "has invalid value"),
                attribute={f"{location_index_set_ncvar}:location": location},
            )
            ok = False

        mesh_ncvar = location_index_set_attributes.get("mesh")
        if mesh_ncvar is None:
            self._add_message(
                location_index_set_ncvar,
                location_index_set_ncvar,
                message=("mesh attribute", "is missing"),
            )
            ok = False
        elif mesh_ncvar not in g["internal_variables"]:
            mesh_ncvar, message = self._missing_variable(
                mesh_ncvar, "Mesh topology variable"
            )
            self._add_message(
                location_index_set_ncvar,
                mesh_ncvar,
                message=message,
                attribute={f"{location_index_set_ncvar}:mesh": mesh_ncvar},
                variable=location_index_set_ncvar,
            )
            ok = False
        elif mesh_ncvar not in g["mesh"]:
            self._add_message(
                location_index_set_ncvar,
                mesh_ncvar,
                message=("Mesh attribute", "is not a mesh topology variable"),
                attribute={f"{location_index_set_ncvar}:mesh": mesh_ncvar},
            )
            ok = False

        return ok

    def _ugrid_check_field_location_index_set(
        self,
        parent_ncvar,
        location_index_set_ncvar,
    ):
        """Check a UGRID location index set variable.

        These checks are in the context of a parent data variable.

        .. versionadded:: (cfdm) UGRIDVER

        :Parameters:

            parent_ncvar: `str`
                The netCDF variable name of the parent field
                construct.

            location_index_set_ncvar: `str`
                The name of the UGRID location index set netCDF
                variable.

        :Returns:

            `bool`

        """
        g = self.read_vars

        ok = True

        if "mesh" in g["variable_attributes"][parent_ncvar]:
            self._add_message(
                parent_ncvar,
                parent_ncvar,
                ("Location index set variable", "is referenced incorrectly"),
            )
            return False

        if location_index_set_ncvar not in g["internal_variables"]:
            location_index_set_ncvar, message = self._missing_variable(
                location_index_set_ncvar, "Location index set variable"
            )
            self._add_message(
                parent_ncvar,
                location_index_set_ncvar,
                message=message,
                attribute={
                    f"{parent_ncvar}:location_index_set": location_index_set_ncvar
                },
            )
            ok = False
            return ok

        location_index_set_attributes = g["variable_attributes"][
            location_index_set_ncvar
        ]

        location = location_index_set_attributes.get("location")
        if location is None:
            self._add_message(
                parent_ncvar,
                location_index_set_ncvar,
                message=("location attribute", "is missing"),
            )
            ok = False
        elif location not in ("node", "edge", "face", "volume"):
            self._add_message(
                parent_ncvar,
                location_index_set_ncvar,
                message=("location attribute", "has invalid value"),
                attribute={f"{location_index_set_ncvar}:location": location},
            )
            ok = False

        mesh_ncvar = location_index_set_attributes.get("mesh")
        if mesh_ncvar is None:
            self._add_message(
                parent_ncvar,
                location_index_set_ncvar,
                message=("mesh attribute", "is missing"),
            )
            ok = False
        elif mesh_ncvar not in g["internal_variables"]:
            mesh_ncvar, message = self._missing_variable(
                mesh_ncvar, "Mesh topology variable"
            )
            self._add_message(
                parent_ncvar,
                mesh_ncvar,
                message=message,
                attribute={f"{location_index_set_ncvar}:mesh": mesh_ncvar},
                variable=location_index_set_ncvar,
            )
            ok = False
        elif mesh_ncvar not in g["mesh"]:
            self._add_message(
                parent_ncvar,
                location_index_set_ncvar,
                message=("Mesh attribute", "is not a mesh topology variable"),
                attribute={f"{location_index_set_ncvar}:mesh": mesh_ncvar},
            )
            ok = False

        parent_ncdims = self._ncdimensions(parent_ncvar)
        lis_ncdims = self._ncdimensions(location_index_set_ncvar)
        if not set(lis_ncdims).issubset(parent_ncdims):
            self._add_message(
                parent_ncvar,
                location_index_set_ncvar,
                message=(
                    "Location index set variable",
                    "spans incorrect dimensions",
                ),
                attribute="location_index_set",
                dimensions=g["variable_dimensions"][location_index_set_ncvar],
            )
            ok = False

        self._include_component_report(parent_ncvar, location_index_set_ncvar)
        return ok

    def _ugrid_check_field_mesh(
        self,
        parent_ncvar,
        mesh_ncvar,
    ):
        """Check a UGRID mesh topology variable.

        These checks are in the context of a parent data variable.

        .. versionadded:: (cfdm) UGRIDVER

        :Parameters:

            parent_ncvar: `str`
                The netCDF variable name of the parent field
                construct.

        :Returns:

            `bool`

        """
        g = self.read_vars

        ok = True

        parent_attributes = g["variable_attributes"][parent_ncvar]
        if "location_index_set" in parent_attributes:
            self._add_message(
                parent_ncvar,
                parent_ncvar,
                ("Mesh topology variable", "is referenced incorrectly"),
            )
            return False

        if mesh_ncvar not in g["mesh"]:
            self._add_message(
                parent_ncvar,
                parent_ncvar,
                message=(
                    "mesh attribute",
                    "is not a mesh topology variable",
                ),
                attribute={f"{parent_ncvar}:mesh": mesh_ncvar},
            )
            return False

        location = parent_attributes.get("location")
        if location is None:
            self._add_message(
                parent_ncvar,
                parent_ncvar,
                message=("location attribute", "is missing"),
            )
            ok = False
        elif location not in ("node", "edge", "face", "volume"):
            self._add_message(
                parent_ncvar,
                parent_ncvar,
                message=("location attribute", "has invalid value"),
                attribute={f"{parent_ncvar}:location": location},
            )
            ok = False
        elif location not in g["mesh"][mesh_ncvar].domain_topologies:
            self._add_message(
                parent_ncvar,
                mesh_ncvar,
                message=(
                    "Couldn't create domain topology construct",
                    "from UGRID mesh topology variable",
                ),
                attribute={f"{parent_ncvar}:mesh": mesh_ncvar},
            )
            ok = False

        self._include_component_report(parent_ncvar, mesh_ncvar)
        return ok

    def _ugrid_check_connectivity_variable(
        self, parent_ncvar, mesh_ncvar, connectivity_ncvar, connectivity_attr
    ):
        """Check a UGRID connectivity variable.

        .. versionadded:: (cfdm) UGRIDVER

        :Parameters:

            parent_ncvar: `str`
                The netCDF variable name of the parent field
                construct.

            mesh_ncvar: `str`
                The netCDF variable name of the UGRID mesh topology
                variable.

            connectivity_ncvar: `str`
                The netCDF variable name of the UGRID connectivity
                variable.

            connectivity_attr: `str`
                The name of the UGRID connectivity attribute,
                e.g. ``'face_face_connectivity'``.

        :Returns:

            `bool`

        """
        g = self.read_vars

        ok = True
        if connectivity_ncvar is None:
            self._add_message(
                parent_ncvar,
                connectivity_ncvar,
                message=(f"{connectivity_attr} attribute", "is missing"),
                variable=mesh_ncvar,
            )
            ok = False
            return ok

        if connectivity_ncvar not in g["internal_variables"]:
            connectivity_ncvar, message = self._missing_variable(
                connectivity_ncvar, f"{connectivity_attr} variable"
            )
            self._add_message(
                parent_ncvar,
                connectivity_ncvar,
                message=message,
                attribute={
                    f"{mesh_ncvar}:{connectivity_attr}": connectivity_ncvar
                },
                variable=mesh_ncvar,
            )
            ok = False
            return ok

        parent_ncdims = self._ncdimensions(parent_ncvar)
        connectivity_ncdims = self._ncdimensions(connectivity_ncvar)[0]
        if not connectivity_ncdims[0] not in parent_ncdims:
            self._add_message(
                parent_ncvar,
                mesh_ncvar,
                message=(
                    f"UGRID {connectivity_attr} variable",
                    "spans incorrect dimensions",
                ),
                attribute={
                    f"mesh:{connectivity_attr}": f"{connectivity_ncvar}"
                },
                dimensions=g["variable_dimensions"][connectivity_ncvar],
            )
            ok = False

        return ok
