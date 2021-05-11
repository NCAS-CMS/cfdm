from .parameters import Parameters


class ParametersDomainAncillaries(Parameters):
    """Mixin to collect named parameters and domain ancillaries.

    .. versionadded:: (cfdm) 1.7.0

    """

    def __init__(
        self, parameters=None, domain_ancillaries=None, source=None, copy=True
    ):
        """**Initialisation**

        :Parameters:

            parameters: `dict`, optional
               Set parameters. The dictionary keys are term names,
               with corresponding parameter values. Ignored if the
               *source* parameter is set.

               Parameters may also be set after initialisation with
               the `set_parameters` and `set_parameter` methods.

               *Parameter example:*
                 ``parameters={'earth_radius': 6371007.}``

            domain_ancillaries: `dict`, optional
               Set references to domain ancillary constructs. The
               dictionary keys are term names, with corresponding
               domain ancillary construct keys. Ignored if the
               *source* parameter is set.

               Domain ancillaries may also be set after initialisation
               with the `set_domain_ancillaries` and
               `set_domain_ancillary` methods.

               *Parameter example:*
                 ``domain_ancillaries={'orog': 'domainancillary2'}``

            source: optional
                Initialise the parameters and domain ancillary terms
                from those of *source*.

                {{init source}}

            {{init copy: `bool`, optional}}

        """
        super().__init__(parameters=parameters, source=source, copy=copy)

        self._set_component("domain_ancillaries", {}, copy=False)

        if source:
            try:
                domain_ancillaries = source.domain_ancillaries()
            except AttributeError:
                domain_ancillaries = None

        if domain_ancillaries is None:
            domain_ancillaries = {}

        self.set_domain_ancillaries(domain_ancillaries, copy=False)

    def clear_domain_ancillaries(self):
        """Remove all domain_ancillaries.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `del_domain_ancillary`, `domain_ancillaries`,
                     `set_domain_ancillaries`

        :Returns:

            `dict`
                The domain ancillaries that have been removed.

        **Examples:**

        >>> f = {{package}}.{{class}}()
        >>> f.domain_ancillaries()
        {}
        >>> d = {'a': 'domainancillary0',
        ...      'b': 'domainancillary1',
        ...      'orog': 'domainancillary2'}
        >>> f.set_domain_ancillaries(d)
        >>> f.domain_ancillaries()
        {'a': 'domainancillary0',
         'b': 'domainancillary1',
         'orog': 'domainancillary2'}

        >>> old = f.clear_domain_ancillaries()
        >>> f.domain_ancillaries()
        {}
        >>> old
        {'a': 'domainancillary0',
         'b': 'domainancillary1',
         'orog': 'domainancillary2'}

        """
        out = self._get_component("domain_ancillaries")
        self._set_component("domain_ancillaries", {})
        return out.copy()

    def del_domain_ancillary(self, domain_ancillary, default=ValueError()):
        """Delete a domain ancillary.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `domain_ancillaries`, `get_domain_ancillary`,
                     `set_domain_ancillary`

        :Parameters:

            domain_ancillary: `str`
                The name of the domain ancillary to be deleted.

                *Parameter example:*
                   ``domain_ancillary='orog'``

            default: optional
                Return the value of the *default* parameter if the domain
                ancillary term has not been set.

                {{default Exception}}

        :Returns:

            `str`
                The removed domain ancillary key.

        **Examples:**

        >>> c = {{package}}.{{class}}()
        >>> c.set_domain_ancillary('orog', 'domainancillary2')
        >>> c.has_domain_ancillary('orog')
        True
        >>> c.get_domain_ancillary('orog')
        'domainancillary2'
        >>> c.del_domain_ancillary('orog')
        'domainancillary2'
        >>> c.has_domain_ancillary('orog')
        False
        >>> print(c.del_domain_ancillary('orog', None))
        None
        >>> print(c.get_domain_ancillary('orog', None))
        None

        """
        try:
            return self._get_component("domain_ancillaries").pop(
                domain_ancillary
            )
        except KeyError:
            if default is None:
                return

            return self._default(
                default,
                f"{self.__class__.__name__!r} has no {domain_ancillary!r} domain ancillary",
            )

    def domain_ancillaries(self):
        """Return all domain_ancillaries.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `clear_domain_ancillaries`, `get_domain_ancillary`,
                     `has_domain_ancillaryr` `set_domain_ancillaries`

        :Returns:

            `dict`
                The domain ancillaries.

        **Examples:**

        >>> f = {{package}}.{{class}}()
        >>> f.domain_ancillaries()
        {}
        >>> d = {'a': 'domainancillary0',
        ...      'b': 'domainancillary1',
        ...      'orog': 'domainancillary2'}
        >>> f.set_domain_ancillaries(d)
        >>> f.domain_ancillaries()
        {'a': 'domainancillary0',
         'b': 'domainancillary1',
         'orog': 'domainancillary2'}

        >>> old = f.clear_domain_ancillaries()
        >>> f.domain_ancillaries()
        {}
        >>> old
        {'a': 'domainancillary0',
         'b': 'domainancillary1',
         'orog': 'domainancillary2'}

        """
        return self._get_component("domain_ancillaries").copy()

    def get_domain_ancillary(self, domain_ancillary, default=ValueError()):
        """Return a domain ancillary term.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `del_domain_ancillary`, `domain_ancillaries`,
                     `set_domain_ancillary`

        :Parameters:

            domain_ancillary: `str`
                The name of the term.

            default: optional
                Return the value of the *default* parameter if the domain
                ancillary term has not been set.

                {{default Exception}}

        :Returns:

                The domain ancillary construct key.

        **Examples:**

        >>> c = {{package}}.{{class}}()
        >>> c.set_domain_ancillary('orog', 'domainancillary2')
        >>> c.has_domain_ancillary('orog')
        True
        >>> c.get_domain_ancillary('orog')
        'domainancillary2'
        >>> c.del_domain_ancillary('orog')
        'domainancillary2'
        >>> c.has_domain_ancillary('orog')
        False
        >>> print(c.del_domain_ancillary('orog', None))
        None
        >>> print(c.get_domain_ancillary('orog', None))
        None

        """
        try:
            return self._get_component("domain_ancillaries")[domain_ancillary]
        except KeyError:
            if default is None:
                return

            return self._default(
                default,
                f"{self.__class__.__name__!r} has no {domain_ancillary!r} domain ancillary",
            )

    def has_domain_ancillary(self, domain_ancillary):
        """Whether a domain ancillary has been set.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `del_domain_ancillary`, `domain_ancillaries`,
                     `has_domain_ancillary`, `set_domain_ancillary`

        :Parameters:

            domain_ancillary: `str`
                The name of the term.

        :Returns:

                The domain ancillary construct key.

        **Examples:**

        >>> c = {{package}}.{{class}}()
        >>> c.set_domain_ancillary('orog', 'domainancillary2')
        >>> c.has_domain_ancillary('orog')
        True
        >>> c.get_domain_ancillary('orog')
        'domainancillary2'
        >>> c.del_domain_ancillary('orog')
        'domainancillary2'
        >>> c.has_domain_ancillary('orog')
        False
        >>> print(c.del_domain_ancillary('orog', None))
        None
        >>> print(c.get_domain_ancillary('orog', None))
        None

        """
        return domain_ancillary in self._get_component("domain_ancillaries")

    def set_domain_ancillaries(self, domain_ancillaries, copy=True):
        """Set domain_ancillaries.

        .. versionadded:: (cfdm) 1.7.0

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

        >>> f = {{package}}.{{class}}()
        >>> f.domain_ancillaries()
        {}
        >>> d = {'a': 'domainancillary0',
        ...      'b': 'domainancillary1',
        ...      'orog': 'domainancillary2'}
        >>> f.set_domain_ancillaries(d)
        >>> f.domain_ancillaries()
        {'a': 'domainancillary0',
         'b': 'domainancillary1',
         'orog': 'domainancillary2'}

        >>> old = f.clear_domain_ancillaries()
        >>> f.domain_ancillaries()
        {}
        >>> old
        {'a': 'domainancillary0',
         'b': 'domainancillary1',
         'orog': 'domainancillary2'}

        """
        self._get_component("domain_ancillaries").update(domain_ancillaries)

    def set_domain_ancillary(self, term, value, copy=True):
        """Set an domain ancillary-valued term.

        .. versionadded:: (cfdm) 1.7.0

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

        >>> c = {{package}}.{{class}}()
        >>> c.set_domain_ancillary('orog', 'domainancillary2')
        >>> c.has_domain_ancillary('orog')
        True
        >>> c.get_domain_ancillary('orog')
        'domainancillary2'
        >>> c.del_domain_ancillary('orog')
        'domainancillary2'
        >>> c.has_domain_ancillary('orog')
        False
        >>> print(c.del_domain_ancillary('orog', None))
        None
        >>> print(c.get_domain_ancillary('orog', None))
        None

        """
        self._get_component("domain_ancillaries")[term] = value
