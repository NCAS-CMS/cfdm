import logging
from copy import deepcopy

import numpy

from . import core, mixin
from .data import Data
from .decorators import _manage_log_level_via_verbosity

logger = logging.getLogger(__name__)


class CellMethod(mixin.Container, core.CellMethod):
    """A cell method construct of the CF data model.

    One or more cell method constructs describe how the cell values of
    the field construct represent the variation of the physical
    quantity within its cells, i.e. the structure of the data at a
    higher resolution.

    A single cell method construct consists of a set of axes, a
    "method" property which describes how a value of the field
    construct's data array describes the variation of the quantity
    within a cell over those axes (e.g. a value might represent the
    cell area average), and descriptive qualifiers serving to indicate
    more precisely how the method was applied (e.g. recording the
    spacing of the original data, or the fact that the method was
    applied only over El Nino years).

    .. versionadded:: (cfdm) 1.7.0

    """

    def __new__(cls, *args, **kwargs):
        """This must be overridden in subclasses.

        .. versionadded:: (cfdm) 1.8.7.0

        """
        instance = super().__new__(cls)
        instance._Data = Data
        return instance

    def __str__(self):
        """Called by the `str` built-in function.

        x.__str__() <==> str(x)

        Returns a CF-netCDF-like string of the cell method.

        Note that if the intention is to use this string in a CF-netCDF
        cell_methods attribute then, unless they are standard names, the
        axes names will need to be modified to be netCDF dimension names.

        .. versionadded:: (cfdm) 1.7.0

        """
        string = [f"{axis}:" for axis in self.get_axes(())]

        string.append(self.get_method(""))

        for portion in ("within", "where", "over"):
            q = self.get_qualifier(portion, None)
            if q is not None:
                string.extend((portion, q))

        interval = self.get_qualifier("interval", ())
        comment = self.get_qualifier("comment", None)

        if interval:
            x = ["("]

            y = [f"interval: {data}" for data in interval]
            x.append(" ".join(y))

            if comment is not None:
                x.append(f" comment: {comment}")

            x.append(")")

            string.append("".join(x))

        elif comment is not None:
            string.append(f"({comment})")

        return " ".join(string)

    def _identities_iter(self):
        """Return all possible identities.

        See `identities` for details and examples.

        :Returns:

            generator
                The identities.

        """
        n = self.get_method(None)
        if n is not None:
            yield f"method:{n}"

    def creation_commands(
        self, namespace=None, indent=0, string=True, name="c", header=True
    ):
        """Returns the commands to create the cell method construct.

        .. versionadded:: (cfdm) 1.8.7.0

        .. seealso:: `{{package}}.Data.creation_commands`,
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

        >>> x = {{package}}.CellMethod(
        ...     axes=['area'],
        ...     qualifiers={'over': 'land'}
        ... )
        >>> print(x.creation_commands(header=False))
        c = {{package}}.CellMethod()
        c.set_axes(('area',))
        c.set_qualifier('over', 'land')

        """
        namespace0 = namespace
        if namespace is None:
            namespace = self._package() + "."
        elif namespace and not namespace.endswith("."):
            namespace += "."

        out = []

        method = self.get_method(None)

        if header:
            out.append("#")
            out.append(f"# {self.construct_type}:")
            if method is not None:
                out[-1] += f" {method}"

        out.append(f"{name} = {namespace}{self.__class__.__name__}()")

        if method is not None:
            out.append(f"{name}.set_method({method!r})")

        axes = self.get_axes(None)
        if axes is not None:
            out.append(f"{name}.set_axes({axes!r})")

        for term, value in self.qualifiers().items():
            if term == "interval":
                value = deepcopy(value)
                for i, data in enumerate(value[:]):
                    if isinstance(data, self._Data):
                        value[i] = data.creation_commands(
                            name=None,
                            namespace=namespace0,
                            indent=0,
                            string=True,
                        )
                    else:
                        value[i] = str(data)

                value = ", ".join(value)
                value = f"[{value}]"
            else:
                value = repr(value)

            out.append(f"{name}.set_qualifier({term!r}, {value})")

        if string:
            indent = " " * indent
            out[0] = indent + out[0]
            out = ("\n" + indent).join(out)

        return out

    def dump(self, display=True, _title=None, _level=0):
        """A full description of the cell method construct.

        Returns a description the method, all qualifiers and the axes
        to which it applies.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            display: `bool`, optional
                If False then return the description as a string. By
                default the description is printed.

        :Returns:

            {{returns dump}}

        """
        indent0 = "    " * _level

        if _title is None:
            _title = "Cell Method: "

        return indent0 + _title + str(self)

    @_manage_log_level_via_verbosity
    def equals(
        self,
        other,
        rtol=None,
        atol=None,
        verbose=None,
        ignore_qualifiers=(),
        ignore_type=False,
    ):
        """Whether two cell method constructs are the same.

        Equality is strict by default. This means that:

        * the descriptive qualifiers must be the same (see the
          *ignore_qualifiers* parameter).

        The axes of the cell method constructs are *not* considered,
        because they may only be correctly interpreted by the field
        constructs that contain the cell method constructs in
        question. They are, however, taken into account when two
        fields constructs are tested for equality.

        {{equals tolerance}}

        Any type of object may be tested but, in general, equality is
        only possible with another cell method construct, or a
        subclass of one. See the *ignore_type* parameter.

        {{equals tolerance}}

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            other:
                The object to compare for equality.

            {{atol: number, optional}}

            {{rtol: number, optional}}

            {{verbose: `int` or `str` or `None`, optional}}

            ignore_qualifiers: sequence of `str`, optional
                The names of qualifiers to omit from the comparison.

            {{ignore_type: `bool`, optional}}

        :Returns:

            `bool`
                Whether the two cell method constructs are equal.

        **Examples:**

        >>> c = {{package}}.CellMethod()
        >>> c.equals(c)
        True
        >>> c.equals(c.copy())
        True
        >>> c.equals('not a cell method')
        False

        """
        pp = super()._equals_preprocess(
            other, verbose=verbose, ignore_type=ignore_type
        )
        if pp is True or pp is False:
            return pp

        other = pp

        # ------------------------------------------------------------
        # Check the methods
        # ------------------------------------------------------------
        if self.get_method(None) != other.get_method(None):
            logger.info(
                f"{self.__class__.__name__}: Different methods: "
                f"{self.get_method(None)!r} != {other.get_method(None)!r}"
            )  # pragma: no cover
            return False

        # ------------------------------------------------------------
        # Check the qualifiers
        # ------------------------------------------------------------
        self_qualifiers = self.qualifiers()
        other_qualifiers = other.qualifiers()

        for prop in tuple(ignore_qualifiers) + ("interval",):
            self_qualifiers.pop(prop, None)
            other_qualifiers.pop(prop, None)

        if set(self_qualifiers) != set(other_qualifiers):
            for q in set(self_qualifiers).symmetric_difference(
                other_qualifiers
            ):
                logger.info(
                    f"{self.__class__.__name__}: Non-common qualifier: {q!r}"
                )  # pragma: no cover
            return False

        for qualifier, x in self_qualifiers.items():
            y = other_qualifiers[qualifier]

            if not self._equals(
                x,
                y,
                rtol=rtol,
                atol=atol,
                ignore_data_type=True,
                verbose=verbose,
                basic=True,
            ):
                logger.info(
                    f"{self.__class__.__name__}: Different {prop} "
                    f"qualifiers: {x!r}, {y!r}"
                )  # pragma: no cover
                return False

        if "interval" in ignore_qualifiers:
            return True

        intervals0 = self.get_qualifier("interval", ())
        intervals1 = other.get_qualifier("interval", ())
        if intervals0:
            if not intervals1:
                logger.info(
                    f"{self.__class__.__name__}: Different interval "
                    f"qualifiers: {intervals0!r} != {intervals1!r}"
                )  # pragma: no cover
                return False

            if len(intervals0) != len(intervals1):
                logger.info(
                    f"{self.__class__.__name__}: Different numbers of "
                    f"interval qualifiers: {intervals0!r} != {intervals1!r}"
                )  # pragma: no cover
                return False

            for data0, data1 in zip(intervals0, intervals1):
                if not self._equals(
                    data0,
                    data1,
                    rtol=rtol,
                    atol=atol,
                    verbose=verbose,
                    ignore_data_type=True,
                    ignore_fill_value=True,
                ):
                    logger.info(
                        f"{self.__class__.__name__}: Different interval "
                        f"qualifiers: {intervals0!r} != {intervals1!r}"
                    )  # pragma: no cover
                    return False

        elif intervals1:
            logger.info(
                f"{self.__class__.__name__}: Different intervals: "
                f"{intervals0!r} != {intervals1!r}"
            )  # pragma: no cover
            return False

        # ------------------------------------------------------------
        # Do NOT check the axes
        # ------------------------------------------------------------

        return True

    def identity(self, default=""):
        """Return the canonical identity for the cell method construct.

        By default the identity is the first found of the following:

        1. The method, preceded by 'method:'
        2. The value of the *default* parameter.

        .. versionadded:: (cfdm) 1.7.0

        .. seealso:: `identities`

        :Parameters:

            default: optional
                If no identity can be found then return the value of the
                default parameter.

        :Returns:

                The identity.

        **Examples:**

        >>> f = {{package}}.example_field(1)
        >>> c = f.get_construct('cellmethod1')
        >>> c.get_method()
        'maximum'
        >>> c.identity()
        'method:maximum'
        >>> c.del_method()
        'maximum'
        >>> c.identity()
        ''
        >>> c.identity(default='no identity')
        'no identity'

        """
        n = self.get_method(None)
        if n is not None:
            return f"method:{n}"

        return default

    def identities(self, generator=False, **kwargs):
        """Return all possible identities.

        The identities comprise:

        * The method, preceded by 'method:'.

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

        >>> f = {{package}}.example_field(1)
        >>> c = f.get_construct('cellmethod1')
        >>> c.get_method()
        'maximum'
        >>> c.identities()
        ['method:maximum']
        >>> c.del_method()
        'maximum'
        >>> c.identities()
        []
        >>> for i in c.identities(generator=True):
        ...     print(i)
        ...

        """
        g = self._iter(body=self._identities_iter(), **kwargs)
        if generator:
            return g

        return list(g)

    def sorted(self, indices=None):
        """Return a new cell method construct with sorted axes.

        The axes are sorted by domain axis construct identifier or
        standard name, and any intervals are sorted accordingly.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            indices: ordered sequence of `int`, optional
                Sort the axes with the given indices. By default the axes
                are sorted by domain axis construct identifier or standard
                name.

        :Returns:

            `CellMethod`
                A new cell method construct with sorted axes.

        **Examples:**

        >>> cm = {{package}}.CellMethod(axes=['domainaxis1', 'domainaxis0'],
        ...                      method='mean',
        ...                      qualifiers={'interval': [1, 2]})
        >>> cm
        <{{repr}}CellMethod: domainaxis1: domainaxis0: mean (interval: 1 interval: 2)>
        >>> cm.sorted()
        <{{repr}}CellMethod: domainaxis0: domainaxis1: mean (interval: 2 interval: 1)>

        >>> cm = {{package}}.CellMethod(axes=['domainaxis0', 'area'],
        ...                      method='mean',
        ...                      qualifiers={'interval': [1, 2]})
        >>> cm
        <{{repr}}CellMethod: domainaxis0: area: mean (interval: 1 interval: 2)>
        >>> cm.sorted()
        <{{repr}}CellMethod: area: domainaxis0: mean (interval: 2 interval: 1)>

        """
        new = self.copy()

        axes = new.get_axes(())
        if len(axes) == 1:
            return new

        if indices is None:
            indices = numpy.argsort(axes)
        elif len(indices) != len(axes):
            raise ValueError(
                f"Can't sort cell method axes. The given indices ({indices}) "
                f"do not correspond to the number of axes ({axes})"
            )

        axes2 = []
        for i in indices:
            axes2.append(axes[i])

        new.set_axes(tuple(axes2))

        intervals = new.get_qualifier("interval", ())
        if len(intervals) <= 1:
            return new

        intervals2 = []
        for i in indices:
            intervals2.append(intervals[i])

        new.set_qualifier("interval", tuple(intervals2))

        return new
