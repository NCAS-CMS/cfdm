import abc

import csv
import os

from .                    import __file__
from .dimensioncoordinate import DimensionCoordinate
from .auxiliarycoordinate import AuxiliaryCoordinate

import mixin

from .structure import CoordinateReference as structure_CoordinateReference

# --------------------------------------------------------------------
# Map coordinate conversion names to the set of coordinates to which
# they apply
# --------------------------------------------------------------------
_name_to_coordinates = {}
_file = os.path.join(os.path.dirname(__file__),
                     'etc/coordinate_reference/coordinates.txt')
for x in csv.reader(open(_file, 'r'), delimiter=' ', skipinitialspace=True):
    if not x or x[0] == '#':
        continue
    _name_to_coordinates[x[0]] = set(x[1:])

# --------------------------------------------------------------------
# Map coordinate conversion names to the set of coordinates to which
# they apply
# --------------------------------------------------------------------
_datum_parameters = []
_file = os.path.join(os.path.dirname(__file__),
                     'etc/coordinate_reference/datum_parameters.txt')
for x in csv.reader(open(_file, 'r'), delimiter=' ', skipinitialspace=True):
    if not x or x[0] == '#':
        continue
    _datum_parameters.append(x[0])
    
_datum_parameters = set(_datum_parameters)

# ====================================================================
#
# CoordinateReference object
#
# ====================================================================

class CoordinateReference(mixin.Container, structure_CoordinateReference):
    '''A CF coordinate reference construct.

    '''
   
    _name_to_coordinates = _name_to_coordinates
    _datum_parameters    = _datum_parameters

    def __init__(self,
                 coordinates=None,
                 domain_ancillaries=None,
                 parameters=None,
                 coordinate_conversion_domain_ancillaries=None,
                 coordinate_conversion_parameters=None,
                 datum_parameters=None,
                 datum_domain_ancillaries=None,
                 source=None, copy=True):
        '''**Initialization**

:Parameters:

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
        if parameters is not None and source is None:
            if datum_parameters is not None:
                raise ValueError("zcnz x.cn 90 datum")
            if coordinate_conversion_parameters is not None:
                raise ValueError("zcnz x.cn 90 coordinate_conversion")
            
            datum_parameters = {}
            coordinate_conversion_parameters = {}
            
            for p, value in parameters.iteritems():
                if p in self._datum_parameters:
                    datum_parameters[p] = value
                else:
                    coordinate_conversion_parameters[p] = value
        #-- End: if
        
        super(CoordinateReference, self).__init__(
            coordinates=coordinates,
            coordinate_conversion_domain_ancillaries=coordinate_conversion_domain_ancillaries,
            coordinate_conversion_parameters=coordinate_conversion_parameters,
            datum_domain_ancillaries=datum_domain_ancillaries,
            datum_parameters=datum_parameters,
            source=source,
            copy=copy)
    #--- End: def
   
    def __str__(self):
        '''

The built-in function `str`

x.__str__() <==> str(x)

'''    
        return self.name(default=self.get_ncvar(''))
    #--- End: def

    def dump(self, display=True, _omit_properties=None, field=None,
             key='', _level=0, _title=None):
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
            string = ['{0}Coordinate Reference: {1}'.format(indent0,
                                                            self.name(default=key))]
        else:
            string = [indent0 + _title]

#        string.append(
#            super(CoordinateReference, self)._dump_properties(
#                _level=_level+1))
            
        # Coordinate conversion parameter-valued terms
        coordinate_conversion = self.get_coordinate_conversion()
        for term, value in sorted(coordinate_conversion.parameters().items()):
            string.append("{0}Coordinate conversion:{1} = {2}".format(
                indent1, term, value))

        # Coordinate conversion domain ancillary-valued terms
        if field:
            for term, key in sorted(coordinate_conversion.domain_ancillaries().items()):
                value = field.domain_ancillaries().get(key)
                if value is not None:
                    value = 'Domain Ancillary: '+value.name(default=key)
                else:
                    value = ''
                string.append('{0}Coordinate conversion:{1} = {2}'.format(
                    indent1, term, str(value)))
        else:
            for term, value in sorted(coordinate_conversion.domain_ancillaries.items()):
                string.append("{0}Coordinate conversion:{1} = {2}".format(
                    indent1, term, str(value)))

        # Datum parameter-valued terms
        datum = self.get_datum()
        for term, value in sorted(datum.parameters().items()):
            string.append("{0}Datum:{1} = {2}".format(indent1, term, value))

        # Datum domain ancillary-valued terms
        if field:
            for term, key in sorted(datum.domain_ancillaries().items()):
                value = field.domain_ancillaries().get(key)
                if value is not None:
                    value = 'Domain Ancillary: '+value.name(default=key)
                else:
                    value = ''
                string.append('{0}Datum:{1} = {2}'.format(indent1, term, str(value)))
        else:
            for term, value in sorted(datum.domain_ancillaries().items()):
                string.append("{0}Datum:{1} = {2}".format(indent1, term, str(value)))

        # Coordinates 
        if field:
            for key in sorted(self.coordinates()):
                coord = field.coordinates().get(key)
                if coord is not None:
                    if isinstance(coord, DimensionCoordinate):
                        coord = 'Dimension Coordinate: '+coord.name(default=key)
                    elif isinstance(coord, AuxiliaryCoordinate):
                        coord = 'Auxiliary Coordinate: '+coord.name(default=key)
                    else:
                        coord = coord.name(default=key)

#                    string.append('{0}Coordinate = {1}'.format(indent1, coord))
                    string.append('{0}{1}'.format(indent1, coord))
        else:
            for identifier in sorted(self.coordinates()):
#                string.append('{0}Coordinate = {1}'.format(indent1, identifier))
                string.append('{0}{1}'.format(indent1, identifier))
            
        string = '\n'.join(string)
       
        if display:
            print string
        else:
            return string
    #--- End: def
            
    def equals(self, other, rtol=None, atol=None, traceback=False,
               ignore_data_type=False, ignore_fill_value=False,
               ignore_construct_type=False):
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
        if not super(CoordinateReference, self).equals(
                other, rtol=rtol, atol=atol,
                traceback=traceback,
                ignore_construct_type=ignore_construct_type):
	    return False

        print '________________'
        for a in ('datum', 'coordinate_conversion'):

            x0 = getattr(self, 'get_'+a)()
            x1 = getattr(other, 'get_'+a)()
            print 'AAAAAAAAAAAAAAA a=', a, x0.parameters(), x1.parameters()
            
            # Check that the coordinate conversion parameter terms match
            parameters0 = x0.parameters()
            parameters1 = x1.parameters()
            if set(parameters0) != set(parameters1):
                if traceback:
                    print(
"{0}: Different {1} parameter-valued terms ({2} != {3})".format(
    self.__class__.__name__, a,
    set(parameters0), set(parameters1)))
                return False
            #--- End: if

            # Check that the coordinate conversion domain ancillary terms
            # match
            ancillaries0 = x0.domain_ancillaries()
            ancillaries1 = x1.domain_ancillaries()
            if set(ancillaries0) != set(ancillaries1):
                if traceback:
                    print(
"{0}: Different {1} domain ancillary-valued terms ({2} != {3})".format(
    self.__class__.__name__, a,
    set(ancillaries0), set(ancillaries1)))
                return False
            #--- End: if

            for term, value0 in ancillaries0.iteritems():            
                value1 = ancillaries1[term]  
                if value0 is None or (value1 is None and value0 is not None):
                    if traceback:
                        print(
"{}: Unequal {!r} domain ancillary {} terms ({!r} != {!r})".format( 
    self.__class__.__name__, term, a,
    value0, value1))
                    return False
            #--- End: for
     
            # Check that the coordinate conversion parameter term
            # values are equal.
            for term, value0 in parameters0.iteritems():            
                value1 = parameters1[term]  

                if value0 is None and value1 is None:
                    # Term values are None in both coordinate
                    # references
                    continue
                
                if not self._equals(value0, value1, rtol=rtol, atol=atol,
                                    traceback=traceback,
                                    ignore_data_type=ignore_data_type,
                                    ignore_fill_value=ignore_fill_value,
                                    ignore_construct_type=ignore_construct_type):
                    if traceback:
                        print(
                            "{}: Unequal {!r} terms ({!r} != {!r})".format( 
                                self.__class__.__name__, term, value0, value1))
                    return False
            #--- End: for
        #--- End: for
        
        coords0 = self.coordinates()
        coords1 = other.coordinates()
        if len(coords0) != len(coords1):
            if traceback:
                print(
"{0}: Different sized collections of coordinates ({1} != {2})".format(
    self.__class__.__name__, len(coords0), len(coords1)))
            return False
        #--- End: if

        # Still here? Then the two coordinate references are as equal
        # as can be ascertained in the absence of domains.
        return True
    #--- End: def

    def name(self, default=None):
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
        n = self.coordinate_conversion.get_parameter('standard_name', None)
        if n is not None:
            return n
        
        n = self.coordinate_conversion.get_parameter('grid_mapping_name', None)
        if n is not None:
            return n
        
        return default
    #--- End: def

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

#    @classmethod
#    def _name_to_coordinates
#    # Map coordinate conversion names to their
#    _name_to_coordinates = _name_to_coordinates
    
#--- End: class

