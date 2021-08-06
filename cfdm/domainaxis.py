import logging

from . import core, mixin
from .decorators import _manage_log_level_via_verbosity

logger = logging.getLogger(__name__)


class DomainAxis(
    mixin.NetCDFDimension,
    mixin.NetCDFUnlimitedDimension,
    mixin.Container,
    core.DomainAxis,
):
    """A domain axis construct of the CF data model.

    A domain axis construct specifies the number of points along an
    independent axis of the domain. It comprises a positive integer
    representing the size of the axis. In CF-netCDF it is usually
    defined either by a netCDF dimension or by a scalar coordinate
    variable, which implies a domain axis of size one. The field
    construct's data array spans the domain axis constructs of the
    domain, with the optional exception of size one axes, because
    their presence makes no difference to the order of the elements.

    **NetCDF interface**

    The netCDF dimension name of the construct may be accessed with
    the `nc_set_dimension`, `nc_get_dimension`, `nc_del_dimension` and

    Whether or not the netCDF is unlimited may be accessed with the
    `nc_is_unlimited` and `nc_set_unlimited` methods.
    `nc_has_dimension` methods.

    The netCDF dimension group structure may be accessed with the
    `nc_set_dimension`, `nc_get_dimension`, `nc_dimension_groups`,
    `nc_clear_dimension_groups` and `nc_set_dimension_groups` methods.

    .. versionadded:: (cfdm) 1.7.0

    """

    def __init__(self, size=None, source=None, copy=True):
        """**Initialisation**

        :Parameters:

            size: `int`, optional
                The size of the domain axis.

                The size may also be set after initialisation with the
                `set_size` method.

                *Parameter example:*
                  ``size=192``

            source: optional
                Initialise the size from that of *source*.

                {{init source}}

            {{init copy: `bool`, optional}}

        """
        super().__init__(size=size, source=source, copy=copy)

        self._initialise_netcdf(source)

    def __str__(self):
        """Called by the `str` built-in function.

        x.__str__() <==> str(x)

        .. versionadded:: (cfdm) 1.7.0

        """
        return f"size({self.get_size('')})"

    def _identities_iter(self):
        """Return all possible identities.

        See `identities` for details and examples.

        :Returns:

            generator
                The identities.

        """
        n = self.nc_get_dimension(None)
        if n is not None:
            yield f"ncdim%{n}"

    def creation_commands(
        self, namespace=None, indent=0, string=True, name="c", header=True
    ):
        """Returns the commands to create the domain axis construct.

        .. versionadded:: (cfdm) 1.8.7.0

        .. seealso:: `{{package}}.Field.creation_commands`

        :Parameters:

            {{namespace: `str`, optional}}

            {{indent: `int`, optional}}

            {{string: `bool`, optional}}

            {{name: `str`, optional}}

            {{header: `bool`, optional}}

        :Returns:

            {{returns creation_commands}}

        **Examples:**

        >>> x = {{package}}.DomainAxis(size=12)
        >>> x.nc_set_dimension('time')
        >>> print(x.creation_commands(header=False))
        c = {{package}}.DomainAxis()
        c.set_size(12)
        c.nc_set_dimension('time')

        """
        if namespace is None:
            namespace = self._package() + "."
        elif namespace and not namespace.endswith("."):
            namespace += "."

        out = []

        if header:
            out.append("#")
            out.append(f"# {self.construct_type}:")
            identity = self.identity()
            if identity:
                out[-1] += f" {identity}"

        out.append(f"{name} = {namespace}{self.__class__.__name__}()")

        size = self.get_size(None)
        if size is not None:
            out.append(f"{name}.set_size({size})")

        nc = self.nc_get_dimension(None)
        if nc is not None:
            out.append(f"{name}.nc_set_dimension({nc!r})")

        if self.nc_is_unlimited():
            out.append("fc.nc_set_unlimited({True})")

        if string:
            indent = " " * indent
            out[0] = indent + out[0]
            out = (f"\n{indent}").join(out)

        return out

    @_manage_log_level_via_verbosity
    def equals(self, other, verbose=None, ignore_type=False):
        """Whether two domain axis constructs are the same.

        Equality is strict by default. This means that:

        * the axis sizes must be the same.

        Any type of object may be tested but, in general, equality is
        only possible with another domain axis construct, or a
        subclass of one. See the *ignore_type* parameter.

        NetCDF elements, such as netCDF variable and dimension names,
        do not constitute part of the CF data model and so are not
        checked.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            other:
                The object to compare for equality.

            {{verbose: `int` or `str` or `None`, optional}}

            {{ignore_type: `bool`, optional}}

        :Returns:

            `bool`
                Whether the two domain axis constructs are equal.

        **Examples:**

        >>> d.equals(d)
        True
        >>> d.equals(d.copy())
        True
        >>> d.equals('not a domain axis')
        False

        >>> d = {{package}}.DomainAxis(1)
        >>> e = {{package}}.DomainAxis(99)
        >>> d.equals(e, verbose=3)
        DomainAxis: Different axis sizes: 1 != 99
        False

        """
        pp = super()._equals_preprocess(
            other, verbose=verbose, ignore_type=ignore_type
        )
        if pp is True or pp is False:
            return pp

        other = pp

        # Check that each axis has the same size
        self_size = self.get_size(None)
        other_size = other.get_size(None)
        if not self_size == other_size:
            logger.info(
                f"{self.__class__.__name__}: Different axis sizes: "
                f"{self_size} != {other_size}"
            )
            return False

        return True

    def identity(self, default=""):
        """Return the canonical identity.

        The identity is the first found of the following:

        1. The netCDF dimension name, preceded by 'ncdim%'.
        2. The value of the default parameter.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `identities`

        :Parameters:

            default: optional
                If no identity can be found then return the value of
                the default parameter.

        :Returns:

                The identity.

        **Examples:**

        >>> d = {{package}}.DomainAxis(size=9)
        >>> d.nc_set_dimension('time')
        >>> d.identity()
        'ncdim%time'
        >>> d.identity(default='no identity')
        'ncdim%time'
        >>> d.nc_del_dimension()
        'time'
        >>> d.identity()
        ''
        >>> d.identity(default='no identity')
        'no identity'

        """
        n = self.nc_get_dimension(None)
        if n is not None:
            return f"ncdim%{n}"

        return default

    def identities(self, generator=False, **kwargs):
        """Return all possible identities.

        The identities comprise:

        * The netCDF dimension name, preceded by 'ncdim%'.

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

        >>> d = {{package}}.DomainAxis(size=9)
        >>> d.nc_set_dimension('time')
        >>> d.identities()
        ['ncdim%time']
        >>> d.nc_del_dimension()
        'time'
        >>> d.identities()
        []
        >>> for i in d.identities(generator=True):
        ...     print(i)
        ...

        """
        g = self._iter(body=self._identities_iter(), **kwargs)
        if generator:
            return g

        return list(g)
