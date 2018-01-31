from collections import abc

#import os
#
#from csv  import reader as csv_reader
#from re   import match as re_match

#from .          import __file__
#from .functions import RTOL, ATOL, equals, allclose
#from .units     import Units

import .abstract

## --------------------------------------------------------------------
## Map coordinate conversion names to their CF-netCDF types
## --------------------------------------------------------------------
#_cf_types = {}
#_file = os.path.join(os.path.dirname(__file__),
#                     'etc/coordinate_reference/type.txt')
#for x in csv_reader(open(_file, 'r'), delimiter=' ', skipinitialspace=True):
#    if not x or x[0] == '#':
#        continue
#    _cf_types[x[0]] = x[1]
#
## --------------------------------------------------------------------
## Map coordinate conversion names to the set of coordinates to which
## they apply
## --------------------------------------------------------------------
#_name_to_coordinates = {}
#_file = os.path.join(os.path.dirname(__file__),
#                     'etc/coordinate_reference/coordinates.txt')
#for x in csv_reader(open(_file, 'r'), delimiter=' ', skipinitialspace=True):
#    if not x or x[0] == '#':
#        continue
#    _name_to_coordinates[x[0]] = set(x[1:])
#
## --------------------------------------------------------------------
## Map coordinate conversion terms to their terms default values
## --------------------------------------------------------------------
#_default_values = {}
#_file = os.path.join(os.path.dirname(__file__),
#                     'etc/coordinate_reference/default_values.txt')
#for x in csv_reader(open(_file, 'r'), delimiter=' ', skipinitialspace=True):
#    if not x or x[0] == '#':
#        continue
#    _default_values[x[0]] = float(x[1])
#
### --------------------------------------------------------------------
### Map coordinate conversion terms to their canonical units
### --------------------------------------------------------------------
##_canonical_units = {}
##_file = os.path.join(os.path.dirname(__file__),
##                     'etc/coordinate_reference/canonical_units.txt')
##for x in csv_reader(open(_file, 'r'), delimiter=' ', skipinitialspace=True):
##    if not x or x[0] == '#':
##        continue
##    try:
##        _canonical_units[x[0]] = Units(x[1]) # DCH 
##    except:
##        _canonical_units[x[0]] = x[1]
#
## --------------------------------------------------------------------
## Map coordinate reference names to their terms which may take
## non-constant values (i.e. pointers to coordinate objects or
## non-scalar field objects).
## --------------------------------------------------------------------
#_non_constant_terms = {}
#_file = os.path.join(os.path.dirname(__file__),
#                     'etc/coordinate_reference/non_constant_terms.txt')
#for x in csv_reader(open(_file, 'r'), delimiter=' ', skipinitialspace=True):
#    if not x or x[0] == '#' or len(x) == 1:
#        continue
#    _non_constant_terms[x[0]] = set(x[1:])


# ====================================================================
#
# CoordinateReference object
#
# ====================================================================

#_units = {}

class CoordinateReference(abstract.Properties):
    '''A coordinate reference construct of the CF data model. 

The domain of a field construct may contain various coordinate
systems, each of which is constructed from a subset of the dimension
and auxiliary coordinate constructs. For example, the domain of a
four-dimensional field construct may contain horizontal (y–x),
vertical (z), and temporal (t) coordinate systems. There may be more
than one of each of these, if there is more than one coordinate
construct applying to a particular spatiotemporal dimension (for
example, there could be both latitude–longitude and y–x projection
coordinate systems). In general, a coordinate system may be
constructed implicitly from any subset of the coordinate constructs,
yet a coordinate construct does not need to be explicitly or
exclusively associated with any coordinate system.

A coordinate system of the field construct can be explicitly defined
by a coordinate reference construct which relates the coordinate
values of the coordinate system to locations in a planetary reference
frame and consists of the following:

  * The dimension coordinate and auxiliary coordinate constructs that
    define the coordinate system to which the coordinate reference
    construct applies. Note that the coordinate values are not
    relevant to the coordinate reference construct, only their
    properties.

  * A definition of a datum specifying the zeroes of the dimension and
    auxiliary coordinate constructs which define the coordinate
    system. The datum may be explicitly indicated via properties, or
    it may be implied by the metadata of the contained dimension and
    auxiliary coordinate constructs. Note that the datum may contain
    the definition of a geophysical surface which corresponds to the
    zero of a vertical coordinate construct, and this may be required
    for both horizontal and vertical coordinate systems.

  * A coordinate conversion, which defines a formula for converting
    coordinate values taken from the dimension or auxiliary coordinate
    constructs to a different coordinate system. A term of the
    conversion formula can be a scalar or vector parameter which does
    not depend on any domain axis constructs, may have units (such as
    a reference pressure value), or may be a descriptive string (such
    as the projection name "mercator"), or it can be a domain
    ancillary construct (such as one containing spatially varying
    orography data) A coordinate reference construct relates the
    field's coordinate values to locations in a planetary reference
    frame.

    '''
    __metaclass__ = abc.ABCMeta
    
#    # Map coordinate conversion names to their CF-netCDF types
#    _cf_types = _cf_types
#    
#    # Map coordinate conversion names to their
#    _name_to_coordinates = _name_to_coordinates
#    
#    # Map coordinate conversion terms to their terms default values
#    _default_values = _default_values
#    
#    # Map coordinate conversion terms to their canonical units
#    _canonical_units = _canonical_units
#    
#    # Map coordinate reference names to their terms which may take
#    # non-constant values (i.e. pointers to coordinate objects or
#    # non-scalar field objects).
#    _non_constant_terms = _non_constant_terms
    
    def __init__(self, name=None, coordinates=None,
                 domain_ancillaries=None, parameters=None, datum=None,
                 source=None, copy=True):
        '''**Initialization**

:Parameters:

    name: `str`, optional
        A name which describes the nature of the coordinate
        conversion. This is usually a CF grid_mapping name or the
        standard name of a CF dimensionless vertical coordinate, but
        is not restricted to these.

          Example: To create a polar stereographic coordinate
          reference: ``name='polar_stereographic'``. To create
          coordinate reference for an ocean sigma over z coordinate:
          ``name='ocean_sigma_z_coordinate'``. To create new type of
          coordinate reference: ``name='my_new_type'``.

    crtype: `str`, optional
        The CF type of the coordinate reference. This is either
        ``'grid_mapping'`` or ``'formula_terms'``. By default the type
        is inferred from the *name*, if possible. For example:

        >>> c = CoordinateReference('transverse_mercator')
        >>> c.type
        'grid_mapping'

        >>> c = CoordinateReference('my_new_type', crtype='formula_terms')
        >>> c.type
        'formula_terms'

        >>> c = CoordinateReference('my_new_type')
        >>> print c.type
        None

        >>> c = CoordinateReference('my_new_type', crtype='grid_mapping')
        >>> print c.type
        'grid_mapping'

    coordinates: sequence of `str`, optional
        Identify the dimension and auxiliary coordinate objects which
        apply to this coordinate reference. By default the standard
        names of those expected by the CF conventions are used. For
        example:

        >>> c = CoordinateReference('transverse_mercator')
        >>> c.coordinates
        {'latitude', 'longitude', 'projection_x_coordinate', 'projection_y_coordinate'}

        >>> c = cf.CoordinateReference('transverse_mercator', coordinates=['ncvar%lat'])
        >>> c.coordinates
        {'ncvar%lat', 'latitude', 'longitude', 'projection_x_coordinate', 'projection_y_coordinate'}

        '''

        self._coordinates        = set()
        self._parameters         = {}
        self._domain_ancillaries = {}
        
        if source:
            if not isinstance(source, CoordinateReference):
                raise ValueError(
"ERROR: source must be a subclass of 'CoordinateReference'. Got {!r}".format(
    source.__class__.__name__))

#            # not structure
#            if crtype is None:
#                crtype = source.get_type(None)

            if coordinates is None:
                coordinates = source.coordinates()
            else:
                coordinates = set(coordinates)
                coordinates.update(source.coordinates())
                
            if datum is None:
                datum = source.get_datum(None)

            if name is None:
                name = source.get_name(None)
            
            if parameters is None:
                parameters = source.parameters()
            else:
                parameters = parameters.copy()
                parameters.update(source.parameters())

            if domain_ancillaries is None:
                domain_ancillaries = source.domain_ancillaries()
            else:
                domain_ancillaries = domain_ancillaries.copy()
                domain_ancillaries.update(source.domain_ancillaries())
        #--- End: if

#        # not structure
#        cf_type = self._cf_types.get(name, None)
#        if cf_type is not None:
#            if crtype is None:
#                crtype = cf_type
#            elif cf_type != crtype:
#                raise ValueError(" 888 askjdalsjkdnlaksjd lasdna")
#        #--- End: if
#        self._crtype = crtype
#        
#        if crtype == 'formula_terms':
#            self.set_term('parameter', 'standard_name', name)
#        elif crtype == 'grid_mapping':
#            self.set_term('parameter', 'grid_mapping_name', name)

        if coordinates is not None:
            for value in coordinates:
                self.insert_coordinate(value)
        
        if datum is not None:
            self.set_datum(datum)

        if name is not None:
            self.set_name(name)
                         
        if parameters is not None:
            for term, value in parameters.iteritems():
                self.set_parameter(term, value)
                
        if domain_ancillaries is not None: 
            for term, value in domain_ancillaries.iteritems():
                self.set_domain_ancillary(term, value)
    #--- End: def
   
    def __str__(self):
        '''x.__str__() <==> str(x)

        '''    
        return self.identity('')
    #--- End: def

#    def canonical(self, field=None):
#        '''
#'''
#        ref = self.copy()
#
#        for term, value in ref.parameters.iteritems():
#            if value is None or isinstance(value, basestring):
#                continue
#
#            canonical_units = self.canonical_units(term)
#            if canonical_units is None:
#                continue
#
#            if isinstance(canonical_units, basestring):
#                # units is a standard_name of a coordinate
#                if field is None:
#                    raise ValueError("Set the field parameter")
#                coord = field.coord(canonical_units)
#                if coord is not None:
#                    canonical_units = coord.Units
#
#            if canonical_units is not None:
#                units = getattr(value, 'Units', None)
#                if units is not None:
#                    if not canonical_units.equivalent(units):
#                        raise ValueError("xasdddddddddddddd 87236768")                
#                    value.Units = canonical_units
#        #--- End: for
#
#        return ref
#    #--- End: def

#    @classmethod
#    def canonical_units(cls, term):
#        '''Return the canonical units for a standard CF coordinate conversion
#term.
#
#:Parameters:
#
#    term: `str`
#        The name of the term.
#
#:Returns:
#
#    out: `Units` or `None`
#        The canonical units, or `None` if there are not any.
#
#:Examples:
#
#>>> print CoordinateReference.canonical_units('perspective_point_height')
#'m'
#>>> CoordinateReference.canonical_units('ptop')
#None
#
#        '''
#        return cls._canonical_units.get(term, None)
#    #--- End: def

    def coordinates(self):
        '''
        '''
        return self._get_attribute('coordinates').copy()
    #--- End: def

    def del_datum(self):
        '''
        '''
        return self._del_attribute('datum')
    #--- End: def
    
    def del_name(self):
        '''
        '''
        return self._del_attribute('name')
    #--- End: def
    
    def del_term(self, term)
        '''
        '''        
        d = self._get_attribute('domain_ancillaries')
        if term in d:
            return d.pop(term, None)
        
        d = self._get_attribute('parameters')
        if term in d:
            return d.pop(term, None)
    #--- End: def

    def domain_ancillaries(self):
        '''
        '''
        return self._get_attribute('domain_ancillaries').copy()
    #--- End: def

    def get_datum(self, *default):
        '''
        '''
        return self._get_attribute('datum', *default)
    #--- End: def

    def get_name(self, value, *default):
        '''
        '''
        self._get_attribute('name', *default)
    #--- End: def

    def get_term(self, term, *default):
        '''
        '''
        d = self._get_attribute('domain_ancillaries')
        if term not in d:
            d = self._get_attribute('parameters')

        if default:
            return d.get(term, default[0])

        try:
            return d[term]
        except KeyError:
            raise AttributeError("{} doesn't have formula term {}".format(
                self.__class__.__name__, term))
    #--- End: def
    
    def has_term(self, term):
        '''
        '''
        return (term in self._get_attribute('domain_ancillaries') or
                term in self._get_attribute('parameters'))
    #--- End: def

    def insert_coordinate(self, coordinate):
        '''
        '''
        c = self._get_attribute('coordinates')
        c.add(coordinate)
    #--- End: def

    def parameters(self):
        '''
        '''
        return self._get_attribute('parameters').copy()
    #--- End: def

    def remove_coordinate(self, coordinate):
        '''
        '''
        c = self._get_attribute('coordinates')
        c.discard(coordinate)
    #--- End: def
    
    def set_datum(self, value):
        '''
'''
        self._set_attribute('datum', value)
    #--- End: def

    def set_domain_ancillary(self, term, value):
        '''
        '''
        self._get_attribute('domain_ancillaries')[term] = value
    #--- End: def
    
    def set_name(self, value):
        '''
'''
        self._set_attribute('name', value)
    #--- End: def

    def set_parameter(self, term, value):
        '''
'''
        self._get_attribute('parameters')[term] = value
    #--- End: def
    
    def terms(self):
        '''
        '''
        out = self.parameters()
        out.update(self._get_attribute('domain_ancillaries'))
        return out
    #--- End: def
    
#    @classmethod
#    def default_value(cls, term):
#        '''
#
#Return the default value for an unset standard CF coordinate
#conversion term.
#
#The default values are stored in the file
#cf/etc/coordinate_reference/default_values.txt.
#
#:Parameters:	
#
#    term: `str`
#        The name of the term.
#
#:Returns:	
#
#    out: 
#        The default value.
#
#:Examples:
#
#>>> cf.CoordinateReference.default_value('ptop')
#0.0
#>>> print cf.CoordinateReference.default_value('north_pole_grid_latitude')
#0.0
#
#        '''
#        return cls._default_values.get(term, 0.0)
#    #--- End: def

    def type(self, *name):
        '''
        '''
        if not name:
            name = self._crtype
            return name
        #--- End: if

        name = name[0]
        self._crtype = name

        return name
    #--- End: def

    def identity(self, default=None):
        '''Return the identity of the coordinate reference.

The identity is the standard_name of a formula_terms-type coordinate
reference or the grid_mapping_name of grid_mapping-type coordinate
reference.

:Parameters:

    default: optional
        If the coordinate reference has no identity then return
        *default*. By default, *default* is None.

:Returns:

    out:
        The identity.

:Examples:

>>> r.identity()
'rotated_latitude_longitude'
>>> r.identity()
'atmosphere_hybrid_height_coordinate'

        '''
        return self.name(default=default, identity=True)
    #--- End: def

    def ncvar(self, *name):
        '''
        '''
        if not name:
            return self._ncvar

        name = name[0]
        self._ncvar = name

        return name
    #--- End: def
    
    def name(self, default=None, identity=False, ncvar=False):
        '''Return a name.

By default the name is the first found of the following:

  1. The `standard_name` CF property.
  
  2. The `!id` attribute.
  
  3. The `long_name` CF property, preceeded by the string
     ``'long_name:'``.
  
  4. The `!ncvar` attribute, preceeded by the string ``'ncvar%'``.
  
  5. The value of the *default* parameter.

Note that ``f.name(identity=True)`` is equivalent to ``f.identity()``.

.. seealso:: `identity`

:Examples 1:

>>> n = r.name()
>>> n = r.name(default='NO NAME'))
'''
        if not ncvar:
            parameter_terms = self.parameters

            n = parameter_terms.get('standard_name', None)
            if n is not None:
                return n
                
            n = parameter_terms.get('grid_mapping_name', None)
            if n is not None:
                return n
                
            if identity:
                return default

        elif identity:
            raise ValueError("Can't set identity=True and ncvar=True")

        n = self.ncvar()
        if n is not None:
            return 'ncvar%{0}'.format(n)
            
        return default
    #--- End: def

    def change_identifiers(self, identity_map, coordinate=True,
                           domain_ancillary=True, strict=False, copy=True):
        '''Change the

ntifier is not in the provided mapping then it is
set to `None` and thus effectively removed from the coordinate
reference.

:Parameters:

    identity_map: dict
        For example: ``{'dim2': 'dim3', 'aux2': 'latitude', 'aux4': None}``
        
    strict: `bool`, optional
        If True then coordinate or domain ancillary identifiers not
        set in the *identity_map* dictiontary are set to `None`. By
        default they are left unchanged.

    i: `bool`, optional

:Returns:

    `None`

:Examples:

>>> r = cf.CoordinateReference('atmosphere_hybrid_height_coordinate',
...                             a='ncvar%ak',
...                             b='ncvar%bk')
>>> r.coordinates
{'atmosphere_hybrid_height_coordinate'}
>>> r.change_coord_identitiers({'atmosphere_hybrid_height_coordinate', 'dim1',
...                             'ncvar%ak': 'aux0'})
>>> r.coordinates
{'dim1', 'aux0'}

        '''
        if copy:
            r = self.copy()
        else:
            r = self

        if not identity_map and not strict:
            return r

        if strict:
            default = None

        if domain_ancillary:
            for term, identifier in r._get_attribute('domain_ancillaries'):
                if not strict:
                    default = identifier

                self.set_domain_ancillary(term,
                                          identity_map.get(identifier, default))
        #--- End: if
        
        if coordinate:
            coordinates = []
            for identifier in r._get_attribute('coordinates'):
                if not strict:
                    default = identifier

                coordinates.append(identity_map.get(identifier, default))
            
            coordinates = set(coordinates)
            coordinates.discard(None)
            r._set_attribute('coordinates', coordinates)

        return r
    #---End: def

    def all_identifiers(self):
        '''
        '''
        return self.coordinates().union(self.domain_ancillaries())
    #--- End: def

    def clear(self, coordinates=True, parameters=True, domain_ancillaries=True):
        '''
        '''
        if coordinates:            
            self._coordinates.clear()            

        if parameters and ancillaries:
              self._parameters.clear()
              self._domain_ancillaries.clear()
              super(CoordinateReference, self).clear()

        elif parameters:      
            for term in self._parameters:
                self.del_term(term)

            self._parameters.clear()

        elif domain_ancillaries:            
            for term in self._domain_ancillaries:
                self.del_term(term)

            self._domain_ancillaries.clear()
    #---End: def

#    def _parse_match(self, match):
#        '''Called by `match`
#
#:Parameters:
#
#    match: 
#        As for the *match* parameter of `match` method.
#
#:Returns:
#
#    out: `list`
#        '''        
#        if not match:
#            return ()
#
#        if not isinstance(match, (list, tuple)): #basestring, dict, Query)):
#            match = (match,)
#
#        matches = []
#        for m in match:            
#            if isinstance(m, basestring):
#                if ':' in m:
#                    # CF property (string-valued)
#                    m = m.split(':')
#                    matches.append({m[0]: ':'.join(m[1:])})
#                else:
#                    # Identity (string-valued) or python attribute
#                    # (string-valued) or axis type
#                    matches.append({None: m})
#
#            elif isinstance(m, dict):
#                # Dictionary
#                matches.append(m)
#
#            else:
#                # Identity (not string-valued, e.g. cf.Query).
#                matches.append({None: m})
#        #--- End: for
#
#        return matches
#    #--- End: def
#
#    def match(self, description=None, inverse=False):
#        '''Test whether or not the coordinate reference satisfies the given
#conditions.
#
#:Returns:
#
#    out: `bool`
#        True if the coordinate reference satisfies the given criteria,
#        False otherwise.
#
#:Examples:
#
#        '''
##        conditions_have_been_set = False
##        something_has_matched    = False
#
#        description = self._parse_match(description)
#
##        if description:
##            conditions_have_been_set = True
#
#        found_match = True
#        for match in description:
#            found_match = True
#            
#            for prop, value in match.iteritems():
#                if prop is None: 
#                    if isinstance(value, basestring):
#                        if value in ('T', 'X', 'Y', 'Z'):
#                            # Axis type, e.g. 'T'
#                            x = getattr(v, value, False)
#                            value = True
#                        else:
#                            y = value.split('%')
#                            if len(y) > 1:
#                                # String-valued python attribute,
#                                # e.g. 'ncvar%latlon'
#                                x = getattr(v, y[0], None)
#                                value = '%'.join(y[1:])
#                            else:
#                                # String-valued identity
#                                x = v.identity(default=None)
#                    else:   
#                        # Non-string-valued identity
#                        x = v.identity(default=None)
#                else:
#                    x = v.get(prop)
#
#                if x is None:
#                    found_match = False
#                elif value is None:
#                    found_match = True
#                else:
#                    found_match = (value == x)
#                    try:
#                        found_match == True
#                    except ValueError:
#                        found_match = False
#                #--- End: if
#
#                if not found_match:
#                    break
#            #--- End: for
#
#            if found_match:
#                break
#        #--- End: for
#
#        return not bool(inverse)
#    #--- End: def



#--- End: class
