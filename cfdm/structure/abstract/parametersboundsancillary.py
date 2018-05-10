import abc

from copy import deepcopy

from .container import Container


class BoundsParametersAncillaries(Container):
    '''Base class for parameter- and domain ancillary-valued terms.

    '''
    __metaclass__ = abc.ABCMeta

    def __init__(self, parameters=None, bounds_ancillaries=None, source=None,
                 copy=True):
        '''**Initialization**

:Parameters:

    source: optional

    copy: `bool`, optional

        '''
        super(Parameters, self).__init__(parameters=parameters,
                                         source=source, copy=copy)

        if source:
            try:
                bounds_ancillaries = source.bounds_ancillaries()
            except AttributeError:
                bounds_ancillaries = None
        #--- End: if
        
        if bounds_ancillaries is None:
            bounds_ancillaries = {}

        self.bounds_ancillaries(bounds_ancillaries, copy=copy)
    #--- End: def

    def __str__(self):
        '''x.__str__() <==> str(x)

        '''
        out = [super(ParametersBoundsAncillaries, self).__str__()]

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

    def del_parameter(self, parameter):
        '''Delete a parameter

.. seealso:: `get_parameter`, `has_parameter`, `parameters`, `set_parameter`

:Examples 1:

>>> f.del_parameter('grid_mapping_name')

:Parameters:

    parmtaeter: `str`
        The name of the parameter to be deleted.

:Returns:

     out:
        The value of the deleted parameter, or `None` if the parameter
        was not set.

:Examples 2:

        '''
        return self._del_component('parameters', parameter)
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
