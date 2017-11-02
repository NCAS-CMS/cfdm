import copy
import re
import os
import struct
import sys

import numpy

from .functions import abspath, flat

class NetCDF(object):
    '''
    '''
    def __init__(self, mode=None, **kwargs):
        '''
        '''
        if mode == 'read':
            for attr in ('NetCDFArray',
                         'AuxiliaryCoordinate',
                         'CellMeasure',        
                         'CellMethod',        
                         'CoordinateReference',
                         'DimensionCoordinate',
                         'DomainAncillary',
                         'DomainAxis',         
                         'Field',     
                         'FieldAncillary',     
                         'Bounds', 
                         'Data',
                         'Units'):
                if attr not in kwargs:
                    raise ValueError("Must set {!r} parameter in 'read' mode".format(attr))
        elif mode == 'write':
            for attr in ('NetCDFArray',
                         'Conventions'):
                if attr not in kwargs:
                    raise ValueError("Must set {!r} parameter in 'write' mode".format(attr))
        #--- End: if

        for key, value in kwargs.iteritems():
            setattr(self, key, value)
            
        self._read_vars = {
            #
            'new_dimensions': {},
            #
            'formula_terms': {},
            #
            'compression': {},
            'uncompress' : True,
            # Chatty?
            'verbose': False,
            # Debug  print statements?
            '_debug': False,
        }
        
        self._write_vars =  {
            # Format of output file
            'fmt': None,
            # netCDF4.Dataset instance
            'netcdf'           : None,    
            # Map netCDF variable names to netCDF4.Variable instances
            'nc': {},      
            # Map netCDF dimension names to netCDF dimension sizes
            'ncdim_to_size': {},
            # Dictionary of netCDF variable names and netCDF
            # dimensions keyed by items of the field (such as a
            # coordinate or a coordinate reference)
            'seen': {},
            # Set of all netCDF dimension and netCDF variable names.
            'ncvar_names': set(()),
            # Set of global or non-standard CF properties which have
            # identical values across all input fields.
            'global_properties': set(()), 
            'variable_attributes': set(()),
            'bounds': {},
            # Compression/endian
            'compression': {},
            'endian': 'native',
            'least_significant_digit': None,
            # CF properties which need not be set on bounds if they're set
            # on the parent coordinate
            'omit_bounds_properties': ('units', 'standard_name', 'axis',
                                       'positive', 'calendar', 'month_lengths',
                                       'leap_year', 'leap_month'),
            # Data type conversions to be applied prior to writing
            'datatype': {},
            #
            'unlimited': (),
            # Print statements
            'verbose': False,
            '_debug' : False,
        }
    #--- End: def    
    
    def read(self, filename, field=(), verbose=False, uncompress=True,
             _debug=False):
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

          ======================  ====================================
          *field*                 Field components
          ======================  ====================================
          ``'field_ancillary'``   Field ancillary objects
          ``'domain_ancillary'``  Domain ancillary objects
          ``'dimension'``         Dimension coordinate objects
          ``'auxiliary'``         Auxiliary coordinate objects
          ``'measure'``           Cell measure objects
          ``'all'``               All of the above
          ======================  ====================================

            *Example:*
              To create fields from auxiliary coordinate objects:
              ``field=['auxiliary']``.

            *Example:*
              To create fields from domain ancillary and cell measure
              objects: ``field=['domain_ancillary', 'measure']``.

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
        if isinstance(filename, file):
            name = filename.name
            filename.close()
            filename = name

        self.read_vars = copy.deepcopy(self._read_vars)
        g = self.read_vars
        
        g['uncompress'] = uncompress
        g['verbose']    = verbose
        g['_debug']     = _debug
        
        compression = {}
        
        # ----------------------------------------------------------------
        # Parse field
        # ----------------------------------------------------------------
        try:
            iter(field)
        except TypeError:
            raise ValueError(
                "Can't read: Bad parameter value: field={!r}".format(field))
               
        if 'all' in field:
            field = set(('domain_ancillary', 'field_ancillary',
                         'dimension_coordinate', 'auxiliary_coordinate',
                         'cell_measure'))
    
        g['field']    = field
        g['promoted'] = []
        
        filename = abspath(filename)
        g['filename'] = filename
        
        # ------------------------------------------------------------
        # Open the netCDF file to be read
        # ------------------------------------------------------------        
        nc = self.NetCDFArray.file_open(filename, 'r')
        g['nc'] = nc
        
        if _debug:
            print 'Reading file', filename
            print '    Input netCDF dataset =',nc
    
        # Set of all of the netCDF variable names in the file.
        #
        # For example:
        # >>> variables
        # set(['lon','lat','tas'])
        variables = set(map(str, nc.variables))
    
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
            
        # ----------------------------------------------------------------
        # Create a dictionary keyed by nc variable names where each key's
        # value is a dictionary of that variable's nc
        # attributes. E.g. attributes['tas']['units']='K'
        # ----------------------------------------------------------------
        attributes = {}
        for ncvar in variables:
            attributes[ncvar] = {}
            for attr in map(str, nc.variables[ncvar].ncattrs()):
                try:
                    attributes[ncvar][attr] = nc.variables[ncvar].getncattr(attr)
                    if isinstance(attributes[ncvar][attr], basestring):
                        try:
                            attributes[ncvar][attr] = str(attributes[ncvar][attr])
                        except UnicodeEncodeError:
                            attributes[ncvar][attr] = attributes[ncvar][attr].encode(errors='ignore')
                except UnicodeDecodeError:
                    pass
            #--- End: for  
    
#            # Check for bad units
#            units = self.Units(attributes[ncvar].get('units', None), 
#                               attributes[ncvar].get('calendar', None))
#            if verbose and not units.isvalid:
#                print(
#"WARNING: Unsupported units in file {0} on variable {1}: {2}".format(
#    filename, ncvar, units))
        #--- End: for
    
        # ----------------------------------------------------------------
        # Remove everything bar data variables from the list of
        # variables. I.e. remove dimension and auxiliary coordinates,
        # their bounds and grid_mapping variables
        # ----------------------------------------------------------------
        nc_dimensions = map(str, nc.dimensions)
        if _debug:
            print '    netCDF dimensions:', nc_dimensions
    
        sample_ncdimension   = None
        instance_ncdimension = None
            
        for ncvar in variables.copy():
            if ncvar not in variables:
                # Skip netCDF variables which have already been checked
                continue
            
            if _debug:
                print '    Pre-processing', ncvar
    
            # Remove list, index and count variables
            compressed_ncdims = attributes[ncvar].get('compress', None)
            if compressed_ncdims is not None:
                # This variable is a list variable for gathering arrays
                self._read_parse_compression_gathered( ncvar,
                                                       attributes, compressed_ncdims)
                variables.discard(ncvar)
            
            if g['global_attributes'].get('featureType'):
                if 'sample_dimension' in attributes[ncvar]:
                    # This variable is a count variable for DSG contiguous
                    # ragged arrays
                    sample_ncdimension = attributes[ncvar]['sample_dimension']        
                    element_dimension_2 = self._read_parse_DSG_contiguous_compression(
                        ncvar,
                        attributes,
                        sample_ncdimension)
                    variables.discard(ncvar)
                
                if 'instance_dimension' in attributes[ncvar]:
                    # This variable is an index variable for DSG indexed
                    # ragged arrays
                    instance_ncdimension = attributes[ncvar]['instance_dimension']
                    element_dimension_1 = self._read_parse_DSG_indexed_compression(
                        ncvar,
                        attributes,
                        instance_ncdimension)
                    variables.discard(ncvar)
                
                if sample_ncdimension and instance_ncdimension:
                    self._read_parse_DSG_indexed_contiguous_compression(
                        ncvar,
                        sample_ncdimension,
                        instance_ncdimension)
                    sample_ncdimension   = None
                    instance_ncdimension = None
            #--- End: if
            
            # Remove dimension coordinates and their bounds
            if ncvar in nc_dimensions:
    
                if ncvar in variables:
                    # ----------------------------------------------------
                    # ncvar is a CF coordinate variable
                    # ----------------------------------------------------
                    if 'dimension_coordinate' in g['field']:
                        # Add the dimension coordinate to the set of
                        # top-level fields, so that it doesn't get demoted
                        # if the auxiliary coordinate is also in a
                        # coordinate reference.
                        g['promoted'].append(ncvar)
                    else:
                        # Do not promote a dimension coordinate to also
                        # appear as a top-level field
                        if _debug:
                            print '        Is a netCDF coordinate variable'
                        variables.discard(ncvar)
    
                    for attr in ('bounds', 'climatology'):
                        if attr not in attributes[ncvar]:
                            continue
    
                        if _debug:
                            print '        Has bounds'
                        
                        # Check the dimensionality of the coordinate's
                        # bounds. If it is not right, then it can't be a
                        # bounds variable and so promote to an independent
                        # data variable
                        bounds = attributes[ncvar][attr]
                        if bounds in nc.variables:
                            if nc.variables[bounds].ndim == nc.variables[ncvar].ndim + 1:
                                variables.discard(bounds)
                            else:
                                del attributes[ncvar][attr]
    
                            break
                        else:
                            del attributes[ncvar][attr]
                            if verbose:
                                print(
    "WARNING: Missing bounds variable {!r} in {}".format(bounds, filename))
                    #--- End: for
    
                    # Remove domain ancillaries (unless they have been
                    # promoted) and their bounds.
                    if 'formula_terms' in attributes[ncvar]:
                        formula_terms = attributes[ncvar]['formula_terms']
                        if _debug:
                            print '        Has formula_terms'
                            
                        self._read_formula_terms_variables(ncvar, formula_terms,
                                                           variables, coord=True)
    
                        bounds = attributes[ncvar].get('bounds', None)
                        if bounds is not None and 'formula_terms' in attributes[bounds]:
                            bounds_formula_terms = attributes[bounds]['formula_terms']
    
                            self._read_formula_terms_variables(ncvar,
                                                               bounds_formula_terms,
                                                               variables,
                                                               bounds=True)
                    #--- End: if
    
                #--- End: if
                    
                continue
            #--- End: if
    
            # Still here? Then remove auxiliary coordinates (unless they
            # have been promoted) and their bounds.
            if 'coordinates' in attributes[ncvar]:
                # Allow for (incorrect) comma separated lists
                for aux in re.split('\s+|\s*,\s*', attributes[ncvar]['coordinates']):
                    if aux in variables:
                        # ------------------------------------------------
                        # aux is a CF auxiliary coordinate variable
                        # ------------------------------------------------
                        if 'auxiliary_coordinate' in g['field']:
                            # Add the auxiliary coordinate to the set of
                            # top-level fields, so that it doesn't get
                            # demoted if the auxiliary coordinate is also
                            # in a coordinate reference.
                            g['promoted'].append(ncvar)
                        else:
                            # Do not promote an auxiliary coordinate to
                            # also appear as a top-level field
                            if _debug:
                                print '        Has auxiliary coordinate:', aux
                            variables.discard(aux)
                                        
                        for attr in ('bounds', 'climatology'):
                            if attr not in attributes[aux]:
                                continue
                            
                            # Check the dimensionality of the coordinate's
                            # bounds. If it is not right, then it can't be
                            # a bounds variable and so promote to an
                            # independent data variable.
                            bounds = attributes[aux][attr]
                            if bounds in nc.variables:
                                if nc.variables[bounds].ndim == nc.variables[aux].ndim+1:
                                    variables.discard(bounds)
                                else:
                                    del attributes[aux][attr]
                                            
                                break
                            else:
                                del attributes[aux][attr]
                                if verbose:
                                    print(
"WARNING: Missing bounds variable {0!r} in {1}".format(bounds, filename))
                #--- End: for
            #--- End: if
            
            # Remove field ancillaries (unless they have been promoted).
            if ('field_ancillary' not in g['field'] and
                'ancillary_variables' in attributes[ncvar]):
                # Allow for (incorrect) comma separated lists
                for anc in re.split('\s+|\s*,\s*',
                                    attributes[ncvar]['ancillary_variables']):
                    if _debug:
                        print '        Has field ancillary:', anc
                    variables.discard(anc)
            #--- End: if
    
            # Remove grid mapping variables
            if 'grid_mapping' in attributes[ncvar]:
                if _debug:
                    print '        Has grid mapping:', ncvar
                variables.discard(attributes[ncvar]['grid_mapping'])
    
            # Remove cell measure variables (unless they have been promoted).
            if 'cell_measure' not in g['field'] and 'cell_measures' in attributes[ncvar]:
                cell_measures = re.split('\s*(\w+):\s*',
                                         attributes[ncvar]['cell_measures'])
                for msr in cell_measures[2::2]:
                    if _debug:
                        print '        Has cell measure:', msr
                    variables.discard(msr)
            #--- End: if
        #--- End: for
    
        g['featureType'] = global_attributes.get('featureType')
                
        # ----------------------------------------------------------------
        # Everything left in the variables set is now a proper data
        # variable, so make a list of fields, each of which contains one
        # data variable and the relevant shared metadata.
        # ----------------------------------------------------------------
        if _debug:
            print 'Data variables that will become fields:'
            for ncvar in variables:
                print '   ', ncvar
    
        domain_ancillaries    = {}
        field_ancillaries     = {}
        dimension_coordinates = {}
        auxiliary_coordinates = {}
        cell_measures         = {}
#        coordref_parameters   = {}
        list_variables        = {}
    
        fields_in_file = [] #self.FieldList()
    
        for data_ncvar in variables:
            f = self._read_create_Field(data_ncvar,
                                        attributes,
                                        dimension_coordinates,
                                        auxiliary_coordinates,
                                        cell_measures,
                                        domain_ancillaries,
                                        field_ancillaries,
                                        list_variables,
                                        verbose=verbose)
    
            fields_in_file.append(f)
        #--- End: for
    
        return fields_in_file
    #--- End: def

    @classmethod
    def file_type(cls, filename):
        '''
    
:Parameters:
    
    filename: `str`
        The file name.
    
:Returns:
 
    out: `str`
        The format type of the file.
    
:Examples:

>>> filetype = file_type(filename)
    
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

    def _read_parse_compression_gathered(self, ncvar, attributes,
                                         compressed_ncdims):
        '''
        '''
        g = self.read_vars
        
        _debug = g['_debug']
        if _debug:
            print '        List variable: compress =', compressed_ncdims
    
        compression_type = 'gathered'
        gathered_ncdimension = g['nc'][ncvar].dimensions[0]
        indices = self._read_create_array(ncvar, attributes)
        
        g['compression'][gathered_ncdimension] = {
            'gathered': {'indices'             : indices,
                         'implied_ncdimensions': compressed_ncdims.split()}}
    #--- End: def
    
    def _read_parse_DSG_contiguous_compression(self, ncvar,
                                               attributes,
                                               sample_ncdimension):
        '''
        ncvar: `str`
            The netCDF variable name of the DSG count variable.
    
        attributes: `dict`
    
        sample_ncdimension: `str`
            The netCDF variable name of the DSG sample dimension.
    '''
        g = self.read_vars        

        _debug = g['_debug']
        if _debug:
            print '    DSG count variable: sample_dimension =', sample_ncdimension
    
        variable = g['nc'][ncvar]
        instance_ncdimension = variable.dimensions[0]
    
        elements_per_instance = self._read_create_array(ncvar, attributes)
    
        instance_dimension_size = elements_per_instance.size    
        element_dimension_size  = int(elements_per_instance.max())
    
        # Create an empty Data array which has dimensions (instance
        # dimension, element dimension).
        data = self.Data.compression_initialize_contiguous(
            instance_dimension_size,
            element_dimension_size,
            elements_per_instance)
    
        if _debug:
            print '    DSG contiguous array implied shape:', data.shape
    
        # Make up a netCDF dimension name for the element dimension
        featureType = g['global_attributes'].get('featureType')
        if featureType in ('timeSeries', 'trajectory', 'profile'):
            element_dimension = featureType.lower()
        elif featureType == 'timeSeriesProfile':
            element_dimension = 'profile'
        elif featureType == 'trajectoryProfile':
            element_dimension = 'profile'
        else:
            element_dimension = 'element'
        if _debug:        
            print '    featureType =', featureType
    
        base = element_dimension
        n = 0
        while (element_dimension in g['nc'].dimensions or
               element_dimension in g['new_dimensions']):
            n += 1
            element_dimension = '{0}_{1}'.format(base, n)
             
        g['compression'].setdefault(sample_ncdimension, {})['DSG_contiguous'] = {
            'empty_data'            : data,
            'elements_per_instance' : elements_per_instance,
            'implied_ncdimensions'  : (instance_ncdimension,
                                       element_dimension),
            'profile_ncdimension'   : instance_ncdimension,
            'element_dimension'     : element_dimension,
            'element_dimension_size': element_dimension_size,
        }
    
        g['new_dimensions'][element_dimension] = element_dimension_size
        
        if _debug:
            print "    Creating g['compression'][{!r}]['DSG_contiguous']".format(
                sample_ncdimension)
    
        return element_dimension
    #--- End: def
    
    def _read_parse_DSG_indexed_compression(self, ncvar, attributes,
                                            instance_ncdimension):
        '''
        ncvar: `str`
            The netCDF variable name of the DSG index variable.
    
        attributes: `dict`
    
        instance_ncdimension: `str`
            The netCDF variable name of the DSG instance dimension.
    
        '''
        g = self.read_vars
                
        _debug = g['_debug']
        if _debug:
            print '    DSG index variable: instance_dimension =', instance_ncdimension
        
        index = self._read_create_array(ncvar, attributes)
        
        (instance, inverse, count) = numpy.unique(index,
                                                  return_inverse=True,
                                                  return_counts=True)
    
        # The indices of the sample dimension which apply to each
        # instance. For example, if the sample dimension has size 20 and
        # there are 3 instances then the instance_indices arary might look
        # like [1, 0, 2, 2, 1, 0, 2, 1, 0, 0, 2, 1, 2, 2, 1, 0, 0, 0, 2,
        # 0].
        instance_indices = self._read_create_Data(inverse)
    
        # The number of elements per instance. For the instance_indices
        # example, the elements_per_instance array is [7, 5, 7].
        elements_per_instance = self._read_create_Data(array=count)
    
        instance_dimension_size = g['nc'].dimensions[instance_ncdimension].size
        element_dimension_size  = int(elements_per_instance.max())
    
        # Create an empty Data array which has dimensions
        # (instance dimension, element dimension)
        data = self.Data.compression_initialize_indexed(
            instance_dimension_size,
            element_dimension_size,
            instance_indices)
        
        if _debug:        
            print '    DSG indexed array implied shape:', data.shape
    
        # Make up a netCDF dimension name for the element dimension
        featureType = g['global_attributes'].get('featureType')
        if featureType in ('timeSeries', 'trajectory', 'profile'):
            element_dimension = featureType.lower()
        elif featureType == 'timeSeriesProfile':
            element_dimension = 'timeseries'
        elif featureType == 'trajectoryProfile':
            element_dimension = 'trajectory'
        else:
            element_dimension = 'element'
        if _debug:        
            print '    featureType =', featureType
    
        base = element_dimension
        n = 0
        while (element_dimension in g['nc'].dimensions or
               element_dimension in g['new_dimensions']):
            n += 1
            element_dimension = '{0}_{1}'.format(base, n)
            
        indexed_sample_dimension = g['nc'][ncvar].dimensions[0]
        
        g['compression'].setdefault(indexed_sample_dimension, {})['DSG_indexed'] = {
            'empty_data'             : data,
            'elements_per_instance'  : elements_per_instance,
            'instance_indices'       : instance_indices,
            'implied_ncdimensions'   : (instance_ncdimension,
                                        element_dimension),
            'element_dimension'      : element_dimension,
            'instance_dimension_size': instance_dimension_size,
        }
    
        g['new_dimensions'][element_dimension] = element_dimension_size
        
        if _debug:
            print "    Created g['compression'][{!r}]['DSG_indexed']".format(
                indexed_sample_dimension)
    
        return element_dimension
    #--- End: def
    
    def _read_parse_DSG_indexed_contiguous_compression(self, ncvar,
                                                       sample_ncdimension,
                                                       instance_ncdimension):
        '''

:Parameters:
    
    sample_ncdimension: `str`
        The netCDF dimension name of the DSG sample dimension.

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
            print 'Pre-processing DSG indexed and contiguous compression'
    
        profile_ncdimension = g['compression'][sample_ncdimension]['DSG_contiguous']['profile_ncdimension']
    
        if _debug:
            print '    sample_ncdimension  :', sample_ncdimension
            print '    instance_ncdimension:', instance_ncdimension
            print '    profile_ncdimension :', profile_ncdimension
            
        contiguous = g['compression'][sample_ncdimension]['DSG_contiguous']
        indexed    = g['compression'][profile_ncdimension]['DSG_indexed']
    
        # The indices of the sample dimension which define the start
        # positions of each instances profiles
        profile_indices = indexed['instance_indices']
    
        profiles_per_instance = indexed['elements_per_instance']
        elements_per_profile  = contiguous['elements_per_instance']
    
    #    print 'profile_indices =',profile_indices.array, profile_indices.size
    #    print 'elements_per_profile =',elements_per_profile.array,elements_per_profile.size
    #    print 'profiles_per_instance =',profiles_per_instance.array,profiles_per_instance.size
        
        instance_dimension_size  = indexed['instance_dimension_size']
        element_dimension_1_size = int(profiles_per_instance.max())
        element_dimension_2_size = int(elements_per_profile.max())
        
        # Create an empty Data array which has dimensions
        # (instance_dimension, element_dimension_1, element_dimension_2)
        data = self.Data.compression_initialize_indexed_contiguous(
            instance_dimension_size,
            element_dimension_1_size,
            element_dimension_2_size,
            profiles_per_instance,
            elements_per_profile,
            profile_indices)
        
        if _debug:
            print '    DSG indexed and contiguous array implied shape:', data.shape
    
        if _debug:
            print "    Creating g['compression'][{!r}]['DSG_indexed_contiguous']".format(
                sample_ncdimension)
            
        g['compression'][sample_ncdimension]['DSG_indexed_contiguous'] = {
            'empty_data'           : data,
            'profiles_per_instance': profiles_per_instance,
            'elements_per_profile' : elements_per_profile,
            'profile_indices'      : profile_indices,
            'implied_ncdimensions' : (instance_ncdimension,
                                      indexed['element_dimension'],
                                      contiguous['element_dimension'])
        }
    
        if _debug:
            print '    Implied dimensions: {} -> {}'.format(
                sample_ncdimension,
                g['compression'][sample_ncdimension]['DSG_indexed_contiguous']['implied_ncdimensions'])
    
        if _debug:
            print "    Removing g['compression'][{!r}]['DSG_contiguous']".format(
                sample_ncdimension)
            
        del g['compression'][sample_ncdimension]['DSG_contiguous']
    #--- End: def
    
    def _read_formula_terms_variables(self, ncvar, formula_terms,
                                      variables, coord=False, bounds=False):
        '''
    :Parameters:
    
        ncvar: `str`
    
        formula_terms: `str`
            A CF-netCDF formula_terms attribute.
    
        variables: `set`
        '''
        g = self.read_vars
            
        g['formula_terms'].setdefault(ncvar, {'coord' : {},
                                              'bounds': {}})
        
        formula_terms = re.split('\s+|\s*:\s+',formula_terms)
    
        if bounds:
            b = ' bounds'
        else:
            b = ''
            
        for name, term in zip(formula_terms[0::2],
                              formula_terms[1::2]):
            # Skip terms which are in the list but not in the file
            if term not in g['nc'].variables:
                continue
            
            if g['_debug']:
                print '        Has domain ancillary{}: {}'.format(b, term)
    
            if 'domain_ancillary' not in g['field']:
                # Do not promote a domain ancillary to also appear as a
                # top-level field
                variables.discard(term)
            else:
                g['promoted'].append(term)
                
            if bounds and term not in g['formula_terms'][ncvar]['coord'].values():
                # Do not promote a domain ancillary's bounds to also
                # appear as a top-level field
                variables.discard(term)
                g['promoted'].append(term)
    
            if coord:
                g['formula_terms'][ncvar]['coord'][name] = term
            elif bounds:
                g['formula_terms'][ncvar]['bounds'][name] = term
    #--- End: def
    
    def _read_create_Field(self, data_ncvar, attributes,
                           dimension_coordinates,
                           auxiliary_coordinates, cell_measures,
                           domain_ancillaries, field_ancillaries,
                           list_variables, verbose=False):
        '''Create a field for a given netCDF variable.
    
:Parameters:

    filename: `str`
        The name of the netCDF file.

    data_ncvar: `str`
        The name of the netCDF variable to be turned into a field.

    attributes: `dict`
        Dictionary of the data variable's netCDF attributes.

:Returns:

    out: `Field`
        The new field.

        '''
        g = self.read_vars
        nc = g['nc']
        
        _debug = g['_debug']
        if _debug:
            print 'Converting data variable {!r} to a Field:'.format(data_ncvar)
        
        compression = g['compression']
        
        properties = attributes[data_ncvar]
    
        # Add global attributes to the data variable's properties, unless
        # the data variables already has a property with the same name.
        for attr, value in g['global_attributes'].iteritems():
            if attr not in properties:
                properties[attr] = value
    
        # Take cell_methods out of the data variable's properties since it
        # will need special processing once the domain has been defined
        cell_methods = properties.pop('cell_methods', None)
        if cell_methods is not None:
            try:
#                cell_methods = self.CellMethods(cell_methods)
                cell_methods = self.CellMethod.parse(cell_methods)
            except:
                # Something went wrong whilst trying to parse the cell
                # methods string
                properties['nonCF_cell_methods'] = cell_methods
                cell_methods = None
                if verbose:
                    print(
"WARNING: Moving unsupported cell methods to 'nonCF_cell_methods': {0!r}".format(
    cell_methods))
    
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
    
        # Change numpy arrays to tuples for selected attributes
        for attr in ('valid_range',):
            if attr in properties:
                properties[attr] = tuple(properties[attr])
    
        # ----------------------------------------------------------------
        # Initialize the field with the data variable and its attributes
        # ----------------------------------------------------------------
        f_Units = self.Units(properties.pop('units', None),
                             properties.pop('calendar', None))

        if g['verbose'] and not f_Units.isvalid:
            print(
"WARNING: Unsupported units in file {0} on variable {1}: {2}".format(
    g['filename'], data_ncvar, f_Units))

        f = self.Field(properties=properties, copy=False)
    
        f.ncvar = data_ncvar
        f.file  = g['filename']
        f.Units = f_Units
    
        f._global_attributes = tuple(g['global_attributes'])
    
        # Map netCDF dimension dimension names to domain axis names.
        # 
        # For example:
        # >>> ncdim_to_axis
        # {'lat': 'dim0', 'time': 'dim1'}
        ncdim_to_axis = {}
    
        ncscalar_to_axis = {}
    
        ncvar_to_key = {}
            
        f._data_axes = []
    
        # ----------------------------------------------------------------
        # Add axes and non-scalar dimension coordinates to the field
        # ----------------------------------------------------------------
        field_ncdimensions = self._ncdimensions(data_ncvar)
        if _debug:
            print '    Field dimensions:', field_ncdimensions
            
        for ncdim in field_ncdimensions:
            if ncdim in nc.variables:
                
                # There is a Unidata coordinate variable for this dimension, so
                # create the coordinate and the dimension.
                if ncdim in dimension_coordinates:
                    coord = dimension_coordinates[ncdim].copy()
                else:
                    coord = self._read_create_bounded_item(ncdim,
                                                           attributes,
                                                           f,
                                                           dimension=True,
                                                           verbose=verbose)
                    dimension_coordinates[ncdim] = coord
                
                if _debug:
                    print '    Inserting', repr(coord)
    
                axis = self.DomainAxis(coord.size)
                dim = f.insert_axis(axis, copy=False)
                
                dim = f.insert_dim(coord, axes=[dim], copy=False)            
    
                # Record the netCDF dimension name for this axis
                f.axes()[dim].ncdim = ncdim
    
                # Set unlimited status of axis
                if nc.dimensions[ncdim].isunlimited():
                    f.unlimited({dim: True})
    
                ncvar_to_key[ncdim] = dim
            else:
    
                # There is no dimension coordinate for this dimension, so
                # just create a dimension with the correct size.
                if ncdim in g['new_dimensions']:
                    size = g['new_dimensions'][ncdim]
                else:
                    size = len(nc.dimensions[ncdim])
    
                axis = self.DomainAxis(size)
                if _debug:
                    print '    Inserting', repr(axis)
                dim = f.insert_axis(axis)
                # Record the netCDF dimension name for this axis
                f.axes()[dim].ncdim = ncdim
                
                # Set unlimited status of axis
                try:
                    if nc.dimensions[ncdim].isunlimited():
                        f.unlimited({dim: True})
                except KeyError:
                    # This dimension is not in the netCDF file (as might
                    # be the case for an element dimension implied by a
                    # DSG ragged array).
                    pass            
            #--- End: if
    
            # Update data dimension name and set dimension size
            f._data_axes.append(dim)
    
            ncdim_to_axis[ncdim] = dim
        #--- End: for
    
        f._Data = self._set_Data(data_ncvar, f, unpacked_dtype=unpacked_dtype)
        
        # ----------------------------------------------------------------
        # Add scalar dimension coordinates and auxiliary coordinates to
        # the field
        # ----------------------------------------------------------------
        coordinates = f.getprop('coordinates', None)
        if coordinates is not None:
            
            # Split the list (allowing for incorrect comma separated
            # lists).
            for ncvar in re.split('\s+|\s*,\s*', coordinates):
                # Skip dimension coordinates which are in the list
                if ncvar in field_ncdimensions:
                    continue
    
                # Skip auxiliary coordinates which are in the list but not
                # in the file
                if ncvar not in nc.variables:
                    continue
    
                # Set dimensions for this variable 
                dimensions = [ncdim_to_axis[ncdim]
                              for ncdim in self._ncdimensions(ncvar)
                              if ncdim in ncdim_to_axis]
    
                if ncvar in auxiliary_coordinates:
                    coord = auxiliary_coordinates[ncvar].copy()
                else:
                    coord = self._read_create_bounded_item(ncvar,
                                                           attributes,
                                                           f,
                                                           auxiliary=True,
                                                           verbose=verbose)
                    auxiliary_coordinates[ncvar] = coord
                #--- End: if
    
                # --------------------------------------------------------
                # Turn a 
                # --------------------------------------------------------
                is_dimension_coordinate = False
                scalar = False
                if not dimensions:
                    scalar = True
                    if nc.variables[ncvar].dtype.kind is 'S':
                        # String valued scalar coordinate. Is this CF
                        # compliant? Don't worry about it - we'll just
                        # turn it into a 1-d, size 1 auxiliary coordinate
                        # construct.
                        axis = self.DomainAxis(1)
                        dim = f.insert_axis(axis)
                        if _debug:
                            print '    Inserting', repr(axis)

                        # Record the netCDF dimension name for this axis
                        f.axes()[dim].ncdim = ncdim
                        dimensions = [dim]
                    else:  
                        # Numeric valued scalar coordinate
                        is_dimension_coordinate = True
                #--- End: if
    
                if is_dimension_coordinate:
                    # Insert dimension coordinate
                    coord = self.DimensionCoordinate(source=coord, copy=False)
    
                    if _debug:
                        print '    Inserting', repr(coord)
    
                    axis = self.DomainAxis(coord.size)
                    dim = f.insert_axis(axis, copy=False)
                    
                    dim = f.insert_dim(coord, axes=[dim], copy=False)
    
                    # Record the netCDF dimension name for this axis
                    f.axes()[dim].ncdim = ncvar
                    dimensions = [dim]
                    ncvar_to_key[ncvar] = dim
                    dimension_coordinates[ncvar] = coord
                    del auxiliary_coordinates[ncvar]
                else:
                    # Insert auxiliary coordinate
                    if _debug:
                        print '    Inserting', repr(coord)
                    aux = f.insert_aux(coord, axes=dimensions, copy=False)
                    ncvar_to_key[ncvar] = aux
                
                if scalar:
                    ncscalar_to_axis[ncvar] = dimensions[0]
            #--- End: for
    
            f.delprop('coordinates')
        #--- End: if
    
        # ----------------------------------------------------------------
        # Add coordinate references from formula_terms properties
        # ----------------------------------------------------------------
        if data_ncvar not in g['promoted']:
            # Only add coordinate references to metadata variables

            for key, coord in f.items(role=('d', 'a')).iteritems():
                formula_terms = attributes[coord.ncvar].get('formula_terms', None)
                if formula_terms is None:
                    # This coordinate doesn't have a formula_terms attribute
                    continue
        
                for term, ncvar in g['formula_terms'][coord.ncvar]['coord'].iteritems():
                    # Set dimensions 
                    axes = [ncdim_to_axis[ncdim]
                            for ncdim in self._ncdimensions(ncvar)
                            if ncdim in ncdim_to_axis]    
                    
    #                if not axes:
    #                    # Variable is scalar => term is a parameter, not a
    #                    # DomainAncillary
    #                    if ncvar not in coordref_parameters:
    #                        variable = self._read_create_array(ncvar, attributes)
    #                        coordref_parameters[ncvar] = variable
    #                    continue
    #    
    ##                # Still here? Then the term is a DomainAncillary, not a
    #                # parameter.
                    if ncvar in domain_ancillaries:
                        domain_anc = domain_ancillaries[ncvar][1].copy()
                    else:
                        bounds = g['formula_terms'][coord.ncvar]['bounds'].get(term)
                        if bounds == ncvar:
                            bounds = None
        
                        domain_anc = self._read_create_bounded_item(ncvar,
                                                                    attributes,
                                                                    f,
                                                                    domainancillary=True,
                                                                    bounds=bounds,
                                                                    verbose=verbose)
                    #--- End: if
                    
                    # Insert domain ancillary
                    da_key = f.insert_domain_anc(domain_anc, axes=axes, copy=False)
                    if ncvar not in ncvar_to_key:
                        ncvar_to_key[ncvar] = da_key
        
                    domain_ancillaries[ncvar] = (da_key, domain_anc)
                #--- End: for
        
                self._read_create_formula_terms_ref(f, key, coord,
                                                    g['formula_terms'][coord.ncvar]['coord'],
                                                    domain_ancillaries)
            #--- End: for
        #--- End: if
    
        # ----------------------------------------------------------------
        # Add grid mapping coordinate references
        # ----------------------------------------------------------------
        grid_mapping = f.getprop('grid_mapping', None)
        if grid_mapping is not None:
            self._read_create_grid_mapping_ref(f, grid_mapping,
                                               attributes, ncvar_to_key)
    
        # ----------------------------------------------------------------
        # Add cell measures to the field
        # ----------------------------------------------------------------
        measures = f.getprop('cell_measures', None)
        if measures is not None:
    
            # Parse the cell measures attribute
            measures = re.split('\s*(\w+):\s*', measures)
            
            for measure, ncvar in zip(measures[1::2], 
                                      measures[2::2]):
                
                if ncvar not in attributes:
                    continue
    
                # Set cell measures' dimensions 
                cm_ncdimensions = self._ncdimensions(ncvar)
                axes = [ncdim_to_axis[ncdim] for ncdim in cm_ncdimensions]
    
                if ncvar in cell_measures:
                    # Copy the cell measure as it already exists
                    cell = cell_measures[ncvar].copy()
                else:
                    cell = self._read_create_item(ncvar, attributes,
                                                  f, cell_measure=True)
                    cell.measure = measure
                    cell_measures[ncvar] = cell
                #--- End: if
    
                clm = f.insert_measure(cell, axes=axes, copy=False)
    
                ncvar_to_key[ncvar] = clm
            #--- End: for
    
            f.delprop('cell_measures')
        #--- End: if
    
        # ----------------------------------------------------------------
        # Add cell methods to the field
        # ----------------------------------------------------------------
        if cell_methods: # is not None:
            name_to_axis = ncdim_to_axis.copy()
            name_to_axis.update(ncscalar_to_axis)
            for cm in cell_methods:
                cm.axes = tuple([name_to_axis.get(axis, axis) for axis in cm.axes])
                f.insert_cell_method(cm)
#            f.insert_cell_methods(cell_methods)
    
        # ----------------------------------------------------------------
        # Add field ancillaries to the field
        # ----------------------------------------------------------------
        ancillary_variables = f.getprop('ancillary_variables', None)
        if ancillary_variables is not None:
            f.delprop('ancillary_variables')
            # Allow for incorrect comma separated lists
            for ncvar in re.split('\s+|\s*,\s*', ancillary_variables):
                # Skip variables which are in the list but not in the file
                if ncvar not in nc.variables:
                    continue
    
                # Set dimensions 
                anc_ncdimensions = self._ncdimensions(ncvar)
                axes = [ncdim_to_axis[ncdim] for ncdim in anc_ncdimensions
                        if ncdim in ncdim_to_axis]    
                
                if ncvar in field_ancillaries:
                    field_anc = field_ancillaries[ncvar].copy()
                else:
                    field_anc = self._read_create_item(ncvar,
                                                       attributes, f,
                                                       field_ancillary=True)
                    field_ancillaries[ncvar] = field_anc
                    
                # Insert the field ancillary
                key = f.insert_field_anc(field_anc, axes=axes, copy=False)
                ncvar_to_key[ncvar] = key
        #--- End: if
    
        # Return the finished field
        return f
    #--- End: def
    
    def _read_create_bounded_item(self, ncvar, attributes, f,
                                  dimension=False, auxiliary=False,
                                  domainancillary=False, bounds=None,
                                  verbose=False):
        '''Create a variable which might have bounds.
    
    :Parameters:
    
        ncvar: `str`
            The netCDF name of the variable.
    
        attributes: `dict`
            Dictionary of the variable's netCDF attributes.
    
        f: `Field`
    
        dimension: `bool`, optional
            If True then a dimension coordinate is created.
    
        auxiliary: `bool`, optional
            If True then an auxiliary coordinate is created.
    
        domainancillary: `bool`, optional
            If True then a domain ancillary is created.
    
    :Returns:
    
        out : `DimensionCoordinate` or `AuxiliaryCoordinate` or `DomainAncillary`
            The new item.
    
        '''
        g = self.read_vars
        nc = g['nc']
        
        properties = attributes[ncvar].copy()
      
        c_Units = self.Units(properties.pop('units', None),
                             properties.pop('calendar', None))
    
        if g['verbose'] and not c_Units.isvalid:
            print(
"WARNING: Unsupported units in file {0} on variable {1}: {2}".format(
    g['filename'], ncvar, c_Units))

        properties.pop('formula_terms', None)
    
        if bounds is not None:
            properties['bounds'] = bounds
    
        ncbounds = properties.pop('bounds', None)
        if ncbounds is None:
            ncbounds = properties.pop('climatology', None)
            climatology = True
        else:
            climatology = False
    
        if dimension:
            c = self.DimensionCoordinate(properties=properties)
        elif auxiliary:
            c = self.AuxiliaryCoordinate(properties=properties)
        elif domainancillary:
            properties.pop('coordinates', None)
            properties.pop('grid_mapping', None)
            properties.pop('cell_measures', None)
    
            properties.pop('formula_terms', None)
            properties.pop('positive', None)
    
            c = self.DomainAncillary(properties=properties)
        else:
            raise ValueError(
"Must set one of the dimension, auxiliary or domainancillary parmaeters to True")
    
        c.ncvar = ncvar
        c.Units = c_Units
    
        if climatology:
            c.climatology = climatology
    
        data = self._set_Data(ncvar, c)
    
        # ------------------------------------------------------------
        # Add any bounds
        # ------------------------------------------------------------
        if ncbounds is None:
            bounds = None
        else:
            properties = attributes[ncbounds].copy()
            properties.pop('formula_terms', None)
    
            b_Units = self.Units(properties.pop('units', None),
                                 properties.pop('calendar', None))
    
            if g['verbose'] and not b_Units.isvalid:
                print(
"WARNING: Unsupported units in file {0} on variable {1}: {2}".format(
    g['filename'], ncbounds, b_Units))

            bounds = self.Bounds(properties=properties, copy=False)
    
            if not b_Units:
                b_Units = c_Units
    
            bounds.Units = b_Units
            
            bounds.ncvar = ncbounds
    
            bounds_data = self._set_Data(ncbounds, bounds)
    
            bounds.insert_data(bounds_data, copy=False)
    
    #        if b_Units != c_Units:
    #            if b_Units.equivalent(c_Units):
    #                bounds.Units = c_Units
    #            else:
    #                bounds.override_units(c_Units, copy=False)
    #                print(
    #"WARNING: Overriding {0!r} bounds units from {1!r} to {2!r}".format(
    #    ncbounds, b_Units, c_Units))
    #        #--- End: if
            
            # Make sure that the bounds dimensions are in the same order
            # as its parent's dimensions
            c_ncdims = nc.variables[ncvar].dimensions
            b_ncdims = nc.variables[ncbounds].dimensions
            if c_ncdims != b_ncdims[:-1]:
                axes = [c_ncdims.index(ncdim) for ncdim in b_ncdims[:-1]]
                axes.append(-1)
                bounds.transpose(axes, copy=False)
        #--- End: if
    
        c.insert_data(data, bounds=bounds, copy=False)
    
        # ---------------------------------------------------------
        # Return the bounded variable
        # ---------------------------------------------------------
        return c
    #--- End: def
    
    def _read_create_array(self, ncvar, attributes):
        '''Create
    
:Parameters:

    ncvar: `str`
        The netCDF variable name.

    attributes: `dict`
        Dictionary of the netCDF variable's attributes.

:Returns:
    
    out: `Data`

        '''
        properties = attributes[ncvar]
    
        units = self.Units(properties.get('units'),
                           properties.get('calendar'))
    
        if self.read_vars['verbose'] and not units.isvalid:
            print(
"WARNING: Unsupported units in file {0} on variable {1}: {2}".format(
    self.read_vars['filename'], ncvar, units))

        data = self._set_Data(ncvar, units=units)
    
        return data
    #--- End: def
    
    def _read_create_item(self, ncvar, attributes, f,
                          cell_measure=False, field_ancillary=False):
        '''Create a cell measure or field ancillary object.
    
:Parameters:
    
    nc : netCDF4.Dataset
        The entire netCDF file in a `netCDF4.Dataset` instance.

    ncvar : str
        The netCDF name of the cell measure variable.

    attributes : dict
        Dictionary of the cell measure variable's netCDF attributes.

    f: `Field`

:Returns:

    out: `CellMeasure`
        The new cell measure.

        '''
        g = self.read_vars
                
        if cell_measure:
            clm = self.CellMeasure(properties=attributes[ncvar])
        elif field_ancillary:
            clm = self.FieldAncillary(properties=attributes[ncvar])
    
        data = self._set_Data(ncvar, clm)
    
        clm.insert_data(data, copy=False)
    
        clm.ncvar = ncvar
    
        return clm
    #--- End: def
    
    def _ncdimensions(self, ncvar):
        '''Return a list of the netCDF dimensions corresponding to a netCDF
    variable.
    
:Parameters:

    ncvar: `str`
        The netCDF variable name.

:Returns:

    out: `list`
        The list of netCDF dimension names spanned by the netCDF
        variable.

:Examples: 

>>> _ncdimensions('humidity')
['time', 'lat', 'lon']
    
        '''
        g = self.read_vars
                
        ncvariable = g['nc'].variables[ncvar]
    
        ncattrs = ncvariable.ncattrs()
    
        ncdimensions = list(ncvariable.dimensions)
          
        # Remove a string-length dimension, if there is one. DCH ALERT
        if (ncvariable.dtype.kind == 'S' and
            ncvariable.ndim >= 2 and ncvariable.shape[-1] > 1):
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
                    elif 'DSG_indexed_contiguous' in c:
                        # DSG indexed contiguous ragged array.
                        #
                        # Check this before DSG_indexed and DSG_contiguous
                        # because both of these will exist for an array
                        # that is both indexed and contiguous.
                        i = ncdimensions.index(ncdim)
                        ncdimensions = c['DSG_indexed_contiguous']['implied_ncdimensions']
                    elif 'DSG_contiguous' in c:
                        # DSG contiguous ragged array
                        ncdimensions = c['DSG_contiguous']['implied_ncdimensions']
                    elif 'DSG_indexed' in c:
                        # DSG indexed ragged array
                        ncdimensions = c['DSG_indexed']['implied_ncdimensions']
    
                    break
        #--- End: if
        
        return map(str, ncdimensions)
    #--- End: def
    
    def _read_create_grid_mapping_ref(self, f, grid_mapping,
                                      attributes, ncvar_to_key):
        '''
    
:Parameters:

    f: `Field`

    grid_mapping : str

    attributes : dict

    ncvar_to_key : dict

:Returns:

    None

        '''
        g = self.read_vars
                
        if ':' not in grid_mapping:
            grid_mapping = '{0}:'.format(grid_mapping)

        coordinates = []
        for x in re.sub('\s*:\s*', ': ', grid_mapping).split()[::-1]:
            if not x.endswith(':'):
                try:
                    coordinates.append(ncvar_to_key[x])
                except KeyError:
                    continue
            else:
                if not coordinates:
                    coordinates = None
    
                grid_mapping = x[:-1]
    
                if grid_mapping not in attributes:
                    coordinates = []      
                    continue
                    
                    
                parameter_terms = attributes[grid_mapping].copy()
                
                name = parameter_terms.pop('grid_mapping_name', None)                 
      
                coordref = self.CoordinateReference(name,
                                                    crtype='grid_mapping',
                                                    coordinates=coordinates,
                                                    parameters=parameter_terms)
                coordref.ncvar = grid_mapping
    
                f.insert_ref(coordref, copy=False)
    
                coordinates = []      
        #--- End: for
    
        f.delprop('grid_mapping')
    #--- End: def
    
    def _read_create_formula_terms_ref(self, f, key, coord,
                                       formula_terms, domain_ancillaries):
        '''
    
    :Parameters:
    
        f: `Field`
    
        key: `str`
    
        coord: `Coordinate`
    
        formula_terms: `dict`
            The formula_terms attribute value from the netCDF file.
    
        domain_ancillaries: `dict`
    
#        coordref_parameters: `dict`
    
    :Returns:
    
        out: `CoordinateReference`
    
    '''
        g = self.read_vars

        parameters  = {}
        ancillaries = {}
    
        for term, ncvar in formula_terms.iteritems():
#            if ncvar in domain_ancillaries:

            # The term's value is a domain ancillary of the field, so
            # we put its identifier into the coordinate reference.
            ancillaries[term] = domain_ancillaries[ncvar][0]

#            elif ncvar in coordref_parameters:
#                # The term's value is a parameter
#                parameters[term] = coordref_parameters[ncvar].copy()
#        #--- End: for 
    
        coordref = self.CoordinateReference(name=coord.getprop('standard_name', None),
                                            crtype='formula_terms',
                                            coordinates=(key,),
                                            ancillaries=ancillaries)
    
        f.insert_ref(coordref, copy=False)
    
        return coordref
    #--- End: def
    
    def _set_Data(self, ncvar, variable=None, unpacked_dtype=False,
                  uncompress_override=None, units=None,
                  fill_value=None):
        '''
    
    Set the Data attribute of a variable.
    
    :Parameters:
    
        ncvar: `str`
    
        variable: `Variable`, optional
    
        unpacked_dtype: `False` or `numpy.dtype`, optional
    
        g: `dict`
    
    :Returns:
    
        out: `Data`
    
    :Examples: 
    
    '''
        g = self.read_vars

        nc = g['nc']
        
        ncvariable = nc.variables[ncvar]
    
        dtype = ncvariable.dtype
        if unpacked_dtype is not False:
            dtype = numpy.result_type(dtype, unpacked_dtype)
    
        ndim  = ncvariable.ndim
        shape = ncvariable.shape
        size  = ncvariable.size
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
    
        filearray = self.NetCDFArray(file=g['filename'],
                                     ncvar=ncvar,
                                     dtype=dtype,
                                     ndim=ndim,
                                     shape=shape,
                                     size=size)
    
        # Find the units for the data
        if units is None and variable is not None:
            units = variable.Units
            
        # Find the fill_value for the data
        if fill_value is None and variable is not None:
            fill_value = variable.fill_value()
            
        compression = g['compression']
    
        if ((uncompress_override is not None and not uncompress_override) or
            not g['compression'] or 
            not g['uncompress'] or
            not set(compression).intersection(ncvariable.dimensions)):        
            # --------------------------------------------------------
            # The array is not compressed
            # --------------------------------------------------------
            data = self._read_create_Data(filearray, units=units,
                                          fill_value=fill_value)
            
        else:
            # --------------------------------------------------------
            # The array is compressed
            # --------------------------------------------------------
            # Loop round the data variables dimensions as they are in
            # the netCDF file
            for ncdim in ncvariable.dimensions:
                if ncdim in compression:
                    c = compression[ncdim]
                    if 'gathered' in c:
                        # Create an empty Data array which has dimensions
                        # uncompressed_shape  
                        ncdims = self._ncdimensions(ncvar)
                        uncompressed_shape = tuple([nc[dim].size for dim in ncdims])
    
                        empty_data = self.Data.compression_initialize_gathered(uncompressed_shape)
    
                        # The position of the compressed axis in the
                        # gathered array
    
                        sample_axis = ncvariable.dimensions.index(ncdim)
    
                        # The uncompression indices
                        indices = c['gathered']['indices']
    
    #                    data = data.array.GatheredArray(uncompressed_shape=uncompressed_shape, 
    #                                                             dtype=dtype,
    #                                                             gathered_array=filearray,
    #                                                             sample_axis=sample_axis, 
    #                                                             indices=indices)
    
                        data = self.Data.compression_fill_gathered(empty_data,
                                                                   dtype,
                                                                   units,
                                                                   fill_value,
                                                                   filearray,
                                                                   sample_axis,
                                                                   indices)
    
                    elif 'DSG_indexed_contiguous' in c:
                        # DSG contiguous indexed ragged array. Check
                        # this before DSG_indexed and DSG_contiguous
                        # because both of these will exist for an
                        # indexed and contiguous array.
                        empty_data            = c['DSG_indexed_contiguous']['empty_data'].copy()
                        profiles_per_instance = c['DSG_indexed_contiguous']['profiles_per_instance']
                        elements_per_profile  = c['DSG_indexed_contiguous']['elements_per_profile']
                        profile_indices       = c['DSG_indexed_contiguous']['profile_indices']
    
                        data = self.Data.compression_fill_indexed_contiguous(
                            empty_data,
                            dtype,
                            units,
                            fill_value,
                            filearray,
                            profiles_per_instance,
                            elements_per_profile,
                            profile_indices)
                        
                    elif 'DSG_contiguous' in c:                    
                        # DSG contiguous ragged array
                        empty_data            = c['DSG_contiguous']['empty_data'].copy()
                        elements_per_instance = c['DSG_contiguous']['elements_per_instance']
                                            
                        data = self.Data.compression_fill_contiguous(
                            empty_data,
                            dtype,
                            units,
                            fill_value,
                            filearray,
                            elements_per_instance)
                        
                    elif 'DSG_indexed' in c:
                        # DSG indexed ragged array
                        empty_data       = c['DSG_indexed']['empty_data'].copy()
                        instance_indices = c['DSG_indexed']['instance_indices']
                        
                        data = self.Data.compression_fill_indexed(
                            empty_data,
                            dtype,
                            units,
                            fill_value,
                            filearray,
                            instance_indices)
                            
                    else:
                        raise ValueError("Bad compression vibes. c.keys()={}".format(c.keys()))
        #--- End: if
            
        return data
    #--- End: def

    def _read_create_Data(self, array=None, units=None, fill_value=None):
        '''
        '''    
        return self.Data(array, units=units, fill_value=fill_value)        
    #--- End: def
    
    @classmethod    
    def is_netcdf_file(cls, filename):
        '''Return True if the file is a netCDF file.
    
    Note that the file type is determined by inspecting the file's
    contents and any file suffix is not not considered.
    
    :Parameters:
    
        filename : str
    
    :Returns:
    
        out : bool
    
    :Examples:
    
    >>> is_netcdf_file('myfile.nc')
    True
    >>> is_netcdf_file('myfile.pp')
    False
    >>> is_netcdf_file('myfile.pdf')
    False
    >>> is_netcdf_file('myfile.txt')
    False
    
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

    def write(self, fields, filename, fmt='NETCDF4', overwrite=True,
              verbose=False, mode='w', least_significant_digit=None,
              endian='native', compress=0, fletcher32=False,
              no_shuffle=False, datatype=None,
              variable_attributes=None, HDF_chunks=None,
              unlimited=None, _debug=False):
        '''Write fields to a CF-netCDF file.
        
NetCDF dimension and variable names will be taken from variables'
`!ncvar` attributes and the field attribute `!ncdimensions` if
present, otherwise they are inferred from standard names or set to
defaults. NetCDF names may be automatically given a numerical suffix
to avoid duplication.
    
Output netCDF file global properties are those which occur in the set
of CF global properties and non-standard data variable properties and
which have equal values across all input fields.
    
Logically identical field components are only written to the file
once, apart from when they need to fulfil both dimension coordinate
and auxiliary coordinate roles for different data variables.
    
:Parameters:

    fields : (arbitrarily nested sequence of) `cf.Field`
        The field or fields to write to the file.

    filename : str
        The output CF-netCDF file. Various type of expansion are
        applied to the file names:
        
          ====================  ======================================
          Expansion             Description
          ====================  ======================================
          Tilde                 An initial component of ``~`` or
                                ``~user`` is replaced by that *user*'s
                                home directory.
           
          Environment variable  Substrings of the form ``$name`` or
                                ``${name}`` are replaced by the value
                                of environment variable *name*.
          ====================  ======================================
    
        Where more than one type of expansion is used in the same
        string, they are applied in the order given in the above
        table.

          Example: If the environment variable *MYSELF* has been set
          to the "david", then ``'~$MYSELF/out.nc'`` is equivalent to
          ``'~david/out.nc'``.
  
    fmt : str, optional
        The format of the output file. One of:

           =====================  ================================================
           fmt                    Description
           =====================  ================================================
           ``'NETCDF3_CLASSIC'``  Output to a CF-netCDF3 classic format file
           ``'NETCDF3_64BIT'``    Output to a CF-netCDF3 64-bit offset format file
           ``'NETCDF4_CLASSIC'``  Output to a CF-netCDF4 classic format file
           ``'NETCDF4'``          Output to a CF-netCDF4 format file
           =====================  ================================================

        By default the *fmt* is ``'NETCDF3_CLASSIC'``. Note that the
        netCDF3 formats may be slower than any of the other options.

    overwrite: bool, optional
        If False then raise an exception if the output file
        pre-exists. By default a pre-existing output file is over
        written.

    verbose : bool, optional
        If True then print one-line summaries of each field written.

    mode : str, optional
        Specify the mode of write access for the output file. One of:
 
           =======  ==================================================
           mode     Description
           =======  ==================================================
           ``'w'``  Create the file. If it already exists and
                    *overwrite* is True then the file is deleted prior
                    to being recreated.
           =======  ==================================================
       
        By default the file is opened with write access mode ``'w'``.
    
    datatype : dict, optional
        Specify data type conversions to be applied prior to writing
        data to disk. Arrays with data types which are not specified
        remain unchanged. By default, array data types are preserved
        with the exception of booleans (``numpy.dtype(bool)``, which
        are converted to 32 bit integers.

          **Example:**
            To convert 64 bit floats and integers to their 32 bit
            counterparts: ``dtype={numpy.dtype(float):
            numpy.dtype('float32'), numpy.dtype(int):
            numpy.dtype('int32')}``.

:Returns:

    `None`

:Examples 2:

>>> f
[<CF Field: air_pressure(30, 24)>,
 <CF Field: u_compnt_of_wind(19, 29, 24)>,
 <CF Field: v_compnt_of_wind(19, 29, 24)>,
 <CF Field: potential_temperature(19, 30, 24)>]
>>> write(f, 'file')

>>> type(f)
<class 'cf.field.FieldList'>
>>> type(g)
<class 'cf.field.Field'>
>>> cf.write([f, g], 'file.nc', verbose=True)
[<CF Field: air_pressure(30, 24)>,
 <CF Field: u_compnt_of_wind(19, 29, 24)>,
 <CF Field: v_compnt_of_wind(19, 29, 24)>,
 <CF Field: potential_temperature(19, 30, 24)>]
        '''    
        if _debug:
            print 'Writing to netCDF:'

        # ------------------------------------------------------------
        # Initialize dictionary of useful global variables
        # ------------------------------------------------------------
        self.write_vars = copy.deepcopy(self._write_vars)
        g = self.write_vars

        compress = int(compress)
        zlib = bool(compress) 
    
        if fmt not in ('NETCDF3_CLASSIC', 'NETCDF3_64BIT',
                       'NETCDF4', 'NETCDF4_CLASSIC'):
            raise ValueError("Unknown output file format: {}".format(fmt))
    
        if compress and fmt in ('NETCDF3_CLASSIC', 'NETCDF3_64BIT'):
            raise ValueError("Can't compress {} format file".format(fmt))
        
        # ------------------------------------------------------------
        # Set up non-global attributes
        # ------------------------------------------------------------
        if variable_attributes:
            if isinstance(variable_attributes, basestring):
                variable_attributes = set((variable_attributes,))
            else:
                variable_attributes = set(variable_attributes)

            g['variable_attributes'] = variable_attributes
        #--- End: def
    
        # ------------------------------------------------------------
        # Set up data type conversions. By default, booleans are
        # converted to 32-bit integers and python objects are
        # converted to 64-bit floats.
        # ------------------------------------------------------------
        dtype_conversions = {numpy.dtype(bool)  : numpy.dtype('int32'),
                             numpy.dtype(object): numpy.dtype(float)}
        if datatype:
            g['dtype_conversions'].update(datatype)

        if unlimited:
            g['unlimited'] = unlimited
    
        # -------------------------------------------------------
        # Compression/endian
        # -------------------------------------------------------
        g['compression'].update(
            {'zlib'       : zlib,
             'complevel'  : compress,
             'fletcher32' : fletcher32,
             'shuffle'    : not no_shuffle,
            })
        g['endian'] = endian
        g['least_significant_digit'] = least_significant_digit
        
        g['verbose'] = verbose
        g['_debug']  = _debug        
        
        g['fmt'] = fmt
    
        # ---------------------------------------------------------------
        # Flatten the sequence of intput fields
        # ---------------------------------------------------------------
        fields = list(flat(fields))
    
        # ---------------------------------------------------------------
        # Still here? Open the output netCDF file.
        # ---------------------------------------------------------------
    #    if mode != 'w':
    #        raise ValueError("Can only set mode='w' at the moment")
    
        filename = os.path.expanduser(os.path.expandvars(filename))
    
        if mode == 'w' and os.path.isfile(filename):
            if not overwrite:
                raise IOError(
                    "Can't write to an existing file unless overwrite=True: {}".format(
                        abspath(filename)))
                    
            if not os.access(filename, os.W_OK):
                raise IOError(
                    "Can't overwrite an existing file without permission: {}".format(
                        abspath(filename)))
                
            os.remove(filename)
        #--- End: if          

        # ------------------------------------------------------------
        # Open the netCDF file to be written
        # ------------------------------------------------------------
        g['netcdf'] = self.NetCDFArray.file_open(filename, mode, fmt)
    
        # ---------------------------------------------------------------
        # Set the fill mode for a Dataset open for writing to off. This
        # will prevent the data from being pre-filled with fill values,
        # which may result in some performance improvements.
        # ---------------------------------------------------------------
        g['netcdf'].set_fill_off()
    
        # ---------------------------------------------------------------
        # Write global properties to the file first. This is important as
        # doing it later could slow things down enormously. This function
        # also creates the g['global_properties'] set, which is used in
        # the _write_a_field function.
        # ---------------------------------------------------------------
        self._write_global_properties(fields)
    
        # ---------------------------------------------------------------
        # ---------------------------------------------------------------
        for f in fields:
    
    #        # Set HDF chunking
    #        chunks = f.HDF_chunks()
    #        if chunks
    #        
    #        org_chunks = f.HDF_chunks(HDF_chunks)
    #        default_chunks = f.HDF_chunks()
    #        chunks = org_chunks.copy()
    #        shape = f.shape
    #        for i, size in org_chunks.iteritems():
    #            if size is None:
    #                size = default_chunks[i]
    #            dim_size = shape[i]
    #            if size is None or size > dim_size:
    #                size = dim_size
    #            chunks[i] = size
    #        #--- End: for
    #        f.HDF_chunks(chunks)
    
            if g['_debug']:            
                print '  Field shape:', f.shape
                print '  HDF chunks :', f.HDF_chunks()
            
            # Write the field
            self._write_a_field(f)
    
    #        # Reset HDF chunking
    #        f.HDF_chunks(org_chunks)
        #-- End: for
    
        # ---------------------------------------------------------------
        # Write all of the buffered data to disk
        # ---------------------------------------------------------------
        self.NetCDFArray.file_close(filename)
    #--- End: def
    
    def _write_check_name(self, base, dimsize=None):
        '''
    
    :Parameters:
    
        base: `str`
    
        g: `dict`
    
        dimsize: `int`, optional
    
    :Returns:
    
        ncvar: `str`
            NetCDF dimension name or netCDF variable name.
    
        '''
        g = self.write_vars

        ncvar_names = g['ncvar_names']
    
        if dimsize is not None:
            if base in ncvar_names and dimsize == g['ncdim_to_size'][base]:
                # Return the name of an existing netCDF dimension with
                # this size
                return base
        #--- End: if
    
        if base in ncvar_names:
    
            counter = g.setdefault('count_'+base, 1)
        
            ncvar = '{0}_{1}'.format(base, counter)
            while ncvar in ncvar_names:
                counter += 1
                ncvar = '{0}_{1}'.format(base, counter)
        else:
            ncvar = base
    
        ncvar_names.add(ncvar)
    
        return ncvar
    #--- End: def
    
    def _write_attributes(self, ncvar, netcdf_attrs):
        '''
    
    :Parameters:
    
        ncvar: `str`
    
        netcdf_attrs : dict
    
    :Returns:
    
        None
    
    :Examples:
    
    
        '''
        netcdf_var = self.write_vars['nc'][ncvar]

        if hasattr(netcdf_var, 'setncatts'):
            # Use the faster setncatts
            netcdf_var.setncatts(netcdf_attrs)
        else:
            # Otherwise use the slower setncattr
            for attr, value in netcdf_attrs.iteritems():
                netcdf_var.setncattr(attr, value)
    #--- End: def
    
    def _write_character_array(self, array):
        '''Convert a numpy string array to a numpy character array wih an
extra trailing dimension.
    
:Parameters:

    array: `numpy.ndarray`

:Returns:

    out: `numpy.ndarray`

:Examples:

>>> print a, a.shape, a.dtype.itemsize
['fu' 'bar'] (2,) 3
>>> b = _character_array(a)
>>> print b, b.shape, b.dtype.itemsize
[['f' 'u' ' ']
 ['b' 'a' 'r']] (2, 3) 1

>>> print a, a.shape, a.dtype.itemsize
[-- 'bar'] (2,) 3
>>> b = _character_array(a)
>>> print b, b.shape, b.dtype.itemsize
[[-- -- --]
 ['b' 'a' 'r']] (2, 3) 1

        '''
        strlen = array.dtype.itemsize
        shape  = array.shape

        new = numpy.ma.masked_all(shape + (strlen,), dtype='S1')
        
        for index in numpy.ndindex(shape):
            value = array[index]
            if value is numpy.ma.masked:
                new[index] = numpy.ma.masked
            else:
                new[index] = tuple(value.ljust(strlen, ' ')) 
        #--- End: for
    
        return new
    #--- End: def
    
    def _write_datatype(self, variable):
        '''Return the netCDF4.createVariable datatype corresponding to the
datatype of the array of the input variable
    
For example, if variable.dtype is 'float32', then 'f4' will be
returned.
    
Numpy string data types will return 'S1' regardless of the numpy
string length. This means that the required conversion of
multi-character datatype numpy arrays into single-character datatype
numpy arrays (with an extra trailing dimension) is expected to be done
elsewhere (currently in the _write_create_netcdf_variable method).
    
If the input variable has no `!dtype` attribute (or it is None) then
'S1' is returned.
    
 :Parameters:
 
     variable: 
         Any object with a `!dtype` attribute whose value is a
         `numpy.dtype` object or `None`.
 
 :Returns:
 
     out: `str`
        The `netCDF4.createVariable` data type corresponding to the
        datatype of the array of the input variable.

        '''
        g = self.write_vars

        if not hasattr(variable, 'dtype'):
            dtype = numpy.asanyarray(variable).dtype
        elif (variable.dtype.char == 'S' or variable.dtype is None):
            return 'S1'            
    
        dtype = variable.dtype
    
        convert_dtype = g['datatype']
    
        new_dtype = convert_dtype.get(dtype, None)
        if new_dtype is not None:
            dtype = new_dtype
            
        return '{0}{1}'.format(dtype.kind, dtype.itemsize)
    #--- End: def
    
    def _write_string_length_dimension(self, size):
        '''Create, if necessary, a netCDF dimension for string variables.
    
:Parameters:

    size: `int`

:Returns:

    out: `str`
        The netCDF dimension name.

        '''
        g = self.write_vars

        # ----------------------------------------------------------------
        # Create a new dimension for the maximum string length
        # ----------------------------------------------------------------
        ncdim = self._write_check_name('strlen{0}'.format(size), dimsize=size)
        
        if ncdim not in g['ncdim_to_size']:
            # This string length dimension needs creating
            g['ncdim_to_size'][ncdim] = size
            g['netcdf'].createDimension(ncdim, size)
        #--- End: if
    
        return ncdim
    #--- End: def
    
    def _write_grid_ncdimensions(self, f, key, axis_to_ncdim):
        '''Return a tuple of the netCDF dimension names for the axes of a
coordinate or cell measures objects.
    
:Parameters:

    f : `Field`

    key : str

    axis_to_ncdim : dict
        Mapping of field axis identifiers to netCDF dimension names.

    g : dict

:Returns:

    out : tuple
        A tuple of the netCDF dimension names.

        '''
        g = self.write_vars
                
    #    if f.item(key).ndim == 0:
    #        return ()
    #    else:
        return tuple([axis_to_ncdim[axis] for axis in f.item_axes(key)])
    #--- End: def
        
    def _write_create_netcdf_variable_name(self, variable, default):
        '''
        
    :Returns:
    
        variable : `Variable` or `CoordinateReference`
           
        default : str
    
        g : dict
    
    '''
        g = self.write_vars

        ncvar = getattr(variable, 'ncvar', variable.identity(default=default))    
        return self._write_check_name(ncvar)
    #--- End: def
    
    def _data_ncvar(self, ncvar):
        '''
        
    :Parmaeters:
    
        data: `Data`
           
        ncvar: `str`
    
        g: `dict`
    
        '''
        g = self.write_vars

        return self._write_check_name(ncvar, None)
    #--- End: def
    
    def _write_dimension(self, ncdim, f, axis, axis_to_ncdim, unlimited=False):
        '''Write a dimension to the netCDF file.
    
    .. note:: This function updates ``axis_to_ncdim``, ``g['ncdim_to_size']``.
    
    :Parameters:
    
        ncdim: `str`
            The netCDF dimension name.
    
        f: `Field`
       
        axis: `str`
            The field's axis identifier.
    
        axis_to_ncdim: `dict`
            Mapping of field axis identifiers to netCDF dimension names.
    
        unlimited: `bool`, optional
            If true then create an unlimited dimension. By default
            dimensions are not unlimited.
    
        g: `dict`
    
    :Returns:
    
        `None`
    
        '''
        g = self.write_vars
                
        size = f.axis_size(axis)
    
        g['ncdim_to_size'][ncdim] = size
        axis_to_ncdim[axis] = ncdim
    
        if unlimited:
            # Create an unlimited dimension
            try:
                g['netcdf'].createDimension(ncdim, None)
            except RuntimeError as error:
    
                message = "Can't create unlimited dimension in {} file ({}).".format(
                    g['netcdf'].file_format, error)
    
                error = str(error)
                if error == 'NetCDF: NC_UNLIMITED size already in use':
                    raise RuntimeError(
    message+" Only one unlimited dimension allowed. Consider using a netCDF4 format.")
                    
                raise RuntimeError(message)
        else:
            try:
                g['netcdf'].createDimension(ncdim, size)
            except RuntimeError as error:
                raise RuntimeError(
    "Can't create dimension of size {} in {} file ({})".format(
        size, g['netcdf'].file_format, error))
    #--- End: def
    
#    def _change_reference_datetime(self, coord):
#        '''
#    
#    :Parameters:
#    
#        coord : `Coordinate`
#    
#        g : dict
#    
#    :Returns:
#    
#        out : `Coordinate`
#    
#    '''
#        g = self.write_vars
#
#        if not coord.Units.isreftime:
#            return coord
#    
#        reference_datetime = g['reference_datetime']
#        if not reference_datetime:
#            return coord
#    
#        coord2 = coord.copy()
#        try:
#            coord2.reference_datetime = reference_datetime
#        except ValueError:
#            raise ValueError(
#    "Can't override coordinate reference date-time {!r} with {!r}".format(
#        coord.reference_datetime, reference_datetime))
#    
#        return coord2
#    #--- End: def
    
    def _write_dimension_coordinate(self, f, axis, coord,
                                    key_to_ncvar, axis_to_ncdim):
        '''Write a dimension coordinate and its bounds to the netCDF file.
    
This also writes a new netCDF dimension to the file and, if required,
a new netCDF bounds dimension.

.. note:: This function updates ``axis_to_ndim``, ``g['seen']``.

:Parameters:

    f: `Field`
   
    axis: `str`

    coord: `DimensionCoordinate`

    key_to_ncvar: `dict`
        Mapping of field item identifiers to netCDF dimension names.

    axis_to_ncdim: `dict`
        Mapping of field axis identifiers to netCDF dimension names.

:Returns:

    out : str
        The netCDF name of the dimension coordinate.

    '''       
        g = self.write_vars

        seen = g['seen']
    
#        coord = self._change_reference_datetime(coord)
    
        create = False
        if not self._seen(coord):
            create = True
        elif seen[id(coord)]['ncdims'] != ():
            if seen[id(coord)]['ncvar'] != seen[id(coord)]['ncdims'][0]:
                # Already seen this coordinate but it was an auxiliary
                # coordinate, so it needs to be created as a dimension
                # coordinate.
                create = True
        #--- End: if
    
        if create:
            ncdim = self._write_create_netcdf_variable_name(coord,
                                               default='coordinate')
    
            # Create a new dimension, if it is not a scalar coordinate
            if coord.ndim > 0:
                unlimited = self._unlimited(f, axis)
                self._write_dimension(ncdim, f, axis, axis_to_ncdim,
                                      unlimited=unlimited)
    
            ncdimensions = self._write_grid_ncdimensions(f, axis,
                                                         axis_to_ncdim)
            
            # If this dimension coordinate has bounds then create the
            # bounds netCDF variable and add the bounds or climatology
            # attribute to a dictionary of extra attributes
            extra = self._write_bounds(coord, ncdimensions, ncdim)
    
            # Create a new dimension coordinate variable
            self._write_create_netcdf_variable(ncdim, ncdimensions,
                                               coord, extra=extra)
        else:
            ncdim = seen[id(coord)]['ncvar']
    
        key_to_ncvar[axis] = ncdim
    
    #    try:    ### ????? why not always do this dch??
        axis_to_ncdim[axis] = ncdim
    #    except KeyError:
    #        pass
    
        return ncdim
    #--- End: def
    
    def _write_scalar_data(self, value, ncvar):
        '''Write a dimension coordinate and bounds to the netCDF file.
    
    This also writes a new netCDF dimension to the file and, if required,
    a new netCDF bounds dimension.
    
    .. note:: This function updates ``g['seen']``.
    
    :Parameters:
    
        data: `Data`
       
        ncvar: `str`
    
        g: `dict`
    
    :Returns:
    
        out: `str`
            The netCDF name of the scalar data variable
    
        '''
        g = self.write_vars

        seen = g['seen']
    
        create = not self._seen(value, ncdims=())
    
        if create:
            ncvar = self._write_check_name(ncvar) # DCH ?
            
            # Create a new dimension coordinate variable
            self._write_create_netcdf_variable(ncvar, (), value)
        else:
            ncvar = seen[id(value)]['ncvar']
    
        return ncvar
    #--- End: def
    
    def _seen(self, variable, ncdims=None):
        '''Return True if a variable is logically equal any variable in the
g['seen'] dictionary.
    
If this is the case then the variable has already been written to the
output netCDF file and so we don't need to do it again.
    
If 'ncdims' is set then a extra condition for equality is applied,
namely that of 'ncdims' being equal to the netCDF dimensions (names
and order) to that of a variable in the g['seen'] dictionary.
    
When True is returned, the input variable is added to the g['seen']
dictionary.
    
    .. note:: This function updates ``g['seen']``.
    
    :Parameters:
    
        variable : 
    
        ncdims : tuple, optional
    
        g : dict
    
    :Returns:
    
        out : bool
            True if the variable has already been written to the file,
            False otherwise.

        '''
        g = self.write_vars

        seen = g['seen']
    
        ignore_type = getattr(variable, 'isdomainancillary', False) # other types, too?
        
        for value in seen.itervalues():
            if ncdims is not None and ncdims != value['ncdims']:
                # The netCDF dimensions (names and order) of the input
                # variable are different to those of this variable in
                # the 'seen' dictionary
                continue
    
            # Still here?
            if variable.equals(value['variable'], ignore_type=ignore_type):
                seen[id(variable)] = {'variable': variable,
                                      'ncvar'   : value['ncvar'],
                                      'ncdims'  : value['ncdims']}
                return True
        #--- End: for
        
        return False
    #--- End: def
    
    def _write_bounds(self, coord, coord_ncdimensions, coord_ncvar):
        '''Create a bounds netCDF variable, creating a new bounds netCDF
    dimension if required. Return the bounds variable's netCDF variable
    name.
    
    .. note:: This function updates ``g['netcdf']``.
    
    :Parameters:
    
        coord: `BoundedVariable`
    
        coord_ncdimensions: `tuple`
            The ordered netCDF dimension names of the coordinate's
            dimensions (which do not include the bounds dimension).
    
        coord_ncvar: `str`
            The netCDF variable name of the parent variable
    
         g: `dict`
    
    :Returns:
    
        out: `dict`
    
    :Examples:
    
    >>> extra = _write_bounds(c, ('dim2',))
    
        '''
        g = self.write_vars
    
        if not (coord.hasbounds and coord.bounds.hasdata):
            return {}
    
        extra = {}
    
        # Still here? Then this coordinate has a bounds attribute
        # which contains data.
        bounds = coord.bounds
    
        size = bounds.shape[-1]
    
        ncdim = self._write_check_name('bounds{0}'.format(size), dimsize=size)
    
        # Check if this bounds variable has not been previously
        # created.
        ncdimensions = coord_ncdimensions +(ncdim,)        
        if self._seen(bounds, ncdimensions):
            # This bounds variable has been previously created, so no
            # need to do so again.
            ncvar = g['seen'][id(bounds)]['ncvar']
    
        else:
    
            # This bounds variable has not been previously created, so
            # create it now.
            ncdim_to_size = g['ncdim_to_size']
            if ncdim not in ncdim_to_size:
                ncdim_to_size[ncdim] = size
                g['netcdf'].createDimension(ncdim, size)
            #--- End: if
            
            ncvar = getattr(bounds, 'ncvar', coord_ncvar+'_bounds')
            
            ncvar = self._write_check_name(ncvar)
            
            # Note that, in a field, bounds always have equal units to
            # their parent coordinate
    
            # Select properties to omit
            omit = []
            for prop in g['omit_bounds_properties']:
                if coord.hasprop(prop):
                    omit.append(prop)
    
            # Create the bounds netCDF variable
            self._write_create_netcdf_variable(ncvar, ncdimensions,
                                               bounds, omit=omit)
        #--- End: if
    
        if getattr(coord, 'climatology', None):
            extra['climatology'] = ncvar
        else:
            extra['bounds'] = ncvar
    
        g['bounds'][coord_ncvar] = ncvar
            
        return extra
    #--- End: def
            
    def _write_scalar_coordinate(self, f, axis, coord, coordinates,
                                 key_to_ncvar, axis_to_ncscalar):
        '''Write a scalar coordinate and its bounds to the netCDF file.
    
It is assumed that the input coordinate is has size 1, but this is not
checked.
    
If an equal scalar coordinate has already been written to the file
then the input coordinate is not written.
    
.. note:: This function updates ``key_to_ncvar``,
          ``axis_to_ncscalar``.
    
:Parameters:

    f: `Field`
   
    axis : str
        The field's axis identifier for the scalar coordinate.

    key_to_ncvar : dict
        Mapping of field item identifiers to netCDF dimension names.

    axis_to_ncscalar : dict
        Mapping of field axis identifiers to netCDF scalar coordinate
        variable names.

    coordinates : list

:Returns:

    coordinates: `list`
        The updated list of netCDF auxiliary coordinate names.

        '''
        g = self.write_vars

#        coord = self._change_reference_datetime(coord)
            
        coord = self._squeeze_coordinate(coord)
    
        if not self._seen(coord, ()):
            ncvar = self._write_create_netcdf_variable_name(coord,
                                               default='scalar')
    
            # If this scalar coordinate has bounds then create the
            # bounds netCDF variable and add the bounds or climatology
            # attribute to the dictionary of extra attributes
            extra = self._write_bounds(coord, (), ncvar)
    
            # Create a new auxiliary coordinate variable
            self._write_create_netcdf_variable(ncvar, (), coord,
                                               extra=extra)
    
        else:
            # This scalar coordinate has already been written to the
            # file
            ncvar = g['seen'][id(coord)]['ncvar']
    
        axis_to_ncscalar[axis] = ncvar
    
        key_to_ncvar[axis] = ncvar
    
        coordinates.append(ncvar)
    
        return coordinates
    #--- End: def
    
    def _squeeze_coordinate(self, coord):
        '''
        '''
        coord = coord.copy()
        
        coord.data._array = numpy.squeeze(coord.array)
        if coord.hasbounds:
            coord.bounds.data._array = numpy.squeeze(coord.bounds.array, axis=0)
    
        return coord
    #--- End: def
    
    def _write_auxiliary_coordinate(self, f, key, coord, coordinates,
                                    key_to_ncvar, axis_to_ncdim):
        '''
    
    Write an auxiliary coordinate and its bounds to the netCDF file.
    
    If an equal auxiliary coordinate has already been written to the file
    then the input coordinate is not written.
    
    :Parameters:
    
        f : `Field`
       
        key : str
    
        coord : `Coordinate`
    
        coordinates : list
    
        key_to_ncvar : dict
            Mapping of field item identifiers to netCDF dimension names.
    
        axis_to_ncdim : dict
            Mapping of field axis identifiers to netCDF dimension names.
    
        g : dict
    
    :Returns:
    
        coordinates : list
            The list of netCDF auxiliary coordinate names updated in
            place.
    
    :Examples:
    
    >>> coordinates = _write_auxiliary_coordinate(f, 'aux2', coordinates)
    
        '''
        g = self.write_vars

#        coord = self._change_reference_datetime(coord)
    
        ncdimensions = self._write_grid_ncdimensions(f, key,
                                                     axis_to_ncdim)
    
        if self._seen(coord, ncdimensions):
            ncvar = g['seen'][id(coord)]['ncvar']
        
        else:
            ncvar = self._write_create_netcdf_variable_name(coord,
                                               default='auxiliary')
            
            # If this auxiliary coordinate has bounds then create the
            # bounds netCDF variable and add the bounds or climatology
            # attribute to the dictionary of extra attributes
            extra = self._write_bounds(coord, ncdimensions, ncvar)
    
            # Create a new auxiliary coordinate variable
            self._write_create_netcdf_variable(ncvar, ncdimensions,
                                               coord, extra=extra)
        #--- End: if
    
        key_to_ncvar[key] = ncvar
    
        coordinates.append(ncvar)
    
        return coordinates
    #--- End: def
      
    def _write_domain_ancillary(self, f, key, anc, key_to_ncvar, axis_to_ncdim):
        '''Write a domain ancillary and its bounds to the netCDF file.
    
    If an equal domain ancillary has already been written to the file then
    it is not re-written.
    
    :Parameters:
    
        f: `Field`
       
        key: `str`
            The internal identifier of the domain ancillary object.
    
        anc: `DomainAncillary`
    
        key_to_ncvar: `dict`
            Mapping of field item identifiers to netCDF variables.
    
        axis_to_ncdim: `dict`
            Mapping of field axis identifiers to netCDF dimensions.
    
        g: `dict`
    
    :Returns:
    
        out: `str`
            The netCDF variable name of the new netCDF variable.
    
    :Examples:
    
    >>> _write_domain_ancillary(f, 'cct2', anc)
    
        '''
        g = self.write_vars

        ncdimensions = tuple([axis_to_ncdim[axis] for axis in f.item_axes(key)])
    
        create = not self._seen(anc, ncdimensions)
    
        if not create:
            ncvar = g['seen'][id(anc)]['ncvar']
        
        else:
            ncvar = self._write_create_netcdf_variable_name(anc,
                                               default='domain_ancillary')
    
            # If this domain ancillary has bounds then create the bounds
            # netCDF variable
            self._write_bounds(anc, ncdimensions, ncvar)
    
            self._write_create_netcdf_variable(ncvar, ncdimensions,
                                               anc, extra={})
        #--- End: if
    
        key_to_ncvar[key] = ncvar
    
        return ncvar
    #--- End: def
      
    def _write_field_ancillary(self, f, key, anc, key_to_ncvar, axis_to_ncdim):
        '''Write a field ancillary to the netCDF file.
    
    If an equal field ancillary has already been written to the file then
    it is not re-written.
    
    :Parameters:
    
        f : `Field`
       
        key : str
    
        anc : `FieldAncillary`
    
        key_to_ncvar : dict
            Mapping of field item identifiers to netCDF variables
    
        axis_to_ncdim : dict
            Mapping of field axis identifiers to netCDF dimensions.
    
        g : dict
    
    :Returns:
    
        out : str
            The ncvar.
    
    :Examples:
    
    >>> ncvar = _write_field_ancillary(f, 'fav2', anc, key_to_ncvar, axis_to_ncdim)
    
        '''
        g = self.write_vars

        ncdimensions = tuple([axis_to_ncdim[axis] for axis in f.item_axes(key)])
    
        create = not self._seen(anc, ncdimensions)
    
        if not create:
            ncvar = g['seen'][id(anc)]['ncvar']    
        else:
            ncvar = self._write_create_netcdf_variable_name(anc, 'ancillary_data')
            self._write_create_netcdf_variable(ncvar, ncdimensions, anc)
    
        key_to_ncvar[key] = ncvar
    
        return ncvar
    #--- End: def
      
    def _write_cell_measure(self, f, key, msr, key_to_ncvar, axis_to_ncdim):
        '''
    
    Write an auxiliary coordinate and bounds to the netCDF file.
    
    If an equal cell measure has already been written to the file then the
    input coordinate is not written.
    
    :Parameters:
    
        f : `Field`
            The field containing the cell measure.
    
        key : str
            The identifier of the cell measure (e.g. 'msr0').
    
        key_to_ncvar : dict
            Mapping of field item identifiers to netCDF dimension names.
    
        axis_to_ncdim : dict
            Mapping of field axis identifiers to netCDF dimension names.
    
        g : dict
    
    :Returns:
    
        out : str
            The 'measure: ncvar'.
    
    :Examples:
    
    '''
        g = self.write_vars

        ncdimensions = self._write_grid_ncdimensions(f, key,
                                                     axis_to_ncdim)
    
        create = not self._seen(msr, ncdimensions)
    
        if not create:
            ncvar = g['seen'][id(msr)]['ncvar']
        else:
            if not hasattr(msr, 'measure'):
                raise ValueError(
    "Can't create a cell measure variable without a 'measure' attribute")
    
            ncvar = self._write_create_netcdf_variable_name(msr, 'cell_measure')
    
            self._write_create_netcdf_variable(ncvar, ncdimensions, msr)
        #--- End: if
                
        key_to_ncvar[key] = ncvar
    
        # Update the cell_measures list
        return '{0}: {1}'.format(msr.measure, ncvar)
    #--- End: def
      
    
    def _write_grid_mapping(self, f, ref, multiple_grid_mappings, key_to_ncvar):
        '''
    
    Write a grid mapping georeference to the netCDF file.
    
    .. note:: This function updates ``grid_mapping``, ``g['seen']``.
    
    :Parameters:
    
        f : `Field`
    
        ref : `CoordinateReference`
            The grid mapping coordinate reference to write to the file.
    
        multiple_grid_mappings : bool
    
        key_to_ncvar : dict
            Mapping of field item identifiers to netCDF variable names.
    
        g : dict
    
    :Returns:
    
        out : str
    
    :Examples:
    
    '''
        g = self.write_vars

        if self._seen(ref):
            # Use existing grid_mapping
            ncvar = g['seen'][id(ref)]['ncvar']
    
        else:
            # Create a new grid mapping
            ncvar = self._write_create_netcdf_variable_name(ref, 'grid_mapping')
    
            g['nc'][ncvar] = g['netcdf'].createVariable(ncvar, 'S1', (),
                                                        endian=g['endian'],
                                                        **g['compression'])
    
            cref = ref.canonical(f)
    
            # Add properties from key/value pairs
            if hasattr(g['nc'][ncvar], 'setncatts'):
                # Use the faster setncatts
                for term, value in cref.parameters.iteritems():
                    if value is None:
                        del cref[term]
                    elif numpy.size(value) == 1:
                        cref[term] = numpy.array(value, copy=False).item()
                    else:
                        cref[term] = numpy.array(value, copy=False).tolist()
                #--- End: for
                g['nc'][ncvar].setncatts(cref.parameters)
            else:
                # Otherwise use the slower setncattr
                pass #  I don't want to support this any more.
            
            # Update the 'seen' dictionary
            g['seen'][id(ref)] = {'variable': ref, 
                                  'ncvar'   : ncvar,
                                  'ncdims'  : (), # Grid mappings have no netCDF dimensions
                              }
        #--- End: if
    
        # Update the grid_mapping list in place
        if multiple_grid_mappings:
            return ncvar+':'+' '.join(sorted([key_to_ncvar[key] for key in ref.coordinates]))
        else:
            return ncvar
    #--- End: def
    
    def _write_create_netcdf_variable(self, ncvar, dimensions, cfvar,
                                      omit=(), extra={},
                                      data_variable=False):
        '''Create a netCDF variable from *cfvar* with name *ncvar* and
dimensions *ncdimensions*. The new netCDF variable's properties are
given by cfvar.properties(), less any given by the *omit* argument. If
a new string-length netCDF dimension is required then it will also be
created. The ``seen`` dictionary is updated for *cfvar*.
    
:Parameters:

    ncvar: `str`
        The netCDF name of the variable.

    dimensions: `tuple`
        The netCDF dimension names of the variable

    cfvar: `Variable`
        The coordinate, cell measure or field object to write to the
        file.

    omit: sequence of `str`, optional

    extra: `dict`, optional

:Returns:

    `None`

        '''
        g = self.write_vars
                
        _debug = g['_debug']
        
        if g['verbose']:
            print repr(cfvar)+' netCDF: '+ncvar
     
        if _debug:
            print '  '+repr(cfvar)+' netCDF: '+ncvar
            
        # ----------------------------------------------------------------
        # Set the netCDF4.createVariable datatype
        # ----------------------------------------------------------------
        datatype = self._write_datatype(cfvar)
    
        # ----------------------------------------------------------------
        # Set the netCDF4.createVariable dimensions
        # ----------------------------------------------------------------
        ncdimensions = dimensions
        
        if not cfvar.hasdata:
            data = None
        else:
            data = cfvar.data            
            if datatype == 'S1':
                # --------------------------------------------------------
                # Convert a string data type numpy array into a character
                # data type ('S1') numpy array with an extra trailing
                # dimension.
                # --------------------------------------------------------
                strlen = data.dtype.itemsize
                if strlen > 1:
                    data = self._write_convert_to_char(data)
                    ncdim = self._write_string_length_dimension(strlen)            
                    ncdimensions = dimensions + (ncdim,)
        #--- End: if
    
        # Find the fill value (note that this is set in the call to
        # netCDF4.createVariable, rather than with setncattr).
        fill_value = cfvar.fill_value()
    
        # Add simple properties (and units and calendar) to the netCDF
        # variable
        netcdf_attrs = cfvar.properties()
        for attr in ('units', 'calendar'):
            value = getattr(cfvar, attr, None)
            if value is not None:
                netcdf_attrs[attr] = value
        #--- End: for
    
        netcdf_attrs.update(extra)
        netcdf_attrs.pop('_FillValue', None)
    
        for attr in omit:
            netcdf_attrs.pop(attr, None) 
    
        # ------------------------------------------------------------
        # Create a new netCDF variable and set the _FillValue
        # ------------------------------------------------------------ 
        if data_variable:
            lsd = g['least_significant_digit']
        else:
            lsd = None
    
        # Set HDF chunk sizes
        chunksizes = None
    #    chunksizes = [size for i, size in sorted(cfvar.HDF_chunks().items())]
    #    if chunksizes == [None] * cfvar.ndim:
    #        chunksizes = None
    #
    #    if _debug:
    #        print '  chunksizes:', chunksizes

        try:
            g['nc'][ncvar] = g['netcdf'].createVariable(
                ncvar,
                datatype, 
                ncdimensions,
                fill_value=fill_value,
                least_significant_digit=lsd,
                endian=g['endian'],
                chunksizes=chunksizes,
                **g['compression'])
        except RuntimeError as error:
            error = str(error)
            if error == 'NetCDF: Not a valid data type or _FillValue type mismatch':
                raise ValueError(
    "Can't write {} data from {!r} to a {} file. Consider using a netCDF4 format or use the 'single' or 'datatype' parameters or change the datatype before writing.".format(
        cfvar.dtype.name, cfvar, g['netcdf'].file_format))
                
            message = "Can't create variable in {} file from {} ({})".format(g['netcdf'].file_format, cfvar, error)

            if error == 'NetCDF: NC_UNLIMITED in the wrong index':            
                raise RuntimeError(
    message+". Unlimited dimension must be the first (leftmost) dimension of the variable. Consider using a netCDF4 format.")
                    
            raise RuntimeError(message)
        #--- End: try
#        print ncvar
        self._write_attributes(ncvar, netcdf_attrs)
#        print 'CCC', g['nc'][ncvar]    , '-CCC'
    
        #-------------------------------------------------------------
        # Add data to the netCDF variable
        #
        # Note that we don't need to worry about scale_factor and
        # add_offset, since if a partition's data array is *not* a
        # numpy array, then it will have its own scale_factor and
        # add_offset parameters which will be applied when the array
        # is realised, and the python netCDF4 package will deal with
        # the case when scale_factor or add_offset are set as
        # properties on the variable.
        # -------------------------------------------------------------
        if data is not None:  
    
            # Find the missing data values, if any.
            if not fill_value:
                missing_data = None
            else:
                _FillValue    = getattr(cfvar, '_FillValue', None) 
                missing_value = getattr(cfvar, 'missing_value', None)
                missing_data = [value for value in (_FillValue, missing_value)
                                if value is not None]
            #--- End: if

            self._write_data_to_variable(data, ncvar, missing_data)

            # Update the 'seen' dictionary
            g['seen'][id(cfvar)] = {'variable': cfvar,
                                    'ncvar'   : ncvar,
                                    'ncdims'  : dimensions}
    #--- End: def
    
    def _write_data_to_variable(self, data, ncvar, missing_data):
        '''
        '''
        g = self.write_vars

        convert_dtype = g['datatype']

        array = data.array

        # Convert data type
        new_dtype = convert_dtype.get(array.dtype, None)
        if new_dtype is not None:
            array = array.astype(new_dtype)  

        # Check that the array doesn't contain any elements
        # which are equal to any of the missing data values
        if missing_data:
            if numpy.ma.is_masked(array):
                temp_array = array.compressed()
            else:
                temp_array = array
                
            if numpy.intersect1d(missing_data, temp_array):
                raise ValueError(
    "ERROR: Can't write field when array has _FillValue or missing_value at unmasked point: {!r}".format(cfvar))
        #--- End: if
    
        # Copy the array into the netCDF variable
        g['nc'][ncvar][...] = array
    #--- End: def
    
    def _write_convert_to_char(self, data):
        '''Convert a string array into a character array (data type 'S1') with
     an extra trailing dimension.
    
    :Parameters:
    
        data: `Data`
    
        '''
        strlen = data.dtype.itemsize
        if strlen > 1:
            data = data.copy()
            
            array = self._write_character_array(data.array)
            
            data._shape = array.shape
            data._ndim  = array.ndim
            data._dtype = array.dtype
            data._array = array
    
        return data
    #--- End: def
    
    def _write_a_field(self, f, add_to_seen=False, allow_data_expand_dims=True,
                       remove_crap_axes=False):
        '''
    
    :Parameters:
    
        f : `Field`
    
        add_to_seen : bool, optional
    
        allow_data_expand_dims : bool, optional
    
        g : dict
    
    :Returns:
    
        None
    
        '''
        g = self.write_vars

    #    if g['_debug']:
    #        print '  '+repr(f)
    
        seen = g['seen']
          
        if add_to_seen:
            id_f = id(f)
            org_f = f
            
        f = f.copy()
    
        data_axes = f.data_axes()
    
        # Mapping of field axis identifiers to netCDF dimension names
        axis_to_ncdim = {}
    
        # Mapping of field axis identifiers to netCDF scalar coordinate
        # variable names
        axis_to_ncscalar = {}
    
        # Mapping of field item identifiers to netCDF variable names
        key_to_ncvar = {}
    
        # Initialize the list of the field's auxiliary coordinates
        coordinates = []
    
        # For each of the field's axes ...
        for axis in sorted(f.axes()):
            dim_coord = f.item(axis, role='d')
            if dim_coord is not None:
                # --------------------------------------------------------
                # A dimension coordinate exists for this axis
                # --------------------------------------------------------
                if axis in data_axes:
                    # The data array spans this axis, so write the
                    # dimension coordinate to the file as a netCDF 1-d
                    # coordinate variable.
                    ncdim = self._write_dimension_coordinate(f, axis, dim_coord,
                                                             key_to_ncvar, axis_to_ncdim)
                else:
                    # The data array does not span this axis (and
                    # therefore it must have size 1).
                    if f.items(role=('a', 'm', 'c', 'f'), axes=axis):
                        # There ARE auxiliary coordinates, cell measures,
                        # domain ancillaries or field ancillaries which
                        # span this axis, so write the dimension
                        # coordinate to the file as a netCDF 1-d
                        # coordinate variable.
                        ncdim = self._write_dimension_coordinate(f, axis, dim_coord,
                                                                 key_to_ncvar,
                                                                 axis_to_ncdim)
    
                        # Expand the field's data array to include this
                        # axis
                        f.expand_dims(0, axes=axis, copy=False) 
                    else:
                        # There are NO auxiliary coordinates, cell
                        # measures, domain ancillaries or field
                        # ancillaries which span this axis, so write the
                        # dimension coordinate to the file as a netCDF
                        # scalar coordinate variable.
                        coordinates = self._write_scalar_coordinate(f, axis, dim_coord,
                                                                    coordinates,
                                                                    key_to_ncvar,
                                                                    axis_to_ncscalar)
                #--- End: if
            else:
                # --------------------------------------------------------
                # There is no dimension coordinate for this axis
                # --------------------------------------------------------
                if axis not in data_axes and f.items(role=('a', 'm', 'c', 'f'), axes=axis):
                    # The data array doesn't span the axis but an
                    # auxiliary coordinate, cell measure, domain ancillary
                    # or field ancillary does, so expand the data array to
                    # include it.
                    f.expand_dims(0, axes=axis, copy=False)
                    data_axes.append(axis)
                #--- End: if
    
                # If the data array (now) spans this axis then create a
                # netCDF dimension for it
                if axis in data_axes:
                    ncdim = getattr(f, 'ncdimensions', {}).get(axis, 'dim')
                    ncdim = self._write_check_name(ncdim)
    
                    unlimited = self._unlimited(f, axis)
                    self._write_dimension(ncdim, f, axis, axis_to_ncdim,
                                          unlimited=unlimited)
                 #--- End: if
            #--- End: if
    
        #--- End: for
    
        # ----------------------------------------------------------------
        # Create auxiliary coordinate variables, except those which might
        # be completely specified elsewhere by a transformation.
        # ----------------------------------------------------------------
        # Initialize the list of 'coordinates' attribute variable values
        # (each of the form 'name')
        for key, aux_coord in sorted(f.items(role='a').iteritems()):
            coordinates = self._write_auxiliary_coordinate(f, key, aux_coord,
                                                           coordinates, key_to_ncvar,
                                                           axis_to_ncdim)
        #--- End: for
    
        # ----------------------------------------------------------------
        # Create domain ancillary netCDF variables
        # ----------------------------------------------------------------
        for key, anc in sorted(f.items(role='c').iteritems()):
            self._write_domain_ancillary(f, key, anc, key_to_ncvar,
                                         axis_to_ncdim)
    
        # ----------------------------------------------------------------
        # Create cell measures netCDF variables
        # ----------------------------------------------------------------
        # Set the list of 'cell_measures' attribute values (each of
        # the form 'measure: name')
        cell_measures = [self._write_cell_measure(f, key, msr, key_to_ncvar,
                                                  axis_to_ncdim)
                         for key, msr in sorted(f.items(role='m').iteritems())]
    
        # ----------------------------------------------------------------
        # Grid mappings
        # ----------------------------------------------------------------
        grid_mapping_refs = f.items('type%grid_mapping', role='r').values()
        multiple_grid_mappings = len(grid_mapping_refs) > 1
    
        grid_mapping = [self._write_grid_mapping(f, ref, multiple_grid_mappings,
                                                 key_to_ncvar)
                        for ref in grid_mapping_refs]
        
        if multiple_grid_mappings:        
            grid_mapping2 = []
            for x in grid_mapping:
                name, a = x.split(':')
                a = a.split()
                for y in grid_mapping:
                    if y == x:
                        continue
                    b = y.split(':')[1].split()
    
                    if len(a) > len(b) and set(b).issubset(a):
                        a = [q for q in a if q not in b]
                #--- End: for
                grid_mapping2.apend(name+':'+' '.join(a))
            #--- End: for
            grid_mapping = grid_mapping2
        #--- End: if
    
        # ----------------------------------------------------------------
        # formula_terms
        # ----------------------------------------------------------------
        for ref in f.items('type%formula_terms', role='r').values():
            formula_terms = []
            bounds_formula_terms = []
    
            formula_terms_name = ref.name()
            if formula_terms_name is None:
                owning_coord = None
            else:
                owning_coord = f.item(formula_terms_name, role=('d', 'a'), exact=True)
    
            z_axis = f.item_axes(formula_terms_name, role=('d', 'a'), exact=True)[0]
                
            if owning_coord is not None:
                # This formula_terms coordinate reference matches up with
                # an existing coordinate
    
                for term, value in ref.parameters.iteritems():
                    if value is None:
                        continue
    
                    if term == 'standard_name':
                        continue
    
    #                value = Data.asdata(value)
                    ncvar = self._write_scalar_data(value, ncvar=term)
    
                    formula_terms.append('{0}: {1}'.format(term, ncvar))
                    bounds_formula_terms.append('{0}: {1}'.format(term, ncvar))
                #--- End: for
            
                for term, value in ref.ancillaries.iteritems():
                    if value is None:
                        continue
    
                    domain_anc = f.item(value, role='c')
                    if domain_anc is None:
                        continue
    
                    if id(domain_anc) not in seen:
                        continue
    
                    # Get the netCDF variable name for the domain
                    # ancillary and add it to the formula_terms attribute
                    ncvar = seen[id(domain_anc)]['ncvar']                
                    formula_terms.append('{0}: {1}'.format(term, ncvar))
    
                    bounds = g['bounds'].get(ncvar, None)
                    if bounds is not None:
                        if z_axis not in f.item_axes(value, role='c'):
                            bounds = None
    
                    if bounds is None:        
                        bounds_formula_terms.append('{0}: {1}'.format(term, ncvar))
                    else:
                        bounds_formula_terms.append('{0}: {1}'.format(term, bounds))
            #--- End: if
    
            # Add the formula_terms attribute to the parent coordinate
            # variable
            if formula_terms:
                ncvar = seen[id(owning_coord)]['ncvar']
                formula_terms = ' '.join(formula_terms)
                g['nc'][ncvar].setncattr('formula_terms', formula_terms)
                if g['_debug']:
                    print '  formula_terms =', formula_terms
    
                # Add the formula_terms attribute to the coordinate bounds
                # variable
                bounds = g['bounds'].get(ncvar)
                if bounds is not None:
                    bounds_formula_terms = ' '.join(bounds_formula_terms)
                    g['nc'][bounds].setncattr('formula_terms', bounds_formula_terms)
                    if g['_debug']:
                        print '  Bounds formula_terms =', bounds_formula_terms
        #--- End: for
    
        # ----------------------------------------------------------------
        # Field ancillary variables
        # ----------------------------------------------------------------
        # Create the 'ancillary_variables' CF-netCDF attribute and create
        # the referenced CF-netCDF ancillary variables
        ancillary_variables = [self._write_field_ancillary(f, key, anc, key_to_ncvar,
                                                           axis_to_ncdim)
                               for key, anc in f.items(role='f').iteritems()]
    
        # ----------------------------------------------------------------
        # Create the CF-netCDF data variable
        # ----------------------------------------------------------------
        ncvar = self._write_create_netcdf_variable_name(f, 'data')
    
        ncdimensions = tuple([axis_to_ncdim[axis] for axis in f.data_axes()])
    
        extra = {}
    
        # Cell measures
        if cell_measures:
            extra['cell_measures'] = ' '.join(cell_measures)           
    
        # Auxiliary/scalar coordinates
        if coordinates:
            extra['coordinates'] = ' '.join(coordinates)
    
        # Grid mapping
        if grid_mapping: 
            extra['grid_mapping'] = ' '.join(grid_mapping)
    
        # Ancillary variables
        if ancillary_variables:
            extra['ancillary_variables'] = ' '.join(ancillary_variables)
            
        # Flag values
        if hasattr(f, 'flag_values'):
            extra['flag_values'] = f.flag_values
    
        # Flag masks
        if hasattr(f, 'flag_masks'):
            extra['flag_masks'] = f.flag_masks
    
        # Flag meanings
        if hasattr(f, 'flag_meanings'):
            extra['flag_meanings'] = ' '.join(f.flag_meanings)
    
        # name can be a dimension of the variable, a scalar coordinate
        # variable, a valid standard name, or the word 'area'
        cell_methods = f.Items.cell_methods
        if cell_methods:
            axis_map = axis_to_ncdim.copy()
            axis_map.update(axis_to_ncscalar)
            extra['cell_methods'] = ' '.join([cm.write(axis_map)
                                              for cm in cell_methods])            
#            extra['cell_methods'] = cell_methods.write(axis_map)
    
        # Create a new data variable
        self._write_create_netcdf_variable(ncvar, ncdimensions, f,
                                           omit=g['global_properties'],
                                           extra=extra, data_variable=True)
        
        # Update the 'seen' dictionary, if required
        if add_to_seen:
            seen[id_f] = {'variable': org_f,
                          'ncvar'   : ncvar,
                          'ncdims'  : ncdimensions}
    #--- End: def
    
    def _unlimited(self, f, axis):
        '''
    '''
        g = self.write_vars

        unlimited = f.unlimited().get(axis)
    
        if unlimited is None:
            unlimited = False
            for u in g['unlimited']:
                if f.axis(u, key=True) == axis:
                    unlimited = True
                    break
        
        return unlimited
    #--- End: def
    
    def _write_global_properties(self, fields):
        '''Find the netCDF global properties from all of the input fields and
write them to the netCDF4.Dataset.
    
.. note:: This function updates ``g['global_properties']``.
    
:Parameters:
  
    fields : list
  
:Returns:
    
    `None`
        
        '''
        g = self.write_vars
        
        # Data variable properties, as defined in Appendix A, without
        # those which are not simple.
        data_properties = set(('add_offset',
                               'cell_methods',
                               '_FillValue',
                               'flag_masks',
                               'flag_meanings',
                               'flag_values',
                               'long_name',
                               'missing_value',
                               'scale_factor',
                               'standard_error_multiplier',
                               'standard_name',
                               'units',
                               'valid_max',
                               'valid_min',
                               'valid_range',
                               ))
    
        # Global properties, as defined in Appendix A
        global_properties = set(('comment',
                                 'Conventions',
                                 'featureType',
                                 'history',
                                 'institution',
                                 'references',
                                 'source',
                                 'title',
                                 ))
    
        # Put all non-standard CF properties (i.e. those not in the
        # data_properties set) into the global_properties set, but
        # omitting those which have been requested to be on variables.
        for f in fields:
            for attr in set(f._simple_properties()) - global_properties - g['variable_attributes']:
                if attr not in data_properties:
                    global_properties.add(attr)
        #--- End: for
    
        # Remove properties from the new global_properties set which
        # have different values in different fields
        f0 = fields[0]
        for prop in tuple(global_properties):
            if not f0.hasprop(prop):
                global_properties.remove(prop)
                continue
                
            prop0 = f0.getprop(prop)
    
            if len(fields) > 1:
                for f in fields[1:]:
                    if (not f.hasprop(prop) or 
                        not equals(f.getprop(prop), prop0, traceback=False)):
                        global_properties.remove(prop)
                        break
        #--- End: for
    
        # Write the global properties to the file
        g['netcdf'].setncattr('Conventions', self.Conventions)
        
        for attr in global_properties - set(('Conventions',)):
            g['netcdf'].setncattr(attr, f0.getprop(attr)) 
    
        g['global_properties'] = global_properties
    #--- End: def

#--- End: class
