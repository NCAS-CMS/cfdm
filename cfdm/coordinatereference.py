from __future__ import print_function
from __future__ import absolute_import
from builtins import (str, super)
from past.builtins import basestring

import abc

import csv
import os

from .                     import __file__
from .auxiliarycoordinate  import AuxiliaryCoordinate
from .coordinateconversion import CoordinateConversion
from .datum                import Datum
from .dimensioncoordinate  import DimensionCoordinate

from . import mixin
from . import structure


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
    
_datum_parameters  = set(_datum_parameters)
#_datum_ancillaries = set()


class CoordinateReference(mixin.Container, structure.CoordinateReference):
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
    orography data). A coordinate reference construct relates the
    field's coordinate values to locations in a planetary reference
    frame.

    '''

    _name_to_coordinates = _name_to_coordinates
    _datum_parameters    = _datum_parameters
#    _datum_ancillaries   = _datum_ancillaries

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        instance._CoordinateConversion = CoordinateConversion
        instance._Datum                = Datum
        return instance
#        obj = object.__new__(cls, *args, **kwargs)        
#        obj._CoordinateConversion = CoordinateConversion
#        obj._Datum                = Datum
#        return obj
    #--- End: def

    def __init__(self, coordinates=None, datum=None,
                 coordinate_conversion=None, domain_ancillaries=None,
                 parameters=None, source=None, copy=True):
        '''**Initialization**

:Parameters:

    coordinates: sequence of `str`, optional
        Identify the dimension and auxiliary coordinate objects which
        apply to this coordinate reference. 

          *Example:*
            ``coordinates=['dimensioncoordinate2']``

          *Example:*
            ``coordinates=('dimensioncoordinate0', 'dimensioncoordinate1', 'auxiliarycoordinate0', 'auxiliarycoordinate1')``

    parameters: `dict`, optional
        Define parameter-valued terms of both the coordinate
        conversion formula and the datum. A term is assumed to apply
        to the coordinate conversion formula unless it is one of the
        terms defined by `CoordinateReference._datum_parameters`, in
        which case the term applies to the datum.

          *Example:*
            In this case, the ``'earth_radius'`` term is applied to
            the datum and all of the other terms are applied to the
            coordinate conversion formula:

            >>> c = CoordinateReference(
            ...         parameters={'grid_mapping_name': 'rotated_latitude_longitude',
            ...                     'grid_north_pole_latitude': 38.0,
            ...                     'grid_north_pole_longitude': 190.0,
            ...                     'earth_radius': 6371007})
            ...
            >>> c.coordinate_conversion.parameters()
            {'grid_mapping_name': 'rotated_latitude_longitude',
             'grid_north_pole_latitude': 38.0,
             'grid_north_pole_longitude': 190.0}
            >>> c.datum.parameters()
            {'earth_radius': 6371007}

    domain_ancillaries: `dict`, optional
        Define domain ancillary-valued terms of both the coordinate
        conversion formula and the datum. A term is assumed to apply
        to the coordinate conversion formula unless it is one of the
        terms defined by
        `CoordinateReference._datum_ancillaries`, in which case
        the term applies to the datum.

          *Example:*
            In this case, all terms are applied to the coordinate
            conversion formula:

            >>> c = CoordinateReference(
            ...         domain_ancillaries={'orog': 'domainancillary2',
            ...                             'a': 'domainancillary0',
            ...                             'b': 'domainancillary1'})
            ...
            >>> c.coordinate_conversion.domain_ancillaries()
            {'a': 'domainancillary0',
             'b': 'domainancillary1',
             'orog': 'domainancillary2'}
            >>> c.datum.domain_ancillaries()
            {}

    datum: `Datum`, optional
        Define the datum of the coordinate reference construct. Cannot
        be used with the *parameters* nor *domain_ancillaries*
        keywords.

          *Example:*
            >>> d = Datum(parameters={'earth_radius': 6371007})
            >>> c = CoordinateReference(datum=d)

    coordinate_conversion: `CoordinateConversion`, optional
        Define the coordinate conversion formula of the coordinate
        reference construct. Cannot be used with the *parameters* nor
        *domain_ancillaries* keywords.

          *Example:*
            >>> f = CoordinateConversion(
            ...         parameters={'standard_name': 'atmosphere_hybrid_height'},
            ...         domain_ancillaries={'orog': 'domainancillary2',
            ...                             'a': 'domainancillary0',
            ...                             'b': 'domainancillary1'})
            ...
            >>> c = CoordinateReference(coordinate_conversion=f)

    source: optional
        Initialise the *coordinates*, *datum* and
        *coordinate_conversion* parameters from the object given by
        *source*.

    copy: `bool`, optional
        If False then do not deep copy arguments prior to
        initialization. By default arguments are deep copied.

        '''
        if source is None:
            if parameters is not None or domain_ancillaries is not None:
                if datum is not None or coordinate_conversion is not None:
                    raise ValueError(" xcawed we2q3 \a")

                datum_parameters = {}
                coordinate_conversion_parameters = {}

#                datum_domain_ancillaries = {}
                coordinate_conversion_domain_ancillaries = {}

                if parameters is not None:
                    for x, value in parameters.items():
                        if x in self._datum_parameters:
                            datum_parameters[x] = value
                        else:
                            coordinate_conversion_parameters[x] = value
                #-- End: if
            
                if domain_ancillaries is not None:                 
                    for x, value in domain_ancillaries.items():
#                        if x in self._datum_ancillaries:
#                            datum_domain_ancillaries[x] = value
#                        else:
                        coordinate_conversion_domain_ancillaries[x] = value
                #-- End: if

                datum = self._Datum(
                    parameters=datum_parameters)
        
                coordinate_conversion = self._CoordinateConversion(
                    parameters=coordinate_conversion_parameters,
                    domain_ancillaries=coordinate_conversion_domain_ancillaries)
        #--- End: if
            
#        super(CoordinateReference, self).__init__(
        super().__init__(
            coordinates=coordinates,
            datum=datum,
            coordinate_conversion=coordinate_conversion,
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
        if field:
            for key in sorted(self.coordinates()):
                coord = field.coordinates().get(key)
                if coord is not None:
                    if isinstance(coord, DimensionCoordinate):
                        coord = 'Dimension Coordinate: '+coord.name(default='key%'+key)
                    elif isinstance(coord, AuxiliaryCoordinate):
                        coord = 'Auxiliary Coordinate: '+coord.name(default='key%'+key)
                    else:
                        coord = coord.name(default=key)

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
               ignore_data_type=False, ignore_fill_value=False,
               ignore_construct_type=False):
        '''True if two instances are equal, False otherwise.

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
#        if not super(CoordinateReference, self).equals(
        if not super().equals(
                other, rtol=rtol, atol=atol,
                traceback=traceback,
                ignore_construct_type=ignore_construct_type):
            return False

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
                ignore_construct_type=ignore_construct_type):
            if traceback:
                print(
"{}: Different coordinate conversions".format(self.__class__.__name__))
            return False
        
        if not self.datum.equals(
                other.datum,
                rtol=rtol, atol=atol,
                traceback=traceback,
                ignore_construct_type=ignore_construct_type):
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

:Examples 1:

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
            n = self.get_ncvar(None)
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
