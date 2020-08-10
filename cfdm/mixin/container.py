import inspect
import logging

import numpy

from ..functions import atol, rtol

from ..decorators import _manage_log_level_via_verbosity

logger = logging.getLogger(__name__)


class Container:
    '''Mixin class for storing object components.

    .. versionadded:: (cfdm) 1.7.0

    '''
    def __repr__(self):
        '''Called by the `repr` built-in function.

    x.__repr__() <==> repr(x)

    .. versionadded:: (cfdm) 1.7.0

        '''
        return '<{0}: {1}>'.format(self.__class__.__name__, str(self))

    def __str__(self):
        '''Called by the `str` built-in function.

    x.__str__() <==> str(x)

    .. versionadded:: (cfdm) 1.7.0

        '''
        out = sorted(self._components)    
        return ', '.join(out)

    def __docstring_substitution__(self):
        '''TODO
    Substitutions may be easily modified by overriding the
    __docstring_substitution__ method.
    Modifications can be applied to any class, and will only apply to
    that class and all of its subclases.
    If the key is a string then the special subtitutions will be
    applied to the dictionary values after replacement in the
    docstring.
    If the key is a compiled regular expession then the special
    subtitutions will be applied to the match of the regular
    expression after replacement in the docstring.
    For example::
       def __docstring_substitution__(self):
           def _upper(match):
               return match.group(1).upper()
           out = {
                  # Simple substitutions 
                  '{{repr}}': 'CF '
                  '{{foo}}': 'bar'
                  '{{parameter: `int`}}': """parameter: `int`
               This parameter does something to `{{class}}`
               instances. It has no default value.""",
                   # Regular expression subsititions
                   # 
                   # Convert text to upper case
                   re.compile('{{<upper (.*?)>}}'): _upper
            }
           return out
        '''
        return {
            # Parameter descriptions
            '{{inplace: `bool`, optional}}':
            """inplace: `bool`, optional
            If True then do the operation in-place and return `None`.""",

            # verbose
            '{{verbose: `int` or `str` or `None`, optional}}':
            """verbose: `int` or `str` or `None`, optional
            If an integer from ``-1`` to ``3``, or an equivalent
            string equal ignoring case to one of:

            * ``'DISABLE'`` (``0``)
            * ``'WARNING'`` (``1``)
            * ``'INFO'`` (``2``)
            * ``'DETAIL'`` (``3``)
            * ``'DEBUG'`` (``-1``)

            set for the duration of the method call only as the
            minimum cut-off for the verboseness level of displayed
            output (log) messages, regardless of the
            globally-configured `cf.log_level`.  Note that increasing
            numerical value corresponds to increasing verbosity, with
            the exception of ``-1`` as a special case of maximal and
            extreme verbosity.

            Otherwise, if `None` (the default value), output messages
            will be shown according to the value of the `cf.log_level`
            setting.

            Overall, the higher a non-negative integer or equivalent
            string that is set (up to a maximum of ``3``/``'DETAIL'``)
            for increasing verbosity, the more description that is
            printed to convey information about the operation.""",

            # ignore_type
            '{{ignore_type: `bool`, optional}}':
            """ignore_type: `bool`, optional
            Any type of object may be tested but, in general, equality
            is only possible with another `{{class}}` instance, or a
            subclass of one. If *ignore_type* is True then
            ``{{package}}.{{class}}(source=other)`` is tested, rather
            than the ``other`` defined by the *other* parameter.""",
        }

    @property
    def _atol(self):
        '''Internal alias for `cfdm.atol`.

    An alias is necessary to avoid a name clash with the keyword argument
    of identical name (`atol`) in calling functions.
        '''
        return atol()

    @property
    def _rtol(self):
        '''Internal alias for `cfdm.rtol`.

    An alias is necessary to avoid a name clash with the keyword argument
    of identical name (`rtol`) in calling functions.
        '''
        return rtol()

    def _equals(self, x, y, rtol=None, atol=None,
                ignore_data_type=False, **kwargs):
        '''Whether two objects are the same.

    Equality either uses one or other of the objects `!equals`
    methods, or casts them as numpy arrays and carried aout numericlly
    tolerant equality checks.

    .. versionadded:: (cfdm) 1.7.0

    :Parameters:

        atol: float, optional
            The tolerance on absolute differences between real
            numbers. The default value is set by the `atol` function.

        rtol: float, optional
            The tolerance on relative differences between real
            numbers. The default value is set by the `rtol` function.

        '''
        if rtol is None:
            rtol = self._rtol
        if atol is None:
            atol = self._atol

        kwargs['ignore_data_type'] = ignore_data_type
        kwargs['rtol'] = rtol
        kwargs['atol'] = atol

        eq = getattr(x, 'equals', None)
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

        eq = getattr(y, 'equals', None)
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
            if (x.dtype.kind not in ('S', 'U')
                    and y.dtype.kind not in ('S', 'U')):
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
            elif ((x_is_masked and x.mask.any()) or
                  (y_is_masked and y.mask.any())):
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
        '''Common preprocessing prior to testing of equality.

    * If the LHS operand is (object identity) the RHS operand then
      return True.

    * If ignore_type=False and the LHS operand is not of the same type, or
      a squblcass of, the RHS operand then return False

    * If ignore_type=True and the LHS operand is not of the same type,
      or a sublcass of, the RHS operand then instantiate a new
      instance based on the the RHS class and return it.

    .. versionadded:: (cfdm) 1.7.0

        '''
        # Check for object identity
        if self is other:
            return True

        # Check that each object is of compatible type
        if ignore_type:
            if not isinstance(other, self.__class__):
                other = type(self)(source=other, copy=False)
        elif not isinstance(other, self.__class__):
            logger.info("{}: Incompatible type: {}".format(
                self.__class__.__name__, type(other)))
            return False

        return other

# --- End: class
