import abc

from copy import deepcopy

from .container import Container


class Terms(Container):
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
        super(Terms, self).__init__(source=source)

        if source:
            try:
                parameters = source.parameters()
            except AttributeError:
                parameters = None
                
            try:
                domain_ancillaries = source.domain_ancillaries()
            except AttributeError:
                domain_ancillaries = None
        #--- End: if
        
        if domain_ancillaries is None:
            domain_ancillaries = {}

        self.domain_ancillaries(domain_ancillaries, copy=copy)

        if parameters is None:
            parameters = {}

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

``t.copy()`` is equivalent to ``copy.deepcopy(t)``.

:Examples 1:

>>> u = t.copy()

:Returns:

    out:
        The deep copy.

        '''
        return type(self)(source=self, copy=True)
    #--- End: def

    def del_term(self, term):
        '''Delete a term.

To retain term as a placeholder but delete its value, use the
`del_term_value` method.

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
        '''Delete the value of a term.

This method retains the term as a placeholder. To completely remove a
term, use the `del_term` method.

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
