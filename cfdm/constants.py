import logging
import sys

from enum import Enum

from functools import total_ordering

import numpy


"""
A dictionary of useful constants.

Whilst the dictionary may be modified directly, it is safer to
retrieve and set the values with the dedicated get-and-set functions.

:Keys:

    ATOL : float
      The value of absolute tolerance for testing numerically
      tolerant equality.

    RTOL : float
      The value of relative tolerance for testing numerically
      tolerant equality.

    LOG_LEVEL : str
      The minimal level of seriousness for which log messages are shown.
      See `cfdm.log_level`.
"""
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
    '''A container for a global constant with context manager support.

    Conversion to `int`, `float` and `str` is with the usual built-in
    functions:

       >>> c = cfdm.Constant(1.9)
       >>>  int(c)
       1
       >>> float(c)
       1.9
       >>> str(c)
       '1.9'

    Augmented arithmetic assignments (``+=``, ``-=``, ``*=``, ``/=``,
    ``//=``) update `Constant` objects in-place:

       >>> c = cfdm.Constant(20)
       >>> c /= 2
       >>> c
       <Constant: 10.0>
       >>> c += c
       <Constant: 20.0>

       >>> c = cfdm.Constant('New_')
       >>> c *= 2
       <Constant: 'New_New_'>

    All other binary arithmetic operations (``+``, ``-``, ``*``,
    ``/``, ``//``) return a new scalar value, even if both operands
    are `Constant` instances:

       >>> c = cfdm.Constant(20)
       >>> c * c
       400
       >>> c * 3
       60
       >>> 2 - c
       -38

       >>> c = cfdm.Constant('New_')
       >>> c * 2
       'New_New_'

    Rich comparison operations are possible between other `Constant`
    instances as well as any scalar value:

       >>> c = cfdm.Constant(20)
       >>> d = cfdm.Constant(1)
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

    `Constant` instances are hashable.

    .. versionadded:: (cfdm) 1.8.8.0

    '''
    __slots__ = ('_func',  'value', '_type')

    def __init__(self, value, _func=None):
        '''**Initialization**

    :Parameters:

        value:
            A value for the constant.

        _func: function, optional
            A function that gets and sets the constant. Required if
            the object is to be used a context manager. This function
            takes a `Constant` instance as its unique argument and
            returns the constant as it was prior to the function being
            called.

        '''
        self.value = value
        self._func = _func

    def __enter__(self):
        if getattr(self, '_func', None) is None:
            raise AttributeError(
                "Can't use {!r} as a context manager because the '_func' "
                "attribute is not defined".format(self))

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._func(self)

    def __float__(self):
        return float(self.value)

    def __int__(self):
        return int(self.value)

    def __eq__(self, other):
        try:
            other = other.value
        except AttributeError:
            pass

        return self.value == other

    def __lt__(self, other):
        try:
            other = other.value
        except AttributeError:
            pass

        return self.value < other

    def __iadd__(self, other):
        try:
            other = other.value
        except AttributeError:
            pass

        self.value += other
        return self

    def __ifloordiv__(self, other):
        try:
            other = other.value
        except AttributeError:
            pass

        self.value //= other
        return self

    def __imul__(self, other):
        try:
            other = other.value
        except AttributeError:
            pass

        self.value *= other
        return self

    def __isub__(self, other):
        try:
            other = other.value
        except AttributeError:
            pass

        self.value -= other
        return self

    def __itruediv__(self, other):
        try:
            other = other.value
        except AttributeError:
            pass

        self.value /= other
        return self

    def __add__(self, other):
        try:
            other = other.value
        except AttributeError:
            pass

        return self.value + other

    def __floordiv__(self, other):
        try:
            other = other.value
        except AttributeError:
            pass

        return self.value // other

    def __mul__(self, other):
        try:
            other = other.value
        except AttributeError:
            pass

        return self.value * other

    def __sub__(self, other):
        try:
            other = other.value
        except AttributeError:
            pass

        return self.value - other

    def __truediv__(self, other):
        try:
            other = other.value
        except AttributeError:
            pass

        return self.value / other

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
        return hash(self.value)

    def __repr__(self):
        return "<{0}: {1!r}>".format(
            self.__class__.__name__, self.value
        )

    def __str__(self):
        return str(self.value)
