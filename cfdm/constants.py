import logging
import sys

from copy import deepcopy

from enum import Enum

from functools import total_ordering

import numpy


'''A dictionary of useful constants.

Whilst the dictionary may be modified directly, it is safer to
retrieve and set the values with the dedicated get-and-set functions.

:Keys:

    ATOL: `float`
      The value of absolute tolerance for testing numerically tolerant
      equality.

    RTOL: `float`
      The value of relative tolerance for testing numerically tolerant
      equality.

    LOG_LEVEL: `str`
      The minimal level of seriousness for which log messages are
      shown.  See `cfdm.log_level`.

'''
CONSTANTS = {
    'ATOL': sys.float_info.epsilon,
    'RTOL': sys.float_info.epsilon,
    'LOG_LEVEL': logging.getLevelName(logging.getLogger().level),
}


# --------------------------------------------------------------------
# logging
# --------------------------------------------------------------------
class ValidLogLevels(Enum):
    DISABLE = 0
    WARNING = 1
    INFO = 2
    DETAIL = 3
    DEBUG = -1


# --------------------------------------------------------------------
# masked
# --------------------------------------------------------------------
'''A constant that allows data values to be masked by direct
assignment. This is consistent with the behaviour of numpy masked
arrays.

For example, masking every element of a field constructs data array
could be done as follows:

>>> f[...] = cfdm.masked

'''
masked = numpy.ma.masked


@total_ordering
class Constant:
    '''A container for a constant with context manager support.

    The constant value is accessed via the `value` attribute:

       >>> c = cfdm.Constant(1.9)
       >>> c.value
       1.9

    Conversion to `int`, `float` and `str` is with the usual built-in
    functions:

       >>> c = cfdm.Constant(1.9)
       >>> int(c)
       1
       >>> float(c)
       1.9
       >>> str(c)
       '1.9'

    Augmented arithmetic assignments (``+=``, ``-=``, ``*=``, ``/=``,
    ``//=``) update `Constant` objects in-place:

       >>> c = cfdm.Constant(20)
       >>> c.value
       20
       >>> c /= 2
       >>> c
       <Constant: 10.0>
       >>> c += c
       <Constant: 20.0>

       >>> c = cfdm.Constant('New_')
       >>> c *= 2
       <Constant: 'New_New_'>

    Binary arithmetic operations (``+``, ``-``, ``*``, ``/``, ``//``)
    are equivalent to the operation acting on the `Constant` object's
    `value` attribute:

       >>> c = cfdm.Constant(20)
       >>> c.value
       20
       >>> c * c
       400
       >>> c * 3
       60
       >>> 2 - c
       -38

       >>> c = cfdm.Constant('New_')
       >>> c * 2
       'New_New_'

    Care is required when the right hand side operand is a `numpy`
    array

       >>> import numpy
       >>> c * numpy.array([1, 2, 3])
       array([20, 40, 60])
       >>> d = numpy.array([1, 2, 3]) * c
       >>> d
       array([10, 20, 30], dtype=object)
       >>> type(d[0])
       int

    Unary arithmetic operations (``+``, ``-``, `abs`) are equivalent
    to the operation acting on the `Constant` object's `value`
    attribute:

       >>> c = cfdm.Constant(-20)
       >>> c.value
       -20
       >>> -c
       20
       >>> abs(c)
       20
       >>> +c
       -20

    Rich comparison operations are equivalent to the operation acting
    on the `Constant` object's `value` attribute:

       >>> c = cfdm.Constant(20)
       >>> d = cfdm.Constant(1)
       >>> c.value
       20
       >>> d.value
       1
       >>> d < c
       True
       >>> c != 20
       False
       >>> 20 == c
       True

       >>> c = cfdm.Constant('new')
       >>> d = cfdm.Constant('old')
       >>> c == d
       False
       >>> c == 'new'
       True
       >>> c != 3
       True
       >>> 3 == c
       False

       >>> import numpy
       >>> c = cfdm.Constant(20)
       >>> c < numpy.array([10, 20, 30])
       array([False, False,  True])
       >>> numpy.array([10, 20, 30]) >= c
       array([False,  True,  True])

    `Constant` instances are hashable.

    **Context manager**

    The `Constant` instance can be used as a context manager that upon
    exit executes the function defined by the `_func` attribute, with
    the `value` attribute as an argument. For example, the `Constant`
    instance ``c`` would execute ``c._func(c.value)`` upon exit.

    .. versionadded:: (cfdm) 1.8.8.0

    '''
    __slots__ = ('_func',  'value', '_type')

    def __init__(self, value, _func=None):
        '''**Initialization**

    :Parameters:

        value:
            A value for the constant.

        _func: function, optional
            A function that that is executed upon exit from a context
            manager, that takes the *value* parameter as its argument.

        '''
        self.value = value
        self._func = _func

    def __enter__(self):
        '''Enter the runtime context.

        '''
        if getattr(self, '_func', None) is None:
            raise AttributeError(
                "Can't use {!r} as a context manager because the '_func' "
                "attribute is not defined".format(self))

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        '''Exit the runtime context.

        '''
        self._func(self.value)

    def __deepcopy__(self, memo):
        '''Called by the `copy.deepcopy` function.

    x.__deepcopy__() <==> copy.deepcopy(x)

        '''
        return self.copy()

    def __float__(self):
        return float(self.value)

    def __int__(self):
        return int(self.value)

    def __eq__(self, other):
        return self.value == other

    def __lt__(self, other):
        return self.value < other

    def __abs__(self):
        return abs(self.value)

    def __neg__(self):
        return -self.value

    def __pos__(self):
        return self.value

    def __iadd__(self, other):
        self.value += other
        return self

    def __ifloordiv__(self, other):
        self.value //= other
        return self

    def __imul__(self, other):
        self.value *= other
        return self

    def __isub__(self, other):
        self.value -= other
        return self

    def __itruediv__(self, other):
        self.value /= other
        return self

    def __add__(self, other):
        try:
            return self.value + other
        except TypeError:
            return NotImplemented

    def __floordiv__(self, other):
        try:
            return self.value // other
        except TypeError:
            return NotImplemented

    def __mul__(self, other):
        try:
            return self.value * other
        except TypeError:
            return NotImplemented

    def __sub__(self, other):
        try:
            return self.value - other
        except TypeError:
            return NotImplemented

    def __truediv__(self, other):
        try:
            return self.value / other
        except TypeError:
            return NotImplemented

    def __radd__(self, other):
        return other + self.value

    def __rfloordiv__(self, other):
        return other // self.value

    def __rmul__(self, other):
        return other * self.value

    def __rsub__(self, other):
        return other - self.value

    def __rtruediv__(self, other):
        return other / self.value

    def __hash__(self):
        return hash((self.value, getattr(self, '_func', None)))

    def __repr__(self):
        '''Called by the `repr` built-in function.

        '''
        return "<{0}: {1!r}>".format(
            self.__class__.__name__, self.value
        )

    def __str__(self):
        '''Called by the `str` built-in function.

        '''
        return str(self.value)

    # ----------------------------------------------------------------
    # Methods
    # ----------------------------------------------------------------
    def copy(self):
        '''Return a deep copy.

    ``c.copy()`` is equivalent to ``copy.deepcopy(c)``.

    .. versionadded:: (cfdm) 1.8.8.0

    :Returns:

        `Constant`
            The deep copy.

        '''
        out = type(self)(value=deepcopy(self.value),
                         _func=getattr(self, '_func', None))

        if not hasattr(self, '_func'):
            del out._func

        return out
