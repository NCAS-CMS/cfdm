from collections import abc
from ast import literal_eval as ast_literal_eval
from re import sub    as re_sub
from re import search as re_search

from .functions import equals

from .data.data import Data

import ..structure

# ====================================================================
#
# CellMethod object
#
# ====================================================================

class CellMethod(structure.CellMethod):
    '''**Attributes**

===========  =========================================================
Attribute    Description
===========  =========================================================
`!names`      
`!interval`  
`!method`     
`!over`       
`!where`      
`!within`     
`!comment`    
`!axes`       
===========  =========================================================

    '''
    __metaclass__ = abc.ABCMeta
    
    def __new__(cls, *args, **kwargs):
        obj = object.__new__(cls, *args, **kwargs)
        obj._Data = Data
        return obj
    #--- End: def

    def __init__(self, cell_method=None, axes=(), method=None,
                 where=None, within=None, over=None, interval=(),
                 comment=None):
        '''
'''
        if cell_method is not None:
            cell_method = self.parse(cell_method)
            if len(cell_method) > 1:
                raise ValueError(" e5y 6sdf ")

            self.__dict__ = cell_method[0].__dict__.copy()
            
        else:
            super(CellMethod, self).__init__(axes=axes, method=method,
                                             where=where,
                                             within=within, over=over,
                                             interval=interval,
                                             comment=coment)
    #--- End: def

    @classmethod
    def parse(cls, string=None): #, field=None):
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
            cm.axes  = axes

            if not cell_methods:
                out.append(cm)
                break

            # Method
            cm.method = cell_methods.pop(0)

            if not cell_methods:
                out.append(cm)
                break

            # Climatological statistics and statistics which apply to
            # portions of cells
            while cell_methods[0] in ('within', 'where', 'over'):
                attr = cell_methods.pop(0)
                setattr(cm, attr, cell_methods.pop(0))
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
#                            parsed_interval = float(ast_literal_eval(interval))
                            parsed_interval = ast_literal_eval(interval)
                        except:
                            raise ValueError(
"Unparseable cell methods interval: {!r}".format(
    interval+' '+units if units is not None else interval))

                        try:
                            intervals.append(cls._Data(parsed_interval, units))
                        except:
                            raise ValueError(
"Unparseable cell methods interval: {!r}".format(
    interval+' '+units if units is not None else interval))
                            
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
                        cm.comment = ' '.join(comment)
                    #--- End: if

                #--- End: while 

                if cell_methods[0].endswith(')'):
                    cell_methods.pop(0)
            #--- End: if

            n_intervals = len(intervals)          
            if n_intervals > 1 and n_intervals != len(axes):
                raise ValueError("0798798  ")

            cm.interval = tuple(intervals)

            out.append(cm)
        #--- End: while

        return out
    #--- End: def

    @property
    def within(self):
        '''The cell method's within keyword.

These describe how climatological statistics have been derived.

.. seealso:: `over`

:Examples:

>>> c
>>> c
<CF CellMethod: time: minimum>
>>> print c.within
None
>>> c.within = 'years'
>>> c
<CF CellMethod: time: minimum within years>
>>> del c.within
>>> c
<CF CellMethod: time: minimum>

        '''
        return self._within
    @within.setter
    def within(self, value):
        self._within = value
    @within.deleter
    def within(self):
        self._within = None

    @property
    def where(self):
        '''
         
The cell method's where keyword.

These describe how climatological statistics have been derived.

.. seealso:: `over`

:Examples:

>>> c
>>> c
<CF CellMethod: time: minimum>
>>> print c.where
None
>>> c.where = 'land'
>>> c
<CF CellMethod: time: minimum where years>
>>> del c.where
>>> c
<CF CellMethod: time: minimum>
'''
        return self._where
    @where.setter
    def where(self, value):
        self._where = value
    @where.deleter
    def where(self):
        self._where = None

    @property
    def over(self):
        '''
         
The cell method's over keyword.

These describe how climatological statistics have been derived.

.. seealso:: `within`

:Examples:

>>> c
>>> c
<CF CellMethod: time: minimum>
>>> print c.over
None
>>> c.over = 'years'
>>> c
<CF CellMethod: time: minimum over years>
>>> del c.over
>>> c
<CF CellMethod: time: minimum>
'''
        return self._over
    @over.setter
    def over(self, value):
        self._over = value
    @over.deleter
    def over(self):
        self._over = None

    @property
    def comment(self):
        '''
        
Each cell method's comment keyword.

'''
        return self._comment
    @comment.setter
    def comment(self, value):
        self._comment = value
    @comment.deleter
    def comment(self):
        self._comment = None

    @property
    def method(self):
        '''The cell method's method keyword.

Describes how the cell values have been determined or derived.

:Examples:

>>> c
<CF CellMethod: time: minimum>
>>> c.method
'minimum'
>>> c.method = 'variance'
>>> c
<CF CellMethods: time: variance>
>>> del c.method
>>> c
<CF CellMethod: time: >

        '''
        return self._method
    @method.setter
    def method(self, value):
        self._method = value
    @method.deleter
    def method(self):
        self._method = None
#    @property
#    def names(self):
#        '''
#         
#Each cell method's name keyword(s).
#
#:Examples:
#
#>>> c = cf.CellMethods('time: minimum area: mean')       
#>>> c
#<CF CellMethods: time: minimum area: mean>
#>>> c.names
#(('time',), ('area',))
#>>> c[1].names = ['lat', 'lon']
#>>> c.names 
#(('time',), ('lat', 'lon'))
#>>> c
#<CF CellMethods: time: minimum lat: lon: mean>
#>>> d = c[1]
#>>> d
#<CF CellMethods: lat: lon: mean>
#>>> d.names
#(('lat', 'lon'),)
#>>> d.names = ('area',)
#>>> d.names
#(('area',),)
#>>> c
#<CF CellMethods: time: minimum area: mean>
#
#'''        
#        return self._names
#
#    @names.setter
#    def names(self, value):
#        if not isinstance(value, (list, tuple)):
#            raise ValueError(
#"names attribute must be a tuple or list, not {0!r}".format(
#    value.__class__.__name__))
#
#        self._names = tuple(value)
#
#        # Make sure that axes has the same number of elements as names
#        len_value = len(value)
#        if len_value != len(self._axes):
#            self.axes = (None,) * len_value
#    #--- End: def
# 
#    @names.deleter
#    def names(self):
#        self._.names = ()
    @property
    def interval(self):
        '''

Each cell method's interval keyword(s).

:Examples:

>>> c
<CF CellMethod: time: minimum>
>>> c.interval
()
>>> c.interval = ['1 hr']
>>> c
<CF CellMethod: time: minimum (interval: 1 hr)>
>>> c.interval
(<CF Data: 1 hr>,)
>>> c.interval = [cf.Data(7.5 'minutes')]
>>> c
<CF CellMethod: time: minimum (interval: 7.5 minutes)>
>>> c.interval
(<CF Data: 7.5 minutes>,)
>>> del c.interval
>>> c
<CF CellMethods: time: minimum>

>>> c
<CF CellMethod: lat: lon: mean>
>>> c.interval = ['0.2 degree_N', cf.Data(0.1 'degree_E')]
>>> c
<CF CellMethod: lat: lon: mean (interval: 0.1 degree_N interval: 0.2 degree_E)>

        '''
        return self._interval

    @interval.setter
    def interval(self, value):
        if not isinstance(value, (tuple, list)):
            raise ValueError(
"interval attribute must be a tuple or list, not {0!r}".format(
    value.__class__.__name__))
        
        # Parse the intervals
        values = []
        for interval in value:
            if isinstance(interval, basestring):
                i = interval.split()

                try:
                    x = ast_literal_eval(i.pop(0))
                except:
                    raise ValueError(
                        "Unparseable interval: {0!r}".format(interval))

                if interval:
                    units = ' '.join(i)
                else:
                    units = None
                    
                try:
                    d = self._Data(x, units)
                except:
                    raise ValueError(
                        "Unparseable interval: {0!r}".format(interval))
            else:
                try:
                    d = self._Data.asdata(interval, copy=True)
                except:
                    raise ValueError(
                        "Unparseable interval: {0!r}".format(interval))
            #--- End: if
            
            if d.size != 1:
                raise ValueError(
                    "Unparseable interval: {0!r}".format(interval))
                
            if d.ndim > 1:
                d.squeeze(copy=False)

            values.append(d)
        #--- End: for

        self._interval = tuple(values)
    #--- End: def
    @interval.deleter
    def interval(self):
        self._interval = ()

    @property
    def axes(self):
        '''
'''
        return self._axes
    @axes.setter
    def axes(self, value):
        if not isinstance(value, (tuple, list)):
            raise ValueError(
"axes attribute must be a tuple or list, not {0}".format(
    value.__class__.__name__))
        
        self._axes = tuple(value)
    #--- End: def
    @axes.deleter
    def axes(self):
        self._axes = ()

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

        n_axes = len(c._axes)
        intervals = c._interval
        if n_axes > 1 and len(intervals) == 1:
            c._interval *= n_axes

        return c
    #--- End: def

    def sort(self, argsort=None):
        axes = self._axes
        if len(axes) == 1:
            return

        if argsort is None:
            argsort = numpy_argsort(axes)
        elif len(argsort) != len(axes):
            raise ValueError(".sjdn ;siljdf vlkjndf jk")

        axes2 = []
        for i in argsort:
            axes2.append(axes[i])
        self._axes = tuple(axes2)

        intervals = self._interval
        if len(intervals) <= 1:
            return

        intervals2 = []
        for i in argsort:
            intervals2.append(intervals[i])
        self._interval = tuple(intervals2)
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

    def change_axes(self, axis_map, copy=True):
        '''
    '''
        if copy:
            c = self.copy()
        else:
            c = self

        if not axis_map:
            return c

        c._axes = tuple([axis_map.get(axis, axis) for axis in self._axes])

        return c
    #--- End: def

    def copy(self):
        '''Return a deep copy.

``c.copy()`` is equivalent to ``copy.deepcopy(c)``.

:Returns:

    out: `CellMethod`
        The deep copy.

:Examples:

>>> d = c.copy()

        '''   
        X = type(self)
        new = X.__new__(X)

        new._axes    = self._axes     
        new._method  = self._method   
        new._comment = self._comment  
        new._where   = self._where    
        new._within  = self._within   
        new._over    = self._over     

        intervals = self.interval
        if intervals:
            new.interval = tuple([i.copy() for i in intervals])
        else:
            new.interval = ()

        return new
    #--- End: def

    def equals(self, other, rtol=None, atol=None,
               ignore_data_type=False, ignore_fill_value=False,
               ignore=(), traceback=False):
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
        if self is other:
            return True

        # Check that each instance is the same type
        if self.__class__ != other.__class__:
            if traceback:
                print("{0}: Different types: {0} != {1}".format(
                    self.__class__.__name__, other.__class__.__name__))
            return False
        #--- End: if
        
        for attr in ('method', 'within', 'over', 'where', 'comment', 'axes'):
            if attr in ignore:
                continue

            x = getattr(self, attr)
            y = getattr(other, attr)
            if x != y:
                if traceback:
                    print("{0}: Different {1}: {2!r} != {3!r}".format(
                        self.__class__.__name__, attr, x, y))
                return False
        #--- End: for
        
        if 'intervals' in ignore:
            return True

        intervals0 = self.interval
        intervals1 = other.interval
        if intervals0:
            if not intervals1:
                if traceback:
                    print(
"{0}: Different intervals: {1!r} != {2!r}".format(
    self.__class__.__name__, self.interval, other.interval))
                return False
            #--- End: if
            
            if len(intervals0) != len(intervals1):
                if traceback:
                    print(
"{0}: Different intervals: {1!r} != {2!r}".format(
    self.__class__.__name__, self.interval, other.interval))
                return False
            #--- End: if
            
            for data0, data1 in zip(intervals0, intervals1):
                if not data0.equals(data1, rtol=rtol, atol=atol,
                                    ignore_data_type=ignore_data_type,
                                    ignore_fill_value=ignore_fill_value,
                                    traceback=traceback):
                    if traceback:
                        print(
"{0}: Different intervals: {1!r} != {2!r}".format(
    self.__class__.__name__, self.interval, other.interval))
                    return False
            #--- End: for

        elif intervals1:
            if traceback:
                print("{}: Different intervals: {!r} != {!r}".format(
                    self.__class__.__name__, self.interval, other.interval))
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

        other1 = other.copy()
        argsort = [axes1.index(axis0) for axis0 in axes0]
        other1.sort(argsort=argsort)
        self1 = self

        if not self1.equals(other1, rtol=rtol, atol=atol, ignore=('interval',)):
            if traceback:
                print("{0}: Nonequivalent: {1!r}, {2!r}".format(
                    self.__class__.__name__, self, other))
            return False
        #--- End: if

        if len(self1.interval) != len(other1.interval):
            self1 = self1.expand_intervals(copy=False)
            other1.expand_intervals(copy=False)
            if len(self1.interval) != len(other1.interval):
                if traceback:
                    print(
"{0}: Different numbers of intervals: {1!r} != {2!r}".format(
    self.__class__.__name__, self1.interval, other1.interval))
                return False
        #--- End: if

        intervals0 = self1.interval
        if intervals0:
            for data0, data1 in zip(intervals0, other1.interval):
                if not data0.allclose(data1, rtol=rtol, atol=atol):
                    if traceback:
                        print(
"{0}: Different interval data: {1!r} != {2!r}".format(
    self.__class__.__name__, self.interval, other.interval))
                    return False
        #--- End: if

        # Still here? Then they are equivalent
        return True
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
#                c.sort(argsort=[c.axes.index(axis) for axis in self.axes])
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


    def properties(self):
        '''
    '''
        out = {'axes'    : self.axes    ,
               'method'  : self.method  ,
               'where'   : self.where   ,
               'within'  : self.within  ,
               'over'    : self.over    ,
               'interval': self.interval,
               'comment' : self.comment ,
        }

        for key, value in out.items():
            if not value:
                del out[key]
        #--- End: for
        
        return out
    #--- End: def
    
#--- End: class
