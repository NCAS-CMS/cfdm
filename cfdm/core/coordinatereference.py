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
  constructs that define the coordinate system to which the coordinate
  reference construct applies. Note that the coordinate values are not
  relevant to the coordinate reference construct, only their
  properties.

..

* A definition of a datum specifying the zeroes of the dimension and
  auxiliary coordinate constructs which define the coordinate
  system. The datum may be implied by the metadata of the referenced
  dimension and auxiliary coordinate constructs, or explicitly
  provided.

..

* A coordinate conversion, which defines a formula for converting
  coordinate values taken from the dimension or auxiliary coordinate
  constructs to a different coordinate system. A coordinate
  reference construct relates the coordinate values of the field to
  locations in a planetary reference frame.

.. versionadded:: 1.7.0

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
        Identify the related dimension and auxiliary coordinate
        constructs by their construct identifiers. Ignored if the
        *source* parameter is set.

        *Parameter example:*
          ``coordinates=['dimensioncoordinate2']``

        *Parameter example:*
          ``coordinates=('dimensioncoordinate0', 'dimensioncoordinate1')``

        The coordinates may also be set after initialisation with the
        `coordinates` and `set_coordinate` methods.

    datum: `Datum`, optional
        Set the datum component of the coordinate reference
        construct. Ignored if the *source* parameter is set.

        The datum may also be set after initialisation with the
        `set_datum` method.

    coordinate_conversion: `CoordinateConversion`, optional
        Set the coordinate conversion component of the coordinate
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

    # ----------------------------------------------------------------
    # Attributes
    # ----------------------------------------------------------------
    @property
    def construct_type(self):
        '''Return a description of the construct type.
        
.. versionadded:: 1.7.0
        
:Returns:

    `str`
        The construct type.

        '''
        return 'coordinate_reference'

    @property
    def coordinate_conversion(self):
        '''Return the coordinate conversion component.

.. versionadded:: 1.7.0

.. seealso:: `datum`, `get_coordinate_conversion`

:Returns:

    `CoordinateConversion`
        The coordinate conversion.

**Examples:**

>>> c.coordinate_conversion
<>
        '''
        return self.get_coordinate_conversion()
    #--- End: def
        
    @property
    def datum(self):
        '''Return the datum component.

.. versionadded:: 1.7.0

.. seealso:: `coordinate_conversion`, `datum`

:Returns:

   `Datum`
        The datum.

**Examples:**

>>> c.datum
<>
        '''
        return self.get_datum()
    #--- End: def

    # ----------------------------------------------------------------
    # Methods
    # ----------------------------------------------------------------
    def coordinates(self, coordinates=None):
        '''Return or replace all references to coordinate constructs.

.. seealso:: `del_coordinate`, `set_coordinate`

:Parameters:

    coordinates: sequence of `str`

:Returns:

    `set`
        The identifiers of the coordinate objects.

**Examples:**

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

.. versionadded:: 1.7.0

:Returns:

        The deep copy.

**Examples:**

>>> d = c.copy()

        '''
        return type(self)(source=self, copy=True)
    #--- End: def

    def del_coordinate(self, cid, *default):
        '''Remove a reference to a coordinate construct.

.. versionadded:: 1.7.0

.. seealso:: `coordinates`, `set_coordinate`

:Parameters:

    cid: `str`
        The construct identifier of the coordinate construct.

          *Parameter example:*
             ``cid='dimensioncoordinate1'``

          *Parameter example:*
             ``cid='auxiliarycoordinate0'``

    default: optional
        Return *default* if the coordinate construct has not been
        referenced.

:Returns:

      The removed coordinate construct identifier property. If unset
      then *default* is returned, if provided.

**Examples:**

>>> c.coordinates()
{'dimensioncoordinate0',
 'dimensioncoordinate1'}
>>> c.del_coordinate('dimensioncoordinate0')
'dimensioncoordinate0'
>>> c.coordinates()
{'dimensioncoordinate1'}
>>> c.del_coordinate('dimensioncoordinate0', 'not set')
'not set'

        '''
        coordinates = self._get_component('coordinates')
        if cid in coordinates:
            coordinates.remove(cid)
            return cid

        if default:
            return default[0]
        
        raise AttributeError("{!r} has no {!r} coordinate".format(
            self.__class__.__name__, cid))
    #--- End: def
    
    def del_coordinate_conversion(self):
        '''Remove the coordinate conversion component.

.. versionadded:: 1.7.0

.. seealso:: `coordinate_conversion`, `get_coordinate_conversion`,
             `set_coordinate_conversion`

:Returns:

        The removed coordinate conversion component.

**Examples:**

>>> c.del_coordinate_conversion()
<CoordinateConversion: Parameters(grid_mapping_name, grid_north_pole_latitude, grid_north_pole_longitude)>
>>> c.get_coordinate_conversion()
<CoordinateConversion: >

        '''
        new = self._CoordinateConversion()
        out = self._del_component('coordinate_conversion', new)
        self.set_coordinate_conversion(new)
        return out
    #--- End: def
    
    def del_datum(self):
        '''Remove the datum component.

.. versionadded:: 1.7.0

.. seealso:: `datum`, `get_datum`, `set_datum`

:Returns:

        The removed datum component.

**Examples:**

>>> c.del_datum()
<Datum: Parameters(earth_radius)>
>>> c.get_datum()
<Datum: >

        '''
        new = self._Datum()
        out = self._del_component('datum', new)
        self.set_datum(new)
        return out
    #--- End: def

    def get_coordinate_conversion(self):
        '''Get the coordinate conversion component.

.. versionadded:: 1.7.0

.. seealso:: `coordinate_conversion`, `del_coordinate_conversion`,
             `set_coordinate_conversion`

:Returns:

    `CoordinateConversion`
        The coordinate conversion component.

**Examples:**

>>> c.get_coordinate_conversion()
<CoordinateConversion: Parameters(grid_mapping_name, grid_north_pole_latitude, grid_north_pole_longitude)>

        '''
        out = self._get_component('coordinate_conversion', None)
        if out is None:
            out = self._CoordinateConversion()
            self.set_coordinate_conversion(out)

        return out
    #--- End: def
    
    def get_datum(self):
        '''Return the datum component.

.. versionadded:: 1.7.0

.. seealso:: `datum`, `get_coordinate_conversion`

:Returns:

   `Datum`
        The datum component.

**Examples:**

>>> c.get_datum()
<Datum: Parameters(earth_radius)>

        '''
        out = self._get_component('datum', None)
        if out is None:
            out = self._Datum()
            self.set_datum(out)
            
        return out
    #--- End: def
    
    def set_coordinate(self, cid):
        '''Set a reference to a coordinate construct.

.. versionadded:: 1.7.0

.. seealso:: `coordinates`, `del_coordinate`

:Parameters:

    cid: `str`
        The construct identifier of the coordinate construct.

          *Parameter example:*
             ``cid='dimensioncoordinate1'``

          *Parameter example:*
             ``cid='auxiliarycoordinate0'``

:Returns:

    `None`

**Examples:**

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
        c.add(cid)
    #--- End: def

    def set_coordinate_conversion(self, coordinate_conversion, copy=True):
        '''Set the coordinate conversion component.

.. versionadded:: 1.7.0

.. seealso:: `coordinate_conversion`, `del_coordinate_conversion`,
             `get_coordinate_conversion`

:Parameters:

    coordinate_conversion: `CoordinateConversion`
        The coordinate conversion component to be inserted.

    copy: `bool`, optional
        If False then do not copy the coordinate conversion prior to
        insertion. By default the coordinate conversion is copied.

:Returns:

    `None`

**Examples:**

>>> c.set_coordinate_conversion(cc)

>>> c.set_coordinate_conversion(cc, copy=False)

        '''
        if copy and coordinate_conversion is not None:
            coordinate_conversion = coordinate_conversion.copy()
            
        self._set_component('coordinate_conversion',
                            coordinate_conversion, copy=False)
    #--- End: def

    def set_datum(self, datum, copy=True):
        '''Set the datum component.

.. versionadded:: 1.7.0

.. seealso:: `datum`, `del_datum`, `get_datum`

:Parameters:

    datum: `Datum`
        The datum component to be inserted.

    copy: `bool`, optional
        If False then do not copy the datum prior to insertion. By
        default the datum is copied.

:Returns:

    `None`

**Examples:**

>>> c.set_datum(d)

>>> c.set_datum(d, copy=False)

        '''
        if copy and datum is not None:
            datum = datum.copy()
            
        self._set_component('datum', datum, copy=False)
    #--- End: def

#--- End: class
