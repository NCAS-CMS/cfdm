from __future__ import print_function
from builtins import (str, super, zip)

import logging

import numpy

from . import mixin
from . import core

from .decorators import _manage_log_level_via_verbosity


logger = logging.getLogger(__name__)


class CellMethod(mixin.Container,
                 core.CellMethod):
    '''A cell method construct of the CF data model.

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

    .. versionadded:: 1.7.0

    '''
    def __str__(self):
        '''Called by the `str` built-in function.

    x.__str__() <==> str(x)

    Returns a CF-netCDF-like string of the cell method.

    Note that if the intention is to use this string in a CF-netCDF
    cell_methods attribute then, unless they are standard names, the
    axes names will need to be modified to be netCDF dimension names.

    .. versionadded:: 1.7.0

        '''
        string = ['{0}:'.format(axis) for axis in self.get_axes(())]

        string.append(self.get_method(''))

        for portion in ('within', 'where', 'over'):
            q = self.get_qualifier(portion, None)
            if q is not None:
                string.extend((portion, q))
        # --- End: for

        interval = self.get_qualifier('interval', ())
        comment = self.get_qualifier('comment', None)

        if interval:
            x = ['(']

            y = ['interval: {0}'.format(data) for data in interval]
            x.append(' '.join(y))

            if comment is not None:
                x.append(' comment: {0}'.format(comment))

            x.append(')')

            string.append(''.join(x))

        elif comment is not None:
            string.append('({0})'.format(comment))

        return ' '.join(string)

    def dump(self, display=True, _title=None, _level=0):
        '''A full description of the cell method construct.

    Returns a description the method, all qualifiers and the axes to
    which it applies.

    .. versionadded:: 1.7.0

    :Parameters:

        display: `bool`, optional
            If False then return the description as a string. By
            default the description is printed.

    :Returns:

        `None` or `str`
            The description. If *display* is True then the description
            is printed and `None` is returned. Otherwise the
            description is returned as a string.

        '''
        indent0 = '    ' * _level

        if _title is None:
            _title = 'Cell Method: '

        return indent0 + _title + str(self)

#    def expand_intervals(self):
#        '''
#        '''
#        c = self.copy()
#
#        n_axes = len(c.get_axes(()))
#        if n_axes > 1:
#            interval = c.get_qualifier('interval', ())
#            if len(interval) == 1:
#                c.set_property('interval', interval*n_axes)
#
#        return c

#    @classmethod
#    def parse(cls, string, allow_error=False):
#        '''Parse a CF cell_methods string.
#
# :Parameters:
#
#     string: `str`
#         The CF cell_methods string to be parsed into the
#         `cf.CellMethods` object. By default the cell methods will be
#         empty.
#
#     allow_error: `bool`, optional
#
# :Returns:
#
#     `list`
#
# **Examples:**
#
# >>> c = CellMethod.parse(
# ...     'time: minimum within years time: mean over years (ENSO years)')
# >>> print c
# Cell methods    : time: minimum within years
#                   time: mean over years (ENSO years)
#
# >>> c = CellMethod()
# >>> d = c.parse(
# ...     'time: minimum within years time: mean over years (ENSO years)')
# >>> print d
# Cell methods    : time: minimum within years
#                   time: mean over years (ENSO years)
#
#        '''
#        out = []
#
#        if not string:
#            return out
#
#        # Split the cell_methods string into a list of strings ready
#        # for parsing into the result list. For example,
#        #
#        # 'lat: mean (interval: 1 hour)
#        #
#        # maps to
#        #
#        # ['lat:', 'mean', '(', 'interval:', '1', 'hour', ')']
#        cell_methods = re_sub('\((?=[^\s])' , '( ', string)
#        cell_methods = re_sub('(?<=[^\s])\)', ' )', cell_methods).split()
#
#        while cell_methods:
#            cm = cls()
#
#            axes  = []
#            while cell_methods:
#                if not cell_methods[0].endswith(':'):
#                    break
#
#                # Check that "name" ends with colon? How?
#                # ('lat: mean (area-weighted) or lat: mean
#                #  (interval: 1 degree_north comment: area-weighted)')
#
#                axis = cell_methods.pop(0)[:-1]
#
#                axes.append(axis)
#            # --- End: while
#            cm.set_axes(axes)
#
#            if not cell_methods:
#                out.append(cm)
#                break
#
#            # Method
#            cm.set_method(cell_methods.pop(0))
#
#            if not cell_methods:
#                out.append(cm)
#                break
#
#            # Climatological statistics and statistics which apply to
#            # portions of cells
#            while cell_methods[0] in ('within', 'where', 'over'):
#                attr = cell_methods.pop(0)
#                cm.set_property(attr, cell_methods.pop(0))
#                if not cell_methods:
#                    break
#            # --- End: while
#            if not cell_methods:
#                out.append(cm)
#                break
#
#            # interval and comment
#            interval = []
#            if cell_methods[0].endswith('('):
#                cell_methods.pop(0)
#
#                if not (re_search('^(interval|comment):$', cell_methods[0])):
#                    cell_methods.insert(0, 'comment:')
#
#                while not re_search('^\)$', cell_methods[0]):
#                    term = cell_methods.pop(0)[:-1]
#
#                    if term == 'interval':
#                        interval = cell_methods.pop(0)
#                        if cell_methods[0] != ')':
#                            units = cell_methods.pop(0)
#                        else:
#                            units = None
#
#                        try:
#                            parsed_interval = ast_literal_eval(interval)
#                        except:
#                            message = ("Cell method interval is incorrectly "
#                                       "formatted")
#                            if allow_error:
#                                cm = cls()
#                                cm.set_string(string)
#                                cm.set_error(message)
#                                return [out]
#                            else:
#                                raise ValueError("{}: {}".format(
#                                    message, string))
#                        # ---End: try
#
#                        try:
#                            interval.append(
#                                cm._Data(parsed_interval, units=units))
#                        except:
#                            message = ("Cell method interval is incorrectly "
#                                       formatted")
#                            if allow_error:
#                                cm = cls()
#                                cm.set_string(string)
#                                cm.set_error(message)
#                                return [cm]
#                            else:
#                                raise ValueError(
#                                    "{}: {}".format(message, string))
#                        # ---End: try
#
#                        continue
#                    # --- End: if
#
#                    if term == 'comment':
#                        comment = []
#                        while cell_methods:
#                            if cell_methods[0].endswith(')'):
#                                break
#                            if cell_methods[0].endswith(':'):
#                                break
#                            comment.append(cell_methods.pop(0))
#                        # --- End: while
#                        cm.set_property('comment', ' '.join(comment))
#                    # --- End: if
#
#                # --- End: while
#
#                if cell_methods[0].endswith(')'):
#                    cell_methods.pop(0)
#            # --- End: if
#
#            n_intervals = len(interval)
#            if n_intervals > 1 and n_intervals != len(axes):
#                message = "Cell method interval is incorrectly formatted"
#                if allow_error:
#                    cm = cls()
#                    cm.set_string(string)
#                    cm.set_error(message)
#                    return [out]
#                else:
#                    raise ValueError("{}: {}".format(message, string))
#            # ---End: if
#
#            if interval:
#                cm.set_property('interval', tuple(interval))
#
#            out.append(cm)
#        # --- End: while
#
#        return out

    @_manage_log_level_via_verbosity
    def equals(self, other, rtol=None, atol=None, verbose=None,
               ignore_qualifiers=(), ignore_type=False):
        '''Whether two cell method constructs are the same.

    Equality is strict by default. This means that:

    * the descriptive qualifiers must be the same (see the
      *ignore_qualifiers* parameter).

    The axes of the cell method constructs are *not* considered,
    because they may only be correctly interpreted by the field
    constructs that contain the cell method constructs in
    question. They are, however, taken into account when two fields
    constructs are tested for equality.

    Two real numbers ``x`` and ``y`` are considered equal if
    ``|x-y|<=atol+rtol|y|``, where ``atol`` (the tolerance on absolute
    differences) and ``rtol`` (the tolerance on relative differences)
    are positive, typically very small numbers. The data type of the
    numbers is not taken into consideration. See the *atol* and *rtol*
    parameters.

    Any type of object may be tested but, in general, equality is only
    possible with another cell method construct, or a subclass of
    one. See the *ignore_type* parameter.

    NetCDF elements, such as netCDF variable and dimension names, do
    not constitute part of the CF data model and so are not checked.

    .. versionadded:: 1.7.0

    :Parameters:

        other:
            The object to compare for equality.

        atol: float, optional
            The tolerance on absolute differences between real
            numbers. The default value is set by the `cfdm.ATOL`
            function.

        rtol: float, optional
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

        ignore_qualifiers: sequence of `str`, optional
            The names of qualifiers to omit from the comparison.

        ignore_type: `bool`, optional
            Any type of object may be tested but, in general, equality
            is only possible with another cell method construct, or a
            subclass of one. If *ignore_type* is True then
            ``CellMethod(source=other)`` is tested, rather than the
            ``other`` defined by the *other* parameter.

    :Returns:

        `bool`
            Whether the two cell method constructs are equal.

    **Examples:**

    >>> c.equals(c)
    True
    >>> c.equals(c.copy())
    True
    >>> c.equals('not a cell method')
    False

        '''
        pp = super()._equals_preprocess(other, verbose=verbose,
                                        ignore_type=ignore_type)
        if pp is True or pp is False:
            return pp

        other = pp

        # ------------------------------------------------------------
        # Check the methods
        # ------------------------------------------------------------
        if self.get_method(None) != other.get_method(None):
            logger.info(
                "{0}: Different methods: {1!r} != {2!r}".format(
                    cm0.__class__.__name__, self.get_method(None),
                    other.get_method(None)
                )
            )
            return False

        # ------------------------------------------------------------
        # Check the qualifiers
        # ------------------------------------------------------------
        self_qualifiers = self.qualifiers()
        other_qualifiers = other.qualifiers()

#        if ignore_qualifiers:
        for prop in tuple(ignore_qualifiers) + ('interval',):
            self_qualifiers.pop(prop, None)
            other_qualifiers.pop(prop, None)

        if set(self_qualifiers) != set(other_qualifiers):
            for q in set(self_qualifiers).symmetric_difference(
                    other_qualifiers):
                logger.info(
                    "{0}: Non-common qualifier: {1!r}".format(
                        self.__class__.__name__, q)
                )
            return False

        for qualifier, x in self_qualifiers.items():
            y = other_qualifiers[qualifier]

            if not self._equals(x, y, rtol=rtol, atol=atol,
                                ignore_data_type=True,
                                verbose=verbose):
                logger.info(
                    "{0}: Different {1} qualifiers: {2!r}, {3!r}".format(
                        self.__class__.__name__, prop, x, y)
                )
                return False
        # --- End: for

        if 'interval' in ignore_qualifiers:
            return True

        intervals0 = self.get_qualifier('interval', ())
        intervals1 = other.get_qualifier('interval', ())
        if intervals0:
            if not intervals1:
                logger.info(
                    "{0}: Different interval qualifiers: "
                    "{1!r} != {2!r}".format(
                        self.__class__.__name__, intervals0, intervals1)
                )
                return False
            # --- End: if

            if len(intervals0) != len(intervals1):
                logger.info(
                    "{0}: Different numbers of interval qualifiers: "
                    "{1!r} != {2!r}".format(
                        self.__class__.__name__, intervals0, intervals1)
                )
                return False
            # --- End: if

            for data0, data1 in zip(intervals0, intervals1):
                if not self._equals(data0, data1,
                                    rtol=rtol, atol=atol,
                                    verbose=verbose,
                                    ignore_data_type=True,
                                    ignore_fill_value=True):
                    logger.info(
                        "{0}: Different interval qualifiers: "
                        "{1!r} != {2!r}".format(
                            self.__class__.__name__,
                            intervals0, intervals1
                        )
                    )
                    return False

        elif intervals1:
            logger.info(
                "{}: Different intervals: {!r} != {!r}".format(
                    self.__class__.__name__, intervals0, intervals1)
            )
            return False
        # --- End: if

        # ------------------------------------------------------------
        # Do NOT check the axes
        # ------------------------------------------------------------

        return True

#    @_manage_log_level_via_verbosity
#    def equivalent(self, other, rtol=None, atol=None, verbose=None):
#        '''True if two cell methods are equivalent, False otherwise.
#
# The `axes` and `interval` attributes are ignored in the comparison.
#
# :Parameters:
#
#     other :
#         The object to compare for equality.
#
#     atol : float, optional
#         The absolute tolerance for all numerical comparisons, By
#         default the value returned by the `ATOL` function is used.
#
#     rtol : float, optional
#         The relative tolerance for all numerical comparisons, By
#         default the value returned by the `RTOL` function is used.
#
# :Returns:
#
#     out : bool
#         Whether or not the two instances are equivalent.
#
# **Examples:**
#
#        '''
#        if self is other:
#            return True
#
#        # Check that each instance is the same type
#        if self.__class__ != other.__class__:
#            logger.info("{0}: Different types: {0} != {1}".format(
#                self.__class__.__name__, other.__class__.__name__))
#            return False
#        # --- End: if
#
#        axes0 = self.axes
#        axes1 = other.axes
#
#        if len(axes0) != len(axes1) or set(axes0) != set(axes1):
#            logger.info("{}: Nonequivalent axes: {!r}, {!r}".format(
#                self.__class__.__name__, axes0, axes1))
#            return False
#        # --- End: if
#
#        argsort = [axes1.index(axis0) for axis0 in axes0]
#        other1 = other.sorted(argsort=argsort)
#        self1 = self
#
#        if not self1.equals(
#                other1, rtol=rtol, atol=atol, ignore=('interval',)):
#            logger.info("{0}: Nonequivalent: {1!r}, {2!r}".format(
#                self.__class__.__name__, self, other))
#            return False
#        # --- End: if
#
#        self_interval  = self1.get_property('interval', ())
#        other_interval = other1.get_property('interval', ())
#
#        if len(self_interval) != len(other_interval):
#            self1 = self1.expand_intervals(copy=False)
#            other1.expand_intervals(copy=False)
#
#            self_interval  = self1.get_property('interval', ())
#            other_interval = other1.get_property('interval', ())
#
#            if len(self_interval) != len(other_interval):
#                logger.info(
#                    "{0}: Different numbers of intervals: "
#                    "{1!r} != {2!r}".format(
#                        self.__class__.__name__, self_interval,
#                        other_interval
#                    )
#                )
#                return False
#        # --- End: if
#
#        # intervals0 = self1.interval
#        if self_interval:
#            for data0, data1 in zip(self_interval, other_interval):
#                if not data0.allclose(data1, rtol=rtol, atol=atol):
#                    logger.info(
#                        "{0}: Different interval data: {1!r} != {2!r}".format(
#                            self.__class__.__name__, self_interval,
#                            other_interval
#                        )
#                    )
#                    return False
#        # --- End: if
#
#        # Still here? Then they are equivalent
#        return True

    def identity(self, default=''):
        '''Return the canonical identity for the cell method construct.

    By default the identity is the first found of the following:

    1. The method, preceeded by 'method:'
    2. The value of the *default* parameter.

    .. versionadded:: 1.7.0

    .. seealso:: `identities`

    :Parameters:

        default: optional
            If no identity can be found then return the value of the
            default parameter.

    :Returns:

            The identity.

    **Examples:**

    >>> c.get_method()
    'minimum;
    >>> c.identity()
    'method:minimum'
    >>> c.identity(default='no identity')
    'method:minimum'
    >>> c.del_method()
    'minimum'
    >>> c.identity()
    ''
    >>> c.identity(default='no identity')
    'no identity'

        '''
        n = self.get_method(None)
        if n is not None:
            return 'method:{0}'.format(n)

        return default

    def identities(self):
        '''Return all possible identities.

    The identities comprise:

    * The method, preceeded by 'method:'.

    .. versionadded:: 1.7.0

    .. seealso:: `identity`

    :Returns:

        `list`
            The identities.

    **Examples:**

    >>> c.get_method()
    'minimum'
    >>> c.identities()
    ['method:minimum']
    >>> c.del_method()
    'minimum'
    >>> c.identities()
    []

        '''
        out = []

        n = self.get_method(None)
        if n is not None:
            out.append('method:{0}'.format(n))

        return out

    def sorted(self, indices=None):
        '''Return a new cell method construct with sorted axes.

    The axes are sorted by domain axis construct identifier or
    standard name, and any intervals are sorted accordingly.

    .. versionadded:: 1.7.0

    :Parameters:

        indices: ordered sequence of `int`, optional
            Sort the axes with the given indices. By default the axes
            are sorted by domain axis construct identifier or standard
            name.

    :Returns:

        `CellMethod`
            A new cell method construct with sorted axes.

    **Examples:**

    >>> cm = cfdm.CellMethod(axes=['domainaxis1', 'domainaxis0'],
    ...                      method='mean',
    ...                      qualifiers={'interval': [1, 2]})
    >>> cm
    <CellMethod: domainaxis1: domainaxis0: mean (interval: 1 interval: 2)>
    >>> cm.sorted()
    <CellMethod: domainaxis0: domainaxis1: mean (interval: 2 interval: 1)>

    >>> cm = cfdm.CellMethod(axes=['domainaxis0', 'area'],
    ...                      method='mean',
    ...                      qualifiers={'interval': [1, 2]})
    >>> cm
    <CellMethod: domainaxis0: area: mean (interval: 1 interval: 2)>
    >>> cm.sorted()
    <CellMethod: area: domainaxis0: mean (interval: 2 interval: 1)>

        '''
        new = self.copy()

        axes = new.get_axes(())
        if len(axes) == 1:
            return new

        if indices is None:
            indices = numpy.argsort(axes)
        elif len(indices) != len(axes):
            raise ValueError(
                "Can't sort cell method axes. The given indices ({}) "
                "do not correspond to the number of axes ({})".format(
                    indices, axes))

        axes2 = []
        for i in indices:
            axes2.append(axes[i])

        new.set_axes(tuple(axes2))

        intervals = new.get_qualifier('interval', ())
        if len(intervals) <= 1:
            return new

        intervals2 = []
        for i in indices:
            intervals2.append(intervals[i])

        new.set_qualifier('interval', tuple(intervals2))

        return new

# --- End: class
