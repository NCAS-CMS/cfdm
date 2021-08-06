import logging

from ..decorators import _manage_log_level_via_verbosity
from . import Parameters

logger = logging.getLogger(__name__)


class ParametersDomainAncillaries(Parameters):
    """Mixin class for parameter- and ancillary-valued terms.

    .. versionadded:: (cfdm) 1.7.0

    """

    def __bool__(self):
        """Called by the `bool` built-in function.

        x.__bool__() <==> bool(x)

        .. versionadded:: (cfdm) 1.7.0

        """
        return super().__bool__() or bool(self.domain_ancillaries())

    def __str__(self):
        """Called by the `str` built-in function.

        x.__str__() <==> str(x)

        """
        out = [super().__str__()]

        x = ", ".join(sorted(self.domain_ancillaries()))
        out.append(f"Ancillaries: {x}")

        return "; ".join(out)

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
          *ignore_data_type* parameter), and

        ..

        * the names of domain ancillary constructs are the same.

        {{equals tolerance}}

        Any type of object may be tested but, in general, equality is
        only possible with another object of the same type, or a
        subclass of one. See the *ignore_type* parameter.

        :Parameters:

            other:
                The object to compare for equality.

            {{atol: number, optional}}

            {{rtol: number, optional}}

            {{ignore_type: `bool`, optional}}

            {{verbose: `int` or `str` or `None`, optional}}

        :Returns:

            `bool`
                Whether the two instances are equal.

        **Examples:**

        >>> c.equals(c)
        True
        >>> c.equals(c.copy())
        True
        >>> c.equals(None)
        False

        """
        if not super().equals(
            other,
            rtol=rtol,
            atol=atol,
            verbose=verbose,
            ignore_type=ignore_type,
        ):
            return False

        domain_ancillaries0 = self.domain_ancillaries()
        domain_ancillaries1 = other.domain_ancillaries()
        if set(domain_ancillaries0) != set(domain_ancillaries1):
            logger.info(
                f"{ self.__class__.__name__}: Different domain ancillary "
                "terms "
                f"({set(domain_ancillaries0)} != {set(domain_ancillaries1)})"
            )  # pragma: no cover
            return False

        for term, value0 in domain_ancillaries0.items():
            value1 = domain_ancillaries1[term]
            if value0 is None and value1 is None:
                continue

            if value0 is None or value1 is None:
                logger.info(
                    f"{self.__class__.__name__}: Unequal {term!r} domain "
                    f"ancillary terms ({value0!r} != {value1!r})"
                )  # pragma: no cover
                return False

        # Still here? Then the two instances are as equal as can be
        # ascertained in the absence of domains.
        return True
