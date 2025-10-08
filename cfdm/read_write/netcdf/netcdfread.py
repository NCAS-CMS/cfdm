import logging
import operator
import re
import struct
import subprocess
import tempfile
from ast import literal_eval
from copy import deepcopy
from dataclasses import dataclass, field
from functools import reduce
from math import log, nan, prod
from numbers import Integral
from os.path import isdir, isfile, join
from typing import Any
from uuid import uuid4

import netCDF4
import numpy as np
from dask.array.core import normalize_chunks
from dask.base import tokenize
from packaging.version import Version
from s3fs import S3FileSystem
from uritools import urisplit

from ...data.netcdfindexer import netcdf_indexer
from ...decorators import _manage_log_level_via_verbosity
from ...functions import abspath, is_log_level_debug, is_log_level_detail
from .. import IORead
from ..exceptions import DatasetTypeError, ReadError
from .constants import (
    CF_QUANTIZATION_PARAMETERS,
    NETCDF_MAGIC_NUMBERS,
    NETCDF_QUANTIZATION_PARAMETERS,
)
from .flatten import netcdf_flatten
from .flatten.config import (
    flattener_attribute_map,
    flattener_dimension_map,
    flattener_separator,
    flattener_variable_map,
)
from .zarr import ZarrDimension

logger = logging.getLogger(__name__)

_cached_temporary_files = {}


@dataclass()
class Mesh:
    """A UGRID mesh defintion.

    .. versionadded:: (cfdm) 1.11.0.0

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
        "Quantization variable": 211,
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

        A coordinate reference canonical name is either the value of the
        grid_mapping_name attribute of a grid mapping variable (e.g.
        'lambert_azimuthal_equal_area'), or the standard name of a
        vertical coordinate variable with a formula_terms attribute
        (e.g. 'ocean_sigma_coordinate').

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

        .. versionadded:: (cfdm) 1.11.0.0

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

        .. versionadded:: (cfdm) 1.11.0.0

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
        g = self.read_vars

        # Close temporary flattened files
        for flat_file in g["flat_files"]:
            flat_file.close()

        if g["file_opened_with"] == "zarr":
            # zarr
            return

        # netCDF4, h5netcdf
        for nc in g["datasets"]:
            nc.close()

        # Close the original grouped file (v1.8.8.1)
        if "nc_grouped" in g:
            g["nc_grouped"].close()

        # Close s3fs.File objects
        for f in g["s3fs_File_objects"]:
            f.close()

    def file_open(self, dataset, flatten=True, verbose=None):
        """Open the netCDF file for reading.

        If the file has hierarchical groups then a flattened version
        of it is returned, and the original grouped file remains open.

        .. versionadded:: (cfdm) 1.7.0

        :Paramters:

            dataset: `str`
                The name of the dataset to be opened.

            flatten: `bool`, optional
                If True (the default) then flatten a grouped file.
                Ignored if the file has no groups.

                .. versionadded:: (cfdm) 1.8.6

        :Returns:

                An object representing the opened dataset.

        **Examples**

        >>> r.file_open('file.nc')

        """
        g = self.read_vars

        netcdf_backend = g["netcdf_backend"]

        if g["d_type"] == "CDL":
            # --------------------------------------------------------
            # Convert a CDL file to a local netCDF4 file
            # --------------------------------------------------------
            cdl_filename = dataset
            dataset = self.cdl_to_netcdf(dataset)
            g["dataset"] = dataset
        else:
            cdl_filename = None

        g["cdl_filename"] = cdl_filename

        u = urisplit(dataset)
        storage_options = self._get_storage_options(dataset, u)

        if u.scheme == "s3":
            # --------------------------------------------------------
            # A file in an S3 object store
            # --------------------------------------------------------

            # Create an openable S3 file object
            fs_key = tokenize(("s3", storage_options))
            file_systems = g["file_systems"]
            file_system = file_systems.get(fs_key)
            if file_system is None:
                # An S3 file system with these options does not exist,
                # so create one.
                file_system = S3FileSystem(**storage_options)
                file_systems[fs_key] = file_system

            # Reset 'dataset' to an s3fs.File object that can be
            # passed to the netCDF backend
            dataset = file_system.open(u.path[1:], "rb")
            g["s3fs_File_objects"].append(dataset)

            if is_log_level_detail(logger):
                logger.detail(
                    f"    S3: s3fs.S3FileSystem options: {storage_options}\n"
                )  # pragma: no cover

        # Map backend names to file-open functions
        file_open_function = {
            "h5netcdf": self._open_h5netcdf,
            "netCDF4": self._open_netCDF4,
            "zarr": self._open_zarr,
        }

        # Loop around the netCDF backends until we successfully open
        # the file
        nc = None
        errors = []
        for backend in netcdf_backend:
            try:
                nc = file_open_function[backend](dataset)
            except KeyError:
                errors.append(f"{backend}: Unknown netCDF backend name")
            except Exception as error:
                errors.append(
                    f"{backend}:\n{error.__class__.__name__}: {error}"
                )
            else:
                break

        if nc is None:
            if cdl_filename is not None:
                dataset = f"{dataset} (created from CDL file {cdl_filename})"

            error = "\n\n".join(errors)
            raise DatasetTypeError(
                f"Can't interpret {dataset} as a netCDF dataset"
                f"with any of the netCDF backends {netcdf_backend!r}:\n\n"
                f"{error}"
            )

        # ------------------------------------------------------------
        # If the file has a group structure then flatten it (CF>=1.8)
        # ------------------------------------------------------------
        if flatten and self._dataset_has_groups(nc):
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
            netcdf_flatten(nc, flat_nc, strict=False, omit_data=True)

            # Store the original grouped file. This is primarily
            # because the unlimited dimensions in the flattened
            # dataset have size 0, since it contains no
            # data. (v1.8.8.1)
            g["nc_grouped"] = nc

            nc = flat_nc

            g["has_groups"] = True
            g["flat_files"].append(flat_file)
            g["nc_opened_with"] = "netCDF4"
        else:
            g["nc_opened_with"] = g["file_opened_with"]

        g["nc"] = nc
        return nc

    def _open_netCDF4(self, filename):
        """Return an open `netCDF4.Dataset`.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            filename: `str`
                The file to open.

        :Returns:

            `netCDF4.Dataset`

        """
        nc = netCDF4.Dataset(filename, "r")
        self.read_vars["file_opened_with"] = "netCDF4"
        return nc

    def _open_h5netcdf(self, filename):
        """Return an open `h5netcdf.File`.

        Uses values of the ``rdcc_nbytes``, ``rdcc_w0``, and
        ``rdcc_nslots`` parameters to `h5netcdf.File` that correspond
        to the default values of the `netCDF4.set_chunk_cache`
        parameters ``size``, ``nelems``, and ``preemption``,
        respectively.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            filename: `str`
                The file to open.

        :Returns:

            `h5netcdf.File`

        """
        import h5netcdf

        nc = h5netcdf.File(
            filename,
            "r",
            decode_vlen_strings=True,
            rdcc_nbytes=16777216,
            rdcc_w0=0.75,
            rdcc_nslots=4133,
        )
        self.read_vars["file_opened_with"] = "h5netcdf"
        return nc

    def _open_zarr(self, dataset):
        """Return an open `zarr.Group`.

        .. versionadded:: (cfdm) 1.12.2.0

        :Parameters:

            dataset: `str`
                The dataset to open.

        :Returns:

            `zarr.Group`

        """
        try:
            import zarr
        except ModuleNotFoundError as error:
            error.msg += ". Install the 'zarr' package to read Zarr datasets"
            raise

        nc = zarr.open(dataset)
        self.read_vars["file_opened_with"] = "zarr"
        return nc

    def cdl_to_netcdf(self, filename):
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

        ncgen_command = ["ncgen", "-knc4", "-o", tmpfile, filename]

        if self.read_vars["debug"]:
            logger.debug(
                f"Converting CDL file {filename} to netCDF file {tmpfile} "
                f"with `{' '.join(ncgen_command)}`"
            )  # pragma: no cover

        try:
            subprocess.run(ncgen_command, check=True)
        except subprocess.CalledProcessError as error:
            msg = str(error)
            if msg.startswith(
                "Command '['ncgen', '-knc4', '-o'"
            ) and msg.endswith("returned non-zero exit status 1."):
                raise RuntimeError(
                    f"The CDL file {filename} cannot be converted to netCDF "
                    f"with `{' '.join(ncgen_command)}`. ncgen output:\n\n"
                    f"{msg}"
                )
            else:
                raise

        # Need to cache the TemporaryFile object so that it doesn't get
        # deleted too soon
        _cached_temporary_files[tmpfile] = x

        return tmpfile

    @classmethod
    def string_to_cdl(cls, cdl_string):
        """Create a temporary text CDL file from a CDL string.

        .. versionadded:: (cfdm) 1.12.0.0

        :Parameters:

            cdl_string: `str`
                The CDL string.

        :Returns:

            `str`
                The name of the new CDL file.

        """
        x = tempfile.NamedTemporaryFile(
            mode="w",
            dir=tempfile.gettempdir(),
            prefix="cfdm_",
            suffix=".cdl",
        )
        tmpfile = x.name

        with open(tmpfile, "w") as f:
            f.write(cdl_string)

        # Need to cache the TemporaryFile object so that it doesn't
        # get deleted too soon
        _cached_temporary_files[tmpfile] = x

        return tmpfile

    @classmethod
    def dataset_type(cls, dataset, allowed_dataset_types):
        """Return type of the dataset.

        The dataset type is determined by solely by inspecting the
        dataset's contents, and any dataset suffix is
        ignored.

        However, dataset names that are non-local URIs (such as those
        starting ``https:`` or ``s3:``) are assumed, without checking,
        to be netCDF files, or Zarr datasets if
        *allowed_dataset_types*` is equivalent to ``['Zarr']``.

        :Parameters:

            dataset: `str`
                The name of the dataset.

            allowed_dataset_types: `None` or sequence of `str`
                The allowed dataset types.

        :Returns:

            `str` or `None`
                The dataset type:

                * ``'netCDF'`` for a netCDF-3 or netCDF-4 file,
                * ``'CDL'`` for a text CDL file,
                * ``'Zarr'`` for a Zarr dataset directory,
                * `None` for anything else.

        """
        # Assume that non-local URIs are netCDF or zarr
        u = urisplit(dataset)
        if u.scheme not in (None, "file"):
            if (
                allowed_dataset_types
                and len(allowed_dataset_types) == 1
                and "Zarr" in allowed_dataset_types
            ):
                # Assume that a non-local URI is zarr if
                # 'allowed_dataset_types' is ('Zarr',)
                return "Zarr"

            # Assume that a non-local URI is netCDF if it's not Zarr
            return "netCDF"

        # Still here? Then check for a local Zarr dataset
        dataset = abspath(dataset, uri=False)
        if isdir(dataset) and cls.is_zarr(dataset):
            return "Zarr"

        # Still here? Then check for a local netCDF or CDL file
        try:
            # Read the first 4 bytes from the file
            fh = open(dataset, "rb")
            magic_number = struct.unpack("=L", fh.read(4))[0]
        except FileNotFoundError:
            raise
        except Exception:
            # Can't read 4 bytes from the file, so it can't be netCDF
            # or CDL.
            d_type = None
        else:
            # Is it a netCDF-3 or netCDF-4 binary file?
            if magic_number in NETCDF_MAGIC_NUMBERS:
                d_type = "netCDF"
            else:
                # Is it a CDL text file?
                fh.seek(0)
                try:
                    line = fh.readline().decode("utf-8")
                except Exception:
                    d_type = None
                else:
                    netcdf = line.startswith("netcdf ")
                    if not netcdf:
                        # Match comment and blank lines at the top of
                        # the file
                        while re.match(r"^\s*//|^\s*$", line):
                            line = fh.readline().decode("utf-8")
                            if not line:
                                break

                        netcdf = line.startswith("netcdf ")

                    if netcdf:
                        d_type = "CDL"
                    else:
                        d_type = None

        try:
            fh.close()
        except Exception:
            pass

        return d_type

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
        dataset,
        extra=None,
        default_version=None,
        external=None,
        extra_read_vars=None,
        _scan_only=False,
        verbose=None,
        mask=True,
        unpack=True,
        warnings=True,
        warn_valid=False,
        domain=False,
        storage_options=None,
        _file_systems=None,
        netcdf_backend=None,
        cache=True,
        dask_chunks="storage-aligned",
        store_dataset_chunks=True,
        cfa=None,
        cfa_write=None,
        to_memory=None,
        squeeze=False,
        unsqueeze=False,
        dataset_type=None,
        cdl_string=False,
        ignore_unknown_type=False,
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

            dataset: `str`
                The name of the datasetset to be read. See `cfdm.read`
                for details.

                .. versionadded:: (cfdm) 1.7.0

            extra: sequence of `str`, optional
                See `cfdm.read` for details

                .. versionadded:: (cfdm) 1.7.0

            warnings: `bool`, optional
                See `cfdm.read` for details

            mask: `bool`, optional
                See `cfdm.read` for details

                .. versionadded:: (cfdm) 1.8.2

            unpack: `bool`, optional
                See `cfdm.read` for details

                .. versionadded:: (cfdm) 1.11.2.0

            warn_valid: `bool`, optional
                See `cfdm.read` for details

                .. versionadded:: (cfdm) 1.8.3

            domain: `bool`, optional
                See `cfdm.read` for details

                .. versionadded:: (cfdm) 1.9.0.0

            storage_options: `bool`, optional
                See `cfdm.read` for details.

                .. versionadded:: (cfdm) 1.11.2.0

            netcdf_backend: `None` or `str`, optional
                See `cfdm.read` for details.

                .. versionadded:: (cfdm) 1.11.2.0

            cache: `bool`, optional
                Control array element caching. See `cfdm.read` for
                details.

                .. versionadded:: (cfdm) 1.11.2.0

            dask_chunks: `str`, `int`, `None`, or `dict`, optional
                Specify the `dask` chunking of dimensions for data in
                the input files. See `cfdm.read` for details.

                .. versionadded:: (cfdm) 1.11.2.0

            store_dataset_chunks: `bool`, optional
                 Store the dataset chunking strategy. See `cfdm.read`
                 for details.

                .. versionadded:: (cfdm) 1.12.0.0

            cfa: `dict`, optional
                Configure the reading of CF-netCDF aggregation files.
                See `cfdm.read` for details.

                .. versionadded:: (cfdm) 1.12.0.0

            cfa_write: sequence of `str`, optional
                Configure the reading of CF-netCDF aggregation files.
                See `cfdm.read` for details.

                .. versionadded:: (cfdm) 1.12.0.0

            to_memory: (sequence) of `str`, optional
                Whether or not to bring data arrays into memory.  See
                `cfdm.read` for details.

                .. versionadded:: (cfdm) 1.12.0.0

            squeeze: `bool`, optional
                Whether or not to remove all size 1 axes from field
                construct data arrays. See `cfdm.read` for details.

                .. versionadded:: (cfdm) 1.12.0.0

            unsqueeze: `bool`, optional
                Whether or not to ensure that all size 1 axes are
                spanned by field construct data arrays. See
                `cfdm.read` for details.

                .. versionadded:: (cfdm) 1.12.0.0

            dataset_type: `None` or (sequence of) `str`, optional
                Only read files of the given type(s). See `cfdm.read`
                for details.

                .. versionadded:: (cfdm) 1.12.0.0

            ignore_unknown_type: `bool`, optional
                If True then ignore any file which does not have one
                of the valid types specified by the *file_type*
                parameter. See `cfdm.read` for details.

                .. versionadded:: (cfdm) 1.11.2.0

            _file_systems: `dict`, optional
                Provide any already-open S3 file systems.

                .. versionadded:: (cfdm) 1.11.2.0

        :Returns:

            `list`
                The field or domain constructs in the file.

        """
        debug = is_log_level_debug(logger)

        # ------------------------------------------------------------
        # Parse the 'dataset_type' keyword parameter
        # ------------------------------------------------------------
        valid_dataset_types = ("netCDF", "CDL", "Zarr")
        if dataset_type is not None:
            if isinstance(dataset_type, str):
                dataset_type = (dataset_type,)

            dataset_type = set(dataset_type)
            if not dataset_type.issubset(valid_dataset_types):
                raise ValueError(
                    "Invalid dataset type given by the 'dataset_type' "
                    f"parameter. Got {tuple(dataset_type)}, expected a "
                    f"subset of {valid_dataset_types!r}"
                )

            if not dataset_type:
                # Return an empty list if there are no valid dataset
                # types
                return []

        # ------------------------------------------------------------
        # Convert a CDL string to a temporary text CDL file
        # ------------------------------------------------------------
        if cdl_string:
            if dataset_type is not None and "CDL" not in dataset_type:
                raise ValueError(
                    "When cdl_string=True, can't set "
                    f"dataset_type={dataset_type!r}"
                )

            dataset = self.string_to_cdl(dataset)

        # ------------------------------------------------------------
        # Parse the 'dataset' keyword parameter
        # ------------------------------------------------------------
        try:
            dataset = abspath(dataset, uri=False)
        except ValueError:
            dataset = abspath(dataset)

        # ------------------------------------------------------------
        # Check the file type, raising an exception if the type is not
        # valid.
        #
        # Note that the `dataset_type` method is much faster than the
        # `file_open` method at returning for unrecognised types.
        # ------------------------------------------------------------
        d_type = self.dataset_type(dataset, dataset_type)
        if not d_type:
            # Can't interpret the dataset as a recognised type, so
            # either raise an exception or return an empty list.
            if dataset_type is None:
                raise DatasetTypeError(
                    f"Can't interpret {dataset} as a dataset of one of the "
                    f"valid types: {valid_dataset_types!r}"
                )

            return []

        # Can interpret the dataset as a recognised type, but return
        # an empty list if that type has been exlcuded.
        if dataset_type is not None and d_type not in dataset_type:
            return []

        # ------------------------------------------------------------
        # Parse the 'netcdf_backend' keyword parameter
        # ------------------------------------------------------------
        if d_type == "Zarr":
            netcdf_backend = ("zarr",)
        elif netcdf_backend is None:
            # By default, try netCDF backends in this order:
            netcdf_backend = ("h5netcdf", "netCDF4")
        else:
            valid_netcdf_backends = ("h5netcdf", "netCDF4", "zarr")
            if isinstance(netcdf_backend, str):
                netcdf_backend = (netcdf_backend,)

            if not set(netcdf_backend).issubset(valid_netcdf_backends):
                raise ValueError(
                    "Invalid netCDF backend given by the 'netcdf_backend' "
                    f"parameter. Got {netcdf_backend}, expected a subset of "
                    f"{valid_netcdf_backends!r}"
                )

        # ------------------------------------------------------------
        # Parse the 'external' keyword parameter
        # ------------------------------------------------------------
        if external:
            if isinstance(external, str):
                external = (external,)

            external = set(external)
        else:
            external = set()

        # ------------------------------------------------------------
        # Parse 'extra' keyword parameter
        # ------------------------------------------------------------
        get_constructs = {
            "auxiliary_coordinate": self.implementation.get_auxiliary_coordinates,
            "cell_measure": self.implementation.get_cell_measures,
            "dimension_coordinate": self.implementation.get_dimension_coordinates,
            "domain_ancillary": self.implementation.get_domain_ancillaries,
            "field_ancillary": self.implementation.get_field_ancillaries,
        }

        if extra:
            if isinstance(extra, str):
                extra = (extra,)

            for f in extra:
                if f not in get_constructs:
                    raise ValueError(
                        f"Can't read: Bad parameter value: extra={extra!r}"
                    )

            extra = set(extra)
        else:
            extra = set()

        # ------------------------------------------------------------
        # Parse 'dask_chunks' keyword parameter
        # ------------------------------------------------------------
        if dask_chunks is not None and not isinstance(
            dask_chunks, (str, Integral, dict)
        ):
            raise ValueError(
                "The 'dask_chunks' keyword must be of type str, int, None or "
                f"dict. Got: {dask_chunks!r}"
            )

        # ------------------------------------------------------------
        # Parse the 'cfa' keyword parameter
        # ------------------------------------------------------------
        if cfa is None:
            cfa = {}
        else:
            cfa = cfa.copy()
            keys = ("replace_directory",)
            if not set(cfa).issubset(keys):
                raise ValueError(
                    "Invalid dictionary key to the 'cfa' parameter."
                    f"Valid keys are {keys}. Got: {cfa}"
                )

            if not isinstance(cfa.get("replace_directory", {}), dict):
                raise ValueError(
                    "The 'replace_directory' key of the 'cfa' parameter "
                    "must have a dictionary value. "
                    f"Got: {cfa['replace_directory']!r}"
                )

        # ------------------------------------------------------------
        # Parse the 'cfa_write' keyword parameter
        # ------------------------------------------------------------
        if cfa_write:
            if isinstance(cfa_write, str):
                cfa_write = (cfa_write,)
            else:
                cfa_write = tuple(cfa_write)
        else:
            cfa_write = ()

        # ------------------------------------------------------------
        # Parse the 'squeeze' and 'unsqueeze' keyword parameters
        # ------------------------------------------------------------
        if squeeze and unsqueeze:
            raise ValueError(
                "'squeeze' and 'unsqueeze' parameters can not both be True"
            )

        # ------------------------------------------------------------
        # Parse the 'to_memory' keyword parameter
        # ------------------------------------------------------------
        if to_memory:
            if isinstance(to_memory, str):
                to_memory = (to_memory,)

            if "metadata" in to_memory:
                to_memory = tuple(to_memory) + (
                    "field_ancillary",
                    "domain_ancillary",
                    "dimension_coordinate",
                    "auxiliary_coordinate",
                    "cell_measure",
                    "domain_topology",
                    "cell_connectivity",
                )
                to_memory = set(to_memory)
                to_memory.remove("metadata")
        else:
            to_memory = ()

        # ------------------------------------------------------------
        # Parse the 'storage_options' keyword parameter
        # ------------------------------------------------------------
        if storage_options is None:
            storage_options = {}

        # ------------------------------------------------------------
        # Parse the '_file_systems' keyword parameter
        # ------------------------------------------------------------
        if _file_systems is None:
            _file_systems = {}

        # ------------------------------------------------------------
        # Parse the 'cdl_string' keyword parameter
        # ------------------------------------------------------------
        if cdl_string and dataset_type and "CDL" not in dataset_type:
            raise ValueError(
                f"When cdl_string=True, can't set dataset_type={dataset_type}"
            )

        # ------------------------------------------------------------
        # Initialise netCDF read parameters
        # ------------------------------------------------------------
        self.read_vars = {
            # --------------------------------------------------------
            # Dataset
            # --------------------------------------------------------
            "dataset": dataset,
            "d_type": d_type,
            "cdl_string": bool(cdl_string),
            "ignore_unknown_type": bool(ignore_unknown_type),
            # --------------------------------------------------------
            # Verbosity
            # --------------------------------------------------------
            "debug": debug,
            #
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
            "external_files": external,
            "external_variables": set(),
            # External variables that are actually referenced from
            # within the parent file
            "referenced_external_variables": set(),
            # --------------------------------------------------------
            # Create extra, independent fields from netCDF variables
            # that correspond to particular types metadata constructs
            # --------------------------------------------------------
            "extra": extra,
            "get_constructs": get_constructs,
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
            # Auto mask and unpack?
            "mask": bool(mask),
            "unpack": bool(unpack),
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
            # NetCDF backend
            # --------------------------------------------------------
            "netcdf_backend": netcdf_backend,
            # --------------------------------------------------------
            # S3
            # --------------------------------------------------------
            # Input file system storage options
            "storage_options": storage_options,
            # File system storage options for each file
            "file_system_storage_options": {},
            # Cached s3fs.S3FileSystem objects
            "file_systems": _file_systems,
            # Cache of open s3fs.File objects
            "s3fs_File_objects": [],
            # --------------------------------------------------------
            # Array element caching
            # --------------------------------------------------------
            "cache": bool(cache),
            # --------------------------------------------------------
            # Dask
            # --------------------------------------------------------
            "dask_chunks": dask_chunks,
            # --------------------------------------------------------
            # Aggregation
            # --------------------------------------------------------
            "parsed_aggregated_data": {},
            # fragment_array_variables as numpy arrays
            "fragment_array_variables": {},
            # Aggregation configuration overrides
            "cfa": cfa,
            # Dask chunking of aggregated data for selected constructs
            "cfa_write": cfa_write,
            # --------------------------------------------------------
            # Whether or not to store the dataset chunking strategy
            # --------------------------------------------------------
            "store_dataset_chunks": bool(store_dataset_chunks),
            # --------------------------------------------------------
            # Constructs to read into memory
            # --------------------------------------------------------
            "to_memory": to_memory,
            # --------------------------------------------------------
            # Squeeze/unsqueeze fields
            # --------------------------------------------------------
            "squeeze": bool(squeeze),
            "unsqueeze": bool(unsqueeze),
            # --------------------------------------------------------
            # Quantization
            # --------------------------------------------------------
            # Maps quantization variable names to Quantization objects
            "quantization_variable": {},
            # Maps variable names to their quantization container
            # variable names
            "quantization": {},
            # Cached data elements, keyed by variable names.
            # --------------------------------------------------------
            "cached_data_elements": {},
        }

        g = self.read_vars

        # Set versions
        for version in ("1.6", "1.7", "1.8", "1.9", "1.10", "1.11", "1.12"):
            g["version"][version] = Version(version)

        # ------------------------------------------------------------
        # Add custom read vars
        # ------------------------------------------------------------
        if extra_read_vars:
            g.update(deepcopy(extra_read_vars))

        # ------------------------------------------------------------
        # Open the netCDF file to be read
        # ------------------------------------------------------------
        try:
            nc = self.file_open(dataset, flatten=True, verbose=None)
        except DatasetTypeError:
            if not g["ignore_unknown_type"]:
                raise

            if debug:
                logger.debug(
                    f"Ignoring {dataset}: Can't interpret as a "
                    "netCDF dataset"
                )  # pragma: no cover

                return []

        logger.info(
            f"Reading netCDF file: {g['dataset']}\n"
        )  # pragma: no cover
        if debug:
            logger.debug(
                f"    Input netCDF dataset:\n        {nc}\n"
            )  # pragma: no cover

        # ----------------------------------------------------------------
        # Put the file's global attributes into the global
        # 'global_attributes' dictionary
        # ----------------------------------------------------------------
        global_attributes = {}
        for attr, value in self._file_global_attributes(nc).items():
            attr = str(attr)
            if isinstance(value, bytes):
                value = value.decode(errors="ignore")

            global_attributes[attr] = value

        g["global_attributes"] = global_attributes
        if debug:
            logger.debug(
                f"    Global attributes:\n        {g['global_attributes']}"
            )  # pragma: no cover

        # ------------------------------------------------------------
        # Find the CF version for the file
        # ------------------------------------------------------------
        Conventions = g["global_attributes"].get("Conventions", "")

        # If the string contains any commas, it is assumed to be a
        # comma-separated list.
        all_conventions = re.split(r",\s*", Conventions)
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
        for vn in ("1.6", "1.7", "1.8", "1.9", "1.10", "1.11", "1.12"):
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
        variable_datasetname = {}
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
                nc, flattener_variable_map, None
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
                nc, flattener_dimension_map, None
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
                nc, flattener_attribute_map, None
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
                        ] = self._file_global_attribute(nc, flat_attr)

            # Remove flattener attributes from the global attributes
            for attr in (
                flattener_variable_map,
                flattener_dimension_map,
                flattener_attribute_map,
            ):
                g["global_attributes"].pop(attr, None)

        for ncvar in self._file_variables(nc):
            ncvar_basename = ncvar
            groups = ()
            group_attributes = {}

            variable = self._file_variable(nc, ncvar)

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
                        rf"^{flattener_separator.join(groups)}{flattener_separator}",
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
                    # Remove the leading / (slash) from the absolute
                    # netCDF variable path
                    ncvar = ncvar[1:]
                    flattener_variables[ncvar] = ncvar

                variable_grouped_dataset[ncvar] = g["nc_grouped"]

            variable_attributes[ncvar] = {}
            for attr, value in self._file_variable_attributes(
                variable
            ).items():
                attr = str(attr)
                if isinstance(value, bytes):
                    value = value.decode(errors="ignore")

                variable_attributes[ncvar][attr] = value

            variable_dimensions[ncvar] = tuple(
                self._file_variable_dimensions(variable)
            )
            variable_dataset[ncvar] = nc
            variable_datasetname[ncvar] = g["dataset"]
            variables[ncvar] = variable

            variable_basename[ncvar] = ncvar_basename
            variable_groups[ncvar] = groups
            variable_group_attributes[ncvar] = group_attributes

        # Populate dimensions_groups and dimension_basename
        # dictionaries
        for ncdim in self._file_dimensions(nc):
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
                        r"^{flattener_separator.join(groups)}{flattener_separator}",
                        "",
                        ncdim_flat,
                    )

            dimension_groups[ncdim] = groups
            dimension_basename[ncdim] = ncdim_basename

            dimension_isunlimited[ncdim] = self._file_dimension_isunlimited(
                nc, ncdim_org
            )

        if has_groups:
            variable_dimensions = {
                name: tuple([flattener_dimensions[ncdim] for ncdim in value])
                for name, value in variable_dimensions.items()
            }

        if debug:
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
        g["variable_datasetname"] = variable_datasetname

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
        for name, dimension in self._file_dimensions(nc).items():
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

        if debug:
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
        # Aggregation variables (CF>=1.12)
        # ------------------------------------------------------------
        if g["CF>=1.12"]:
            for ncvar, attributes in variable_attributes.items():
                aggregated_dimensions = attributes.get("aggregated_dimensions")
                if aggregated_dimensions is None:
                    # This is not an aggregated variable
                    continue

                # Set the aggregated variable's dimensions as its
                # aggregated dimensions
                ncdimensions = aggregated_dimensions.split()
                variable_dimensions[ncvar] = tuple(map(str, ncdimensions))

                # Parse the fragment array variables
                self._cfa_parse_aggregated_data(
                    ncvar, attributes.get("aggregated_data")
                )

            # Do not create fields/domains from fragment array
            # variables
            g["do_not_create_field"].update(g["fragment_array_variables"])

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

        if debug:
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

                if "location_index_set" in attributes:
                    # This data variable has a domain defined by a
                    # location_index_set
                    self._ugrid_parse_location_index_set(attributes)

            if debug:
                logger.debug(f"    UGRID meshes:\n       {g['mesh']}")

        # ------------------------------------------------------------
        # Identify and parse all quantization container variables
        # (CF>=1.12)
        # ------------------------------------------------------------
        if g["CF>=1.12"]:
            for ncvar, attributes in variable_attributes.items():
                if "quantization" not in attributes:
                    # This data variable does not have a quantization
                    # container
                    continue

                quantization_ncvar = self._parse_quantization(
                    ncvar, variable_attributes
                )

                if not quantization_ncvar:
                    # The quantization container has already been
                    # parsed, or a sufficiently compliant quantization
                    # container could not be found.
                    continue

                # Do not attempt to create a field or domain construct
                # from a quantization container variable
                g["do_not_create_field"].add(quantization_ncvar)

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

        if debug:
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
        # Squeeze/unsqueeze size 1 axes in field constructs
        # ------------------------------------------------------------
        if not g["domain"]:
            if g["unsqueeze"]:
                for f in out:
                    self.implementation.unsqueeze(f, inplace=True)
            elif g["squeeze"]:
                for f in out:
                    self.implementation.squeeze(f, inplace=True)

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
            "variable_datasetname",
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

            # Note: We pass in the s3 file system (if any) of the
            #       parent file in case we can resuse it for the
            #       external file
            external_read_vars = self.read(
                external_file,
                _scan_only=True,
                _file_systems=read_vars["file_systems"],
                verbose=verbose,
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
        debug = g["debug"]

        profile_dimension = g["compression"][sample_dimension][
            "ragged_contiguous"
        ]["profile_dimension"]

        if debug:
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
        try:
            element_dimension_2_size = int(
                self.implementation.get_data_maximum(elements_per_profile)
            )
        except np.ma.MaskError:
            raise ReadError(
                "Can't create an indexed contiguous ragged array when the "
                "CF-netCDF count variable in "
                f"{g['d_type']} file "
                f"{g.get('cdl_filename', g['dataset'])!r} "
                "contains missing data"
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

        if debug:
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
            size = self._file_dimension_size(g["nc"], node_dimension)
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
            self.implementation.set_original_filenames(index, g["dataset"])

            instance_index = 0
            i = 0
            for cell_no in range(
                self.implementation.get_data_size(nodes_per_geometry)
            ):
                try:
                    n_nodes_in_this_cell = int(
                        self.implementation.get_array(
                            nodes_per_geometry_data[cell_no]
                        )[0]
                    )
                except np.ma.MaskError:
                    raise ReadError(
                        "Can't create geometry cells when the CF-netCDF "
                        f"node count variable {node_count!r} in "
                        f"{g['d_type']} file "
                        f"{g.get('cdl_filename', g['dataset'])!r} "
                        "contains missing data"
                    )

                # Initialise partial_node_count, a running count of
                # how many nodes there are in this geometry
                n_nodes = 0

                for k in range(i, total_number_of_parts):
                    index.data[k] = instance_index
                    try:
                        n_nodes += int(
                            self.implementation.get_array(parts_data[k])[0]
                        )
                    except np.ma.MaskError:
                        raise ReadError(
                            "Can't create geometry cells when the CF-netCDF "
                            f"part node count variable {part_node_count!r} in "
                            f"{g['d_type']} file "
                            f"{g.get('cdl_filename', g['dataset'])!r} "
                            "contains missing data"
                        )

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

    def _parse_quantization(self, parent_ncvar, attributes):
        """Parse a quantization container variable.

        .. versionadded:: (cfdm) 1.12.2.0

        :Parameters:

            parent_ncvar: `str`
                The netCDF variable name of the parent data variable.

            attributes: `dict`
                All attributes of *all* netCDF variables, keyed by netCDF
                variable name.

        :Returns:

            `str` or `None`
                 The netCDF name of the quantization container
                 variable, or `None` if the container has already been
                 parsed.

        """
        g = self.read_vars

        ncvar = attributes[parent_ncvar]["quantization"]
        #        quantization_attribute = attributes[parent_ncvar]["quantization"]

        #       parsed_quantization = self._split_string_by_white_space(
        #           parent_ncvar, quantization_attribute, variables=True
        #        )

        ok = self._check_quantization(parent_ncvar, ncvar)

        #        ncvar = parsed_quantization[0]

        q = g["quantization_variable"].get(ncvar)
        if q is not None:
            # We've already parsed this quantization variable
            g["quantization"][parent_ncvar] = q
            return

        if ncvar in g["quantization_variable"]:
            # We've already parsed this quantization variable
            return

        # Create a quantization object
        q = self._create_quantization(ncvar)

        g["quantization_variable"][ncvar] = q
        g["quantization"][parent_ncvar] = q

        logger.info(
            f"    Quantization variable = {ncvar!r}\n"
            f"        netCDF attributes: {attributes[ncvar]}"
        )  # pragma: no cover

        if not ok:
            return

        return ncvar

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
               The element dimension, possibly modified to make sure
               that it is unique.

        """
        g = self.read_vars

        instance_dimension_size = self.implementation.get_data_size(
            elements_per_instance
        )
        try:
            element_dimension_size = int(
                self.implementation.get_data_maximum(elements_per_instance)
            )
        except np.ma.MaskError:
            raise ReadError(
                "Can't create a contiguous ragged array when the CF-netCDF "
                f"count variable in "
                f"{g['d_type']} file "
                f"{g.get('cdl_filename', g['dataset'])!r} "
                "contains missing data"
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
               The element dimension, possibly modified to make sure
               that it is unique.

        """
        g = self.read_vars

        index_array = self.implementation.get_array(index)
        (_, count) = np.unique(index_array, return_counts=True)

        # The number of elements per instance. For the instances array
        # example above, the elements_per_instance array is [7, 5, 7].
        elements_per_instance = count

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

        if g["debug"]:
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

            .. versionadded:: (cfdm) 1.11.0.0

        :Returns:

            `Field` or `Domain`

        """
        g = self.read_vars

        field = not domain

        # Whether or not we're attempting to a create a domain
        # construct from a URGID mesh topology variable
        mesh_topology = domain and field_ncvar in g["mesh"]
        if mesh_topology and location is None:
            raise ReadError(
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

        if g["debug"]:
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
        if field:
            if g["CF>=1.9"] and has_dimensions_attr:
                # ----------------------------------------------------
                # This netCDF variable has a 'dimensions'
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
                not g["CF>=1.9"] or not has_dimensions_attr
            ):
                # ----------------------------------------------------
                # This netCDF variable (which is not a UGRID mesh
                # topology nor a location index set variable) does not
                # have a 'dimensions' attribute. Therefore it is not a
                # domain variable and is to be ignored. CF>=1.9
                # (Introduced at v1.9.0.0)
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
                    f"with size {size}"
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
        self.implementation.set_original_filenames(f, g["dataset"])

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
                    logger.warning(
                        "There was a problem parsing the UGRID mesh "
                        "topology variable. Ignoring the UGRID mesh "
                        f"for {field_ncvar!r}."
                    )
                    if is_log_level_debug(logger):
                        from pprint import pformat

                        logger.debug(
                            f"Mesh dictionary is: {pformat(g['mesh'])}"
                        )

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
                    logger.warning(
                        "Couldn't find the UGRID discrete axis for mesh "
                        f"topology variable {mesh.mesh_ncvar!r}: "
                        f"Ignoring the UGRID mesh for {field_ncvar!r}."
                    )
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

                    # First turn the scalar auxiliary coordinate into
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
                    raise ReadError(
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

        # -------------------------------------------------------------
        # Set quantization metadata
        # -------------------------------------------------------------
        self._set_quantization(f, field_ncvar)

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
        return datatype == str or datatype.kind in "OSU"

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
                The netCDF variable name for the field construct.

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
                The netCDF variable name of the parent variable.

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

        .. versionadded:: (cfdm) 1.11.0.0

        :Parameters:

            parent_ncvar: `str`
                The netCDF variable name of the parent variable.

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
                Set to True if and only if the coordinate
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
            c, g["variable_datasetname"].get(ncvar, g["dataset"])
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
                bounds, g["variable_datasetname"][bounds_ncvar]
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
                    logger.warning(f"WARNING: {error} in file {g['dataset']}")

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

        # Store the netCDF variable name
        self.implementation.nc_set_variable(c, ncvar)

        if not domain_ancillary:
            g["coordinates"][parent_ncvar].append(ncvar)

        # Set quantization metadata
        self._set_quantization(c, ncvar)

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
            cell_measure, g["variable_datasetname"].get(ncvar)
        )

        # Set quantization metadata
        self._set_quantization(cell_measure, ncvar)

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
            raise ReadError(
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
            param, g["variable_datasetname"][ncvar]
        )

        # Set quantization metadata
        self._set_quantization(param, ncvar)

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
            variable, g["variable_datasetname"][ncvar]
        )

        # Set quantization metadata
        self._set_quantization(variable, ncvar)

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
            variable, g["variable_datasetname"][ncvar]
        )

        # Set quantization metadata
        self._set_quantization(variable, ncvar)

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
            variable, g["variable_datasetname"][ncvar]
        )

        # Set quantization metadata
        self._set_quantization(variable, ncvar)

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
            variable, g["variable_datasetname"][ncvar]
        )

        # Set quantization metadata
        self._set_quantization(variable, ncvar)

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
            variable, g["variable_datasetname"][ncvar]
        )

        # Set quantization metadata
        self._set_quantization(variable, ncvar)

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
            variable, g["variable_datasetname"][ncvar]
        )

        # Set quantization metadata
        self._set_quantization(variable, ncvar)

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
            variable, g["variable_datasetname"][ncvar]
        )

        # Set quantization metadata
        self._set_quantization(variable, ncvar)

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
                instantiating a new `NetCDF4Array` or `H5netcdfArray`.

                .. versionadded:: (cfdm) 1.10.0.1

        :Returns:

            (array, `dict`) or (`None`, `dict`) or `dict`
                The new `NetCDF4Array` or `H5netcdfArray` instance and
                a dictionary of the kwargs used to create it. If the
                array could not be created then `None` is returned in
                its place. If *return_kwargs_only* then only the
                dictionary is returned.

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
        if dtype is str or dtype.kind == "O":
            # netCDF string types have a dtype of `str`, which needs
            # to be reset as a numpy.dtype, but we don't know what
            # without reading the data, so set it to None for now.
            dtype = None

        if dtype is not None and unpacked_dtype is not False:
            dtype = np.result_type(dtype, unpacked_dtype)

        ndim = variable.ndim
        shape = variable.shape
        size = self._file_variable_size(variable)

        if size < 2:
            size = int(size)

        if self._is_char(ncvar) and ndim >= 1:
            # Has a trailing string-length dimension
            strlen = shape[-1]
            shape = shape[:-1]
            size /= strlen
            ndim -= 1
            dtype = np.dtype(f"U{strlen}")

        dataset = g["variable_datasetname"][ncvar]

        attributes = g["variable_attributes"][ncvar].copy()
        if coord_ncvar is not None:
            # Get the Units from the parent coordinate variable, if
            # they've not already been set.
            if "units" not in attributes:
                units = g["variable_attributes"][coord_ncvar].get("units")
                if units is not None:
                    attributes["units"] = units

            if "calendar" not in attributes:
                calendar = g["variable_attributes"][coord_ncvar].get(
                    "calendar"
                )
                if calendar is not None:
                    attributes["calendar"] = calendar

        kwargs = {
            "filename": dataset,
            "address": ncvar,
            "shape": shape,
            "dtype": dtype,
            "mask": g["mask"],
            "unpack": g["unpack"],
            "attributes": attributes,
            "storage_options": g["file_system_storage_options"].get(dataset),
        }

        if not self._cfa_is_aggregation_variable(ncvar):
            # Normal (non-aggregation) variable
            if return_kwargs_only:
                return kwargs

            file_opened_with = g["file_opened_with"]
            if file_opened_with == "netCDF4":
                array = self.implementation.initialise_NetCDF4Array(**kwargs)
            elif file_opened_with == "h5netcdf":
                array = self.implementation.initialise_H5netcdfArray(**kwargs)
            elif file_opened_with == "zarr":
                array = self.implementation.initialise_ZarrArray(**kwargs)

            return array, kwargs

        # ------------------------------------------------------------
        # Still here? Then create a netCDF array for an
        # aggregation variable
        # ------------------------------------------------------------

        # Only keep the relevant attributes
        a = {}
        for attr in ("units", "calendar", "add_offset", "scale_factor"):
            value = attributes.get(attr)
            if value is not None:
                a[attr] = value

        kwargs["attributes"] = a

        # Get rid of the incorrect shape. This will end up getting set
        # correctly by the AggregatedArray instance.
        kwargs.pop("shape", None)

        # 'mask' must be True, to indicate that the aggregated data is
        # to be masked by convention.
        kwargs["mask"] = True

        fragment_array_variables = g["fragment_array_variables"]
        standardised_terms = ("map", "uris", "identifiers", "unique_values")

        fragment_array = {}
        for term, term_ncvar in g["parsed_aggregated_data"][ncvar].items():
            if term not in standardised_terms:
                logger.warning(
                    "Ignoring non-standardised fragment array feature found "
                    "in the aggregated_data attribute of variable "
                    f"{ncvar!r}: {term!r}"
                )
                continue

            fragment_array_variable = fragment_array_variables[term_ncvar]
            fragment_array[term] = fragment_array_variable

            if term == "unique_values" and kwargs["dtype"] is None:
                # This is a string-valued aggregation variable with a
                # 'unique_values' fragment array variable, so set the
                # correct numpy data type.
                kwargs["dtype"] = fragment_array_variable.dtype

        kwargs["fragment_array"] = fragment_array
        if return_kwargs_only:
            return kwargs

        # Use the kwargs to create a AggregatedArray instance
        array = self.implementation.initialise_AggregatedArray(**kwargs)
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

        construct_type = self.implementation.get_construct_type(construct)

        netcdf_array, netcdf_kwargs = self._create_netcdfarray(
            ncvar,
            unpacked_dtype=unpacked_dtype,
            coord_ncvar=coord_ncvar,
        )

        if netcdf_array is None:
            return None

        array = netcdf_array

        dataset = netcdf_kwargs["filename"]

        attributes = netcdf_kwargs["attributes"]
        units = attributes.get("units")
        calendar = attributes.get("calendar")

        compression = g["compression"]

        dimensions = g["variable_dimensions"][ncvar]

        if (
            (uncompress_override is not None and uncompress_override)
            or not compression
            or not set(compression).intersection(dimensions)
        ):
            # The array is not compressed (or is not to be
            # uncompressed)
            compressed = False

        else:
            # The array might be compressed
            compressed = False

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
                    compressed = True

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
                        raise ReadError(
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
                    compressed = True

                elif "ragged_contiguous" in c:
                    # ------------------------------------------------
                    # Contiguous ragged array
                    # ------------------------------------------------
                    c = c["ragged_contiguous"]

                    # i = dimensions.index(ncdim)
                    if dimensions.index(ncdim) != 0:
                        raise ReadError(
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
                    compressed = True

                elif "ragged_indexed" in c:
                    # ------------------------------------------------
                    # Indexed ragged array
                    # ------------------------------------------------
                    c = c["ragged_indexed"]

                    # i = dimensions.index(ncdim)
                    if dimensions.index(ncdim) != 0:
                        raise ReadError(
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
                    compressed = True

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
                            interpolation_parameters[term] = (
                                self._copy_construct(
                                    "interpolation_parameter",
                                    parent_ncvar,
                                    param_ncvar,
                                )
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
                compressed = True

        data = self._create_Data(
            array,
            units=units,
            calendar=calendar,
            ncvar=ncvar,
            compressed=compressed,
            construct_type=construct_type,
        )
        data._original_filenames(define=dataset)

        # ------------------------------------------------------------
        # Cache selected values from disk
        # ------------------------------------------------------------
        aggregation_variable = self._cfa_is_aggregation_variable(ncvar)
        if (
            not compression_index
            and g.get("cache")
            and construct_type != "field"
            and not aggregation_variable
        ):
            # Only cache values from non-field data and
            # non-compression-index data, on the assumptions that:
            #
            # a) Field data is, in general, so large that finding the
            #    cached values takes too long.
            #
            # b) Cached values are never really required for
            #    compression index data.
            self._cache_data_elements(data, ncvar)

        # ------------------------------------------------------------
        # Set data aggregation parameters
        # ------------------------------------------------------------
        if not aggregation_variable:
            # For non-aggregation variables, set the aggregated write
            # status to True when there is exactly one dask chunk.
            if data.npartitions == 1:
                data._nc_set_aggregation_write_status(True)
                data._nc_set_aggregation_fragment_type("uri")
        else:
            if construct is not None:
                # Remove the aggregation attributes from the construct
                self.implementation.del_property(
                    construct, "aggregated_dimensions", None
                )
                aggregated_data = self.implementation.del_property(
                    construct, "aggregated_data", None
                )
                # Store the 'aggregated_data' attribute information
                if aggregated_data:
                    data.nc_set_aggregated_data(aggregated_data)

            # Set the aggregated write status to True iff each
            # non-aggregated axis has exactly one Dask chunk
            cfa_write_status = True
            for n, numblocks in zip(
                netcdf_array.get_fragment_array_shape(), data.numblocks
            ):
                if n == 1 and numblocks > 1:
                    # Note: n is always 1 for non-aggregated axes
                    cfa_write_status = False
                    break

            data._nc_set_aggregation_write_status(cfa_write_status)

            # Store the fragment type
            fragment_type = netcdf_array.get_fragment_type()
            data._nc_set_aggregation_fragment_type(fragment_type)

            # Replace the directories of fragment locations
            if fragment_type == "uri":
                replace_directory = g["cfa"].get("replace_directory")
                if replace_directory:
                    try:
                        data.replace_directory(**replace_directory)
                    except TypeError:
                        raise TypeError(
                            "The 'replace_directory' key of the 'cfa' "
                            "parameter must provide valid parameters to "
                            "the 'Data.replace_directory' method. "
                            f"Got: {replace_directory!r}"
                        )

        # Return the data object
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
            field_ancillary, g["variable_datasetname"][ncvar]
        )

        # Set quantization metadata
        self._set_quantization(field_ancillary, ncvar)

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
                                raise ReadError(incorrect_interval)

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
                                raise ReadError(incorrect_interval)

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
                    raise ReadError(incorrect_interval)

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
                                + ":coordinate_interpolation": coordinate_interpolation
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
                raise ReadError(
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

            gathered_array: `NetCDF4Array` or `H5netcdfArray`

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
        return self.implementation.initialise_RaggedContiguousArray(
            compressed_array=ragged_contiguous_array,
            shape=uncompressed_shape,
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
        return self.implementation.initialise_RaggedIndexedArray(
            compressed_array=ragged_indexed_array,
            shape=uncompressed_shape,
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
        return self.implementation.initialise_RaggedIndexedContiguousArray(
            compressed_array=ragged_indexed_contiguous_array,
            shape=uncompressed_shape,
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
        ncdimensions=None,
        compressed=False,
        construct_type=None,
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

            units: `str`, optional
                The units of *array*. By default, or if `None`, it is
                assumed that there are no units.

            calendar: `str`, optional
                The calendar of *array*. By default, or if `None`, it is
                assumed that there is no calendar.

            ncdimensions: sequence of `str`, optional
                The netCDF dimensions spanned by the array.

                .. versionadded:: (cfdm) 1.11.2.0

            construct_type: `str` or `None`, optional
                The type of the construct that contains *array*. Set
                to `None` if the array does not belong to a construct.

                .. versionadded:: (cfdm) 1.12.0.0

            kwargs: optional
                Extra parameters to pass to the initialisation of the
                returned `Data` object.

        :Returns:

            `Data`

        """
        if array.dtype is None:
            g = self.read_vars
            if g["has_groups"]:
                group, name = self._netCDF4_group(
                    g["variable_grouped_dataset"][ncvar], ncvar
                )
                variable = group.variables.get(name)
            else:
                variable = g["variables"].get(ncvar)

            array = variable[...]

            string_type = isinstance(array, str)
            if string_type:
                # A netCDF string type scalar variable comes out as Python
                # str object, so convert it to a numpy array.
                array = np.array(array, dtype=f"U{len(array)}")

            if not variable.ndim:
                # NetCDF4 has a thing for making scalar size 1
                # variables into 1d arrays
                array = array.squeeze()

            if not string_type:
                # An N-d (N>=1) netCDF string type variable comes out
                # as a numpy object array, so convert it to numpy
                # string array.
                array = array.astype("U", copy=False)
                # NetCDF4 doesn't auto-mask VLEN variables
                array = np.ma.where(array == "", np.ma.masked, array)

        # Set the dask chunking strategy
        chunks = self._dask_chunks(
            array, ncvar, compressed, construct_type=construct_type
        )

        # Set whether or not to read the data into memory
        to_memory = self.read_vars["to_memory"]
        to_memory = "all" in to_memory or construct_type in to_memory

        data = self.implementation.initialise_Data(
            array=array,
            units=units,
            calendar=calendar,
            chunks=chunks,
            to_memory=to_memory,
            copy=False,
            **kwargs,
        )

        # Store the dataset chunking
        if self.read_vars["store_dataset_chunks"] and ncvar is not None:
            # Only store the dataset chunking if 'data' has the same
            # shape as its netCDF variable. This may not be the case
            # for variables compressed by convention (e.g. some DSG
            # variables).
            chunks, shape = self._get_dataset_chunks(ncvar)
            if shape == data.shape:
                self.implementation.nc_set_dataset_chunksizes(data, chunks)

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
            if g["debug"]:
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
            parent_ncvar
            + ":coordinate_interpolation": coordinate_interpolation
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

    def _check_quantization(self, parent_ncvar, ncvar):
        """Check a quantization container variable.

        .. versionadded:: (cfdm) 1.12.2.0

        :Parameters:

            parent_ncvar: `str`
                The netCDF variable name of the parent variable.

            ncvar: `str`
                The netCDF variable name of the quantization variable.

        :Returns:

            `bool`

        """
        attribute = {parent_ncvar + ":quantization": ncvar}

        g = self.read_vars

        ok = True

        # Check that the quantization variable exists in the file
        if ncvar not in g["internal_variables"]:
            ncvar, message = self._missing_variable(
                ncvar, "Quantization variable"
            )
            self._add_message(
                parent_ncvar,
                ncvar,
                message=message,
                attribute=attribute,
            )
            ok = False

        attributes = g["variable_attributes"][ncvar]

        implementation = attributes.get("implementation")
        if implementation is None:
            self._add_message(
                parent_ncvar,
                ncvar,
                message=("implementation attribute", "is missing"),
            )
            ok = False

        algorithm = attributes.get("algorithm")
        if algorithm is None:
            self._add_message(
                parent_ncvar,
                ncvar,
                message=("algorithm attribute", "is missing"),
            )
            ok = False

        parameter = CF_QUANTIZATION_PARAMETERS.get(algorithm)
        if parameter is None:
            self._add_message(
                parent_ncvar,
                ncvar,
                message=(
                    "algorithm attribute",
                    f"has non-standardised value: {algorithm!r}",
                ),
            )
            ok = False

        if parameter not in g["variable_attributes"][parent_ncvar]:
            self._add_message(
                parent_ncvar,
                parent_ncvar,
                message=(f"{parameter} attribute", "is missing"),
            )
            ok = False

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
                        (
                            mapping[ncvar[:-1]] + ":"
                            if ncvar.endswith(":")
                            else mapping[ncvar]
                        )
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

        pat_value = subst(r"(?P<value>WORD)SEP")
        pat_values = f"({pat_value})+"

        pat_mapping = subst(
            rf"(?P<mapping_name>WORD):SEP(?P<values>{pat_values})"
        )
        pat_mapping_list = f"({pat_mapping})+"

        pat_all = subst(
            rf"((?P<sole_mapping>WORD)|(?P<mapping_list>{pat_mapping_list}))$"
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
        *location_index_set variable* to
        ``self.read_vars["do_not_create_field"]``.

        .. versionadded:: (cfdm) 1.11.0.0

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
        # Create cell connectivity constructs for each location
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
        *location_index_set* variable to
        ``self.read_vars["do_not_create_field"]``.

        .. versionadded:: (cfdm) 1.11.0.0

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

        .. versionadded:: (cfdm) 1.11.0.0

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

        .. versionadded:: (cfdm) 1.11.0.0

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
            compressed=True,
        )
        self.implementation.set_data(bounds, bounds_data, copy=False)

        # Set the original file names
        self.implementation.set_original_filenames(
            bounds, g["variable_datasetname"][node_ncvar]
        )

        error = self.implementation.set_bounds(aux, bounds, copy=False)
        if error:
            logger.warning(str(error))

        return aux

    def _ugrid_create_domain_topology(self, parent_ncvar, f, mesh, location):
        """Create a domain topology construct.

        .. versionadded:: (cfdm) 1.11.0.0

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
            # appropriate connectivity attribute
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
            properties["long_name"] = (
                "Maps every point to its connected points"
            )
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
            attributes = kwargs["attributes"]
            data = self._create_Data(
                array,
                units=attributes.get("units"),
                calendar=attributes.get("calendar"),
                ncvar=connectivity_ncvar,
                compressed=True,
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
            domain_topology, self.read_vars["dataset"]
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

        Only "face_face_connectivity" is supported.

        .. versionadded:: (cfdm) 1.11.0.0

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
        attributes = kwargs["attributes"]
        data = self._create_Data(
            array,
            units=attributes.get("units"),
            calendar=attributes.get("calendar"),
            ncvar=connectivity_ncvar,
            compressed=True,
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
            connectivity, self.read_vars["dataset"]
        )

        index_set = mesh.index_set
        if index_set is not None:
            # Apply a location index set
            connectivity = connectivity[index_set]

        return [connectivity]

    def _ugrid_cell_dimension(self, location, connectivity_ncvar, mesh):
        """The connectivity variable dimension that indexes the cells.

        .. versionadded:: (cfdm) 1.11.0.0

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

        .. versionadded:: (cfdm) 1.11.0.0

        :Parameters:

            mesh_ncvar: `str`
                The name of the netCDF mesh topology variable.

        :Returns:

            `bool`
                Whether or not the mesh topology variable adheres to
                the CF conventions.

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

        These checks are independent of any parent variable.

        .. versionadded:: (cfdm) 1.11.0.0

        :Parameters:

            location_index_set_ncvar: `str`
                The name of the UGRID location index set netCDF
                variable.

        :Returns:

            `bool`
                Whether or not the location index set variable adheres
                to the CF conventions.

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

        These checks are in the context of a parent variable.

        .. versionadded:: (cfdm) 1.11.0.0

        :Parameters:

            parent_ncvar: `str`
                The netCDF variable name of the parent field or domain
                construct.

            location_index_set_ncvar: `str`
                The name of the UGRID location index set netCDF
                variable.

        :Returns:

            `bool`
                Whether or not the location index set variable of a
                field or domain variable adheres to the CF
                conventions.

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

        These checks are in the context of a parent variable.

        .. versionadded:: (cfdm) 1.11.0.0

        :Parameters:

            parent_ncvar: `str`
                The netCDF variable name of the parent field or domain
                construct.

        :Returns:

            `bool`
                Whether or not the mesh topology variable of a field
                or domain variable adheres to the CF conventions.

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

        .. versionadded:: (cfdm) 1.11.0.0

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
                Whether or not the connectivity variable adheres to
                the CF conventions.

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

    def _dataset_has_groups(self, nc):
        """True if the dataset has a groups other than the root group.

        If the dataset is a Zarr dataset then an exception is raised
        of the dataset has groups.

        .. versionadded:: (cfdm) 1.12.2.0

        :Parameters:

            nc: `netCDF.Dataset` or `h5netcdf.File` or `zarr.Group`
                The dataset.

        :Returns:

            `bool`

        """
        if self.read_vars["file_opened_with"] == "zarr":
            # zarr
            if len(tuple(nc.groups())) > 1:
                raise ReadError(
                    "Can't read Zarr dataset that has groups: "
                    f"{self.read_vars['dataset']}"
                )

            return False

        # netCDF4, h5netcdf
        return bool(nc.groups)

    def _file_global_attribute(self, nc, attr):
        """Return a global attribute from a dataset.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            nc: `netCDF4.Dataset`, `h5netcdf.File`, or `zarr.Group`
                The dataset.

            attr: `str`
                The global attribute name.

        :Returns:

                The global attribute value.

        """
        try:
            # netCDF4
            return nc.getncattr(attr)
        except AttributeError:
            # h5netcdf, zarr
            return nc.attrs[attr]

    def _file_global_attributes(self, nc):
        """Return the global attributes from a dataset.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            nc: `netCDF4.Dataset`, `h5netcdf.File`, or `zarr.Group`
                The dataset.

        :Returns:

            `dict`-like
                A dictionary of the attribute values keyed by their
                names.

        """
        try:
            # h5netcdf, zarr
            return nc.attrs
        except AttributeError:
            # netCDF4
            return {attr: nc.getncattr(attr) for attr in nc.ncattrs()}

    def _file_dimensions(self, nc):
        """Return all dimensions in the root group.

        .. versionadded:: (cfdm) 1.11.2.0

        :Returns:

            `dict`-like
                A dictionary of the dimensions keyed by their names.

        """
        try:
            # netCDF4, h5netcdf
            return nc.dimensions
        except AttributeError:
            # zarr
            dimensions = {}
            for var in self._file_variables(nc).values():
                dimensions.update(
                    {
                        name: ZarrDimension(name, size, nc)
                        for name, size in zip(
                            self._file_variable_dimensions(var), var.shape
                        )
                        if name not in dimensions
                    }
                )

            return dimensions

    def _file_dimension(self, nc, dim_name):
        """Return a dimension from the root group of a dataset.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            nc: `netCDF4.Dataset`, `h5netcdf.File`, or `zarr.Group`
                The dataset.

            dim_name: `str`
                The dimension name.

        :Returns:

            `netCDF.Dimension` or `h5netcdf.Dimension`
                The dimension.

        """
        # netCDF5, h5netcdf, zarr
        return self._file_dimensions(nc)[dim_name]

    def _file_dimension_isunlimited(self, nc, dim_name):
        """Return whether a dimension is unlimited.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            nc: `netCDF4.Dataset` or `h5netcdf.File`
                The dataset.

            dim_name: `str`
                The dimension name.

        :Returns:

            `bool`
                Whether the dimension is unlimited.

        """
        try:
            # netCDF4, h5netcdf
            return self._file_dimension(nc, dim_name).isunlimited()
        except Exception:
            # zarr
            return False

    def _file_dimension_size(self, nc, dim_name):
        """Return a dimension's size.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            nc: `netCDF4.Dataset`, `h5netcdf.File`, or `zarr.Group`
                The dataset.

            dim_name: `str`
                The dimension name.

        :Returns:

            `int`
                The dimension size.

        """
        # netCDF5, h5netcdf, zarr
        return self._file_dimension(nc, dim_name).size

    def _file_variables(self, nc):
        """Return all variables in the root group.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            nc: `netCDF4.Dataset`, `h5netcdf.File` or `zarr.Group`
                The dataset.

        :Returns:

            `dict`-like
                A dictionary of the variables keyed by their names.

        """
        try:
            # netCDF4, h5netcdf
            return nc.variables
        except AttributeError:
            # zarr
            return dict(nc.arrays())

    def _file_variable(self, nc, var_name):
        """Return a variable.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            nc: `netCDF4.Dataset`, `h5netcdf.File`, or `zarr.Group`
                The dataset.

            var_name: `str`
                The variable name.

        :Returns:

            `netCDF4.Variable`, `h5netcdf.Variable`, or `zarr.Array`
                The variable.

        """
        # netCDF5, h5netcdf, zarr
        return self._file_variables(nc)[var_name]

    def _file_variable_attributes(self, var):
        """Return the variable attributes.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            var: `netCDF4.Variable`, `h5netcdf.Variable`, or `zarr.Array`
                The variable.

        :Returns:

            `dict`
                A dictionary of the attribute values keyed by their
                names.

        """
        try:
            # h5netcdf, zarr
            attrs = dict(var.attrs)
        except AttributeError:
            # netCDF4
            return {attr: var.getncattr(attr) for attr in var.ncattrs()}
        else:
            if self.read_vars["file_opened_with"] == "zarr":
                # zarr: Remove the _ARRAY_DIMENSIONS attribute
                attrs.pop("_ARRAY_DIMENSIONS", None)

            return attrs

    def _file_variable_dimensions(self, var):
        """Return the variable dimension names.

         .. versionadded:: (cfdm) 1.12.2.0

        :Parameters:

             var: `netCDF4.Variable`, `h5netcdf.Variable`, or `zarr.Array`
                 The variable.

         :Returns:

             `tuple` of `str`
                 The dimension names.

        """
        try:
            # netCDF4, h5netcdf
            return var.dimensions
        except AttributeError:
            try:
                # zarr v3
                dimension_names = var.metadata.dimension_names
                if dimension_names is None:
                    # scalar variable
                    dimension_names = ()

                return dimension_names
            except AttributeError:
                # zarr v2
                return tuple(var.attrs["_ARRAY_DIMENSIONS"])

    def _file_variable_size(self, var):
        """Return the size of a variable's array.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            var: `netCDF4.Variable`, `h5netcdf.Variable`, or `zarr.Array`
                The variable.

        :Returns:

            `int`
                The array size.

        """
        # Use try/except here because the variable type could differ
        # from that implied by the value of
        # read_vars["file_opened_with"]
        try:
            # netCDF4, zarr
            return var.size
        except AttributeError:
            # h5netcdf
            return prod(var.shape)

    def _get_storage_options(self, dataset, parsed_dataset):
        """Get the storage options for accessing a file.

        If returned storage options will always include an
        ``'endpoint_url'`` key.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            dataset: `str`
                The name of the dataset.

            parsed_dataset: `uritools.SplitResultString`
                The parsed dataset name.

        :Returns:

            `dict`
                The storage options for accessing the file.

        """
        g = self.read_vars
        storage_options = g["storage_options"].copy()

        client_kwargs = storage_options.get("client_kwargs", {})
        if (
            "endpoint_url" not in storage_options
            and "endpoint_url" not in client_kwargs
        ):
            authority = parsed_dataset.authority
            if not authority:
                authority = ""

            storage_options["endpoint_url"] = f"https://{authority}"

        g["file_system_storage_options"].setdefault(dataset, storage_options)

        return storage_options

    def _get_dataset_chunks(self, ncvar):
        """Return a netCDF variable's dataset storage chunks.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

           ncvar: `str`
                The netCDF variable name.

        :Returns:

            2-tuple:
                The variable's chunking strategy and its shape.

                The variable's chunking strategy will one of
                ``'contiguous'``, a sequence of `int`, or (only for
                netCDF-3) `None`.

        **Examples**

        >>> n._get_dataset_chunks('tas')
        [1, 324, 432], (12, 324, 432)
        >>> n._get_dataset_chunks('pr')
        'contiguous', (12, 324, 432)
        >>> n._get_dataset_chunks('ua')
        None, (12, 324, 432)

        """
        nc = self.read_vars["variable_dataset"][ncvar]

        # 'nc' is the flattened dataset, so replace an 'ncvar' string
        # that contains groups (e.g. '/forecast/tas') with its
        # flattened version (e.g. 'forecast__tas').
        if ncvar.startswith("/"):
            ncvar = ncvar[1:]
            ncvar = ncvar.replace("/", flattener_separator)

        var = nc[ncvar]
        try:
            # netCDF4
            chunks = var.chunking()
        except AttributeError:
            # h5netcdf, zarr
            chunks = var.chunks
            if chunks is None:
                chunks = "contiguous"

        return chunks, var.shape

    def _dask_chunks(self, array, ncvar, compressed, construct_type=None):
        """Set the Dask chunking strategy for a netCDF variable.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            array:
                The variable data. If the netCDF variable is
                compressed by convention, then *array* is in its
                uncompressed form.

            ncvar: `str`
                The name of the netCDF variable containing the array.

            compressed: `bool`
                Whether or not the netCDF variable is compressed by
                convention.

            construct_type: `str` or `None`
                The type of the construct that contains *array*. Set
                to `None` if the array does not belong to a construct.

        :Returns:

            `str` or `int` or `list`
                The chunks that are suitable for passing to a `Data`
                object containing the variable's array.

        """
        g = self.read_vars

        cfa_write = g["cfa_write"]
        if (
            cfa_write
            and construct_type is not None
            and construct_type in cfa_write
            or "all" in cfa_write
        ):
            # The intention is for this array to be written out as an
            # aggregation variable, so set dask_chunks=None to ensure
            # that each Dask chunk contains exactly one complete
            # fragment.
            dask_chunks = None
        else:
            dask_chunks = g.get("dask_chunks", "storage-aligned")

        storage_chunks = self._netcdf_chunksizes(g["variables"][ncvar])

        # ------------------------------------------------------------
        # None
        # ------------------------------------------------------------
        if dask_chunks is None:
            # No Dask chunking
            return -1

        ndim = array.ndim
        if (
            storage_chunks is not None
            and not compressed
            and len(storage_chunks) > ndim
        ):
            # Remove irrelevant trailing dimensions (e.g. as used by
            # char data-type variables)
            storage_chunks = storage_chunks[:ndim]

        # ------------------------------------------------------------
        # storage-aligned
        # ------------------------------------------------------------
        if dask_chunks == "storage-aligned":
            if compressed or storage_chunks is None:
                # Use "auto" Dask chunking for contiguous variables
                # and variables compressed by convention. (In the
                # latter case, the Dask chunks reflect the
                # uncompressed data, rather than the compressed data
                # found in the file.)
                return "auto"

            # --------------------------------------------------------
            # Strategy for creating storage-aligned Dask chunks:
            #
            # 1) Initialise the Dask chunk as the Dask's "auto" shape.
            #
            # 2) Whilst there are Dask elements that are strictly less
            #    than their corresponding storage elements,
            #    iteratively increase those Dask axis elements whilst
            #    reducing the other Dask axis elements in a manner
            #    such that the total number of Dask chunk elements is
            #    preserved.
            #
            # 3) When all Dask elements have become greater than or
            #    equal to their corresponding storage elements,
            #    replace each Dask element with the largest multiple
            #    of the storage element that doesn't exceed the
            #    current Dask element.
            #
            # Note: If the number of elements in the storage chunk is
            #       less than or equal to the number of elements in
            #       the original Dask chunk, then the storage-aligned
            #       chunk also will also have an amount of elements
            #       that is less than or equal to the number of
            #       elements in the original Dask chunk. Otherwise,
            #       the storage-aligned chunk will have more elements
            #       than the original Dask chunk:
            #
            #                        Chunk shape              Elements
            #       ---------------- ----------------------- ---------
            #       storage:         (50, 100, 150, 20,   5)  75000000
            #       original Dask:   (49, 101, 150,  5, 160) 593880000
            #       storage-aligned: (50, 100, 150, 20,  35) 525000000
            #       ---------------- ----------------------- ---------
            #       storage:         (50, 100, 150, 20,   5)  75000000
            #       original Dask:   (5,   15, 150,  5, 160)   9000000
            #       storage-aligned: (50, 100, 150, 20,   5)  75000000
            # --------------------------------------------------------
            # 1) Initialise the Dask chunk shape
            dask_chunks = normalize_chunks(
                "auto", shape=array.shape, dtype=array.dtype
            )
            dask_chunks = [sizes[0] for sizes in dask_chunks]
            n_dask_elements = prod(dask_chunks)

            # 2) While there are Dask axis elements that are less than
            #    their corresponding storage axis elements,
            #    iteratively increase the those Dask axis elements
            #    whilst reducing the other Dask axis elements so that
            #    the total number of Dask chunk elements is preserved.
            continue_iterating = True

            while continue_iterating:
                continue_iterating = False

                # Index locations of Dask elements which are greater
                # than their corresponding storage elements
                dask_gt_storage = []

                # Product of Dask elements which are greater than
                # their corresponding storage element
                p_dask_gt_storage = 1

                # Product of storage elements which are less than or
                # equal to their corresponding Dask element
                p_storage_ge_dask = 1
                for i, (sc, dc) in enumerate(
                    zip(storage_chunks, dask_chunks[:])
                ):
                    if dc > sc:
                        # Dask element is greater than the storage
                        # element
                        dask_gt_storage.append(i)
                        p_dask_gt_storage *= dc
                    else:
                        # Dask element is less than or equal to the
                        # storage element
                        p_storage_ge_dask *= sc

                if not dask_gt_storage:
                    # All Dask elements are less than or equal to
                    # their corresponding storage elements => we can
                    # stop the iteration, after setting the Dask chunk
                    # to the storage chunk.
                    dask_chunks[:] = storage_chunks
                    break

                # Calculate the x that preserves the Dask chunk size
                # (i.e. the number of elements in the Dask chunk) when
                #
                #  i) All Dask elements that are strictly less than
                #     their corresponding storage axis elements have
                #     been replaced with those corresponding larger
                #     values.
                #
                # ii) All other Dask elements have been reduced by
                #     being raised to the power of x.
                #
                # I.e. x is such that
                #
                #      p_storage_ge_dask * p_dask_gt_storage**x = n_dask_elements
                #  =>  x = log(n_dask_elements / p_storage_ge_dask) / log(p_dask_gt_storage)
                #
                # E.g. if the storage chunk shape is (40, 20, 15,  5)
                #      and the Dask chunk shape is   (20, 25, 10, 30),
                #      then x is such that
                #
                #      (40 * 15) * (25 * 30)**x = 20 * 25 * 10 * 30
                #   => 600 * 750**x = 150000
                #   => x = log(150000 / 600) / log(750)
                #   => x = 0.834048317232446
                #
                # Note: If we have reached here to calculate x, then
                #       it must be the case that p_dask_gt_storage > 1
                #       and n_dask_elements >
                #       p_storage_ge_dask. Therefore:
                #
                #       a) log(p_dask_gt_storage) > 0
                #       b) x is in the range (-inf, 1], excluding 0
                #       c) x is 1 if no Dask element is less than its
                #          corresponding storage element
                #
                # Note: There are other reasonable methods for
                #       reducing Dask elements. With the method used
                #       here (i.e. using a power of x that is <= 1),
                #       larger values get reduced by a greater factor
                #       than smaller values, thereby promoting the
                #       Dask preference for square-like chunk shapes
                #       (although I suspect that in many cases,
                #       different approaches will give the same
                #       result).
                x = log(n_dask_elements / p_storage_ge_dask) / log(
                    p_dask_gt_storage
                )

                for i, (sc, dc) in enumerate(
                    zip(storage_chunks, dask_chunks[:])
                ):
                    if i in dask_gt_storage:
                        # The Dask element is greater than the storage
                        # element => raise the Dask element to the
                        # power of x.
                        if x == 1:
                            # After being raised to the power of x (=
                            # 1), the Dask element will still be
                            # greater than the storage element, so we
                            # don't need to change it.
                            c = dc
                        else:
                            # x < 1
                            c = dc**x
                            if c < sc:
                                # After being raised to the power of
                                # x, the Dask element has become less
                                # than the storage element => we need
                                # to go round the 2) iteration again,
                                # because this new Dask element will
                                # need increasing to its corresponding
                                # storage element value, with the
                                # possibility of further reductions to
                                # other Dask elements.
                                continue_iterating = True
                    else:
                        # The Dask element is less than or equal to
                        # the storage element, so replace it with the
                        # storage element.
                        c = sc

                    # Update the Dask chunk element
                    dask_chunks[i] = c

            # 3) All Dask elements are now greater than or equal to
            #    their corresponding storage elements, so replace each
            #    Dask element with the largest multiple of the storage
            #    element that doesn't exceed the current Dask element.
            #
            # E.g. if the storage chunk is (12, 40, 40) and the
            #      current Dask chunk is (12, 64, 128), then the Dask
            #      chunk will be modified to be (12, 40, 120).
            if dask_gt_storage:
                for i, (sc, dc, axis_size) in enumerate(
                    zip(storage_chunks, dask_chunks[:], array.shape)
                ):
                    if i in dask_gt_storage and dc < axis_size:
                        # Dask element is strictly greater than the
                        # corresponding storage element, and smaller
                        # that the axis size.
                        dc = int(dc)
                        c = dc - (dc % sc)
                        if not c:
                            # Analytically, c must be a positive
                            # integer multiple of sc, but it's
                            # conceivable that rounding errors could
                            # result in c being 0 when it should be
                            # sc.
                            c = sc

                        dask_chunks[i] = c

            # Return the storage-aligned Dask chunks
            return dask_chunks

        # ------------------------------------------------------------
        # storage-exact
        # ------------------------------------------------------------
        if dask_chunks == "storage-exact":
            if compressed or storage_chunks is None:
                # Use "auto" Dask chunking for contiguous variables
                # and variables compressed by convention. (In the
                # latter case, the Dask chunks reflect the
                # uncompressed data, rather than the compressed data
                # found in the file.)
                return "auto"

            # Set the Dask chunks to be exactly the storage chunks for
            # chunked variables.
            return storage_chunks

        # ------------------------------------------------------------
        # dict
        # ------------------------------------------------------------
        if isinstance(dask_chunks, dict):
            # For ncdimensions = ('t', 'lat'):
            #
            # {}                                         -> ["auto", "auto"]
            # {'ncdim%t': 12}                            -> [12, "auto"]
            # {'ncdim%t': 12, 'ncdim%lat': 10000}        -> [12, 10000]
            # {'ncdim%t': 12, 'ncdim%lat': "20MB"}       -> [12, "20MB"]
            # {'ncdim%t': 12, 'latitude': -1}            -> [12, -1]
            # {'ncdim%t': 12, 'Y': None}                 -> [12, None]
            # {'ncdim%t': 12, 'ncdim%lat': (30, 90)}     -> [12, (30, 90)]
            # {'ncdim%t': 12, 'ncdim%lat': None, 'X': 5} -> [12, None]
            if not dask_chunks:
                return "auto"

            attributes = g["variable_attributes"]
            chunks = []
            for ncdim in g["variable_dimensions"][ncvar]:
                key = f"ncdim%{ncdim}"
                if key in dask_chunks:
                    chunks.append(dask_chunks[key])
                    continue

                found_coord_attr = False
                dim_coord_attrs = attributes.get(ncdim)
                if dim_coord_attrs is not None:
                    for attr in ("standard_name", "axis"):
                        key = dim_coord_attrs.get(attr)
                        if key in dask_chunks:
                            found_coord_attr = True
                            chunks.append(dask_chunks[key])
                            break

                if not found_coord_attr:
                    # Use "auto" chunks for this dimension
                    chunks.append("auto")

            dask_chunks = chunks

        # ------------------------------------------------------------
        # Return the Dask chunks
        # ------------------------------------------------------------
        return dask_chunks

    def _cache_data_elements(self, data, ncvar):
        """Cache selected element values.

        Updates *data* in-place to store its first, second,
        penultimate, and last element values (as appropriate).

        Doing this here is quite cheap because only the individual
        elements are read from the already-open file, as opposed to
        being retrieved from *data* (which would require a whole dask
        chunk to be read to get each single value).

        However, empirical evidence shows that using netCDF4 to access
        the first and last elements of a large array on disk
        (e.g. shape (1, 75, 1207, 1442)) is slow (e.g. ~2 seconds) and
        doesn't scale well with array size (i.e. it takes
        disproportionally longer for larger arrays).

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

            data: `Data`
                The data to be updated with its cached values.

            ncvar: `str`
                The name of the netCDF variable that contains the
                data.

        :Returns:

            `None`

        """
        if data.data.get_compression_type():
            # Don't get cached elements from arrays compressed by
            # convention, as they'll likely be wrong.
            return

        g = self.read_vars

        # Get the netCDF4.Variable for the data
        if g["has_groups"]:
            group, name = self._netCDF4_group(
                g["variable_grouped_dataset"][ncvar], ncvar
            )
            variable = group.variables.get(name)
        else:
            variable = g["variables"].get(ncvar)

        # Check for cached data elements and use them if they exist
        elements = g["cached_data_elements"].get(ncvar)
        if elements is not None:
            # Store the cached elements in the data object
            data._set_cached_elements(elements)
            return

        # ------------------------------------------------------------
        # Still here? then there were no cached data elements, so we
        #             have to create them.
        # ------------------------------------------------------------
        # Get the required element values
        size = data.size
        ndim = data.ndim

        # Whether or not this is an array of strings
        dtype = variable.dtype
        string = dtype == str
        obj = not string and dtype.kind == "O"

        # Whether or not this is an array of chars
        if (
            not (string or obj)
            and dtype.kind in "SU"
            and variable.ndim == ndim + 1
        ):
            # This variable is a netCDF classic style char array with
            # a trailing dimension that needs to be collapsed
            char = True
        else:
            char = False

        if ndim == 1:
            # Also cache the second element for 1-d data, on the
            # assumption that they may well be dimension coordinate
            # data.
            if size == 1:
                indices = (0, -1)
                value = variable[...]
                values = (value, value)
            elif size == 2:
                indices = (0, 1, -1)
                value = variable[-1:]
                values = (variable[:1], value, value)
            else:
                indices = (0, 1, -1)
                values = (variable[:1], variable[1:2], variable[-1:])
        elif ndim == 2 and data.shape[-1] == 2:
            # Assume that 2-d data with a last dimension of size 2
            # contains coordinate bounds, for which it is useful to
            # cache the upper and lower bounds of the the first and
            # last cells.
            indices = (0, 1, -2, -1)
            ndim1 = ndim - 1
            values = (
                variable[(slice(0, 1),) * ndim1 + (slice(0, 1),)],
                variable[(slice(0, 1),) * ndim1 + (slice(1, 2),)],
            )
            if data.size == 2:
                values = values + values
            else:
                values += (
                    variable[(slice(-1, None, 1),) * ndim1 + (slice(0, 1),)],
                    variable[(slice(-1, None, 1),) * ndim1 + (slice(1, 2),)],
                )
        elif size == 1:
            indices = (0, -1)
            value = variable[...]
            values = (value, value)
        elif size == 3:
            indices = (0, 1, -1)
            if char:
                values = variable[...].reshape(3, variable.shape[-1])
            else:
                values = variable[...].flatten()
        else:
            indices = (0, -1)
            values = (
                variable[(slice(0, 1),) * ndim],
                variable[(slice(-1, None, 1),) * ndim],
            )

        # Create a dictionary of the element values
        elements = {}
        for index, value in zip(indices, values):
            if obj:
                value = value.astype(str)
            elif string:
                # Convert an array of objects to an array of strings
                value = np.array(value, dtype="U")
            elif char:
                # Variable is a netCDF classic style char array, so
                # collapse (by concatenation) the outermost (fastest
                # varying) dimension. E.g. [['a','b','c']] becomes
                # ['abc']
                if dtype.kind == "U":
                    value = value.astype("S")

                a = netCDF4.chartostring(value)
                shape = a.shape
                a = np.array([x.rstrip() for x in a.flat])
                a = np.reshape(a, shape)
                value = np.ma.masked_where(a == "", a)

            elements[index] = value

        # Cache the cached data elements for this variable
        g["cached_data_elements"][ncvar] = elements

        # Store the elements in the data object
        data._set_cached_elements(elements)

    def _netcdf_chunksizes(self, variable):
        """Return the variable chunk sizes.

        .. versionadded:: (cfdm) 1.11.2.0

        :Parameters:

        variable:
                The variable, that has the same API as
                `netCDF4.Variable` or `h5netcdf.Variable`.

        :Returns:

            sequence of `int`
                The chunksizes. If the variable is contiguous
                (i.e. not chunked) then the variable's shape is
                returned.

        **Examples**

        >>> f.chunksizes(variable)
        [1, 324, 432]

        >>> f.chunksizes(variable)
        None

        """
        try:
            # netCDF4
            chunks = variable.chunking()
            if chunks == "contiguous":
                chunks = None
        except AttributeError:
            # h5netcdf
            chunks = variable.chunks

        return chunks

    def _cfa_is_aggregation_variable(self, ncvar):
        """Return True if *ncvar* is a CF-netCDF aggregation variable.

        .. versionadded:: (cfdm) 1.12.0.0

        :Parameters:

            ncvar: `str`
                The name of the netCDF variable.

        :Returns:

            `bool`
                Whether or not *ncvar* is an aggregation variable.

        """
        g = self.read_vars
        return (
            ncvar in g["parsed_aggregated_data"]
            and ncvar not in g["external_variables"]
        )

    def _cfa_parse_aggregated_data(self, ncvar, aggregated_data):
        """Parse a CF-netCDF 'aggregated_data' attribute.

        .. versionadded:: (cfdm) 1.12.0.0

        :Parameters:

            ncvar: `str`
                The netCDF variable name.

            aggregated_data: `str` or `None`
                The CF-netCDF ``aggregated_data`` attribute.

        :Returns:

            `dict`
                The parsed attribute.

        """
        if not aggregated_data:
            return {}

        g = self.read_vars
        fragment_array_variables = g["fragment_array_variables"]
        variables = g["variables"]
        variable_attributes = g["variable_attributes"]

        # Loop round aggregation instruction terms
        out = {}
        for x in self._parse_x(
            ncvar,
            aggregated_data,
            keys_are_variables=True,
        ):
            term, term_ncvar = tuple(x.items())[0]
            term_ncvar = term_ncvar[0]
            out[term] = term_ncvar

            if term_ncvar in fragment_array_variables:
                # We've already processed this term
                continue

            attributes = variable_attributes[term_ncvar]
            array = netcdf_indexer(
                variables[term_ncvar],
                mask=True,
                unpack=True,
                always_masked_array=False,
                orthogonal_indexing=False,
                attributes=attributes,
                copy=False,
            )
            fragment_array_variables[term_ncvar] = array[...]

        g["parsed_aggregated_data"][ncvar] = out
        return out

    @classmethod
    def is_zarr(cls, path):
        """Whether or not a directory contains a Zarr dataset.

        Zarr v2 and v3 are supported.

        .. versionadded:: (cfdm) 1.12.2.0

        :Parameters:

            path: `str`
                A directory pathname.

        :Returns:

            `bool`
                `True` if *path* contains a Zarr dataset, otherwise
                `False`.

        """
        return (
            isfile(join(path, "zarr.json"))  # v3
            or isfile(join(path, ".zgroup"))  # v2
            or isfile(join(path, ".zarray"))  # v2
        )

    def _create_quantization(self, ncvar):
        """Create quantization metadata.

        .. versionadded:: (cfdm) 1.12.2.0

        :Parameters:

            ncvar: `str`
                The netCDF name of the quantization container
                variable.

        :Returns:

            `Quantization`
                The Quantization metadata.

        """
        q = self.implementation.initialise_Quantization(
            parameters=self.read_vars["variable_attributes"][ncvar].copy(),
            copy=False,
        )
        self.implementation.nc_set_variable(q, ncvar)
        return q

    def _set_quantization(self, parent, ncvar):
        """Set a quantization metadata on a construct.

        .. versionadded:: (cfdm) 1.12.2.0

        :Parameters:

            parent:
                The construct that might be quantized.

            ncvar: `str`
                The netCDF name of the quantization container
                variable.

        :Returns:

            `None`ppp

        """
        g = self.read_vars

        q = g["quantization"].get(ncvar)
        if q is None:
            # No quantization for this construct
            return

        # Delete the parent's quantization properties, moving them to
        # the Quantization component as appropriate.
        q = q.copy()

        attributes = g["variable_attributes"][ncvar]
        self.implementation.del_property(parent, "quantization", None)

        for attr in set(CF_QUANTIZATION_PARAMETERS.values()) | set(
            NETCDF_QUANTIZATION_PARAMETERS.values()
        ):
            value = attributes.get(attr, None)
            if value is not None:
                self.implementation.set_parameter(q, attr, value, copy=False)
                self.implementation.del_property(parent, attr, None)

        # Set the Quantization metadata
        self.implementation.set_quantization(parent, q, copy=False)
