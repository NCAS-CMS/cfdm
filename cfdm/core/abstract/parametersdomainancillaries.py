from builtins import super
from future.utils import with_metaclass

import abc

from copy import deepcopy

from . import Parameters


class ParametersDomainAncillaries(with_metaclass(abc.ABCMeta, Parameters)):
    '''Abstract base class for a collection of named parameters and named
domain ancillary constructs.

.. versionadded:: 1.7.0

    '''

    def __init__(self, parameters=None, domain_ancillaries=None,
                 source=None, copy=True):
        '''**Initialization**

:Parameters:

    parameters: `dict`, optional
       Set parameters. The dictionary keys are term names, with
       corresponding parameter values. Ignored if the *source*
       parameter is set.

       *Parameter example:*
         ``parameters={'earth_radius': 6371007.}``

       Parameters may also be set after initialisation with the
       `parameters` and `set_parameter` methods.

    domain_ancillaries: `dict`, optional
       Set references to domain ancillary constructs. The dictionary
       keys are term names, with corresponding domain ancillary
       construct keys. Ignored if the *source* parameter is set.

       *Parameter example:*
         ``domain_ancillaries={'orog': 'domainancillary2'}``

       Domain ancillaries may also be set after initialisation with
       the `domain_ancillaries` and `set_domain_ancillary` methods.

    source: optional
        Initialize the parameters and domain ancillary terms from
        those of *source*.

    copy: `bool`, optional
        If False then do not deep copy input parameters prior to
        initialization. By default arguments are deep copied.

        '''
        super().__init__(parameters=parameters, source=source,
                         copy=copy)

        self._set_component('domain_ancillaries', {}, copy=False)

        if source:
            try:
                domain_ancillaries = source.domain_ancillaries()
            except AttributeError:
                domain_ancillaries = None
        #--- End: if
        
        if domain_ancillaries is None:
            domain_ancillaries = {}
        elif copy:
            domain_ancillaries = domain_ancillaries.copy()
            for key, value in list(domain_ancillaries.items()):
                domain_ancillaries[key] = deepcopy(value)
        #--- End: if
            
        self.domain_ancillaries(domain_ancillaries, copy=False)
    #--- End: def

    def copy(self):
        '''Return a deep copy.

``f.copy()`` is equivalent to ``copy.deepcopy(f)``.

.. versionadded:: 1.7.0

:Returns:

        The deep copy.

**Examples:**

>>> g = f.copy()

        '''
        return type(self)(source=self, copy=True) #, _use_data=data)
    #--- End: def

    def del_domain_ancillary(self, domain_ancillary, *default):
        '''Delete a domain ancillary.

.. versionadded:: 1.7.0

.. seealso:: `domain_ancillaries`, `get_domain_ancillary`,
             `set_domain_ancillary`

:Parameters:

    domain_ancillary: `str`
        The name of the domain ancillary to be deleted.

        *Parameter example:*
           ``domain_ancillary='orog'``

    default: optional
        Return *default* if the domain ancillary has not been set.

:Returns:

        The removed domain acnillary key. If unset then *default* is
        returned, if provided.

**Examples:**

>>> c.domain_ancillaries()
{'a': 'domainancillary0',
 'b': 'domainancillary1',
 'orog': 'domainancillary2'}
>>> c.del_domain_ancillary('orog')
'domainancillary2'
>>> c..domain_ancillaries()
{'a': 'domainancillary0',
 'b': 'domainancillary1'}

        '''
        return self._get_component('domain_ancillaries').pop(
            domain_ancillary, None)
    #--- End: def

    def domain_ancillaries(self, domain_ancillaries=None, copy=True):
        '''Return or replace all domain ancillary-valued terms.

.. versionadded:: 1.7.0

.. seealso:: `del_domain_ancillary`, `get_domain_ancillary`,
             `parameters`, `set_domain_ancillary`

:Parameters:

    domain_ancillaries: `dict`, optional
        Delete all existing named domain ancillary, and instead store
        those from the dictionary supplied.

        *Parameter example:*
          ``domain_ancillaries={'orog': 'domainancillary1'}``

        *Parameter example:*
          ``domain_ancillaries={}``

    copy: `bool`, optional
        If False then any terms provided by the *domain_ancillaries*
        parameter are not copied before insertion. By default they are
        deep copied.

:Returns:

    `dict`
        The domain ancillary terms or, if the *domain_ancillaries*
        parameter was set, the original terms.

**Examples:**

<TODO>

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
        '''Return a domain ancillary term.

.. versionadded:: 1.7.0

.. seealso:: `del_domain_ancillary`, `domain_ancillaries`,
             `set_domain_ancillary`

:Parameters:

    term: `str`
        The name of the term.

    default: optional
        <TODO>

:Returns:

        <TODO>

**Examples:**

<TODO>

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

.. versionadded:: 1.7.0

.. seealso:: `del_domain_ancillary`, `domain_ancillaries`,
             `get_domain_ancillary`
:Parameters:

        <TODO>
:Returns:

    `None`

**Examples:**

<TODO>

        '''
        if copy:
            value = deepcopy(value)
            
        self._get_component('domain_ancillaries')[term] = value
    #--- End: def
        
#--- End: class
