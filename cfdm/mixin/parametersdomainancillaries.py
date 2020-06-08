from __future__ import print_function
from builtins import super

import logging

from . import Parameters

from ..decorators import _manage_log_level_via_verbosity


logger = logging.getLogger(__name__)


class ParametersDomainAncillaries(Parameters):
    '''Mixin class for parameter- and ancillary-valued terms.

    .. versionadded:: 1.7.0

    '''
    def __bool__(self):
        '''Called by the `bool` built-in function.

    x.__bool__() <==> bool(x)

    .. versionadded:: 1.7.0

        '''
        return (super().__bool__() or bool(self.domain_ancillaries()))

    def __nonzero__(self):
        '''Called by the `bool` built-in function.

    x.__nonzero__() <==> bool(x)

    .. versionadded:: 1.7.0

        '''
        return self.__bool__()

    def __str__(self):
        '''Called by the `str` built-in function.

    x.__str__() <==> str(x)

        '''
        out = [super().__str__()]

        out.append('Ancillaries: {0}'.format(', '.join(
            sorted(self.domain_ancillaries()))))

        return '; '.join(out)

    @_manage_log_level_via_verbosity
    def equals(self, other, rtol=None, atol=None, verbose=None,
               ignore_data_type=False, ignore_fill_value=False,
               ignore_type=False):
        '''Whether two instances are the same.

    Equality is strict by default. This means that:

    * the named parameters must be the same, with the same values and
      data types, and vector-valued parameters must also have same the
      size and be element-wise equal (see the *ignore_data_type*
      parameter), and

    ..

    * the names of domain ancillary constructs are the same.

    Two real numbers ``x`` and ``y`` are considered equal if
    ``|x-y|<=atol+rtol|y|``, where ``atol`` (the tolerance on absolute
    differences) and ``rtol`` (the tolerance on relative differences)
    are positive, typically very small numbers. See the *atol* and
    *rtol* parameters.

    Any type of object may be tested but, in general, equality is only
    possible with another object of the same type, or a subclass of
    one. See the *ignore_type* parameter.

    :Parameters:

        other:
            The object to compare for equality.

        atol: `float`, optional
            The tolerance on absolute differences between real
            numbers. The default value is set by the `cfdm.ATOL`
            function.

        rtol: `float`, optional
            The tolerance on relative differences between real
            numbers. The default value is set by the `cfdm.RTOL`
            function.

        verbose: `int` or `None`, optional
            If an integer from ``0`` to ``3``, corresponding to increasing
            verbosity (else ``-1`` as a special case of maximal and extreme
            verbosity), set for the duration of the method call (only) as
            the minimum severity level cut-off of displayed log messages,
            regardless of the global configured `cfdm.LOG_LEVEL`.

            Else, if `None` (the default value), log messages will be
            filtered out, or otherwise, according to the value of the
            `cfdm.LOG_LEVEL` setting.

            Overall, the higher a non-negative integer that is set (up to
            a maximum of ``3``) the more description that is printed to
            convey information about differences that lead to inequality.

        ignore_type: `bool`, optional
            Any type of object may be tested but, in general, equality
            is only possible with another object of the same type, or
            a subclass of one. If *ignore_type* is True then equality
            is possible for any object with a compatible API.

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

        '''
        if not super().equals(other, rtol=rtol, atol=atol,
                              verbose=verbose,
                              ignore_type=ignore_type):
            return False

        domain_ancillaries0 = self.domain_ancillaries()
        domain_ancillaries1 = other.domain_ancillaries()
        if set(domain_ancillaries0) != set(domain_ancillaries1):
            logger.info(
                "{0}: Different domain ancillary terms "
                "({1} != {2})".format(
                    self.__class__.__name__,
                    set(domain_ancillaries0), set(domain_ancillaries1)
                )
            )
            return False

        for term, value0 in domain_ancillaries0.items():
            value1 = domain_ancillaries1[term]
            if value0 is None and value1 is None:
                continue

            if value0 is None or value1 is None:
                logger.info(
                    "{}: Unequal {!r} domain ancillary terms "
                    "({!r} != {!r})".format(
                        self.__class__.__name__, term, value0, value1)
                )
                return False
        # --- End: for

        # Still here? Then the two instances are as equal as can be
        # ascertained in the absence of domains.
        return True

# --- End: class
