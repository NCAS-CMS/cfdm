from builtins import super

from . import abstract

from . import CoordinateConversion
from . import Datum


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
    
    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        instance._CoordinateConversion = CoordinateConversion
        instance._Datum                = Datum
        return instance
    #--- End: def

    def __init__(self, coordinates=None, datum=None,
                 coordinate_conversion=None, source=None, copy=True):
        '''**Initialization**

:Parameters:

    coordinates: sequence of `str`, optional
        Identify the dimension and auxiliary coordinate objects which
        apply to this coordinate reference. By default the standard
        names of those expected by the CF conventions are
        used. Ignored if the *source* parameter is set.

        Coordinates may also be set after initialisation with the
        `coordinates` and `set_coordinate` methods.
  
    datum: `Datum`, optional
        Set the datum. Ignored if the *source* parameter is set.

        The datum may also be set after initialisation with the
        `set_datum` method.
  
          *Example:*
            >>> d = Datum(parameters={'earth_radius': 6371007})
            >>> c = CoordinateReference(datum=d)

    coordinate_conversion: `CoordinateConversion`, optional
        Set the coordinate conversion formula. Ignored if the *source*
        parameter is set.

        The coordinate conversion formula may also be set after
        initialisation with the `set_coordinate conversion` method.
  
          *Example:*
            >>> f = CoordinateConversion(
            ...         parameters={'standard_name': 'atmosphere_hybrid_height'},
            ...         domain_ancillaries={'orog': 'domainancillary2',
            ...                             'a': 'domainancillary0',
            ...                             'b': 'domainancillary1'}))
            ...
            >>> c = CoordinateReference(coordinate_conversion=f)

    source: optional
         Override the *coordinates*, *datum* and
         *coordinate_conversion* parameters with
         ``source.coordinates()``, ``source.get_datum()`` and
         ``source.get_coordinate_conversion()`` respectively.

        If *source* does not have one of these methods, or it can not
        return anything, then that parameter is not set.
        
    copy: `bool`, optional
        If False then do not deep copy arguments prior to
        initialization. By default arguments are deep copied.

        '''
        super().__init__()

        self._set_component('coordinates', set(), copy=False)
        
        if source:
            try:
                coordinates = source.coordinates()
            except AttributeError:
                coordinates = None

            try:
                coordinate_conversion = source.get_coordinate_conversion()
            except AttributeError:
                coordinate_conversion = None

            try:
                datum = source.get_datum()
            except AttributeError:
                datum = None
        #--- End: if
              
        self.coordinates(coordinates)
        self.set_coordinate_conversion(coordinate_conversion, copy=copy)
        self.set_datum(datum, copy=copy)
    #--- End: def
   
#    def __str__(self):
#        '''x.__str__() <==> str(x)
#
#        '''    
#        return ', '.join(sorted(self.terms()))
#    #--- End: def

    @property
    def construct_type(self):
        '''Return a description of the construct type.
        
.. versionadded:: 1.7
        
:Returns:

    out: `str`
        The construct type.

        '''
        return 'coordinate_reference'

    @property
    def coordinate_conversion(self):
        '''Return the coordinate conversion.

.. versionadded:: 1.7

..seealso:: `datum`, `get_coordinate_conversion`

:Returns:

    out: `CoordinateConversion`
        The coordinate conversion.

**Examples**

>>> c.coordinate_conversion
<>
        '''
        return self.get_coordinate_conversion()
    #--- End: def
        
    @property
    def datum(self):
        '''Return the datum.

.. versionadded:: 1.7

..seealso:: `coordinate_conversion`, `datum`

:Returns:

   out: `Datum`
        The datum.

**Examples**

>>> c.datum
<>
        '''
        return self.get_datum()
    #--- End: def

    def coordinates(self, coordinates=None):
        '''Return or replace the identifiers of the coordinate objects that
define the coordinate system.

.. seealso:: `del_coordinate`, `set_coordinate`

:Examples 1:

>>> coordinates = c.coordinates()

:Returns:

    out: `set`
        The identifiers of the coordinate objects.

**Examples**

>>> c.coordinates()
{'dimensioncoordinate0',
 'dimensioncoordinate1',
 'auxiliarycoordinate0',
 'auxiliarycoordinate1'}

        '''
        out = self._get_component('coordinates').copy()

        if coordinates is not None:
            self._set_component('coordinates', set(coordinates), copy=False)

        return out
    #--- End: def
            
    def copy(self):
        '''Return a deep copy.

``f.copy()`` is equivalent to ``copy.deepcopy(f)``.

.. versionadded:: 1.7

:Examples 1:

>>> g = f.copy()

:Returns:

    out:
        The deep copy.

        '''
        return type(self)(source=self, copy=True)
    #--- End: def

    def del_coordinate(self, key, *default):
        '''Delete the identifier of a coordinate object that defines the
coordinate system.

.. versionadded:: 1.7

.. seealso:: `coordinates`

:Parameters:

    key: `str`

          *Example:*
             ``key='dimensioncoordinate1'``

    default: optional
        Return *default* if the coordinate key has not been set.

:Returns:

    out: 
        The removed coordinate key. If unset then *default* is
        returned, if provided.

**Examples**

>>> c.coordinates()
{'dimensioncoordinate0',
 'dimensioncoordinate1'}
>>> c.del_coordinate('dimensioncoordinate0')
>>> c.coordinates()
{'dimensioncoordinate1'}

        '''
        coordinates = self._get_component('coordinates')
        if key in coordinates:
            coordinates.remove(key)
            return key

        if default:
            return default[0]
        
        raise AttributeError("{!r} has no {!r} coordinate".format(
            self.__class__.__name__, key))
    #--- End: def
    
    def del_coordinate_conversion(self, *default):
        '''Remove the coordinate conversion.

.. versionadded:: 1.7

..seealso:: `coordinate_conversion`, `get_coordinate_conversion`,
            `has_coordinate_conversion`, `set_coordinate_conversion`

:Parameters:

    default: optional
        Return *default* if the coordinate conversion has not been
        set.

:Returns:

    out: 
        The removed coordinate conversion. If unset then *default* is
        returned, if provided.

**Examples**

        '''
        new = self._CoordinateConversion()
        out = self._del_component('coordinate_conversion', new)
        self.set_coordinate_conversion(new)
        return out
    #--- End: def
    
    def del_datum(self):
        '''Remove the datum.

.. versionadded:: 1.7

..seealso:: `datum`, `get_datum`, `has_datum`, `set_datum`

        :Returns:

    out: 
        The removed datum.

**Examples**

        '''
        new = self._Datum()
        out = self._del_component('datum', new)
        self.set_datum(new)
        return out
    #--- End: def

    def get_coordinate_conversion(self):
        '''Get the coordinate conversion.

.. versionadded:: 1.7

..seealso:: `coordinate_conversion`, `del_coordinate_conversion`,
            `has_coordinate_conversion`, `set_coordinate_conversion`

:Returns:

    out: `CoordinateConversion`
        The coordinate conversion.

**Examples**

        '''
        out = self._get_component('coordinate_conversion', None)
        if out is None:
            out = self._CoordinateConversion()
            self.set_coordinate_conversion(out)

        return out
    #--- End: def
    
    def get_datum(self):
        '''Return the datum.

.. versionadded:: 1.7

..seealso:: `datum`, `get_coordinate_conversion`

:Returns:

   out: `Datum`
        The datum.

**Examples**
        '''
        out = self._get_component('datum', None)
        if out is None:
            out = self._Datum()
            self.set_datum(out)
            
        return out
    #--- End: def
    
    def has_datum(self):
        '''TODO
        '''
        return self._has_component('datum')
    #--- End: def

    def has_coordinate_conversion(self):
        '''TODO
        '''
        return self._has_component('coordinate_conversion')
    #--- End: def

    def set_coordinate(self, coordinate):
        '''Set a coordinate.

.. versionadded:: 1.7

.. seealso:: `del_coordinate`

:Examples 1:

>>> c.set_coordinates('auxiliarycoordinate1')

:Parameters:

    coordinate: `str`

:Returns:

    `None`

**Examples**

>>> c.coordinates()
{'dimensioncoordinate0',
 'dimensioncoordinate1'}
>>> c.set_coordinates('auxiliarycoordinate0')
>>> c.coordinates()
{'dimensioncoordinate0',
 'dimensioncoordinate1',
 'auxiliarycoordinate0'}

        '''
        c = self._get_component('coordinates')
        c.add(coordinate)
    #--- End: def

    def set_coordinate_conversion(self, value, copy=True):
        '''TODO
        '''
        if copy and value is not None:
            value = value.copy()
            
        self._set_component('coordinate_conversion', value, copy=False)
    #--- End: def

    def set_datum(self, value, copy=True):
        '''TODO
        '''
        if copy and value is not None:
            value = value.copy()
            
        self._set_component('datum', value, copy=False)
    #--- End: def

#--- End: class
