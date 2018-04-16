import abc

from copy import deepcopy

import abstract

# ====================================================================
#
# CoordinateReference object
#
# ====================================================================

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
    orography data) A coordinate reference construct relates the
    field's coordinate values to locations in a planetary reference
    frame.

    '''
    __metaclass__ = abc.ABCMeta
    
    def __init__(self,
                 coordinates=None,
                 coordinate_conversion_domain_ancillaries=None,
                 coordinate_conversion_parameters=None,
                 datum_domain_ancillaries=None,
                 datum_parameters=None,
                 source=None,
                 copy=True):
        '''**Initialization**

:Parameters:

    coordinates: sequence of `str`, optional
        Identify the dimension and auxiliary coordinate objects which
        apply to this coordinate reference. By default the standard
        names of those expected by the CF conventions are used. For
        example:

        '''
        super(CoordinateReference, self).__init__(
            source=source,
            copy=copy)

        if source:
            coordinates           = source.coordinates()
            coordinate_conversion = source.get_coordinate_conversion()
            datum                 = source.get_datum()

            if copy:
                coordinate_conversion = coordinate_conversion.copy()
                datum                 = datum.copy()
        else:
            if not coordinates:
                coordinates = set()
            else:
                coordinates = set(coordinates)

            if coordinate_conversion_parameters is None:
                coordinate_conversion_parameters = {}

            if coordinate_conversion_domain_ancillaries is None:
                coordinate_conversion_domain_ancillaries = {}

            coordinate_conversion = Terms(
                domain_ancillaries=coordinate_conversion_domain_ancillaries,
                parameters=coordinate_conversion_parameters,
                copy=copy)
            
            if datum_parameters is None:
                datum_parameters = {}
                
            if datum_domain_ancillaries is None:
                datum_domain_ancillaries = {}

            datum = Terms(
                domain_ancillaries=datum_domain_ancillaries,
                parameters=datum_parameters,
                copy=copy)
        #--- End: if
              
        self._set_component('coordinates', None, coordinates)
        self.set_coordinate_conversion(coordinate_conversion)
        self.set_datum(datum)
    #--- End: def
   
    def __str__(self):
        '''x.__str__() <==> str(x)

        '''    
        return ', '.join(sorted(self.terms()))
    #--- End: def

    @property
    def coordinate_conversion(self):
        '''
        '''
        return self.get_coordinate_conversion()
    #--- End: def
        
    @property
    def datum(self):
        '''
        '''
        return self.get_datum()
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
        self.set_coordinate_conversion(Terms())
        return coordinate_conversion
    #--- End: def
    
    def del_datum(self):
        '''
        '''
        datum = self.get_datum()
        self.set_datum(Terms())
        return datum
    #--- End: def
    
    def get_coordinate_conversion(self):
        '''Get the coordinate_conversion.

:Returns:

    out: `Datum`
        '''
        return self._get_component('coordinate_conversion', None)       
    #--- End: def

    def get_datum(self):
        '''Get the datum.

:Returns:

    out: `Datum`
        '''
        return self._get_component('datum', None)       
    #--- End: def
    
    def has_datum(self):
        '''
        '''
        return bool(self._get_component('datum', None, False))
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

    def set_datum(self, value, copy=True):
        '''
        '''
        if copy:
            value = value.copy()
            
        self._set_component('datum', None, value)
    #--- End: def

    def set_coordinate_conversion(self, value, copy=True):
        '''
        '''
        if copy:
            value = value.copy()
            
        self._set_component('coordinate_conversion', None, value)
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
            parameter_terms = self.coordinate_conversion.parameters()

            n = parameter_terms.get('standard_name')
            if n is not None:
                return n
                
            n = parameter_terms.get('grid_mapping_name')
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

#--- End: class



# ====================================================================
#

#
# ====================================================================

class Terms(abstract.Container):
    '''
    '''
    __metaclass__ = abc.ABCMeta


    def __init__(self, domain_ancillaries=None, parameters=None,
                 source=None, copy=True):
        '''**Initialization**

:Parameters:

    source: optional

    copy: `bool`, optional

        '''
        super(Terms, self).__init__(source=source, copy=copy)

        if source:
            parameters         = source.parameters()            
            domain_ancillaries = source.domain_ancillaries()
        else:
            if not domain_ancillaries:
                domain_ancillaries = {}

            if not parameters:
                parameters = {}
        #--- End: if
        
        if domain_ancillaries:
            self.domain_ancillaries(domain_ancillaries, copy=copy)

        if parameters:
            self.parameters(parameters, copy=copy)
    #--- End: def

    def __str__(self):
        '''x.__str__() <==> str(x)

        '''
        out = []

        parameters = self.parameters()
        if parameters:
            out.append('Parameters: {0}'.format(', '.join(sorted(parameters))))
            
        domain_ancillaries = self.domain_ancillaries()
        if domain_ancillaries:
            out.append('Domain ancillaries: {0}'.format(', '.join(sorted(domain_ancillaries))))
            
        return '; '.join(out)
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

    def del_term(self, term):
        '''Delete a term.

To delete a term's value but retain term as a placeholder, use the
`del_term_value` method.

.. versionadded:: 1.6

.. seealso:: `del_term_value`, `get_term`, `terms`

:Examples 1:

>>> v = c.del_term('orog')

:Parameters:

    term: `str`
        The name of the term to be deleted.

:Returns:

    out:
        The value of the deleted term, or `None` if the term did not
        exist.

:Examples 2:

>>> c.terms()
{'standard_parallel': 25.0;
 'longitude_of_central_meridian': 265.0,
 'latitude_of_projection_origin': 25.0}
>>> v = c.del_term('standard_parallel')
>>> c.terms()
{'longitude_of_central_meridian': 265.0,
 'latitude_of_projection_origin': 25.0}

>>> c.terms()
{'a': 'domainancillary0',
 'b': 'domainancillary2',
 'orog': 'domainancillary1'}
>>> c.del_term('b')
>>> c.terms()
{'a': 'domainancillary0',
 'orog': 'domainancillary1'}

        '''
        value = self._get_component('domain_ancillaries', None).pop(term, None)
        if value is None:
            value = self._get_component('parameters', None).pop(term, None)

        return value
    #--- End: def

    def del_term_value(self, term):
        '''Delete the value term.

The term is retained as a placeholder. To completely remove a term,
use the `del_term` method.

.. versionadded:: 1.6

.. seealso:: `del_term`, `get_term`, `terms`

:Examples 1:

>>> v = c.del_term_value('orog')

:Parameters:

    term: `str`
        The name of the term whose value is to be deleted.

:Returns:

    out:
        The deleted value, or `None` if the term did not exist.

:Examples 2:

>>> c.terms()
{'standard_parallel': 25.0;
 'longitude_of_central_meridian': 265.0,
 'latitude_of_projection_origin': 25.0}
>>> v = c.del_term_value('standard_parallel')
>>> c.terms()
{'standard_parallel': None,
 'longitude_of_central_meridian': 265.0,
 'latitude_of_projection_origin': 25.0}

>>> c.terms()
{'a': 'domainancillary0',
 'b': 'domainancillary2',
 'orog': 'domainancillary1'}
>>> c.del_term_value('b')
>>> c.terms()
{'a': 'domainancillary0',
 'b': None,
 'orog': 'domainancillary1'}

        '''
        value = self._get_component('domain_ancillaries', None).pop(term, None)
        if value is None:
            value = self._get_component('parameters', None).pop(term, None)

        return value
    #--- End: def

    def domain_ancillaries(self, domain_ancillaries=None, copy=True):
        '''Return or replace the domain_ancillary-valued terms.

.. versionadded:: 1.6

.. seealso:: `parameters`

:Examples 1:

>>> d = c.domain_ancillaries()

:Parameters:

    domain_ancillaries: `dict`, optional
        Replace all domain ancillary-valued terms with those provided.

          *Example:*
            ``domain_ancillies={'a': 'domainancillary0',
                                'b': 'domainancillary1',
                                'orog': 'domainancillary2'}``

    copy: `bool`, optional

:Returns:

    out: `dict`
        The domain ancillary-valued terms and their values. If the
        *domain_ancillaries* keyword has been set then the domain
        ancillary-valued terms prior to replacement are returned.

:Examples 2:

        '''
#        return self._get_component('domain_ancillaries', None, {}).copy()

        existing = self._get_component('domain_ancillaries', None, None)

        if existing is None:
            existing = {}
            self._set_component('domain_ancillaries', None, existing)

        out = existing.copy()

        if not domain_ancillaries:
            return out

        # Still here?
        if copy:
            parameters = deepcopy(domain_ancillaries)

        existing.clear()
        existing.update(domain_ancillaries)

        return out
    #--- End: def

    def get_term(self, term, *default):
        '''Get the value of a term.

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
    
    def get_parameter(self, term, *default):
        '''Get the value of a term.

.. versionadded:: 1.6

:Examples 1:

>>> v = c.get_parameter('false_northing')

:Parameters:

    term: `str`
        The name of the term.

    default: optional

:Returns:

    out:
        The value of the term <SOMETING BAOUT DEFAULT>

:Examples 2:

>>> c.get_parameter('grid_north_pole_latitude')
70.0

>>> c.get_parameter('foo')
ERROR
>>> c.get_parameter('foo', 'nonexistent term')
'nonexistent term'


        '''
        d = self._get_component('parameters', None)
        if term in d:
            return d[term]
        
        if default:
            return default[0]

        raise AttributeError("{} doesn't have parameter term {!r}".format(
                self.__class__.__name__, term))
    #--- End: def
    
    def has_term(self, term):
        '''Return whether a term has been set.

.. versionadded:: 1.6

:Examples 1:

>>> v = c.has_term('orog')

:Parameters:

    term: `str`
        The name of the term.

:Returns:

    out: `bool`
        True if the term exists , False otherwise.

:Examples 2:

>>> v = c.has_term('a')

>>> v = c.has_term('false_northing')

        '''
        return (self._has_component('domain_ancillaries', term) or
                self._has_component('parameters', term))
    #--- End: def

    def parameters(self, parameters=None, copy=True):
        '''Return or replace the parameter-valued terms.

.. versionadded:: 1.6

.. seealso:: `domain_ancillaries`

:Examples 1:

>>> d = c.parameters()

:Parameters:

    parameters: `dict`, optional
        Replace all parameter-valued terms with those provided.

          *Example:*
            ``parameters={'earth_radius': 6371007}``

    copy: `bool`, optional

:Returns:

    out: `dict`
        The parameter-valued terms and their values. If the
        *parameters* keyword has been set then the parameter-valued
        terms prior to replacement are returned.

:Examples 2:

>>> c.parameters()
{'standard_parallel': 25.0;
 'longitude_of_central_meridian': 265.0,
 'latitude_of_projection_origin': 25.0}

>>> c.parameters()
{}

        '''
#        return self._get_component('parameters', None, {}).copy()

        existing = self._get_component('parameters', None, None)

        if existing is None:
            existing = {}
            self._set_component('parameters', None, existing)

        out = existing.copy()

        if not parameters:
            return out

        # Still here?
        if copy:
            parameters = deepcopy(parameters)

        existing.clear()
        existing.update(parameters)

        return out
    #--- End: def

    def set_domain_ancillary(self, term, value, copy=True):
        '''Set a domain ancillary-valued term.

.. versionadded:: 1.6

.. seealso:: `domain_ancillaries`

:Examples 1:

>>> c.set_domain_ancillary('orog', 'domainancillary1')

:Returns:

    `None`

:Examples 2:

>>> c.domain_ancillaries()
{'a': 'domainancillary0',
 'b': 'domainancillary2'}
>>> c.set_domain_ancillary('orog', 'domainancillary1')
>>> c.domain_ancillaries()
{'a': 'domainancillary0',
 'b': 'domainancillary2',
 'orog': 'domainancillary1'}

        '''
        self._set_component('domain_ancillaries', term, value)
    #--- End: def
    
    def set_parameter(self, term, value, copy=True):
        '''Set a parameter-valued term.

.. versionadded:: 1.6

.. seealso:: `domain_ancillaries`

:Examples 1:

>>> c.set_parameter('longitude_of_central_meridian', 265.0)

:Returns:

    `None`

:Examples 2:

>>> c.parameters()
{'standard_parallel': 25.0;
 'latitude_of_projection_origin': 25.0}
>>> c.set_parameter('longitude_of_central_meridian', 265.0)
>>> c.parameters()
{'standard_parallel': 25.0;
 'longitude_of_central_meridian': 265.0,
 'latitude_of_projection_origin': 25.0}
        '''
        if copy:
            value = deepcopy(value)
            
        self._set_component('parameters', term, value)
    #--- End: def
    
    def terms(self):
        '''Return the terms.

Both parameter-valued and domain_ancillary-valued terms are returned.

Note that ``c.terms()`` is equivalent to
``c.parameters().update(c.domain_ancillaries())``.

.. versionadded:: 1.6

.. seealso:: `domain_ancillaries`, `parameters`

:Examples 1:

>>> d = c.terms()

:Returns:

    out: `dict`
        The terms and their values.

:Examples 2:

>>> c.terms()
{'a': 'domainancillary0',
 'b': 'domainancillary2',
 'orog': 'domainancillary1'}

>>> c.terms()
{'standard_parallel': 25.0;
 'longitude_of_central_meridian': 265.0,
 'latitude_of_projection_origin': 25.0}

>>> c.terms()
{}

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
