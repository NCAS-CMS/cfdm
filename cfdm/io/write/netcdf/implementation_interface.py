class API(object):
    '''
    '''
   
    def _write_field(self, f, add_to_seen=False,
                     allow_data_expand_dims=True):
        '''
    
:Parameters:

    f : `Field`

    add_to_seen : bool, optional

    allow_data_expand_dims: `bool`, optional

:Returns:

    `None`

        '''
        g = self.write_vars
        
        _debug = g['_debug']
        if _debug:
            print '  Writing', repr(f)+':'

        xxx = []
            
        seen = g['seen']
          
        if add_to_seen:
            id_f = id(f)
            org_f = f
            
        f = self.copy_field(f)
    
        data_axes = self.get_data_axes(f)
    
        # Mapping of domain axis identifiers to netCDF dimension
        # names. This gets reset for each new field that is written to
        # the file.
        g['axis_to_ncdim'] = {}
    
        # Mapping of domain axis identifiers to netCDF scalar
        # coordinate variable names
        g['axis_to_ncscalar'] = {}
    
        # Mapping of field component internal identifiers to netCDF
        # variable names
        #
        # For example: {'dimensioncoordinate1': 'longitude'}
        g['key_to_ncvar'] = {}
    
        # Initialize the list of the field's auxiliary/scalar coordinates
        coordinates = []

        g['formula_terms_refs'] = [
            ref for ref in self.get_coordinate_references(f).values()
            if self.get_coordinate_conversion_parameters(ref).get('standard_name', False)]

        g['grid_mapping_refs'] = [
            ref for ref in self.get_coordinate_references(f).values()
            if self.get_coordinate_conversion_parameters(ref).get('grid_mapping_name', False)]

        field_coordinates = self.get_coordinates(f)
                        
        owning_coordinates = []
        standard_names = []
        computed_standard_names = []
        for ref in g['formula_terms_refs']:
            coord_key = None

            standard_name = self.get_coordinate_conversion_parameters(ref).get(
                'standard_name')
            computed_standard_name = self.get_coordinate_conversion_parameters(ref).get(
                'computed_standard_name')
            
            if standard_name is not None and computed_standard_name is not None:
                for key in self.get_coordinate_reference_coordinates(ref):
                    coord = field_coordinates[key]

                    if not (self.get_ndim(coord) == 1 and                        
                            self.get_property(coord, 'standard_name', None) == standard_name):
                        continue
                    
                    if coord_key is not None:
                        coord_key = None
                        break

                    coord_key = key
            #--- End: if
                
            owning_coordinates.append(coord_key)
            standard_names.append(standard_name)
            computed_standard_names.append(computed_standard_name)
        #--- End: for

        for key, csn in zip(owning_coordinates, computed_standard_names):
            if key is None:
                continue
            
            x = self.get_property(coord, 'computed_standard_name', None)
            if x is None:
                self.set_property(field_coordinates[key], 'computed_standard_name', csn)
            elif x != csn:
                raise ValueError(";sdm p8whw=0[")
        #--- End: for
        
        dimension_coordinates = self.get_dimension_coordinates(f)
        
        # For each of the field's axes ...
        for axis in sorted(self.get_domain_axes(f)):
            found_dimension_coordinate = False
            for key, dim_coord in dimension_coordinates.iteritems():
                if self.get_construct_axes(f, key) != (axis,):
                    continue

                # --------------------------------------------------------
                # Still here? Then a dimension coordinate exists for
                # this domain axis.
                # --------------------------------------------------------
                if axis in data_axes:
                    # The data array spans this domain axis, so write
                    # the dimension coordinate to the file as a
                    # coordinate variable.
                    ncvar = self._write_dimension_coordinate(f, key, dim_coord)
                else:
                    # The data array does not span this axis (and
                    # therefore it must have size 1).
                    if len(self.get_constructs(f, axes=[axis])) >= 2:
                        # There ARE auxiliary coordinates, cell
                        # measures, domain ancillaries or field
                        # ancillaries which span this domain axis, so
                        # write the dimension coordinate to the file
                        # as a coordinate variable.
                        ncvar = self._write_dimension_coordinate(f, key, dim_coord)
    
                        # Expand the field's data array to include
                        # this domain axis
                        f = self.expand_dims(f, position=0, axis=axis, copy=False) 
                    else:
                        # There are NO auxiliary coordinates, cell
                        # measures, domain ancillaries or field
                        # ancillaries which span this domain axis, so
                        # write the dimension coordinate to the file
                        # as a scalar coordinate variable.
                        coordinates = self._write_scalar_coordinate(f, axis, dim_coord,
                                                                    coordinates)
                #-- End: if

                found_dimension_coordinate = True
                break
            #--- End: for

            if not found_dimension_coordinate:
                # --------------------------------------------------------
                # There is no dimension coordinate for this axis
                # --------------------------------------------------------
                spanning_constructs = self.get_constructs(f, axes=[axis])
                
                if axis not in data_axes and spanning_constructs:
                    # The data array doesn't span the domain axis but
                    # an auxiliary coordinate, cell measure, domain
                    # ancillary or field ancillary does, so expand the
                    # data array to include it.
                    f = self.expand_dims(f, position=0, axis=axis, copy=False)
                    data_axes.append(axis)
    
                # If the data array (now) spans this domain axis then create a
                # netCDF dimension for it
                if axis in data_axes:
                    axis_size0 = self.get_domain_axis_size(f, axis)
                
                    use_existing_dimension = False

                    if spanning_constructs:
                        for key, construct in spanning_constructs.items():
                            axes = self.get_construct_axes(f, key)
                            spanning_constructs[key] = (construct, axes.index(axis))
                        
                        for b1 in g['xxx']:
                            (ncdim1,  axis_size1),  constructs1 = b1.items()[0]
                            if axis_size0 != axis_size1:
                                continue
    
                            if not constructs1:
                                continue

                            constructs1 = constructs1.copy()
                            
                            for key0, (construct0, index0) in spanning_constructs.iteritems():
                                matched_construct = False
                                for key1, (construct1, index1) in constructs1.iteritems():
                                    if index0 == index1 and construct0.equals(construct1):
                                        del constructs1[key1]
                                        matched_construct = True
                                        break
                                #--- End: for        
        
                                if not matched_construct:
                                    break
                            #--- End: for
                            
                            if not constructs1:
                                use_existing_dimension = True
                                break
                        #--- End: for
                    #--- End: if
    
                    if use_existing_dimension:
                        g['axis_to_ncdim'][axis] = ncdim1
                    else:
                        ncdim = self.get_ncdim(f, axis, 'dim')
                        ncdim = self._netcdf_name(ncdim)
    
                        unlimited = self.unlimited(f, axis)
                        self._write_dimension(ncdim, f, axis, unlimited=unlimited)
                        
                        xxx.append({(ncdim, axis_size0): spanning_constructs})
            #--- End: if    
        #--- End: for
    
        # ----------------------------------------------------------------
        # Create auxiliary coordinate variables, except those which might
        # be completely specified elsewhere by a transformation.
        # ----------------------------------------------------------------
        # Initialize the list of 'coordinates' attribute variable values
        # (each of the form 'name')
        for key, aux_coord in sorted(self.get_auxiliary_coordinates(f).iteritems()):
#            if self.is_geometry(aux_coord):
#                coordinates = self._write_geometry_coordinate(f, key, aux_coord,
#                                                              coordinates)

            coordinates = self._write_auxiliary_coordinate(f, key, aux_coord,
                                                           coordinates)
    
        # ------------------------------------------------------------
        # Create netCDF variables from domain ancillaries
        # ------------------------------------------------------------
        for key, anc in sorted(self.get_domain_ancillaries(f).iteritems()):
            self._write_domain_ancillary(f, key, anc)
    
        # ------------------------------------------------------------
        # Create netCDF variables from cell measures 
        # ------------------------------------------------------------
        # Set the list of 'cell_measures' attribute values (each of
        # the form 'measure: name')
        cell_measures = [self._write_cell_measure(f, key, msr)
                         for key, msr in sorted(self.get_cell_measures(f).iteritems())]
        
        # ------------------------------------------------------------
        # Create netCDF formula_terms attributes from vertical
        # coordinate references
        # ------------------------------------------------------------
        for ref in g['formula_terms_refs']:
            formula_terms = []
            bounds_formula_terms = []
            owning_coord = None

            standard_name = self.get_coordinate_conversion_parameters(ref).get('standard_name')
            if standard_name is not None:
#                c = [(key, coord) for key, coord in self.get_coordinates(f).items()
#                     if self.get_property(coord, 'standard_name', None) == standard_name]
                c = []
                for key in self.get_coordinate_reference_coordinates(ref):
                    coord = self.get_coordinates(f)[key]
                    if self.get_property(coord, 'standard_name', None) == standard_name:
                        c.append((key, coord))

                if len(c) == 1:
                    owning_coord_key, owning_coord = c[0]
            #--- End: if
    
            z_axis = self.get_construct_axes(f, owning_coord_key)[0]
                
            if owning_coord is not None:
                # This formula_terms coordinate reference matches up with
                # an existing coordinate
    
                for term, value in self.get_coordinate_conversion_parameters(ref).iteritems():
                    if value is None:
                        continue
    
                    if term in ('standard_name', 'computed_standard_name'):
                        continue
    
                    ncvar = self._write_scalar_data(value, ncvar=term)
    
                    formula_terms.append('{0}: {1}'.format(term, ncvar))
                    bounds_formula_terms.append('{0}: {1}'.format(term, ncvar))
                #--- End: for
            
                for term, key in ref.coordinate_conversion.domain_ancillaries().iteritems(): # DCH ALERT
                    if key is None:
                        continue
    
                    domain_anc = self.get_domain_ancillaries(f)[key]
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
                        if z_axis not in self.get_construct_axes(f, key):
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
                    print '    Writing formula_terms to netCDF variable', ncvar+':', repr(formula_terms)
    
                # Add the formula_terms attribute to the parent
                # coordinate bounds variable
                bounds_ncvar = g['bounds'].get(ncvar)
                if bounds_ncvar is not None:
                    bounds_formula_terms = ' '.join(bounds_formula_terms)
                    g['nc'][bounds_ncvar].setncattr('formula_terms', bounds_formula_terms)
                    if g['_debug']:
                        print '    Writing formula_terms to netCDF bounds variable', bounds_ncvar+':', repr(bounds_formula_terms)
            #--- End: if
                        
            # Deal with a vertical datum
            if owning_coord_key is not None:
                self._create_vertical_datum(ref, owning_coord_key)
        #--- End: for
    
        # ------------------------------------------------------------
        # Create netCDF variables grid mappings
        # ------------------------------------------------------------
        multiple_grid_mappings = (len(g['grid_mapping_refs']) > 1)
        
        grid_mapping = [self._write_grid_mapping(f, ref, multiple_grid_mappings)
                        for ref in g['grid_mapping_refs']]
        
        # ----------------------------------------------------------------
        # Field ancillary variables
        # ----------------------------------------------------------------
        # Create the 'ancillary_variables' CF-netCDF attribute and create
        # the referenced CF-netCDF ancillary variables
        ancillary_variables = [self._write_field_ancillary(f, key, anc)
                               for key, anc in self.get_field_ancillaries(f).iteritems()]
    
        # ----------------------------------------------------------------
        # Create the CF-netCDF data variable
        # ----------------------------------------------------------------
        ncvar = self._create_netcdf_variable_name(f, default='data')
    
        ncdimensions = tuple([g['axis_to_ncdim'][axis] for axis in self.get_data_axes(f)])
    
        extra = {}

        # Cell measures
        if cell_measures:
            cell_measures = ' '.join(cell_measures)
            if _debug:
                print '    Writing cell_measures to netCDF variable', ncvar+':', cell_measures
                
            extra['cell_measures'] = cell_measures
            
        # Auxiliary/scalar coordinates
        if coordinates:
            coordinates = ' '.join(coordinates)
            if _debug:
                print '    Writing coordinates to netCDF variable', ncvar+':', coordinates
                
            extra['coordinates'] = coordinates
    
        # Grid mapping
        if grid_mapping:
            grid_mapping = ' '.join(grid_mapping)
            if _debug:
                print '    Writing grid_mapping to netCDF variable', ncvar+':', grid_mapping
                
            extra['grid_mapping'] = grid_mapping
    
        # Ancillary variables
        if ancillary_variables:
            ancillary_variables = ' '.join(ancillary_variables)
            if _debug:
                print '    Writing ancillary_variables to netCDF variable', ncvar+':', ancillary_variables

            extra['ancillary_variables'] = ancillary_variables
            
#        # Flag values
#        if hasattr(f, 'flag_values'):
#            extra['flag_values'] = f.flag_values
#    
#        # Flag masks
#        if hasattr(f, 'flag_masks'):
#            extra['flag_masks'] = f.flag_masks
#    
#        # Flag meanings
#        if hasattr(f, 'flag_meanings'):
#            extra['flag_meanings'] = f.flag_meanings
    
        # name can be a dimension of the variable, a scalar coordinate
        # variable, a valid standard name, or the word 'area'
        cell_methods = self.get_cell_methods(f)
        if cell_methods:
            axis_map = g['axis_to_ncdim'].copy()
            axis_map.update(g['axis_to_ncscalar'])

            cell_methods_strings = []
            for cm in cell_methods.values():
                axes = [axis_map.get(axis, axis)
                        for axis in self.get_cell_method_axes(cm, ())]
                self.set_cell_method_axes(cm, axes)
                cell_methods_strings.append(self.get_cell_method_string(cm))

            cell_methods = ' '.join(cell_methods_strings)
            if _debug:
                print '    Writing cell_methods to netCDF variable', ncvar+':', cell_methods

            extra['cell_methods'] = cell_methods
            
        # Create a new data variable
        self._write_netcdf_variable(ncvar, ncdimensions, f,
                                    omit=g['global_properties'],
                                    extra=extra)
        
        # Update the 'seen' dictionary, if required
        if add_to_seen:
            seen[id_f] = {'variable': org_f,
                          'ncvar'   : ncvar,
                          'ncdims'  : ncdimensions}

        if xxx:
            g['xxx'].extend(xxx)
    #--- End: def

    def _create_vertical_datum(self, ref, coord_key):
        '''
        '''
        # Deal with a vertical datum
        g = self.write_vars

        datum = self.get_datum(ref)
        if not datum:
            return
            
        if g['_debug']:
            print '    Datum =', datum
            
#        domain_ancillaries = self.get_datum_ancillaries(ref)

        count = [0, None]
        for grid_mapping in g['grid_mapping_refs']:
            datum1 = self.get_datum(grid_mapping)
            if not datum1:
                continue

#            domain_ancillaries1 = self.get_datum_ancillaries(
#                grid_mapping)
                 
            if datum.equals(datum1):
                count = [count[0] + 1, grid_mapping]
                if count[0] > 1:
                    break
                
#            if (datum.equals(datum1) and
#                domain_ancillaries == domain_ancillaries1):
#                count = [count[0] + 1, grid_mapping]
#                if count[0] > 1:
#                    break
        #--- End: for

        if count[0] == 1:
            # Add the vertical coordinate to an existing
            # horizontal coordinate reference
            grid_mapping = count[1]
            self.set_coordinate_reference_coordinate(grid_mapping,
                                                     coord_key)
        else:
            # Create a new horizontal coordinate reference for
            # the vertical datum
            new_grid_mapping = self.initialise( # DCH ALERT
                'CoordinateReference',
                coordinates=[coord_key],
                datum_parameters=self.get_datum_parameters(ref),
#                datum_domain_ancillaries=domain_ancillaries)
                )
            
            g['grid_mapping_refs'].append(new_grid_mapping)
    #--- End: def
                            
    def unlimited(self, field, axis):
        '''

:Parameters:
  
    field: `Field`

    axis: `str`
   
:Returns:

    out: `bool`

        '''
        g = self.write_vars

        unlimited = field.unlimited().get(axis)
    
        if unlimited is None:
            unlimited = False
            for u in g['unlimited']:
                if field.axis(u, key=True) == axis:
                    unlimited = True
                    break
        #--- End: if
        
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
#            for attr in set(f._simple_properties()) - global_properties - g['variable_attributes']:
            for attr in set(f.properties()) - global_properties - g['variable_attributes']: # DCH CHECK
                if attr not in data_properties:
                    global_properties.add(attr)
        #--- End: for
    
        # Remove properties from the new global_properties set which
        # have different values in different fields
        f0 = fields[0]
        for prop in tuple(global_properties):
            if not self.has_property(f0, prop):
                global_properties.remove(prop)
                continue
                
            prop0 = self.get_property(f0, prop)
    
            if len(fields) > 1:
                for f in fields[1:]:
                    if (not self.has_property(f, prop) or 
                        not equals(self.get_property(f, prop), prop0, traceback=False)):
                        global_properties.remove(prop)
                        break
        #--- End: for
    
        # Write the global properties to the file
#        g['netcdf'].setncattr('Conventions', g['Conventions'])
        g['netcdf'].setncattr('Conventions', self.implementation.get_version())
        
        for attr in global_properties - set(('Conventions',)):
            g['netcdf'].setncattr(attr, self.get_property(f0, attr)) 
    
        g['global_properties'] = global_properties
    #--- End: def

    @staticmethod
    def copy_field(field):
        '''

:Parameters:

    field: 

:Returns:

    out:

        '''
        return field.copy()
    #--- End: def

    @staticmethod
    def equal_constructs(construct0, construct1, ignore_construct_type=False):
        '''
        '''    
        return construct0.equals(construct1, ignore_construct_type=ignore_construct_type)
    #--- End: def
    

    @staticmethod
    def expand_dims(construct, position=0, axis=None, copy=True):
        '''
        '''
        return construct.expand_dims(position=position, axis=axis, copy=copy)
    #--- End: def

    def file_close(self, filename):
        '''Close the netCDF file that has been written.

:Returns:

    `None`

        '''
        self.write_vars['netcdf'].close()
    #--- End: def

    def file_open(self, filename, mode, fmt):
        '''Open the netCDF file for writing.
        
:Returns:
        
    out: `netCDF.Dataset`
        
        '''
        try:        
            nc = netCDF4.Dataset(filename, mode, format=fmt)
        except RuntimeError as error:
            raise RuntimeError("{}: {}".format(error, filename))        
        else:
            return nc
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

    @staticmethod
    def get_array(data):
        '''
        '''
        return data.get_array()
    #--- End: def

    @staticmethod
    def get_auxiliary_coordinates(field):
        '''
        '''
        return field.auxiliary_coordinates()
    #--- End: def

    @staticmethod
    def get_bounds(construct, *default):
        '''
        '''
        return construct.get_bounds(*default)
    #--- End: def

    @staticmethod
    def get_cell_measures(field):
        '''
        '''
        return field.cell_measures()
    #--- End: def
        
    @staticmethod
    def get_cell_methods(field):
        '''
        '''
        return field.cell_methods()
    #--- End: def
       
    @staticmethod
    def get_cell_method_axes(cell_method, *default):
        '''

:Returns:

    out: `tuple`
'''
        return cell_method.get_axes(*default)
    #--- End: for
    
    @staticmethod
    def get_cell_method_string(cell_method):
        '''
:Returns:

    out: `str`
'''
        return str(cell_method)
    #--- End: for

    @staticmethod
    def is_climatology(coordinate):
        '''

:Returns:

    out: `bool`
        The value of the 'climatology' cell extent parameter, or False
        if not set.

        '''
#        return coordinate.bounds_mapping.get_parameter('climatology', False)
        return bool(coordinate.get_geometry_type(None) == 'climatology')
    #--- End: def

    @staticmethod
    def get_construct_axes(field, key):
        '''
        '''
        return field.construct_axes(key)
    
    @staticmethod
    def get_constructs(field, axes=None):
        return field.constructs(axes=axes)

    @staticmethod
    def get_coordinate_reference_coordinates(coordinate_reference):
        '''Return the coordinates of a coordinate reference object.

:Parameters:

    coordinate_reference: `CoordinateReference`

:Returns:

    out: `set`

        '''
        return coordinate_reference.coordinates()
    #--- End: def
    
    @staticmethod
    def get_coordinate_conversion_parameters(coordinate_reference):
        '''

:Returns:

    out: `dict`

        '''
        return coordinate_reference.get_coordinate_conversion().parameters()
    #--- End: def

    @staticmethod
    def get_coordinate_references(field):
        '''
        '''
        return field.coordinate_references()
    #--- End: def

    @staticmethod
    def get_coordinates(field):
        '''
        '''
        return field.coordinates()
    #--- End: def

    @staticmethod
    def get_data(parent, *default):
        '''Return the data array.

:Examples 1:

>>> data = w.get_data(x)

:Parameters:

    parent: 
        The object containing the data array.

:Returns:

    out: 
        The data array.

:Examples 2:

>>> d
<DimensionCoordinate: latitude(180) degrees_north>
>>> w.get_data(d)
<Data: [-89.5, ..., 89.5] degrees_north>

>>> b
<Bounds: latitude(180, 2) degrees_north>
>>> w.get_data(b)
<Data: [[-90, ..., 90]] degrees_north>
        '''
        return parent.get_data(*default)
    #--- End: def

    @staticmethod
    def get_data_axes(field):
        '''
        '''
        return field.get_data_axes()
    #--- End: def

    @staticmethod
    def get_domain_ancillaries(field):
        '''
        '''
        return field.domain_ancillaries()

    @staticmethod
    def get_domain_axes(field):
        '''
        '''
        return field.domain_axes()
        
    @staticmethod
    def get_domain_axis_size(field, axis):
        '''
        '''
        return self.get_domain_axes(field)[axis].get_size()

    @staticmethod
    def get_datum(coordinate_reference):
        '''

:Returns:

    out: `dict`

        '''
        return coordinate_reference.get_datum()
    #--- End: def

#    def get_datum_ancillaries(self, coordinate_reference):
#        '''Return the domain ancillary-valued terms of a coordinate reference
#datum.
#
#:Parameters:
#
#    coordinate_reference: `CoordinateReference`
#
#:Returns:
#
#    out: `dict`
#        '''        
#        return self.get_datum(coordinate_reference).ancillaries()
#    #--- End: def
        
    @staticmethod
    def get_datum_parameters(coordinate_reference):
        '''Return the parameter-valued terms of a coordinate reference datum.

:Parameters:

    coordinate_reference: `CoordinateReference`

:Returns:

    out: `dict`

        '''        
        return self.get_datum(coordinate_reference).parameters()
    #--- End: def

    @staticmethod
    def get_dimension_coordinates(field):
        '''
        '''
        return field.dimension_coordinates()
    #--- End: def

    @staticmethod
    def get_external(parent):
        '''Return whether a construct is external.

:Examples 1:

:Parameters:

    parent: 
        The object

    default: optional

:Returns:

    out: `bool`
        Whether the construct is external.

:Examples 2:
        '''
        return parent.get_external()
    #--- End: def

    @staticmethod
    def get_field_ancillaries(field):
        '''Return the field ancillaries of a field.

:Examples 1:

>>> field_ancillaries = w.get_field_ancillaries(f)

:Parameters:

    field: 
        The field object.

:Returns:

    out: `dict`
        The field ancillary objects, keyed by their internal identifiers.

:Examples 2:

>>> w.get_field_ancillaries(f)
{'fieldancillary0': <FieldAncillary: >,
 'fieldancillary1': <FieldAncillary: >}
        '''
        return field.field_ancillaries()
    #--- End: def

    @staticmethod
    def get_measure(cell_measure):
        '''Return the measure property of a cell measure contruct.

:Examples 1:

>>> measure = w.get_measure(c)

:Parameters:

    cell_measure:
        The cell measure object.

:Returns:

    out: `str` or `None`
        The measure property, or `None` if it has not been set.

:Examples 2:

>>> c
<CellMeasure: area(73, 96) km2>
>>> w.get_measure(c)
'area'
        '''
        return cell_measure.get_measure(None)
    #--- End: def

    @staticmethod
    def get_ncvar(parent, *default):
        '''Return the netCDF variable name.

:Examples 1:

>>> ncvar = w.get_ncvar(x)

:Parameters:

    parent: 
        The object containing the data array.

    default: `str`, optional

:Returns:

    out: 
        The netCDF variable name.

:Examples 2:

>>> d
<DimensionCoordinate: latitude(180) degrees_north>
>>> w.get_ncvar(d)
'lat'

>>> b
<Bounds: latitude(180, 2) degrees_north>
>>> w.get_ncvar(b)
'lat_bnds'

>>> w.get_ncvar(x)
AttributeError: Can't get non-existent 'ncvar'
>>> w.get_ncvar(x, 'newname')
'newname'
        '''
        return parent.get_ncvar(*default)
    #--- End: def

    @staticmethod
    def get_ncdim(self, field, axis, *default):
        '''Return the netCDF variable name.

:Examples 1:

>>> ncdim = w.get_ncdim(x)

:Parameters:

    parent: 
        The object containing the data array.

    default: `str`, optional

:Returns:

    out: 
        The netCDF dimension name.

:Examples 2:
        '''
        return field.get_domain_axis()[axis].get_ncdim(*default)
    #--- End: def

    @staticmethod
    def get_ndim(parent):
        '''Return the number of dimensions spanned by the data array.

:Parameters:

    parent: 
        The object containing the data array.

:Returns:

    out: int
        The number of dimensions spanned by the data array.

:Examples 1:

>>> ndim = w.get_ndim(x)

:Examples 2:

>>> d
<DimensionCoordinate: latitude(180) degrees_north>
>>> w.get_ndim(d)
1

>>> b
<Bounds: latitude(180, 2) degrees_north>
>>> w.get_ndim(b)
2
        '''
        return parent.ndim
    #--- End: def

    @staticmethod
    def get_properties(parent):
        '''Return all properties.

:Parameters:

    parent: 
        The object containing the properties.

:Returns:

    out: `dict`
        The property names and their values

:Examples 1:

>>> properties = w.get_properties(x)

:Examples 2:

>>> d
<DimensionCoordinate: latitude(180) degrees_north>
>>> w.get_properties(d)
{'units: 'degrees_north'}
 'standard_name: 'latitude',
 'foo': 'bar'}
        '''
        return parent.properties()
    #--- End: def

    @staticmethod
    def get_property(parent, prop, *default):
        '''Return a property value.

:Parameters:

    parent: 
        The object containing the property.

:Returns:

    out: 
        The value of the property.

:Examples 1:

>>> value = w.get_property(x, 'standard_name')

:Examples 2:

>>> d
<DimensionCoordinate: latitude(180) degrees_north>
>>> w.get_property(d, 'units')
'degees_north'

>>> b
<Bounds: latitude(180, 2) degrees_north>
>>> w.get_property(b, 'long_name')
'Latitude Bounds'

>>> w.get_property(x, 'foo')
AttributeError: Can't get non-existent property 'foo'
>>> w.get_property(x, 'foo', 'bar')
'bar'
        '''
        return parent.get_property(prop, *default)
    #--- End: def
    
    @staticmethod
    def get_shape(self, parent):
        '''Return the shape of the data array.

:Parameters:

    parent: 
        The object containing the data array.

:Returns:

    out: tuple
        The shape of the data array.

:Examples 1:

>>> shape = w.get_shape(x)

:Examples 2:

>>> d
<DimensionCoordinate: latitude(180) degrees_north>
>>> w.get_shape(d)
(180,)

>>> b
<Bounds: latitude(180, 2) degrees_north>
>>> w.get_shape(b)
(180, 2)

        '''
        return parent.shape
    #--- End: def

    @staticmethod
    def has_property(parent, prop):
        '''Return True if a property exists.

:Examples 1:

>>> has_standard_name = w.has_property(x, 'standard_name')

:Parameters:

    parent: 
        The object containing the property.

:Returns:

    out: `bool`
        `True` if the property exists, otherwise `False`.

:Examples 2:

>>> coord
<DimensionCoordinate: latitude(180) degrees_north>
>>> w.has_property(coord, 'units')
True

>>> bounds
<Bounds: latitude(180, 2) degrees_north>
>>> w.has_property(bounds, 'long_name')
False
        '''
        return parent.has_property(prop)
    #--- End: def

    def initialise(self, class_name, **kwargs):
        '''
        '''
        return self.implementation.get_class(class_name)(**kwargs)
    #--- End: def

    @staticmethod
    def set_cell_method_axes(cell_method, axes):
        '''
'''
        cell_method.set_axes(axes)
    #--- End: for
    
    @staticmethod
    def set_property(construct, name, value):
        '''
        '''
        construct.set_property(name, value)
    #--- End: def

    @staticmethod
    def set_coordinate_reference_coordinate(coordinate_reference,
                                            coordinate):
        '''
        '''
        coordinate_reference.set_coordinate(coordinate)
    #--- End: def

    @staticmethod
    def squeeze(construct, axes=None, copy=True):
        '''
        '''
        return construct.squeeze(axes=axes, copy=copy)
    #--- End: def
        
#--- End: class
