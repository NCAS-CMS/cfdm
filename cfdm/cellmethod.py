from __future__ import print_function
from builtins import (str, super, zip)

import numpy

from . import mixin
from . import core


class CellMethod(mixin.Properties,
                 core.CellMethod):
    '''A cell method construct of the CF data model.

One or more cell method constructs describe how the cell values of the
field construct represent the variation of the physical quantity
within its cells, i.e. the structure of the data at a higher
resolution.

A single cell method construct consists of a set of axes, a "method"
property which describes how a value of the field construct's data
array describes the variation of the quantity within a cell over those
axes (e.g. a value might represent the cell area average), and
properties serving to indicate more precisely how the method was
applied (e.g. recording the spacing of the original data, or the fact
that the method was applied only over El Nino years).
    
    '''

    def dump(self, display=True, _title=None, _level=0):
        '''
        
Return a string containing a full description of the instance.

If a cell methods 'name' is followed by a '*' then that cell method is
relevant to the data in a way which may not be precisely defined its
corresponding dimension or dimensions.

:Parameters:

    display: `bool`, optional
        If False then return the description as a string. By default
        the description is printed, i.e. ``c.dump()`` is equivalent to
        ``print c.dump(display=False)``.

:Returns:

    out: `str` or `None`
        A string containing the description.

**Examples**
         
        '''
        indent0 = '    ' * _level

        if _title is None:
            _title = 'Cell Method: '

        return indent0 + _title + str(self)
    #--- End: def

#    def expand_intervals(self):
#        '''
#        '''
#        c = self.copy()
#
#        n_axes = len(c.get_axes(()))
#        if n_axes > 1:
#            intervals = c.get_property('intervals', ())            
#            if len(interval) == 1:
#                c.set_property('intervals', interval*n_axes)
#
#        return c
#    #--- End: def

#    @classmethod
#    def parse(cls, string, allow_error=False):
#        '''Parse a CF cell_methods string.
#
#:Examples 1:
#
#>>> c = CellMethod('t: mean')
#
#:Parameters:
#
#    string: `str`
#        The CF cell_methods string to be parsed into the
#        `cf.CellMethods` object. By default the cell methods will be
#        empty.
#
#    allow_error: `bool`, optional
#
#:Returns:
#
#    out: `list`
#
#**Examples**
#
#>>> c = CellMethod.parse('time: minimum within years time: mean over years (ENSO years)')
#>>> print c
#Cell methods    : time: minimum within years
#                  time: mean over years (ENSO years)
#
#>>> c = CellMethod()
#>>> d = c.parse('time: minimum within years time: mean over years (ENSO years)')
#>>> print d
#Cell methods    : time: minimum within years
#                  time: mean over years (ENSO years)
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
#                # Check that "name" ebds with colon? How? ('lat: mean (area-weighted) or lat: mean (interval: 1 degree_north comment: area-weighted)')
#
#                axis = cell_methods.pop(0)[:-1]
#
#                axes.append(axis)
#            #--- End: while
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
#            #--- End: while
#            if not cell_methods: 
#                out.append(cm)
#                break
#
#            # interval and comment
#            intervals = []
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
#                            message = "Cell method interval is incorrectly formatted"
#                            if allow_error:
#                                cm = cls()
#                                cm.set_string(string)
#                                cm.set_error(message)
#                                return [out]
#                            else:
#                                raise ValueError("{}: {}".format(message, string))
#                        #---End: try
#
#                        try:
#                            intervals.append(cm._Data(parsed_interval, units=units))
#                        except:
#                            message = "Cell method interval is incorrectly formatted"
#                            if allow_error:
#                                cm = cls()
#                                cm.set_string(string)
#                                cm.set_error(message)
#                                return [cm]
#                            else:
#                                raise ValueError("{}: {}".format(message, string))
#                        #---End: try
#
#                        continue
#                    #--- End: if
#
#                    if term == 'comment':
#                        comment = []
#                        while cell_methods:
#                            if cell_methods[0].endswith(')'):
#                                break
#                            if cell_methods[0].endswith(':'):
#                                break
#                            comment.append(cell_methods.pop(0))
#                        #--- End: while
#                        cm.set_property('comment', ' '.join(comment))
#                    #--- End: if
#
#                #--- End: while 
#
#                if cell_methods[0].endswith(')'):
#                    cell_methods.pop(0)
#            #--- End: if
#
#            n_intervals = len(intervals)          
#            if n_intervals > 1 and n_intervals != len(axes):
#                message = "Cell method interval is incorrectly formatted"
#                if allow_error:
#                    cm = cls()
#                    cm.set_string(string)
#                    cm.set_error(message)
#                    return [out]
#                else:
#                    raise ValueError("{}: {}".format(message, string))
#            #---End: if
#
#            if intervals:
#                cm.set_property('intervals', tuple(intervals))
#
#            out.append(cm)
#        #--- End: while
#
#        return out
#    #--- End: def

    def equals(self, other, rtol=None, atol=None, traceback=False,
               ignore_data_type=False, ignore_fill_value=False,
               ignore_properties=(), ignore_construct_type=False):
        '''

True if two cell methods are equal, False otherwise.

The `!axes` attribute is ignored in the comparison.

:Parameters:

    other : 
        The object to compare for equality.

    atol : float, optional
        The absolute tolerance for all numerical comparisons, By
        default the value returned by the `ATOL` function is used.

    rtol : float, optional
        The relative tolerance for all numerical comparisons, By
        default the value returned by the `RTOL` function is used.

    ignore_fill_value : bool, optional
        If True then data arrays with different fill values are
        considered equal. By default they are considered unequal.

    traceback : bool, optional
        If True then print a traceback highlighting where the two
        instances differ.

:Returns: 

    out : bool
        Whether or not the two instances are equal.

**Examples**

'''
        if not super().equals(
                other, rtol=rtol, atol=atol,
                traceback=traceback,
                ignore_data_type=ignore_data_type,
                ignore_fill_value=ignore_fill_value,
                ignore_properties=ignore_properties + ('intervals',),
                ignore_construct_type=ignore_construct_type):
            return False
        
#        axes0 = self.get_axes(())
#        axes1 = other.get_axes(())
#        if len(axes0) != len(axes1):
#            if traceback:
#                print(
#                    "{0}: Different axes: {1!r} != {2!r}".format(
#                        self.__class__.__name__, axes0, axes1))
#            return False
#        #--- End: if
        
        if 'intervals' in ignore_properties:
            return True

        intervals0 = self.get_property('intervals', ())
        intervals1 = other.get_property('intervals', ())
        if intervals0:
            if not intervals1:
                if traceback:
                    print(
                        "{0}: Different intervals: {1!r} != {2!r}".format(
                            self.__class__.__name__, intervals0, intervals1))
                return False
            #--- End: if
            
            if len(intervals0) != len(intervals1):
#                intervals0 = self.expand_intervals().get_property('intervals', ())
#                intervals1 = other.expand_intervals().get_property('intervals', ())        
#                if len(intervals0) != len(intervals1):
                if traceback:
                    print(
                        "{0}: Different numbers of intervals: {1!r} != {2!r}".format(
                            self.__class__.__name__, intervals0, intervals1))
                    return False
            #--- End: if

            for data0, data1 in zip(intervals0, intervals1):
                if not self._equals(data0, data1,
                                    rtol=rtol, atol=atol,
                                    ignore_data_type=ignore_data_type,
                                    ignore_fill_value=ignore_fill_value,
                                    traceback=traceback):
                    if traceback:
                        print(
                            "{0}: Different intervals: {1!r} != {2!r}".format(
                                self.__class__.__name__, intervals0, intervals1))
                    return False

        elif intervals1:
            if traceback:
                print("{}: Different intervals: {!r} != {!r}".format(
                    self.__class__.__name__, intervals0, intervals1))
            return False
        #--- End: if

        return True
    #--- End: def

#    def equivalent(self, other, rtol=None, atol=None, traceback=False):
#        '''True if two cell methods are equivalent, False otherwise.
#
#The `axes` and `interval` attributes are ignored in the comparison.
#
#:Parameters:
#
#    other : 
#        The object to compare for equality.
#
#    atol : float, optional
#        The absolute tolerance for all numerical comparisons, By
#        default the value returned by the `ATOL` function is used.
#
#    rtol : float, optional
#        The relative tolerance for all numerical comparisons, By
#        default the value returned by the `RTOL` function is used.
#
#:Returns: 
#
#    out : bool
#        Whether or not the two instances are equivalent.
#
#**Examples**
#
#        '''
#        if self is other:
#            return True
#
#        # Check that each instance is the same type
#        if self.__class__ != other.__class__:
#            if traceback:
#                print("{0}: Different types: {0} != {1}".format(
#                    self.__class__.__name__, other.__class__.__name__))
#            return False
#        #--- End: if
#
#        axes0 = self.axes
#        axes1 = other.axes
#            
#        if len(axes0) != len(axes1) or set(axes0) != set(axes1):
#            if traceback:
#                print("{}: Nonequivalent axes: {!r}, {!r}".format(
#                    self.__class__.__name__, axes0, axes1))
#            return False
#        #--- End: if
#
#        argsort = [axes1.index(axis0) for axis0 in axes0]
#        other1 = other.sorted(argsort=argsort)
#        self1 = self
#
#        if not self1.equals(other1, rtol=rtol, atol=atol, ignore=('intervals',)):
#            if traceback:
#                print("{0}: Nonequivalent: {1!r}, {2!r}".format(
#                    self.__class__.__name__, self, other))
#            return False
#        #--- End: if
#
#        self_interval  = self1.get_property('intervals', ())
#        other_interval = other1.get_property('intervals', ())
#        
#        if len(self_interval) != len(other_interval):
#            self1 = self1.expand_intervals(copy=False)
#            other1.expand_intervals(copy=False)
#
#            self_interval  = self1.get_property('intervals', ())
#            other_interval = other1.get_property('intervals', ())        
#
#            if len(self_interval) != len(other_interval):
#                if traceback:
#                    print(
#"{0}: Different numbers of intervals: {1!r} != {2!r}".format(
#    self.__class__.__name__, self_interval, other_interval))
#                return False
#        #--- End: if
#
##        intervals0 = self1.interval
#        if self_interval:
#            for data0, data1 in zip(self_interval, other_interval):
#                if not data0.allclose(data1, rtol=rtol, atol=atol):
#                    if traceback:
#                        print(
#"{0}: Different interval data: {1!r} != {2!r}".format(
#    self.__class__.__name__, self_interval, other_interval))
#                    return False
#        #--- End: if
#
#        # Still here? Then they are equivalent
#        return True
#    #--- End: def

    def name(self, default=None, ncvar=False, custom=None,
             all_names=False):
        '''Return a name for the {+variable}.

By default the name is the first found of the following:

  3. If the *ncdim* parameter is True, the netCDF variable name (as
     returned by the `nc_get_variable` method), preceeded by the
     string ``'ncvar%'``.
  
  4. The value of the *default* parameter.

.. versionadded:: 1.7

:Parameters:

    default: optional
        If no name can be found then return the value of the *default*
        parameter. By default the default is `None`.

    ncvar: `bool`, optional

:Returns:

    out:
        The name.

**Examples**


>>> n = f.{+name}()
>>> n = f.{+name}(default='NO NAME')

        '''
        out = []

        if custom is None:
            custom = ('method',)
            
        for prop in custom:
            n = self.get_property(prop, None)
            if n is not None:
                out.append('{0}:{1}'.format(prop, n))
                if not all_names:
                    break
        #--- End: if
        
        if all_names:
            if default is not None:
                out.append(default)
                
            return out
        
        if out:
            return out[-1]

        return default
    
#        if all_names:
#            n = self.get_property('method', None)
#            if n is not None:
#                return [n]
#            else:
#                return []
#            
#        return self.get_property('method', default)
    #--- End: def

    def sorted(self, indices=None):
        '''Return a cell method with sorted domain axes.

The domain axes are sorted by their internal identifiers and the
intervals, if provided, are sorted accordingly.

:Parameters:

    indices: ordered sequence of `int`, optional
        Sort the somain axes with the given indices. By default the
        domain axes are sorted by their internal identifiers.

:Returns:

    out: `CellMethod`
        A new cell method object with sorted domain axes.

**Examples**

>>> cm = CellMethod(axes=['domainaxis1', 'domainaxis0'],
...                 method='mean',
...                 properties={'intervals': [Data(1, 'km'), 
...                                           Data(2, 'km')]})
>>> cm = cfdm.CellMethod(axes=['domainaxis1', 'domainaxis0'],
...                      properties={'method': 'mean',
...                                  'intervals': [1, 2]})
... 
>>> cm
<CellMethod: domainaxis1: domainaxis0: mean (interval: 1 interval: 2)>
>>> cm.sorted()
<CellMethod: domainaxis0: domainaxis1: mean (interval: 2 interval: 1)>

        '''
        new = self.copy()
        
        axes = new.get_axes(())
        if len(axes) == 1:
            return new

        if indices is None:
            indices = numpy.argsort(axes)
        elif len(indices) != len(axes):
            raise ValueError(".sjdn ;siljdf vlkjndf jk")

        axes2 = []
        for i in indices:
            axes2.append(axes[i])

        new.set_axes(tuple(axes2))

        intervals = new.get_property('intervals', ())
        if len(intervals) <= 1:
            return new

        intervals2 = []
        for i in indices:
            intervals2.append(intervals[i])

        new.set_property('intervals', tuple(intervals2))

        return new
    #--- End: def

#    def match(self, description=None, inverse=False):
#        '''
#        '''
#        if not isinstance(description (list, tuple)):
#            description = (description,)
#
#        found_match = True
#
#        for d in description:
#            found_match = True
#            
#            if isinstance(d , basestring):
#                description = {'cell_method': d}
#                
#            c = type(self)(**d)
#
#            has_axes = False
#            if c.axes:
#                has_axes = True
#                if len(self.axes) != len(c.axes):
#                    return False
#    
#                c = c.sorted(argsort=[c.axes.index(axis) for axis in self.axes])
#                
#                if self.axes != c.axes:
#                    found_match = False
#                    continue
#            #--- End: if
#    
#            for attr in ('method', 'within', 'over', 'where', 'comment'):
#                x = getattr(c, attr)
#                if x and x != getattr(self, attr):
#                    found_match = False
#                    break
#            #--- End: for
#        
#            if not found_match:
#                continue
#    
#            if c.interval:
#                d = self.expand_intervals()
#                c.expand_intervals(copy=False)
#                    
#                intervals0 = list(self.interval)
#                intervals1 = list(c.interval)
#    
#                if len(intervals0) != len(intervals1):
#                    return False
#    
#                if has_axes:                
#                    for i0, i1 in zip(intervals0, intervals1):
#                        if i0 != i1:
#                            found_match = False
#                            break
#                else:            
#                    for i0 in intervals0:
#                        found_match = False
#                        for n, i1 in enumerate(intervals1):
#                            if i0 == i1:
#                                del intervals1[n]
#                                found_match = True
#                                break
#            #--- End: if
#
#            if not found_match:
#                continue
#        #--- End: for
#
#        return not bool(inverse)
#    #--- End: def

#--- End: class
