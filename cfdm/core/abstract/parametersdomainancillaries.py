from builtins import super
from future.utils import with_metaclass

import abc

from copy import deepcopy

from . import Parameters


class ParametersDomainAncillaries(with_metaclass(abc.ABCMeta, Parameters)):
    '''Abstract base class for a collection of named parameters and named
domain ancillary constructs.

    '''

    def __init__(self, parameters=None, domain_ancillaries=None,
                 source=None, copy=True, _use_data=True):
        '''**Initialization**

:Parameters:

    source: optional

    copy: `bool`, optional

        '''
        super().__init__(parameters=parameters, source=source,
                         copy=copy,
                         _use_data=_use_data)

        self._set_component('domain_ancillaries', {}, copy=False)

        if source:
            try:
                domain_ancillaries = source.domain_ancillaries()
            except AttributeError:
                domain_ancillaries = None
        #--- End: if
        
        if domain_ancillaries is None:
            domain_ancillaries = {}
        elif copy or not _use_data:
            domain_ancillaries = domain_ancillaries.copy()
            for key, value in list(domain_ancillaries.items()):
                try:
                    domain_ancillaries[key] = value.copy(data=_use_data)
                except AttributeError:
                    domain_ancillaries[key] = deepcopy(value)
        #--- End: if
            
        self.domain_ancillaries(domain_ancillaries, copy=False)
    #--- End: def

    def __str__(self):
        '''x.__str__() <==> str(x)

        '''
        out = [super().__str__()]
            
        domain_ancillaries = self.domain_ancillaries()
        if domain_ancillaries:
            out.append('Domain Ancillaries: {0}'.format(', '.join(sorted(domain_ancillaries))))
            
        return '; '.join(out)
    #--- End: def

    def copy(self, data=True):
        '''Return a deep copy.

``f.copy()`` is equivalent to ``copy.deepcopy(f)``.

.. versionadded:: 1.6

:Examples 1:

>>> g = f.copy()

:Parameters:

    data: `bool`, optional
        If False then do not copy the ancillary data arrays. By
        default the data arrays are copied.

:Returns:

    out:
        The deep copy.

:Examples 2:

>>> g = f.copy(data=False)

        '''
        return type(self)(source=self, copy=True, _use_data=data)
    #--- End: def

    def del_domain_ancillary(self, domain_ancillary):
        '''Delete a domain ancillary.

.. seealso:: `domain_ancillaries`, `get_domain_ancillary`, `has_domain_ancillary`,
             `set_domain_ancillary`

:Examples 1:

>>> f.del_domain_ancillary('orog')

:Parameters:

    parmtaeter: `str`
        The name of the parameter to be deleted.

:Returns:

     out:
        The value of the deleted parameter, or `None` if the parameter
        was not set.

:Examples 2:

        '''
        return self._get_component('domain_ancillaries').pop(domain_ancillary, None)
    #--- End: def

    def domain_ancillaries(self, domain_ancillaries=None, copy=True):
        '''Return or replace the domain ancillary-valued terms.

.. versionadded:: 1.6

.. seealso:: `parameters`

:Examples 1:

>>> d = c.ancillaries()

:Parameters:

    ancillaries: `dict`, optional
        Replace all named domain ancillaries with those provided.

          *Example:*
            ``domain_ancillaries={'x': x_ancillary}``

    copy: `bool`, optional

:Returns:

    out: `dict`
        The parameter-valued terms and their values. If the
        *parameters* keyword has been set then the parameter-valued
        terms prior to replacement are returned.

:Examples 2:

        '''
        out = self._get_component('domain_ancillaries').copy()

        if domain_ancillaries is not None:
            if copy:
                properties = deepcopy(domain_ancillaries)
            else:
                properties = domain_ancillaries.copy()
                
            self._set_component('domain_ancillaries', domain_ancillaries,
                                copy=False)

        return out
    #--- End: def
    
    def get_domain_ancillary(self, domain_ancillary, *default):
        '''Get a parameter value.

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
        d = self._get_component('domain_ancillaries')
        if term in d:
            return d[term]
        
        if default:
            return default[0]

        raise AttributeError("{} doesn't have domain ancillary-valued term {!r}".format(
                self.__class__.__name__, term))
    #--- End: def
    
    def set_domain_ancillary(self, term, value, copy=True):
        '''Set an domain ancillary-valued term.

.. versionadded:: 1.6

.. seealso:: `domain_ancillaries`, `del_domain_ancillary`, `get_domain_ancillary`,
             `set_domain_ancillary`

:Examples 1:

>>> c.set_domain_ancillary('longitude_of_central_meridian', 265.0)

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
            value = value.copy()
            
        self._get_component('domain_ancillaries')[term] = value
    #--- End: def
        
#--- End: class
