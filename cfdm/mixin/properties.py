import logging
import textwrap

from ..decorators import _display_or_return, _manage_log_level_via_verbosity
from . import Container

logger = logging.getLogger(__name__)


class Properties(Container):
    """Mixin class for descriptive properties.

    .. versionadded:: (cfdm) 1.7.0

    """

    def __str__(self):
        """Called by the `str` built-in function.

        x.__str__() <==> str(x)

        .. versionadded:: (cfdm) 1.7.0

        """
        return f"{self.identity('')}"

    def _dump_properties(self, _prefix="", _level=0, _omit_properties=None):
        """Dump the properties.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            _omit_properties: sequence of `str`, optional
                Omit the given CF properties from the description.

            _level: `int`, optional

        :Returns:

            `str`

        """
        indent0 = "    " * _level
        string = []

        properties = self.properties()

        if _omit_properties:
            for prop in _omit_properties:
                properties.pop(prop, None)

        for prop, value in sorted(properties.items()):
            name = f"{indent0}{_prefix}{prop} = "
            value = repr(value)
            subsequent_indent = " " * len(name)
            if value.startswith("'") or value.startswith('"'):
                subsequent_indent = f"{subsequent_indent} "

            string.append(
                textwrap.fill(
                    name + value, 79, subsequent_indent=subsequent_indent
                )
            )

        return "\n".join(string)

    def _identities_iter(self):
        """Return all possible identities.

        See `identities` for details and examples.

        :Returns:

            generator
                The identities.

        """
        standard_name = self.get_property("standard_name", None)
        if standard_name is not None:
            yield standard_name

        properties = self.properties()
        if properties:
            #            standard_name = properties.get("standard_name", None)
            #            if standard_name is not None:
            #                yield standard_name

            for prop in ("cf_role", "axis", "long_name"):
                value = properties.pop(prop, None)
                if value is not None:
                    yield f"{prop}={value}"

            for prop, value in sorted(properties.items()):
                yield f"{prop}={value}"

        ncvar = self.nc_get_variable(None)
        if ncvar is not None:
            yield f"ncvar%{ncvar}"

    # ----------------------------------------------------------------
    # Methods
    # ----------------------------------------------------------------
    def creation_commands(
        self, namespace=None, indent=0, string=True, name="c", header=True
    ):
        """Return the commands that would create the construct.

        .. versionadded:: (cfdm) 1.8.7.0

        .. seealso:: `{{package}}.Domain.creation_commands`,
                     `{{package}}.Field.creation_commands`

        :Parameters:

            {{namespace: `str`, optional}}

            {{indent: `int`, optional}}

            {{string: `bool`, optional}}

            {{name: `str`, optional}}

            {{header: `bool`, optional}}

        :Returns:

            {{returns creation_commands}}

        **Examples:**

        >>> x = {{package}}.{{class}}(
        ...     properties={'units': 'Kelvin',
        ...                 'standard_name': 'air_temperature'}
        ... )
        >>> print(x.creation_commands(header=False))
        c = {{package}}.{{class}}()
        c.set_properties({'units': 'Kelvin', 'standard_name': 'air_temperature'})

        """
        if namespace is None:
            namespace = self._package() + "."
        elif namespace and not namespace.endswith("."):
            namespace += "."

        out = []

        if header:
            out.append("#")
            out.append("#")

            construct_type = getattr(self, "construct_type", None)
            if construct_type is not None:
                out[-1] += f" {construct_type}:"

            identity = self.identity()
            if identity:
                out[-1] += f" {identity}"

        out.append(f"{name} = {namespace}{self.__class__.__name__}()")

        properties = self.properties()
        if properties:
            out.append(f"{name}.set_properties({properties})")

        nc = self.nc_get_variable(None)
        if nc is not None:
            out.append(f"{name}.nc_set_variable('{nc}')")

        if string:
            indent = " " * indent
            out[0] = indent + out[0]
            out = ("\n" + indent).join(out)

        return out

    @_display_or_return
    def dump(
        self,
        display=True,
        _key=None,
        _omit_properties=(),
        _prefix="",
        _title=None,
        _create_title=True,
        _level=0,
    ):
        """A full description.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            display: `bool`, optional
                If False then return the description as a string. By
                default the description is printed.

        :Returns:

            {{returns dump}}

        """
        indent0 = "    " * _level

        string = []

        # ------------------------------------------------------------
        # Title
        # ------------------------------------------------------------
        if _create_title:
            if _title is None:
                if _key:
                    default = f"key%{_key}"
                else:
                    default = ""

                string.append(
                    f"{indent0}{self.__class__.__name_}: "
                    f"{self.identity(default=default)}"
                )
            else:
                string.append(indent0 + _title)

        # ------------------------------------------------------------
        # Properties
        # ------------------------------------------------------------
        properties = self._dump_properties(
            _prefix=_prefix,
            _level=_level + 1,
            _omit_properties=_omit_properties,
        )
        if properties:
            string.append(properties)

        return "\n".join(string)

    @_manage_log_level_via_verbosity
    def equals(
        self,
        other,
        rtol=None,
        atol=None,
        verbose=None,
        ignore_data_type=False,
        ignore_fill_value=False,
        ignore_properties=(),
        ignore_type=False,
        ignore_compression=True,
    ):
        """Whether two instances are the same.

        Equality is strict by default. This means that:

        * the same descriptive properties must be present, with the
          same values and data types, and vector-valued properties
          must also have same the size and be element-wise equal (see
          the *ignore_properties* and *ignore_data_type* parameters).

        {{equals tolerance}}

        Any type of object may be tested but, in general, equality is
        only possible with another object of the same type, or a
        subclass of one. See the *ignore_type* parameter.

        {{equals netCDF}}

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            other:
                The object to compare for equality.

            {[atol: number, optional}}

            {{rtol: number, optional}}

            {{ignore_fill_value: `bool`, optional}}

            {{verbose: `int` or `str` or `None`, optional}}

            {{ignore_properties: sequence of `str`, optional}}

            {{ignore_data_type: `bool`, optional}}

            {{ignore_type: `bool`, optional}}

            ignore_compression:
                Ignored, since properties do not have data arrays.

        :Returns:

            `bool`
                Whether the two instances are equal.

        **Examples:**

        >>> p.equals(p)
        True
        >>> p.equals(p.copy())
        True
        >>> p.equals('not a colection of properties')
        False

        >>> q = p.copy()
        >>> q.set_property('foo', 'bar')
        >>> p.equals(q)
        False
        >>> p.equals(q, verbose=3)
        {{class}}: Non-common property name: foo
        {{class}}: Different properties
        False

        """
        pp = super()._equals_preprocess(
            other, verbose=verbose, ignore_type=ignore_type
        )
        if pp is True or pp is False:
            return pp

        other = pp

        # ------------------------------------------------------------
        # Check the properties
        # ------------------------------------------------------------
        if ignore_fill_value:
            ignore_properties += ("_FillValue", "missing_value")

        self_properties = self.properties()
        other_properties = other.properties()

        if ignore_properties:
            for prop in ignore_properties:
                self_properties.pop(prop, None)
                other_properties.pop(prop, None)

        if set(self_properties) != set(other_properties):
            for prop in set(self_properties).symmetric_difference(
                other_properties
            ):
                logger.info(
                    f"{self.__class__.__name__}: Missing property: {prop}"
                )

            return False

        for prop, x in self_properties.items():
            y = other_properties[prop]

            if not self._equals(
                x,
                y,
                rtol=rtol,
                atol=atol,
                ignore_fill_value=ignore_fill_value,
                ignore_data_type=True,
                verbose=verbose,
            ):
                logger.info(
                    f"{self.__class__.__name__}: Different {prop!r} "
                    f"property values: {x!r}, {y!r}"
                )

                return False

        return True

    def identity(self, default=""):
        """Return the canonical identity.

        By default the identity is the first found of the following:

        * The ``standard_name`` property.
        * The ``cf_role`` property, preceded by ``'cf_role='``.
        * The ``axis`` property, preceded by ``'axis='``.
        * The ``long_name`` property, preceded by ``'long_name='``.
        * The netCDF variable name, preceded by ``'ncvar%'``.
        * The value of the *default* parameter.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `identities`

        :Parameters:

            default: optional
                If no identity can be found then return the value of the
                default parameter.

        :Returns:

                The identity.

        **Examples:**

        >>> f = {{package}}.{{class}}()
        >>> f.set_properties({'foo': 'bar',
        ...                   'long_name': 'Air Temperature',
        ...                   'standard_name': 'air_temperature'})
        >>> f.nc_set_variable('tas')
        >>> f.identity()
        'air_temperature'
        >>> f.del_property('standard_name')
        'air_temperature'
        >>> f.identity(default='no identity')
        'air_temperature'
        >>> f.identity()
        'long_name=Air Temperature'
        >>> f.del_property('long_name')
        >>> f.identity()
        'ncvar%tas'
        >>> f.nc_del_variable()
        'tas'
        >>> f.identity()
        'ncvar%tas'
        >>> f.identity()
        ''
        >>> f.identity(default='no identity')
        'no identity'

        """
        n = self.get_property("standard_name", None)
        if n is not None:
            return n

        for prop in ("cf_role", "axis", "long_name"):
            n = self.get_property(prop, None)
            if n is not None:
                return f"{prop}={n}"

        n = self.nc_get_variable(None)
        if n is not None:
            return f"ncvar%{n}"

        return default

    def identities(self, generator=False, **kwargs):
        """Return all possible identities.

        The identities comprise:

        * The ``standard_name`` property.
        * All properties, preceded by the property name and an equals
          e.g. ``'long_name=Air temperature'``.
        * The netCDF variable name, preceded by ``'ncvar%'``.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `identity`

        :Parameters:

            generator: `bool`, optional
                If True then return a generator for the identities,
                rather than a list.

                .. versionadded:: (cfdm) 1.8.9.0

            kwargs: optional
                Additional configuration parameters. Currently
                none. Unrecognised parameters are ignored.

                .. versionadded:: (cfdm) 1.8.9.0

        :Returns:

            `list` or generator
                The identities.

        **Examples:**

        >>> f.properties()
        {'foo': 'bar',
         'long_name': 'Air Temperature',
         'standard_name': 'air_temperature'}
        >>> f.nc_get_variable()
        'tas'
        >>> f.identities()
        ['air_temperature',
         'long_name=Air Temperature',
         'foo=bar',
         'standard_name=air_temperature',
         'ncvar%tas']
        >>> for i in f.identities(generator=True):
        ...     print(i)
        ...
        air_temperature
        long_name=Air Temperature
        foo=bar
        standard_name=air_temperature
        ncvar%tas

        """
        g = self._iter(body=self._identities_iter(), **kwargs)
        if generator:
            return g

        return list(g)
