from __future__ import print_function
from builtins import object

import inspect
import logging

import numpy

from ..functions import ATOL, RTOL

from ..decorators import _manage_log_level_via_verbosity


logger = logging.getLogger(__name__)


class Container(object):
    '''Mixin class for storing object components.

    .. versionadded:: 1.7.0

    '''
    def __repr__(self):
        '''Called by the `repr` built-in function.

    x.__repr__() <==> repr(x)

    .. versionadded:: 1.7.0

        '''
        return '<{0}: {1}>'.format(self.__class__.__name__, str(self))

    def __str__(self):
        '''Called by the `str` built-in function.

    x.__str__() <==> str(x)

    .. versionadded:: 1.7.0

        '''
        out = sorted(self._components)
        return ', '.join(out)

    @property
    def _ATOL(self):
        '''TODO
        '''
        return ATOL()

    @property
    def _RTOL(self):
        '''TODO
        '''
        return RTOL()

#    @classmethod
    def _equals(self, x, y, rtol=None, atol=None,
                ignore_data_type=False, **kwargs):
        '''Whether two objects are the same.

    Equality either uses one or other of the objects `!equals`
    methods, or casts them as numpy arrays and carried aout numericlly
    tolerant equality checks.

    .. versionadded:: 1.7.0

    :Parameters:

        atol: float, optional
            The tolerance on absolute differences between real
            numbers. The default value is set by the `ATOL` function.

        rtol: float, optional
            The tolerance on relative differences between real
            numbers. The default value is set by the `RTOL` function.

        '''
        if rtol is None:
            rtol = self._RTOL
        if atol is None:
            atol = self._ATOL

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

#        print (type(x), type(y))
#        print (repr(x), repr(y))
#        print (numpy.shape(x))
#        print (numpy.shape(y))
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

    .. versionadded:: 1.7.0

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
