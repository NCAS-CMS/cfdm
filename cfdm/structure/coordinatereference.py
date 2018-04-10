import abc

from copy import deepcopy

import abstract

# ====================================================================
#
# CoordinateReference object
#
# ====================================================================

class CoordinateReference(abstract.Properties):
    '''A coordinate reference construct of the CF data model. 

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
    orography data) A coordinate reference construct relates the
    field's coordinate values to locations in a planetary reference
    frame.

    '''
    __metaclass__ = abc.ABCMeta
    
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

        '''
        super(CoordinateReference, self).__init__(
            properties=properties,
            source=source,
            copy=copy)
              
        if source and  isinstance(source, CoordinateReference):
            if coordinates is None:
                coordinates = source.coordinates()
            else:
                coordinates = set(coordinates)
                coordinates.update(source.coordinates())
                
            if datum is None:
                datum = source.get_datum(None)

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

        if datum is not None:
            if copy:
                datum = datum.copy()
                
            self.set_datum(datum, copy=False)
        #--- End: if                

        if not coordinates:
            coordinates = set()
        else:
            coordinates = set(coordinates)

        if not domain_ancillaries:
            domain_ancillaries = {}
        else:
            domain_ancillaries = domain_ancillaries.copy()

        if not parameters:
            parameters = {}
        elif copy:
            parameters = deepcopy(parameters)
        else:
            parameters = parameters.copy()

        self._set_component('coordinates'       , None, coordinates)
        self._set_component('domain_ancillaries', None, domain_ancillaries)
        self._set_component('parameters'        , None, parameters)
    #--- End: def
   
    def __str__(self):
        '''x.__str__() <==> str(x)

        '''    
        return ', '.join(sorted(self.properties().values()))
    #--- End: def

    def coordinates(self):
        '''Return the identifiers of the coordinate objects that define the
coordinate system.

.. versionadded:: 1.6

.. seealso:: `del_coordinate`

:Examples 1:

>>> s = c.coordinates()

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
        return self._get_component('coordinates', None).copy()
    #--- End: def

    def del_datum(self):
        '''
        '''
        return self._del_component('datum')
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
    
    def del_term(self, term):
        '''Delete a term from the coordinate conversion formula.

.. versionadded:: 1.6

:Examples 1:

>>> v = c.del_term('orog')

:Parameters:

    term: `str`
        The name of the term to be deleted.

:Returns:

    out:
        The value of the deleted term, or `None` if the term did not exist.

:Examples 2:

>>> v = c.del_term('a')

>>> v = c.del_term('false_northing')

        '''
        value = self._get_component('domain_ancillaries', None).pop(term, None)
        if value is None:
            value = self._get_component('parameters', None).pop(term, None)

        return value
    #--- End: def

    def domain_ancillaries(self):
        '''Return the domain ancillary-valued coordinate conversion terms.

.. versionadded:: 1.6

.. seealso:: `parameters`

:Examples 1:

>>> d = c.domain_ancillaries()

:Returns:

    out: `dict`
        The domain ancillary-valued terms and their values.

:Examples 2:

>>> c.domain_ancillaries()
{'a': 'domainancillary0',
 'b': 'domainancillary2',
 'orog': 'domainancillary1'}

>>> c.domain_ancillaries()
{}
        '''
        return self._get_component('domain_ancillaries', None, {}).copy()
    #--- End: def

    def get_datum(self, *default):
        '''
        '''
        return self._get_component('datum', None, *default)       
    #--- End: def

    def get_term(self, term, *default):
        '''Get the value of a term of the coordinate conversion formula.

.. versionadded:: 1.6

:Examples 1:

>>> v = c.get_term('false_northing')

:Parameters:

    term: `str`
        The name of the term.

    default: optional

:Returns:

    out:
        The value of the term <SOMETING BAOUT DEFAULT>

:Examples 2:

>>> c.get_term('b')
'domainancillary2'

>>> c.get_term('grid_north_pole_latitude')
70.0

>>> c.get_term('foo')
ERROR
>>> c.get_term('foo', 'nonexistent term')
'nonexistent term'


        '''
        d = self._get_component('domain_ancillaries', None)
        if term in d:
            return d[term]
        
        d = self._get_component('parameters', None)
        if term in d:
            return d[term]
        
        if default:
            return default[0]

        raise AttributeError("{} doesn't have formula term {!r}".format(
                self.__class__.__name__, term))
    #--- End: def
    
    def has_datum(self):
        '''
        '''
        return self._has_component('datum')
    #--- End: def

    def has_term(self, term):
        '''Return whether a coordinate conversion formula term has been set.

.. versionadded:: 1.6

:Examples 1:

>>> v = c.has_term('orog')

:Parameters:

    term: `str`
        The name of the term.

:Returns:

    out: `bool`
        True if the coordinate conversion formula as the term , False
        oterwise.

:Examples 2:

>>> v = c.has_term('a')

>>> v = c.has_term('false_northing')

        '''
        return (self._has_component('domain_ancillaries', term) or
                self._has_component('parameters', term))
    #--- End: def

    def insert_coordinate(self, coordinate):
        '''
        '''
        c = self._get_component('coordinates', None)
        c.add(coordinate)
    #--- End: def

    def parameters(self):
        '''Return the parmaeter-valued coordinate conversion terms.

.. versionadded:: 1.6

.. seealso:: `domain_ancillaries`

:Examples 1:

>>> d = c.parameters()

:Returns:

    out: `dict`
        The parameter-valued terms and their values.

:Examples 2:

>>> c.parameters()
{'standard_parallel': 25.0;
 'longitude_of_central_meridian': 265.0,
 'latitude_of_projection_origin': 25.0}

>>> c.parameters()
{}

        '''
        return self._get_component('parameters', None, {}).copy()
    #--- End: def

    def remove_coordinate(self, coordinate):
        ''' 
        '''
        c = self._get_component('coordinates', None)
        c.discard(coordinate)
    #--- End: def
    
    def set_datum(self, value, copy=True):
        '''
        '''
        if copy:
            value = deepcopy(value)
            
        self._set_component('datum', None, value)
    #--- End: def

    def set_domain_ancillary(self, term, value, copy=True):
        '''
        '''
        self._set_component('domain_ancillaries', term, value)
    #--- End: def
    
    def set_parameter(self, term, value, copy=True):
        '''
'''
        if copy:
            value = deepcopy(value)
            
        self._set_component('parameters', term, value)
    #--- End: def
    
    def terms(self):
        '''
        '''
        out = self.parameters()
        out.update(self.domain_ancillaries())
        return out
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

#--- End: class
