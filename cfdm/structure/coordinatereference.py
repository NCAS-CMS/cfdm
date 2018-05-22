import abc

from copy import deepcopy

import abstract

from .coordinateconversion import CoordinateConversion
from .datum                import Datum


class CoordinateReference(abstract.Container):
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
    __metaclass__ = abc.ABCMeta
    
    def __new__(cls, *args, **kwargs):
        obj = object.__new__(cls, *args, **kwargs)
        
        obj._CoordinateConversion = CoordinateConversion
        obj._Datum                = Datum

        return obj
    #--- End: def

    def __init__(self, coordinates=None, datum=None,
                 coordinate_conversion=None, source=None, copy=True):
        '''**Initialization**

:Parameters:

    coordinates: sequence of `str`, optional
        Identify the dimension and auxiliary coordinate objects which
        apply to this coordinate reference. By default the standard
        names of those expected by the CF conventions are used. For
        example:

    datum: `Datum`, optional
        Define the datum of the coordinate reference construct.

          *Example:*
            >>> d = Datum(parameters={'earth_radius': 6371007})
            >>> c = CoordinateReference(datum=d)

    coordinate_conversion: `CoordinateConversion`, optional
        Define the coordinate conversion formula of the coordinate
        reference construct.

          *Example:*
            >>> f = CoordinateConversion(
            ...         parameters={'standard_name': 'atmosphere_hybrid_height'},
            ...         domain_ancillaries={'orog': 'domainancillary2',
            ...                             'a': 'domainancillary0',
            ...                             'b': 'domainancillary1'}))
            ...
            >>> c = CoordinateReference(coordinate_conversion=f)

    source: optional
        Initialise the *coordinates*, *datum* and
        *coordinate_conversion* parameters from the *source* object.

    copy: `bool`, optional
        If False then do not deep copy arguments prior to
        initialization. By default arguments are deep copied.

        '''
        super(CoordinateReference, self).__init__(source=source)

        self._set_component('coordinates', None, set())
        
        if source:
            try:
                coordinates = source.coordinates()
            except AttributeError:
                coordinates = None

            try:
                coordinate_conversion = source.get_coordinate_conversion(None)
            except AttributeError:
                coordinate_conversion = None

            try:
                datum = source.get_datum(None)
            except AttributeError:
                datum = None
        #--- End: if
              
        self.coordinates(coordinates)
        self.set_coordinate_conversion(coordinate_conversion, copy=copy)
        self.set_datum(datum, copy=copy)
    #--- End: def
   
    def __str__(self):
        '''x.__str__() <==> str(x)

        '''    
        return ', '.join(sorted(self.terms()))
    #--- End: def

    @property
    def coordinate_conversion(self):
        '''
blah de balh
        '''
        out = self.get_coordinate_conversion(None)
        if out is None:
            out = self._CoordinateConversion
            self.set_coordinate_conversion(out)
            
        return out
    #--- End: def
        
    @property
    def datum(self):
        '''
blah de balh 2
        '''
        out = self.get_datum(None)
        if out is None:
            out = self._Datum()
            self.set_datum(out)
            
        return out
    #--- End: def

    def coordinates(self, coordinates=None, copy=True):
        '''Return or replace the identifiers of the coordinate objects that
define the coordinate system.

.. seealso:: `del_coordinate`, `set_coordinate`

:Examples 1:

>>> coordinates = c.coordinates()

:Returns:

    out: `set`
        The identifiers of the coordinate objects.

:Examples 2:

>>> c.coordinates()
{'dimensioncoordinate0',
 'dimensioncoordinate1',
 'auxiliarycoordinate0',
 'auxiliarycoordinate1'}

        '''
        existing = self._get_component('coordinates', None, None)

        if existing is None:
            existing = set()
            self._set_component('coordinates', None, existing)

        out = existing.copy()

        if not coordinates:
            return out

        # Still here?
        existing.clear()
        existing.update(coordinates)

        return out
    #--- End: def
            
    def copy(self):
        '''Return a deep copy.

``f.copy()`` is equivalent to ``copy.deepcopy(f)``.

.. versionadded:: 1.6

:Examples 1:

>>> g = f.copy()

:Returns:

    out:
        The deep copy.

        '''
        return type(self)(source=self, copy=True)
    #--- End: def

    def del_coordinate(self, key):
        '''Delete the identifier of a coordinate object that defines the
coordinate system.

.. versionadded:: 1.6

.. seealso:: `coordinates`

:Examples 1:

>>> c.del_coordinate('dimensioncoordinate1')

:Parameters:

    key: `str`

:Returns:

    `None`

:Examples 2:

>>> c.coordinates()
{'dimensioncoordinate0',
 'dimensioncoordinate1'}
>>> c.del_coordinate('dimensioncoordinate0')
>>> c.coordinates()
{'dimensioncoordinate1'}
        '''        
        self._get_component('coordinates', None).discard(key)
    #--- End: def
    
    def del_coordinate_conversion(self):
        '''
        '''
        coordinate_conversion = self.get_coordinate_conversion()
        self.set_coordinate_conversion(self._CoordinateConversion())
        return coordinate_conversion
    #--- End: def
    
    def del_datum(self):
        '''
        '''
        datum = self.get_datum()
        self.set_datum(self._Datum())
        return datum
    #--- End: def

    def get_coordinate_conversion(self, *default):
        '''Get the coordinate_conversion.

:Returns:

    out: `Datum`
        '''
        return self._get_component('coordinate_conversion', None, *default)
    #--- End: def
    
    def get_datum(self, *default):
        '''Get the datum.

:Returns:

    out: `Datum`
        '''
        return self._get_component('datum', None, *default)
    #--- End: def
    
    def has_datum(self):
        '''
        '''
        return bool(self._get_component('datum', None, False))
    #--- End: def

    def has_coordinate_conversion(self):
        '''
        '''
        return bool(self._get_component('coordinate_conversion', None, False))
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
            parameters = self.coordinate_conversion.parameters()

            n = parameters.get('standard_name')
            if n is not None:
                return n
                
            n = parameters.get('grid_mapping_name')
            if n is not None:
                return n
                
            if identity:
                return default

        elif identity:
            raise ValueError("Can't set identity=True and ncvar=True")

        n = self.get_ncvar(None)
        if n is not None:
            return 'ncvar%{0}'.format(n)
            
        return default
    #--- End: def

    def set_coordinate(self, coordinate):
        '''Set a coordinate.

.. versionadded:: 1.6

.. seealso:: `del_coordinate`

:Examples 1:

>>> c.set_coordinates('auxiliarycoordinate1')

:Parameters:

    coordinate: `str`

:Returns:

    `None`

:Examples 2:

>>> c.coordinates()
{'dimensioncoordinate0',
 'dimensioncoordinate1'}
>>> c.set_coordinates('auxiliarycoordinate0')
>>> c.coordinates()
{'dimensioncoordinate0',
 'dimensioncoordinate1',
 'auxiliarycoordinate0'}

        '''
        c = self._get_component('coordinates', None)
        c.add(coordinate)
    #--- End: def

    def set_coordinate_conversion(self, value, copy=True):
        '''
        '''
        if copy and value is not None:
            value = value.copy()
            
        self._set_component('coordinate_conversion', None, value)
    #--- End: def

    def set_datum(self, value, copy=True):
        '''
        '''
        if copy and value is not None:
            value = value.copy()
            
        self._set_component('datum', None, value)
    #--- End: def

#--- End: class
