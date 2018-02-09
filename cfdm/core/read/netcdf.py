import copy
import re
import struct

import numpy

from ..functions import abspath, flat

class ReadNetCDF(object):
    '''
    '''
    def __init__(self, NetCDF=None, AuxiliaryCoordinate=None,
                 CellMeasure=None, CellMethod=None,
                 CoordinateAncillary=None ,CoordinateReference=None,
                 DimensionCoordinate=None, DomainAncillary=None,
                 DomainAxis=None, Field=None, FieldAncillary=None,
                 Bounds=None, Data=None):
        '''
        '''
        self._NetCDF              = NetCDF
        self._AuxiliaryCoordinate = AuxiliaryCoordinate
        self._CellMeasure         = CellMeasure
        self._CellMethod          = CellMethod
        self._CoordinateAncillary = CoordinateAncillary
        self._CoordinateReference = CoordinateReference
        self._DimensionCoordinate = DimensionCoordinate
        self._DomainAncillary     = DomainAncillary
        self._DomainAxis          = DomainAxis
        self._Field               = Field         
        self._FieldAncillary      = FieldAncillary
        self._Bounds              = Bounds               
        self._Data                = Data                 

        # ------------------------------------------------------------
        # Initialise netCDF read parameters
        # ------------------------------------------------------------
        self._read_vars = {
            #
            'new_dimensions': {},
            #
            'formula_terms': {},
            #
            'compression': {},
            'uncompress' : True,
            #
            'external_nc': [],
            # Chatty?
            'verbose': False,
            # Debug  print statements?
            '_debug': False,
        }
            
    def read(self, filename, field=(), verbose=False, uncompress=True,
             extra_read_vars=None, _debug=False):
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
        self.read_vars = self._reset_read_vars(extra_read_vars)
        g = self.read_vars
        
        if isinstance(filename, file):
            name = filename.name
            filename.close()
            filename = name

        g['uncompress'] = uncompress
        g['verbose']    = verbose
        g['_debug']     = _debug
        
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
        nc = self.open_file()
        g['nc'] = nc
        
        if _debug:
            print 'Reading netCDF file:', filename
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
                self._parse_compression_gathered(ncvar,
                                                      attributes,
                                                      compressed_ncdims)
                variables.discard(ncvar)
            
            if g['global_attributes'].get('featureType'):
                if 'sample_dimension' in attributes[ncvar]:
                    # This variable is a count variable for DSG contiguous
                    # ragged arrays
                    sample_ncdimension = attributes[ncvar]['sample_dimension']        
                    element_dimension_2 = self._parse_DSG_contiguous_compression(
                        ncvar,
                        attributes,
                        sample_ncdimension)
                    variables.discard(ncvar)
                
                if 'instance_dimension' in attributes[ncvar]:
                    # This variable is an index variable for DSG indexed
                    # ragged arrays
                    instance_ncdimension = attributes[ncvar]['instance_dimension']
                    element_dimension_1 = self._parse_DSG_indexed_compression(
                        ncvar,
                        attributes,
                        instance_ncdimension)
                    variables.discard(ncvar)
                
                if sample_ncdimension and instance_ncdimension:
                    self._parse_DSG_indexed_contiguous_compression(
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
                            
                        self._formula_terms_variables(ncvar, formula_terms,
                                                           variables, coord=True)
    
                        bounds = attributes[ncvar].get('bounds', None)
                        if bounds is not None and 'formula_terms' in attributes[bounds]:
                            bounds_formula_terms = attributes[bounds]['formula_terms']
    
                            self._formula_terms_variables(ncvar,
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
    
        fields_in_file = []
    
        for data_ncvar in variables:
            f = self._create_Field(data_ncvar, attributes,
                                   dimension_coordinates,
                                   auxiliary_coordinates,
                                   cell_measures,
                                   domain_ancillaries,
                                   field_ancillaries,
                                   list_variables,
                                   verbose=verbose)
    
            fields_in_file.append(f)
        #--- End: for

        # ------------------------------------------------------------        
        # Close the netCDF file
        # ------------------------------------------------------------                
        self.close_file()
        
        return fields_in_file
    #--- End: def

    def close_file(self):
        '''Close the netCDF that has been read.

:Returns:

    None

        '''
        nc = self.read_vars['nc']
        nc.close()
    #--- End: def
        
    @classmethod
    def file_type(cls, filename):
        '''Find the format of a file.
    
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

    def open_file(self):
        '''Open the netCDf file for reading.

:Returns:

    out: `netCDF.Dataset`

        '''
        filename = self.read_vars['filename']
        return self._NetCDF.file_open(filename, 'r')
    #--- End: def        

    def _reset_read_vars(self, extra_read_vars):
        '''
        '''
        d = copy.deepcopy(self._read_vars)
        if extra_read_vars:
            d.update(copy.deepcopy(extra_read_vars))

        return d
    #--- End: def

    def _parse_compression_gathered(self, ncvar, attributes,
                                    compressed_ncdims):
        '''
        '''
        g = self.read_vars
        
        _debug = g['_debug']
        if _debug:
            print '        List variable: compress =', compressed_ncdims
    
        compression_type = 'gathered'
        gathered_ncdimension = g['nc'][ncvar].dimensions[0]
        indices = self._create_array(ncvar, attributes)
        
        g['compression'][gathered_ncdimension] = {
            'gathered': {'indices'             : indices,
                         'implied_ncdimensions': compressed_ncdims.split()}}
    #--- End: def
    
    def _parse_DSG_contiguous_compression(self, ncvar, attributes,
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
    
        elements_per_instance = self._create_array(ncvar, attributes)
    
        instance_dimension_size = elements_per_instance.size    
        element_dimension_size  = int(elements_per_instance.max())
    
        # Create an empty Data array which has dimensions (instance
        # dimension, element dimension).
        data = self._Data.compression_initialize_contiguous(
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
    
    def _parse_DSG_indexed_compression(self, ncvar, attributes,
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
        
        index = self._create_array(ncvar, attributes)
        
        (instance, inverse, count) = numpy.unique(index,
                                                  return_inverse=True,
                                                  return_counts=True)
    
        # The indices of the sample dimension which apply to each
        # instance. For example, if the sample dimension has size 20 and
        # there are 3 instances then the instance_indices arary might look
        # like [1, 0, 2, 2, 1, 0, 2, 1, 0, 0, 2, 1, 2, 2, 1, 0, 0, 0, 2,
        # 0].
        instance_indices = self._create_Data(array=inverse)
    
        # The number of elements per instance. For the instance_indices
        # example, the elements_per_instance array is [7, 5, 7].
        elements_per_instance = self._create_Data(array=count)
    
        instance_dimension_size = g['nc'].dimensions[instance_ncdimension].size
        element_dimension_size  = int(elements_per_instance.max())
    
        # Create an empty Data array which has dimensions
        # (instance dimension, element dimension)
        data = self._Data.compression_initialize_indexed(
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
    
    def _parse_DSG_indexed_contiguous_compression(self, ncvar,
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
        data = self._Data.compression_initialize_indexed_contiguous(
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
    
    def _formula_terms_variables(self, ncvar, formula_terms,
                                 variables, coord=False,
                                 bounds=False):
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
    
    def _create_Field(self, data_ncvar, attributes,
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
            cell_methods = self._CellMethod.parse(cell_methods, allow_error=True)
            error = cell_methods[0].get_error(False)
            if verbose and error:
                print ("WARNING: {0}: {1!r}".format(error, cell_methods[0].get_string('')))
        #--- End: if
    
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
        #--- End: for
        
        # ----------------------------------------------------------------
        # Initialize the field with the data variable and its attributes
        # ----------------------------------------------------------------
#        f_Units = self._Units(properties.pop('units', None),
#                              properties.pop('calendar', None))
#
#        if g['verbose'] and not f_Units.isvalid:
#            print(
#"WARNING: Unsupported units in file {0} on variable {1}: {2}".format(
#    g['filename'], data_ncvar, f_Units))

        if _debug:
            print '    Field properties:', properties
            
        f = self._Field(properties=properties, copy=False)

        f.set_ncvar(data_ncvar)
#        f.files = set((g['filename'],))
#        f.Units = f_Units
    
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
                # create a domain axis and dimension coordinate
                if ncdim in dimension_coordinates:
                    coord = dimension_coordinates[ncdim].copy()
                else:
                    coord = self._create_bounded_item(ncdim,
                                                      attributes, f,
                                                      dimension=True,
                                                      verbose=verbose)
                    dimension_coordinates[ncdim] = coord
                
                domain_axis = self._DomainAxis(coord.get_data().size)
                domain_axis.set_ncdim(ncdim)
                if _debug:
                    print '    Inserting', repr(domain_axis)                    
                axis = f.set_domain_axis(domain_axis, copy=False)

                if _debug:
                    print '    Inserting', repr(coord)
                dim = f.set_dimension_coordinate(coord, axes=[axis], copy=False)
                
                # Set unlimited status of axis
                if nc.dimensions[ncdim].isunlimited():
                    f.unlimited({axis: True})
    
                ncvar_to_key[ncdim] = dim
            else:
                # There is no dimension coordinate for this dimension,
                # so just create a domain axis with the correct size.
                if ncdim in g['new_dimensions']:
                    size = g['new_dimensions'][ncdim]
                else:
                    size = len(nc.dimensions[ncdim])
    
                domain_axis = self._DomainAxis(size)
                domain_axis.set_ncdim(ncdim)
                if _debug:
                    print '    Inserting', repr(domain_axis)
                axis = f.set_domain_axis(domain_axis, copy=False)
                
                # Set unlimited status of axis
                try:
                    if nc.dimensions[ncdim].isunlimited():
                        f.unlimited({axis: True})
                except KeyError:
                    # This dimension is not in the netCDF file (as might
                    # be the case for an element dimension implied by a
                    # DSG ragged array).
                    pass            
            #--- End: if
    
            # Update data dimension name and set dimension size
            f._data_axes.append(axis)
    
            ncdim_to_axis[ncdim] = axis
        #--- End: for
    
        f._Data = self._set_Data(data_ncvar, f, unpacked_dtype=unpacked_dtype)
        
        # ----------------------------------------------------------------
        # Add scalar dimension coordinates and auxiliary coordinates to
        # the field
        # ----------------------------------------------------------------
        coordinates = f.get_property('coordinates', None)
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
                    coord = self._create_bounded_item(ncvar,
                                                      attributes, f,
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
                        domain_axis = self._DomainAxis(1)
                        dim = f.set_domain_axis(domain_axis)
                        if _debug:
                            print '    Inserting', repr(domain_axis)

                        # Record the netCDF dimension name for this axis
                        f.axes()[dim].set_ncdim(ncdim)
                        dimensions = [dim]
                    else:  
                        # Numeric valued scalar coordinate
                        is_dimension_coordinate = True
                #--- End: if
    
                if is_dimension_coordinate:
                    # Insert dimension coordinate
                    coord = self._DimensionCoordinate(source=coord, copy=False)
    
                    if _debug:
                        print '    Inserting', repr(coord)
    
                    domain_axis = self._DomainAxis(coord.get_data().size)
                    axis = f.set_domain_axis(domain_axis, copy=False)
                    
                    dim = f.set_dimension_coordinate(coord, axes=[axis], copy=False)
                    
                    # Record the netCDF dimension name for this axis
                    f.axes()[dim].set_ncdim(ncvar)  # ????
                    dimensions = [axis]
                    ncvar_to_key[ncvar] = dim
                    dimension_coordinates[ncvar] = coord
                    del auxiliary_coordinates[ncvar]
                else:
                    # Insert auxiliary coordinate
                    if _debug:
                        print '    Inserting', repr(coord)
                    aux = f.set_auxiliary_coordinate(coord, axes=dimensions, copy=False)
                    ncvar_to_key[ncvar] = aux
                
                if scalar:
                    ncscalar_to_axis[ncvar] = dimensions[0]
            #--- End: for
    
            f.del_property('coordinates')
        #--- End: if
    
        # ----------------------------------------------------------------
        # Add coordinate references from formula_terms properties
        # ----------------------------------------------------------------
        if data_ncvar not in g['promoted']:
            # Only add coordinate references to metadata variables

            for key, coord in f.coordinates().iteritems():
                formula_terms = attributes[coord.get_ncvar()].get('formula_terms', None)
                if formula_terms is None:
                    # This coordinate doesn't have a formula_terms attribute
                    continue
        
                for term, ncvar in g['formula_terms'][coord.get_ncvar()]['coord'].iteritems():
                    # Set dimensions 
                    axes = [ncdim_to_axis[ncdim]
                            for ncdim in self._ncdimensions(ncvar)
                            if ncdim in ncdim_to_axis]    
                    
    #                if not axes:
    #                    # Variable is scalar => term is a parameter, not a
    #                    # DomainAncillary
    #                    if ncvar not in coordref_parameters:
    #                        variable = self._create_array(ncvar, attributes)
    #                        coordref_parameters[ncvar] = variable
    #                    continue
    #    
    ##                # Still here? Then the term is a DomainAncillary, not a
    #                # parameter.
                    if ncvar in domain_ancillaries:
                        domain_anc = domain_ancillaries[ncvar][1].copy()
                    else:
                        bounds = g['formula_terms'][coord.get_ncvar()]['bounds'].get(term)
                        if bounds == ncvar:
                            bounds = None
        
                        domain_anc = self._create_bounded_item(ncvar,
                                                               attributes,
                                                               f,
                                                               domainancillary=True,
                                                               bounds=bounds,
                                                               verbose=verbose)
                    #--- End: if
                    
                    # Insert domain ancillary
                    da_key = f.set_domain_ancillary(domain_anc, axes=axes, copy=False)
                    if ncvar not in ncvar_to_key:
                        ncvar_to_key[ncvar] = da_key
        
                    domain_ancillaries[ncvar] = (da_key, domain_anc)
                #--- End: for
        
                self._create_formula_terms_ref(f, key, coord,
                                               g['formula_terms'][coord.get_ncvar()]['coord'],
                                               domain_ancillaries)
            #--- End: for
        #--- End: if
    
        # ----------------------------------------------------------------
        # Add grid mapping coordinate references
        # ----------------------------------------------------------------
        grid_mapping = f.get_property('grid_mapping', None)
        if grid_mapping is not None:
            self._create_grid_mapping_ref(f, grid_mapping,
                                               attributes, ncvar_to_key)
    
        # ----------------------------------------------------------------
        # Add cell measures to the field
        # ----------------------------------------------------------------
        measures = f.get_property('cell_measures', None)
        if measures is not None:
    
            # Parse the cell measures attribute
            measures = re.split('\s*(\w+):\s*', measures)
            
            for measure, ncvar in zip(measures[1::2], 
                                      measures[2::2]):
                
                if ncvar not in attributes:
                    # EXTERNAL HERE
                    continue
    
                # Set cell measures' dimensions 
                cm_ncdimensions = self._ncdimensions(ncvar)
                axes = [ncdim_to_axis[ncdim] for ncdim in cm_ncdimensions]
    
                if ncvar in cell_measures:
                    # Copy the cell measure as it already exists
                    cell = cell_measures[ncvar].copy()
                else:
                    cell = self._create_item(ncvar, attributes, f,
                                             cell_measure=True)
                    cell.measure = measure
                    cell_measures[ncvar] = cell
                #--- End: if
    
                clm = f.set_cell_measure(cell, axes=axes, copy=False)
    
                ncvar_to_key[ncvar] = clm
            #--- End: for
    
            f.del_property('cell_measures')
        #--- End: if
    
        # ----------------------------------------------------------------
        # Add cell methods to the field
        # ----------------------------------------------------------------
        if cell_methods:
            name_to_axis = ncdim_to_axis.copy()
            name_to_axis.update(ncscalar_to_axis)
            for cm in cell_methods:
                cm = cm.change_axes(name_to_axis)
                f.set_cell_method(cm, copy=False)
        #--- End: if

        # ----------------------------------------------------------------
        # Add field ancillaries to the field
        # ----------------------------------------------------------------
        ancillary_variables = f.get_property('ancillary_variables', None)
        if ancillary_variables is not None:
            f.del_property('ancillary_variables')
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
                    field_anc = self._create_item(ncvar, attributes,
                                                  f,
                                                  field_ancillary=True)
                    field_ancillaries[ncvar] = field_anc
                    
                # Insert the field ancillary
                key = f.set_field_ancillary(field_anc, axes=axes, copy=False)
                ncvar_to_key[ncvar] = key
        #--- End: if
    
        # Return the finished field
        return f
    #--- End: def
    
    def _create_bounded_item(self, ncvar, attributes, f,
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
      
#        c_Units = self._Units(properties.pop('units', None),
#                              properties.pop('calendar', None))
#    
#        if g['verbose'] and not c_Units.isvalid:
#            print(
#"WARNING: Unsupported units in file {0} on variable {1}: {2}".format(
#    g['filename'], ncvar, c_Units))

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
            c = self._DimensionCoordinate(properties=properties)
        elif auxiliary:
            c = self._AuxiliaryCoordinate(properties=properties)
        elif domainancillary:
            properties.pop('coordinates', None)
            properties.pop('grid_mapping', None)
            properties.pop('cell_measures', None)
    
            properties.pop('formula_terms', None)
            properties.pop('positive', None)
    
            c = self._DomainAncillary(properties=properties)
        else:
            raise ValueError(
"Must set one of the dimension, auxiliary or domainancillary parmaeters to True")
    
        c.set_ncvar(ncvar)
#        c.Units = c_Units
    
        if climatology:
            c.climatology = climatology
    
        data = self._set_Data(ncvar, c)

        c.set_data(data, copy=False)
        
        # ------------------------------------------------------------
        # Add any bounds
        # ------------------------------------------------------------
        if ncbounds is None:
            bounds = None
        else:
            properties = attributes[ncbounds].copy()
            properties.pop('formula_terms', None)
    
#            b_Units = self._Units(properties.pop('units', None),
#                                  properties.pop('calendar', None))
#    
#            if g['verbose'] and not b_Units.isvalid:
#                print(
#"WARNING: Unsupported units in file {0} on variable {1}: {2}".format(
#    g['filename'], ncbounds, b_Units))

            bounds = self._Bounds(properties=properties, copy=False)

#            if getattr(bounds, 'units', None) is None:
#                bounds.set_property('units', getattr(c, 'units', None))
#
#            if getattr(bounds, 'calendar', None) is None:
#                bounds.set_property('calendar', getattr(c, 'calendar', None))
#
#            if not b_Units:
#                b_Units = c_Units
#    
#            bounds.Units = b_Units
            
            bounds.set_ncvar(ncbounds)
    
            bounds_data = self._set_Data(ncbounds, bounds)
    
            bounds.set_data(bounds_data, copy=False)
    
            # Make sure that the bounds dimensions are in the same order
            # as its parent's dimensions
            c_ndim = c.get_data().ndim
            b_ndim = bounds.get_data().ndim
            if b_ndim > c_ndim:
                c_ncdims = nc.variables[ncvar].dimensions
                b_ncdims = nc.variables[ncbounds].dimensions
                if c_ncdims != b_ncdims[:c_ndim]:
                    axes = [c_ncdims.index(ncdim) for ncdim in b_ncdims[:c_ndim]
                            if ncdim in c_ncdims]
                    if len(axes) == c_ndim:
                        axes.extend(range(b_ndim - c_ndim, 0))
#                        bounds.transpose(axes, copy=False)
                        self._transpose(bounds, axes=axes, copy=False)
            #--- End: if

            c.set_bounds(bounds, copy=False)
        #--- End: if
    
        # ---------------------------------------------------------
        # Return the bounded variable
        # ---------------------------------------------------------
        return c
    #--- End: def

    def _transpose(self, construct, axes=None, copy=True):
        '''
        '''
        return construct.tranpose(axes=axes, copy=copy)
    #-- End: def
    
    def _create_array(self, ncvar, attributes):
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
    
#        units = self._Units(properties.get('units'),
#                            properties.get('calendar'))
#    
#        if self.read_vars['verbose'] and not units.isvalid:
#            print(
#"WARNING: Unsupported units in file {0} on variable {1}: {2}".format(
#    self.read_vars['filename'], ncvar, units))

        data = self._set_Data(ncvar) #, units=units)
    
        return data
    #--- End: def
    
    def _create_item(self, ncvar, attributes, f,
                          cell_measure=False, field_ancillary=False):
        '''Create a cell measure or field ancillary object.
    
:Parameters:
    
    ncvar: `str`
        The netCDF name of the cell measure variable.

    attributes: `dict`
        Dictionary of the cell measure variable's netCDF attributes.

    f: `Field`

:Returns:

    out: `CellMeasure` or `FieldAncillary`
        The new item.

        '''
        g = self.read_vars
                
        if cell_measure:
            item = self._CellMeasure(properties=attributes[ncvar])
        elif field_ancillary:
            item = self._FieldAncillary(properties=attributes[ncvar])
    
        data = self._set_Data(ncvar, item)
    
        item.set_data(data, copy=False)
    
        item.set_ncvar(ncvar)
    
        return item
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
    
    def _create_grid_mapping_ref(self, f, grid_mapping,
                                      attributes, ncvar_to_key):
        '''
    
:Parameters:

    f: `Field`

    grid_mapping: `str`
        The value of a CF grid_mapping attribute.

    attributes: `dict`

    ncvar_to_key: `dict`

:Returns:

    `None`

        '''
        g = self.read_vars
                
        if ':' not in grid_mapping:
            grid_mapping = '{0}:'.format(grid_mapping)

        coordinates = []
        for x in re.sub('\s*:\s*', ': ', grid_mapping).split()[::-1]:
            qwerty = False
            if not x.endswith(':'):
                try:
                    coordinates.append(ncvar_to_key[x])
                    qwerty = True
                except KeyError:
                    continue
            else:
                if not coordinates:
                    coordinates = None
    
                grid_mapping = x[:-1]
    
                if grid_mapping not in attributes:
                    coordinates = []      
                    continue
                    
                parameters = attributes[grid_mapping].copy()

                props = {}
                name = parameters.pop('grid_mapping_name', None)                 
                if name is not None:
                    props['grid_mapping_name'] = name
                
                if not qwerty:
                    coordinates = []
                    for x in self._CoordinateReference._name_to_coordinates.get(name, ()):
                        for key, coord in f.coordinates().iteritems():
                            if x == coord.get_property('standard_name', None):
                                coordinates.append(key)
                #--- End: if
                
                coordref = self._CoordinateReference(properties=props,
                                                     coordinates=coordinates,
                                                     parameters=parameters)
                coordref.set_ncvar(grid_mapping)

                f.set_coordinate_reference(coordref, copy=False)
    
                coordinates = []      
        #--- End: for
    
        f.del_property('grid_mapping')
    #--- End: def
    
    def _create_formula_terms_ref(self, f, key, coord,
                                       formula_terms, domain_ancillaries):
        '''
    
:Parameters:

    f: `Field`

    key: `str`

    coord: `Coordinate`

    formula_terms: `dict`
        The formula_terms attribute value from the netCDF file.

    coordref_parameters: `dict`

:Returns:

    out: `CoordinateReference`
    
    '''
        g = self.read_vars

#        parameters  = {}
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

        props = {}
        name = coord.get_property('standard_name', None)
        if name is not None:
            props['standard_name'] = name

        coordref = self._CoordinateReference(properties=props,
                                             coordinates=(key,),
                                             domain_ancillaries=ancillaries)
    
        f.set_coordinate_reference(coordref, copy=False)
    
        return coordref
    #--- End: def
    
    def _set_Data(self, ncvar, variable=None, unpacked_dtype=False,
                  uncompress_override=None, units=None, calendar=None,
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
    
        filearray = self._NetCDF(filename=g['filename'], ncvar=ncvar,
                                 dtype=dtype, ndim=ndim, shape=shape,
                                 size=size)
    
        # Find the units for the data
        if units is None:
            try:
                units = ncvariable.getncattr('units')
            except AttributeError:
                units = None

        if calendar is None:
            try:
                calendar = ncvariable.getncattr('calendar')
            except AttributeError:
                calendar = None
            
        # Find the fill_value for the data
        if fill_value is None:
            fill_value = variable.fill_value()
            
        compression = g['compression']
    
        if ((uncompress_override is not None and not uncompress_override) or
            not g['compression'] or 
            not g['uncompress'] or
            not set(compression).intersection(ncvariable.dimensions)):        
            # --------------------------------------------------------
            # The array is not compressed
            # --------------------------------------------------------
            data = self._create_Data(filearray, units=units,
                                     calendar=calendar,
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
    
                        empty_data = self._Data.compression_initialize_gathered(uncompressed_shape)
    
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
    
                        data = self._Data.compression_fill_gathered(empty_data,
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
    
                        data = self._Data.compression_fill_indexed_contiguous(
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
                                            
                        data = self._Data.compression_fill_contiguous(
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
                        
                        data = self._Data.compression_fill_indexed(
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

    def _create_Data(self, array=None, units=None, calendar=None,
                          fill_value=None):
        '''
        '''
        return self._Data(array, units=units, calendar=calendar,
                          fill_value=fill_value)
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
    
#--- End: class
