import abc

from ast import literal_eval as ast_literal_eval
from re  import sub          as re_sub
from re  import search       as re_search

import mixin

from .functions import equals

from .data.data import Data

from ..structure import CellMethod as structure_CellMethod

# ====================================================================
#
# Cell method object
#
# ====================================================================

class CellMethod(structure_CellMethod, mixin.Properties):
    '''A cell method construct od the CF data model.

Cell method constructs describe how the field construct's cell values
represent the variation of the physical quantity within its cells,
i.e. the structure of the data at a higher resolution. A single cell
method construct consists of a set of axes, a property which describes
how a value of the field construct's data array describes the
variation of the quantity within a cell over those axes (e.g. a value
might represent the cell area average), and properties serving to
indicate more precisely how the method was applied (e.g. recording the
spacing of the original data, or the fact the method was applied only
over El Nino years).

    '''
    __metaclass__ = abc.ABCMeta
    
    def __new__(cls, *args, **kwargs):
        '''
        '''
        obj = object.__new__(cls, *args, **kwargs)
        obj._Data = Data
        return obj
    #--- End: def
    
    def __init__(self, axes=None, method=None, where=None,
                 within=None, over=None, interval=None, comment=None,
                 source=None, copy=True):
        '''
        '''
        properties = {'where'   : where,
                      'within'  : within,
                      'over'    : over,
                      'interval': interval,
                      'comment' : comment}

        for key, value in properties.items():
            if value is None:
                del properties[key]
        #--- End: def
        
        super(CellMethod, self).__init__(axes=axes, method=method,
                                         properties=properties,
                                         source=source, copy=copy)
    #--- End: def

    def __str__(self):
        '''x.__str__() <==> str(x)

Return a CF-netCDF-like string of the cell method.

Note that if the intention use this string in a CF-netCDF cell_methods
attribute then the cell method's `!name` attribute may need to be
modified, where appropriate, to reflect netCDF variable names.

        '''
        string = [super(CellMethod, self).__str__()]

        for portion in ('within', 'where', 'over'):
            p = self.get_property(portion, None)
            if p is not None:
                string.extend((portion, p))
        #--- End: for

        intervals = self.get_property('interval', ())
        comment   = self.get_property('comment', None)
        if intervals:
            x = ['(']

            y = ['interval: {0}'.format(data) for data in intervals]
            x.append(' '.join(y))

            if comment is not None:
                x.append(' comment: {0}'.format(comment))

            x.append(')')

            string.append(''.join(x))

        elif comment is not None:
            string.append('({0})'.format(comment))

        return ' '.join(string)
    #--- End: def

    def change_axes(self, axis_map, copy=True):
        '''
:Parameters:

    axis_map: `dict`

    copy: `bool`, optional

:Returns:

    out: `CellMethod`

        '''
        if copy:
            c = self.copy()
        else:
            c = self

        if not axis_map:
            return c

        c.set_axes(tuple([axis_map.get(axis, axis)
                          for axis in self.get_axes(())]))

        return c
    #--- End: def

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

#    field: `cf.Field`, optional

:Returns:

    out: `str` or `None`
        A string containing the description.

:Examples:
         
        '''
        indent0 = '    ' * _level

        if _title is None:
            _title = 'Cell Method: '

        return indent0 + _title + str(self)
    #--- End: def

    def expand_intervals(self, copy=True):
        if copy:
            c = self.copy()
        else:
            c = self

        n_axes = len(c.get_axes(()))
        interval = c.get_property('interval', ())
        if n_axes > 1 and len(interval) == 1:
            c.set_property('interval', interval * n_axes)

        return c
    #--- End: def

    def del_error(self):
        '''
        '''
        return self._del_extra('error')
    
    def get_error(self, *default):
        '''
        '''
        return self._get_extra('error', *default)
    
    def set_error(self, value):
        '''
        '''
        self._set_extra('error', value)
    
    def del_string(self):
        '''
        '''
        return self._del_extra('string')
    
    def get_string(self, *default):
        '''
        '''
        return self._get_extra('string', *default)
    
    def set_string(self, value):
        '''
        '''
        self._set_extra('string', value)
    
    def sorted(self, argsort=None):
        '''
        '''
        new = self.copy()
        
        axes = new.get_axes(())
        if len(axes) == 1:
            return new

        if argsort is None:
            argsort = numpy_argsort(axes)
        elif len(argsort) != len(axes):
            raise ValueError(".sjdn ;siljdf vlkjndf jk")

        axes2 = []
        for i in argsort:
            axes2.append(axes[i])

        new.set_axes(tuple(axes2))

        intervals = new.get_property('interval', ())
        if len(intervals) <= 1:
            return new

        intervals2 = []
        for i in argsort:
            intervals2.append(intervals[i])

        new.set_property('interval', tuple(intervals2))

        return new
    #--- End: def

    @classmethod
    def parse(cls, string=None, allow_error=False): #, field=None):
        '''Parse a CF cell_methods string into this `cf.CellMethods` instance
in place.

:Parameters:

    string: `str`, optional
        The CF cell_methods string to be parsed into the
        `cf.CellMethods` object. By default the cell methods will be
        empty.

:Returns:

    out: `list`

:Examples:

>>> c = cf.CellMethods()
>>> c = c._parse('time: minimum within years time: mean over years (ENSO years)')    
>>> print c
Cell methods    : time: minimum within years
                  time: mean over years (ENSO years)

        '''
        if not string:
            return []

        out = []

        # Split the cell_methods string into a list of strings ready
        # for parsing into the result list. E.g.
        #   'lat: mean (interval: 1 hour)'
        # maps to 
        #   ['lat:', 'mean', '(', 'interval:', '1', 'hour', ')']
        cell_methods = re_sub('\((?=[^\s])' , '( ', string)
        cell_methods = re_sub('(?<=[^\s])\)', ' )', cell_methods).split()

        while cell_methods:
            cm = cls()

            axes  = []
            while cell_methods:
                if not cell_methods[0].endswith(':'):
                    break

                # Check that "name" ebds with colon? How? ('lat: mean (area-weighted) or lat: mean (interval: 1 degree_north comment: area-weighted)')

#                names.append(cell_methods.pop(0)[:-1])            
#                axes.append(None)

                axis = cell_methods.pop(0)[:-1]
#                if field is not None:
#                    axis = field.axis(axis, key=True)

                axes.append(axis)
            #--- End: while
            cm.set_axes(axes)

            if not cell_methods:
                out.append(cm)
                break

            # Method
            cm.set_method(cell_methods.pop(0))

            if not cell_methods:
                out.append(cm)
                break

            # Climatological statistics and statistics which apply to
            # portions of cells
            while cell_methods[0] in ('within', 'where', 'over'):
                attr = cell_methods.pop(0)
                cm.set_property(attr, cell_methods.pop(0))
#                setattr(cm, attr, cell_methods.pop(0))
                if not cell_methods:
                    break
            #--- End: while
            if not cell_methods: 
                out.append(cm)
                break

            # interval and comment
            intervals = []
            if cell_methods[0].endswith('('):
                cell_methods.pop(0)

                if not (re_search('^(interval|comment):$', cell_methods[0])):
                    cell_methods.insert(0, 'comment:')
                           
                while not re_search('^\)$', cell_methods[0]):
                    term = cell_methods.pop(0)[:-1]

                    if term == 'interval':
                        interval = cell_methods.pop(0)
                        if cell_methods[0] != ')':
                            units = cell_methods.pop(0)
                        else:
                            units = None

                        try:
                            parsed_interval = ast_literal_eval(interval)
                        except:
                            message = "Unparseable cell method interval"
#                            interval+' '+units if units is not None else interval)
                            if allow_error:
                                cm = cls()
                                cm.set_string(string)
                                cm.set_error(message)
                                return [out]
                            else:
                                raise ValueError("{}: {}".format(message, string))
                        #---End: try

                        try:
                            intervals.append(cm._Data(parsed_interval, units=units))
                        except:
                            message = "Unparseable cell method interval"
                            if allow_error:
                                cm = cls()
                                cm.set_string(string)
                                cm.set_error(message)
                                return [cm]
                            else:
                                raise ValueError("{}: {}".format(message, string))
                        #---End: try

                        continue
                    #--- End: if

                    if term == 'comment':
                        comment = []
                        while cell_methods:
                            if cell_methods[0].endswith(')'):
                                break
                            if cell_methods[0].endswith(':'):
                                break
                            comment.append(cell_methods.pop(0))
                        #--- End: while
                        cm.set_property('comment', ' '.join(comment))
                    #--- End: if

                #--- End: while 

                if cell_methods[0].endswith(')'):
                    cell_methods.pop(0)
            #--- End: if

            n_intervals = len(intervals)          
            if n_intervals > 1 and n_intervals != len(axes):
                message = "Unparseable cell method intervals"
                if allow_error:
                    cm = cls()
                    cm.set_string(string)
                    cm.set_error(message)
                    return [out]
                else:
                    raise ValueError("{}: {}".format(message, string))
            #---End: if

            if intervals:
                cm.set_property('interval', tuple(intervals))

            out.append(cm)
        #--- End: while

        return out
    #--- End: def

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

:Examples:

'''
        if rtol is None:
            rtol = RTOL()
        if atol is None:
            atol = ATOL()

        if not super(CellMethod, self).equals(
                other, rtol=rtol, atol=atol,
                traceback=traceback,
                ignore_data_type=ignore_data_type,
                ignore_fill_value=ignore_fill_value,
                ignore_properties=ignore_properties + ('interval',),
                ignore_construct_type=ignore_construct_type):
	    return False
        
        if 'interval' in ignore_properties:
            return True

        self_interval  = self.get_property('interval', ())
        other_interval = other.get_property('interval', ())
        if self_interval:
            if not other_interval:
                if traceback:
                    print(
"{0}: Different intervals: {1!r} != {2!r}".format(
    self.__class__.__name__, self_interval, other_interval))
                return False
            #--- End: if
            
            if len(self_interval) != len(other_interval):
                if traceback:
                    print(
"{0}: Different intervals: {1!r} != {2!r}".format(
    self.__class__.__name__, self_interval, other_interval))
                return False
            #--- End: if
            
            for data0, data1 in zip(self_interval, other_interval):
                if not data0.equals(data1, rtol=rtol, atol=atol,
                                    ignore_data_type=ignore_data_type,
                                    ignore_fill_value=ignore_fill_value,
                                    traceback=traceback):
                    if traceback:
                        print(
"{0}: Different intervals: {1!r} != {2!r}".format(
    self.__class__.__name__, self_interval, other_interval))
                    return False
            #--- End: for

        elif other_interval:
            if traceback:
                print("{}: Different intervals: {!r} != {!r}".format(
                    self.__class__.__name__, self_interval, other_interval))
            return False
        #--- End: if

        return True
    #--- End: def

    def equivalent(self, other, rtol=None, atol=None, traceback=False):
        '''True if two cell methods are equivalent, False otherwise.

The `axes` and `interval` attributes are ignored in the comparison.

:Parameters:

    other : 
        The object to compare for equality.

    atol : float, optional
        The absolute tolerance for all numerical comparisons, By
        default the value returned by the `ATOL` function is used.

    rtol : float, optional
        The relative tolerance for all numerical comparisons, By
        default the value returned by the `RTOL` function is used.

:Returns: 

    out : bool
        Whether or not the two instances are equivalent.

:Examples:

        '''
        if self is other:
            return True

        # Check that each instance is the same type
        if self.__class__ != other.__class__:
            if traceback:
                print("{0}: Different types: {0} != {1}".format(
                    self.__class__.__name__, other.__class__.__name__))
            return False
        #--- End: if

        axes0 = self.axes
        axes1 = other.axes
            
        if len(axes0) != len(axes1) or set(axes0) != set(axes1):
            if traceback:
                print("{}: Nonequivalent axes: {!r}, {!r}".format(
                    self.__class__.__name__, axes0, axes1))
            return False
        #--- End: if

#        other1 = other.copy()
        argsort = [axes1.index(axis0) for axis0 in axes0]
        other1 = other.sorted(argsort=argsort)
        self1 = self

        if not self1.equals(other1, rtol=rtol, atol=atol, ignore=('interval',)):
            if traceback:
                print("{0}: Nonequivalent: {1!r}, {2!r}".format(
                    self.__class__.__name__, self, other))
            return False
        #--- End: if

        self_interval  = self1.get_property('interval', ())
        other_interval = other1.get_property('interval', ())
        
        if len(self_interval) != len(other_interval):
            self1 = self1.expand_intervals(copy=False)
            other1.expand_intervals(copy=False)

            self_interval  = self1.get_property('interval', ())
            other_interval = other1.get_property('interval', ())        

            if len(self_interval) != len(other_interval):
                if traceback:
                    print(
"{0}: Different numbers of intervals: {1!r} != {2!r}".format(
    self.__class__.__name__, self_interval, other_interval))
                return False
        #--- End: if

#        intervals0 = self1.interval
        if self_interval:
            for data0, data1 in zip(self_interval, other_interval):
                if not data0.allclose(data1, rtol=rtol, atol=atol):
                    if traceback:
                        print(
"{0}: Different interval data: {1!r} != {2!r}".format(
    self.__class__.__name__, self_interval, other_interval))
                    return False
        #--- End: if

        # Still here? Then they are equivalent
        return True
    #--- End: def

    def remove_axes(self, axes):
        '''

:Parameters:

    axes: sequence of `str`

:Returns:

    None

        '''
        if len(self._interval) <= 1:
            self._axes = tuple([axis for axis in self._axes if axis not in axes])
            if not len(self._axes):
                self._interval = ()
            return
        
        # Still here?
        _axes = []
        _intervals = []

        for axis, interval in zip(self._axes, self._interval):
            if axis not in axes:
                _axes.append(axis)
                _intervals.append(interval)

        self._axes     = tuple(_axes)
        self._interval = tuple(_intervals)
    #--- End: def

#    def write(self, axis_map={}):
#        '''
#
#Return a string of the cell method.
#
#
#'''
#        string = ['{0}:'.format(axis)
#                  for axis in self.change_axes(axis_map).axes]
#
#        method = self._method
#        if method is None:
#            return ''
#
#        string.append(method)
#
#        for portion in ('within', 'where', 'over'):
#            p = getattr(self, portion, None)
#            if p is not None:
#                string.extend((portion, p))
#        #--- End: for
#
#        intervals = self.interval
#        if intervals:
#            x = ['(']
#
#            y = ['interval: {0}'.format(data) for data in intervals]
#            x.append(' '.join(y))
#
#            if self.comment is not None:
#                x.append(' comment: {0}'.format(self.comment))
#
#            x.append(')')
#
#            string.append(''.join(x))
#
#        elif self.comment is not None:
#            string.append('({0})'.format(self.comment))
#
#        return ' '.join(string)
#    #--- End: def
#
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
