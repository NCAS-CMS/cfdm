import operator
import re
import struct

from ast import literal_eval
from copy import deepcopy

from collections import OrderedDict

import numpy

#from ....functions import abspath

from .. import IORead


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
    }

    def _dereference(self, ncvar):
        '''Decrement by one the reference count to a netCDF variable.

:Examples 1:

>>> r._dereference('longitude')

:Parameters:

    ncvar: `str`
        The netCDf variable name.

:Returns:

    out: `int`
        The new reference count.

        '''
        r = self.read_vars['references'].get(ncvar, 0)
        r -= 1
        if r < 0:
            r = 0

        self.read_vars['references'][ncvar] = r
        return r
    #--- End: def 

    def _is_unreferenced(self, ncvar):
        '''Return True if the netCDF variable is not referenced by any other
netCDF variable.

:Examples 1:

>>> x = r._is_unreferenced('tas')

:Parameters:

    ncvar: `str`
        The netCDf variable name.

:Returns:

    out: `bool`

        '''
        return self.read_vars['references'].get(ncvar, 0) <= 0
    #--- End: def

    def _reference(self, ncvar):
        '''Increment by one the reference count to a netCDF variable.

:Examples 1:

>>> r._reference('longitude')

:Parameters:

    ncvar: `str`
        The netCDf variable name.

:Returns:

    out: `int`
        The new reference count.


        '''
        r = self.read_vars['references'].setdefault(ncvar, 0)
        r += 1
        self.read_vars['references'][ncvar] = r
        return r
    #--- End: def 

    def file_close(self):
        '''Close the netCDF files that have been read.

:Returns:

    `None`

        '''
        for nc in self.read_vars['datasets']:
            nc.close()
    #--- End: def
        
    @staticmethod
    def file_type(filename):
        '''Find the format of a file.
    
:Parameters:
    
    filename: `str`
        The file name.
    
:Returns:
 
    out: `str`
        The format type of the file.
    
:Examples:

>>> filetype = n.file_type(filename)
    
    '''
        # ----------------------------------------------------------------
        # Assume that URLs are in netCDF format
        # ----------------------------------------------------------------
        if filename.startswith('http://'):
           return 'netCDF'
    
        # ----------------------------------------------------------------
        # netCDF
        # ----------------------------------------------------------------
        if netcdf.is_netcdf_file(filename):
            return 'netCDF'
    #--- End: def
    
    def file_open(self, filename):
        '''Open the netCDf file for reading.

:Returns:

    out: `netCDF.Dataset`

        '''
        return self.implementation.get_class('NetCDF').file_open(filename, 'r')
    #--- End: def        

    def get_coordinates(self, f):
       '''
       '''
       return f.coordinates()
    #-- End: def

    def get_ncvar(self, construct, *default):
       '''
       '''
       return construct.get_ncvar(*default)
    #-- End: def

    def get_max(self, data):
        '''
        '''
        return int(data.max())

    def get_property(self, construct, prop, *default):
       '''
       '''
       return construct.get_property(prop, *default)
    #-- End: def

    def get_size(self, x):
        '''
        '''
        return x.size

    @classmethod    
    def is_netcdf_file(cls, filename):
        '''Return True if the file is a netCDF file.
    
Note that the file type is determined by inspecting the file's
contents and any file suffix is not not considered.

:Examples 1:

>>> x = n.is_netcdf_file(filename)

:Parameters:

    filename: `str`

:Returns:

    out: `bool`

:Examples 2:

>>> if n.is_netcdf_file(filename):
...     return 'netCDF'

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
    
        if magic_number in (21382211, 1128547841, 1178880137, 38159427):
            return True
        else:
            return False
    #--- End: def

    def read(self, filename, field=(), verbose=False, uncompress=True,
             external_files=(), extra_read_vars=None,
             _scan_only=False, _debug=False):
        '''Read fields from a netCDF file on disk or from an OPeNDAP server
location.

The file may be big or little endian.

NetCDF dimension names are stored in the `ncdim` attributes of the
field's DomainAxis objects and netCDF variable names are stored in the
`ncvar` attributes of the field and its components (coordinates,
coordinate bounds, cell measures and coordinate references, domain
ancillaries, field ancillaries).

:Parameters:

    filename: `str` or `file`
        A string giving the file name or OPenDAP URL, or an open file
        object, from which to read fields. Note that if a file object
        is given it will be closed and reopened.

    field: sequence of `str`, optional
        Create independent fields from field components. The *field*
        parameter may be one, or a sequence, of:

          ==========================  ================================
          *field*                     Field components
          ==========================  ================================
          ``'auxiliary_coordinate'``  Auxiliary coordinate objects
          ``'cell_measure'``          Cell measure objects
          ``'dimension_coordinate'``  Dimension coordinate objects
          ``'domain_ancillary'``      Domain ancillary objects
          ``'field_ancillary'``       Field ancillary objects
          ``'all'``                   All of the above
          ==========================  ================================

            *Example:*
              To create fields from auxiliary coordinate objects:
              ``field=['auxiliarycoordinate']``.

            *Example:*
              To create fields from domain ancillary and cell measure
              objects: ``field=['domain_ancillary', 'cell_measure']``.

    verbose: `bool`, optional
        If True then print information to stdout.
    
:Returns:

    out: `list`
        The fields in the file.

:Examples:

>>> f = cf.netcdf.read('file.nc')
>>> type(f)
<class 'cf.field.FieldList'>
>>> f
[<CF Field: pmsl(30, 24)>,
 <CF Field: z-squared(17, 30, 24)>,
 <CF Field: temperature(17, 30, 24)>,
 <CF Field: temperature_wind(17, 29, 24)>]

>>> cf.netcdf.read('file.nc')[0:2]
[<CF Field: pmsl(30, 24)>,
 <CF Field: z-squared(17, 30, 24)>]

>>> cf.netcdf.read('file.nc', units='K')
[<CF Field: temperature(17, 30, 24)>,
 <CF Field: temperature_wind(17, 29, 24)>]

>>> cf.netcdf.read('file.nc')[0]
<CF Field: pmsl(30, 24)>

        '''
        # ------------------------------------------------------------
        # Initialise netCDF read parameters
        # ------------------------------------------------------------
        self.read_vars = {
            #
            'new_dimensions': {},
            #
            'formula_terms': {},
            #
            'compression': {},
            # Flag on whether or not to uncompress compressed variables
            'uncompress' : uncompress,
            # Chatty?
            'verbose': verbose,
            # Debug  print statements?
            '_debug': _debug   ,
            
            'read_report': {None: {'components': {}}},
            'component_report' : {},
            
            'auxiliary_coordinate' : {},
            'cell_measure'         : {},
            'dimension_coordinate' : {},
            'domain_ancillary'     : {},
            'domain_ancillary_key' : None,
            'field_ancillary'      : {},
            
            'coordinates' : {},
            
            'bounds': {},

            # Vertical coordinate reference constructs, keyed by the
            # netCDF variable name of their parent parametric vertical
            # coordinate variable.
            #
            # E.g. {'ocean_s_coordinate': <CoordinateReference: ocean_s_coordinate>}
            'vertical_crs': {},

            # Geometry containers, keyed by their netCDF variable name.
            #
            # E.g. {'geometry_container': {
            #           'geometry_type'   : "polygon",
            #           'node_count'      : "node_count",
            #           'node_coordinates': ["x", "y"],
            #           'part_node_count  : "part_node_count",
            #           'interior_ring'   : "interior_ring"}
            #      }
            'geometries': {},
            
            'do_not_create_field':  set(),
            'references': {},

            # The collection of external variables that are actually
            # referenced from within the file
            'referenced_external_variables': set(),
        }
        g = self.read_vars

        # ------------------------------------------------------------
        # Add custom read vars
        # ------------------------------------------------------------
        if extra_read_vars:
            g.update(deepcopy(extra_read_vars))
        
        if isinstance(filename, file):
            name = filename.name
            filename.close()
            filename = name

        compression = {}
        
        # ----------------------------------------------------------------
        # Parse field parameter
        # ----------------------------------------------------------------
        try:
            iter(field)
        except TypeError:
            raise ValueError(
                "Can't read: Bad parameter value: field={!r}".format(field))
               
        if 'all' in field:
            field = ('auxiliary_coordinate',
                     'cell_measure',
                     'domain_ancillary',
                     'dimension_coordinate',
                     'field_ancillary')
    
        g['fields'] = field
        
#        filename = abspath(filename)
        g['filename'] = filename

        # ------------------------------------------------------------
        # Open the netCDF file to be read
        # ------------------------------------------------------------
        nc = self.file_open(filename)
        g['nc'] = nc
        
        if _debug:
            print 'Reading netCDF file:', filename
            print '    Input netCDF dataset =',nc
    
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
                        global_attributes[attr] = value.encode(errors='ignore')          
                else:
                    global_attributes[attr] = value     
            except UnicodeDecodeError:
                pass
        #--- End: for
        
        g['global_attributes'] = global_attributes
        if _debug:
            print '    global attributes:', g['global_attributes']

        # ------------------------------------------------------------
        # Create a dictionary keyed by netCDF variable names where
        # each key's value is a dictionary of that variable's nc
        # attributes. E.g. attributes['tas']['units']='K'
        # ------------------------------------------------------------
        variable_attributes = {}
        variable_dimensions = {}
        variable_dataset    = {}
        variables           = {}
        for ncvar in nc.variables:
            variable = nc.variables[ncvar]
            
            variable_attributes[ncvar] = {}
            for attr in map(str, variable.ncattrs()):
                try:
                    variable_attributes[ncvar][attr] = variable.getncattr(attr)
                    if isinstance(variable_attributes[ncvar][attr], basestring):
                        try:
                            variable_attributes[ncvar][attr] = str(variable_attributes[ncvar][attr])
                        except UnicodeEncodeError:
                            variable_attributes[ncvar][attr] = variable_attributes[ncvar][attr].encode(errors='ignore')
                except UnicodeDecodeError:
                    pass
            #--- End: for

            variable_dimensions[ncvar] = tuple(variable.dimensions)

            variable_dataset[ncvar] = nc
            
            variables[ncvar] = variable
        #--- End: for

        # The netCDF attributes for each variable
        g['variable_attributes'] = variable_attributes

        # The netCDF dimensions for each variable
        g['variable_dimensions'] = variable_dimensions

        # The netCDF4 dataset object for each variable
        g['variable_dataset'] = variable_dataset

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
        for name, dimension in nc.dimensions.iteritems():
            internal_dimension_sizes[name] = dimension.size

        g['internal_dimension_sizes'] = internal_dimension_sizes
 
        if _debug:
            print '    netCDF dimensions:', internal_dimension_sizes
    
        # ------------------------------------------------------------
        # List variables
        #
        # Identify and parse all list variables
        # ------------------------------------------------------------
        for ncvar, dimensions in variable_dimensions.iteritems():
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
        # DSG variables  (>= CF-1.6)
        #
        # Identify and parse all DSG count and DSG index variables
        # ------------------------------------------------------------
        featureType = g['global_attributes'].get('featureType')
        if featureType is not None:
            g['featureType'] = featureType

            sample_dimension = None
            for ncvar, attributes in variable_attributes.iteritems():
                if 'sample_dimension' not in attributes:
                    continue
                
                # ----------------------------------------------------
                # This variable is a count variable for DSG
                # contiguous ragged arrays
                # ----------------------------------------------------
                sample_dimension = attributes['sample_dimension']
                cf_compliant = self._check_sample_dimension(ncvar,
                                                            sample_dimension)
                if not cf_compliant:
                    sample_dimension = None
                else:
                    element_dimension_2 = self._parse_ragged_contiguous_compression(
                        ncvar,
                        sample_dimension)

                    # Do not attempt to create a field from a
                    # count variable
                    g['do_not_create_field'].add(ncvar)
            #--- End: for

            instance_dimension = None
            for ncvar, attributes in variable_attributes.iteritems():
                if 'instance_dimension' not in attributes:
                    continue

                # ----------------------------------------------------
                # This variable is an index variable for DSG
                # indexed ragged arrays
                # ----------------------------------------------------
                instance_dimension = attributes['instance_dimension']
                cf_compliant = self._check_instance_dimension(
                    ncvar,
                    instance_dimension)
                if not cf_compliant:
                    instance_dimension = None
                else:
                    element_dimension_1 = self._parse_indexed_compression(
                        ncvar,
                        instance_dimension)

                    # Do not attempt to create a field from a
                    # index variable
                    g['do_not_create_field'].add(ncvar)
            #--- End: for

            if (sample_dimension   is not None and
                instance_dimension is not None):
                # ----------------------------------------------------
                # There are DSG indexed contiguous ragged arrays
                # ----------------------------------------------------
                self._parse_indexed_contiguous_compression(sample_dimension,
                                                           instance_dimension)
        #--- End: if

        # ------------------------------------------------------------
        # Geometry variables (>= CF-1.8)
        #
        # Identify and parse all geometry container variables
        # ------------------------------------------------------------
        for ncvar, attributes in variable_attributes.iteritems():
            if 'geometry' not in attributes:
                continue
            
            geometry_ncvar = attributes['geometry']
            self._parse_geometry(ncvar, geometry_ncvar, variable_attributes)

            # Do not attempt to create a field from a geometry
            # container variable
            g['do_not_create_field'].add(geometry_ncvar)

        # ------------------------------------------------------------
        # External variables
        # ------------------------------------------------------------
        external_variables = global_attributes.pop('external_variables', None)
        parsed_external_variables = self._split_by_white_space(None, external_variables)
        parsed_external_variables = self._check_external_variables(
            external_variables, parsed_external_variables)
        g['external_variables'] = set(parsed_external_variables)
            
        #
        if _scan_only:
            return self.read_vars

        #
        if external_files and external_variables:
            self._get_variables_from_external_files(external_files)
                
        # ------------------------------------------------------------
        # Convert every netCDF variable to a field (apart from special
        # variables that have already been identified as such)
        # ------------------------------------------------------------
        all_fields = OrderedDict()
        for ncvar in g['variables']:
            if ncvar not in g['do_not_create_field']:
                all_fields[ncvar] = self._create_field(ncvar, verbose=verbose)
        #--- End: for
        
        # ------------------------------------------------------------
        # Check for unreferenced external variables
        # ------------------------------------------------------------
        unreferenced_external_variables =  g['external_variables'].difference(
            g['referenced_external_variables'])
        for ncvar in unreferenced_external_variables:
            self._add_message(
                None, ncvar,
                message=('External variable',
                         'is not referenced in file'),
                attribute={'external_variables': external_variables})
            
        # ------------------------------------------------------------
        # Discard fields created from netCDF variables that are
        # referenced by other netCDF variables
        # ------------------------------------------------------------
        fields = OrderedDict()
        for ncvar, f in all_fields.iteritems():
            if self._is_unreferenced(ncvar):
                fields[ncvar] = f
        #--- End: for
        
        if _debug:
            print 'Referenced netCDF variables:\n   ',
            print '\n    '.join([ncvar for  ncvar in all_fields
                                 if not self._is_unreferenced(ncvar)])

            print 'Unreferenced netCDF variables:\n   ',
            print '\n    '.join([ncvar for ncvar in all_fields
                                 if self._is_unreferenced(ncvar)])
        
        # ------------------------------------------------------------
        # If requested, reinstate fields created from netCDF variables
        # that are referenced by othe netCDF variables
        # ------------------------------------------------------------
        if g['fields']:
            fields0 = fields.values()
            for construct_type in g['fields']:
                for f in fields0:
                    constructs = getattr(self, 'get_'+construct_type)(f).itervalues()
                    for construct in constructs:
                        ncvar = self.get_ncvar(construct)
                        if ncvar not in all_fields:
                            continue
                        
                        fields[ncvar] = all_fields[ncvar]
        #--- End: if
            
        for x in fields.values():
            x._set_component('component_report', None, g['component_report'])

        # ------------------------------------------------------------
        # Close the netCDF file(s)
        # ------------------------------------------------------------
        self.file_close()
         
        # ------------------------------------------------------------
        # Return the fields
        # ------------------------------------------------------------
        return fields.values()
    #--- End: def

    def _get_variables_from_external_files(self, external_variables, external_files):
        '''Get external variables from external files.

:Parameters:

    external_files: sequence of `str`
        The external file names.

:Returns:

    `None`

        '''
        attribute = {'external_variables': external_variables}
                
        g = self.read_vars

        external_variables       = g['external_variables']
        datasets                 = g['datasets']
        internal_dimension_sizes = g['internal_dimension_sizes']
                                
        keys  = ('variable_attributes',
                 'variable_dimensions',
                 'variable_dataset',
                 'variables')
        
        found = []
            
        for external_file in external_files:
            external_read_vars = self.read(external_file, _scan_only=True,
                                   _debug=_debug)
            
            datasets.append(external_read_vars['nc'])
            
            for ncvar in external_variables.copy():
                if ncvar not in external_read_vars['internal_variables']:
                    # The external variable name is not in this
                    # external file
                    continue
                
                if ncvar in found:
                    # The external variable exists in more than one
                    # external file
                    external_variables.add(ncvar)
                    for key in keys:
                        g[key].pop(ncvar)

                    self._add_message(
                        None, ncvar,
                        message=('External variable',
                                 'exists in multiple external files'),
                        attribute=attribute)                    
                    continue

                # The external variable exists in this external file
                found.append(ncvar)

                # Check that the external variable dimensions exist in
                # parent file, with the same sizes.
                ok = True
                for d in external_read_vars['variable_dimensions'][ncvar]:
                    size = internal_dimension_sizes.get(d)
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
                #--- End: for
                    
                # Update the read parameters
                if ok:
                    external_variables.remove(ncvar)
                    for key in keys:
                        g[key][ncvar] = external_read_vars[key][ncvar]                   
    #--- End: def
    
    def _set_auxiliary_coordinate(self, field, construct, axes, copy=True):
        '''Insert a auxiliary coordinate object into a field.

:Parameters:

    field: `Field`

    construct: `AuxiliaryCoordinate`

    axes: `tuple`

    copy: `bool`, optional

:Returns:

    out: `str`
        '''
        self._reference(self.get_ncvar(construct))
        if construct.has_bounds():
            self._reference(self.get_ncvar(construct.get_bounds()))
            
        return field.set_auxiliary_coordinate(construct, axes=axes, copy=copy)
    #--- End: def

    def set_bounds(self, construct, bounds, copy=True):
        '''
        '''
        construct.set_bounds(bounds, copy=copy)
    #--- End: def

    def set_coordinate_ancillary(self, coordinate, prop, value):
        '''
        '''
        coordinate.set_ancillary(prop, value)
    #--- End: def
    
    def set_geometry_type(self, coordinate, value):
        '''
        '''
        coordinate.set_geometry_type(value)
    #--- End: def
    
    def set_cell_measure(self, field, construct, axes, copy=True):
        '''Insert a cell_measure object into a field.

:Parameters:

    field: `Field`

    construct: `CellMeasure`

    axes: `tuple`

    copy: `bool`, optional

:Returns:

    out: `str`
        '''
        self._reference(self.get_ncvar(construct))

        return field.set_cell_measure(construct, axes=axes, copy=copy)
    #--- End: def
    
    def set_cell_method(self, field, construct, copy=True):
        '''Insert a cell_method object into a field.

:Parameters:

    field: `Field`

    construct: `cell_method`

    copy: `bool`, optional

:Returns:

    out: `str`
        '''
        return field.set_cell_method(construct, copy=copy)
    #--- End: def

    def set_coordinate_reference(self, field, construct, copy=True):
        '''Insert a coordinate reference object into a field.

:Parameters:

    field: `Field`

    construct: `CoordinateReference`

    copy: `bool`, optional

:Returns:

    out: `str`
        '''
        ncvar = self.get_ncvar(construct, None)
        if ncvar is not None:
            self._reference(ncvar)
                    
        return field.set_coordinate_reference(construct, copy=copy)
    #--- End: def

    def set_coordinate_reference_coordinates(self, coordinate_reference,
                                             coordinates):
        '''

:Parameters:

:Returns:

    `None`
        '''
        coordinate_reference.coordinates(coordinates)
    #--- End: de

    def set_datum(self, coordinate_reference, datum):
        '''
        '''
        coordinate_reference.set_datum(datum)
    #--- End: def
    
    def set_dimension_coordinate(self, field, construct, axes, copy=True):
        '''Insert a dimension coordinate object into a field.

:Parameters:

    field: `Field`

    construct: `DimensionCoordinate`

    axes: `tuple`

    copy: `bool`, optional

:Returns:

    out: `str`
        '''
        self._reference(self.get_ncvar(construct))
        if construct.has_bounds():
            self._reference(self.get_ncvar(construct.get_bounds()))
            
        return field.set_dimension_coordinate(construct, axes=axes, copy=copy)
    #--- End: def
    
    def set_domain_ancillary(self, field, construct, axes,
                             extra_axes=0, copy=True):
        '''Insert a domain ancillary object into a field.

:Parameters:

    field: `Field`

    construct: `DomainAncillary`

    axes: `tuple`

    copy: `bool`, optional

:Returns:

    out: `str`
        '''
        self._reference(self.get_ncvar(construct))
        if construct.has_bounds():
            self._reference(self.get_ncvar(construct.get_bounds()))

        return field.set_domain_ancillary(construct, axes=axes,
                                          extra_axes=extra_axes,
                                          copy=copy)
    #--- End: def
    
    def set_domain_axis(self, field, construct, copy=True):
        '''Insert a domain_axis object into a field.

:Parameters:

    field: `Field`

    construct: `domain_axis`

    copy: `bool`, optional

:Returns:

    out: `str`
        '''
        return field.set_domain_axis(construct, copy=copy)
    #--- End: def
    
    def set_external(self, construct):
        '''
        '''
        construct.set_external(True)
    #--- End: def

    def set_field_ancillary(self, field, construct, axes, copy=True):
        '''Insert a field ancillary object into a field.

:Parameters:

    field: `Field`

    construct: `FieldAncillary`

    axes: `tuple`

    copy: `bool`, optional

:Returns:

    out: `str`
        '''
        self._reference(self.get_ncvar(construct))

        return field.set_field_ancillary(construct, axes=axes, copy=copy)
    #--- End: def

    def set_ncdim(self, construct, ncdim):
        '''
        '''
        construct.set_ncdim(ncdim)
    #-- End: def


    def set_ncvar(self, parent, ncvar):
        '''
        '''
        parent.set_ncvar(ncvar)
    #-- End: def

    def set_properties(self, construct, properties, copy=True):
        '''
        '''
        return construct.properties(properties, copy=copy)
    #--- End: def

    def _parse_compression_gathered(self, ncvar, compress):
        '''
        '''
        g = self.read_vars
        _debug = g['_debug']
        if _debug:
            print '        List variable: compress =', compress
    
        gathered_ncdimension = g['variable_dimensions'][ncvar][0]

        parsed_compress = self._split_by_white_space(ncvar, compress)
        cf_compliant = self._check_compress(ncvar, compress, parsed_compress)
        if not cf_compliant:
            return
            
        compression_type = 'gathered'
        indices = self._create_data(ncvar, uncompress_override=True)
        
        g['compression'][gathered_ncdimension] = {
            'gathered': {'indices'             : indices,
                         'implied_ncdimensions': parsed_compress,
                         'sample_dimension'    : gathered_ncdimension}}
    #--- End: def
    
    def _parse_ragged_contiguous_compression(self, ncvar, 
                                             sample_dimension):
        '''

:Parameters:

    ncvar: `str`
        The netCDF variable name of the count variable.

    sample_dimension: `str`
        The netCDF dimension name of the sample dimension.

:Returns:

    out: `str`
        The made-up netCDF dimension name of the element dimension.

    '''
        g = self.read_vars        

        _debug = g['_debug']
        if _debug:
            print '    count variable: sample_dimension =', sample_dimension

        instance_dimension = g['variable_dimensions'][ncvar][0] 
        
        elements_per_instance = self._create_data(ncvar, uncompress_override=True)
    
        instance_dimension_size = self.get_size(elements_per_instance)
        element_dimension_size  = self.get_max(elements_per_instance)
    
        if _debug:
            print '    contiguous array implied shape:', (instance_dimension_size,element_dimension_size)
    
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
        if _debug:        
            print '    featureType =', g['featureType']
    
        element_dimension = self._set_ragged_contiguous_parameters(
                elements_per_instance=elements_per_instance,
                sample_dimension=sample_dimension,
                element_dimension=element_dimension,
                instance_dimension=instance_dimension)

#        base = element_dimension
#        n = 0
#        while (element_dimension in g['nc'].dimensions or
#               element_dimension in g['new_dimensions']):
#            n += 1
#            element_dimension = '{0}_{1}'.format(base, n)
#
#        g['compression'].setdefault(sample_dimension, {})['ragged_contiguous'] = {
#            'elements_per_instance'  : elements_per_instance,
#            'implied_ncdimensions'   : (instance_dimension,
#                                        element_dimension),
#            'profile_dimension'      : instance_dimension,
#            'element_dimension'      : element_dimension,
#            'element_dimension_size' : element_dimension_size,
#            'instance_dimension_size': instance_dimension_size,
#        }
#    
#        g['new_dimensions'][element_dimension] = element_dimension_size
#        
#        if _debug:
#            print "    Creating g['compression'][{!r}]['ragged_contiguous']".format(
#                sample_dimension)
#    

        return element_dimension
    #--- End: def
    
    def _parse_indexed_compression(self, ncvar, instance_dimension):
        '''
        ncvar: `str`
            The netCDF variable name of the index variable.
    
        instance_dimension: `str`
            The netCDF variable name of the instance dimension.
    
        '''
        g = self.read_vars
                
        _debug = g['_debug']
        if _debug:
            print '    index variable: instance_dimension =', instance_dimension
        
        index = self._create_data(ncvar, uncompress_override=True)

        (instance, inverse, count) = numpy.unique(index.get_array(),
                                                  return_inverse=True,
                                                  return_counts=True)

        # The indices of the sample dimension which apply to each
        # instance. For example, if the sample dimension has size 20
        # and there are 3 instances then the instances array might
        # look like [1, 0, 2, 2, 1, 0, 2, 1, 0, 0, 2, 1, 2, 2, 1, 0,
        # 0, 0, 2, 0].
        instances = self._create_Data(array=inverse)

        # The number of elements per instance. For the instances array
        # example above, the elements_per_instance array is [7, 5, 7].
        elements_per_instance = self._create_Data(array=count)
    
        instance_dimension_size = g['internal_dimension_sizes'][instance_dimension]
        element_dimension_size  = int(elements_per_instance.max())
    
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
        if _debug:        
            print '    featureType =', g['featureType']
    
        base = element_dimension
        n = 0
        while (element_dimension in g['internal_dimension_sizes'] or
               element_dimension in g['new_dimensions']):
            n += 1
            element_dimension = '{0}_{1}'.format(base, n)
            
        indexed_sample_dimension = g['variable_dimensions'][ncvar][0]
        
        g['compression'].setdefault(indexed_sample_dimension, {})['ragged_indexed'] = {
            'elements_per_instance'  : elements_per_instance,
            'instances'              : instances,
            'implied_ncdimensions'   : (instance_dimension,
                                        element_dimension),
            'element_dimension'      : element_dimension,
            'instance_dimension_size': instance_dimension_size,
            'element_dimension_size' : element_dimension_size,
        }
    
        g['new_dimensions'][element_dimension] = element_dimension_size
        
        if _debug:
            print "    Created g['compression'][{!r}]['ragged_indexed']".format(
                indexed_sample_dimension)
    
        return element_dimension
    #--- End: def
    
    def _parse_indexed_contiguous_compression(self, sample_dimension,
                                              instance_dimension):
        '''

:Parameters:
    
    sample_dimension: `str`
        The netCDF dimension name of the sample dimension.

    element_dimension_1: `str`
        The name of the implied element dimension whose size is the
        maximum number of sub-features in any instance.

    element_dimension_2: `str`
        The name of the implied element dimension whose size is the
        maximum number of elements in any sub-feature.

    '''
        g = self.read_vars
                
        _debug = g['_debug']
        if _debug:
            print 'Pre-processing indexed and contiguous compression'
        print g['compression']
        profile_dimension = g['compression'][sample_dimension]['ragged_contiguous']['profile_dimension']
    
        if _debug:
            print '    sample_dimension  :', sample_dimension
            print '    instance_dimension:', instance_dimension
            print '    profile_dimension :', profile_dimension
            
        contiguous = g['compression'][sample_dimension]['ragged_contiguous']
        indexed    = g['compression'][profile_dimension]['ragged_indexed']
    
        # The indices of the sample dimension which define the start
        # positions of each instances profiles
        profile_indices = indexed['instances']
    
        profiles_per_instance = indexed['elements_per_instance']
        elements_per_profile  = contiguous['elements_per_instance']
    
        instance_dimension_size  = indexed['instance_dimension_size']
        element_dimension_1_size = int(profiles_per_instance.max())
        element_dimension_2_size = int(elements_per_profile.max())
        
        if _debug:
            print "    Creating g['compression'][{!r}]['ragged_indexed_contiguous']".format(
                sample_dimension)
            
        g['compression'][sample_dimension]['ragged_indexed_contiguous'] = {
            'profiles_per_instance'   : profiles_per_instance,
            'elements_per_profile'    : elements_per_profile,
            'profile_indices'         : profile_indices,
            'implied_ncdimensions'    : (instance_dimension,
                                         indexed['element_dimension'],
                                         contiguous['element_dimension']),
            'instance_dimension_size' : instance_dimension_size,
            'element_dimension_1_size': element_dimension_1_size,
            'element_dimension_2_size': element_dimension_2_size,
        }
    
        if _debug:
            print '    Implied dimensions: {} -> {}'.format(
                sample_dimension,
                g['compression'][sample_dimension]['ragged_indexed_contiguous']['implied_ncdimensions'])
    
        if _debug:
            print "    Removing g['compression'][{!r}]['ragged_contiguous']".format(
                sample_dimension)
            
        del g['compression'][sample_dimension]['ragged_contiguous']
    #--- End: def
       
    def _parse_geometry(self, field_ncvar, ncvar, attributes):
        '''

:Parameters:

    field_ncvar: `str`
        The netCDF variable name of the parent data variable.

    ncvar: `str`
        The netCDF variable name of the geometry container variable.

    attributes: `dict`

:Returns:

    out: `str`
        The made-up netCDF dimension name of the element dimension.

    '''
        g = self.read_vars        

        _debug = g['_debug']
        if _debug:
            print '    Geometry container =', ncvar
            
        g['geometries'][ncvar] = {'geometry_type': attributes[ncvar].get('geometry_type')}
 
        node_coordinates = attributes[ncvar].get('node_coordinates')
        node_count       = attributes[ncvar].get('node_count')
        coordinates      = attributes[ncvar].get('coordinates')
        part_node_count  = attributes[ncvar].get('part_node_count')
        interior_ring    = attributes[ncvar].get('interior_ring')
        
        parsed_node_coordinates = self._split_by_white_space(ncvar, node_coordinates)
        parsed_interior_ring    = self._split_by_white_space(ncvar, interior_ring)
        parsed_node_count       = self._split_by_white_space(ncvar, node_count)
        parsed_part_node_count  = self._split_by_white_space(ncvar, part_node_count)

        cf_compliant = True
        
        if interior_ring is not None and part_node_count is None:
            attribute = {field_ncvar+':geometry': attributes[field_ncvar]['geometry']}
            self._add_message(field_ncvar, ncvar,
                              message=('part_node_count attribute', 'is missing'),
                              attribute=attribute)
            cf_compliant = False
   
        cf_compliant = cf_compliant & self._check_node_coordinates(ncvar,
                                                                   node_coordinates,
                                                                   parsed_node_coordinates)

        cf_compliant = cf_compliant & self._check_node_count(ncvar,
                                                             node_count,
                                                             parsed_node_count)

        cf_compliant = cf_compliant & self._check_part_node_count(ncvar,
                                                                  part_node_count,
                                                                  parsed_part_node_count)

        cf_compliant = cf_compliant & self._check_interior_ring(ncvar,
                                                                interior_ring,
                                                                parsed_interior_ring)

        if not cf_compliant:
            return

# data:
#  x = 20, 10, 0,  5, 10, 15,  20, 10,  0,   50, 40, 30 ;
#  y =  0, 15, 0,  5, 10, 5,   20, 35, 20,    0, 15,  0 ;
#  lat             = 25,       7 ;
#  lon             = 10,      40 ;
#  node_count      =  9,       3 ;
#  part_node_count =  3, 3, 3, 3 ;
#  interior_ring   =  0, 1, 0, 0 ;

#  row_size        =  3, 3, 3, 3 ;
#  part_index      =  0, 0, 0, 1 ;

        if node_count is not None:
            # Do not attempt to create a field from a node count
            # variable
            g['do_not_create_field'].add(node_count)

            # Find the sample size from one of the node coordinates
            sample_dimension = g['variable_dimensions'][parsed_node_coordinates[0]][0]
                
            instance_dimension = g['variable_dimensions'][node_count][0]
            nodes_per_geometry = self._create_data(node_count)
            
            element_dimension = self._set_ragged_contiguous_parameters(
                elements_per_instance=nodes_per_geometry,
                sample_dimension=sample_dimension,
                element_dimension='node',
                instance_dimension=instance_dimension)
            
            if part_node_count is not None:
                # Do not attempt to create a field from a part node
                # count variable
                g['do_not_create_field'].add(part_node_count)
                
                if interior_ring is not None:
                    # Do not attempt to create a field from an
                    # interior ring variable
                    g['do_not_create_field'].add(interior_ring)
                    
                sample_dimension = g['variable_dimensions'][part_node_count][0]
                
                parts = self._create_data(part_node_count)
                total_number_of_parts = self.get_size(parts)
                parts_per_geometry = nodes_per_geometry.copy()
                
                i = 0
                for j in xrange(self.get_size(nodes_per_geometry)):
                    nodes_in_this_geometry = nodes_per_geometry[j]
                    parts_in_this_geometry = 0
                    s = 0

                    for k in xrange(i, total_number_of_parts):
                        parts_in_this_geometry += 1
                        s += parts[k]
                        if s >= nodes_in_this_geometry:
                            parts_per_geometry[j] = parts_in_this_geometry
                            i += k + 1
                            break                        
                    #--- End: for

                    i += 1
                #--- End: for
                
                element_dimension = self._set_ragged_contiguous_parameters(
                    elements_per_instance=parts_per_geometry,
                    sample_dimension=sample_dimension,
                    element_dimension='part',
                    instance_dimension=instance_dimension)                  
        #--- End: if
        
        g['geometries'][geometry_ncvar].update(
            {'node_coordinates': parsed_node_coordinates,
             'interior_ring   ': interior_ring,
             'node_count      ': node_count,
             'part_node_count ': part_node_count}
        )
    #--- End: def

    def _set_ragged_contiguous_parameters(self,
                                          elements_per_instance=None,
                                          sample_dimension=None,
                                          element_dimension=None,
                                          instance_dimension=None):
        '''qwertyy

:Parameters:

    elements_per_instance: `Data`

#    role: `str`

    sample_dimension: `str`

    element_dimension: `str`
 
    instance_dimension: `str`

:Returns:

    out: `str`
       The element dimension, possibly modified to make sure that it
       is unique.

        '''
        g = self.read_vars
        
        instance_dimension_size = self.get_size(elements_per_instance)
        element_dimension_size  = self.get_max(elements_per_instance)
        
        # Make sure that the element dimension name is unique
        base = element_dimension
        n = 0
        while (element_dimension in g['internal_dimension_sizes'] or
               element_dimension in g['new_dimensions']):
            n += 1
            element_dimension = '{0}_{1}'.format(base, n)

        g['new_dimensions'][element_dimension] = element_dimension_size
                            
        g['compression'].setdefault(sample_dimension, {})['ragged_contiguous'] = {
            'elements_per_instance'  : elements_per_instance,
            'implied_ncdimensions'   : (instance_dimension,
                                        element_dimension),
            'profile_dimension'      : instance_dimension,
            'element_dimension'      : element_dimension,
            'element_dimension_size' : element_dimension_size,
            'instance_dimension_size': instance_dimension_size,
        }
        
        if g['_debug']:
            print "    Creating g['compression'][{!r}]['ragged_contiguous']".format(
                sample_dimension)

        return element_dimension
    #--- End: def
            
    def _check_external_variables(self, external_variables,
                                  parsed_external_variables):
        '''asdsdsa

:Parameters:

    external_variables: `str`
        The external_variables attribute as found in the file.
 
    parsed_external_variables: `list`
        The external_variables attribute parsed into a list of
        external variable names.

:Returns:

    out: `list`
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
        #--- End: for
        
        return out
    #--- End: def
        
                
    def _check_formula_terms(self, field_ncvar, coord_ncvar,
                             formula_terms, z_ncdim=None):
        '''asdsdsa

:Parameters:
    
    field_ncvar: `str`

    coord_ncvar: `str`
    
    formula_terms: `str`
        A CF-netCDF formula_terms attribute.
    
        '''
        #=============================================================
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
        # =============================================================

        g = self.read_vars
 
        nc = g['nc']
        
#        variables = nc.variables
        
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
            term, values = x.items()[0]
            
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
        #--- End: for

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
            bounds_formula_terms = g['variable_attributes'][bounds_ncvar].get('formula_terms')
            if bounds_formula_terms is not None:
                # ----------------------------------------------------
                # Parametric Z coordinate has bounds, and the bounds
                # variable has a formula_terms attribute
                # ----------------------------------------------------
                bounds_attribute = {bounds_ncvar+':formula_terms': bounds_formula_terms}

                parsed_bounds_formula_terms = self._parse_x(bounds_ncvar, bounds_formula_terms)

                if not parsed_bounds_formula_terms:
                    self._add_message(field_ncvar, bounds_ncvar,
                                      message=('Bounds formula_terms attribute',
                                               'is incorrectly formatted'),
                                      attribute=attribute,
                                      variable=coord_ncvar)

                for x in parsed_bounds_formula_terms:
                    term, values = x.items()[0]
                    
                    g['formula_terms'][coord_ncvar]['bounds'][term] = None

                    if len(values) != 1:
                        self._add_message(field_ncvar, bounds_ncvar,
                                          message=('Bounds formula_terms attribute',
                                                   'is incorrectly formatted'),
                                          attribute=bounds_attribute,
                                          variable=coord_ncvar)
                        continue
            
                    ncvar = values[0]
                    
                    if ncvar not in g['internal_variables']:
                        self._add_message(field_ncvar, ncvar,
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
                    
                    parent_ncvar = g['formula_terms'][coord_ncvar]['coord'][term]

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
                        #--- End: if
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
                #--- End: for
                
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
                for term, ncvar in g['formula_terms'][coord_ncvar]['coord'].iteritems():
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
                            g['formula_terms'][coord_ncvar]['bounds'][term] = ncvar
                        else:
                            # Coordinates span the Z dimension
                            b = g['bounds'][field_ncvar].get(ncvar)
                            if b is not None:
                                g['formula_terms'][coord_ncvar]['bounds'][term] = b
                            else:
                                is_coordinate_with_bounds = False
                        #--- End: if
                    
                        break
                    #--- End: for

                    if not is_coordinate_with_bounds:
                         self._add_message(
                             field_ncvar, ncvar,
                             message=('Formula terms variable',
                                      'that spans the vertical dimension has no bounds'),
                             attribute=attribute,
                             variable=coord_ncvar)
                #--- End: for
            #--- End: if
        #--- End: if
   #--- End: def

    def _create_field(self, field_ncvar, verbose=False):
        '''Create a field for a given netCDF variable.
    
:Parameters:

    field_ncvar: `str`
        The name of the netCDF variable to be turned into a field.

:Returns:

    out: `Field`
        The new field.

        '''
        g = self.read_vars

        # Reset 'domain_ancillary_key'
        g['domain_ancillary_key'] = {}
        
        nc = g['variable_dataset'][field_ncvar]

        dimensions = g['variable_dimensions'][field_ncvar]
        g['read_report'][field_ncvar] = {'dimensions': dimensions,
                                         'components': {}}
        
        _debug = g['_debug']
        if _debug:
            print 'Converting netCDF variable {}({}) to a Field:'.format(
                field_ncvar, ', '.join(dimensions))

#        compression = g['compression']
        
        # Add global attributes to the data variable's properties, unless
        # the data variables already has a property with the same name.
        properties = g['global_attributes'].copy()
        properties.update(g['variable_attributes'][field_ncvar])

        if _debug:
            print '    netCDF attributes:', properties
        
        # Take cell_methods out of the data variable's properties since it
        # will need special processing once the domain has been defined
        cell_methods_string = properties.pop('cell_methods', None)
        
#        cell_methods = []
#        if cell_methods_string is not None:
#            cell_methods = self._parse_cell_methods(cell_methods_string,
#                                                    allow_error=True)
#            error = cell_methods[0].get_error(False)
#            if error:
#                self._add_message(
#                    field_ncvar, field_ncvar,
#                    message=(error,),
#                    attribute={field_ncvar+':cell_methods': cell_methods_string})
#
##                if verbose :
##                    print ("WARNING: {0}: {1!r}".format(
##                        error, cell_methods[0].get_string('')))
#                cell_methods = None
#        #--- End: if
#        if cell_methods_string is not None:
#            cell_methods = self.parse_cell_methods(cell_methods_string)
#            if error:
#                self._add_message(
#                    field_ncvar, field_ncvar,
#                    message=(error,),
#                    attribute={field_ncvar+':cell_methods': cell_methods_string})
#
##                if verbose :
##                    print ("WARNING: {0}: {1!r}".format(
##                        error, cell_methods[0].get_string('')))
#                cell_methods = None
#        #--- End: if
    
        # Take add_offset and scale_factor out of the data variable's
        # properties since they will be dealt with by the variable's Data
        # object. Makes sure we note that they were there so we can adjust
        # the field's dtype accordingly
        values = [properties.pop(k, None) for k in ('add_offset', 'scale_factor')]
        unpacked_dtype = (values != [None, None])
        if unpacked_dtype:
            try:
                values.remove(None)
            except ValueError:
                pass
    
            unpacked_dtype = numpy.result_type(*values)
        #--- End: if    
    
        # ----------------------------------------------------------------
        # Initialize the field with its attributes
        # ----------------------------------------------------------------
        f = self.initialise('Field')
        self.set_properties(f, properties, copy=False)

        # Store the field's netCDF variable name
        self.set_ncvar(f, field_ncvar)
   
        f.set_global_attributes(g['global_attributes'])

        # Map netCDF dimension names to domain axis names.
        # 
        # For example:
        # >>> ncdim_to_axis
        # {'lat': 'dim0', 'time': 'dim1'}
        ncdim_to_axis = {}
        g['ncdim_to_axis'] = ncdim_to_axis
    
        ncscalar_to_axis = {}
    
        # Map netCDF variable names to internal identifiers
        # 
        # For example:
        # >>> ncvar_to_key
        # {'dimensioncoordinate1': 'time'}
        ncvar_to_key = {}
            
        data_axes = []
    
        # ----------------------------------------------------------------
        # Add axes and non-scalar dimension coordinates to the field
        # ----------------------------------------------------------------
        field_ncdimensions = self._ncdimensions(field_ncvar)
            
        for ncdim in field_ncdimensions:
            if g['variable_dimensions'].get(ncdim) == (ncdim,):
                # There is a Unidata coordinate variable for this
                # dimension, so create a domain axis and dimension
                # coordinate
                if ncdim in g['dimension_coordinate']:
                    coord = self._copy_construct('dimension_coordinate', field_ncvar, ncdim)
                else:
                    coord = self._create_dimension_coordinate(field_ncvar, ncdim,
                                                              f,
                                                              verbose=verbose)
                    g['dimension_coordinate'][ncdim] = coord
                
                domain_axis = self._create_domain_axis(self.get_size(coord), ncdim)
                if _debug:
                    print '    [0] Inserting', repr(domain_axis)                    
                axis = self.set_domain_axis(f, domain_axis, copy=False)

                if _debug:
                    print '    [1] Inserting', repr(coord)
                dim = self.set_dimension_coordinate(f, coord,
                                                    axes=[axis], copy=False)
                
                # Set unlimited status of axis
                if nc.dimensions[ncdim].isunlimited():
                    f.unlimited({axis: True})
    
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
                if _debug:
                    print '    [2] Inserting', repr(domain_axis)
                axis = self.set_domain_axis(f, domain_axis, copy=False)
                
                # Set unlimited status of axis
                try:
                    if nc.dimensions[ncdim].isunlimited():
                        f.unlimited({axis: True})
                except KeyError:
                    # This dimension is not in the netCDF file (as might
                    # be the case for an element dimension implied by a
                    # ragged array).
                    pass            
            #--- End: if
    
            # Update data dimension name and set dimension size
            data_axes.append(axis)
    
            ncdim_to_axis[ncdim] = axis
        #--- End: for

        data = self._create_data(field_ncvar, f, unpacked_dtype=unpacked_dtype)        
        if _debug:
            print '    [3] Inserting', repr(data)

        self._set_data(f, data, axes=data_axes, copy=False)
          
        # ----------------------------------------------------------------
        # Add scalar dimension coordinates and auxiliary coordinates to
        # the field
        # ----------------------------------------------------------------
        coordinates = self.del_property(f, 'coordinates')
        if coordinates is not None:
            parsed_coordinates = self._split_by_white_space(field_ncvar, coordinates)
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
                    coord = self._create_auxiliary_coordinate(field_ncvar, ncvar,
                                                              f,
                                                              verbose=verbose)
                    g['auxiliary_coordinate'][ncvar] = coord
                #--- End: if
     
                # --------------------------------------------------------
                # Turn a 
                # --------------------------------------------------------
                is_scalar_dimension_coordinate = False
                scalar = False
                if not dimensions:
                    scalar = True
                    if g['variables'][ncvar].dtype.kind is 'S':
                        # String valued scalar coordinate. Is this CF
                        # compliant? Don't worry about it - we'll just
                        # turn it into a 1-d, size 1 auxiliary coordinate
                        # construct.
                        domain_axis = self._create_domain_axis(1)
                        if _debug:
                            print '    [4] Inserting', repr(domain_axis)
                        dim = self.set_domain_axis(f, domain_axis)
                        dimensions = [dim]
                    else:  
                        # Numeric valued scalar coordinate
                        is_scalar_dimension_coordinate = True
                #--- End: if
    
                if is_scalar_dimension_coordinate:
                    # Insert a domain axis and dimension coordinate
                    # derived from a numeric scalar auxiliary
                    # coordinate
                    coord = self.initialise('DimensionCoordinate',
                                             source=coord, copy=False)
                    coord = self.expand_dims(coord, position=0, copy=False)
                    
                    domain_axis = self._create_domain_axis(self.get_size(coord))
                    if _debug:
                        print '    [5] Inserting', repr(domain_axis)
                    axis = self.set_domain_axis(f, domain_axis, copy=False)
                    
                    if _debug:
                        print '    [5] Inserting', repr(coord)
                    dim = self.set_dimension_coordinate(f, coord,
                                                        axes=[axis], copy=False)
                    
                    dimensions = [axis]
                    ncvar_to_key[ncvar] = dim
                                        
                    g['dimension_coordinate'][ncvar] = coord
                    del g['auxiliary_coordinate'][ncvar]
                else:
                    # Insert auxiliary coordinate
                    if _debug:
                        print '    [6] Inserting', repr(coord)
                    aux = self._set_auxiliary_coordinate(f, coord,
                                                         axes=dimensions,
                                                         copy=False)
                    ncvar_to_key[ncvar] = aux

                if scalar:
                    ncscalar_to_axis[ncvar] = dimensions[0]
            #--- End: for
        #--- End: if
    
        # ----------------------------------------------------------------
        # Add coordinate references from formula_terms properties
        # ----------------------------------------------------------------
        for key, coord in self.get_coordinates(f).iteritems():
            coord_ncvar = self.get_ncvar(coord)

            formula_terms = g['variable_attributes'][coord_ncvar].get('formula_terms')        
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
            for term, ncvar in g['formula_terms'][coord_ncvar]['coord'].iteritems():
                if ncvar is None:
                    continue

                # Set dimensions
                axes = self._get_domain_axes(ncvar)

                if ncvar in g['domain_ancillary']:
                    domain_anc = self._copy_construct('domain_ancillary',
                                                      field_ncvar, ncvar)
                else:
                    bounds = g['formula_terms'][coord_ncvar]['bounds'].get(term)
                    if bounds == ncvar:
                        bounds = None
        
                    domain_anc = self._create_domain_ancillary(field_ncvar, ncvar,
                                                               f,
                                                               bounds=bounds,
                                                               verbose=verbose)
                #--- End: if
                
                if len(axes) == len(self._ncdimensions(ncvar)):
                    domain_ancillaries.append((ncvar, domain_anc, axes))
                else:
                    # The domain ancillary variable spans a dimension
                    # that is not spanned by its parent data variable
                    self._add_message(
                        field_ncvar, ncvar,
                        message=('Formula terms variable',
                                 'spans incorrect dimensions'),
                        attribute={coord_ncvar+':formula_terms': formula_terms},
                        dimensions=g['variable_dimensions'][ncvar])
                    ok = False
#                    break
            #--- End: for

            if not ok:
                # Move on to the next coordinate
                continue
               
            # Still here? Create a formula terms coordinate reference.
            for ncvar, domain_anc, axes in domain_ancillaries:
                if _debug:
                    print '    [7] Inserting', repr(domain_anc)
                    
                da_key = self.set_domain_ancillary(f, domain_anc,
                                                   axes=axes, copy=False)
                if ncvar not in ncvar_to_key:
                    ncvar_to_key[ncvar] = da_key
                    
                g['domain_ancillary'][ncvar]     = domain_anc
                g['domain_ancillary_key'][ncvar] = da_key
            #--- End: for
            
            coordinate_reference = self._create_formula_terms_ref(
                f, key, coord,
                g['formula_terms'][coord_ncvar]['coord'])
            
            self.set_coordinate_reference(f, coordinate_reference, copy=False)

            g['vertical_crs'][coord_ncvar] = coordinate_reference
        #--- End: for
    
        # ----------------------------------------------------------------
        # Add grid mapping coordinate references (do this after
        # formula terms)
        # ----------------------------------------------------------------
        grid_mapping = f.del_property('grid_mapping')
        if grid_mapping is not None:
            parsed_grid_mapping = self._parse_x(field_ncvar, grid_mapping)
            cf_compliant = self._check_grid_mapping(field_ncvar,
                                                    grid_mapping,
                                                    parsed_grid_mapping)
            if not cf_compliant:
                if _debug:
                    print '        Bad grid_mapping:', grid_mapping
            else:
                for x in parsed_grid_mapping:
                    grid_mapping_ncvar, coordinates = x.items()[0]

                    parameters = g['variable_attributes'][grid_mapping_ncvar].copy()

                    # Convert netCDF variable names to internal identifiers
                    coordinates = [ncvar_to_key[ncvar] for ncvar in coordinates
                                   if ncvar in ncvar_to_key]
                    
                    coordref = self.initialise('CoordinateReference',
                                                parameters=parameters)
                    
                    datum = self.get_datum(coordref)
                    
                    create_new = True
                    
                    if not coordinates:
                        name = parameters.get('grid_mapping_name', None)
                        for n in self.implementation.get_class('CoordinateReference')._name_to_coordinates.get(name, ()):
                            for key, coord in self.get_coordinates(f).iteritems():
                                if n == self.get_property(coord, 'standard_name', None):
                                    coordinates.append(key)
                        #--- End: for

                        # Add the datum to already existing vertical
                        # coordinate references
                        for vcr in g['vertical_crs'].itervalues():
                            self.set_datum(vcr, datum)
                    else:
                        for vcoord, vcr in g['vertical_crs'].iteritems():
                            if vcoord in coordinates:
                                # Add the datum to an already existing
                                # vertical coordinate reference
                                self.set_datum(vcr, datum)
                                coordinates.remove(vcoord)
                                create_new = bool(coordinates)
                    #--- End: if

                    if create_new:
                        self.set_ncvar(coordref, grid_mapping_ncvar)
                        key = self.set_coordinate_reference_coordinates(coordref,
                                                                        coordinates)
                        self.set_coordinate_reference(f, coordref, copy=False)
                        ncvar_to_key[grid_mapping_ncvar] = key
                #--- End: for
        #--- End: if
        
        # ----------------------------------------------------------------
        # Add cell measures to the field
        # ----------------------------------------------------------------
        measures = f.del_property('cell_measures')
        if measures is not None:
            parsed_cell_measures = self._parse_x(field_ncvar, measures)
            cf_compliant = self._check_cell_measures(field_ncvar,
                                                     measures,
                                                     parsed_cell_measures)
            if cf_compliant:
                for x in parsed_cell_measures:
                    measure, ncvars = x.items()[0]
                    ncvar = ncvars[0]
                        
                    # Set the cell measures domain axes
                    axes = self._get_domain_axes(ncvar, allow_external=True)
        
                    if ncvar in g['cell_measure']:
                        # Copy the cell measure from one that already
                        # exisits
                        cell = g['cell_measure'][ncvar].copy()
                    else:
                        cell = self._create_cell_measure(measure, ncvar)
                        g['cell_measure'][ncvar] = cell
        
                    if _debug:
                        print '    [8] Inserting', repr(cell)

                    key = self.set_cell_measure(f, cell, axes=axes, copy=False)
        
                    ncvar_to_key[ncvar] = key

                    if ncvar in g['external_variables']:
                        g['referenced_external_variables'].add(ncvar)
        #--- End: if
    
        # ------------------------------------------------------------
        # Add cell methods to the field
        # ------------------------------------------------------------
        if cell_methods_string is not None:
            name_to_axis = ncdim_to_axis.copy()
            name_to_axis.update(ncscalar_to_axis)

            cell_methods = self._parse_cell_methods(field_ncvar, cell_methods_string)
            
            for properties in cell_methods:
                axes = [name_to_axis.get(axis, axis)
                        for axis in properties.pop('axes')]
                                
                cell_method = self._create_cell_method(axes, properties)
                if _debug:
                    print '    [ ] Inserting', repr(cell_method)
                        
                self.set_cell_method(f, cell_method, copy=False)
        #--- End: if

        # ----------------------------------------------------------------
        # Add field ancillaries to the field
        # ----------------------------------------------------------------
        ancillary_variables = f.del_property('ancillary_variables')
        if ancillary_variables is not None:
            parsed_ancillary_variables = self._split_by_white_space(field_ncvar, ancillary_variables)
            cf_compliant = self._check_ancillary_variables(field_ncvar,
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
                    if _debug:
                        print '    [9] Inserting', repr(field_anc)                  
                    key = self.set_field_ancillary(f, field_anc, axes=axes, copy=False)
                    ncvar_to_key[ncvar] = key
        #--- End: if

        if _debug:
            print '    Field properties:', f.properties()
        
        # Add the structural read report to the field
        f.set_read_report({field_ncvar: g['read_report'][field_ncvar]})
        
        # Return the finished field
        return f
    #--- End: def

    def _add_message(self, field_ncvar, ncvar, message=None,
                     attribute=None, dimensions=None, variable=None):
        ''':Parameters:

    field_ncvar: `str`a
        The netCDF variable name of the field.

          *Example:*
            ``field_ncvar='pr'``


    ncvar: `str`
        The netCDF variable name of the field component that has the problem.

          *Example:*
            ``field_ncvar='rotated_latitude_longitude'``

    message: (`str`, `str`), optional

    attribute: `str`, optional
        The name and value of the netCDF attribute that has a problem.
        
          *Example:*
            ``attribute={'tas:cell_measures': 'area: areacella'}``

    dimensions: sequence of `str`, optional
        The netCDF dimensions of the variable that has a problem.

          *Example:*
            ``dimensions=('lat', 'lon')``

        
    variable: `str`, optional

        '''
        g = self.read_vars

        if message is not None:
            code = self._code0[message[0]]*1000 + self._code1[message[1]]
            message = ' '.join(message)
        else:
            code = None
            
        d = {'code'     : code,
             'attribute': attribute,
             'message'  : message}

        if dimensions is not None:
            d['dimensions'] = dimensions

        if variable is None:
            variable = ncvar
        
        g['read_report'][field_ncvar]['components'].setdefault(ncvar, []).append(d)

        e = g['component_report'].setdefault(variable, {})
        e.setdefault(ncvar, []).append(d)

        if g['_debug']:
            if dimensions is None:
                dimensions = ''
            else:
                dimensions = '(' + ', '.join(dimensions) + ')'
                
            print '    Error processing netCDF variable {}{}: {}'.format(
                ncvar, dimensions, d['message'])
        #--- End: if
        
        return d
    #--- End: def

    def _get_domain_axes(self, ncvar, allow_external=False):
        '''
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
    #--- End: def
        
    def _create_auxiliary_coordinate(self, field_ncvar, ncvar, 
                                     f, bounds=None, verbose=False):
        '''
        '''
        return self._create_bounded_construct(field_ncvar=field_ncvar,
                                              ncvar=ncvar,
                                              f=f,
                                              auxiliary=True,
                                              bounds=bounds,
                                              verbose=verbose)
    #--- End: def

    def _create_dimension_coordinate(self, field_ncvar, ncvar, f,
                                     bounds=None, verbose=False):
        '''
        '''
        return self._create_bounded_construct(field_ncvar=field_ncvar,
                                              ncvar=ncvar,
                                              f=f,
                                              dimension=True,
                                              bounds=bounds,
                                              verbose=verbose)
    #--- End: def

    def _create_domain_ancillary(self, field_ncvar, ncvar, 
                                 f, bounds=None, verbose=False):
        '''
        '''
        return self._create_bounded_construct(field_ncvar=field_ncvar,
                                              ncvar=ncvar,
                                              f=f,
                                              domain_ancillary=True,
                                              bounds=bounds,
                                              verbose=verbose)
    #--- End: def

    def _create_bounded_construct(self, field_ncvar, ncvar, f,
                                  dimension=False, auxiliary=False,
                                  domain_ancillary=False, bounds=None,
                                  verbose=False):
        '''Create a variable which might have bounds.
    
:Parameters:

    ncvar: `str`
        The netCDF name of the variable.

    f: `Field`
        The parent field.

    dimension: `bool`, optional
        If True then a dimension coordinate is created.

    auxiliary: `bool`, optional
        If True then an auxiliary coordinate is created.

    domain_ancillary: `bool`, optional
        If True then a domain ancillary is created.

:Returns:

    out : `DimensionCoordinate` or `AuxiliaryCoordinate` or `DomainAncillary`
        The new item.
    
        '''
        g = self.read_vars
        nc = g['nc']

        g['bounds'][field_ncvar] = {}
        g['coordinates'][field_ncvar] = []
        
        properties = g['variable_attributes'][ncvar].copy()

        properties.pop('formula_terms', None)
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

        attribute = 'bounds'
        climatology = False
        if bounds is None:
            ncbounds = properties.pop('bounds', None)
            if ncbounds is None:
                ncbounds = properties.pop('climatology', None)
                if ncbounds is not None:
                    attribute = 'climatology'
                    climatology = True
        else:
            ncbounds = bounds

        if dimension:
            properties.pop('compress', None) #??
            c = self.initialise('DimensionCoordinate')
        elif auxiliary:
            c = self.initialise('AuxiliaryCoordinate')
        elif domain_ancillary:
#            properties.pop('coordinates', None)
#            properties.pop('grid_mapping', None)
#            properties.pop('cell_measures', None)
#            properties.pop('positive', None)
            c = self.initialise('DomainAncillary')
        else:
            raise ValueError(
"Must set one of the dimension, auxiliary or domain_ancillary parameters to True")

        self.set_properties(c, properties)
        
        if climatology:
            self.set_geometry_type(c, 'climatology')
    
        data = self._create_data(ncvar, c)
        self._set_data(c, data, copy=False)

        # ------------------------------------------------------------
        # Look for a geometry container (CF >= 1.8)
        # ------------------------------------------------------------
        geometry_ncvar = g['variable_attributes'][field_ncvar].get('geometry')
        geometry = g['geometries'].get(geometry_ncvar)

        # ------------------------------------------------------------
        # Add any bounds
        # ------------------------------------------------------------
        if ncbounds is not None:
                       
            if geometry is None:
                cf_compliant = self._check_bounds(field_ncvar, ncvar,
                                                  attribute, ncbounds)
                if not cf_compliant:
                    pass
            else:
                cf_compliant = self._check_node_coordinate(field_ncvar, ncvar,
                                                           ncbounds)
                if not cf_compliant:
                    pass
            #--- End: if
            
            bounds = self.initialise('Bounds')
            
            properties = g['variable_attributes'][ncbounds].copy()
            properties.pop('formula_terms', None)                
            self.set_properties(bounds, properties, copy=False)
        
            bounds_data = self._create_data(ncbounds, bounds)
    
#                # Make sure that the bounds dimensions are in the same
#                # order as its parent's dimensions. It is assumed that we
#                # have already checked that the bounds netCDF variable has
#                # appropriate dimensions.
#                c_ncdims = nc.variables[ncvar].dimensions
#                b_ncdims = nc.variables[ncbounds].dimensions
#                c_ndim = len(c_ncdims)
#                b_ndim = len(b_ncdims)
#                if b_ncdims[:c_ndim] != c_ncdims:
#                    axes = [c_ncdims.index(ncdim) for ncdim in b_ncdims[:c_ndim]
#                            if ncdim in c_ncdims]
#                    axes.extend(range(c_ndim, b_ndim))
#                    bounds_data = self._transpose_data(bounds_data,
#                                                       axes=axes, copy=False)
#                #--- End: if
    
            self._set_data(bounds, bounds_data, copy=False)
            
            # Store the netCDF variable name
            self.set_ncvar(bounds, ncbounds)
            
            self.set_bounds(c, bounds, copy=False)
            
            if not domain_ancillary:
                g['bounds'][field_ncvar][ncvar] = ncbounds
        #--- End: if

        # ------------------------------------------------------------
        # Add cell extent parameters for geometries (CF >= 1.8)
        # ------------------------------------------------------------ ppp
        if geometry is not None:
            # Add the geometry type as a cell extent parameter
            geometry_type = geometry.get('geometry_type')
            if geometry_type is not None:
                self.set_geometry_type(c, geometry_type)
               
            for attribute in ('part_node_count', 'interior_ring'):                
                g_ncvar = geometry.get(attribute)
                if g_ncvar is None:
                    # This attribute has not been set
                    continue

                if g_ncvar in g['domain_ancillary_key']:
                    # The domain ancillary has already been set for this field 
                    self.set_coordinate_ancillary(
                        c, attribute,
                        g['domain_ancillary_key'][g_ncvar])
                else:
                    # The domain ancillary has NOT already been set on this field 
                    if g_ncvar in g['domain_ancillary']:
                        # The domain ancillary has been created for another field
                        domain_anc = self._copy_construct('domain_ancillary',
                                                          field_ncvar, g_ncvar)
                    else:
                        # Create the domain ancillary
                        domain_anc = self._create_domain_ancillary(field_ncvar,
                                                                   g_ncvar,
                                                                   f,
                                                                   verbose=verbose)
                                    
                    # Set domain ancillary axes
                    axes = self._get_domain_axes(g_ncvar)
                    
                    da_key = self.set_domain_ancillary(f, domain_anc,
                                                       axes=axes,
                                                       extra_axes=1,
                                                       copy=False)
                    
                    self.set_coordinate_ancillary(c, attribute, da_key)
            
                    if ncvar not in ncvar_to_key:
                        ncvar_to_key[part_node_count] = da_key
                        
                    g['domain_ancillary'][g_ncvar]     = domain_anc
                    g['domain_ancillary_key'][g_ncvar] = da_key                
        #--- End: if
        
        # Store the netCDF variable name
        self.set_ncvar(c, ncvar)

        if not domain_ancillary:
            g['coordinates'][field_ncvar].append(ncvar)
        
        # ---------------------------------------------------------
        # Return the bounded variable
        # ---------------------------------------------------------
        return c
    #--- End: def
    
    def _set_data(self, construct, data, axes=None, copy=True):
        '''Insert a data object into construct. 

If the construct is a Field then the corresponding domain axes must
also be provided.

:Parameters:

    construct:

    data: `Data`

    axes: `tuple`, optional

    copy: `bool`, optional

:Returns:

    `None`
        '''
        if axes is None:
            construct.set_data(data, copy=copy)
        else:
            construct.set_data(data, axes, copy=copy)
    #--- End: def

    def expand_dims(self, construct, position, copy=True):
        '''
        '''
        return construct.expand_dims(position=position, copy=copy)
    #--- End: def
    
    def get_auxiliary_coordinate(self, f):
       '''
       '''
       return f.auxiliary_coordinates()
    #-- End: def

    def get_cell_measure(self, f):
       '''
       '''
       return f.cell_measures()
    #-- End: def

    def get_datum(self, coordinate_reference):
        '''
        '''
        return coordinate_reference.datum
    #--- End: def
    
    def get_dimension_coordinate(self, f):
       '''
       '''
       return f.dimension_coordinates()
    #-- End: def

    def get_domain_ancillary(self, f):
       '''
       '''
       return f.domain_ancillaries()
    #-- End: def
 
    def get_field_ancillary(self, f):
       '''
       '''
       return f.field_ancillaries()
    #-- End: def
                                   
#    def _transpose_data(self, data, axes=None, copy=True):
#        '''
#        '''
#        data = data.tranpose(axes=axes, copy=copy)
#        return data
#    #-- End: def
    
    def _create_cell_measure(self, measure, ncvar):
        '''Create a cell measure object.
    
:Parameters:

    measure: `str`
        The cell measure.
        
          *Example:*
             ``measure='area'``
    
    ncvar: `str`
        The netCDF name of the cell measure variable.

          *Example:*
             ``ncvar='areacello'``

:Returns:

    out: `CellMeasure`
        The new item.

        '''
        g = self.read_vars
        
        # Initialise the cell measure construct
        cell_measure = self.initialise('CellMeasure', measure=measure)

        # Store the netCDF variable name
        self.set_ncvar(cell_measure, ncvar)
    
        if ncvar in g['external_variables']:
            # The cell measure variable is in a different file
            self.set_external(cell_measure)
        else:
            # The cell measure variable is this file
            self.set_properties(cell_measure, g['variable_attributes'][ncvar])
            data = self._create_data(ncvar, cell_measure)            
            self._set_data(cell_measure, data, copy=False)
            
        return cell_measure
    #--- End: def

    def _create_cell_method(self, axes, properties):
        '''Create a cell method object.
    
*Example:*

:Parameters:

    axes: `tuple`

    properties: `dict`
        
:Returns:

    out: `CellMethod`

        '''
        cell_method = self.initialise('CellMethod',
                                      axes=axes,
                                      properties=properties)
        return cell_method
    #--- End: def

    def _create_data(self, ncvar, construct=None,
                     unpacked_dtype=False, uncompress_override=None,
                     units=None, calendar=None, fill_value=None):
        '''
    
Set the Data attribute of a variable.

:Parameters:

    ncvar: `str`

    construct: `Variable`, optional

    unpacked_dtype: `False` or `numpy.dtype`, optional

:Returns:

    out: `Data`

:Examples: 
    
    '''
        g = self.read_vars
        nc = g['nc']
        
        variable = g['variables'].get(ncvar)
        if variable is None:
            return None
        
        dtype = variable.dtype
        if unpacked_dtype is not False:
            dtype = numpy.result_type(dtype, unpacked_dtype)
    
        ndim  = variable.ndim
        shape = variable.shape
        size  = variable.size
        if size < 2:
            size = int(size)
    
        if dtype.kind == 'S' and ndim >= 1: #shape[-1] > 1:
            # Has a trailing string-length dimension
            strlen = shape[-1]
            shape = shape[:-1]
            size /= strlen
            ndim -= 1
            dtype = numpy.dtype('S{0}'.format(strlen))
        #--- End: if

        filearray = self._create_NetCDF(filename=g['filename'], ncvar=ncvar,
                                        dtype=dtype, ndim=ndim, shape=shape,
                                        size=size)
        
        # Find the units for the data
        if units is None:
            units = g['variable_attributes'][ncvar].get('units')
            
        if calendar is None:
            calendar = g['variable_attributes'][ncvar].get('calendar')
            
        # Find the fill_value for the data
        if fill_value is None:
            try:
                fill_value = construct.fill_value()
            except AttributeError:
                fill_value = None
                
        compression = g['compression']

        dimensions = g['variable_dimensions'][ncvar]
        
        if ((uncompress_override is not None and not uncompress_override) or
            not compression or 
            not g['uncompress'] or
            not set(compression).intersection(dimensions)):
            # --------------------------------------------------------
            # The array is not compressed (or not to be uncompressed)
            # --------------------------------------------------------
            data = self._create_Data(filearray, ncvar=ncvar)
            
        else:
            # --------------------------------------------------------
            # The array is compressed
            # --------------------------------------------------------

            # Loop round the dimensions of data variable, as they
            # appear in the netCDF file
            for ncdim in dimensions:
                if ncdim in compression:
                    # This dimension is a sample dimension
                    # representing two or more compressed dimensions
                    c = compression[ncdim]
                    if 'gathered' in c:
                        # --------------------------------------------
                        # Compression by gathering. Note the
                        # uncompressed dimensions exist as internal
                        # dimensions.
                        # --------------------------------------------
                        c = c['gathered']
                        dimensions = g['nc'].dimensions        
                        uncompressed_shape = tuple(
                            [g['internal_dimension_sizes'][dim]
                             for dim in self._ncdimensions(ncvar)])
                        sample_axis = g['variable_dimensions'][ncvar].index(c['sample_dimension'])
                        data = self._create_data_gathered(
                            ncvar,
                            filearray,
                            uncompressed_shape=uncompressed_shape,
                            sample_axis=sample_axis,
                            list_indices=c['indices'])
                    elif 'ragged_indexed_contiguous' in c:
                        # --------------------------------------------
                        # Contiguous indexed ragged array. Check this
                        # before ragged_indexed and ragged_contiguous
                        # because both of these will exist for an
                        # indexed and contiguous array.
                        # --------------------------------------------
                        c = c['ragged_indexed_contiguous']
                        uncompressed_shape = (c['instance_dimension_size'],
                                              c['element_dimension_1_size'],
                                              c['element_dimension_2_size'])
                        data = self._create_data_ragged_indexed_contiguous(
                            ncvar,
                            filearray,
                            uncompressed_shape=uncompressed_shape,
                            profile_indices=c['profile_indices'],
                            elements_per_profile=c['elements_per_profile'])
                    elif 'ragged_contiguous' in c:                    
                        # --------------------------------------------
                        # Contiguous ragged array
                        # --------------------------------------------
                        c = c['ragged_contiguous']
                        uncompressed_shape=(c['instance_dimension_size'],
                                            c['element_dimension_size'])
                        data = self._create_data_ragged_contiguous(
                            ncvar,
                            filearray,
                            uncompressed_shape=uncompressed_shape,
                            elements_per_instance=c['elements_per_instance'])
                    elif 'ragged_indexed' in c:
                        # --------------------------------------------
                        # Indexed ragged array
                        # --------------------------------------------
                        c = c['ragged_indexed']
                        uncompressed_shape = (c['instance_dimension_size'],
                                              c['element_dimension_size'])
                        data = self._create_data_ragged_indexed(
                            ncvar,
                            filearray,
                            uncompressed_shape=uncompressed_shape,
                            instances=c['instances'])
                    else:
                        raise ValueError("Bad compression vibes. c.keys()={}".format(c.keys()))
        #--- End: if
                    
        return data
    #--- End: def

    def _create_NetCDF(self,filename=None, ncvar=None, dtype=None,
                       ndim=None, shape=None, size=None):
        '''
        '''
        return self.initialise('NetCDF', filename=filename,
                                ncvar=ncvar, dtype=dtype,
                                ndim=ndim, shape=shape,
                                size=size)
    #--- End: def
    
    def _create_domain_axis(self, size, ncdim=None):
        '''
        '''
        domain_axis = self.initialise('DomainAxis', size=size)
        if ncdim is not None:
            self.set_ncdim(domain_axis, ncdim)

        return domain_axis
    #-- End: def

    def _create_field_ancillary(self, ncvar):
        '''Create a field ancillary object.
    
:Parameters:
    
    ncvar: `str`
        The netCDF name of the field ancillary variable.

:Returns:

    out: `FieldAncillary`
        The new item.

        '''
        # Create a field ancillary object
        field_ancillary = self.initialise('FieldAncillary')

        # Insert properties
        self.set_properties(field_ancillary,
                            self.read_vars['variable_attributes'][ncvar],
                            copy=True)

        # Insert data
        data = self._create_data(ncvar, field_ancillary)
        self._set_data(field_ancillary, data, copy=False)

        # Store the netCDF variable name
        self.set_ncvar(field_ancillary, ncvar)
    
        return field_ancillary
    #--- End: def

    def initialise(self, object_type, **kwargs):
        '''
        '''
        return self.implementation.get_class(object_type)(**kwargs)
    #--- End: def

    def _parse_cell_methods(self, field_ncvar, cell_methods_string):
        '''Parse a CF cell_methods string.

:Examples 1:

>>> cell_methods = c.parse_cell_methods('time: mean')

:Parameters:

    cell_methods_string: `str`
        A CF cell_methods string.

:Returns:

    out: `list` of `dict`

:Examples 2:

>>> c = parse_cell_methods('t: minimum within years t: mean over ENSO years)')
>>> print c
[
]

        '''
        attribute = {field_ncvar+':cell_methods': cell_methods_string}

        incorrect_interval = ('Cell method interval', 'is incorrectly formatted')

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

                # Check that "name" ebds with colon? How? ('lat: mean (area-weighted) or lat: mean (interval: 1 degree_north comment: area-weighted)')

                axis = cell_methods.pop(0)[:-1]

                axes.append(axis)
            #--- End: while
            cm['axes'] = axes

            if not cell_methods:
                out.append(cm)
                break

            # Method
            cm['method'] = cell_methods.pop(0)
            
            if not cell_methods:
                out.append(cm)
                break

            # Climatological statistics and statistics which apply to
            # portions of cells
            while cell_methods[0] in ('within', 'where', 'over'):
                attr = cell_methods.pop(0)
                cm[attr] = cell_methods.pop(0)
                if not cell_methods:
                    break
            #--- End: while
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
                            self._add_message(
                                field_ncvar, field_ncvar,
                                message=incorrect_interval)
                            return []

                        try:
                            data = self.initialise('Data',
                                                   data=parsed_interval,
                                                   units=units)
                        except:
                            self._add_message(
                                field_ncvar, field_ncvar,
                                message=incorrect_interval,
                                attribute=attribute)
                            return []

                        intervals.append(data)
                        continue
                    #--- End: if

                    if term == 'comment':
                        comment = []
                        while cell_methods:
                            if cell_methods[0].endswith(')'):
                                break
                            if cell_methods[0].endswith(':'):
                                break
                            comment.append(cell_methods.pop(0))
                        #--- End: while
                        cm['comment'] = ' '.join(comment)
                #--- End: while 

                if cell_methods[0].endswith(')'):
                    cell_methods.pop(0)
            #--- End: if

            n_intervals = len(intervals)          
            if n_intervals > 1 and n_intervals != len(axes):
                self._add_message(
                    field_ncvar, field_ncvar,
                    message=incorrect_interval,
                    attribute=attribute)
                return []

            if intervals:
                cm['intervals'] = intervals

            out.append(cm)
        #--- End: while

        return out
    #--- End: def

    def _create_formula_terms_ref(self, f, key, coord, formula_terms):
        '''asdasdasdas

If the coordinate object has properties 'standard_name' or
'computed_standard_name' then they are copied to coordinate conversion
parameters.

:Parameters:

    f: `Field`

    key: `str`
        The internal identifier of the coordinate.

    coord: `Coordinate`

    formula_terms: `dict`
        The formula_terms attribute value from the netCDF file.

          *Example:*
            ``formula_terms={'a':'a','b':'b','orog':'surface_altitude'}``

:Returns:

    out: `CoordinateReference`

        '''
        g = self.read_vars

        domain_ancillaries = {}
        parameters         = {}
        
        for term, ncvar in formula_terms.iteritems():
            # The term's value is a domain ancillary of the field, so
            # we put its identifier into the coordinate reference.
            domain_ancillaries[term] = g['domain_ancillary_key'].get(ncvar)

        for name in ('standard_name', 'computed_standard_name'):            
            value = self.get_property(coord, name, None)
            if value is not None:
                parameters[name] = value
        #--- End: for
        
        coordref = self.initialise('CoordinateReference',
                                   coordinates=[key],
                                   domain_ancillaries=domain_ancillaries,
                                   parameters=parameters)

        return coordref
    #--- End: def

    def _ncdimensions(self, ncvar):
        '''Return a list of the netCDF dimensions corresponding to a netCDF
variable.

If the variable has been compressed then the *implied, uncompressed*
dimensions are returned.
    
:Examples 1: 

>>> n._ncdimensions('humidity')
['time', 'lat', 'lon']

:Parameters:

    ncvar: `str`
        The netCDF variable name.

:Returns:

    out: `list`
        The list of netCDF dimension names spanned by the netCDF
        variable.

        '''
        g = self.read_vars

        variable = g['variables'][ncvar]
     
        ncdimensions = list(g['variable_dimensions'][ncvar])
        
        # Remove a string-length dimension, if there is one. DCH ALERT
        if (variable.datatype.kind == 'S' and
            variable.ndim >= 2 and variable.shape[-1] > 1):
            ncdimensions.pop()
    
        # Check for dimensions which have been compressed. If there are
        # any, then return the netCDF dimensions for the uncompressed
        # variable.
        compression = g['compression']
        if compression and set(compression).intersection(ncdimensions):
            for ncdim in ncdimensions:
                if ncdim in compression:
                    c = compression[ncdim]
                    if 'gathered' in c:
                        # Compression by gathering
                        i = ncdimensions.index(ncdim)
                        ncdimensions[i:i+1] = c['gathered']['implied_ncdimensions']
                    elif 'ragged_indexed_contiguous' in c:
                        # Indexed contiguous ragged array.
                        #
                        # Check this before ragged_indexed and
                        # ragged_contiguous because both of these will
                        # exist for an array that is both indexed and
                        # contiguous.
                        i = ncdimensions.index(ncdim)
                        ncdimensions = c['ragged_indexed_contiguous']['implied_ncdimensions']
                    elif 'ragged_contiguous' in c:
                        # Contiguous ragged array
                        ncdimensions = c['ragged_contiguous']['implied_ncdimensions']
                    elif 'ragged_indexed' in c:
                        # Indexed ragged array
                        ncdimensions = c['ragged_indexed']['implied_ncdimensions']
    
                    break
        #--- End: if
        
        return map(str, ncdimensions)
    #--- End: def

    def _create_data_gathered(self, ncvar, filearray,
                              uncompressed_shape=None,
                              sample_axis=None, list_indices=None):
        '''
        '''
        uncompressed_ndim  = len(uncompressed_shape)
        uncompressed_size  = long(reduce(operator.mul, uncompressed_shape, 1))

        compression_parameters = {'sample_axis': sample_axis,
                                  'indices'    : list_indices}
            
        array = self.create_compressed_array(
            filearray,
            uncompressed_ndim=uncompressed_ndim,
            uncompressed_shape=uncompressed_shape,
            uncompressed_size=uncompressed_size,
            compression_type='gathered',
            compression_parameters=compression_parameters
        )

        return self._create_Data(array, ncvar=ncvar)
    #--- End: def
    
    def _create_data_ragged_contiguous(self, ncvar, filearray,
                                       uncompressed_shape=None,
                                       elements_per_instance=None):
        '''
        '''
        uncompressed_ndim  = len(uncompressed_shape)
        uncompressed_size  = long(reduce(operator.mul, uncompressed_shape, 1))

        compression_parameters = {
            'elements_per_instance': elements_per_instance} 
        
        array = self.create_compressed_array(
            filearray,
            uncompressed_ndim=uncompressed_ndim,
            uncompressed_shape=uncompressed_shape,
            uncompressed_size=uncompressed_size,
            compression_type='ragged_contiguous',
            compression_parameters=compression_parameters
        )
        
        return self._create_Data(array, ncvar=ncvar)
    #--- End: def
    
    def _create_data_ragged_indexed(self, ncvar, filearray,
                                    uncompressed_shape=None,
                                    instances=None):
        '''
        '''
        uncompressed_ndim  = len(uncompressed_shape)
        uncompressed_size  = long(reduce(operator.mul, uncompressed_shape, 1))
        
        compression_parameters = {'instances': instances}

        array = self.create_compressed_array(
            filearray,
            uncompressed_ndim=uncompressed_ndim,
            uncompressed_shape=uncompressed_shape,
            uncompressed_size=uncompressed_size,
            compression_type='ragged_indexed',
            compression_parameters=compression_parameters
        )

        return self._create_Data(array, ncvar=ncvar)
    #--- End: def
    
    def _create_data_ragged_indexed_contiguous(self, ncvar, filearray,
                                               uncompressed_shape=None,
                                               profile_indices=None,
                                               elements_per_profile=None):
        '''
        '''
        uncompressed_ndim  = len(uncompressed_shape)
        uncompressed_size  = long(reduce(operator.mul, uncompressed_shape, 1))
        
        compression_parameters = {
            'profile_indices'     : profile_indices,
            'elements_per_profile': elements_per_profile}
        
        array = self.create_compressed_array(
            filearray,
            uncompressed_ndim=uncompressed_ndim,
            uncompressed_shape=uncompressed_shape,
            uncompressed_size=uncompressed_size,
            compression_type='ragged_indexed_contiguous',
            compression_parameters=compression_parameters
        )
        
        return self._create_Data(array, ncvar=ncvar)
    #--- End: def
    
    def _create_Data(self, array=None, ncvar=None, **kwargs):
        '''
        '''
        units    = None
        calendar = None

        g = self.read_vars
        
        if ncvar is not None:
            units    = g['variable_attributes'][ncvar].get('units', None)
            calendar = g['variable_attributes'][ncvar].get('calendar', None)

        return self.initialise('Data', data=array, units=units,
                                calendar=calendar, **kwargs)
    #--- End: def

    def _copy_construct(self, construct_type, field_ncvar, ncvar):
        '''Return a copy of an existing construct.

:Examples 1:

>>> c = n._copy_construct('domain_ancillary', 'tas', 'orog')

:Parameters:

    construct_type: `str`
        E.g. 'dimension_coordinate'

    field_ncvar: `str
        The netCDF variable name of the field that will contain the
        copy of the construct.

    ncvar: `str`
        The netCDF variable name of the construct.

:Returns:

    out:
        A copy of the construct.

        '''
        g = self.read_vars

        component_report = g['component_report'].get(ncvar)

        if component_report is not None:
            for var, report in component_report.iteritems():                
                g['read_report'][field_ncvar]['components'].setdefault(var, []).extend(
                    report)
        #--- End: if

        return g[construct_type][ncvar].copy()    
    #--- End: def
    
    # ================================================================
    #
    # Methods for checking CF compliance
    #
    # These methods (whose names all start with "_check") check the
    # minimum required for mapping te file to CFDM structural
    # elements. General CF compliance is not checked (e.g. whether or
    # not grid mapping variable has a grid_mapping_name attribute).
    # ================================================================
    def _check_bounds(self, field_ncvar, parent_ncvar, attribute,
                      bounds_ncvar, geometry=False):
        '''asdasdasds

Checks that

  * The bounds variable has exactly one more dimension than the parent
    variable

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

    out: `bool`

        '''
        attribute = {parent_ncvar+':'+attribute: bounds_ncvar}
        
        missing_variable      = ('Bounds variable', 'is not in file')
        incorrect_dimensions  = ('Bounds variable', 'spans incorrect dimensions')

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
                                           'not in node_coordinates ????'),
                                  attribute=attribute,
                                  variable=parent_ncvar)
                ok = False
        else:        
            c_ncdims = self._ncdimensions(parent_ncvar)
            b_ncdims = self._ncdimensions(bounds_ncvar)
            
            if len(b_ncdims) == len(c_ncdims) + 1:
                if c_ncdims != b_ncdims[:-1]:
                    self._add_message(field_ncvar, bounds_ncvar,
                                      message=incorrect_dimensions,
                                      attribute=attribute,
                                      dimensions=g['variable_dimensions'][bounds_ncvar],
                                      variable=parent_ncvar)
                    ok = False
    
            else:
                self._add_message(field_ncvar, bounds_ncvar,
                                  message=incorrect_dimensions,
                                  attribute=attribute,
                                  dimensions=g['variable_dimensions'][bounds_ncvar],
                                  variable=parent_ncvar)
                ok = False
        #--- End: if
        
        return ok
    #--- End: def
    
    def _check_cell_measures(self, field_ncvar, string, parsed_string):
        '''asasdads

:Parameters:

    field_ncvar: `str`
        
    string: `str`
        The value of the netCDF cell_measures attribute.

    parsed_string: `list`

:Returns:

    out: `bool`

        '''
        attribute = {field_ncvar+':cell_measures': string}

        incorrectly_formatted = ('cell_measures attribute', 'is incorrectly formatted')
        incorrect_dimensions  = ('Cell measures variable', 'spans incorrect dimensions')
        missing_variable      = ('Cell measures variable',
                                 'is not in file nor referenced by the external_variables global attribute')

        g = self.read_vars
        
        if not parsed_string:
            self._add_message(field_ncvar, field_ncvar,
                              message=incorrectly_formatted,
                              attribute=attribute)
            return False

        parent_dimensions  = self._ncdimensions(field_ncvar)
        external_variables = self.read_vars['external_variables']
        
        ok = True
        for x in parsed_string:
            measure, values = x.items()[0]
            if len(values) != 1:
                self._add_message(field_ncvar, field_ncvar,
                                  message=incorrectly_formatted,
                                  attribute=attribute)
                ok = False
                continue

            ncvar = values[0]
            external = (ncvar in external_variables)

            # Check that the variable exists in the file, or if not
            # that it is listed in the 'external_variables' global
            # file attribute
            if (not external and ncvar not in g['internal_variables']):
                self._add_message(field_ncvar, ncvar,
                                  message=missing_variable,
                                  attribute=attribute)
                ok = False
                continue
                
            dimensions = self._ncdimensions(ncvar)
            if (not external and
                not self._dimensions_are_subset(ncvar, dimensions, parent_dimensions)):
                # The cell measure variable's dimensions do NOT span a
                # subset of the parent variable's dimensions.
                self._add_message(field_ncvar, ncvar,
                                  message=incorrect_dimensions,
                                  attribute=attribute,
                                  dimensions=g['dimensons'][ncvar])
                ok = False
                continue
        #--- End: for

        return ok
    #--- End: def

    def _check_ancillary_variables(self, field_ncvar, string,
                                   parsed_string):
        '''
:Parameters:

    field_ncvar: `str`
        
    ancillary_variables: `str`
        The value of the netCDF cell_measures attribute.

    parsed_ancillary_variables: `list`

:Returns:

    out: `bool`

        '''
        attribute = {field_ncvar+':ancillary_variables': string}

        incorrectly_formatted = ('ancillary_variables attribute', 'is incorrectly formatted')
        missing_variable      = ('Ancillary variable', 'is not in file')
        incorrect_dimensions  = ('Ancillary variable', 'spans incorrect dimensions')
        
        _debug = self.read_vars['_debug']

        g = self.read_vars
        
        if not parsed_string:
            d = self._add_message(field_ncvar, field_ncvar,
                                  message=incorrectly_formatted,
                                  attribute=attribute)

            if _debug:
                print '    Error processing netCDF variable {}: {}'.format(
                    field_ncvar, d['message'])                

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
            
            if not self._dimensions_are_subset(ncvar, self._ncdimensions(ncvar),
                                               parent_dimensions):
                # The ancillary variable's dimensions do NOT span a
                # subset of the parent variable's dimensions
                self._add_message(field_ncvar, ncvar,
                                  message=incorrect_dimensions,
                                  attribute=attribute,
                                  dimensions=g['variable_dimensions'][ncvar])
                ok = False                
                continue
        #--- End: for

        return ok
    #--- End: def

    def _check_auxiliary_scalar_coordinate(self, field_ncvar,
                                           coord_ncvar, string):
        '''
:Parameters:

    field_ncvar: `str`
        
:Returns:

    out: `bool`

        '''
        attribute = {field_ncvar+':coordinates': string}

        incorrectly_formatted = ('coordinate attribute', 'is incorrectly formatted')
        missing_variable      = ('Auxiliary/scalar coordinate variable', 'is not in file')
        incorrect_dimensions  = ('Auxiliary/scalar coordinate variable',
                                 'spans incorrect dimensions')
        
        g = self.read_vars

        if coord_ncvar not in g['internal_variables']:
            self._add_message(field_ncvar, coord_ncvar,
                              message=missing_variable,
                              attribute=attribute)
            return False
            
        # Check that the variable's dimensions span a subset of the
        # parent variable's dimensions (allowing for char variables
        # with a trailing dimension)
        dimensions        = self._ncdimensions(coord_ncvar)
        parent_dimensions = self._ncdimensions(field_ncvar)
        if not self._dimensions_are_subset(coord_ncvar,
                                           self._ncdimensions(coord_ncvar),
                                           self._ncdimensions(field_ncvar)):
            d = self._add_message(field_ncvar, coord_ncvar,
                                  message=incorrect_dimensions,
                                  attribute=attribute,
                                  dimensions=g['variable_dimensions'][coord_ncvar])
            return False

        return True
    #--- End: def

    def _dimensions_are_subset(self, ncvar, dimensions, parent_dimensions):
        '''Return True if 
        '''
        if not set(dimensions).issubset(parent_dimensions):
            if not (self.read_vars['variables'][ncvar].datatype.kind == 'S' and
                    set(dimensions[:-1]).issubset(parent_dimensions)):
                return False

        return True
    #--- End: def
    
    def _check_grid_mapping(self, field_ncvar, grid_mapping,
                            parsed_grid_mapping):
        '''

:Parameters:

    field_ncvar: `str`

    grid_mapping: `str`

    parsed_grid_mapping: `dict`

:Returns:

    out: `bool`

        '''
        attribute = {field_ncvar+':grid_mapping': grid_mapping}

        incorrectly_formatted  = ('grid_mapping attribute', 'is incorrectly formatted')
        missing_variable       = ('grid_mapping variable', 'is not in file')
        coordinate_not_in_file = ('Grid mapping coordinate variable', 'is not in file')
        coordinate_not_in_data_variable = ('Grid mapping coordinate variable',
                                           'is not used by data variable')

        g = self.read_vars
        
        if not parsed_grid_mapping:
            self._add_message(field_ncvar, field_ncvar,
                              message=incorrectly_formatted,
                              attribute=attribute)
            return False

        ok = True
        for x in parsed_grid_mapping:
            grid_mapping_ncvar, values = x.items()[0]
            if grid_mapping_ncvar not in g['internal_variables']:
                ok = False
                self._add_message(field_ncvar, grid_mapping_ncvar,
                                  message=missing_variable,
                                  attribute=attribute)
            
            for coord_ncvar in values:
                if coord_ncvar not in g['internal_variables']:
                    ok = False
                    self._add_message(field_ncvar, coord_ncvar,
                                      message=coordinate_not_in_file,
                                      attribute=attribute)
        #--- End: for
        
        if not ok:
            return False
        
        return True
    #--- End: def

    def _check_compress(self, parent_ncvar, compress, parsed_compress):
        '''
        '''
        attribute = {parent_ncvar+':compress': compress}

        incorrectly_formatted = ('compress attribute', 'is incorrectly formatted')
        missing_dimension     = ('Compressed dimension', 'is not in file')
        
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
        #--- End: for
        
        return ok
    #--- End: def

#   def _check_node_coordinate(self, field_ncvar, coord_ncvar, node_coordinate):
#       '''
#       '''
#       attribute = {coord_ncvar+':bounds': node_coordinate}
#
#       nc = self.read_vars['nc']
#
#               
#       incorrectly_formatted = ('node_coordinates attribute', 'is incorrectly formatted')
#       missing_attribute     = ('node_coordinates attribute', 'is missing')
#       missing_variable      = ('Node coordinate variable', 'is not in file')
#
#       if node_coordinates is None:
#           self._add_message(field_ncvar, geometry_ncvar,
#                             message=missing_attribute,
#                             attribute=attribute)
#           return False
#
#       if not parsed_node_coordinates:
#           self._add_message(field_ncvar, geometry_ncvar,
#                             message=incorrectly_formatted,
#                             attribute=attribute)
#           return False
#
#       ok = True
        
    def _check_node_coordinates(self, field_ncvar, geometry_ncvar,
                                node_coordinates,
                                parsed_node_coordinates):
        '''
        '''

        attribute = {geometry_ncvar+':node_coordinates': node_coordinates}

        g = self.read_vars
        
        incorrectly_formatted = ('node_coordinates attribute', 'is incorrectly formatted')
        missing_attribute     = ('node_coordinates attribute', 'is missing')
        missing_variable      = ('Node coordinate variable', 'is not in file')

        if node_coordinates is None:
            self._add_message(field_ncvar, geometry_ncvar,
                              message=missing_attribute,
                              attribute=attribute)
            return False

        if not parsed_node_coordinates:
            self._add_message(field_ncvar, geometry_ncvar,
                              message=incorrectly_formatted,
                              attribute=attribute)
            return False

        ok = True
        
        for ncvar in parsed_node_coordinates:
            # Check that the variable exists in the file
            if ncvar not in g['internal_variables']:
                self._add_message(field_ncvar, ncvar,
                                  message=missing_variable,
                                  attribute=attribute)
                ok = False                
                continue
        #--- End: for

        return ok
    #--- End: def

    def _check_node_count(self, field_ncvar, geometry_ncvar,
                          node_count, parsed_node_count):
        '''
        '''
        attribute = {geometry_ncvar+':node_count': node_count}

        g = self.read_vars

        if node_node_count is None:
            return True
                
        incorrectly_formatted = ('node_count attribute', 'is incorrectly formatted')
        missing_variable      = ('Node count variable', 'is not in file')

        if len(parsed_node_count) != 1:
            self._add_message(field_ncvar, ncvar,
                              message=incorrectly_formatted,
                              attribute=attribute)
            return False
            
        ok = True

        for ncvar in parsed_node_count:
            # Check that the variable exists in the file
            if ncvar not in g['internal_variables']:
                self._add_message(field_ncvar, ncvar,
                                  message=missing_variable,
                                  attribute=attribute)
                ok = False                
                continue
        #--- End: for

        return ok
    #--- End: def

    def _check_part_node_count(self, field_ncvar, geometry_ncvar,
                               part_node_count, parsed_part_node_count):
        '''
        '''
        if part_node_count is None:
            return True
                
        attribute = {geometry_ncvar+':part_node_count': part_node_count}

        g = self.read_vars

        incorrectly_formatted = ('part_node_count attribute', 'is incorrectly formatted')
        missing_variable      = ('Part node count variable', 'is not in file')
        
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
        #--- End: for

        return ok
    #--- End: def

    def _check_interior_ring(self, field_ncvar, geometry_ncvar,
                          interior_ring, parsed_interior_ring):
        '''
        '''
        if node_interior_ring is None:
            return True
                
        attribute = {geometry_ncvar+':interior_ring': interior_ring}

        g = self.read_vars
                
        incorrectly_formatted = ('interior_ring attribute', 'is incorrectly formatted')
        missing_variable      = ('Interior ring variable', 'is not in file')
        
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
        #--- End: for

        return ok
    #--- End: def

    def _check_instance_dimension(self, parent_ncvar, instance_dimension):
        '''asdasd

CF-1.7 Appendix A

* instance_dimension: An attribute which identifies an index variable
                      and names the instance dimension to which it
                      applies. The index variable indicates that the
                      indexed ragged array representation is being
                      used for a collection of features.

        '''  
        attribute = {parent_ncvar+':instance_dimension': instance_dimension}
 
        missing_dimension = ('Instance dimension', 'is not in file')

        if instance_dimension not in self.read_vars['internal_dimension_sizes']:
            self._add_message(None, parent_ncvar,
                              message=missing_dimension,
                              attribute=attribute)
            return False

        return True
    #--- End: def
                
    def _check_sample_dimension(self, parent_ncvar, sample_dimension):
        '''asdasd

CF-1.7 Appendix A

* sample_dimension: An attribute which identifies a count variable and
                    names the sample dimension to which it
                    applies. The count variable indicates that the
                    contiguous ragged array representation is being
                    used for a collection of features.

        '''        
        # Check that the named netCDF dimension exists in the file
        return sample_dimension in self.read_vars['internal_dimension_sizes']
    #--- End: def
        
    def _split_by_white_space(self, parent_ncvar, string):
        '''Split a string by white space.
        '''
        if string is None:
            return []
        
        return string.split()
    #--- End: def

    def _parse_x(self, parent_ncvar, string):
        '''

        '''
        # ============================================================
        # Thanks to Alan Iwi for creating these regular expressions
        # ============================================================
        
        def subst(s):
            "substitute tokens for WORD and SEP (space or end of string)"
            return s.replace('WORD', r'[A-Za-z0-9_]+').replace('SEP', r'(\s+|$)')

        out = []
        
        pat_value = subst('(?P<value>WORD)SEP')
        pat_values = '({})+'.format(pat_value)
        
        pat_mapping = subst('(?P<mapping_name>WORD):SEP(?P<values>{})'.format(pat_values))
        pat_mapping_list = '({})+'.format(pat_mapping)
        
        pat_all = subst('((?P<sole_mapping>WORD)|(?P<mapping_list>{}))$'.format(pat_mapping_list))
        
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
                          for value in re.finditer(pat_value, mapping.group('values'))]

                out.append({term: values})

        return out
    #--- End: def

    def create_compressed_array(self, array=None,
                                uncompressed_ndim=None,
                                uncompressed_shape=None,
                                uncompressed_size=None,
                                compression_type=None,
                                compression_parameters=None):
        '''
        '''
        return self.initialise('CompressedArray',
            array=array,
            ndim=uncompressed_ndim,
            shape=uncompressed_shape,
            size=uncompressed_size,
            compression_type=compression_type,
            compression_parameters=compression_parameters)
    #--- End: def

    def del_property(self, construct, prop):
        '''
        '''
        return construct.del_property(prop)
    #--- End: def
    
#--- End: class

