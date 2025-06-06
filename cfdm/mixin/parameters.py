import logging
import textwrap

from ..decorators import _display_or_return, _manage_log_level_via_verbosity
from . import Container

logger = logging.getLogger(__name__)


class Parameters(Container):
    """Mixin class for parameters.

    .. versionadded:: (cfdm) 1.7.0

    """

    def __bool__(self):
        """Called by the `bool` built-in function.

        x.__bool__() <==> bool(x)

        .. versionadded:: (cfdm) 1.7.0

        """
        return bool(self.parameters())

    def __str__(self):
        """Called by the `str` built-in function.

        x.__str__() <==> str(x)

        .. versionadded:: (cfdm) 1.7.0

        """
        x = [f"{p}={v}" for p, v in sorted(self.parameters().items())]
        return ", ".join(x)

    def creation_commands(
        self, namespace=None, indent=0, string=True, name="p", header=True
    ):
        """Return the commands that would create the component.

        .. versionadded:: (cfdm) 1.12.2.0

        .. seealso:: `{{package}}.Field.creation_commands`

        :Parameters:

            {{namespace: `str`, optional}}

            {{indent: `int`, optional}}

            {{string: `bool`, optional}}

            {{name: `str`, optional}}

            {{header: `bool`, optional}}

        :Returns:

            {{returns creation_commands}}

        **Examples**

        >>> x = {{package}}.{{class}}({'algorithm': 'granular_bitround'})
        >>> x.nc_set_variable('var')
        >>> print(x.creation_commands(header=False))
        p = {{package}}.{{class}}()
        p.set_parameters({'algorithm': 'granular_bitround'})
        p.nc_set_variable('var')

        """
        if namespace is None:
            namespace = self._package() + "."
        elif namespace and not namespace.endswith("."):
            namespace += "."

        out = []

        if header:
            out.append("#")
            out.append("#")
            out[-1] += f" {self.__class__.__name__.lower()} component"

        out.append(f"{name} = {namespace}{self.__class__.__name__}()")

        parameters = self.parameters()
        if parameters:
            out.append(f"{name}.set_parameters({parameters})")

        try:
            nc = self.nc_get_variable(None)
        except AttributeError:
            pass
        else:
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
        _prefix="",
        _title=None,
        _create_title=True,
        _level=0,
    ):
        """A full description.

        .. versionadded:: (cfdm) 1.12.2.0

        :Parameters:

            display: `bool`, optional
                If False then return the description as a string. By
                default the description is printed.

        :Returns:

            {{returns dump}}

        """
        indent0 = "    " * _level
        string = []

        # Title
        if _create_title:
            if _title is None:
                string.append(f"{indent0}{self.__class__.__name__}: ")
            else:
                string.append(indent0 + _title)

        # Parameters
        indent1 = "    " * (_level + 1)
        parameters = self.parameters()
        for param, value in sorted(parameters.items()):
            name = f"{indent1}{_prefix}{param} = "
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

    @_manage_log_level_via_verbosity
    def equals(
        self,
        other,
        rtol=None,
        atol=None,
        verbose=None,
        ignore_data_type=False,
        ignore_fill_value=False,
        ignore_type=False,
    ):
        """Whether two instances are the same.

        Equality is strict by default. This means that:

        * the named parameters must be the same, with the same values
          and data types, and vector-valued parameters must also have
          same the size and be element-wise equal (see the
          *ignore_data_type* parameter).

        {{equals tolerance}}

        Any type of object may be tested but, in general, equality is
        only possible with another object of the same type, or a
        subclass of one. See the *ignore_type* parameter.

        :Parameters:

            other:
                The object to compare for equality.

            {{atol: number, optional}}

            {{rtol: number, optional}}

            {{ignore_data_type: `bool`, optional}}

            {{ignore_type: `bool`, optional}}

            {{verbose: `int` or `str` or `None`, optional}}

        :Returns:

            `bool`
               Whether the two instances are equal.

        **Examples**

        >>> d.equals(d)
        True
        >>> d.equals(d.copy())
        True
        >>> d.equals(None)
        False

        """
        pp = super()._equals_preprocess(
            other, verbose=verbose, ignore_type=ignore_type
        )
        if pp is True or pp is False:
            return pp

        other = pp

        # Check that the coordinate conversion parameter terms match
        parameters0 = self.parameters()
        parameters1 = other.parameters()
        if set(parameters0) != set(parameters1):
            logger.info(
                f"{self.__class__.__name__}: Different parameter-valued "
                f"terms: {set(parameters0)} != {set(parameters1)}"
            )  # pragma: no cover
            return False

        # Check that the parameter values are equal
        for term, value0 in parameters0.items():
            value1 = parameters1[term]

            if value0 is None and value1 is None:
                # Parameter values are both None
                continue

            if not self._equals(
                value0,
                value1,
                rtol=rtol,
                atol=atol,
                verbose=verbose,
                ignore_data_type=True,
                ignore_fill_value=ignore_fill_value,
                ignore_type=ignore_type,
            ):
                logger.info(
                    f"{self.__class__.__name__}: Unequal {term!r} terms: "
                    f"{value0!r} != {value1!r}"
                )  # pragma: no cover
                return False

        # Still here? Then the two parameter collections are equal
        return True
