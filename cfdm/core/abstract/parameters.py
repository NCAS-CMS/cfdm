from ..functions import deepcopy
from .container import Container


class Parameters(Container):
    """Mixin class for a collection of named parameters.

    .. versionadded:: (cfdm) 1.7.0

    """

    def __init__(self, parameters=None, source=None, copy=True):
        """**Initialisation**

        :Parameters:

            parameters: `dict`, optional
               Set parameters. The dictionary keys are parameter
               names, with corresponding values. Ignored if the
               *source* parameter is set.

               Parameters may also be set after initialisation with
               the `set_parameters` and `set_parameter` methods.

               *Parameter example:*
                 ``parameters={'earth_radius': 6371007.}``

            source: optional
                Initialise the parameters from those of *source*.

                {{init source}}

            {{init copy: `bool`, optional}}

        """
        super().__init__(source=source, copy=copy)

        self._set_component("parameters", {}, copy=False)

        if source:
            try:
                parameters = source.parameters()
            except AttributeError:
                parameters = None

        if parameters is None:
            parameters = {}
            copy = False

        self.set_parameters(parameters, copy=copy)

    def clear_parameters(self):
        """Remove all parameters.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `del_parameter`, `parameters`, `set_parameters`

        :Returns:

            `dict`
                The parameters that have been removed.

        **Examples:**

        >>> f = {{package}}.{{class}}()
        >>> f.parameters()
        {}
        >>> p = {'standard_parallel': 25.0,
        ...      'longitude_of_central_meridian': 265.0,
        ...      'latitude_of_projection_origin': 25.0}
        >>> f.set_parameters(p)
        >>> f.parameters()
        {'standard_parallel': 25.0,
         'longitude_of_central_meridian': 265.0,
         'latitude_of_projection_origin': 25.0}

        >>> old = f.clear_parameters()
        >>> old
        {'standard_parallel': 25.0,
         'longitude_of_central_meridian': 265.0,
         'latitude_of_projection_origin': 25.0}
        >>> f.set_parameters(old)

        """
        out = self._get_component("parameters")
        self._set_component("parameters", {}, copy=False)
        return out.copy()

    def del_parameter(self, parameter, default=ValueError()):
        """Delete a parameter.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `get_parameter`, `has_parameter`, `parameters`,
                     `set_parameter`

        :Parameters:

            parameter: `str`
                The name of the parameter to be deleted.

            default: optional
                Return the value of the *default* parameter if the
                parameter has not been set.

                {{default Exception}}

        :Returns:

                The removed parameter value.

        **Examples:**

        >>> f = {{package}}.{{class}}()
        >>> f.set_parameter('earth_radius', 6371007)
        >>> f.has_parameter('earth_radius')
        True
        >>> f.get_parameter('earth_radius')
        6371007
        >>> f.del_parameter('earth_radius')
        6371007
        >>> f.has_parameter('earth_radius')
        False
        >>> print(f.del_parameter('earth_radius', None))
        None
        >>> print(f.get_parameter('earth_radius', None))
        None

        """
        try:
            return self._get_component("parameters").pop(parameter)
        except KeyError:
            if default is None:
                return

            return self._default(
                default,
                f"{self.__class__.__name__!r} has no {parameter!r} parameter",
            )

    def get_parameter(self, parameter, default=ValueError()):
        """Get a parameter value.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            parameter: `str`
                The name of the parameter.

            default: optional
                Return the value of the *default* parameter if the
                parameter has not been set.

                {{default Exception}}

        :Returns:

                The value of the parameter.

        **Examples:**

        >>> f = {{package}}.{{class}}()
        >>> f.set_parameter('earth_radius', 6371007)
        >>> f.has_parameter('earth_radius')
        True
        >>> f.get_parameter('earth_radius')
        6371007
        >>> f.del_parameter('earth_radius')
        6371007
        >>> f.has_parameter('earth_radius')
        False
        >>> print(f.del_parameter('earth_radius', None))
        None
        >>> print(f.get_parameter('earth_radius', None))
        None

        """
        try:
            return self._get_component("parameters")[parameter]
        except KeyError:
            if default is None:
                return

            return self._default(
                default,
                f"{self.__class__.__name__!r} has no {parameter!r} parameter",
            )

    def has_parameter(self, parameter):
        """Whether a parameter has been set.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `del_parameter`, `get_parameter`, `parameters`,
                     `set_parameter`

        :Parameters:

            parameter: `str`
                The name of the parameter.

                *Parameter example:*
                   ``parameter='geoid_name'``

        :Returns:

             `bool`
                True if the parameter has been set, otherwise False.

        **Examples:**

        >>> f = {{package}}.{{class}}()
        >>> f.set_parameter('earth_radius', 6371007)
        >>> f.has_parameter('earth_radius')
        True
        >>> f.get_parameter('earth_radius')
        6371007
        >>> f.del_parameter('earth_radius')
        6371007
        >>> f.has_parameter('earth_radius')
        False
        >>> print(f.del_parameter('earth_radius', None))
        None
        >>> print(f.get_parameter('earth_radius', None))
        None

        """
        return parameter in self._get_component("parameters")

    def parameters(self):
        """Return all parameters.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `clear_parameters`, `get_parameter`, `has_parameter`
                     `set_parameters`

        :Returns:

            `dict`
                The parameters.

        **Examples:**

        >>> f = {{package}}.{{class}}()
        >>> f.parameters()
        {}
        >>> p = {'standard_parallel': 25.0,
        ...      'longitude_of_central_meridian': 265.0,
        ...      'latitude_of_projection_origin': 25.0}
        >>> f.set_parameters(p)
        >>> f.parameters()
        {'standard_parallel': 25.0,
         'longitude_of_central_meridian': 265.0,
         'latitude_of_projection_origin': 25.0}

        >>> old = f.clear_parameters()
        >>> old
        {'standard_parallel': 25.0,
         'longitude_of_central_meridian': 265.0,
         'latitude_of_projection_origin': 25.0}
        >>> f.set_parameters(old)

        """
        return self._get_component("parameters").copy()

    def set_parameters(self, parameters, copy=True):
        """Set parameters.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `clear_parameters`, `parameters`, `set_parameter`

        :Parameters:

            parameters: `dict`
                Store the parameters from the dictionary supplied.

                *Parameter example:*
                  ``parameters={'earth_radius': 6371007}``

            copy: `bool`, optional
                If False then any parameter values provided by the
                *parameters* parameter are not copied before insertion. By
                default they are deep copied.

        :Returns:

            `None`

        **Examples:**

        >>> f = {{package}}.{{class}}()
        >>> f.parameters()
        {}
        >>> p = {'standard_parallel': 25.0,
        ...      'longitude_of_central_meridian': 265.0,
        ...      'latitude_of_projection_origin': 25.0}
        >>> f.set_parameters(p)
        >>> f.parameters()
        {'standard_parallel': 25.0,
         'longitude_of_central_meridian': 265.0,
         'latitude_of_projection_origin': 25.0}

        >>> old = f.clear_parameters()
        >>> old
        {'standard_parallel': 25.0,
         'longitude_of_central_meridian': 265.0,
         'latitude_of_projection_origin': 25.0}
        >>> f.set_parameters(old)

        """
        if copy:
            parameters = deepcopy(parameters)

        self._get_component("parameters").update(parameters)

    def set_parameter(self, term, value, copy=True):
        """Set a parameter-valued term.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `parameters`

        :Returns:

            `None`

        **Examples:**

        >>> f = {{package}}.{{class}}()
        >>> f.set_parameter('earth_radius', 6371007)
        >>> f.has_parameter('earth_radius')
        True
        >>> f.get_parameter('earth_radius')
        6371007
        >>> f.del_parameter('earth_radius')
        6371007
        >>> f.has_parameter('earth_radius')
        False
        >>> print(f.del_parameter('earth_radius', None))
        None
        >>> print(f.get_parameter('earth_radius', None))
        None

        """
        if copy:
            value = deepcopy(value)

        self._get_component("parameters")[term] = value
