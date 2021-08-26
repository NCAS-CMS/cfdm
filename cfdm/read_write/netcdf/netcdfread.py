import logging
import operator
import os
import re
import struct
import subprocess
import tempfile
from ast import literal_eval
from collections import OrderedDict
from copy import deepcopy
from distutils.version import LooseVersion
from functools import reduce

import netCDF4
import netcdf_flattener
import numpy

from ...decorators import _manage_log_level_via_verbosity
from ...functions import is_log_level_debug
from .. import IORead

logger = logging.getLogger(__name__)

_cached_temporary_files = {}

_flattener_separator = netcdf_flattener._Flattener._Flattener__new_separator


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
        (e.g. ocean_sigma_coordinate').

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
            "latitude_longitude": (
                "latitude",
                "longitude",
            ),
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

    def _is_unreferenced(self, ncvar):
        """True if a netCDF variable is not referenced by another.

        Return True if the netCDF variable is not referenced by any
        other netCDF variable.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `_reference`

        :Parameters:

            ncvar: `str`
                The netCDF variable name.

        :Returns:

            `bool`

        **Examples:**

        >>> x = r._is_unreferenced('tas')

        """
        return self.read_vars["references"].get(ncvar, 0) <= 0

    def _reference(self, ncvar, referencing_ncvar):
        """Increment by one the reference count to a netCDF variable.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: _is_unreferenced

        :Parameters:

            ncvar: `str`
                The netCDF variable name.

            referencing_ncvar: `str`
                The netCDF name of the the variable that is doing the
                referencing.

                .. versionaddedd:: (cfdm) 1.8.6.0

        :Returns:

            `int`
                The new reference count.

        **Examples:**

        >>> r._reference('longitude')

        """
        g = self.read_vars

        count = g["references"].setdefault(ncvar, 0)
        count += 1
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

        **Examples:**

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
                If False then do not flatten a grouped file. Ignored if
                the file has no groups.

                .. versionadded:: (cfdm) 1.8.6

        :Returns:

            `netCDF4.Dataset`
                A `netCDF4.Dataset` object for the file.

        **Examples:**

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

        Note that the file type is determined by inspecting the file's
        contents and any file suffix is not not considered.

        :Parameters:

            filename: `str`
                The name of the file.

        :Returns:

            `bool`
                `True` if the file is netCDF, otherwise `False`

        **Examples:**

        >>> {{package}}.{{class}}.is_netcdf_file('file.nc')
        True

        """
        # Assume that URLs are in netCDF format
        if filename.startswith("http://"):
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

        .. versionaddedd:: 1.7.8

        :Parameters:

            filename: `str`
                The name of the file.

        :Returns:

            `bool`
                `True` if the file is CDL, otherwise `False`

        **Examples:**

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

                if line.startswith("netcdf "):
                    cdl = True
            except UnicodeDecodeError:
                pass

        try:
            fh.close()
        except Exception:
            pass

        return cdl

    def default_netCDF_fill_value(self, ncvar):
        """The default netCDF fill value for a variable.

        :Parameters:

            ncvar: `str`
                The netCDF variable name of the variable.

        :Returns:

                The default fill value for the netCDF variable.

        **Examples:**

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
            "new_dimensions": {},
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
            # Domains
            # --------------------------------------------------------
            "domain": bool(domain),
        }

        g = self.read_vars

        # Set versions
        for version in ("1.6", "1.7", "1.8", "1.9"):
            g["version"][version] = LooseVersion(version)

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

        if os.path.isdir(filename):
            raise IOError(f"Can't read directory {filename}")

        if not os.path.isfile(filename):
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
        # Find the CF version for the file
        # ------------------------------------------------------------
        Conventions = g["global_attributes"].get("Conventions", "")

        all_conventions = re.split(",", Conventions)
        if all_conventions[0] == Conventions:
            all_conventions = re.split(r"\s+", Conventions)

        file_version = None
        for c in all_conventions:
            if not re.match(r"^CF-\d", c):
                continue

            file_version = re.sub("^CF-", "", c)

        if not file_version:
            if default_version is not None:
                # Assume the default version provided by the user
                file_version = default_version
            else:
                # Assume the file has the same version of the CFDM
                # implementation
                file_version = self.implementation.get_cf_version()

        g["file_version"] = LooseVersion(file_version)

        # Set minimum/maximum versions
        for vn in ("1.6", "1.7", "1.8", "1.9"):
            g["CF>=" + vn] = g["file_version"] >= g["version"][vn]

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
                f"    netCDF dimensions: {internal_dimension_sizes}"
            )  # pragma: no cover

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

        # Now that all of the variables have been scanned, customize
        # the read parameters.
        self._customize_read_vars()

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

        all_fields_or_domains = OrderedDict()
        for ncvar in g["variables"]:
            if ncvar not in g["do_not_create_field"]:
                field_or_domain = self._create_field_or_domain(
                    ncvar, domain=g["domain"]
                )
                if field_or_domain is not None:
                    all_fields_or_domains[ncvar] = field_or_domain

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
        fields_or_domains = OrderedDict()
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
            "    Referenced netCDF variables:\n        "
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

        **Examples:**

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

    def _customize_read_vars(self):
        """Customize the read parameters.

        This method is primarily aimed at providing a customization
        entry point for subclasses.

        .. versionadded:: (cfdm) 1.7.3

        """
        pass

    def _get_variables_from_external_files(self, netcdf_external_variables):
        """Get external variables from external files.

        ..versionadded:: (cfdm) 1.7.0

        :Parameters:

            netcdf_external_variables: `str`
                The un-parsed netCDF external_variables attribute in the
                parent file.

                *Parmaeter example:*
                  ``external_variables='areacello'``

        :Returns:

            `None`

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
            "        netCDF attributes: {attributes[geometry_ncvar]}"
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
                array=numpy.ones((size,), dtype="int32"), copy=False
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
            nc = self._create_NodeCount(ncvar=node_count)
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
        base = element_dimension
        n = 0
        while (
            element_dimension in g["internal_dimension_sizes"]
            or element_dimension in g["new_dimensions"]
            or element_dimension in g["variables"]
        ):
            n += 1
            element_dimension = f"{base}_{n}"

        g["new_dimensions"][element_dimension] = element_dimension_size

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

        (_, count) = numpy.unique(index.data.array, return_counts=True)

        # The number of elements per instance. For the instances array
        # example above, the elements_per_instance array is [7, 5, 7].
        elements_per_instance = count  # self._create_Data(array=count)

        instance_dimension_size = g["internal_dimension_sizes"][
            instance_dimension
        ]
        element_dimension_size = int(elements_per_instance.max())

        base = element_dimension
        n = 0
        while (
            element_dimension in g["internal_dimension_sizes"]
            or element_dimension in g["new_dimensions"]
            or element_dimension in g["variables"]
        ):
            n += 1
            element_dimension = f"{base}_{n}"

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

        g["new_dimensions"][element_dimension] = element_dimension_size

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
                The external variable names, less those which are also netCDF
                variables in the file.

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
                ncvar, message = self._check_missing_variable(
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
                        ncvar, message = self._check_missing_variable(
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

    def _check_missing_variable(self, ncvar, message0):
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

    def _create_field_or_domain(self, field_ncvar, domain=False):
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

        :Returns:

        Field or Domain construct

        """
        g = self.read_vars

        field = not domain
        if field:
            construct_type = "Field"
        else:
            construct_type = "Domain"

        # Reset the dimensions of a domain variable
        g["domain_ncdimensions"] = {}

        # Reset 'domain_ancillary_key'
        g["domain_ancillary_key"] = {}

        dimensions = g["variable_dimensions"][field_ncvar]
        g["dataset_compliance"][field_ncvar] = {
            "CF version": self.implementation.get_cf_version(),
            "dimensions": dimensions,
            "non-compliance": {},
        }

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

                unpacked_dtype = numpy.result_type(*values)

        # Initialise node_coordinates_as_bounds
        g["node_coordinates_as_bounds"] = set()

        # ------------------------------------------------------------
        # Initialize the field/domain
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

        # Map netCDF dimension names to domain axis names.
        #
        # For example: {'lat': 'dim0', 'time': 'dim1'}
        ncdim_to_axis = {}
        g["ncdim_to_axis"] = ncdim_to_axis

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
            if has_dimensions_attr and ndim < 1:
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
            if not g["CF>=1.9"] or not has_dimensions_attr or ndim >= 1:
                # ----------------------------------------------------
                # This netCDF variable is not scalar, or does not have
                # a 'dimensions' attribute. Therefore it is not a
                # domain variable and is to be ignored. CF>=1.9
                # (Introduced at v1.9.0.0)
                # ----------------------------------------------------
                logger.info(
                    "        {field_ncvar} is not a domain variable"
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
                    f"        [a] Inserting {domain_axis.__class__.__name__} sith size {size}"
                )  # pragma: no cover
                axis = self.implementation.set_domain_axis(
                    field=f, construct=domain_axis, copy=False
                )

                logger.detail(
                    f"        [b] Inserting {coord.__class__.__name__}{method}"
                )  # pragma: no cover
                dim = self.implementation.set_dimension_coordinate(
                    field=f, construct=coord, axes=[axis], copy=False
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
                if ncdim in g["new_dimensions"]:
                    size = g["new_dimensions"][ncdim]
                else:
                    size = g["internal_dimension_sizes"][ncdim]

                domain_axis = self._create_domain_axis(size, ncdim)
                logger.detail(
                    f"        [c] Inserting {domain_axis.__class__.__name__} with size {size}"
                )  # pragma: no cover
                axis = self.implementation.set_domain_axis(
                    field=f, construct=domain_axis, copy=False
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

        # ------------------------------------------------------------
        # Add the data to the field
        # ------------------------------------------------------------
        if field:
            data = self._create_data(
                field_ncvar, f, unpacked_dtype=unpacked_dtype
            )

            logger.detail(
                "        [d] Inserting {data.__class__.__name__}{data.shape}"
            )  # pragma: no cover

            self.implementation.set_data(f, data, axes=data_axes, copy=False)

        # ------------------------------------------------------------
        # Add scalar dimension coordinates and auxiliary coordinates
        # to the field/domain
        # ------------------------------------------------------------
        coordinates = self.implementation.del_property(f, "coordinates", None)

        if coordinates is not None:
            parsed_coordinates = self._split_string_by_white_space(
                field_ncvar, coordinates, variables=True
            )

            for ncvar in parsed_coordinates:
                # Skip dimension coordinates which are in the list
                if ncvar in field_ncdimensions:
                    continue

                cf_compliant = self._check_auxiliary_or_scalar_coordinate(
                    field_ncvar, ncvar, coordinates
                )
                if not cf_compliant:
                    continue

                # Set dimensions for this variable
                dimensions = self._get_domain_axes(ncvar)

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
                        # String valued scalar coordinate. T turn it
                        # into a 1-d auxiliary coordinate construct.
                        domain_axis = self._create_domain_axis(1)
                        logger.detail(
                            "        [d] Inserting {domain_axis.__class__.__name__} with size 1"
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
                        f"        [e] Inserting {domain_axis.__class__.__name__} with size {size}"
                    )  # pragma: no cover
                    axis = self.implementation.set_domain_axis(
                        field=f, construct=domain_axis, copy=False
                    )

                    logger.detail(
                        f"        [e] Inserting {coord.__class__.__name__}"
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
                        f"        [f] Inserting {coord.__class__.__name__}"
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
                        field_ncvar=field_ncvar,
                        ncvar=None,
                        f=f,
                        bounds_ncvar=node_ncvar,
                        nodes=True,
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
        # Add coordinate reference constructs from formula_terms
        # properties
        # ------------------------------------------------------------
        for key, coord in self.implementation.get_coordinates(field=f).items():
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
                    field=f, construct=domain_anc, axes=axes, copy=False
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
                field=f, construct=coordinate_reference, copy=False
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
                                field=f
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
                                    f"        [k] Inserting {datum.__class__.__name__} into {vcr.__class__.__name__}"
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
                            field=f, construct=coordref, copy=False
                        )

                        logger.detail(
                            f"        [l] Inserting {coordref.__class__.__name__}"
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
                        field=f, construct=cell, axes=axes, copy=False
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
                    f"        [i] Inserting {method!r} {cell_method.__class__.__name__}"
                )  # pragma: no cover

                self.implementation.set_cell_method(
                    field=f, construct=cell_method, copy=False
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
                            field=f, construct=field_anc, axes=axes, copy=False
                        )
                        self._reference(ncvar, field_ncvar)

                        ncvar_to_key[ncvar] = key

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
            return ncvar, " (found by proximal serach)"

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

        **Examples:**

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

        **Examples:**

            >>> n._is_char('regions')
            True

        """
        datatype = self.read_vars["variables"][ncvar].dtype
        return datatype != str and datatype.kind in "SU"

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
        field_ncvar,
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

            field_ncvar: `str`
                The netCDF variable name of the field.

                *Parameter example:*
                  ``field_ncvar='tas'``

            ncvar: `str`
                The netCDF variable name of the field component that has
                the problem.

                *Parameter example:*
                  ``field_ncvar='rotated_latitude_longitude'``

            message: (`str`, `str`), optional

            attribute: `str`, optional
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

        d = {
            "code": code,
            "attribute": attribute,
            "reason": message,
        }

        if dimensions is not None:
            d["dimensions"] = dimensions

        if variable is None:
            variable = ncvar

        g["dataset_compliance"][field_ncvar]["non-compliance"].setdefault(
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

    def _get_domain_axes(self, ncvar, allow_external=False):
        """Find a domain axis identifier for the variable's dimensions.

        Return the domain axis identifiers that correspond to a
        netCDF variable's netCDF dimensions.

        .. versionadded:: (cfdm) 1.7.0

        :Parameter:

            ncvar: `str`
                The netCDF variable name.

            allow_external: `bool`
                If True and *ncvar* is an external variable then return an
                empty list.

        :Returns:

            `list`

        **Examples:**

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
            ncdimensions = self._ncdimensions(ncvar)

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
        self, field_ncvar, ncvar, f, bounds_ncvar=None, nodes=False
    ):
        """Create an auxiliary coordinate construct.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            field_ncvar: `str`
                The netCDF variable name of the parent field construct.

            ncvar: `str` or `None`
                The netCDF name of the variable. See the *nodes*
                parameter.

            field: field construct
                The parent field construct.

            bounds_ncvar: `str`, optional
                The netCDF variable name of the coordinate bounds.

            nodes: `bool`
                Set to True only if and only if the coordinate construct
                is to be created with only bounds from a node coordinates
                variable, whose netCDF name is given by *bounds_ncvar*. In
                this case *ncvar* must be `None`.

        :Returns:

                The auxiliary coordinate construct.

        """
        return self._create_bounded_construct(
            field_ncvar=field_ncvar,
            ncvar=ncvar,
            f=f,
            auxiliary=True,
            bounds_ncvar=bounds_ncvar,
            nodes=nodes,
        )

    def _create_dimension_coordinate(
        self, field_ncvar, ncvar, f, bounds_ncvar=None
    ):
        """Create a dimension coordinate construct.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            field_ncvar: `str`
                The netCDF variable name of the parent field construct.

            ncvar: `str`
                The netCDF name of the variable.

            field: field construct
                The parent field construct.

            bounds_ncvar: `str`, optional
                The netCDF variable name of the coordinate bounds.

        :Returns:

                The dimension coordinate construct.

        """
        return self._create_bounded_construct(
            field_ncvar=field_ncvar,
            ncvar=ncvar,
            f=f,
            dimension=True,
            bounds_ncvar=bounds_ncvar,
        )

    def _create_domain_ancillary(
        self, field_ncvar, ncvar, f, bounds_ncvar=None
    ):
        """Create a domain ancillary construct object.

        .. versionadded:: (cfdm) 1.7.0

        :Returns:

            The domain ancillary construct.

        """
        return self._create_bounded_construct(
            field_ncvar=field_ncvar,
            ncvar=ncvar,
            f=f,
            domain_ancillary=True,
            bounds_ncvar=bounds_ncvar,
        )

    def _create_bounded_construct(
        self,
        field_ncvar,
        ncvar,
        f,
        dimension=False,
        auxiliary=False,
        domain_ancillary=False,
        bounds_ncvar=None,
        has_coordinates=True,
        nodes=False,
    ):
        """Create a variable which might have bounds.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            ncvar: `str` or `None`
                The netCDF name of the variable. See the *nodes*
                parameter.

            f: `Field`
                The parent field construct.

            dimension: `bool`, optional
                If True then a dimension coordinate construct is created.

            auxiliary: `bool`, optional
                If True then an auxiliary coordinate consrtruct is created.

            domain_ancillary: `bool`, optional
                If True then a domain ancillary construct is created.

            nodes: `bool`
                Set to True only if and only if the coordinate construct
                is to be created with only bounds from a node coordinates
                variable, whose netCDF name is given by *bounds_ncvar*. In
                this case *ncvar* must be `None`.

        :Returns:

            `DimensionCoordinate` or `AuxiliaryCoordinate` or `DomainAncillary`
                The new construct.

        """
        g = self.read_vars
        nc = g["nc"]

        g["bounds"][field_ncvar] = {}
        g["coordinates"][field_ncvar] = []

        if ncvar is not None:
            properties = g["variable_attributes"][ncvar].copy()
            properties.pop("formula_terms", None)
        else:
            properties = {}

        # ------------------------------------------------------------
        # Look for a geometry container
        # ------------------------------------------------------------
        geometry = self._get_geometry(field_ncvar)

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
        elif nodes:
            attribute = "nodes"

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
            data = self._create_data(ncvar, c)
            self.implementation.set_data(c, data, copy=False)

        # ------------------------------------------------------------
        # Add any bounds
        # ------------------------------------------------------------
        if bounds_ncvar:
            if g["has_groups"]:
                # Replace a flattened name with an absolute name
                bounds_ncvar = g["flattener_variables"].get(
                    bounds_ncvar, bounds_ncvar
                )

            if attribute == "nodes":
                # Check geomerty node coordinate boounds
                cf_compliant = self._check_geometry_node_coordinates(
                    field_ncvar, bounds_ncvar, geometry
                )
            else:
                # Check "normal" boounds
                cf_compliant = self._check_bounds(
                    field_ncvar, ncvar, attribute, bounds_ncvar
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
                bounds_ncvar, bounds, parent_ncvar=ncvar
            )

            self.implementation.set_data(bounds, bounds_data, copy=False)

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
                g["bounds"][field_ncvar][ncvar] = bounds_ncvar

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

                # Add a node count variable
                nc = geometry.get("node_count")
                if nc is not None:
                    self.implementation.set_node_count(parent=c, node_count=nc)

                # Add a part node count variable
                pnc = geometry.get("part_node_count")
                if pnc is not None:
                    self.implementation.set_part_node_count(
                        parent=c, part_node_count=pnc
                    )

                # Add an interior ring variable
                interior_ring = geometry.get("interior_ring")
                if interior_ring is not None:
                    self.implementation.set_interior_ring(
                        parent=c, interior_ring=interior_ring
                    )

        # Store the netCDF variable name
        self.implementation.nc_set_variable(c, ncvar)

        if not domain_ancillary:
            g["coordinates"][field_ncvar].append(ncvar)

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

        return cell_measure

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

        data = self._create_data(ncvar, variable, uncompress_override=True)

        self.implementation.set_data(variable, data, copy=False)

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

                Index variable instance

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
        data = self._create_data(ncvar, variable, uncompress_override=True)
        self.implementation.set_data(variable, data, copy=False)

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
        # Initialise the list variable
        variable = self.implementation.initialise_List()

        # Store the netCDF variable name
        self.implementation.nc_set_variable(variable, ncvar)

        properties = self.read_vars["variable_attributes"][ncvar]
        properties.pop("compress", None)
        self.implementation.set_properties(variable, properties)

        if not self.read_vars["mask"]:
            self._set_default_FillValue(variable, ncvar)

        data = self._create_data(ncvar, variable, uncompress_override=True)
        self.implementation.set_data(variable, data, copy=False)

        return variable

    def _create_NodeCount(self, ncvar):
        """Create a node count variable.

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

        # Initialise the interior ring variable
        variable = self.implementation.initialise_NodeCount()

        # Store the netCDF variable name
        self.implementation.nc_set_variable(variable, ncvar)

        properties = g["variable_attributes"][ncvar]
        self.implementation.set_properties(variable, properties)

        if not g["mask"]:
            self._set_default_FillValue(variable, ncvar)

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

        # Initialise the interior ring variable
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

    def _create_netcdfarray(self, ncvar, unpacked_dtype=False):
        """Set the Data attribute of a variable.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            ncvar: `str`

            unpacked_dtype: `False` or `numpy.dtype`, optional

        :Returns:

            `NetCDFArray`

        """
        g = self.read_vars

        if g["has_groups"]:
            # Get the variable from the original grouped file. This is
            # primarily so that unlimited dimensions don't come out
            # with size 0 (v1.8.8.1)
            group, name = self._netCDF4_group(
                g["variable_grouped_dataset"][ncvar], ncvar
            )
            #            path = ncvar.split('/')
            #            for group_name in path[1:-1]:
            #                group = group[group_name]
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
            dtype = numpy.result_type(dtype, unpacked_dtype)

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
            dtype = numpy.dtype(f"S{strlen}")

        filename = g["variable_filename"][ncvar]

        # Find the group that this variable is in. The group will be
        # None if the variable is in the root group.
        if g["has_groups"]:
            group = g["variable_groups"].get(ncvar, ())
            if group:
                # Make sure that we use the variable name without any
                # group structure prepended to it
                ncvar = g["variable_basename"][ncvar]
        else:
            # This variable is in the root group
            group = None

            # TODO: think using e.g. '/forecasts/model1' has the value for
            # nc_set_variable. What about nc_set_dimension?

        return self.implementation.initialise_NetCDFArray(
            filename=filename,
            ncvar=ncvar,
            group=group,
            dtype=dtype,
            ndim=ndim,
            shape=shape,
            size=size,
            mask=g["mask"],
        )

    def _create_data(
        self,
        ncvar,
        construct=None,
        unpacked_dtype=False,
        uncompress_override=None,
        parent_ncvar=None,
    ):
        """Create a data object (Data).

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            ncvar: `str`
                The name of the netCDF variable that contains the data.

            construct: optional

            unpacked_dtype: `False` or `numpy.dtype`, optional

            uncompress_override: `bool`, optional

        :Returns:

            `Data`

        """
        g = self.read_vars

        array = self._create_netcdfarray(ncvar, unpacked_dtype=unpacked_dtype)
        if array is None:
            return None

        units = g["variable_attributes"][ncvar].get("units", None)
        calendar = g["variable_attributes"][ncvar].get("calendar", None)

        if parent_ncvar is not None:
            if units is None:
                units = g["variable_attributes"][parent_ncvar].get(
                    "units", None
                )

            if calendar is None:
                calendar = g["variable_attributes"][parent_ncvar].get(
                    "calendar", None
                )

        compression = g["compression"]

        dimensions = g["variable_dimensions"][ncvar]

        if (
            (uncompress_override is not None and uncompress_override)
            or not compression
            or not set(compression).intersection(dimensions)
        ):
            # --------------------------------------------------------
            # The array is not compressed (or not to be uncompressed)
            # --------------------------------------------------------
            pass

        else:
            # --------------------------------------------------------
            # The array is compressed
            # --------------------------------------------------------
            # Loop round the dimensions of data variable, as they
            # appear in the netCDF file
            for ncdim in dimensions:
                if ncdim in compression:
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
                        # --------------------------------------------
                        # Compression by gathering. Note the
                        # uncompressed dimensions exist as internal
                        # dimensions.
                        # --------------------------------------------
                        c = c["gathered"]
                        uncompressed_shape = tuple(
                            [
                                g["internal_dimension_sizes"][dim]
                                for dim in self._ncdimensions(ncvar)
                            ]
                        )
                        compressed_dimension = g["variable_dimensions"][
                            ncvar
                        ].index(c["sample_dimension"])
                        array = self._create_gathered_array(
                            gathered_array=self._create_Data(array),
                            uncompressed_shape=uncompressed_shape,
                            compressed_dimension=compressed_dimension,
                            list_variable=c["list_variable"],
                        )
                    elif "ragged_indexed_contiguous" in c:
                        # --------------------------------------------
                        # Contiguous indexed ragged array. Check this
                        # before ragged_indexed and ragged_contiguous
                        # because both of these will exist for an
                        # indexed and contiguous array.
                        # --------------------------------------------
                        c = c["ragged_indexed_contiguous"]

                        i = dimensions.index(ncdim)
                        if i != 0:
                            raise ValueError(
                                "Data can only be created when the netCDF "
                                "dimension spanned by the data variable is the "
                                "left-most dimension in the ragged array."
                            )

                        uncompressed_shape = list(array.shape)
                        uncompressed_shape[i : i + 1] = [
                            c["instance_dimension_size"],
                            c["element_dimension_1_size"],
                            c["element_dimension_2_size"],
                        ]
                        uncompressed_shape = tuple(uncompressed_shape)

                        array = self._create_ragged_indexed_contiguous_array(
                            ragged_indexed_contiguous_array=self._create_Data(
                                array
                            ),
                            uncompressed_shape=uncompressed_shape,
                            count_variable=c["count_variable"],
                            index_variable=c["index_variable"],
                        )

                    elif "ragged_contiguous" in c:
                        # --------------------------------------------
                        # Contiguous ragged array
                        # --------------------------------------------
                        c = c["ragged_contiguous"]

                        i = dimensions.index(ncdim)
                        if i != 0:
                            raise ValueError(
                                "Data can only be created when the netCDF "
                                "dimension spanned by the data variable is the "
                                "left-most dimension in the ragged array."
                            )

                        uncompressed_shape = list(array.shape)
                        uncompressed_shape[i : i + 1] = [
                            c["instance_dimension_size"],
                            c["element_dimension_size"],
                        ]
                        uncompressed_shape = tuple(uncompressed_shape)

                        array = self._create_ragged_contiguous_array(
                            ragged_contiguous_array=self._create_Data(array),
                            uncompressed_shape=uncompressed_shape,
                            count_variable=c["count_variable"],
                        )
                    elif "ragged_indexed" in c:
                        # --------------------------------------------
                        # Indexed ragged array
                        # --------------------------------------------
                        c = c["ragged_indexed"]

                        i = dimensions.index(ncdim)
                        if i != 0:
                            raise ValueError(
                                "Data can only be created when the netCDF "
                                "dimension spanned by the data variable is the "
                                "left-most dimension in the ragged array."
                            )

                        uncompressed_shape = list(array.shape)
                        uncompressed_shape[i : i + 1] = [
                            c["instance_dimension_size"],
                            c["element_dimension_size"],
                        ]
                        uncompressed_shape = tuple(uncompressed_shape)

                        array = self._create_ragged_indexed_array(
                            ragged_indexed_array=self._create_Data(array),
                            uncompressed_shape=uncompressed_shape,
                            index_variable=c["index_variable"],
                        )
                    else:
                        raise ValueError(
                            f"Bad compression vibes. c.keys()={list(c.keys())}"
                        )

        return self._create_Data(array, units=units, calendar=calendar)

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
        # Create a field ancillary object
        field_ancillary = self.implementation.initialise_FieldAncillary()

        # Insert properties
        self.implementation.set_properties(
            field_ancillary,
            self.read_vars["variable_attributes"][ncvar],
            copy=True,
        )

        if not self.read_vars["mask"]:
            self._set_default_FillValue(field_ancillary, ncvar)

        # Insert data
        data = self._create_data(ncvar, field_ancillary)
        self.implementation.set_data(field_ancillary, data, copy=False)

        # Store the netCDF variable name
        self.implementation.nc_set_variable(field_ancillary, ncvar)

        return field_ancillary

    def _parse_cell_methods(self, cell_methods_string, field_ncvar=None):
        """Parse a CF cell_methods string.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            cell_methods_string: `str`
                A CF cell methods string.

        :Returns:

            `list` of `dict`

        **Examples:**

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

    def _ncdimensions(self, ncvar, ncdimensions=None):
        """Lists the netCDF dimensions associated with a variable.

            If the variable has been compressed then the *implied
            uncompressed* dimensions are returned.

            .. versionadded:: (cfdm) 1.7.0

            :Parameters:

                ncvar: `str`
                    The netCDF variable name.

            ncdimensions: sequence of `str`, optional
                Use these netCDF dimensions, rather than retrieving them
                from the netCDF variable itself. This allows the
                dimensions of a domain variable to be parsed. Note that
                this only parameter only needs to be used once because the
                parsed domain dimensions are automatically stored in
                `self.read_var['domain_ncdimensions'][ncvar]`.

                .. versionadded:: (cfdm) 1.9.0.0

        :Returns:


                `list`
                    The list of netCDF dimension names spanned by the netCDF
                    variable.

            **Examples:**

            >>> n._ncdimensions('humidity')
            ['time', 'lat', 'lon']

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
            for ncdim in ncdimensions:
                if ncdim in compression:
                    c = compression[ncdim]

                    if ncvar not in c.get("netCDF_variables", (ncvar,)):
                        # This variable is not compressed, even though
                        # it spans a dimension that is compressed for
                        # some other variables For example, this sort
                        # of situation may arise with simple
                        # geometries.
                        continue

                    i = ncdimensions.index(ncdim)

                    if "gathered" in c:
                        # Compression by gathering
                        ncdimensions[i : i + 1] = c["gathered"][
                            "implied_ncdimensions"
                        ]
                    elif "ragged_indexed_contiguous" in c:
                        # Indexed contiguous ragged array.
                        #
                        # Check this before ragged_indexed and
                        # ragged_contiguous because both of these will
                        # exist for an array that is both indexed and
                        # contiguous.
                        ncdimensions[i : i + 1] = c[
                            "ragged_indexed_contiguous"
                        ]["implied_ncdimensions"]
                    elif "ragged_contiguous" in c:
                        # Contiguous ragged array
                        ncdimensions[i : i + 1] = c["ragged_contiguous"][
                            "implied_ncdimensions"
                        ]
                    elif "ragged_indexed" in c:
                        # Indexed ragged array
                        ncdimensions[i : i + 1] = c["ragged_indexed"][
                            "implied_ncdimensions"
                        ]

                    break

        out = list(map(str, ncdimensions))

        if domain:
            # Record the domain variable dimensions
            g["domain_ncdimensions"][ncvar] = out

        return out

    def _create_gathered_array(
        self,
        gathered_array=None,
        uncompressed_shape=None,
        compressed_dimension=None,
        list_variable=None,
    ):
        """Creates Data for a compressed-by-gathering netCDF variable.

        Specifically, a `Data` object is created.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            gathered_array: `NetCDFArray`

            list_variable: `List`

        :Returns:

            `Data`

        """
        uncompressed_ndim = len(uncompressed_shape)
        uncompressed_size = int(reduce(operator.mul, uncompressed_shape, 1))

        return self.implementation.initialise_GatheredArray(
            compressed_array=gathered_array,
            ndim=uncompressed_ndim,
            shape=uncompressed_shape,
            size=uncompressed_size,
            compressed_dimension=compressed_dimension,
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

            `Data`

        """
        uncompressed_ndim = len(uncompressed_shape)
        uncompressed_size = int(reduce(operator.mul, uncompressed_shape, 1))

        return self.implementation.initialise_RaggedContiguousArray(
            compressed_array=ragged_contiguous_array,
            ndim=uncompressed_ndim,
            shape=uncompressed_shape,
            size=uncompressed_size,
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

            `Data`

        """
        uncompressed_ndim = len(uncompressed_shape)
        uncompressed_size = int(reduce(operator.mul, uncompressed_shape, 1))

        return self.implementation.initialise_RaggedIndexedArray(
            compressed_array=ragged_indexed_array,
            ndim=uncompressed_ndim,
            shape=uncompressed_shape,
            size=uncompressed_size,
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

            `Data`

        """
        uncompressed_ndim = len(uncompressed_shape)
        uncompressed_size = int(reduce(operator.mul, uncompressed_shape, 1))

        return self.implementation.initialise_RaggedIndexedContiguousArray(
            compressed_array=ragged_indexed_contiguous_array,
            ndim=uncompressed_ndim,
            shape=uncompressed_shape,
            size=uncompressed_size,
            count_variable=count_variable,
            index_variable=index_variable,
        )

    def _create_Data(
        self, array=None, units=None, calendar=None, ncvar=None, **kwargs
    ):
        """Create a Data object.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            ncvar: `str`
                The netCDF variable from which to get units and calendar.

        """
        data = self.implementation.initialise_Data(
            array=array, units=units, calendar=calendar, copy=False, **kwargs
        )

        return data

    def _copy_construct(self, construct_type, field_ncvar, ncvar):
        """Return a copy of an existing construct.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            construct_type: `str`
                E.g. 'dimension_coordinate'

            field_ncvar: `str
                The netCDF variable name of the field that will contain the
                copy of the construct.

            ncvar: `str`
                The netCDF variable name of the construct.

        :Returns:

                A copy of the construct.

        """
        g = self.read_vars

        component_report = g["component_report"].get(ncvar)

        if component_report is not None:
            for var, report in component_report.items():
                g["dataset_compliance"][field_ncvar][
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
        self, field_ncvar, parent_ncvar, attribute, bounds_ncvar
    ):
        """Check a bounds variable spans the correct dimensions.

        .. versionadded:: (cfdm) 1.7.0

        Checks that

        * The bounds variable has exactly one more dimension than the
          parent variable

        * The bounds variable's dimensions, other than the trailing
          dimension are the same, and in the same order, as the parent
          variable's dimensions.

        :Parameters:

            nc: `netCDF4.Dataset`
                The netCDF dataset object.

            parent_ncvar: `str`
                The netCDF variable name of the parent variable.

            bounds_ncvar: `str`
                The netCDF variable name of the bounds.

        :Returns:

            `bool`

        """
        attribute = {parent_ncvar + ":" + attribute: bounds_ncvar}

        incorrect_dimensions = (
            "Bounds variable",
            "spans incorrect dimensions",
        )

        g = self.read_vars

        if bounds_ncvar not in g["internal_variables"]:
            bounds_ncvar, message = self._check_missing_variable(
                bounds_ncvar, "Bounds variable"
            )
            self._add_message(
                field_ncvar,
                bounds_ncvar,
                message=message,
                attribute=attribute,
                variable=parent_ncvar,
            )
            return False

        ok = True

        c_ncdims = self._ncdimensions(parent_ncvar)
        b_ncdims = self._ncdimensions(bounds_ncvar)

        if len(b_ncdims) == len(c_ncdims) + 1:
            if c_ncdims != b_ncdims[:-1]:
                self._add_message(
                    field_ncvar,
                    bounds_ncvar,
                    message=incorrect_dimensions,
                    attribute=attribute,
                    dimensions=g["variable_dimensions"][bounds_ncvar],
                    variable=parent_ncvar,
                )
                ok = False

        else:
            self._add_message(
                field_ncvar,
                bounds_ncvar,
                message=incorrect_dimensions,
                attribute=attribute,
                dimensions=g["variable_dimensions"][bounds_ncvar],
                variable=parent_ncvar,
            )
            ok = False

        return ok

    def _check_geometry_node_coordinates(
        self, field_ncvar, node_ncvar, geometry
    ):
        """Check a geometry node corodinate variable.

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
            node_ncvar, message = self._check_missing_variable(
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
            # file attribute
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

    def _check_geometry_attribute(self, field_ncvar, string, parsed_string):
        """Checks requirements.

        .. versionadded:: (cfdm) 1.8.0

        :Parameters:

            field_ncvar: `str`

            string: `str`
                The value of the netCDF geometry attribute.

            parsed_string: `list`

        :Returns:

            `bool`

        """
        attribute = {field_ncvar + ":geometry": string}

        incorrectly_formatted = (
            "geometry attribute",
            "is incorrectly formatted",
        )

        g = self.read_vars

        if len(parsed_string) != 1:
            self._add_message(
                field_ncvar,
                field_ncvar,
                message=incorrectly_formatted,
                attribute=attribute,
                conformance="?",
            )
            return False

        for ncvar in parsed_string:
            # Check that the variable exists in the file, or if not
            # that it is listed in the 'external_variables' global
            # file attribute
            if ncvar not in g["variables"]:
                ncvar, message = self._check_missing_variable(
                    ncvar, "Geometry variable"
                )
                self._add_message(
                    field_ncvar,
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
                    f"    Error processing netCDF variable {field_ncvar}: {d['reason']}"
                )  # pragma: no cover

            return False

        parent_dimensions = self._ncdimensions(field_ncvar)

        ok = True
        for ncvar in parsed_string:
            # Check that the variable exists in the file
            if ncvar not in g["internal_variables"]:
                ncvar, message = self._check_missing_variable(
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
            coord_ncvar, message = self._check_missing_variable(
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
            self._ncdimensions(coord_ncvar),
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
                grid_mapping_ncvar, message = self._check_missing_variable(
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
                    coord_ncvar, message = self._check_missing_variable(
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
                ncvar, message = self._check_missing_variable(
                    ncvar,
                    "Node coordinate variable",
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
                ncvar, message = self._check_missing_variable(
                    ncvar,
                    "Node count variable",
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
                ncvar, message = self._check_missing_variable(
                    ncvar,
                    "Part node count variable",
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
                ncvar, message = self._check_missing_variable(
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

    def _split_string_by_white_space(
        self, parent_ncvar, string, variables=False
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

        :Returns:

            `list`

        """
        if string is None:
            return []

        try:
            out = string.split()
        except AttributeError:
            return []
        else:
            if variables and out and self.read_vars["has_groups"]:
                mapping = self.read_vars["flattener_variables"]
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

    def _parse_x(self, parent_ncvar, string, keys_are_variables=False):
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

        .. versionadded:: 1.8.8.1

        :Parameters:

            nc: `netCDF4._netCDF4.Dataset` or `netCDF4._netCDF4.Group`

            name: `str`

        :Returns:

            `netCDF4._netCDF4.Dataset` or `netCDF4._netCDF4.Group`, `str`

        **Examples:**

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
