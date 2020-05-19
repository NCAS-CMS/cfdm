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

           Parameters may also be set after initialisation with the
           `set_parameters` and `set_parameter` methods.

           *Parameter example:*
             ``parameters={'earth_radius': 6371007.}``

        domain_ancillaries: `dict`, optional
           Set references to domain ancillary constructs. The
           dictionary keys are term names, with corresponding domain
           ancillary construct keys. Ignored if the *source* parameter
           is set.

           Domain ancillaries may also be set after initialisation
           with the `set_domain_ancillaries` and
           `set_domain_ancillary` methods.

           *Parameter example:*
             ``domain_ancillaries={'orog': 'domainancillary2'}``

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
        # --- End: if

        if domain_ancillaries is None:
            domain_ancillaries = {}
        elif copy:
            domain_ancillaries = domain_ancillaries.copy()
            for key, value in list(domain_ancillaries.items()):
                domain_ancillaries[key] = deepcopy(value)
        # --- End: if

        self.set_domain_ancillaries(domain_ancillaries, copy=False)

    def clear_domain_ancillaries(self):
        '''Remove all domain_ancillaries.

    .. versionadded:: 1.7.0

    .. seealso:: `del_domain_ancillary`, `domain_ancillaries`,
                 `set_domain_ancillaries`

    :Returns:

        `dict`
            The domain ancillaries that have been removed.

    **Examples:**

    >>> old = f.clear_domain_ancillaries()
    >>> old
    {'a': 'domainancillary0',
     'b': 'domainancillary1',
     'orog': 'domainancillary2'}
    >>> f.set_domain_ancillaries(old)
    >>> f.domain_ancillaries()
    {'a': 'domainancillary0',
     'b': 'domainancillary1',
     'orog': 'domainancillary2'}

        '''
        out = self._get_component('domain_ancillaries')
        self._set_component('domain_ancillaries', {})
        return out.copy()

    def del_domain_ancillary(self, domain_ancillary,
                             default=ValueError()):
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
            Return the value of the *default* parameter if the domain
            ancillary term has not been set. If set to an `Exception`
            instance then it will be raised instead.

    :Returns:

            The removed domain ancillary key.

    **Examples:**

    >>> c.set_domain_ancillary('orog', 'domainancillary2')
    >>> c.has_domain_ancillary('orog')
    True
    >>> c.get_domain_ancillary('orog')
    domainancillary2'
    >>> c.del_domain_ancillary('orog')
    domainancillary2'
    >>> c.has_domain_ancillaryr('orog')
    False
    >>> print(c.del_domain_ancillaryy('orog', None))
    None
    >>> print(c.get_domain_ancillary('orog', None))
    None

        '''
        try:
            return self._get_component('domain_ancillaries').pop(
                domain_ancillary)
        except KeyError:
            return self._default(default,
                                 "{!r} has no {!r} domain ancillary".format(
                                     self.__class__.__name__, domain_ancillary))

    def domain_ancillaries(self):
        '''Return all domain_ancillaries.

    .. versionadded:: 1.7.0

    .. seealso:: `clear_domain_ancillaries`, `get_domain_ancillary`,
                 `has_domain_ancillaryr` `set_domain_ancillaries`

    :Returns:

        `dict`
            The domain ancillaries.

    **Examples:**

    >>> old = f.clear_domain_ancillaries()
    >>> old
    {'a': 'domainancillary0',
     'b': 'domainancillary1',
     'orog': 'domainancillary2'}
    >>> f.set_domain_ancillaries(old)
    >>> f.domain_ancillaries()
    {'a': 'domainancillary0',
     'b': 'domainancillary1',
     'orog': 'domainancillary2'}

        '''
        return self._get_component('domain_ancillaries').copy()

    def get_domain_ancillary(self, domain_ancillary,
                             default=ValueError()):
        '''Return a domain ancillary term.

    .. versionadded:: 1.7.0

    .. seealso:: `del_domain_ancillary`, `domain_ancillaries`,
                 `set_domain_ancillary`

    :Parameters:

        domain_ancillary: `str`
            The name of the term.

        default: optional
            Return the value of the *default* parameter if the domain
            ancillary term has not been set. If set to an `Exception`
            instance then it will be raised instead.

    :Returns:

            The domain ancillary construct key.

    **Examples:**

    >>> c.set_domain_ancillary('orog', 'domainancillary2')
    >>> c.has_domain_ancillary('orog')
    True
    >>> c.get_domain_ancillary('orog')
    domainancillary2'
    >>> c.del_domain_ancillary('orog')
    domainancillary2'
    >>> c.has_domain_ancillaryr('orog')
    False
    >>> print(c.del_domain_ancillaryy('orog', None))
    None
    >>> print(c.get_domain_ancillary('orog', None))
    None

        '''
        try:
            return self._get_component('domain_ancillaries')[domain_ancillary]
        except KeyError:
            return self._default(default,
                                 "{!r} has no {!r} domain ancillary".format(
                                     self.__class__.__name__, domain_ancillary))

    def has_domain_ancillary(self, domain_ancillary):
        '''Whether a domain ancillary has been set.

    .. versionadded:: 1.7.0

    .. seealso:: `del_domain_ancillary`, `domain_ancillaries`,
                 `has_domain_ancillary`, `set_domain_ancillary`

    :Parameters:

        domain_ancillary: `str`
            The name of the term.

        default: optional
            Return the value of the *default* parameter if the domain
            ancillary term has not been set. If set to an `Exception`
            instance then it will be raised instead.

    :Returns:

            The domain ancillary construct key.

    **Examples:**

    >>> c.set_domain_ancillary('orog', 'domainancillary2')
    >>> c.has_domain_ancillary('orog')
    True
    >>> c.get_domain_ancillary('orog')
    domainancillary2'
    >>> c.del_domain_ancillary('orog')
    domainancillary2'
    >>> c.has_domain_ancillaryr('orog')
    False
    >>> print(c.del_domain_ancillaryy('orog', None))
    None
    >>> print(c.get_domain_ancillary('orog', None))
    None

        '''
        return domain_ancillary in self._get_component('domain_ancillaries')

    def set_domain_ancillaries(self, domain_ancillaries, copy=True):
        '''Set domain_ancillaries.

    .. versionadded:: 1.7.0

    .. seealso:: `clear_domain_ancillaries`, `domain_ancillaries`,
                 `set_domain_ancillary`

    :Parameters:

        domain_ancillaries: `dict`
            Store the domain ancillaries from the dictionary supplied.

            *Parameter example:*
              ``domain_ancillaries={'earth_radius': 6371007}``

        copy: `bool`, optional
            If False then any parameter values provided by the
            *domain_ancillaries* parameter are not copied before
            insertion. By default they are deep copied.

    :Returns:

        `None`

    **Examples:**

    >>> old = f.clear_domain_ancillaries()
    >>> old
    {'a': 'domainancillary0',
     'b': 'domainancillary1',
     'orog': 'domainancillary2'}
    >>> f.set_domain_ancillaries(old)
    >>> f.domain_ancillaries()
    {'a': 'domainancillary0',
     'b': 'domainancillary1',
     'orog': 'domainancillary2'}

        '''
        if copy:
            domain_ancillaries = deepcopy(domain_ancillaries)
        else:
            domain_ancillaries = domain_ancillaries.copy()

        self._get_component('domain_ancillaries').update(domain_ancillaries)

    def set_domain_ancillary(self, term, value, copy=True):
        '''Set an domain ancillary-valued term.

    .. versionadded:: 1.7.0

    .. seealso:: `del_domain_ancillary`, `domain_ancillaries`,
                 `get_domain_ancillary`

    :Parameters:

        term: `str`
            The name of the term to be set.

        value:
            The value for the term.

        copy: `bool`, optional
            If True then set a deep copy of *value*.

    :Returns:

        `None`

    **Examples:**

    >>> c.set_domain_ancillary('orog', 'domainancillary2')
    >>> c.has_domain_ancillary('orog')
    True
    >>> c.get_domain_ancillary('orog')
    domainancillary2'
    >>> c.del_domain_ancillary('orog')
    domainancillary2'
    >>> c.has_domain_ancillaryr('orog')
    False
    >>> print(c.del_domain_ancillaryy('orog', None))
    None
    >>> print(c.get_domain_ancillary('orog', None))
    None

        '''
        if copy:
            value = deepcopy(value)

        self._get_component('domain_ancillaries')[term] = value

# --- End: class
