import abc

import csv
import os

from .          import __file__
from .functions import equals as cfdm_equals

import mixin

from ..structure import CoordinateReference as structure_CoordinateReference

# --------------------------------------------------------------------
# Map coordinate conversion names to the set of coordinates to which
# they apply
# --------------------------------------------------------------------
#_name_to_coordinates = {}
#_file = os.path.join(os.path.dirname(__file__),
#                     'etc/coordinatereference/name_to_coordinates.txt')
#for x in csv.reader(open(_file, 'r'), delimiter=' ', skipinitialspace=True):
#    if not x or x[0] == '#':
#        continue
#    _name_to_coordinates[x[0]] = set(x[1:])

# ====================================================================
#
# CoordinateReference object
#
# ====================================================================

class CoordinateReference(structure_CoordinateReference, mixin.Properties):
    '''A CF coordinate reference construct.

    '''
   
#    # Map coordinate conversion names to their
#    _name_to_coordinates = _name_to_coordinates
    
    def __init__(self, properties={}, coordinates=None,
                 domain_ancillaries=None, parameters=None, datum=None,
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
        super(CoordinateReference, self).__init__(
            properties=properties,
            coordinates=coordinates,
            domain_ancillaries=domain_ancillaries,
            parameters=parameters,
            datum=datum, source=source, copy=copy)
    #--- End: def
   
    def __str__(self):
        '''

The built-in function `str`

x.__str__() <==> str(x)

'''    
        return self.identity('')
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
            string.append("{0}{1} = {2}".format(indent1, term, self.get_term(term)))

        # Domain ancillary-valued terms
        if field:
            for term in sorted(self._domain_ancillaries):
                value = field.domain_ancillaries().get(self.get_term(term))
                if value is not None:
                    value = 'Domain Ancillary: '+value.name('')
                else:
                    value = ''
                string.append('{0}{1} = {2}'.format(indent1, term, str(value)))
        else:
            for term, value in self.domain_ancillaries.iteritems():
                string.append("{0}{1} = {2}".format(indent1, term, str(value)))

        # Coordinates 
        if field:
            for identifier in sorted(self._coordinates):
                coord = field.coordinates().get(identifier)
                if coord is not None:
                    if getattr(coord, 'isdimension', False):
                        coord = 'Dimension Coordinate: '+coord.name('')
                    else:
                        coord = 'Auxiliary Coordinate: '+coord.name('')

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
            
    def equals(self, other, rtol=None, atol=None, traceback=False, **kwargs):
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
        if self.get_name(None) != other.get_name(None):
            if traceback:
                print("{}: Different names ({} != {})".format(
                    self.__class__.__name__,
                    self.get_name(None), other.get_name(None)))
            return False
        #--- End: if
                
        if rtol is None:
            rtol = RTOL()
        if atol is None:
            atol = ATOL()

        # ------------------------------------------------------------
        # Check that the same terms are present
        # ------------------------------------------------------------
        if set(self.terms()) != set(other.terms()):
            if traceback:
                print(
                    "{0}: Different collections of terms ({1} != {2})".format(
                        self.__class__.__name__, set(self.terms()),
                        set(other.terms())))
            return False
        #--- End: if

        # Check that the parameter terms match
        parameters0 = self.parameters()
        parameters1 = other.parameters()
        if set(parameters0) != set(parameters1):
            if traceback:
                print(
                    "{0}: Different parameter-valued terms ({1} != {2})".format(
                        self.__class__.__name__,
                        set(parameters0), set(parameters1)))
            return False
        #--- End: if

        # Check that the domain ancillary terms match
        ancillaries0 = self.domain_ancillaries()
        ancillaries1 = other.domain_ancillaries()
        if set(ancillaries0) != set(ancillaries1):
            if traceback:
                print(
                    "{0}: Different ancillary-valued terms ({1} != {2})".format(
                        self.__class__.__name__,
                        set(ancillaries0), set(ancillaries1)))
            return False
        #--- End: if

        for term, value0 in ancillaries0.iteritems():            
            value1 = ancillaries1[term]  
            if value0 is None or (value1 is None and value0 is not None):
                if traceback:
                    print(
                        "{}: Unequal {!r} domain ancillary terms ({!r} != {!r})".format( 
                            self.__class__.__name__, term, value0, value1))
                return False
        #--- End: for

        # ------------------------------------------------------------
        # Check that the parameter term values are equal.
        # ------------------------------------------------------------
        coords0 = self.coordinates()
        coords1 = other.coordinates()
        if len(coords0) != len(coords1):
            if traceback:
                print(
"{0}: Different sized collections of coordinates ({1} != {2})".format(
    self.__class__.__name__, len(coords0), len(coords1)))
            return False
        #--- End: if

        for term, value0 in parameters0.iteritems():            
            value1 = parameters1[term]  

            if value0 is None and value1 is None:
                # Term values are None in both coordinate
                # references
                continue
                
            if not cfdm_equals(value0, value1, rtol=rtol, atol=atol,
                               traceback=traceback, **kwargs):
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

