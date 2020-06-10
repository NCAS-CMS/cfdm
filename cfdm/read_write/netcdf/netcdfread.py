from __future__ import print_function
from builtins import (map, range, str)
from past.builtins import basestring

import logging
import operator
import os
import re
import struct
import subprocess
import tempfile

from ast               import literal_eval
from collections       import OrderedDict
from copy              import deepcopy
from distutils.version import LooseVersion
from functools         import reduce
from pprint            import pformat

import numpy
import netCDF4

from ...decorators import _manage_log_level_via_verbosity

from .. import IORead

from . import constants


_cached_temporary_files = {}

logger = logging.getLogger(__name__)


class NetCDFRead(IORead):
    '''
    '''
    _code0 = {
        # Physically meaningful and corresponding to constructs
        'Cell measures variable' : 100,
        'cell_measures attribute': 101,

        'Bounds variable'        : 200,
        'bounds attribute'       : 201,

        'Ancillary variable': 120,
        'ancillary_variables attribute': 121,

        'Formula terms variable': 130,
        'formula_terms attribute': 131,
        'Bounds formula terms variable': 132,
        'Bounds formula_terms attribute': 133,

        'Auxiliary/scalar coordinate variable': 140,
        'coordinates attribute': 141,

        'grid mapping variable': 150,
        'grid_mapping attribute' : 151,
        'Grid mapping coordinate variable': 152,

        'Cell method interval': 160,

        'External variable': 170,

        # Purely structural
        'Compressed dimension': 300,
        'compress attribute': 301,
        'Instance dimension':310,
        'instance_dimension attribute':311,
        'Count dimension': 320,
        'count_dimension attribute': 321,
    }

    _code1 = {
        'is incorrectly formatted': 2,
        'is not in file': 3,
        'spans incorrect dimensions': 4,
        'is not in file nor referenced by the external_variables global attribute': 5,
        'has incompatible terms': 6,
        'that spans the vertical dimension has no bounds': 7,
        'that does not span the vertical dimension is inconsistent with the formula_terms of the parametric coordinate variable': 8,
        'is not referenced in file': 9,
        'exists in the file': 10,
        'does not exist in file': 11,
        'exists in multiple external files': 12,
        'has incorrect size': 13,
        'is missing': 14,
        'is not used by data variable': 15,
        'not in node_coordinates': 16,
    }

    def cf_datum_parameters(self):
        '''Datum-defining parameters names
        '''
        return ('earth_radius',
                'geographic_crs_name',
                'geoid_name',
                'geopotential_datum_name',
                'horizontal_datum_name',
                'inverse_flattening',
                'longitude_of_prime_meridian',
                'prime_meridian_name',
                'reference_ellipsoid_name',
                'semi_major_axis',
                'semi_minor_axis',
                'towgs84',
        )

    def cf_coordinate_reference_coordinates(self):
        '''Mapping of each coordinate reference canonical name to the
    coordinates to which it applies. The coordinates are defined by
    their standard names.

    A coordinate reference canonical name is either the value of the
    grid_mapping_name attribute of a grid mapping variable
    (e.g. 'lambert_azimuthal_equal_area'), or the standard name of a
    vertical coordinate variable with a formula_terms attribute
    (e.g. ocean_sigma_coordinate').

        '''
        return {
            'albers_conical_equal_area'                  : ('projection_x_coordinate',
                                                            'projection_y_coordinate',
                                                            'latitude',
                                                            'longitude',),
            'azimuthal_equidistant'                      : ('projection_x_coordinate',
                                                            'projection_y_coordinate',
                                                            'latitude',
                                                            'longitude',),
            'geostationary'                              : ('projection_x_coordinate',
                                                            'projection_y_coordinate',
                                                            'latitude',
                                                            'longitude',),
            'lambert_azimuthal_equal_area'               : ('projection_x_coordinate',
                                                            'projection_y_coordinate',

                                                            'latitude',
                                                            'longitude',),
            'lambert_conformal_conic'                    : ('projection_x_coordinate',
                                                            'projection_y_coordinate',
                                                            'latitude',
                                                            'longitude',),
            'lambert_cylindrical_equal_area'             : ('projection_x_coordinate',
                                                            'projection_y_coordinate',
                                                            'latitude',
                                                            'longitude',),
            'latitude_longitude'                         : ('latitude',
                                                            'longitude',),
            'mercator'                                   : ('projection_x_coordinate',
                                                            'projection_y_coordinate',
                                                            'latitude',
                                                            'longitude',),
            'orthographic'                               : ('projection_x_coordinate',
                                                            'projection_y_coordinate',
                                                            'latitude',
                                                            'longitude',),
            'polar_stereographic'                        : ('projection_x_coordinate',
                                                            'projection_y_coordinate',
                                                            'latitude',
                                                            'longitude',),
            'rotated_latitude_longitude'                 : ('grid_latitude',
                                                            'grid_longitude',
                                                            'latitude',
                                                            'longitude',),
            'sinusoidal'                                 : ('projection_x_coordinate',
                                                            'projection_y_coordinate',
                                                            'latitude',
                                                            'longitude',),
            'stereographic'                              : ('projection_x_coordinate',
                                                            'projection_y_coordinate',
                                                            'latitude',
                                                            'longitude',),
            'transverse_mercator'                        : ('projection_x_coordinate',
                                                            'projection_y_coordinate',
                                                            'latitude',
                                                            'longitude',),
            'vertical_perspective'                       : ('projection_x_coordinate',
                                                            'projection_y_coordinate',
                                                            'latitude',
                                                            'longitude',),
            'atmosphere_ln_pressure_coordinate'          : ('atmosphere_ln_pressure_coordinate',),
            'atmosphere_sigma_coordinate'                : ('atmosphere_sigma_coordinate',),
            'atmosphere_hybrid_sigma_pressure_coordinate': ('atmosphere_hybrid_sigma_pressure_coordinate',),
            'atmosphere_hybrid_height_coordinate'        : ('atmosphere_hybrid_height_coordinate',),
            'atmosphere_sleve_coordinate'                : ('atmosphere_sleve_coordinate',),
            'ocean_sigma_coordinate'                     : ('ocean_sigma_coordinate',),
            'ocean_s_coordinate'                         : ('ocean_s_coordinate',),
            'ocean_sigma_z_coordinate'                   : ('ocean_sigma_z_coordinate',),
            'ocean_double_sigma_coordinate'              : ('ocean_double_sigma_coordinate',),
        }

    def _is_unreferenced(self, ncvar):
        '''Return True if the netCDF variable is not referenced by any other
    netCDF variable.

    :Parameters:

        ncvar: `str`
            The netCDF variable name.

    :Returns:

        `bool`

    **Examples:**

    >>> x = r._is_unreferenced('tas')

        '''
        return self.read_vars['references'].get(ncvar, 0) <= 0

    def _reference(self, ncvar):
        '''Increment by one the reference count to a netCDF variable.

    :Parameters:

        ncvar: `str`
            The netCDF variable name.

    :Returns:

        `int`
            The new reference count.

    **Examples:**

    >>> r._reference('longitude')

        '''
        count = self.read_vars['references'].setdefault(ncvar, 0)
        count += 1
        self.read_vars['references'][ncvar] = count
        return count

    def file_close(self):
        '''Close the netCDF files that have been read.

    :Returns:

        `None`

        '''
        for nc in self.read_vars['datasets']:
            nc.close()

    def file_open(self, filename):
        '''Open the netCDf file for reading.

    :Paramters:

        filename: `str`
            As for the *filename* parameter for initialising a
            `netCDF.Dataset` instance.

    :Returns:

        `netCDF4.Dataset`
            A `netCDF4.Dataset` object for the file.

        '''
        try:
            nc = netCDF4.Dataset(filename, 'r')
        except RuntimeError as error:
            raise RuntimeError("{}: {}".format(error, filename))

        return nc

    @classmethod
    def cdl_to_netcdf(cls, filename):
        '''TODO

        '''
        x = tempfile.NamedTemporaryFile(mode='wb', dir=tempfile.gettempdir(),
                                        prefix='cfdm_', suffix='.nc')
        tmpfile = x.name

        # ----------------------------------------------------------------
        # Need to cache the TemporaryFile object so that it doesn't get
        # deleted too soon
        # ----------------------------------------------------------------
        _cached_temporary_files[tmpfile] = x

        subprocess.run(['ncgen', '-v3', '-o', tmpfile, filename], check=True)

        return tmpfile

    @classmethod
    def is_netcdf_file(cls, filename):
        '''Return `True` if the file is a netCDF file.

    Note that the file type is determined by inspecting the file's
    contents and any file suffix is not not considered.

    :Parameters:

        filename: `str`
            The name of the file.

    :Returns:

        `bool`
            `True` if the file is netCDF, otherwise `False`

    **Examples:**

    >>> if NetCDFRead.is_netcdf_file(filename):
    ...     return 'netCDF'

        '''
        # Assume that URLs are in netCDF format
        if filename.startswith('http://'):
            return True

        # Read the magic number
        try:
            fh = open(filename, 'rb')
            magic_number = struct.unpack('=L', fh.read(4))[0]
        except:
            magic_number = None

        try:
            fh.close()
        except:
            pass

        if magic_number in (21382211, 1128547841, 1178880137,
                            38159427, 88491075):
            return True
        else:
            return False

    def is_cdl_file(cls, filename):
        '''Return True if the file is a CDL text representation of a netCDF
    file.

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

    >>> if NetCDFRead.is_cdl_file(filename):
    ...     return 'CDL'

        '''
        # Read the magic number
        cdl = False
        try:
            fh = open(filename, 'rt')
        except UnicodeDecodeError:
            pass
        except:
            pass
        else:
            try:
                line = fh.readline()

                # Match comment and blank lines at the top of the file
                while re.match('^\s*//|^\s*$', line):
                    line = fh.readline()

                if line.startswith('netcdf '):
                    cdl = True
            except UnicodeDecodeError:
                pass
        # --- End: try

        try:
            fh.close()
        except:
            pass

        return cdl

    def default_netCDF_fill_value(self, ncvar):
        '''The default netCDF fill value for a variable.

    :Parameters:

        ncvar: `str`
            The netCDF variable name of the variable.

    :Returns:

            The default fill value for the netCDF variable.

    **Examples:**

    >>> n.default_netCDF_fill_value('ua')
    9.969209968386869e+36

        '''
        data_type = self.read_vars['variables'][ncvar].dtype.str[-2:]
        return netCDF4.default_fillvals[data_type]

    @_manage_log_level_via_verbosity
    def read(self, filename, extra=None, default_version=None,
             external=None, extra_read_vars=None, _scan_only=False,
             verbose=None, mask=True, warnings=True,
             warn_valid=False):
        '''Read fields from a netCDF file on disk or from an OPeNDAP server
    location.

    The file may be big or little endian.

    NetCDF dimension names are stored in the `ncdim` attributes of the
    field's DomainAxis objects and netCDF variable names are stored in
    the `ncvar` attributes of the field and its components
    (coordinates, coordinate bounds, cell measures and coordinate
    references, domain ancillaries, field ancillaries).

    :Parameters:

        filename: `str`
            The file name or OPenDAP URL of the dataset.

            Relative paths are allowed, and standard tilde and shell
            parameter expansions are applied to the string.

            *Parameter example:*
              The file ``file.nc`` in the user's home directory could
              be described by any of the following:
              ``'$HOME/file.nc'``, ``'${HOME}/file.nc'``,
              ``'~/file.nc'``, ``'~/tmp/../file.nc'``.

        extra: sequence of `str`, optional
            Create extra, independent fields from the particular types
            of metadata constructs. The *extra* parameter may be one,
            or a sequence, of:

            ==========================  ================================
            *extra*                     Metadata constructs
            ==========================  ================================
            ``'field_ancillary'``       Field ancillary constructs
            ``'domain_ancillary'``      Domain ancillary constructs
            ``'dimension_coordinate'``  Dimension coordinate constructs
            ``'auxiliary_coordinate'``  Auxiliary coordinate constructs
            ``'cell_measure'``          Cell measure constructs
            ==========================  ================================

            *Parameter example:*
              To create fields from auxiliary coordinate constructs:
              ``extra='auxiliary_coordinate'`` or
              ``extra=['auxiliary_coordinate']``.

            *Parameter example:*
              To create fields from domain ancillary and cell measure
              constructs: ``extra=['domain_ancillary',
              'cell_measure']``.

        warnings: `bool`, optional
            If False then do not print warnings when an output field
            construct is incomplete due to "structural
            non-CF-compliance" of the dataset. By default such
            warnings are displayed.

            Structural non-CF-compliance occurs when it is not
            possible to unambiguously map an element of the netCDF
            dataset to an element of the CF data model. Other type on
            non-CF-compliance are not checked, for example, whether or
            not controlled vocabularies have been adhered to is not
            checked.

        mask: `bool`, optional
            If False then do not mask by convention when reading the
            data of field or metadata constructs from disk. By default
            data is masked by convention.

            The masking by convention of a netCDF array depends on the
            values of any of the netCDF variable attributes
            ``_FillValue`` and ``missing_value``,``valid_min``,
            ``valid_max``, ``valid_range``. See the CF conventions for
            details.

            .. versionadded:: 1.8.2

        warn_valid: `bool`, optional
            If True then print a warning for the presence of
            ``valid_min``, ``valid_max`` or ``valid_range`` properties
            on field contructs and metadata constructs that have
            data. By default no such warning is printed

            "Out-of-range" data values in the file, as defined by any
            of these properties, are by default automatically masked,
            which may not be as intended. See the *mask* parameter for
            turning off all automatic masking.

            .. versionadded:: 1.8.3

    :Returns:

        `list`
            The fields in the file.

    **Examples:**

    TODO

        '''
        # ------------------------------------------------------------
        # Initialise netCDF read parameters
        # ------------------------------------------------------------
        self.read_vars = {
            'new_dimensions': {},
            'formula_terms': {},
            'compression': {},

            # Verbose?
            'verbose': verbose,

            # Warnings?
            'warnings': warnings,

            'dataset_compliance': {None: {'non-compliance': {}}},
            'component_report' : {},

            'auxiliary_coordinate' : {},
            'cell_measure'         : {},
            'dimension_coordinate' : {},
            'domain_ancillary'     : {},
            'domain_ancillary_key' : None,
            'field_ancillary'      : {},

            'coordinates' : {},

            'bounds': {},

            # --------------------------------------------------------
            # Geometry containers, keyed by their netCDF geometry
            # container variable names.
            # --------------------------------------------------------
            'geometries': {},

            'do_not_create_field':  set(),
            'references': {},

            # --------------------------------------------------------
            # External variables
            # --------------------------------------------------------
            # Variables listed by the global external_variables
            # attribute
            'external_variables': set(),

            # External variables that are actually referenced from
            # within the parent file
            'referenced_external_variables': set(),

            # --------------------------------------------------------
            # Coordinate references
            # --------------------------------------------------------
            # Grid mapping attributes that describe horizontal datum
            'datum_parameters': self.cf_datum_parameters(),

            # Vertical coordinate reference constructs, keyed by the
            # netCDF variable name of their parent parametric vertical
            # coordinate variable.
            #
            # E.g. {'ocean_s_coordinate':
            #        <CoordinateReference: ocean_s_coordinate>}
            'vertical_crs': {},

            #
            'version': {},

            # Auto mask?
            'mask': bool(mask),

            # Warn for the presence of valid_[min|max|range]
            # attributes?
            'warn_valid': bool(warn_valid),
            'valid_properties': set(('valid_min', 'valid_max', 'valid_range')),
        }

        g = self.read_vars

        # Set versions
        for version in ('1.6', '1.7', '1.8', '1.9'):
            g['version'][version] = LooseVersion(version)

        # ------------------------------------------------------------
        # Add custom read vars
        # ------------------------------------------------------------
        if extra_read_vars:
            g.update(deepcopy(extra_read_vars))

        compression = {}

        # ----------------------------------------------------------------
        # Parse field parameter
        # ----------------------------------------------------------------
        g['get_constructs'] = {
            'auxiliary_coordinate': self.implementation.get_auxiliary_coordinates,
            'cell_measure'        : self.implementation.get_cell_measures,
            'dimension_coordinate': self.implementation.get_dimension_coordinates,
            'domain_ancillary'    : self.implementation.get_domain_ancillaries,
            'field_ancillary'     : self.implementation.get_field_ancillaries,
        }

        # Parse external parameter
        if external:
            if isinstance(external, basestring):
                external = (external,)
        else:
            external = ()

        g['external_files'] = set(external)

        # Parse extra parameter
        if extra:
            if isinstance(extra, basestring):
                field = (extra,)

            for f in extra:
                if f not in g['get_constructs']:
                    raise ValueError(
                        "Can't read: Bad parameter value: extra={!r}".format(
                            extra))
        # --- End: if
        g['extra'] = extra

        filename = os.path.expanduser(os.path.expandvars(filename))

        if os.path.isdir(filename):
            raise IOError("Can't read directory {}".format(filename))

        if not os.path.isfile(filename):
            raise IOError("Can't read non-existent file {}".format(filename))

        g['filename'] = filename

        # ------------------------------------------------------------
        # Open the netCDF file to be read
        # ------------------------------------------------------------
        nc = self.file_open(filename)
        g['nc'] = nc
        logger.info(
            "Reading netCDF file: {}".format(filename)
        )  # pragma: no cover
        logger.info(
            "    Input netCDF dataset = {}".format(nc)
        )  # pragma: no cover

        # ----------------------------------------------------------------
        # Put the file's global attributes into the global
        # 'global_attributes' dictionary
        # ----------------------------------------------------------------
        global_attributes = {}
        for attr in map(str, nc.ncattrs()):
            try:
                value = nc.getncattr(attr)
                if isinstance(value, basestring):
                    try:
                        global_attributes[attr] = str(value)
                    except UnicodeEncodeError:
                        global_attributes[attr] = (
                            value.encode(errors='ignore'))
                else:
                    global_attributes[attr] = value
            except UnicodeDecodeError:
                pass
        # --- End: for

        g['global_attributes'] = global_attributes
        logger.detail(
            "    Global attributes:\n" +
            pformat(g['global_attributes'], indent=4)
        )  # pragma: no cover

        # ------------------------------------------------------------
        # Find the CF version for the file
        # ------------------------------------------------------------
        Conventions =  g['global_attributes'].get('Conventions', '')
        
        all_conventions = re.split(',', Conventions)
        if all_conventions[0] == Conventions:
            all_conventions = re.split('\s+', Conventions)
            
        file_version = None
        for c in all_conventions:
            if not re.match('^CF-\d', c):
                continue

            file_version = re.sub('^CF-', '', c)
            
        if not file_version:
            if default_version is not None:
                # Assume the default version provided by the user
                file_version = default_version
            else:
                # Assume the file has the same version of the CFDM
                # implementation
                file_version = self.implementation.get_cf_version()
        # --- End: if

        g['file_version'] = LooseVersion(file_version)

        # Set minimum versions
        for vn in ('1.6', '1.7', '1.8', '1.9'):
            g['CF>='+vn] = (g['file_version'] >= g['version'][vn])

        # ------------------------------------------------------------
        # Create a dictionary keyed by netCDF variable names where
        # each key's value is a dictionary of that variable's netCDF
        # attributes. E.g. attributes['tas']['units']='K'
        # ------------------------------------------------------------
        variable_attributes = {}
        variable_dimensions = {}
        variable_dataset    = {}
        variable_filename   = {}
        variables           = {}
        for ncvar in nc.variables:
            variable = nc.variables[ncvar]

            variable_attributes[ncvar] = {}
            for attr in map(str, variable.ncattrs()):
                try:
                    variable_attributes[ncvar][attr] = variable.getncattr(attr)
                    if isinstance(variable_attributes[ncvar][attr],
                                  basestring):
                        try:
                            variable_attributes[ncvar][attr] = (
                                str(variable_attributes[ncvar][attr])
                            )
                        except UnicodeEncodeError:
                            variable_attributes[ncvar][attr] = (
                                variable_attributes[ncvar][attr].encode(errors='ignore')
                            )
                except UnicodeDecodeError:
                    pass
            # --- End: for

            variable_dimensions[ncvar] = tuple(variable.dimensions)
            variable_dataset[ncvar]    = nc
            variable_filename[ncvar]   = g['filename']
            variables[ncvar]           = variable

        # The netCDF attributes for each variable
        #
        # E.g. {'grid_lon': {'standard_name': 'grid_longitude'}}
        g['variable_attributes'] = variable_attributes

        # The netCDF dimensions for each variable
        #
        # E.g. {'grid_lon_bounds': ('grid_longitude', 'bounds2')}
        g['variable_dimensions'] = variable_dimensions

        # The netCDF4 dataset object for each variable
        g['variable_dataset'] = variable_dataset

        # The name of the file containing the each variable
        g['variable_filename'] = variable_filename

        # The netCDF4 variable object for each variable
        g['variables'] = variables

        # The netCDF4 dataset objects that have been opened (i.e. the
        # for parent file and any external files)
        g['datasets'] = [nc]

        # The names of the variable in the parent files
        # (i.e. excluding any external variables)
        g['internal_variables'] = set(variables)

        # The netCDF dimensions of the parent file
        internal_dimension_sizes = {}
        for name, dimension in nc.dimensions.items():
            internal_dimension_sizes[name] = dimension.size

        g['internal_dimension_sizes'] = internal_dimension_sizes

        logger.detail(
            "    netCDF dimensions:\n" +
            pformat(internal_dimension_sizes, indent=4)
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
            compress = variable_attributes[ncvar].get('compress')
            if compress is None:
                continue

            # This variable is a list variable for gathering
            # arrays
            self._parse_compression_gathered(ncvar, compress)

            # Do not attempt to create a field from a list
            # variable
            g['do_not_create_field'].add(ncvar)

        # ------------------------------------------------------------
        # DSG variables (CF>=1.6)
        #
        # Identify and parse all DSG count and DSG index variables
        # ------------------------------------------------------------
        if g['CF>=1.6']:
            featureType = g['global_attributes'].get('featureType')
            if featureType is not None:
                g['featureType'] = featureType

                sample_dimension = None
                for ncvar, attributes in variable_attributes.items():
                    if 'sample_dimension' not in attributes:
                        continue

                    # ------------------------------------------------
                    # This variable is a count variable for DSG
                    # contiguous ragged arrays
                    # ------------------------------------------------
                    sample_dimension = attributes['sample_dimension']
                    cf_compliant = self._check_sample_dimension(
                        ncvar,
                        sample_dimension)
                    if not cf_compliant:
                        sample_dimension = None
                    else:
                        element_dimension_2 = (
                            self._parse_ragged_contiguous_compression(
                                ncvar, sample_dimension))

                        # Do not attempt to create a field from a
                        # count variable
                        g['do_not_create_field'].add(ncvar)
                # --- End: for

                instance_dimension = None
                for ncvar, attributes in variable_attributes.items():
                    if 'instance_dimension' not in attributes:
                        continue

                    # ------------------------------------------------
                    # This variable is an index variable for DSG
                    # indexed ragged arrays
                    # ------------------------------------------------
                    instance_dimension = attributes['instance_dimension']
                    cf_compliant = self._check_instance_dimension(
                        ncvar,
                        instance_dimension)
                    if not cf_compliant:
                        instance_dimension = None
                    else:
                        element_dimension_1 = self._parse_indexed_compression(
                            ncvar, instance_dimension)

                        # Do not attempt to create a field from a
                        # index variable
                        g['do_not_create_field'].add(ncvar)
                # --- End: for

                if (sample_dimension   is not None and
                    instance_dimension is not None):
                    # ------------------------------------------------
                    # There are DSG indexed contiguous ragged arrays
                    # ------------------------------------------------
                    self._parse_indexed_contiguous_compression(
                        sample_dimension,
                        instance_dimension)
        # --- End: if

        # ------------------------------------------------------------
        # Geometry container variables (CF>=1.8)
        #
        # Identify and parse all geometry container variables
        # ------------------------------------------------------------
        if g['CF>=1.8']:
            for ncvar, attributes in variable_attributes.items():
                if 'geometry' not in attributes:
                    continue

                geometry_ncvar = attributes['geometry']
                self._parse_geometry(ncvar, geometry_ncvar,
                                     variable_attributes)

                # Do not attempt to create a field construct from a
                # geometry container variable
                g['do_not_create_field'].add(geometry_ncvar)
        # --- End: if

        # ------------------------------------------------------------
        # Parse external variables (CF>=1.7)
        # ------------------------------------------------------------
        if g['CF>=1.7']:
            netcdf_external_variables = global_attributes.pop(
                'external_variables', None)
            parsed_external_variables = self._split_string_by_white_space(
                None, netcdf_external_variables)
            parsed_external_variables = self._check_external_variables(
                netcdf_external_variables, parsed_external_variables)
            g['external_variables'] = set(parsed_external_variables)

        # Now that all of the variables have been scanned, customize
        # the read parameters.
        self._customize_read_vars()

        if _scan_only:
            return self.read_vars

        # ------------------------------------------------------------
        # Get external variables (CF>=1.7)
        # ------------------------------------------------------------
        if g['CF>=1.7']:
            logger.info(
                "    External variables: {}".format(
                    sorted(g['external_variables']))
            )  # pragma: no cover
            logger.info(
                "    External files    : {}".format(g['external_files']),
            )  # pragma: no cover

            if g['external_files'] and g['external_variables']:
                self._get_variables_from_external_files(
                    netcdf_external_variables)
        # --- End: if

        # ------------------------------------------------------------
        # Create a field from every netCDF variable (apart from
        # special variables that have already been identified as such)
        # ------------------------------------------------------------
        all_fields = OrderedDict()
        for ncvar in g['variables']:
            if ncvar not in g['do_not_create_field']:
                all_fields[ncvar] = self._create_field(ncvar)
        # --- End: for

        # ------------------------------------------------------------
        # Check for unreferenced external variables (CF>=1.7)
        # ------------------------------------------------------------
        if g['CF>=1.7']:
            unreferenced_external_variables = (
                g['external_variables'].difference(
                    g['referenced_external_variables']))
            for ncvar in unreferenced_external_variables:
                self._add_message(
                    None, ncvar,
                    message=('External variable',
                             'is not referenced in file'),
                    attribute={
                        'external_variables': netcdf_external_variables}
                )
        # --- End: if

        # ------------------------------------------------------------
        # Discard fields created from netCDF variables that are
        # referenced by other netCDF variables
        # ------------------------------------------------------------
        fields = OrderedDict()
        for ncvar, f in all_fields.items():
            if self._is_unreferenced(ncvar):
                fields[ncvar] = f
        # --- End: for

        logger.detail(
            "Referenced netCDF variables:\n    " +
            "\n    ".join(
                [ncvar for  ncvar in all_fields
                if not self._is_unreferenced(ncvar)]
            )
        )  # pragma: no cover

        logger.detail(
            "Unreferenced netCDF variables:\n    " +
            "\n    ".join(
                [ncvar for ncvar in all_fields
                if self._is_unreferenced(ncvar)]
            )
        )  # pragma: no cover

        # ------------------------------------------------------------
        # If requested, reinstate fields created from netCDF variables
        # that are referenced by other netCDF variables.
        # ------------------------------------------------------------
        if g['extra']:
            fields0 = list(fields.values())
            for construct_type in g['extra']:
                for f in fields0:
                    for construct in (
                            g['get_constructs'][construct_type](f).values()):
                        ncvar = self.implementation.nc_get_variable(construct)
                        if ncvar not in all_fields:
                            continue

                        fields[ncvar] = all_fields[ncvar]
        # --- End: if

        out = [x[1] for x in sorted(fields.items())]

        if warnings:
            for x in out:
                qq = x.dataset_compliance()
                if qq:
                    logger.warning(
                        "WARNING: Field incomplete due to "
                        "non-CF-compliant dataset: {!r}".format(x)
                    )
                    logger.warning("Report:")
                    x.dataset_compliance(display=True)
        # --- End: if

        if warn_valid:
            # --------------------------------------------------------
            # Warn for the presence of 'valid_min', 'valid_max'or
            # 'valid_range' properties. (Introduced at v1.8.3.)
            # --------------------------------------------------------
            for f in out:
                # Check field constructs
                self._check_valid(f, f)

                # Check constructs with data
                for c in self.implementation.get_constructs(
                        f, data=True).values():
                    self._check_valid(f, c)
        # --- End: if

        # ------------------------------------------------------------
        # Close the netCDF file(s)
        # ------------------------------------------------------------
        self.file_close()
        # ------------------------------------------------------------
        # Return the fields
        # ------------------------------------------------------------
        return out

    def _check_valid(self, field, construct):
        '''Issue a warning if a construct with data has valid_[min|max|range]
    properties.

    .. versionadded:: 1.8.3

    :Parameters:

        field: `Field`
            The parent field construct.

        construct: Construct or Bounds
            The construct that may have valid_[min|max|range]
            properties. May also be the parent field construct or
            Bounds.

    :Returns:

        `None`

        '''
        # Check the bounds, if any.
        if self.implementation.has_bounds(construct):
            bounds = self.implementation.get_bounds(construct)
            self._check_valid(field, bounds)

        x = sorted(self.read_vars['valid_properties'].intersection(
            self.implementation.get_properties(construct)))
        if not x:
            return

        # Still here?
        if self.implementation.is_field(construct):
            construct = ""
        else:
            construct = " {!r} with".format(construct)

        message = (
            "WARNING: {!r} has {} {} {}. "
            "Set warn_valid=False to suppress warning.".format(
                field,
                construct,
                ', '.join(x),
                self._plural(x, 'property')
            )
        )
        print(message)

    def _plural(self, x, singular):
        '''TODO

    :Parameters:

        x: sequence

        singular: `str`

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

        '''
        if len(x) == 1:
            return singular

        if singular[-1] == 'y':
            return singular[:-1] + 'ies'

        raise ValueError("Can't (yet) pluralise {}".format(singular))

    def _set_default_FillValue(self, construct, ncvar):
        '''
        '''
        # ------------------------------------------------------------
        # Masking has been turned off, so make sure that there is a
        # fill value recorded so that masking may later be applied
        # manually, if required.
        # ------------------------------------------------------------
        _FillValue = self.implementation.get_property(construct, '_FillValue',
                                                      None)
        if _FillValue is None:
            self.implementation.set_properties(
                construct, {'_FillValue':
                            self.default_netCDF_fill_value(ncvar)}
            )

    def _customize_read_vars(self):
        '''TODO

    .. versionadded:: 1.7.3

        '''
        pass

    def _get_variables_from_external_files(self,
                                           netcdf_external_variables):
        '''Get external variables from external files.

    ..versionadded:: 1.7.0

    :Parameters:

        netcdf_external_variables: `str`
            The un-parsed netCDF external_variables attribute in the
            parent file.

            *Parmaeter example:*
              ``external_variables='areacello'``

    :Returns:

        `None`

        '''
        attribute = {'external_variables': netcdf_external_variables}

        read_vars = self.read_vars.copy()
        verbose = read_vars['verbose']

        external_variables     = read_vars['external_variables']
        external_files         = read_vars['external_files']
        datasets               = read_vars['datasets']
        parent_dimension_sizes = read_vars['internal_dimension_sizes']

        keys = ('variable_attributes',
                'variable_dimensions',
                'variable_dataset',
                'variable_filename',
                'variables')

        found = []

        for external_file in external_files:

            logger.info(
                "\nScanning external file:\n-----------------------"
            )  # pragma: no cover

            external_read_vars = self.read(external_file, _scan_only=True,
                                           verbose=verbose)

            logger.info(
                "Finished scanning external file\n"
            )  # pragma: no cover

            # Reset self.read_vars
            self.read_vars = read_vars

            datasets.append(external_read_vars['nc'])

            for ncvar in external_variables.copy():
                if ncvar not in external_read_vars['internal_variables']:
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
                        None, ncvar,
                        message=('External variable',
                                 'exists in multiple external files'),
                        attribute=attribute)
                    continue

                # Still here? Then the external variable exists in
                # this external file
                found.append(ncvar)

                # Check that the external variable dimensions exist in
                # parent file, with the same sizes.
                ok = True
                for d in external_read_vars['variable_dimensions'][ncvar]:
                    size = parent_dimension_sizes.get(d)
                    if size is None:
                        ok = False
                        self._add_message(
                            None, ncvar,
                            message=('External variable dimension',
                                     'does not exist in file'),
                            attribute=attribute)
                    elif external_read_vars['internal_dimension_sizes'][d] != size:
                        ok = False
                        self._add_message(
                            None, ncvar,
                            message=('External variable dimension',
                                     'has incorrect size'),
                            attribute=attribute)
                    else:
                        continue
                # --- End: for

                if ok:
                    # Update the read parameters so that this external
                    # variable looks like its internal
                    for key in keys:
                        self.read_vars[key][ncvar] = (
                            external_read_vars[key][ncvar]
                        )

                    # Remove this ncvar from the set of external variables
                    external_variables.remove(ncvar)
            # --- End: for
        # --- End: for

    def _parse_compression_gathered(self, ncvar, compress):
        '''TODO
        '''
        g = self.read_vars

        logger.info(
            "        List variable: compress = {}".format(compress),
        )  # pragma: no cover

        gathered_ncdimension = g['variable_dimensions'][ncvar][0]

        parsed_compress = self._split_string_by_white_space(ncvar, compress)
        cf_compliant = self._check_compress(ncvar, compress, parsed_compress)
        if not cf_compliant:
            return

        list_variable = self._create_List(ncvar)

        g['compression'][gathered_ncdimension] = {
            'gathered': {'list_variable'       : list_variable,
                         'implied_ncdimensions': parsed_compress,
                         'sample_dimension'    : gathered_ncdimension}}

    def _parse_ragged_contiguous_compression(self, ncvar,
                                             sample_dimension):
        '''TODO

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

        '''
        g = self.read_vars

        logger.info(
            "    count variable: sample_dimension = {}".format(
                sample_dimension),
        )  # pragma: no cover

        instance_dimension = g['variable_dimensions'][ncvar][0]

        elements_per_instance = self._create_Count(ncvar=ncvar,
                                                   ncdim=instance_dimension)

        # Make up a netCDF dimension name for the element dimension
        featureType = g['featureType'].lower()
        if featureType in ('timeseries', 'trajectory', 'profile'):
            element_dimension = featureType
        elif featureType == 'timeseriesprofile':
            element_dimension = 'profile'
        elif featureType == 'trajectoryprofile':
            element_dimension = 'profile'
        else:
            element_dimension = 'element'

        logger.info(
            "    featureType = {}".format(g['featureType'])
        )  # pragma: no cover

        element_dimension = self._set_ragged_contiguous_parameters(
                elements_per_instance=elements_per_instance,
                sample_dimension=sample_dimension,
                element_dimension=element_dimension,
                instance_dimension=instance_dimension)

        return element_dimension

    def _parse_indexed_compression(self, ncvar, instance_dimension):
        '''TODO

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

        '''
        g = self.read_vars

        logger.info(
            "    index variable: instance_dimension = {}".format(
                instance_dimension),
        )  # pragma: no cover

        # Read the data of the index variable
        ncdim = g['variable_dimensions'][ncvar][0]

        index = self._create_Index(ncvar, ncdim=ncdim)

        # Make up a netCDF dimension name for the element dimension
        featureType = g['featureType'].lower()
        if featureType in ('timeseries', 'trajectory', 'profile'):
            element_dimension = featureType.lower()
        elif featureType == 'timeseriesprofile':
            element_dimension = 'timeseries'
        elif featureType == 'trajectoryprofile':
            element_dimension = 'trajectory'
        else:
            element_dimension = 'element'

        logger.info(
            "    featureType = {}".format(g['featureType'])
        )  # pragma: no cover

        element_dimension = self._set_ragged_indexed_parameters(
            index=index,
            indexed_sample_dimension=g['variable_dimensions'][ncvar][0],
            element_dimension=element_dimension,
            instance_dimension=instance_dimension)

        return element_dimension

    def _parse_indexed_contiguous_compression(self, sample_dimension,
                                              instance_dimension):
        '''TODO

    :Parameters:

        sample_dimension: `str`
            The netCDF dimension name of the sample dimension.

        element_dimension_1: `str`
            The name of the implied element dimension whose size is the
            maximum number of sub-features in any instance.

    '''
        g = self.read_vars

        logger.info(
            "Pre-processing indexed and contiguous compression"
        )  # pragma: no cover
        logger.info(g['compression'])  # pragma: no cover

        profile_dimension = g['compression'][sample_dimension]['ragged_contiguous']['profile_dimension']


        logger.info(
            "    sample_dimension  : {}".format(sample_dimension)
        )  # pragma: no cover
        logger.info(
            "    instance_dimension: {}".format(instance_dimension)
        )  # pragma: no cover
        logger.info(
            "    profile_dimension : {}".format(profile_dimension)
        )  # pragma: no cover

        contiguous = g['compression'][sample_dimension]['ragged_contiguous']
        indexed    = g['compression'][profile_dimension]['ragged_indexed']

        # The indices of the sample dimension which define the start
        # positions of each instances profiles
        profile_indices = indexed['index_variable']

        # profiles_per_instance is a numpy array
        profiles_per_instance = indexed['elements_per_instance']

        elements_per_profile = contiguous['count_variable']

        instance_dimension_size  = indexed['instance_dimension_size']
        element_dimension_1_size = int(profiles_per_instance.max())
        element_dimension_2_size = (
            int(self.implementation.get_data_maximum(elements_per_profile)))

        logger.info(
            "    Creating g['compression'][{!r}]"
            "['ragged_indexed_contiguous']".format(
                  sample_dimension)
        )  # pragma: no cover

        g['compression'][sample_dimension]['ragged_indexed_contiguous'] = {
            'count_variable'          : elements_per_profile,
            'index_variable'          : profile_indices,
            'implied_ncdimensions'    : (instance_dimension,
                                         indexed['element_dimension'],
                                         contiguous['element_dimension']),
            'instance_dimension_size' : instance_dimension_size,
            'element_dimension_1_size': element_dimension_1_size,
            'element_dimension_2_size': element_dimension_2_size,
        }

        logger.info(
            "    Implied dimensions: {} -> {}".format(
                sample_dimension,
                g['compression'][sample_dimension][
                    'ragged_indexed_contiguous']['implied_ncdimensions']
            )
        )  # pragma: no cover
        logger.info(
            "    Removing "
            "g['compression'][{!r}]['ragged_contiguous']".format(
                sample_dimension))  # pragma: no cover

        del g['compression'][sample_dimension]['ragged_contiguous']

    def _parse_geometry(self, field_ncvar, geometry_ncvar, attributes):
        '''TODO

    .. versionadded:: 1.8.0

    :Parameters:

        field_ncvar: `str`
            The netCDF variable name of the parent data variable.

        geometry_ncvar: `str`
            The netCDF variable name of the geometry container
            variable.

        attributes: `dict`
            All attributes of all netCDF variables, keyed by netCDF
            variable name.

    :Returns:

        TODO

        '''
        g = self.read_vars

        logger.info(
            "    Geometry container = {!r}".format(geometry_ncvar)
        )  # pragma: no cover
        logger.info(
            "        netCDF attributes: {}".format(
                attributes[geometry_ncvar])
        )  # pragma: no cover

        if geometry_ncvar in g['geometries']:
            # We've already parsed this geometry container
            return

        geometry_type = attributes[geometry_ncvar].get('geometry_type')

        g['geometries'][geometry_ncvar] = {'geometry_type': geometry_type}

        node_coordinates = attributes[geometry_ncvar].get('node_coordinates')
        node_count = attributes[geometry_ncvar].get('node_count')
        coordinates = attributes[geometry_ncvar].get('coordinates')
        part_node_count = attributes[geometry_ncvar].get('part_node_count')
        interior_ring = attributes[geometry_ncvar].get('interior_ring')

        parsed_node_coordinates = self._split_string_by_white_space(
            geometry_ncvar, node_coordinates)
        parsed_interior_ring = self._split_string_by_white_space(
            geometry_ncvar, interior_ring)
        parsed_node_count = self._split_string_by_white_space(
            geometry_ncvar, node_count)
        parsed_part_node_count = self._split_string_by_white_space(
            geometry_ncvar, part_node_count)

        logger.info(
            "        parsed_node_coordinates = {}".format(
                parsed_node_coordinates)
        )  # pragma: no cover
        logger.info(
            "        parsed_interior_ring    = {}".format(
                parsed_interior_ring)
        )  # pragma: no cover
        logger.info(
            "        parsed_node_count       = {}".format(
                parsed_node_count)
        )  # pragma: no cover
        logger.info(
            "        parsed_part_node_count  = {}".format(
                parsed_part_node_count)
        )  # pragma: no cover

        cf_compliant = True

        if interior_ring is not None and part_node_count is None:
            attribute = {field_ncvar+':geometry':
                         attributes[field_ncvar]['geometry']}
            self._add_message(field_ncvar, geometry_ncvar,
                              message=('part_node_count attribute',
                                       'is missing'),
                              attribute=attribute)
            cf_compliant = False

        cf_compliant = cf_compliant & self._check_node_coordinates(
            field_ncvar, geometry_ncvar, node_coordinates,
            parsed_node_coordinates)

        cf_compliant = cf_compliant & self._check_node_count(
            field_ncvar, geometry_ncvar, node_count,
            parsed_node_count)

        cf_compliant = cf_compliant & self._check_part_node_count(
            field_ncvar, geometry_ncvar, part_node_count,
            parsed_part_node_count)

        cf_compliant = cf_compliant & self._check_interior_ring(
            field_ncvar, geometry_ncvar, interior_ring,
            parsed_interior_ring)

        if not cf_compliant:
            return

        part_dimension = None

        # Find the netCDF dimension for the total number of nodes
        node_dimension = (
            g['variable_dimensions'][parsed_node_coordinates[0]][0])

        logger.info(
            "        node_dimension = {!r}".format(node_dimension)
        )  # pragma: no cover

        if node_count is None:
            # --------------------------------------------------------
            # There is no node_count variable, so all geometries must
            # be size 1 point geometries => we can create a node_count
            # variable in this case.
            # --------------------------------------------------------
            nodes_per_geometry = self.implementation.initialise_Count()
            size = g['nc'].dimensions[node_dimension].size
            ones = self.implementation.initialise_Data(
                array=numpy.ones((size,), dtype='int32'), copy=False)
            self.implementation.set_data(nodes_per_geometry, data=ones)

            # --------------------------------------------------------
            # Cell dimension can not be taken from the node_count
            # variable (becuase it doesn't exist), so it has to be
            # taken from one of the node_coordinate variables,
            # instead.
            # --------------------------------------------------------
            geometry_dimension = (
                g['variable_dimensions'][parsed_node_coordinates[0]][0])
        else:
            # Find the netCDF dimension for the total number of cells
            geometry_dimension = g['variable_dimensions'][node_count][0]

            nodes_per_geometry = self._create_Count(ncvar=node_count,
                                                    ncdim=geometry_dimension)

            # --------------------------------------------------------
            # Create a node count variable (which does not contain any
            # data)
            # --------------------------------------------------------
            nc = self._create_NodeCount(ncvar=node_count)
            g['geometries'][geometry_ncvar]['node_count'] = nc

            # Do not attempt to create a field construct from a
            # netCDF part node count variable
            g['do_not_create_field'].add(node_count)

        # Record the netCDF node dimension as the sample dimension of
        # the count variable
        self.implementation.nc_set_sample_dimension(nodes_per_geometry,
                                                    node_dimension)

        if part_node_count is None:
            # --------------------------------------------------------
            # There is no part_count variable, i.e. cell has exactly
            # one part.
            #
            # => we can treat the nodes as a contiguous ragged array
            # --------------------------------------------------------
            element_dimension = self._set_ragged_contiguous_parameters(
                elements_per_instance=nodes_per_geometry,
                sample_dimension=node_dimension,
                element_dimension='node',
                instance_dimension=geometry_dimension)

            g['compression'][node_dimension]['netCDF_variables'] = (
                parsed_node_coordinates[:])
        else:
            # --------------------------------------------------------
            # There is a part_count variable.
            #
            # => we must treat the nodes as an indexed contiguous
            # ragged array
            # --------------------------------------------------------

            # Do not attempt to create a field construct from a
            # netCDF part node count variable
            g['do_not_create_field'].add(part_node_count)

            part_dimension = g['variable_dimensions'][part_node_count][0]
            g['geometries'][geometry_ncvar]['part_dimension'] = part_dimension

            parts = self._create_Count(ncvar=part_node_count,
                                       ncdim=part_dimension)

            total_number_of_parts = self.implementation.get_data_size(parts)

            parts_data = self.implementation.get_data(parts)
            nodes_per_geometry_data = self.implementation.get_data(
                nodes_per_geometry)

            index = self.implementation.initialise_Index()
            self.implementation.set_data(index, data=parts_data)

            instance_index = 0
            i = 0
            for cell_no in range(self.implementation.get_data_size(
                    nodes_per_geometry)):
                n_nodes_in_this_cell = int(nodes_per_geometry_data[cell_no])

                # Initiailize partial_node_count, a running count
                # of how many nodes there are in this geometry
                n_nodes = 0

                for k in range(i, total_number_of_parts):
                    index.data[k] = instance_index
                    n_nodes += int(parts_data[k])
                    if n_nodes >= n_nodes_in_this_cell:
                        instance_index += 1
                        i += k + 1
                        break
            # --- End: for

            element_dimension_1 = self._set_ragged_contiguous_parameters(
                elements_per_instance=parts,
                sample_dimension=node_dimension,
                element_dimension='node',
                instance_dimension=part_dimension)

            element_dimension_2 = self._set_ragged_indexed_parameters(
                index=index,
                indexed_sample_dimension=g['variable_dimensions'][part_node_count][0],
                element_dimension='part',
                instance_dimension=geometry_dimension)

            self._parse_indexed_contiguous_compression(
                sample_dimension=node_dimension,
                instance_dimension=geometry_dimension)

            # --------------------------------------------------------
            # Create a part node count variable (which does not
            # contain any data)
            # --------------------------------------------------------
            pnc = self._create_PartNodeCount(ncvar=part_node_count,
                                             ncdim=part_dimension)
            g['geometries'][geometry_ncvar]['part_node_count'] = pnc

            # Do not attempt to create a field construct from a
            # netCDF part node count variable
            g['do_not_create_field'].add(part_node_count)

            # --------------------------------------------------------
            # Create an interior ring variable (do this after setting
            # up the indexed ragged array compression parameters).
            # --------------------------------------------------------
            if interior_ring is not None:
                part_dimension = g['variable_dimensions'][interior_ring][0]
                ir = self._create_InteriorRing(ncvar=interior_ring,
                                               ncdim=part_dimension)
                g['geometries'][geometry_ncvar]['interior_ring'] = ir

                # Do not attempt to create a field from an
                # interior ring variable
                g['do_not_create_field'].add(interior_ring)
        # --- End: if

        g['geometries'][geometry_ncvar].update(
            {'node_coordinates'  : parsed_node_coordinates,
             'geometry_dimension': geometry_dimension,
             'node_dimension'    : node_dimension}
        )

    def _set_ragged_contiguous_parameters(self,
                                          elements_per_instance=None,
                                          sample_dimension=None,
                                          element_dimension=None,
                                          instance_dimension=None):
        '''TODO

    :Parameters:

        elements_per_instance: `Count`

        sample_dimension: `str`

        element_dimension: `str`

        instance_dimension: `str`

    :Returns:

        `str`
           The element dimension, possibly modified to make sure that it
           is unique.

        '''
        g = self.read_vars

        instance_dimension_size = self.implementation.get_data_size(
            elements_per_instance)
        element_dimension_size  = int(self.implementation.get_data_maximum(
            elements_per_instance))

        # Make sure that the element dimension name is unique
        base = element_dimension
        n = 0
        while (element_dimension in g['internal_dimension_sizes'] or
               element_dimension in g['new_dimensions'] or
               element_dimension in g['variables']):
            n += 1
            element_dimension = '{0}_{1}'.format(base, n)

        g['new_dimensions'][element_dimension] = element_dimension_size

        g['compression'].setdefault(
            sample_dimension, {})['ragged_contiguous'] = {
                'count_variable'         : elements_per_instance,
                'implied_ncdimensions'   : (instance_dimension,
                                            element_dimension),
                'profile_dimension'      : instance_dimension,
                'element_dimension'      : element_dimension,
                'element_dimension_size' : element_dimension_size,
                'instance_dimension_size': instance_dimension_size,
        }

        logger.info(
            "    Creating g['compression'][{!r}]"
            "['ragged_contiguous']".format(sample_dimension)
        )  # pragma: no cover

        return element_dimension

    def _set_ragged_indexed_parameters(self, index=None,
                                       indexed_sample_dimension=None,
                                       element_dimension=None,
                                       instance_dimension=None):
        '''TODO

    :Parameters:


        index: `Index`

        element_dimension: `str`

        instance_dimension: `str`

    :Returns:

        `str`
           The element dimension, possibly modified to make sure that it
           is unique.

        '''
        g = self.read_vars

        (_, count) = numpy.unique(index.data.array, return_counts=True)

        # The number of elements per instance. For the instances array
        # example above, the elements_per_instance array is [7, 5, 7].
        elements_per_instance = count #self._create_Data(array=count)

        instance_dimension_size = (
            g['internal_dimension_sizes'][instance_dimension])
        element_dimension_size  = int(elements_per_instance.max())

        base = element_dimension
        n = 0
        while (element_dimension in g['internal_dimension_sizes'] or
               element_dimension in g['new_dimensions'] or
               element_dimension in g['variables']):
            n += 1
            element_dimension = '{0}_{1}'.format(base, n)

        g['compression'].setdefault(indexed_sample_dimension, {})['ragged_indexed'] = {
            'elements_per_instance'  : elements_per_instance,
            'index_variable'         : index,
            'implied_ncdimensions'   : (instance_dimension,
                                        element_dimension),
            'element_dimension'      : element_dimension,
            'instance_dimension_size': instance_dimension_size,
            'element_dimension_size' : element_dimension_size,
        }

        g['new_dimensions'][element_dimension] = element_dimension_size

        logger.info(
            "    Created "
            "g['compression'][{!r}]['ragged_indexed']".format(
                indexed_sample_dimension)
        )  # pragma: no cover

        return element_dimension

    def _check_external_variables(self, external_variables,
                                  parsed_external_variables):
        '''TODO

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

        '''
        g = self.read_vars

        attribute = {'external_variables': external_variables}
        message = ('External variable', 'exists in the file')

        out = []

        for ncvar in parsed_external_variables:
            if ncvar not in g['internal_variables']:
                out.append(ncvar)
            else:
                self._add_message(None, ncvar,
                                  message=message,
                                  attribute=attribute)
        # --- End: for

        return out

    def _check_formula_terms(self, field_ncvar, coord_ncvar,
                             formula_terms, z_ncdim=None):
        '''asdsdsa

    .. versionadded:: 1.7.0

    :Parameters:

        field_ncvar: `str`

        coord_ncvar: `str`

        formula_terms: `str`
            A CF-netCDF formula_terms attribute.

        '''
        # ============================================================
        # CF-1.7 7.1. Cell Boundaries
        #
        # If a parametric coordinate variable with a formula_terms
        # attribute (section 4.3.2) also has a bounds attribute, its
        # boundary variable must have a formula_terms attribute
        # too. In this case the same terms would appear in both (as
        # specified in Appendix D), since the transformation from the
        # parametric coordinate values to physical space is realized
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

        nc = g['nc']

        attribute = {coord_ncvar+':formula_terms': formula_terms}

        g['formula_terms'].setdefault(coord_ncvar, {'coord' : {},
                                                    'bounds': {}})

        parsed_formula_terms = self._parse_x(coord_ncvar, formula_terms)

        if not parsed_formula_terms:
            self._add_message(field_ncvar, coord_ncvar,
                              message=incorrectly_formatted,
                              attribute=attribute)
            return False

        parent_dimensions = self._ncdimensions(field_ncvar)

        for x in parsed_formula_terms:
            term, values = list(x.items())[0]

            g['formula_terms'][coord_ncvar]['coord'][term] = None

            if len(values) != 1:
                self._add_message(field_ncvar, coord_ncvar,
                                  message=('formula_terms attribute',
                                           'is incorrectly formatted'),
                                  attribute=attribute)
                continue

            ncvar = values[0]

            if ncvar not in g['internal_variables']:
                self._add_message(field_ncvar, ncvar,
                                  message=('Formula terms variable',
                                           'is not in file'),
                                  attribute=attribute)
                continue

#            if not self._dimensions_are_subset(ncvar, self._ncdimensions(ncvar),
#                                               parent_dimensions):
#                self._add_message(field_ncvar, ncvar,
#                                  message=incorrect_dimensions,
#                                  attribute=attribute,
#                                  dimensions=nc.variables[ncvar].dimensions ,
#                                  variable=field_ncvar)
#                continue

            g['formula_terms'][coord_ncvar]['coord'][term] = ncvar
        # --- End: for

        bounds_ncvar =  g['variable_attributes'][coord_ncvar].get('bounds')

        if bounds_ncvar is None:
            # --------------------------------------------------------
            # Parametric Z coordinate does not have bounds
            # --------------------------------------------------------
            for term in g['formula_terms'][coord_ncvar]['coord']:
                g['formula_terms'][coord_ncvar]['bounds'][term] = None
        else:
            # --------------------------------------------------------
            # Parametric Z coordinate has bounds
            # --------------------------------------------------------
            bounds_formula_terms = (
                g['variable_attributes'][bounds_ncvar].get('formula_terms'))
            if bounds_formula_terms is not None:
                # ----------------------------------------------------
                # Parametric Z coordinate has bounds, and the bounds
                # variable has a formula_terms attribute
                # ----------------------------------------------------
                bounds_attribute = {bounds_ncvar+':formula_terms':
                                    bounds_formula_terms}

                parsed_bounds_formula_terms = self._parse_x(
                    bounds_ncvar,
                    bounds_formula_terms)

                if not parsed_bounds_formula_terms:
                    self._add_message(
                        field_ncvar, bounds_ncvar,
                        message=('Bounds formula_terms attribute',
                                 'is incorrectly formatted'),
                        attribute=attribute,
                        variable=coord_ncvar)

                for x in parsed_bounds_formula_terms:
                    term, values = list(x.items())[0]

                    g['formula_terms'][coord_ncvar]['bounds'][term] = None

                    if len(values) != 1:
                        self._add_message(
                            field_ncvar, bounds_ncvar,
                            message=('Bounds formula_terms attribute',
                                     'is incorrectly formatted'),
                            attribute=bounds_attribute,
                            variable=coord_ncvar)
                        continue

                    ncvar = values[0]

                    if ncvar not in g['internal_variables']:
                        self._add_message(
                            field_ncvar, ncvar,
                            message=('Bounds formula terms variable',
                                     'is not in file'),
                            attribute=bounds_attribute,
                            variable=coord_ncvar)
                        continue

                    if term not in g['formula_terms'][coord_ncvar]['coord']:
                        self._add_message(
                            field_ncvar, bounds_ncvar,
                            message=('Bounds formula_terms attribute',
                                     'has incompatible terms'),
                            attribute=bounds_attribute,
                            variable=coord_ncvar)
                        continue

                    parent_ncvar = (
                        g['formula_terms'][coord_ncvar]['coord'][term])

                    d_ncdims   = g['variable_dimensions'][parent_ncvar]
                    dimensions = g['variable_dimensions'][ncvar]

                    if z_ncdim not in d_ncdims:
                        if ncvar != parent_ncvar:
                            self._add_message(
                                field_ncvar, bounds_ncvar,
                                message=(
                                    'Bounds formula terms variable',
                                    'that does not span the vertical dimension is inconsistent with the formula_terms of the parametric coordinate variable'),
                                attribute=bounds_attribute,
                                variable=coord_ncvar)
                            continue
                        # --- End: if
                    elif len(dimensions) != len(d_ncdims) + 1:
                        self._add_message(
                            field_ncvar, bounds_ncvar,
                            message=('Bounds formula terms variable',
                                     'spans incorrect dimensions'),
                            attribute=bounds_attribute,
                            dimensions=dimensions,
                            variable=coord_ncvar)
                        continue
                    elif d_ncdims != dimensions[:-1]: # WRONG - need to account for char arrays
                        self._add_message(
                            field_ncvar, bounds_ncvar,
                            message=('Bounds formula terms variable',
                                     'spans incorrect dimensions'),
                            attribute=bounds_attribute,
                            dimensions=dimensions,
                            variable=coord_ncvar)
                        continue

                    # Still here?
                    g['formula_terms'][coord_ncvar]['bounds'][term] = ncvar
                # --- End: for

                if (set(g['formula_terms'][coord_ncvar]['coord']) !=
                    set(g['formula_terms'][coord_ncvar]['bounds'])):
                    self._add_message(
                        field_ncvar, bounds_ncvar,
                        message=('Bounds formula_terms attribute',
                                 'has incompatible terms'),
                        attribute=bounds_attribute,
                        variable=coord_ncvar)

            else:
                # ----------------------------------------------------
                # Parametric Z coordinate has bounds, but the bounds
                # variable does not have a formula_terms attribute =>
                # Infer the formula terms bounds variables from the
                # coordinates
                # ----------------------------------------------------
                for term, ncvar in (
                        g['formula_terms'][coord_ncvar]['coord'].items()):
                    g['formula_terms'][coord_ncvar]['bounds'][term] = None

                    if z_ncdim not in self._ncdimensions(ncvar):
                        g['formula_terms'][coord_ncvar]['bounds'][term] = ncvar
                        continue

                    is_coordinate_with_bounds = False
                    for c_ncvar in g['coordinates'][field_ncvar]:
                        if ncvar != c_ncvar:
                            continue

                        is_coordinate_with_bounds = True

                        if z_ncdim not in g['variable_dimensions'][c_ncvar]:
                            # Coordinates do not span the Z dimension
                            g['formula_terms'][coord_ncvar]['bounds'][term] = (
                                ncvar)
                        else:
                            # Coordinates span the Z dimension
                            b = g['bounds'][field_ncvar].get(ncvar)
                            if b is not None:
                                g['formula_terms'][coord_ncvar]['bounds'][term] = b
                            else:
                                is_coordinate_with_bounds = False
                        # --- End: if

                        break
                    # --- End: for

                    if not is_coordinate_with_bounds:
                         self._add_message(
                             field_ncvar, ncvar,
                             message=("Formula terms variable",
                                      "that spans the vertical dimension "
                                      "has no bounds"),
                             attribute=attribute,
                             variable=coord_ncvar)
                # --- End: for
            # --- End: if
        # --- End: if

    def _create_field(self, field_ncvar):
        '''Create a field for a given netCDF variable.

    .. versionadded:: 1.7.0

    :Parameters:

        field_ncvar: `str`
            The name of the netCDF variable to be turned into a field.

    :Returns:

        `Field`
            The new field.

        '''
        g = self.read_vars

        # Reset 'domain_ancillary_key'
        g['domain_ancillary_key'] = {}

        nc = g['variable_dataset'][field_ncvar]

        dimensions = g['variable_dimensions'][field_ncvar]
        g['dataset_compliance'][field_ncvar] = {
            'CF version': self.implementation.get_cf_version(),
            'dimensions': dimensions,
            'non-compliance': {}
        }

        logger.info(
            "Converting netCDF variable {} ({}) to a Field:".format(
                field_ncvar, ', '.join(dimensions))
        )  # pragma: no cover

        # Combine the global properties with the data variable
        # properties, giving precedence to those of the data variable.
        field_properties = g['global_attributes'].copy()
        field_properties.update(g['variable_attributes'][field_ncvar])

        logger.detail(
            "    netCDF attributes:\n" +
            pformat(field_properties, indent=4)
        )  # pragma: no cover

        # Take cell_methods out of the data variable's properties
        # since it will need special processing once the domain has
        # been defined
        cell_methods_string = field_properties.pop('cell_methods', None)

        # Take add_offset and scale_factor out of the data variable's
        # properties since they will be dealt with by the variable's
        # Data object. Makes sure we note that they were there so we
        # can adjust the field's data type accordingly.
        values = [field_properties.pop(k, None)
                  for k in ('add_offset', 'scale_factor')]
        unpacked_dtype = (values != [None, None])
        if unpacked_dtype:
            try:
                values.remove(None)
            except ValueError:
                pass

            unpacked_dtype = numpy.result_type(*values)

        # Initialise node_coordinates_as_bounds
        g['node_coordinates_as_bounds'] = set()

        # ------------------------------------------------------------
        # Initialize the field with properties
        # ------------------------------------------------------------
        f = self.implementation.initialise_Field()

        self.implementation.set_properties(f, field_properties, copy=True)

        if not g['mask']:
            # --------------------------------------------------------
            # Masking has been turned off, so make sure that there is
            # a fill value recorded on the field so that masking may
            # later be applied manually, if required. (Introduced at
            # v1.8.2.)
            # --------------------------------------------------------
            self._set_default_FillValue(f, field_ncvar)

        # Store the field's netCDF variable name
        self.implementation.nc_set_variable(f, field_ncvar)

        x = g['global_attributes'].copy()
        for k, v in g['global_attributes'].items():
            if k not in g['variable_attributes'][field_ncvar]:
                x[k] = None
        # --- End: for

        self.implementation.nc_set_global_attributes(f, x)

        # ------------------------------------------------------------
        # Remove the field construct's "geometry" property, saving its
        # value
        # ------------------------------------------------------------
        if g['CF>=1.8']:
            geometry = self.implementation.del_property(f, 'geometry', None)
            if geometry is not None:
                self.implementation.nc_set_geometry_variable(f, geometry)
        # --- End: if

        # Map netCDF dimension names to domain axis names.
        #
        # For example: {'lat': 'dim0', 'time': 'dim1'}
        ncdim_to_axis = {}
        g['ncdim_to_axis'] = ncdim_to_axis

        ncscalar_to_axis = {}

        # Map netCDF variable names to internal identifiers
        #
        # For example: {'dimensioncoordinate1': 'time'}
        ncvar_to_key = {}

        data_axes = []

        # ------------------------------------------------------------
        # Add axes and non-scalar dimension coordinates to the field
        # ------------------------------------------------------------
        field_ncdimensions = self._ncdimensions(field_ncvar)

#        unlimited = []

        for ncdim in field_ncdimensions:
#            print (ncdim, 'ncdim=',  g['variable_dimensions'].get(ncdim))
            if g['variable_dimensions'].get(ncdim) == (ncdim,):
                # There is a Unidata coordinate variable for this
                # dimension, so create a domain axis and dimension
                # coordinate
                if ncdim in g['dimension_coordinate']:
                    coord = self._copy_construct('dimension_coordinate',
                                                 field_ncvar, ncdim)
                else:
                    coord = self._create_dimension_coordinate(field_ncvar,
                                                              ncdim, f)
                    g['dimension_coordinate'][ncdim] = coord

                domain_axis = self._create_domain_axis(
                    self.implementation.get_construct_data_size(coord),
                    ncdim)

                logger.debug(
                    "    [0] Inserting {!r}".format(domain_axis)
                )  # pragma: no cover
                axis = self.implementation.set_domain_axis(
                    field=f,
                    construct=domain_axis,
                    copy=False)

                logger.debug(
                    "    [1] Inserting {!r}".format(coord)
                )  # pragma: no cover
                dim = self.implementation.set_dimension_coordinate(
                    field=f, construct=coord,
                    axes=[axis], copy=False)

                self._reference(ncdim)
                if coord.has_bounds():
                    bounds = self.implementation.get_bounds(coord)
                    self._reference(self.implementation.nc_get_variable(
                        bounds))

                # Set unlimited status of axis
                if nc.dimensions[ncdim].isunlimited():
                    self.implementation.nc_set_unlimited_axis(f, axis)

                ncvar_to_key[ncdim] = dim
                g['coordinates'].setdefault(field_ncvar, []).append(ncdim)
            else:
                # There is no dimension coordinate for this dimension,
                # so just create a domain axis with the correct size.


                if ncdim in g['new_dimensions']:
                    size = g['new_dimensions'][ncdim]
                else:
                    size = g['internal_dimension_sizes'][ncdim]

                domain_axis = self._create_domain_axis(size, ncdim)
                logger.debug(
                    "    [2] Inserting {!r}".format(domain_axis)
                )  # pragma: no cover
                axis = self.implementation.set_domain_axis(
                    field=f,
                    construct=domain_axis,
                    copy=False)

                # Set unlimited status of axis
                try:
                    if nc.dimensions[ncdim].isunlimited():
                        self.implementation.nc_set_unlimited_axis(f, axis)
#                        unlimited.append(axis)
                except KeyError:
                    # This dimension is not in the netCDF file (as might
                    # be the case for an element dimension implied by a
                    # ragged array).
                    pass
            # --- End: if

            # Update data dimension name and set dimension size
            data_axes.append(axis)

            ncdim_to_axis[ncdim] = axis
        # --- End: for

#        if unlimited:
#            self.implementation.nc_set_unlimited_dimensions(f, unlimited)

        data = self._create_data(field_ncvar, f, unpacked_dtype=unpacked_dtype)

        logger.debug(
            "    [3] Inserting {!r}".format(data)
        )  # pragma: no cover

        self.implementation.set_data(f, data, axes=data_axes, copy=False)

        # ----------------------------------------------------------------
        # Add scalar dimension coordinates and auxiliary coordinates to
        # the field
        # ----------------------------------------------------------------
        coordinates = self.implementation.del_property(f, 'coordinates', None)

        if coordinates is not None:
            parsed_coordinates = self._split_string_by_white_space(
                field_ncvar,
                coordinates)
            for ncvar in parsed_coordinates:

                # Skip dimension coordinates which are in the list
                if ncvar in field_ncdimensions:
                    continue

                cf_compliant = self._check_auxiliary_scalar_coordinate(
                    field_ncvar, ncvar, coordinates)
                if not cf_compliant:
                    continue

                # Set dimensions for this variable
                dimensions = self._get_domain_axes(ncvar)

                if ncvar in g['auxiliary_coordinate']:
                    coord = g['auxiliary_coordinate'][ncvar].copy()
                else:
                    coord = self._create_auxiliary_coordinate(
                        field_ncvar, ncvar, f)
                    g['auxiliary_coordinate'][ncvar] = coord

                # --------------------------------------------------------
                # Turn a
                # --------------------------------------------------------
                is_scalar_dimension_coordinate = False
                scalar = False
                if not dimensions:
                    scalar = True
#                    if g['variables'][ncvar].dtype.kind is 'S':
                    if self._is_char_or_string(ncvar):
                        # String valued scalar coordinate. T turn it
                        # into a 1-d auxiliary coordinate construct.
                        domain_axis = self._create_domain_axis(1)
                        logger.debug(
                            "    [4] Inserting {!r}".format(domain_axis)
                        )  # pragma: no cover
                        dim = self.implementation.set_domain_axis(
                            f, domain_axis)

                        dimensions = [dim]

                        coord = self.implementation.construct_insert_dimension(
                            construct=coord, position=0)
                        g['auxiliary_coordinate'][ncvar] = coord
                    else:
                        # Numeric valued scalar coordinate
                        is_scalar_dimension_coordinate = True
                # --- End: if

                if is_scalar_dimension_coordinate:
                    # Insert a domain axis and dimension coordinate
                    # derived from a numeric scalar auxiliary
                    # coordinate
                    coord = self.implementation.initialise_DimensionCoordinate_from_AuxiliaryCoordinate(
                        auxiliary_coordinate=coord,
                        copy=False)

                    coord = self.implementation.construct_insert_dimension(
                                construct=coord, position=0)

                    domain_axis = self._create_domain_axis(
                        self.implementation.get_construct_data_size(coord))
                    logger.debug(
                        "    [5] Inserting {!r}".format(domain_axis)
                    )  # pragma: no cover
                    axis = self.implementation.set_domain_axis(
                        field=f,
                        construct=domain_axis,
                        copy=False)

                    logger.debug(
                        "    [5] Inserting {!r}".format(coord)
                    )  # pragma: no cover
                    dim = self.implementation.set_dimension_coordinate(
                        f, coord,
                        axes=[axis],
                        copy=False)

                    self._reference(ncvar)
                    if self.implementation.has_bounds(coord):
                        bounds = self.implementation.get_bounds(coord)
                        self._reference(
                            self.implementation.nc_get_variable(bounds))

                    dimensions = [axis]
                    ncvar_to_key[ncvar] = dim

                    g['dimension_coordinate'][ncvar] = coord
                    del g['auxiliary_coordinate'][ncvar]
                else:
                    # Insert auxiliary coordinate
                    logger.debug(
                        "    [6] Inserting {!r}".format(coord)
                    )  # pragma: no cover

                    aux = self.implementation.set_auxiliary_coordinate(
                        f, coord, axes=dimensions, copy=False)

                    self._reference(ncvar)
                    if self.implementation.has_bounds(coord):
                        bounds = self.implementation.get_bounds(coord)
                        self._reference(
                            self.implementation.nc_get_variable(bounds))

                    ncvar_to_key[ncvar] = aux

                if scalar:
                    ncscalar_to_axis[ncvar] = dimensions[0]
            # --- End: for
        # --- End: if

        # ------------------------------------------------------------
        # Add auxiliary coordinate constructs from geometry node
        # coordinates that are not already bounds of existing
        # auxiliary coordinate constructs (CF>=1.8)
        # ------------------------------------------------------------
        geometry = self._get_geometry(field_ncvar)
        if geometry is not None:
            node_coordinates = set(geometry['node_coordinates']).difference(
                g['node_coordinates_as_bounds'])

            for node_ncvar in geometry['node_coordinates']:
                found = any(
                    [(self.implementation.get_bounds_ncvar(a) == node_ncvar)
                     for a in f.auxiliary_coordinates.values()]
                )

                if found:
                    continue

                #
                if node_ncvar in g['auxiliary_coordinate']:
                    coord = g['auxiliary_coordinate'][node_ncvar].copy()
                else:
                    coord = self._create_auxiliary_coordinate(
                        field_ncvar=field_ncvar,
                        ncvar=None,
                        f=f,
                        bounds_ncvar=node_ncvar)

                    geometry_type = geometry['geometry_type']
                    if geometry_type is not None:
                        self.implementation.set_geometry(coord, geometry_type)

                    g['auxiliary_coordinate'][node_ncvar] = coord

                # Insert auxiliary coordinate
                logger.debug(
                    "    [6] Inserting {!r}".format(coord)
                )  # pragma: no cover

                # TODO check that geometry_dimension is a dimension of
                # the data variable
                geometry_dimension = geometry['geometry_dimension']
                if geometry_dimension not in g['ncdim_to_axis']:
                    logger.warning(
                        "geometry['geometry_dimension'] is not in "
                        "g['ncdim_to_axis']"
                    )

                aux = self.implementation.set_auxiliary_coordinate(
                    f, coord,
                    axes=(g['ncdim_to_axis'][geometry_dimension],),
                    copy=False)

                self._reference(node_ncvar)
                ncvar_to_key[node_ncvar] = aux
        # --- End: if

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

            formula_terms = (
                g['variable_attributes'][coord_ncvar].get('formula_terms'))
            if formula_terms is None:
                # This coordinate doesn't have a formula_terms attribute
                continue

            if coord_ncvar not in g['formula_terms']:
                self._check_formula_terms(
                    field_ncvar,
                    coord_ncvar,
                    formula_terms,
                    z_ncdim=g['variable_dimensions'][coord_ncvar][0])

            ok = True
            domain_ancillaries = []
            for term, ncvar in (
                    g['formula_terms'][coord_ncvar]['coord'].items()):
                if ncvar is None:
                    continue

                # Set dimensions
                axes = self._get_domain_axes(ncvar)

                if ncvar in g['domain_ancillary']:
                    domain_anc = self._copy_construct('domain_ancillary',
                                                      field_ncvar, ncvar)
                else:
                    bounds = (
                        g['formula_terms'][coord_ncvar]['bounds'].get(term))
                    if bounds == ncvar:
                        bounds = None

                    domain_anc = self._create_domain_ancillary(
                        field_ncvar,
                        ncvar,
                        f,
                        bounds_ncvar=bounds)

                if len(axes) == len(self._ncdimensions(ncvar)):
                    domain_ancillaries.append((ncvar, domain_anc, axes))
                else:
                    # The domain ancillary variable spans a dimension
                    # that is not spanned by its parent data variable
                    self._add_message(
                        field_ncvar, ncvar,
                        message=('Formula terms variable',
                                 'spans incorrect dimensions'),
                        attribute={coord_ncvar+':formula_terms':
                                   formula_terms},
                        dimensions=g['variable_dimensions'][ncvar])
                    ok = False
            # --- End: for

            if not ok:
                # Move on to the next coordinate
                continue

            # Still here? Create a formula terms coordinate reference.
            for ncvar, domain_anc, axes in domain_ancillaries:
                logger.debug(
                    "    [7] Inserting {!r}".format(domain_anc)
                )  # pragma: no cover

                da_key = self.implementation.set_domain_ancillary(field=f,
                                                  construct=domain_anc,
                                                  axes=axes, copy=False)

                self._reference(ncvar)
                if self.implementation.has_bounds(domain_anc):
                    bounds = self.implementation.get_bounds(domain_anc)
                    self._reference(
                        self.implementation.nc_get_variable(bounds))

                if ncvar not in ncvar_to_key:
                    ncvar_to_key[ncvar] = da_key

                g['domain_ancillary'][ncvar]     = domain_anc
                g['domain_ancillary_key'][ncvar] = da_key

            coordinate_reference = self._create_formula_terms_ref(
                f, key, coord,
                g['formula_terms'][coord_ncvar]['coord'])

            self.implementation.set_coordinate_reference(
                field=f,
                construct=coordinate_reference,
                copy=False)

#            g['vertical_crs'][coord_ncvar] = coordinate_reference
            g['vertical_crs'][key] = coordinate_reference
        # --- End: for

        # ------------------------------------------------------------
        # Add grid mapping coordinate references (do this after
        # formula terms)
        # ------------------------------------------------------------
        grid_mapping = self.implementation.del_property(
            f, 'grid_mapping', None)
        if grid_mapping is not None:
            parsed_grid_mapping = self._parse_grid_mapping(
                field_ncvar, grid_mapping)

            cf_compliant = self._check_grid_mapping(field_ncvar,
                                                    grid_mapping,
                                                    parsed_grid_mapping)
            if not cf_compliant:
                logger.warning(
                    "        Bad grid_mapping: {}".format(grid_mapping)
                )  # pragma: no cover
            else:
                for x in parsed_grid_mapping:
                    grid_mapping_ncvar, coordinates = list(x.items())[0]

                    parameters = (
                        g['variable_attributes'][grid_mapping_ncvar].copy())

                    # Convert netCDF variable names to internal identifiers
                    coordinates = [ncvar_to_key[ncvar] for ncvar in coordinates
                                   if ncvar in ncvar_to_key]

                    # ------------------------------------------------
                    # Find the datum and coordinate conversion for the
                    # grid mapping
                    # ------------------------------------------------
                    datum_parameters = {}
                    coordinate_conversion_parameters = {}
                    for parameter, value in parameters.items():
                        if parameter in g['datum_parameters']:
                            datum_parameters[parameter] = value
                        else:
                            coordinate_conversion_parameters[parameter] = value
                    # --- End: for

                    datum = self.implementation.initialise_Datum(
                        parameters=datum_parameters)

                    coordinate_conversion = (
                        self.implementation.initialise_CoordinateConversion(
                            parameters=coordinate_conversion_parameters))

                    create_new = True

                    if not coordinates:
                        # DCH ALERT
                        # what to do about duplicate standard names? TODO
                        name = parameters.get('grid_mapping_name', None)
                        for n in self.cf_coordinate_reference_coordinates().get(name, ()):
                            for key, coord in self.implementation.get_coordinates(field=f).items():
                                if n == self.implementation.get_property(
                                        coord, 'standard_name', None):
                                    coordinates.append(key)
                        # --- End: for

                        # Add the datum to already existing vertical
                        # coordinate references
                        for vcr in g['vertical_crs'].values():
                            self.implementation.set_datum(
                                coordinate_reference=vcr,
                                datum=datum)
                    else:
                        for vcoord, vcr in g['vertical_crs'].items():
                            if vcoord in coordinates:
                                # Add the datum to an already existing
                                # vertical coordinate reference
                                logger.debug(
                                    "    [ ] Inserting "
                                    "{!r} into {!r}".format(datum, vcr)
                                )  # pragma: no cover

                                self.implementation.set_datum(
                                    coordinate_reference=vcr,
                                    datum=datum)
                                coordinates.remove(vcoord)
                                create_new = bool(coordinates)
                    # --- End: if

                    if create_new:
                        coordref = self.implementation.initialise_CoordinateReference()

                        self.implementation.set_datum(
                            coordinate_reference=coordref,
                            datum=datum)

                        self.implementation.set_coordinate_conversion(
                            coordinate_reference=coordref,
                            coordinate_conversion=coordinate_conversion)

                        self.implementation.set_coordinate_reference_coordinates(
                            coordref,
                            coordinates)

                        self.implementation.nc_set_variable(
                            coordref, grid_mapping_ncvar)

                        key = self.implementation.set_coordinate_reference(
                            field=f,
                            construct=coordref,
                            copy=False)
                        self._reference(grid_mapping_ncvar)
                        ncvar_to_key[grid_mapping_ncvar] = key
                # --- End: for
        # --- End: if

        # ----------------------------------------------------------------
        # Add cell measures to the field
        # ----------------------------------------------------------------
        measures = self.implementation.del_property(f, 'cell_measures', None)
        if measures is not None:
            parsed_cell_measures = self._parse_x(field_ncvar, measures)

            cf_compliant = self._check_cell_measures(field_ncvar,
                                                     measures,
                                                     parsed_cell_measures)

            if cf_compliant:
                for x in parsed_cell_measures:
                    measure, ncvars = list(x.items())[0]
                    ncvar = ncvars[0]

                    # Set the domain axes for the cell measure
                    axes = self._get_domain_axes(ncvar, allow_external=True)

                    if ncvar in g['cell_measure']:
                        # Copy the cell measure from one that already
                        # exists
                        cell = g['cell_measure'][ncvar].copy()
                    else:
                        cell = self._create_cell_measure(measure, ncvar)
                        g['cell_measure'][ncvar] = cell

                    logger.debug(
                        "    [8] Inserting {!r}".format(cell)
                    )  # pragma: no cover

                    key = self.implementation.set_cell_measure(
                        field=f, construct=cell,
                        axes=axes, copy=False)

                    self._reference(ncvar)

                    ncvar_to_key[ncvar] = key

                    if ncvar in g['external_variables']:
                        g['referenced_external_variables'].add(ncvar)
        # --- End: if

        # ------------------------------------------------------------
        # Add cell methods to the field
        # ------------------------------------------------------------
        if cell_methods_string is not None:
            name_to_axis = ncdim_to_axis.copy()
            name_to_axis.update(ncscalar_to_axis)

            cell_methods = self._parse_cell_methods(
                cell_methods_string, field_ncvar)

            for properties in cell_methods:
                axes = [name_to_axis.get(axis, axis)
                        for axis in properties.pop('axes')]

                method = properties.pop('method', None)

                cell_method = self._create_cell_method(
                    axes, method, properties)
                logger.debug(
                    "    [ ] Inserting {!r}".format(cell_method)
                )  # pragma: no cover

                self.implementation.set_cell_method(field=f,
                                                    construct=cell_method,
                                                    copy=False)
        # --- End: if

        # ------------------------------------------------------------
        # Add field ancillaries to the field
        # ------------------------------------------------------------
        ancillary_variables = self.implementation.del_property(
            f, 'ancillary_variables', None)
        if ancillary_variables is not None:
            parsed_ancillary_variables = self._split_string_by_white_space(
                field_ncvar,
                ancillary_variables)
            cf_compliant = self._check_ancillary_variables(
                field_ncvar,
                ancillary_variables,
                parsed_ancillary_variables)
            if not cf_compliant:
                pass
            else:
                for ncvar in parsed_ancillary_variables:
                    # Set dimensions
                    axes = self._get_domain_axes(ncvar)

                    if ncvar in g['field_ancillary']:
                        field_anc = g['field_ancillary'][ncvar].copy()
                    else:
                        field_anc = self._create_field_ancillary(ncvar)
                        g['field_ancillary'][ncvar] = field_anc

                    # Insert the field ancillary
                    logger.debug(
                        "    [9] Inserting {!r}".format(field_anc)
                    )  # pragma: no cover
                    key = self.implementation.set_field_ancillary(field=f,
                                                     construct=field_anc,
                                                     axes=axes, copy=False)
                    self._reference(ncvar)

                    ncvar_to_key[ncvar] = key
        # --- End: if

        logger.info(
            "    Field properties:\n" +
            pformat(self.implementation.get_properties(f), indent=4)
        )  # pragma: no cover

        # Add the structural read report to the field
        dataset_compliance = g['dataset_compliance'][field_ncvar]
        components = dataset_compliance['non-compliance']
        if components:
            dataset_compliance = {field_ncvar: dataset_compliance}
        else:
            dataset_compliance = {}

        self.implementation.set_dataset_compliance(f, dataset_compliance)

        # Return the finished field
        return f

    def _is_char_or_string(self, ncvar):
        '''Return True if the netCDf variable has string or char datatype.

    :Parameters:

        ncvar: `str`
            The name of the netCDF variable.

    :Returns:

        `bool`

    **Examples:**

        >>> n._is_char_or_string('regions')
        True

        '''
        datatype = self.read_vars['variables'][ncvar].dtype
        return datatype == str or datatype.kind in 'SU'

    def _is_char(self, ncvar):
        '''Return True if the netCDf variable has char datatype.

    :Parameters:

        ncvar: `str`
            The name of the netCDF variable.

    :Returns:

        `bool`

    **Examples:**

        >>> n._is_char('regions')
        True

        '''
        datatype = self.read_vars['variables'][ncvar].dtype
        return datatype != str and datatype.kind in 'SU'

    def _get_geometry(self, field_ncvar):
        '''Return a geometry container for this field construct.

    .. versionadded:: 1.8.0

    :Parameters:

        field_ncvar: `str`
            The netCDF varibalename for the field construct.

    :Returns:

        `dict` or `None`
            A `dict` containing geometry container information. If
            there is no geometry container for this data variable, or
            if the file version is pre-CF-1.8, then `None` is
            returned.

        '''
        g = self.read_vars
        if g['CF>=1.8']:
            geometry_ncvar = (
                g['variable_attributes'][field_ncvar].get('geometry'))
            return g['geometries'].get(geometry_ncvar)

    def _add_message(self, field_ncvar, ncvar, message=None,
                     attribute=None, dimensions=None, variable=None,
                     conformance=None):
        '''TODO

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

        '''
        g = self.read_vars

        if message is not None:
            code = self._code0[message[0]]*1000 + self._code1[message[1]]
            message = ' '.join(message)
        else:
            code = None

        d = {'code'          : code,
             'attribute'     : attribute,
             'reason'        : message,
        }

        if dimensions is not None:
            d['dimensions'] = dimensions

        if variable is None:
            variable = ncvar

        g['dataset_compliance'][field_ncvar]['non-compliance'].setdefault(ncvar, []).append(d)

        e = g['component_report'].setdefault(variable, {})
        e.setdefault(ncvar, []).append(d)

        if dimensions is None:  # pragma: no cover
            dimensions = ''  # pragma: no cover
        else:  # pragma: no cover
            dimensions = '(' + ', '.join(dimensions) + ')'  # pragma: no cover

        # Though an error of sorts, set as warning as does not terminate read
        logger.info(
            "    Error processing netCDF variable {} {}: {}".format(
                ncvar, dimensions, d['reason'])
        )  # pragma: no cover

        return d

    def _get_domain_axes(self, ncvar, allow_external=False):
        '''Return the domain axis identifiers that correspond to a netCDF
    variable's netCDF dimensions.

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

        '''
        g = self.read_vars

        if allow_external and ncvar in g['external_variables']:
            axes = []
        else:
            ncdim_to_axis = g['ncdim_to_axis']
            ncdimensions = self._ncdimensions(ncvar)

            axes = [ncdim_to_axis[ncdim] for ncdim in ncdimensions
                    if ncdim in ncdim_to_axis]

        return axes

    def _create_auxiliary_coordinate(self, field_ncvar, ncvar, f,
                                     bounds_ncvar=None):
        '''TODO

    :Returns:

        The auxiliary coordinate constuct.

        '''
        return self._create_bounded_construct(field_ncvar=field_ncvar,
                                              ncvar=ncvar, f=f,
                                              auxiliary=True,
                                              bounds_ncvar=bounds_ncvar)

    def _create_dimension_coordinate(self, field_ncvar, ncvar, f,
                                     bounds_ncvar=None):
        '''TODO

    :Returns:

        The dimension coordinate constuct.

        '''
        return self._create_bounded_construct(field_ncvar=field_ncvar,
                                              ncvar=ncvar, f=f,
                                              dimension=True,
                                              bounds_ncvar=bounds_ncvar)

    def _create_domain_ancillary(self, field_ncvar, ncvar, f,
                                 bounds_ncvar=None):
        '''TODO

    :Returns:

        The domain ancillary constuct.

        '''
        return self._create_bounded_construct(field_ncvar=field_ncvar,
                                              ncvar=ncvar, f=f,
                                              domain_ancillary=True,
                                              bounds_ncvar=bounds_ncvar)

    def _create_bounded_construct(self, field_ncvar, ncvar, f,
                                  dimension=False, auxiliary=False,
                                  domain_ancillary=False,
                                  bounds_ncvar=None,
                                  has_coordinates=True):
        '''Create a variable which might have bounds.

    :Parameters:

        ncvar: `str`
            The netCDF name of the variable.

        f: `Field`
            The parent field construct.

        dimension: `bool`, optional
            If True then a dimension coordinate construct is created.

        auxiliary: `bool`, optional
            If True then an auxiliary coordinate consrtruct is created.

        domain_ancillary: `bool`, optional
            If True then a domain ancillary construct is created.

    :Returns:

        `DimensionCoordinate` or `AuxiliaryCoordinate` or `DomainAncillary`
            The new construct.

        '''
        g = self.read_vars
        nc = g['nc']

        g['bounds'][field_ncvar] = {}
        g['coordinates'][field_ncvar] = []

        if ncvar is not None:
            properties = g['variable_attributes'][ncvar].copy()
            properties.pop('formula_terms', None)
        else:
            properties = {}

        # ------------------------------------------------------------
        # Look for a geometry container
        # ------------------------------------------------------------
        geometry = self._get_geometry(field_ncvar)

        has_bounds = False
        attribute = 'bounds' # TODO Bad default? consider if bounds != None

#if len(axes) == len(ncdimensions):
#                    domain_ancillaries.append((ncvar, domain_anc, axes))
#                else:
#                    # The domain ancillary variable spans a dimension
#                    # that is not spanned by its parent data variable
#                    self._add_message(
#                        field_ncvar, ncvar,
#                        message=('Formula terms variable', 'spans incorrect dimensions'),
#                        attribute={coord_ncvar+':formula_terms': formula_terms},
#                        dimensions=nc.variables[ncvar].dimensions)
#                    ok = False
#                    break

        # If there are bounds then find the name of the attribute that
        # names them, and the netCDF variable name of the bounds.
        if bounds_ncvar is None:
            bounds_ncvar = properties.pop('bounds', None)
            if bounds_ncvar is None:
                bounds_ncvar = properties.pop('climatology', None)
                if bounds_ncvar is not None:
                    attribute = 'climatology'
                elif geometry:
                    bounds_ncvar = properties.pop('nodes', None)
                    if bounds_ncvar is not None:
                        attribute = 'nodes'
        # --- End: if

        if dimension:
            properties.pop('compress', None)
            c = self.implementation.initialise_DimensionCoordinate()
        elif auxiliary:
            c = self.implementation.initialise_AuxiliaryCoordinate()
        elif domain_ancillary:
            c = self.implementation.initialise_DomainAncillary()
        else:
            raise ValueError(
                "Must set one of the dimension, auxiliary or domain_ancillary "
                "parameters to True")

        self.implementation.set_properties(c, properties)

        if not g['mask']:
            # --------------------------------------------------------
            # Masking has been turned off, so make sure that there is
            # a fill value recorded on the coordinate or domain
            # ancillary so that masking may later be applied manually,
            # if required. (Introduced at v1.8.3.)
            # --------------------------------------------------------
            self._set_default_FillValue(c, ncvar)

#        if attribute == 'climatology':
#            # Need to
#            self.implementation.set_geometry(coordinate=c, value='climatology')

        if has_coordinates and ncvar is not None:
            data = self._create_data(ncvar, c)
            self.implementation.set_data(c, data, copy=False)

        # ------------------------------------------------------------
        # Add any bounds
        # ------------------------------------------------------------
        if bounds_ncvar:
            if geometry is None:
                # Check "normal" boounds
                cf_compliant = self._check_bounds(field_ncvar, ncvar,
                                                  attribute, bounds_ncvar)
                if not cf_compliant:
                    pass
            else:
                pass

            bounds = self.implementation.initialise_Bounds()

            bounds_properties = g['variable_attributes'][bounds_ncvar].copy()
            bounds_properties.pop('formula_terms', None)
            self.implementation.set_properties(bounds, bounds_properties)

            if not g['mask']:
                # ----------------------------------------------------
                # Masking has been turned off, so make sure that there
                # is a fill value recorded on the bounds so that
                # masking may later be applied manually, if
                # required. (Introduced at v1.8.3.)
                # ----------------------------------------------------
                self._set_default_FillValue(bounds, bounds_ncvar)

            bounds_dimensions = g['variable_dimensions'][bounds_ncvar]

#            if bounds_properties.get('units') is not None:
            bounds_data = self._create_data(bounds_ncvar, bounds,
                                            parent_ncvar=ncvar)
#                                            geometry_bounds=(geometry is not None))

#                                            non_compressed_dimensions=nc_dimensions=bounds_dimensions)
#ppp
#            else:
#                bounds_data = self._create_data(ncvar, bounds)
#                self.implementation.set_data_units(bounds_data, properties.get('units'))
 #
 #           if bounds_properties.get('calendar') is None:
 #               self.implementation.set_data_calendar(bounds_data, properties.get('calendar'))
 #               ##
#
#            bounds_data = self._create_data(bounds_ncvar, bounds)
#
#            if bounds_properties.get('units') is None:
#                self.implementation.set_data_units(bounds_data, properties.get('units'))
#
#            if bounds_properties.get('calendar') is None:
#                self.implementation.set_data_calendar(bounds_data, properties.get('calendar'))

#                # Make sure that the bounds dimensions are in the same
#                # order as its parent's dimensions. It is assumed that we
#                # have already checked that the bounds netCDF variable has
#                # appropriate dimensions.
#                c_ncdims = nc.variables[ncvar].dimensions
#                b_ncdims = nc.variables[bounds_ncvar].dimensions
#                c_ndim = len(c_ncdims)
#                b_ndim = len(b_ncdims)
#                if b_ncdims[:c_ndim] != c_ncdims:
#                    axes = [c_ncdims.index(ncdim) for ncdim in b_ncdims[:c_ndim]
#                            if ncdim in c_ncdims]
#                    axes.extend(range(c_ndim, b_ndim))
#                    bounds_data = self._transpose_data(bounds_data,
#                                                       axes=axes, copy=False)
#                # --- End: if

            self.implementation.set_data(bounds, bounds_data, copy=False)

            # Store the netCDF variable name
            self.implementation.nc_set_variable(bounds, bounds_ncvar)

            # Store the netCDF bounds dimension name
            self.implementation.nc_set_dimension(
                bounds,
                g['variable_dimensions'][bounds_ncvar][-1])
            self.implementation.set_bounds(c, bounds, copy=False)

            if not domain_ancillary:
                g['bounds'][field_ncvar][ncvar] = bounds_ncvar

            # --------------------------------------------------------
            # Geometries
            # --------------------------------------------------------
            if (geometry is not None
                and bounds_ncvar in geometry['node_coordinates']):
                # Record the netCDF node dimension name
                count = self.implementation.get_count(bounds)
                node_ncdim = self.implementation.nc_get_sample_dimension(count)
                self.implementation.nc_set_dimension(bounds, node_ncdim)

                geometry_type = geometry['geometry_type']
                if geometry_type is not None:
                    self.implementation.set_geometry(c, geometry_type)

                g['node_coordinates_as_bounds'].add(bounds_ncvar)

                if self.implementation.get_data_ndim(bounds) == 2:
                    # Insert a size 1 part dimension
                    bounds = self.implementation.bounds_insert_dimension(
                        bounds=bounds,
                        position=1)
                    self.implementation.set_bounds(c, bounds, copy=False)

                # Add a node count variable
                nc = geometry.get('node_count')
                if nc is not None:
                    self.implementation.set_node_count(parent=c,
                                                       node_count=nc)

                # Add a part node count variable
                pnc = geometry.get('part_node_count')
                if pnc is not None:
                    self.implementation.set_part_node_count(
                        parent=c,
                        part_node_count=pnc)

                # Add an interior ring variable
                interior_ring = geometry.get('interior_ring')
                if interior_ring is not None:
                    self.implementation.set_interior_ring(
                        parent=c,
                        interior_ring=interior_ring)
       # --- End: if

        # Store the netCDF variable name
        self.implementation.nc_set_variable(c, ncvar)

        if not domain_ancillary:
            g['coordinates'][field_ncvar].append(ncvar)

        # ---------------------------------------------------------
        # Return the bounded variable
        # ---------------------------------------------------------
        return c

    def _create_cell_measure(self, measure, ncvar):
        '''Create a cell measure object.

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

        '''
        g = self.read_vars

        # Initialise the cell measure construct
        cell_measure = self.implementation.initialise_CellMeasure(
            measure=measure)

        # Store the netCDF variable name
        self.implementation.nc_set_variable(cell_measure, ncvar)

        if ncvar in g['external_variables']:
            # The cell measure variable is in an unknown external file
            self.implementation.nc_set_external(construct=cell_measure)
        else:
            # The cell measure variable is in this file or in a known
            # external file
            self.implementation.set_properties(cell_measure,
                                               g['variable_attributes'][ncvar])

            if not g['mask']:
                # ----------------------------------------------------
                # Masking has been turned off, so make sure that there
                # is a fill value recorded on the cell measure so that
                # masking may later be applied manually, if
                # required. (Introduced at v1.8.3.)
                # ----------------------------------------------------
                self._set_default_FillValue(cell_measure, ncvar)

            data = self._create_data(ncvar, cell_measure)
            self.implementation.set_data(cell_measure, data, copy=False)

        return cell_measure

    def _create_Count(self, ncvar, ncdim):
        '''Create a

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

        '''
        g = self.read_vars

        # Initialise the count variable
        variable = self.implementation.initialise_Count()

        # Set the CF properties
        properties = g['variable_attributes'][ncvar]
        sample_ncdim = properties.pop('sample_dimension', None)
        self.implementation.set_properties(variable, properties)

        if not g['mask']:
            # --------------------------------------------------------
            # Masking has been turned off, so make sure that there is
            # a fill value recorded on the variable so that masking
            # may later be applied manually, if required. (Introduced
            # at v1.8.3.)
            # --------------------------------------------------------
            self._set_default_FillValue(variable, ncvar)

        # Set the netCDF variable name
        self.implementation.nc_set_variable(variable, ncvar)

        # Set the netCDF sample dimension name
        if sample_ncdim is not None:
            self.implementation.nc_set_sample_dimension(variable, sample_ncdim)

        # Set the name of the netCDF dimension spaned by the variable
        # (which, for indexed contiguous ragged arrays, will not be the
        # same as the netCDF instance dimension)
        self.implementation.nc_set_dimension(variable, ncdim)

        data = self._create_data(ncvar, variable, uncompress_override=True)
        self.implementation.set_data(variable, data, copy=False)

        return variable

    def _create_Index(self, ncvar, ncdim):
        '''Create a

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

        '''
        g = self.read_vars

        # Initialise the index variable
        variable = self.implementation.initialise_Index()

        # Set the CF properties
        properties = g['variable_attributes'][ncvar]
        instance_ncdim = properties.pop('instance_dimension', None)
        self.implementation.set_properties(variable, properties)

        if not g['mask']:
            # --------------------------------------------------------
            # Masking has been turned off, so make sure that there is
            # a fill value recorded on the variable so that masking
            # may later be applied manually, if required. (Introduced
            # at v1.8.3.)
            # --------------------------------------------------------
            self._set_default_FillValue(variable, ncvar)

        # Set the netCDF variable name
        self.implementation.nc_set_variable(variable, ncvar)

#        # Set the netCDF instance dimension name
#        if instance_ncdim is not None:
#            self.implementation.nc_set_instance_dimension(variable, instance_ncdim)

        # Set the netCDF sample dimension name
        sample_ncdim = ncdim
        self.implementation.nc_set_sample_dimension(variable, sample_ncdim)

        # Set the name of the netCDF dimension spaned by the variable
        # (which, for indexed contiguous ragged arrays, will not be
        # the same as the netCDF sample dimension)
        self.implementation.nc_set_dimension(variable, ncdim)

        # Set the data
        data = self._create_data(ncvar, variable, uncompress_override=True)
        self.implementation.set_data(variable, data, copy=False)

        return variable

    def _create_InteriorRing(self, ncvar, ncdim):
        '''Create a

    .. versionadded:: 1.8.0

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

        '''
        g = self.read_vars

        # Initialise the interior ring variable
        variable = self.implementation.initialise_InteriorRing()

        # Store the netCDF variable name
        self.implementation.nc_set_variable(variable, ncvar)
        self.implementation.nc_set_dimension(variable, ncdim)

        properties = g['variable_attributes'][ncvar]
        self.implementation.set_properties(variable, properties)

        if not g['mask']:
            # --------------------------------------------------------
            # Masking has been turned off, so make sure that there is
            # a fill value recorded on the variable so that masking
            # may later be applied manually, if required. (Introduced
            # at v1.8.3.)
            # --------------------------------------------------------
            self._set_default_FillValue(variable, ncvar)

        data = self._create_data(ncvar, variable)
        self.implementation.set_data(variable, data, copy=False)

        return variable

    def _create_List(self, ncvar):
        '''Create a TODO

    :Parameters:

        ncvar: `str`
            The name of the netCDF list variable.

            *Parameter example:*
               ``ncvar='landpoints'``

    :Returns:

        `List`

        '''
        # Initialise the list variable
        variable = self.implementation.initialise_List()

        # Store the netCDF variable name
        self.implementation.nc_set_variable(variable, ncvar)

        properties = self.read_vars['variable_attributes'][ncvar]
        properties.pop('compress', None)
        self.implementation.set_properties(variable, properties)

        if not self.read_vars['mask']:
            # --------------------------------------------------------
            # Masking has been turned off, so make sure that there is
            # a fill value recorded on the variable so that masking
            # may later be applied manually, if required. (Introduced
            # at v1.8.3.)
            # --------------------------------------------------------
            self._set_default_FillValue(variable, ncvar)

        data = self._create_data(ncvar, variable, uncompress_override=True)
        self.implementation.set_data(variable, data, copy=False)

        return variable

    def _create_NodeCount(self, ncvar):
        '''Create a node count variable.

    .. versionadded:: 1.8.0

    :Parameters:

        ncvar: `str`
            The netCDF node count variable name.

            *Parameter example:*
              ``ncvar='node_count'``

    :Returns:

            Node count variable instance

        '''
        g = self.read_vars

        # Initialise the interior ring variable
        variable = self.implementation.initialise_NodeCount()

        # Store the netCDF variable name
        self.implementation.nc_set_variable(variable, ncvar)

        properties = g['variable_attributes'][ncvar]
        self.implementation.set_properties(variable, properties)

        if not g['mask']:
            # --------------------------------------------------------
            # Masking has been turned off, so make sure that there is
            # a fill value recorded on the variable so that masking
            # may later be applied manually, if required. (Introduced
            # at v1.8.3.)
            # --------------------------------------------------------
            self._set_default_FillValue(variable, ncvar)

        return variable

    def _create_PartNodeCount(self, ncvar, ncdim):
        '''Create a part node count variable.

    .. versionadded:: 1.8.0

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

        '''
        g = self.read_vars

        # Initialise the interior ring variable
        variable = self.implementation.initialise_PartNodeCount()

        # Store the netCDF variable name
        self.implementation.nc_set_variable(variable, ncvar)
        self.implementation.nc_set_dimension(variable, ncdim)

        properties = g['variable_attributes'][ncvar]
        self.implementation.set_properties(variable, properties)

        if not g['mask']:
            # --------------------------------------------------------
            # Masking has been turned off, so make sure that there is
            # a fill value recorded on the variable so that masking
            # may later be applied manually, if required. (Introduced
            # at v1.8.3.)
            # --------------------------------------------------------
            self._set_default_FillValue(variable, ncvar)

        return variable

    def _create_cell_method(self, axes, method, qualifiers):
        '''Create a cell method object.

    :Parameters:

        axes: `tuple`

        method: 'str`

        properties: `dict`

    :Returns:

        `CellMethod`

        '''
        return self.implementation.initialise_CellMethod(axes=axes,
                                                         method=method,
                                                         qualifiers=qualifiers)

    def _create_netcdfarray(self, ncvar, unpacked_dtype=False):
        '''Set the Data attribute of a variable.

    :Parameters:

        ncvar: `str`

        unpacked_dtype: `False` or `numpy.dtype`, optional

    :Returns:

        `NetCDFArray`

        '''
        g = self.read_vars

        variable = g['variables'].get(ncvar)
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

        ndim  = variable.ndim
        shape = variable.shape
        size  = variable.size
        if size < 2:
            size = int(size)

#        if dtype.kind == 'S' and ndim >= 1: #shape[-1] > 1:
        if self._is_char(ncvar) and ndim >= 1:
            # Has a trailing string-length dimension
            strlen = shape[-1]
            shape = shape[:-1]
            size /= strlen
            ndim -= 1
            dtype = numpy.dtype('S{0}'.format(strlen))

        filename = g['variable_filename'][ncvar]

        return self.implementation.initialise_NetCDFArray(
            filename=filename, ncvar=ncvar,
            dtype=dtype,
            ndim=ndim,
            shape=shape,
            size=size,
            mask=g['mask'])

    def _create_data(self, ncvar, construct=None,
                     unpacked_dtype=False, uncompress_override=None,
                     parent_ncvar=None, nc_dimensions=None):
        '''TODO

    :Parameters:

        ncvar: `str`
            The name of the netCDF variable that contains the data.

        construct: optional

        unpacked_dtype: `False` or `numpy.dtype`, optional

        uncompress_override: `bool`, optional

        geometry_boounds: `bool`
            If True then the data are destined to become simple
            geometry coordinate bounds.

    :Returns:

        `Data`

        '''
        g = self.read_vars

        array = self._create_netcdfarray(ncvar,
                                         unpacked_dtype=unpacked_dtype)

        if array is None:
            return None

#        insert_size1_geometry_bounds_part_dimension = geometry_bounds

        units    = g['variable_attributes'][ncvar].get('units', None)
        calendar = g['variable_attributes'][ncvar].get('calendar', None)

        if parent_ncvar is not None and units is None:
            units    = g['variable_attributes'][parent_ncvar].get('units',
                                                                  None)
            calendar = g['variable_attributes'][parent_ncvar].get('calendar',
                                                                  None)

        compression = g['compression']

        dimensions = g['variable_dimensions'][ncvar]

        if ((uncompress_override is not None and not uncompress_override) or
            not compression or
            not set(compression).intersection(dimensions)):
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

                    if ncvar not in c.get('netCDF_variables', (ncvar,)):
                        # This variable is not compressed, even though
                        # it spans a dimension that is compressed for
                        # some other variables For example, this sort
                        # of situation may arise with simple
                        # geometries.
                        continue

                    if 'gathered' in c:
                        # --------------------------------------------
                        # Compression by gathering. Note the
                        # uncompressed dimensions exist as internal
                        # dimensions.
                        # --------------------------------------------
                        c = c['gathered']
                        uncompressed_shape = tuple(
                            [g['internal_dimension_sizes'][dim]
                             for dim in self._ncdimensions(ncvar)])
                        compressed_dimension = (
                            g['variable_dimensions'][ncvar].index(
                                c['sample_dimension'])
                        )
                        array = self._create_gathered_array(
                            gathered_array=self._create_Data(array),
                            uncompressed_shape=uncompressed_shape,
                            compressed_dimension=compressed_dimension,
                            list_variable=c['list_variable'])
                    elif 'ragged_indexed_contiguous' in c:
                        # --------------------------------------------
                        # Contiguous indexed ragged array. Check this
                        # before ragged_indexed and ragged_contiguous
                        # because both of these will exist for an
                        # indexed and contiguous array.
                        # --------------------------------------------
                        c = c['ragged_indexed_contiguous']

                        i = dimensions.index(ncdim)
                        if i != 0:
                            raise ValueError("TODO")

                        uncompressed_shape = list(array.shape)
                        uncompressed_shape[i:i+1] = [
                            c['instance_dimension_size'],
                            c['element_dimension_1_size'],
                            c['element_dimension_2_size']
                        ]
                        uncompressed_shape = tuple(uncompressed_shape)

                        array = self._create_ragged_indexed_contiguous_array(
                            ragged_indexed_contiguous_array=self._create_Data(
                                array),
                            uncompressed_shape=uncompressed_shape,
                            count_variable=c['count_variable'],
                            index_variable=c['index_variable'])

#                        insert_size1_geometry_bounds_part_dimension = False
                    elif 'ragged_contiguous' in c:
                        # --------------------------------------------
                        # Contiguous ragged array
                        # --------------------------------------------
                        c = c['ragged_contiguous']

                        i = dimensions.index(ncdim)
                        if i != 0:
                            raise ValueError("TODO")

                        uncompressed_shape = list(array.shape)
                        uncompressed_shape[i:i+1] = [
                            c['instance_dimension_size'],
                            c['element_dimension_size']
                        ]
                        uncompressed_shape = tuple(uncompressed_shape)

                        array = self._create_ragged_contiguous_array(
                            ragged_contiguous_array=self._create_Data(array),
                            uncompressed_shape=uncompressed_shape,
                            count_variable=c['count_variable'])
                    elif 'ragged_indexed' in c:
                        # --------------------------------------------
                        # Indexed ragged array
                        # --------------------------------------------
                        c = c['ragged_indexed']

                        i = dimensions.index(ncdim)
                        if i != 0:
                            raise ValueError("TODO")

                        uncompressed_shape = list(array.shape)
                        uncompressed_shape[i:i+1] = [
                            c['instance_dimension_size'],
                            c['element_dimension_size']
                        ]
                        uncompressed_shape = tuple(uncompressed_shape)

                        array = self._create_ragged_indexed_array(
                            ragged_indexed_array=self._create_Data(array),
                            uncompressed_shape=uncompressed_shape,
                            index_variable=c['index_variable'])
                    else:
                        raise ValueError("Bad compression vibes. "
                                         "c.keys()={}".format(
                                             list(c.keys())))
        # --- End: if

        return self._create_Data(array, units=units,
                                 calendar=calendar)

    def _create_domain_axis(self, size, ncdim=None):
        '''TODO

    :Parameters:

        size: `int`

        ncdim: `str, optional

        '''
        domain_axis = self.implementation.initialise_DomainAxis(size=size)
        if ncdim is not None:
            self.implementation.nc_set_dimension(construct=domain_axis,
                                                 ncdim=ncdim)

        return domain_axis

    def _create_field_ancillary(self, ncvar):
        '''Create a field ancillary object.

    :Parameters:

        ncvar: `str`
            The netCDF name of the field ancillary variable.

    :Returns:

        `FieldAncillary`
            The new item.

        '''
        # Create a field ancillary object
        field_ancillary = self.implementation.initialise_FieldAncillary()

        # Insert properties
        self.implementation.set_properties(field_ancillary,
                           self.read_vars['variable_attributes'][ncvar],
                           copy=True)

        if not self.read_vars['mask']:
            # --------------------------------------------------------
            # Masking has been turned off, so make sure that there is
            # a fill value recorded on the field ancillary so that
            # masking may later be applied manually, if
            # required. (Introduced at v1.8.3.)
            # --------------------------------------------------------
            self._set_default_FillValue(field_ancillary, ncvar)

        # Insert data
        data = self._create_data(ncvar, field_ancillary)
        self.implementation.set_data(field_ancillary, data, copy=False)

        # Store the netCDF variable name
        self.implementation.nc_set_variable(field_ancillary, ncvar)

        return field_ancillary

    def _parse_cell_methods(self, cell_methods_string, field_ncvar=None):
        '''Parse a CF cell_methods string.

    :Parameters:

        cell_methods_string: `str`
            A CF cell methods string.

    :Returns:

        `list` of `dict`

    **Examples:**

    >>> c = parse_cell_methods('t: minimum within years t: mean over ENSO years)')

        '''
        if field_ncvar:
            attribute = {field_ncvar+':cell_methods': cell_methods_string}

        incorrect_interval = ('Cell method interval',
                              'is incorrectly formatted')

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
        cell_methods = re.sub('\((?=[^\s])' , '( ', cell_methods_string)
        cell_methods = re.sub('(?<=[^\s])\)', ' )', cell_methods).split()

        while cell_methods:
            cm = {}

            axes  = []
            while cell_methods:
                if not cell_methods[0].endswith(':'):
                    break

# TODO Check that "name" ends with colon? How? ('lat: mean
#      (area-weighted) or lat: mean (interval: 1 degree_north comment:
#      area-weighted)')

                axis = cell_methods.pop(0)[:-1]

                axes.append(axis)
            # --- End: while
            cm['axes'] = axes

            if not cell_methods:
                out.append(cm)
                break

            # Method
            cm['method'] = cell_methods.pop(0)

            if not cell_methods:
                out.append(cm)
                break

            # Climatological statistics, and statistics which apply to
            # portions of cells
            while cell_methods[0] in ('within', 'where', 'over'):
                attr = cell_methods.pop(0)
                cm[attr] = cell_methods.pop(0)
                if not cell_methods:
                    break
            # --- End: while
            if not cell_methods:
                out.append(cm)
                break

            # interval and comment
            intervals = []
            if cell_methods[0].endswith('('):
                cell_methods.pop(0)

                if not (re.search('^(interval|comment):$', cell_methods[0])):
                    cell_methods.insert(0, 'comment:')

                while not re.search('^\)$', cell_methods[0]):
                    term = cell_methods.pop(0)[:-1]

                    if term == 'interval':
                        interval = cell_methods.pop(0)
                        if cell_methods[0] != ')':
                            units = cell_methods.pop(0)
                        else:
                            units = None

                        try:
                            parsed_interval = literal_eval(interval)
                        except (SyntaxError, ValueError):
                            if not field_ncvar:
                                raise ValueError(incorrect_interval)

                            self._add_message(
                                field_ncvar, field_ncvar,
                                message=incorrect_interval)
                            return []

                        try:
                            data = self.implementation.initialise_Data(
                                array=parsed_interval,
                                units=units,
                                copy=False)
                        except:
                            if not field_ncvar:
                                raise ValueError(incorrect_interval)

                            self._add_message(
                                    field_ncvar, field_ncvar,
                                    message=incorrect_interval,
                                    attribute=attribute)
                            return []

                        intervals.append(data)
                        continue
                    # --- End: if

                    if term == 'comment':
                        comment = []
                        while cell_methods:
                            if cell_methods[0].endswith(')'):
                                break
                            if cell_methods[0].endswith(':'):
                                break
                            comment.append(cell_methods.pop(0))
                        # --- End: while
                        cm['comment'] = ' '.join(comment)
                # --- End: while

                if cell_methods[0].endswith(')'):
                    cell_methods.pop(0)
            # --- End: if

            n_intervals = len(intervals)
            if n_intervals > 1 and n_intervals != len(axes):
                if not field_ncvar:
                    raise ValueError(incorrect_interval)

                self._add_message(
                    field_ncvar, field_ncvar,
                    message=incorrect_interval,
                    attribute=attribute)
                return []

            if intervals:
                cm['interval'] = intervals

            out.append(cm)
        # --- End: while

        return out

    def _create_formula_terms_ref(self, f, key, coord, formula_terms):
        '''TODO

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

        '''
        g = self.read_vars

        domain_ancillaries = {}
        parameters         = {}

        for term, ncvar in formula_terms.items():
            # The term's value is a domain ancillary of the field, so
            # we put its identifier into the coordinate reference.
            domain_ancillaries[term] = g['domain_ancillary_key'].get(ncvar)

        for name in ('standard_name', 'computed_standard_name'):
            value = self.implementation.get_property(coord, name, None)
            if value is not None:
                parameters[name] = value
        # --- End: for

        datum_parameters = {}
        coordinate_conversion_parameters = {}
        for x, value in parameters.items():
            if x in g['datum_parameters']:
                datum_parameters[x] = value
            else:
                coordinate_conversion_parameters[x] = value
        # --- End: for

        datum = self.implementation.initialise_Datum(
            parameters=datum_parameters)

        coordinate_conversion = (
            self.implementation.initialise_CoordinateConversion(
                parameters=coordinate_conversion_parameters,
                domain_ancillaries=domain_ancillaries))

        coordref = self.implementation.initialise_CoordinateReference()

        self.implementation.set_coordinate_reference_coordinates(
            coordinate_reference=coordref,
            coordinates=[key])

        self.implementation.set_datum(
            coordinate_reference=coordref,
            datum=datum)

        self.implementation.set_coordinate_conversion(
            coordinate_reference=coordref,
            coordinate_conversion=coordinate_conversion)

        return coordref

    def _ncdimensions(self, ncvar):
        '''Return a list of the netCDF dimensions corresponding to a netCDF
    variable.

    If the variable has been compressed then the *implied
    uncompressed* dimensions are returned.

    .. versionadded:: 1.7.0

    :Parameters:

        ncvar: `str`
            The netCDF variable name.

    :Returns:

        `list`
            The list of netCDF dimension names spanned by the netCDF
            variable.

    **Examples:**

    >>> n._ncdimensions('humidity')
    ['time', 'lat', 'lon']

        '''
        g = self.read_vars

        variable = g['variables'][ncvar]

        ncdimensions = list(g['variable_dimensions'][ncvar])

#        if (variable.datatype.kind == 'S' and
#            variable.ndim >= 2): # and variable.shape[-1] > 1):
#            ncdimensions.pop()
        if self._is_char(ncvar) and variable.ndim >= 1:
            # Remove the trailing string-length dimension
            ncdimensions.pop()

        # Check for dimensions which have been compressed. If there are
        # any, then return the netCDF dimensions for the uncompressed
        # variable.
        compression = g['compression']
        if compression and set(compression).intersection(ncdimensions):
            for ncdim in ncdimensions:
                if ncdim in compression:
                    c = compression[ncdim]

                    if ncvar not in c.get('netCDF_variables', (ncvar,)):
                        # This variable is not compressed, even though
                        # it spans a dimension that is compressed for
                        # some other variables For example, this sort
                        # of situation may arise with simple
                        # geometries.
                        continue

                    i = ncdimensions.index(ncdim)

                    if 'gathered' in c:
                        # Compression by gathering
                        ncdimensions[i:i+1] = (
                            c['gathered']['implied_ncdimensions'])
                    elif 'ragged_indexed_contiguous' in c:
                        # Indexed contiguous ragged array.
                        #
                        # Check this before ragged_indexed and
                        # ragged_contiguous because both of these will
                        # exist for an array that is both indexed and
                        # contiguous.
#                        ncdimensions = c['ragged_indexed_contiguous']['implied_ncdimensions']
                        ncdimensions[i:i+1] = c['ragged_indexed_contiguous']['implied_ncdimensions']
                    elif 'ragged_contiguous' in c:
                        # Contiguous ragged array
#                        ncdimensions = c['ragged_contiguous']['implied_ncdimensions']
                        ncdimensions[i:i+1] = c['ragged_contiguous']['implied_ncdimensions']
                    elif 'ragged_indexed' in c:
                        # Indexed ragged array
#                        ncdimensions = c['ragged_indexed']['implied_ncdimensions']
                        ncdimensions[i:i+1] = (
                            c['ragged_indexed']['implied_ncdimensions'])

                    break
        # --- End: if

        return list(map(str, ncdimensions))

    def _create_gathered_array(self, gathered_array=None,
                               uncompressed_shape=None,
                               compressed_dimension=None,
                               list_variable=None):
        '''Create a `Data` object for a compressed-by-gathering netCDF
    variable.

    :Parameters:

        gathered_array: `NetCDFArray`

        list_variable: `List`

    :Returns:

        `Data`

        '''
        uncompressed_ndim  = len(uncompressed_shape)
        uncompressed_size  = int(reduce(operator.mul, uncompressed_shape, 1))

        return self.implementation.initialise_GatheredArray(
            compressed_array=gathered_array,
            ndim=uncompressed_ndim,
            shape=uncompressed_shape,
            size=uncompressed_size,
            compressed_dimension=compressed_dimension,
            list_variable=list_variable,
        )

    def _create_ragged_contiguous_array(self, ragged_contiguous_array,
                                        uncompressed_shape=None,
                                        count_variable=None):
        '''Create a `Data` object for a compressed-by-contiguous-ragged-array
    netCDF variable.

    :Parameters:

        ragged_contiguous_array: `Data`

        uncompressed_shape; `tuple`

        count_variable: `Count`

    :Returns:

        `Data`

        '''
        uncompressed_ndim  = len(uncompressed_shape)
        uncompressed_size  = int(reduce(operator.mul, uncompressed_shape, 1))

        return self.implementation.initialise_RaggedContiguousArray(
            compressed_array=ragged_contiguous_array,
            ndim=uncompressed_ndim,
            shape=uncompressed_shape,
            size=uncompressed_size,
            count_variable=count_variable)

    def _create_ragged_indexed_array(self, ragged_indexed_array,
                                     uncompressed_shape=None,
                                     index_variable=None):
        '''Create a `Data` object for a compressed-by-indexed-ragged-array
    netCDF variable.

    :Returns:

        `Data`

        '''
        uncompressed_ndim  = len(uncompressed_shape)
        uncompressed_size  = int(reduce(operator.mul, uncompressed_shape, 1))

        return self.implementation.initialise_RaggedIndexedArray(
            compressed_array=ragged_indexed_array,
            ndim=uncompressed_ndim,
            shape=uncompressed_shape,
            size=uncompressed_size,
            index_variable=index_variable)

    def _create_ragged_indexed_contiguous_array(
            self,
            ragged_indexed_contiguous_array,
            uncompressed_shape=None,
            count_variable=None,
            index_variable=None):
        '''Create a `Data` object for a
    compressed-by-indexed-contiguous-ragged-array netCDF variable.

    :Returns:

        `Data`

        '''
        uncompressed_ndim  = len(uncompressed_shape)
        uncompressed_size  = int(reduce(operator.mul, uncompressed_shape, 1))

        return self.implementation.initialise_RaggedIndexedContiguousArray(
            compressed_array=ragged_indexed_contiguous_array,
            ndim=uncompressed_ndim,
            shape=uncompressed_shape,
            size=uncompressed_size,
            count_variable=count_variable,
            index_variable=index_variable)

    def _create_Data(self, array=None, units=None, calendar=None,
                     ncvar=None, **kwargs):
        '''TODO

    :Parameters:

        ncvar: `str`
            The netCDF variable from which to get units and calendar.

        '''
#        g = self.read_vars

        data = self.implementation.initialise_Data(array=array,
                                                   units=units,
                                                   calendar=calendar,
                                                   copy=False,
                                                   **kwargs)

#        if insert_size1_geometry_bounds_part_dimension:
#            self.implementation.data_insert_dimension_inplace(data, position=1)

        return data

    def _copy_construct(self, construct_type, field_ncvar, ncvar):
        '''Return a copy of an existing construct.

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

        '''
        g = self.read_vars

        component_report = g['component_report'].get(ncvar)

        if component_report is not None:
            for var, report in component_report.items():
                g['dataset_compliance'][field_ncvar]['non-compliance'].setdefault(var, []).extend(
                    report)
        # --- End: if

        return self.implementation.copy_construct(g[construct_type][ncvar])

    # ================================================================
    # Methods for checking CF compliance
    #
    # These methods (whose names all start with "_check") check the
    # minimum required for mapping the file to CFDM structural
    # elements. General CF compliance is not checked (e.g. whether or
    # not grid mapping variable has a grid_mapping_name attribute).
    # ================================================================
    def _check_bounds(self, field_ncvar, parent_ncvar, attribute,
                      bounds_ncvar, geometry=False):
        '''TODO

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

        '''
        attribute = {parent_ncvar+':'+attribute: bounds_ncvar}

        missing_variable      = ('Bounds variable', 'is not in file')
        incorrect_dimensions  = ('Bounds variable',
                                 'spans incorrect dimensions')

        g = self.read_vars

        if bounds_ncvar not in g['internal_variables']:
            self._add_message(field_ncvar, bounds_ncvar,
                              message=missing_variable,
                              attribute=attribute,
                              variable=parent_ncvar)
            return False

        ok = True

        if geometry:
            if bounds_ncvar not in geometry.get('node_coordinates', ()):
                self._add_message(field_ncvar, bounds_ncvar,
                                  message=('Node coordinate variable',
                                           'not in node_coordinates'),
                                  attribute=attribute,
                                  variable=parent_ncvar)
                ok = False
        else:
            c_ncdims = self._ncdimensions(parent_ncvar)
            b_ncdims = self._ncdimensions(bounds_ncvar)

            if len(b_ncdims) == len(c_ncdims) + 1:
                if c_ncdims != b_ncdims[:-1]:
                    self._add_message(
                        field_ncvar, bounds_ncvar,
                        message=incorrect_dimensions,
                        attribute=attribute,
                        dimensions=g['variable_dimensions'][bounds_ncvar],
                        variable=parent_ncvar)
                    ok = False

            else:
                self._add_message(
                    field_ncvar, bounds_ncvar,
                    message=incorrect_dimensions,
                    attribute=attribute,
                    dimensions=g['variable_dimensions'][bounds_ncvar],
                    variable=parent_ncvar)
                ok = False
        # --- End: if

        return ok

    def _check_cell_measures(self, field_ncvar, string, parsed_string):
        '''Checks requirements

    * 7.2.requirement.1
    * 7.2.requirement.3
    * 7.2.requirement.4

    :Parameters:

        field_ncvar: `str`

        string: `str`
            The value of the netCDF cell_measures attribute.

        parsed_string: `list`

    :Returns:

        `bool`

        '''
        attribute = {field_ncvar+':cell_measures': string}

        incorrectly_formatted = ('cell_measures attribute',
                                 'is incorrectly formatted')
        incorrect_dimensions = ('Cell measures variable',
                                'spans incorrect dimensions')
        missing_variable = (
            'Cell measures variable',
            'is not in file nor referenced by the external_variables global attribute')

        g = self.read_vars

        if not parsed_string:
            self._add_message(field_ncvar, field_ncvar,
                              message=incorrectly_formatted,
                              attribute=attribute,
                              conformance='7.2.requirement.1')
            return False

        parent_dimensions  = self._ncdimensions(field_ncvar)
        external_variables = g['external_variables']

        ok = True
        for x in parsed_string:
            measure, values = list(x.items())[0]
            if len(values) != 1:
                self._add_message(field_ncvar, field_ncvar,
                                  message=incorrectly_formatted,
                                  attribute=attribute,
                                  conformance='7.2.requirement.1')
                ok = False
                continue

            ncvar = values[0]

            unknown_external = (ncvar in external_variables)

            # Check that the variable exists in the file, or if not
            # that it is listed in the 'external_variables' global
            # file attribute
            if (not unknown_external and ncvar not in g['variables']):
                self._add_message(field_ncvar, ncvar,
                                  message=missing_variable,
                                  attribute=attribute,
                                  conformance='7.2.requirement.3')
                ok = False
                continue

            if not unknown_external:
                dimensions = self._ncdimensions(ncvar)
                if (not unknown_external and not
                    self._dimensions_are_subset(ncvar, dimensions,
                                                parent_dimensions)):
                    # The cell measure variable's dimensions do NOT span a
                    # subset of the parent variable's dimensions.
                    self._add_message(
                        field_ncvar, ncvar,
                        message=incorrect_dimensions,
                        attribute=attribute,
                        dimensions=g['variable_dimensons'][ncvar],
                        conformance='7.2.requirement.4')
                    ok = False
                    continue
        # --- End: for

        return ok

    def _check_ancillary_variables(self, field_ncvar, string,
                                   parsed_string):
        '''Checks requirements

    :Parameters:

        field_ncvar: `str`

        ancillary_variables: `str`
            The value of the netCDF ancillary_variables attribute.

        parsed_ancillary_variables: `list`

    :Returns:

        `bool`

        '''
        attribute = {field_ncvar+':ancillary_variables': string}

        incorrectly_formatted = ('ancillary_variables attribute',
                                 'is incorrectly formatted')
        missing_variable = ('Ancillary variable',
                            'is not in file')
        incorrect_dimensions = ('Ancillary variable',
                                'spans incorrect dimensions')

        g = self.read_vars

        if not parsed_string:
            d = self._add_message(field_ncvar, field_ncvar,
                                  message=incorrectly_formatted,
                                  attribute=attribute)

            # Though an error of sorts, set as warning; read not terminated
            logger.debug(
                "    Error processing netCDF variable {}: {}".format(
                    field_ncvar, d['reason'])
            )  # pragma: no cover

            return False

        parent_dimensions = self._ncdimensions(field_ncvar)

        ok = True
        for ncvar in parsed_string:
            # Check that the variable exists in the file
            if ncvar not in g['internal_variables']:
                self._add_message(field_ncvar, ncvar,
                                  message=missing_variable,
                                  attribute=attribute)
                return False

            if not self._dimensions_are_subset(ncvar,
                                               self._ncdimensions(ncvar),
                                               parent_dimensions):
                # The ancillary variable's dimensions do NOT span a
                # subset of the parent variable's dimensions
                self._add_message(field_ncvar, ncvar,
                                  message=incorrect_dimensions,
                                  attribute=attribute,
                                  dimensions=g['variable_dimensions'][ncvar])
                ok = False
                continue
        # --- End: for

        return ok

    def _check_auxiliary_scalar_coordinate(self, field_ncvar,
                                           coord_ncvar, string):
        '''Checks requirements

      * 5.requirement.5
      * 5.requirement.6

    :Parameters:

        field_ncvar: `str`

    :Returns:

        `bool`

        '''
        attribute = {field_ncvar+':coordinates': string}

        incorrectly_formatted = ('coordinate attribute',
                                 'is incorrectly formatted')
        missing_variable = ('Auxiliary/scalar coordinate variable',
                            'is not in file')
        incorrect_dimensions = ('Auxiliary/scalar coordinate variable',
                                'spans incorrect dimensions')

        g = self.read_vars

        if coord_ncvar not in g['internal_variables']:
            self._add_message(field_ncvar, coord_ncvar,
                              message=missing_variable,
                              attribute=attribute,
                              conformance='5.requirement.5')
            return False

        # Check that the variable's dimensions span a subset of the
        # parent variable's dimensions (allowing for char variables
        # with a trailing dimension)
        dimensions        = self._ncdimensions(coord_ncvar)
        parent_dimensions = self._ncdimensions(field_ncvar)

        if not self._dimensions_are_subset(coord_ncvar,
                                           self._ncdimensions(coord_ncvar),
                                           self._ncdimensions(field_ncvar)):
            d = self._add_message(
                field_ncvar, coord_ncvar,
                message=incorrect_dimensions,
                attribute=attribute,
                dimensions=g['variable_dimensions'][coord_ncvar],
                conformance='5.requirement.6')
            return False

        return True

    def _dimensions_are_subset(self, ncvar, dimensions, parent_dimensions):
        '''Return True if TODO

        '''
        if not set(dimensions).issubset(parent_dimensions):
#            if not (self.read_vars['variables'][ncvar].datatype.kind == 'S' and
#                    set(dimensions[:-1]).issubset(parent_dimensions)):
            if not (self._is_char(ncvar) and
                    set(dimensions[:-1]).issubset(parent_dimensions)):
                return False

        return True

    def _check_grid_mapping(self, field_ncvar, grid_mapping,
                            parsed_grid_mapping):
        '''Checks requirements

      * 5.6.requirement.1
      * 5.6.requirement.2
      * 5.6.requirement.3

    :Parameters:

        field_ncvar: `str`

        grid_mapping: `str`

        parsed_grid_mapping: `dict`

    :Returns:

        `bool`

        '''
        attribute = {field_ncvar+':grid_mapping': grid_mapping}

        incorrectly_formatted = ('grid_mapping attribute',
                                 'is incorrectly formatted')
        missing_variable  = ('grid_mapping variable',
                             'is not in file')
        coordinate_not_in_file = ('Grid mapping coordinate variable',
                                  'is not in file')
        coordinate_not_in_data_variable = ('Grid mapping coordinate variable',
                                           'is not used by data variable')

        g = self.read_vars

        if not parsed_grid_mapping:
            self._add_message(field_ncvar, field_ncvar,
                              message=incorrectly_formatted,
                              attribute=attribute,
                              conformance='5.6.requirement.1')
            return False

        ok = True
        for x in parsed_grid_mapping:
            grid_mapping_ncvar, values = list(x.items())[0]
            if grid_mapping_ncvar not in g['internal_variables']:
                ok = False
                self._add_message(field_ncvar, grid_mapping_ncvar,
                                  message=missing_variable,
                                  attribute=attribute,
                                  conformance='5.6.requirement.2')

            for coord_ncvar in values:
                if coord_ncvar not in g['internal_variables']:
                    ok = False
                    self._add_message(field_ncvar, coord_ncvar,
                                      message=coordinate_not_in_file,
                                      attribute=attribute,
                                      conformance='5.6.requirement.3')
        # --- End: for

        if not ok:
            return False

        return True

    def _check_compress(self, parent_ncvar, compress, parsed_compress):
        '''TODO

        '''
        attribute = {parent_ncvar+':compress': compress}

        incorrectly_formatted = ('compress attribute',
                                 'is incorrectly formatted')
        missing_dimension = ('Compressed dimension',
                             'is not in file')

        if not parsed_compress:
            self._add_message(None, parent_ncvar,
                              message=incorrectly_formatted,
                              attribute=attribute)
            return False

        ok = True

        dimensions = self.read_vars['internal_dimension_sizes']

        for ncdim in parsed_compress:
            if ncdim not in dimensions:
                self._add_message(None, parent_ncvar,
                                  message=missing_dimension,
                                  attribute=attribute)
                ok = False
                continue
        # --- End: for

        return ok

    def _check_node_coordinates(self, field_ncvar, geometry_ncvar,
                                node_coordinates,
                                parsed_node_coordinates):
        '''TODO

        '''
        attribute = {geometry_ncvar+':node_coordinates': node_coordinates}

        g = self.read_vars

        incorrectly_formatted = ('node_coordinates attribute',
                                 'is incorrectly formatted')
        missing_attribute = ('node_coordinates attribute',
                             'is missing')
        missing_variable = ('Node coordinate variable',
                            'is not in file')

        if node_coordinates is None:
            self._add_message(field_ncvar, geometry_ncvar,
                              message=missing_attribute,
                              attribute=attribute)
            return False

        if not parsed_node_coordinates:
            # There should be at least one node coordinate variable
            self._add_message(field_ncvar, geometry_ncvar,
                              message=incorrectly_formatted,
                              attribute=attribute)
            return False

        ok = True

        for ncvar in parsed_node_coordinates:
            # Check that the node coordinate variable exists in the
            # file
            if ncvar not in g['internal_variables']:
                self._add_message(field_ncvar, ncvar,
                                  message=missing_variable,
                                  attribute=attribute)
                ok = False
                continue
        # --- End: for

        return ok

    def _check_node_count(self, field_ncvar, geometry_ncvar,
                          node_count, parsed_node_count):
        '''TODO

        '''
        attribute = {geometry_ncvar+':node_count': node_count}

        g = self.read_vars

        if node_count is None:
            return True

        incorrectly_formatted = ('node_count attribute',
                                 'is incorrectly formatted')
        missing_variable = ('Node count variable',
                            'is not in file')

        if len(parsed_node_count) != 1:
            self._add_message(field_ncvar, geometry_ncvar,
                              message=incorrectly_formatted,
                              attribute=attribute)
            return False

        ok = True

        for ncvar in parsed_node_count:
            # Check that the node count variable exists in the file
            if ncvar not in g['internal_variables']:
                self._add_message(field_ncvar, ncvar,
                                  message=missing_variable,
                                  attribute=attribute)
                ok = False
                continue
        # --- End: for

        return ok

    def _check_part_node_count(self, field_ncvar, geometry_ncvar,
                               part_node_count, parsed_part_node_count):
        '''TODO

        '''
        if part_node_count is None:
            return True

        attribute = {geometry_ncvar+':part_node_count': part_node_count}

        g = self.read_vars

        incorrectly_formatted = ('part_node_count attribute',
                                 'is incorrectly formatted')
        missing_variable = ('Part node count variable',
                            'is not in file')

        if len(parsed_part_node_count) != 1:
            self._add_message(field_ncvar, geometry_ncvar,
                              message=incorrectly_formatted,
                              attribute=attribute)
            return False

        ok = True

        for ncvar in parsed_part_node_count:
            # Check that the variable exists in the file
            if ncvar not in g['internal_variables']:
                self._add_message(field_ncvar, ncvar,
                                  message=missing_variable,
                                  attribute=attribute)
                ok = False
                continue
        # --- End: for

        return ok

    def _check_interior_ring(self, field_ncvar, geometry_ncvar,
                          interior_ring, parsed_interior_ring):
        '''TODO

        '''
        if interior_ring is None:
            return True

        attribute = {geometry_ncvar+':interior_ring': interior_ring}

        g = self.read_vars

        incorrectly_formatted = ('interior_ring attribute',
                                 'is incorrectly formatted')
        missing_variable = ('Interior ring variable',
                            'is not in file')

        if not parsed_interior_ring:
            self._add_message(field_ncvar, geometry_ncvar,
                              message=incorrectly_formatted,
                              attribute=attribute)
            return False

        ok = True

        if len(parsed_interior_ring) != 1:
            self._add_message(field_ncvar, ncvar,
                              message=incorrectly_formatted,
                              attribute=attribute)
            return False

        for ncvar in parsed_interior_ring:
            # Check that the variable exists in the file
            if ncvar not in g['internal_variables']:
                self._add_message(field_ncvar, ncvar,
                                  message=missing_variable,
                                  attribute=attribute)
                ok = False
                continue
        # --- End: for

        return ok

    def _check_instance_dimension(self, parent_ncvar, instance_dimension):
        '''asdasd

    .. versionadded:: 1.7.0

    CF-1.7 Appendix A

    * instance_dimension: An attribute which identifies an index
                          variable and names the instance dimension to
                          which it applies. The index variable
                          indicates that the indexed ragged array
                          representation is being used for a
                          collection of features.

        '''
        attribute = {parent_ncvar+':instance_dimension': instance_dimension}

        missing_dimension = ('Instance dimension', 'is not in file')

        if instance_dimension not in self.read_vars['internal_dimension_sizes']:
            self._add_message(None, parent_ncvar,
                              message=missing_dimension,
                              attribute=attribute)
            return False

        return True

#    def _check_geometry_dimension(self, parent_ncvar, geometry_dimension):
#        '''TODO
#
#    .. versionadded:: 1.8.0
#
#        '''
#        attribute={parent_ncvar+':geometry_dimension': geometry_dimension}
#
#        # Check that the geometry dimension name is a netCDF dimension
#        ok = (geometry_dimension in self.read_vars['internal_dimension_sizes'])
#
#        if not ok:
#            self._add_message(None, geometry_ncvar,
#                              message=('geometry_dimension attribute', 'does not name a dimension'),
#                              attribute=attribute)
#
#        return ok

    def _check_sample_dimension(self, parent_ncvar, sample_dimension):
        '''asdasd

    .. versionadded:: 1.7.0

    CF-1.7 Appendix A

    * sample_dimension: An attribute which identifies a count variable
                        and names the sample dimension to which it
                        applies. The count variable indicates that the
                        contiguous ragged array representation is
                        being used for a collection of features.

        '''
        # Check that the sample dimension name is a netCDF dimension
        return sample_dimension in self.read_vars['internal_dimension_sizes']

    def _split_string_by_white_space(self, parent_ncvar, string):
        '''Split a string by white space.

        '''
        if string is None:
            return []

        try:
            return string.split()
        except AttributeError:
            return []

    def _parse_grid_mapping(self, parent_ncvar, string):
        '''TODO

    .. versionadded:: 1.7.0

        '''
        g = self.read_vars
        if g['CF>=1.6']:
            return self._parse_x(parent_ncvar, string)
        else:
            # Pre v1.6, the grid mapping attribute may only point to a
            # single netCDF variable
            out = self._split_string_by_white_space(parent_ncvar, string)
            if len(out) == 1:
                return [{out[0]: []}]

            return []

    def _parse_x(self, parent_ncvar, string):
        '''TODO

    .. versionadded:: 1.7.0

        '''
        # ============================================================
        # Thanks to Alan Iwi for creating these regular expressions
        # ============================================================

        def subst(s):
            "substitute tokens for WORD and SEP (space or end of string)"
            return s.replace('WORD', r'[A-Za-z0-9_]+').replace(
                'SEP', r'(\s+|$)')

        out = []

        pat_value = subst('(?P<value>WORD)SEP')
        pat_values = '({})+'.format(pat_value)

        pat_mapping = (
            subst('(?P<mapping_name>WORD):SEP(?P<values>{})'.format(
                pat_values)))
        pat_mapping_list = '({})+'.format(pat_mapping)

        pat_all = (
            subst('((?P<sole_mapping>WORD)|(?P<mapping_list>{}))$'.format(
                pat_mapping_list)))

        m = re.match(pat_all, string)

        if m is None:
            return []

        sole_mapping = m.group('sole_mapping')
        if sole_mapping:
            out.append({sole_mapping: []})
        else:
            mapping_list = m.group('mapping_list')
            for mapping in re.finditer(pat_mapping, mapping_list):
                term = mapping.group('mapping_name')
                values = [value.group('value')
                          for value in re.finditer(pat_value,
                                                   mapping.group('values'))
                ]
                out.append({term: values})
        # --- End: if

        return out

# --- End: class

