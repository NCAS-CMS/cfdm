import os

from copy import deepcopy
from csv  import reader as csv_reader
from re   import match as re_match

from .          import __file__
from .functions import RTOL, ATOL, equals, allclose
from .units     import Units

from .data.data import Data

# --------------------------------------------------------------------
# Map coordinate conversion names to their CF-netCDF types
# --------------------------------------------------------------------
_type = {}
_file = os.path.join(os.path.dirname(__file__),
                     'etc/coordinate_reference/type.txt')
for x in csv_reader(open(_file, 'r'), delimiter=' ', skipinitialspace=True):
    if not x or x[0] == '#':
        continue
    _type[x[0]] = x[1]

# --------------------------------------------------------------------
# Map coordinate conversion names to their
# --------------------------------------------------------------------
_coordinates = {}
_file = os.path.join(os.path.dirname(__file__),
                     'etc/coordinate_reference/coordinates.txt')
for x in csv_reader(open(_file, 'r'), delimiter=' ', skipinitialspace=True):
    if not x or x[0] == '#':
        continue
    _coordinates[x[0]] = set(x[1:])

# --------------------------------------------------------------------
# Map coordinate conversion terms to their terms default values
# --------------------------------------------------------------------
_default_values = {}
_file = os.path.join(os.path.dirname(__file__),
                     'etc/coordinate_reference/default_values.txt')
for x in csv_reader(open(_file, 'r'), delimiter=' ', skipinitialspace=True):
    if not x or x[0] == '#':
        continue
    _default_values[x[0]] = float(x[1])

# --------------------------------------------------------------------
# Map coordinate conversion terms to their canonical units
# --------------------------------------------------------------------
_canonical_units = {}
_file = os.path.join(os.path.dirname(__file__),
                     'etc/coordinate_reference/canonical_units.txt')
for x in csv_reader(open(_file, 'r'), delimiter=' ', skipinitialspace=True):
    if not x or x[0] == '#':
        continue
    try:
        _canonical_units[x[0]] = Units(x[1])
    except:
        _canonical_units[x[0]] = x[1]

# --------------------------------------------------------------------
# Map coordinate reference names to their terms which may take
# non-constant values (i.e. pointers to coordinate objects or
# non-scalar field objects).
# --------------------------------------------------------------------
_non_constant_terms = {}
_file = os.path.join(os.path.dirname(__file__),
                     'etc/coordinate_reference/non_constant_terms.txt')
for x in csv_reader(open(_file, 'r'), delimiter=' ', skipinitialspace=True):
    if not x or x[0] == '#' or len(x) == 1:
        continue
    _non_constant_terms[x[0]] = set(x[1:])


# ====================================================================
#
# CoordinateReference object
#
# ====================================================================

_units = {}

class CoordinateReference(dict):
    '''A CF coordinate reference construct.

A coordinate reference construct relates the field's coordinate values
to locations in a planetary reference frame.

The coordinate reference object is associated with a coordinate system
and contains links to the dimension or auxiliary coordinate constructs
to which it applies; and any additional terms, such as scalar values
and field objects which define a datum and coordinate conversion,
i.e. a formula for converting coordinate values taken from the
dimension or auxiliary coordinate objects to a different coordinate
system.

**Accessing terms**

The coordinate reference object behaves like a dictionary when it
comes to accessing its terms and their values: For example:

>>> c = cf.CoordinateReference('azimuthal_equidistant', 
...                             longitude_of_projection_origin=80.5,
...                             latitude_of_projection_origin=5, 
...                             false_easting=cf.Data(-200, 'km'),
...                             false_northing=cf.Data(-100, 'km'))
>>> c.keys()
['false_easting',
 'latitude_of_projection_origin',
 'false_northing',
 'longitude_of_projection_origin']
>>> c.items()
[('false_easting', <CF Data: -200 km>),
 ('latitude_of_projection_origin', 5),
 ('false_northing', <CF Data: -100 km>),
 ('longitude_of_projection_origin', 80.5)]
>>> c['latitude_of_projection_origin']
5
>>> c['latitude_of_projection_origin'] = -75.25
>>> c['latitude_of_projection_origin']
-75.25


**Attributes**

==============  ======================================================

Attribute       Description
==============  ======================================================
`!name`         The identity of the coordinate reference.

`!type`         The CF type of the coordinate reference. 

`!coordinates`  The identities of the dimension and auxiliary
                coordinate objects of the which apply to this
                coordinate reference. 

==============  ======================================================

    '''

    def __init__(self, name=None, crtype=None, coordinates=None,
                 ancillaries=None, parameters=None, datum=None):
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

        >>> c = cf.CoordinateReference('transverse_mercator')
        >>> c.type
        'grid_mapping'

        >>> c = cf.CoordinateReference('my_new_type', crtype='formula_terms')
        >>> c.type
        'formula_terms'

        >>> c = cf.CoordinateReference('my_new_type')
        >>> print c.type
        None

        >>> c = cf.CoordinateReference('my_new_type', crtype='grid_mapping')
        >>> print c.type
        'grid_mapping'

    coordinates: sequence of `str`, optional
        Identify the dimension and auxiliary coordinate objects which
        apply to this coordinate reference. By default the standard
        names of those expected by the CF conventions are used. For
        example:

        >>> c = cf.CoordinateReference('transverse_mercator')
        >>> c.coordinates
        {'latitude', 'longitude', 'projection_x_coordinate', 'projection_y_coordinate'}

        >>> c = cf.CoordinateReference('transverse_mercator', coordinates=['ncvar%lat'])
        >>> c.coordinates
        {'ncvar%lat', 'latitude', 'longitude', 'projection_x_coordinate', 'projection_y_coordinate'}

    kwargs: *optional*
        The terms of the coordinate conversion and their values. A
        term's value may be one of the following:

          * A number or size one numeric array.

          * A string containing a coordinate object's identity.

          * A Field.
 
          * `None`, indicating that the term exists but is unset.

        For example:

        >>> c = cf.CoordinateReference('orthographic', 
        ...                            grid_north_pole_latitude=70,
        ...                            grid_north_pole_longitude=cf.Data(120, 'degreesE'))
        >>> c['grid_north_pole_longitude']
        <CF Data: 120 degreesE>

        >>> orog_field
        <CF Field: surface_altitude(latitude(73), longitude(96)) m>
        >>> c = cf.CoordinateReference('atmosphere_hybrid_height_coordinate',
        ...                            a='long_name:ak',
        ...                            b='long_name:bk',
        ...                            orog=orog_field)

        '''
        t = _type.get(name, None)
        if t is None:
            pass
        elif crtype is None:
            crtype = t
        elif t != crtype:
            raise ValueError(" 888 askjdalsjkdnlaksjd lasdna")
            
        self.type = crtype
        self.datum = datum

        self._coordinates = set(_coordinates.get(name, ()))
        if coordinates:
            self._coordinates.update(coordinates)

        self._parameters  = set()
        self._ancillaries = set()

        if crtype == 'formula_terms':
            self.set_term('parameter', 'standard_name', name)
        elif crtype == 'grid_mapping':
            self.set_term('parameter', 'grid_mapping_name', name)

        if parameters:
            for term, value in parameters.iteritems():
                self.set_term('parameter', term, value)
                
        if ancillaries: 
            for term, value in ancillaries.iteritems():
                self.set_term('ancillary', term, value)
    #--- End: def
   
    def __repr__(self):
        '''

The built-in function `repr`

x.__repr__() <==> repr(x)

''' 
        try:
            return '<CF {0}: {1}>'.format(self.__class__.__name__,
                                        self.identity(''))
        except AttributeError:
            return '<CF {0}: >'.format(self.__class__.__name__)
    #--- End: def

    def __delitem__(self, key):
        '''

x.__delitem__(key) <==> del x[key]

'''
        self._parameters.discard(key)
        self._ancillaries.discard(key)

        super(CoordinateReference, self).__delitem__(key)
    #--- End: def

    def __str__(self):
        '''

The built-in function `str`

x.__str__() <==> str(x)

'''    
        return 'Coord reference : {0!r}'.format(self)
    #--- End: def

    # ----------------------------------------------------------------
    # Attribute (read only)
    # ----------------------------------------------------------------
    @property
    def hasbounds(self):
        '''

False. Coordinate reference objects do not have cell bounds.

:Examples:

>>> c.hasbounds
False

'''
        return False
    #--- End: def

    def canonical(self, field=None):
        '''
'''
        ref = self.copy()

        for term, value in ref.parameters.iteritems():
            if value is None or isinstance(value, basestring):
                continue

            canonical_units = self.canonical_units(term)
            if canonical_units is None:
                continue

            if isinstance(canonical_units, basestring):
                # units is a standard_name of a coordinate
                if field is None:
                    raise ValueError("Set the field parameter")
                coord = field.coord(canonical_units, exact=True)
                if coord is not None:
                    canonical_units = coord.Units

            if canonical_units is not None:
                units = getattr(value, 'Units', None)
                if units is not None:
                    if not canonical_units.equivalent(units):
                        raise ValueError("xasdddddddddddddd 87236768")                
                    value.Units = canonical_units
        #--- End: for

        return ref
    #--- End: def

    @classmethod
    def canonical_units(cls, term):
        '''Return the canonical units for a standard CF coordinate conversion
term.

:Parameters:

    term: `str`
        The name of the term.

:Returns:

    out: `cf.Units` or `None`
        The canonical units, or `None` if there are not any.

:Examples:

>>> cf.CoordinateReference.canonical_units('perspective_point_height')
<CF Units: m>
>>> cf.CoordinateReference.canonical_units('ptop')
None

        '''
        return _canonical_units.get(term, None)
    #--- End: def

    def close(self):
        '''

Close all files referenced by coordinate conversion term values.

:Returns:

    None

:Examples:

>>> c.close()

'''
        pass
    #--- End: def

    def copy(self):
        '''

Return a deep copy.

``c.copy()`` is equivalent to ``copy.deepcopy(c)``.

:Examples 1:

>>> d = c.copy()

:Returns:

    out:
        The deep copy.

'''       
        X = type(self)
        new = X.__new__(X)

        new.type = self.type

        new.datum = deepcopy(self.datum)

        new._coordinates = self._coordinates.copy()
        new._parameters  = self._parameters.copy()
        new._ancillaries = self._ancillaries.copy()

        for term, value in self.iteritems():
            c = getattr(value, 'copy', None)
            if c is None:
                new[term] = value
            else:
                new[term] = value.copy()

        return new
    #---End: def

    @classmethod
    def default_value(cls, term):
        '''

Return the default value for an unset standard CF coordinate
conversion term.

The default values are stored in the file
cf/etc/coordinate_reference/default_values.txt.

:Parameters:	

    term: `str`
        The name of the term.

:Returns:	

    out: 
        The default value.

:Examples:

>>> cf.CoordinateReference.default_value('ptop')
0.0
>>> print cf.CoordinateReference.default_value('north_pole_grid_latitude')
0.0

        '''
        return _default_values.get(term, 0.0)
    #--- End: def

    def dump(self, display=True, omit=(), field=None, key=None,
             _level=0, _title=None):
        '''Return a string containing a full description of the coordinate
reference object.

:Parameters:

    display: `bool`, optional
        If False then return the description as a string. By default
        the description is printed, i.e. ``c.dump()`` is equivalent to
        ``print c.dump(display=False)``.

    field: `cf.Field`, optional

    key: `str`, optional
        Ignored.

:Returns:

    out: `None` or `str`

:Examples:

        '''          
        indent0 = '    ' * _level
        indent1 = '    ' * (_level+1)
        indent2 = '    ' * (_level+2)

        if _title is None:
            string = ['{0}Coordinate Reference: {1}'.format(indent0, self.name(''))]
        else:
            string = [indent0 + _title]

        # Parameter-valued terms
        for term in sorted(self._parameters):
            string.append("{0}{1} = {2}".format(indent1, term, self[term]))

        # Domain ancillary-valued terms
        if field:
            for term in sorted(self._ancillaries):
                value = field.item(self[term], role='c')
                if value is not None:
                    value = 'Domain Ancillary: '+value.name('')
                else:
                    value = ''
                string.append('{0}{1} = {2}'.format(indent1, term, str(value)))
        else:
            for term, value in self.ancillaries.iteritems():
                string.append("{0}{1} = {2}".format(indent1, term, str(value)))

        # Coordinates 
        if field:
            for identifier in sorted(self._coordinates):
                coord = field.item(identifier, role=('d', 'a'))
                if coord is not None:
                    if getattr(coord, 'isdimension', False):
                        coord = 'Dimension Coordinate: '+coord.name('')
                    else:
                        coord = 'Auxiliary Coordinate: '+coord.name('')
                else:
                    coord = str(identifier)

                string.append('{0}Coordinate = {1}'.format(indent1, coord))
        else:
            for identifier in sorted(self._coordinates):
                string.append('{0}Coordinate = {1}'.format(indent1, identifier))
            
        string = '\n'.join(string)
       
        if display:
            print string
        else:
            return string
    #--- End: def

    def equals(self, other, rtol=None, atol=None,
               ignore_data_type=False, ignore_fill_value=False,
               traceback=False, mapping=None, ignore_type=False):
        '''

True if two instances are equal, False otherwise.

:Parameters:

    other:
        The object to compare for equality.

    atol: `float`, optional
        The absolute tolerance for all numerical comparisons, By
        default the value returned by the `ATOL` function is used.

    rtol: `float`, optional
        The relative tolerance for all numerical comparisons, By
        default the value returned by the `RTOL` function is used.

    ignore_fill_value: `bool`, optional
        If True then data arrays with different fill values are
        considered equal. By default they are considered unequal.

    traceback: `bool`, optional
        If True then print a traceback highlighting where the two
        instances differ.

:Returns: 

    out: `bool`
        Whether or not the two instances are equal.

:Examples:

'''
        if self is other:
            return True
        
        # Check that each instance is the same type
        if self.__class__ != other.__class__:
            if traceback:
                print("{0}: Different types: {0}, {1}".format(
                    self.__class__.__name__,
                    other.__class__.__name__))
            return False
        #--- End: if
   
        # ------------------------------------------------------------
        # Check the name
        # ------------------------------------------------------------
        if self.name != other.name:
            if traceback:
                print("{}: Different names ({} != {})",format(
                    self.__class__.__name__, self.name, other.name))
            return False
        #--- End: if
                
        if rtol is None:
            rtol = RTOL()
        if atol is None:
            atol = ATOL()

        # ------------------------------------------------------------
        # Check that the same terms are present
        # ------------------------------------------------------------
        if set(self) != set(other):
            if traceback:
                print(
                    "{}: Different collections of terms ({} != {})".format(
                        self.__class__.__name__, set(self), set(other)))
            return False
        #--- End: if

        # Check that the parameter terms match
        parameter_terms0 = self._parameters
        parameter_terms1 = other._parameters
        if set(parameter_terms0) != set(parameter_terms1):
            if traceback:
                print(
                    "{}: Different parameter-valued terms ({} != {})".format(
                        self.__class__.__name__,
                        parameter_terms0, parameter_terms1))
            return False
        #--- End: if

        # Check that the domain ancillary terms match
        ancillary_terms0 = self._ancillaries
        ancillary_terms1 = other._ancillaries
        if set(ancillary_terms0) != set(ancillary_terms1):
            if traceback:
                print(
                    "{}: Different ancillary-valued terms ({} != {})".format(
                        self.__class__.__name__,
                        ancillary_terms0, ancillary_terms1))
            return False
        #--- End: if

        # ------------------------------------------------------------
        # Check that the parameter term values are equal.
        #
        # If the values for a particular term are both undefined or
        # are both pointers to coordinates then they are considered
        # equal.
        # ------------------------------------------------------------
        coords0 = self._coordinates
        coords1 = other._coordinates
        if len(coords0) != len(coords1):
            if traceback:
                print(
"{}: Different sized collections of coordinates ({} != {})".format(
    self.__class__.__name__, len(coords0), len(coords1)))
            return False
        #--- End: if

        for term, value0 in self.iteritems():            
            value1 = other[term]  

            if value0 is None and value1 is None:
                # Term values are None in both coordinate
                # references
                continue
                
            if equals(value0, value1, rtol=rtol, atol=atol,
                      ignore_data_type=ignore_data_type,
                      ignore_fill_value=ignore_fill_value,
                      traceback=traceback):
                # Term values are the same in both coordinate
                # references
                continue

            # Still here? Then the two coordinate references are not
            # equal.
            if traceback:
                print(
                    "{}: Unequal {!r} terms ({!r} != {!r})".format( 
                        self.__class__.__name__, term, value0, value1))
                return False
        #--- End: for

        # ------------------------------------------------------------
        # Still here? Then the two coordinate references are as equal
        # as can be ascertained in the absence of domains.
        # ------------------------------------------------------------
        return True
    #--- End: def

    @property
    def ancillaries(self):
        out = {}
        for term in self._ancillaries:
            out[term] = self[term]
        return out
    #--- End: def

    @property
    def parameters(self):
        out = {}
        for term in self._parameters:
            out[term] = self[term]
        return out
    #--- End: def

    @property
    def coordinates(self):
        return self._coordinates.copy()
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

        n = getattr(self, 'ncvar', None)
        if n is not None:
            return 'ncvar%{0}'.format(n)
            
        return default
    #--- End: def

    def change_identifiers(self, identity_map, coordinate=True,
                           ancillary=True, strict=False, i=False):
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
...                             a='ncvar:ak',
...                             b='ncvar:bk')
>>> r.coordinates
{'atmosphere_hybrid_height_coordinate'}
>>> r.change_coord_identitiers({'atmosphere_hybrid_height_coordinate', 'dim1',
...                             'ncvar:ak': 'aux0'})
>>> r.coordinates
{'dim1', 'aux0'}

        '''
        if i:
            r = self
        else:
            r = self.copy()

        if not identity_map and not strict:
            return r

        if strict:
            default = None

        if ancillary:
#            ancillary = r._conversion['ancillary']
            for term in r._ancillaries:
                identifier = self[term]
                if not strict:
                    default = identifier
                self[term] = identity_map.get(identifier, default)

        if coordinate:
            coordinates = []
            for identifier in r._coordinates:
                if not strict:
                    default = identifier
                coordinates.append(identity_map.get(identifier, default))
            
            coordinates = set(coordinates)
            coordinates.discard(None)
            r._coordinates = coordinates

        return r
    #---End: def

    def all_identifiers(self):
        '''
'''
        return self._coordinates.union(self._ancillaries)
    #--- End: def

    def clear(self, coordinates=True, parameters=True, ancillaries=True):
        '''
        '''
        if coordinates:            
            self._coordinates.clear()            

        if parameters and ancillaries:
              self._parameters.clear()
              self._ancillaries.clear()
              super(CoordinateReference, self).clear()

        elif parameters:      
            for term in self._parameters:
                del self[term]
            self._parameters.clear()

        elif ancillaries:            
            for term in self._ancillaries:
                del self[term]
            self._ancillaries.clear()
    #---End: def

# MOVE TO FUNCTIONS
    def _parse_match(self, match):
        '''Called by `match`

:Parameters:

    match: 
        As for the *match* parameter of `match` method.

:Returns:

    out: `list`
        '''        
        if not match:
            return ()

        if not isinstance(match, (list, tuple)): #basestring, dict, Query)):
            match = (match,)

        matches = []
        for m in match:            
            if isinstance(m, basestring):
                if ':' in m:
                    # CF property (string-valued)
                    m = m.split(':')
                    matches.append({m[0]: ':'.join(m[1:])})
                else:
                    # Identity (string-valued) or python attribute
                    # (string-valued) or axis type
                    matches.append({None: m})

            elif isinstance(m, dict):
                # Dictionary
                matches.append(m)

            else:
                # Identity (not string-valued, e.g. cf.Query).
                matches.append({None: m})
        #--- End: for

        return matches
    #--- End: def

    def match(self, match=None, exact=False, match_all=True, inverse=False):
        '''Test whether or not the coordinate reference satisfies the given
conditions.

:Returns:

    out: `bool`
        True if the coordinate reference satisfies the given criteria,
        False otherwise.

:Examples:

        '''
        conditions_have_been_set = False
        something_has_matched    = False

        matches = self._parse_match(match)

        if matches:
            conditions_have_been_set = True

        found_match = True
        for match in matches:
            found_match = True

            for prop, value in match.iteritems():
                if prop is None:
                    if isinstance(value, basestring):
                        if value in ('T', 'X', 'Y', 'Z'):
                            # Axis type
                            x = getattr(self, value)
                            value = True
                        elif '%' in value:
                            # Python attribute (string-valued)
                            value = value.split('%')
                            x = getattr(self, value[0], None)
                            value = '%'.join(value[1:])
                        else:
                            # Identity (string-valued)
                            x = self.identity(None)
                    else:   
                        # Identity (not string-valued, e.g. cf.Query)
                        x = self.identity(None)
                else:
                    # CF term name                    
                    x = self.get(prop, None)

                if x is None:
                    found_match = False
                elif isinstance(x, basestring) and isinstance(value, basestring):
                    if exact:
                        found_match = (value == x)
                    else:
                        found_match = re_match(value, x)
                else:	
                    found_match = (value == x)
                    try:
                        found_match == True
                    except ValueError:
                        found_match = False
                #--- End: if

                if found_match:
                    break
            #--- End: for

            if found_match:
                something_has_matched = True
                break
        #--- End: for

        if match_all and not found_match:
            return bool(inverse)

        if conditions_have_been_set:
            if something_has_matched:            
                return not bool(inverse)
            else:
                return bool(inverse)
        else:
            return not bool(inverse)
    #--- End: def

    def set_term(self, term_type, term, value):
        '''
'''
        if (term_type == 'ancillary' and term in self._parameters or
            term_type == 'parameter' and term in self._ancillaries):
            raise KeyError("Can't set key - already set with different type")

        self[term] = value

        if term_type == 'ancillary':
            self._ancillaries.add(term)
        elif term_type == 'parameter':
            self._parameters.add(term)
    #--- End: def

    @property
    def conversion(self):
        '''
'''        
        return dict(self)
    #--- End: def

#--- End: class

