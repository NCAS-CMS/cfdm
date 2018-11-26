from __future__ import print_function
from builtins import (str, super)
from past.builtins import basestring

#import csv
#import os

#from . import __file__

from . import mixin
from . import core

from . import CoordinateConversion
from . import Datum


## --------------------------------------------------------------------
## Map coordinate conversion names to the set of coordinates to which
## they apply
## --------------------------------------------------------------------
#_name_to_coordinates = {}
#_file = os.path.join(os.path.dirname(__file__),
#                     'etc/coordinate_reference/coordinates.txt')
#for x in csv.reader(open(_file, 'r'), delimiter=' ', skipinitialspace=True):
#    if not x or x[0] == '#':
#        continue
#    _name_to_coordinates[x[0]] = set(x[1:])
#
## --------------------------------------------------------------------
## Map coordinate conversion names to the set of coordinates to which
## they apply
## --------------------------------------------------------------------
#_datum_parameters = []
#_file = os.path.join(os.path.dirname(__file__),
#                     'etc/coordinate_reference/datum_parameters.txt')
#for x in csv.reader(open(_file, 'r'), delimiter=' ', skipinitialspace=True):
#    if not x or x[0] == '#':
#        continue
#    _datum_parameters.append(x[0])
#    
#_datum_parameters  = set(_datum_parameters)
##_datum_ancillaries = set()


class CoordinateReference(mixin.NetCDFVariable,
                          mixin.Container,
                          core.CoordinateReference):
    '''A coordinate reference construct of the CF data model. 

A coordinate reference construct relates the coordinate values of the
coordinate system to locations in a planetary reference frame.

The domain of a field construct may contain various coordinate
systems, each of which is constructed from a subset of the dimension
and auxiliary coordinate constructs. For example, the domain of a
four-dimensional field construct may contain horizontal (y-x),
vertical (z), and temporal (t) coordinate systems. There may be more
than one of each of these, if there is more than one coordinate
construct applying to a particular spatiotemporal dimension (for
example, there could be both latitude-longitude and y-x projection
coordinate systems). In general, a coordinate system may be
constructed implicitly from any subset of the coordinate constructs,
yet a coordinate construct does not need to be explicitly or
exclusively associated with any coordinate system.

A coordinate system of the field construct can be explicitly defined
by a coordinate reference construct which relates the coordinate
values of the coordinate system to locations in a planetary reference
frame and consists of the following:

  * References to the dimension coordinate and auxiliary coordinate
    constructs that define the coordinate system to which the
    coordinate reference construct applies. Note that the coordinate
    values are not relevant to the coordinate reference construct,
    only their properties.

  * A definition of a datum specifying the zeroes of the dimension and
    auxiliary coordinate constructs which define the coordinate
    system. The datum may be implied by the metadata of the referenced
    dimension and auxiliary coordinate constructs, or explicitly
    provided by a `Datum` instance.

  * A coordinate conversion, which defines a formula for converting
    coordinate values taken from the dimension or auxiliary coordinate
    constructs to a different coordinate system. A coordinate
    reference construct relates the coordinate values of the field to
    locations in a planetary reference frame. The coordinate
    conversion formula is stored in a `CoordinateConversion` instance.

.. versionadded:: 1.7

    '''

#    _name_to_coordinates = _name_to_coordinates
#    _datum_parameters    = _datum_parameters
#    _datum_ancillaries   = _datum_ancillaries

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        instance._CoordinateConversion = CoordinateConversion
        instance._Datum                = Datum
        return instance
    #--- End: def

    def __init__(self, coordinates=None, datum=None,
                 coordinate_conversion=None,
                 source=None, copy=True):
        '''**Initialization**

:Parameters:

    coordinates: sequence of `str`, optional
        Identify the related dimension and auxiliary coordinate
        constructs by their construct identifiers. Ignored if the
        *source* parameter is set.

        *Example:*
          ``coordinates=['dimensioncoordinate2']``

        *Example:*
          ``coordinates=('dimensioncoordinate0', 'dimensioncoordinate1')``

        The coordinates may also be set after initialisation with the
        `coordinates` and `set_coordinate` methods.

    datum: `Datum`, optional
        Define the datum component of the coordinate reference
        construct. Ignored if the *source* parameter is set.

        The datum may also be set after initialisation with the
        `set_datum` method.

    coordinate_conversion: `CoordinateConversion`, optional
        Define the coordinate conversion component of the coordinate
        reference construct. Ignored if the *source* parameter is set.

        The coordinate conversion may also be set after initialisation
        with the `set_coordinate_conversion` method.

    source: optional
        Initialize the coordinates, datum and coordinate conversion
        from those of *source*.

    copy: `bool`, optional
        If False then do not deep copy arguments prior to
        initialization. By default arguments are deep copied.

        '''
        super().__init__(
            coordinates=coordinates,
            datum=datum,
            coordinate_conversion=coordinate_conversion,
            source=source,
            copy=copy)
        
        self._initialise_netcdf(source)
    #--- End: def
   
    def __str__(self):
        '''Called by the `str` built-in function.

x.__str__() <==> str(x)

.. versionadded:: 1.7

        '''    
        return self.name(default=self.nc_get_variable(''))
    #--- End: def

    def dump(self, display=True, _omit_properties=None, field=None,
             key='', _level=0, _title=None, _construct_names=None,
             _auxiliary_coordinates=None, _dimension_coordinates=None):
        '''A full description of the coordinate reference construct.

Returns a description of all properties, including those of
components.

.. versionadded:: 1.7

:Parameters:

    display: `bool`, optional
        If False then return the description as a string. By default
        the description is printed.

:Returns:

    out: `None` or `str`
        The description. If *display* is True then the description is
        printed and `None` is returned. Otherwise the description is
        returned as a string.

        '''          
        indent0 = '    ' * _level
        indent1 = '    ' * (_level+1)
        indent2 = '    ' * (_level+2)

        if _title is None:
            string = ['{0}Coordinate Reference: {1}'.format(
                indent0, self.name(default=''))]
        else:
            string = [indent0 + _title]

        # Coordinate conversion parameter-valued terms
        coordinate_conversion = self.get_coordinate_conversion()
        for term, value in sorted(coordinate_conversion.parameters().items()):
            string.append("{0}Coordinate conversion:{1} = {2}".format(
                indent1, term, value))

        # Coordinate conversion domain ancillary-valued terms
#        if field:
#            for term, key in sorted(coordinate_conversion.domain_ancillaries().items()):
#                value = field.domain_ancillaries().get(key)
#                if value is not None:
#                    value = 'Domain Ancillary: '+value.name(default=key)
#                else:
#                    value = ''
#                string.append('{0}Coordinate conversion:{1} = {2}'.format(
#                    indent1, term, str(value)))
        if _construct_names:
            for term, key in sorted(coordinate_conversion.domain_ancillaries().items()):
#                value = field.domain_ancillaries().get(key)
#                if value is not None:
#                    value = 'Domain Ancillary: '+value.name(default=key)
#                else:
#                    value = ''
                string.append('{0}Coordinate conversion:{1} = Domain Ancillary: {2}'.format(
                    indent1, term, _construct_names.get(key, 'cid%{}'.format(key))))
        else:
            for term, value in sorted(coordinate_conversion.ancillaries.items()):
                string.append("{0}Coordinate conversion:{1} = {2}".format(
                    indent1, term, str(value)))

        # Datum parameter-valued terms
        datum = self.get_datum()
        for term, value in sorted(datum.parameters().items()):
            string.append("{0}Datum:{1} = {2}".format(indent1, term, value))

#        # Datum domain ancillary-valued terms
#        if field:
#            for term, key in sorted(datum.domain_ancillaries().items()):
#                value = field.domain_ancillaries().get(key)
#                if value is not None:
#                    value = 'Domain Ancillary: '+value.name(default=key)
#                else:
#                    value = ''
#                string.append('{0}Datum:{1} = {2}'.format(indent1, term, str(value)))
#        else:
#            for term, value in sorted(datum.ancillaries().items()):
#                string.append("{0}Datum:{1} = {2}".format(indent1, term, str(value)))

        # Coordinates 
#       if field:
#           for key in sorted(self.coordinates()):
#               coord = field.coordinates().get(key)
#               if coord is not None:
#                   if isinstance(coord, DimensionCoordinate):
#                       coord = 'Dimension Coordinate: '+coord.name(default='key%'+key)
#                   elif isinstance(coord, AuxiliaryCoordinate):
#                       coord = 'Auxiliary Coordinate: '+coord.name(default='key%'+key)
#                   else:
#                       coord = coord.name(default=key)
#
#                   string.append('{0}{1}'.format(indent1, coord))
        if _construct_names:
            for key in sorted(self.coordinates(), reverse=True):
                coord = '{}'.format(_construct_names.get(key, 'cid%{}'.format(key)))
                if key in _dimension_coordinates:
                    coord = 'Dimension Coordinate: '+coord
                elif key in _auxiliary_coordinates:
                    coord = 'Auxiliary Coordinate: '+coord
                    
                string.append('{0}{1}'.format(indent1, coord))
        else:
            for identifier in sorted(self.coordinates()):
                string.append('{0}{1}'.format(indent1, identifier))
            
        string = '\n'.join(string)
       
        if display:
            print(string)
        else:
            return string
    #--- End: def
            
    def equals(self, other, rtol=None, atol=None, traceback=False,
               ignore_type=False):
        '''Whether two coordinate reference constructs are the same.

Equality is strict by default. This means that for two coordinate
reference constructs to be considered equal:

* the datum and coordinate conversion components must have the same
  string and numerical parameters.

The dimension coordinate, auxiliary coordinate and domain ancillary
constructs of the coordinate reference constructs are *not*
considered, because they may ony be correctly interpreted by the field
constructs that contain the coordinate reference constructs in
question. They are, however, taken into account when two fields
constructs are tested for equality.

Two numerical parameters ``a`` and ``b`` are considered equal if
``|a-b|<=atol+rtol|b|``, where ``atol`` (the tolerance on absolute
differences) and ``rtol`` (the tolerance on relative differences) are
positive, typically very small numbers. The data type of the numbers
is not taken into consideration. See the *atol* and *rtol* parameters.

Any type of object may be tested but, in general, equality is only
possible with another coordinate reference construct, or a subclass of
one. See the *ignore_type* parameter.

NetCDF elements, such as netCDF variable and dimension names, do not
constitute part of the CF data model and so are not checked.

.. versionadded:: 1.7

:Parameters:

    other: 
        The object to compare for equality.

    atol: float, optional
        The tolerance on absolute differences between real
        numbers. The default value is set by the `cfdm.ATOL` function.
        
    rtol: float, optional
        The tolerance on relative differences between real
        numbers. The default value is set by the `cfdm.RTOL` function.

    traceback: `bool`, optional
        If True then print information about differences that lead to
        inequality.

    ignore_type: `bool`, optional
        Any type of object may be tested but, in general, equality is
        only possible with another coordinate reference construct, or
        a subclass of one. If *ignore_type* is True then then
        ``CoordinateReference(source=other)`` is tested, rather than
        the ``other`` defined by the *other* parameter.

:Returns: 
  
    out: `bool`
        Whether the two coordinate reference constructs are equal.

**Examples:**

>>> c.equals(c)
True
>>> c.equals(c.copy())
True
>>> c.equals('not a coordinate reference')
False

        '''
        pp = super()._equals_preprocess(other, traceback=traceback,
                                        ignore_type=ignore_type)
        if pp in (True, False):
            return pp
        
        other = pp
        
#        # Check for object identity
#        if self is other:
#            return True
#
#        # Check that each object is of the same type
#        if ignore_type:
#            if not isinstance(other, self.__class__):
#                other = type(self)(source=other, copy=False)
#        elif not isinstance(other, self.__class__):
#            if traceback:
#                print("{0}: Incompatible types: {0}, {1}".format(
#		    self.__class__.__name__,
#		    other.__class__.__name__))
#            return False
        
#        if not super().equals(
#                other, #rtol=rtol, atol=atol,
#                traceback=traceback,
#                ignore_type=ignore_type):
#            return False

        coords0 = self.coordinates()
        coords1 = other.coordinates()
        if len(coords0) != len(coords1):
            if traceback:
                print(
"{}: Different sized collections of coordinates ({}, {})".format(
    self.__class__.__name__, coords0, coords1))
            return False

        if not self.coordinate_conversion.equals(
                other.coordinate_conversion,
                rtol=rtol, atol=atol,
                traceback=traceback,
                ignore_type=ignore_type):
            if traceback:
                print(
"{}: Different coordinate conversions".format(self.__class__.__name__))
            return False
        
        if not self.datum.equals(
                other.datum,
                rtol=rtol, atol=atol,
                traceback=traceback,
                ignore_type=ignore_type):
            if traceback:
                print(
"{}: Different datums".format(self.__class__.__name__))
            return False

        # Still here? Then the two coordinate references are as equal
        # as can be ascertained in the absence of domains.
        return True
    #--- End: def

    def name(self, default=None, ncvar=True, custom=None,
             all_names=False):
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

**Examples**

>>> n = r.name()
>>> n = r.name(default='NO NAME'))
'''
#        n = self.coordinate_conversion.get_parameter('standard_name', None)
#        if n is not None:
#            return n
#        
#        n = self.coordinate_conversion.get_parameter('grid_mapping_name', None)
#        if n is not None:
#            return n
#        
#        return default


        out = []

        if custom is None:
            custom = ('standard_name', 'grid_mapping_name')
        elif isinstance(custom, basestring):
            custom = (custom,)
            
        for prop in custom:
            n = self.coordinate_conversion.get_parameter(prop, None)
            if n is not None:
                out.append(str(n))
                if not all_names:
                    break
        #--- End: if
        
        if ncvar and (all_names or not out):
            n = self.nc_get_variable(None)
            if n is not None:
                out.append('ncvar%{0}'.format(n))
        #--- End: if

        if all_names:
            return out
        
        if out:
            return out[-1]

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
#**Examples**
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
