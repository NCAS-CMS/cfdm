import logging

import numpy

from ..functions import atol, rtol

from ..decorators import _manage_log_level_via_verbosity

from ..docstring import _docstring_substitution_definitions


logger = logging.getLogger(__name__)


class Container:
    """Mixin class for storing object components.

    .. versionadded:: (cfdm) 1.7.0

    """

    def __repr__(self):
        """Called by the `repr` built-in function.

        x.__repr__() <==> repr(x)

        .. versionadded:: (cfdm) 1.7.0

        """
        return f"<{self.__class__.__name__}: {self}>"

    def __str__(self):
        """Called by the `str` built-in function.

        x.__str__() <==> str(x)

        .. versionadded:: (cfdm) 1.7.0

        """
        out = sorted(self._components)
        return ", ".join(out)

    def __docstring_substitutions__(self):
        """Define docstring substitutions for the class hierarchy.

        The defined substitutions apply to this class along with
        all of its subclasses.

        These are in addtion to, and take precendence over, docstring
        substitutions defined by the base classes of this class.

        See `_docstring_substitutions` for details.

        .. versionaddedd:: (cfdm) 1.8.7.0

        :Returns:

            `dict`
                The docstring substitutions that have been applied.

        """
        return _docstring_substitution_definitions

    def __docstring_package_depth__(self):
        """Return the package depth for {{package}} substitutions.

        See `_docstring_package_depth` for details.

        """
        return 0

    @property
    def _atol(self):
        """Internal alias for `{{package}}.atol`.

        An alias is necessary to avoid a name clash with the keyword
        argument of identical name (`atol`) in calling functions.

        """
        return atol().value

    @property
    def _rtol(self):
        """Internal alias for `{{package}}.rtol`.

        An alias is necessary to avoid a name clash with the keyword
        argument of identical name (`rtol`) in calling functions.

        """
        return rtol().value

    def _equals(
        self, x, y, rtol=None, atol=None, ignore_data_type=False, **kwargs
    ):
        """Whether two objects are the same.

        Equality either uses one or other of the objects `!equals`
        methods, or casts them as numpy arrays and carried aout numericlly
        tolerant equality checks.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            {{atol: number, optional}}

            {{rtol: number, optional}}

        """
        if rtol is None:
            rtol = self._rtol
        else:
            rtol = float(rtol)

        if atol is None:
            atol = self._atol
        else:
            atol = float(atol)

        kwargs["ignore_data_type"] = ignore_data_type
        kwargs["rtol"] = rtol
        kwargs["atol"] = atol

        eq = getattr(x, "equals", None)
        if callable(eq):
            # --------------------------------------------------------
            # x has a callable "equals" method
            # --------------------------------------------------------
            # Check that the kwargs are OK
            try:
                # Python 3
                pass
            #                parameters = inspect.signature(eq).bind_partial(**kwargs)
            except AttributeError:
                # Python 2
                pass

            return eq(y, **kwargs)

        eq = getattr(y, "equals", None)
        if callable(eq):
            # --------------------------------------------------------
            # y has a callable "equals" method
            # --------------------------------------------------------
            # Check that the kwargs are OK
            try:
                # Python 3
                pass
            #                parameters = inspect.signature(eq).bind_partial(**kwargs)
            except AttributeError:
                # Python 2
                pass
            return eq(x, **kwargs)

        if numpy.shape(x) != numpy.shape(y):
            return False

        # ------------------------------------------------------------
        # Cast x and y as numpy arrays
        # ------------------------------------------------------------
        if not isinstance(x, numpy.ndarray):
            x = numpy.asanyarray(x)

        if not isinstance(y, numpy.ndarray):
            y = numpy.asanyarray(y)

        # THIS IS WHERE SOME NUMPY FUTURE WARNINGS ARE COMING FROM

        if not ignore_data_type and x.dtype != y.dtype:
            if x.dtype.kind not in ("S", "U") and y.dtype.kind not in (
                "S",
                "U",
            ):
                return False

        x_is_masked = numpy.ma.isMA(x)
        y_is_masked = numpy.ma.isMA(y)

        if not (x_is_masked or y_is_masked):
            try:
                return bool(numpy.allclose(x, y, rtol=rtol, atol=atol))
            except (IndexError, NotImplementedError, TypeError):
                return bool(numpy.all(x == y))
        else:
            if x_is_masked and y_is_masked:
                if (x.mask != y.mask).any():
                    return False
            elif (x_is_masked and x.mask.any()) or (
                y_is_masked and y.mask.any()
            ):
                return False

            try:
                return bool(numpy.ma.allclose(x, y, rtol=rtol, atol=atol))
            except (IndexError, NotImplementedError, TypeError):
                out = numpy.ma.all(x == y)
                if out is numpy.ma.masked:
                    return True
                else:
                    return bool(out)

    @_manage_log_level_via_verbosity
    def _equals_preprocess(self, other, verbose=None, ignore_type=False):
        """Common preprocessing prior to testing of equality.

        * If the LHS operand is (object identity) the RHS operand then
          return True.

        * If ignore_type=False and the LHS operand is not of the same type, or
          a squblcass of, the RHS operand then return False

        * If ignore_type=True and the LHS operand is not of the same type,
          or a sublcass of, the RHS operand then instantiate a new
          instance based on the the RHS class and return it.

        .. versionadded:: (cfdm) 1.7.0

        """
        # Check for object identity
        if self is other:
            return True

        # Check that each object is of compatible type
        if ignore_type:
            if not isinstance(other, self.__class__):
                other = type(self)(source=other, copy=False)
        elif not isinstance(other, self.__class__):
            logger.info(
                f"{self.__class__.__name__}: Incompatible type: {type(other)}"
            )
            return False

        return other

    def _package(self):
        """Return the name of the package in which this class resides.

        :Returns:

            `str`
               The package name

        """
        depth = self.__class__._docstring_package_depth(self.__class__)
        return ".".join(self.__module__.split(".")[0 : depth + 1])
