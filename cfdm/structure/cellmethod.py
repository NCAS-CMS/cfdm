from collections import abc
from re import sub    as re_sub
from re import search as re_search
from ast import literal_eval as ast_literal_eval

from .functions import equals

from .data.data import Data

# ====================================================================
#
# CellMethod object
#
# ====================================================================

class CellMethod(object):
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
    
    _Data = Data
#    def __new__(cls, **kwargs):
#        cls = object.__new__(cls)
#        cls._Data = Data
#        return cls

    def __init__(self, axes=(), method=None, where=None, within=None,
                 over=None, intervals=(), comment=None, source=None,
                 copy=True):
        '''
'''
        if source:
            print 'WHAT?'

        else:
            if axes is not None:
                axes = self.get_axes(())
            if method is not None:
                method = self.get_method(None)
            if where is not None:
               where  = self.get_where(None)
            if within is not None:
                within = self.get_within(None)
            if over is not None:
                over = self.get_over(None)
            if comment is not None:
                comment = self.get_comment(None)
            if intervals is not None:
                intervals = self.get_intervals(())
                if copy and intervals:
                    intervals = tuple([i.copy() for i in intervals])
        #--- End: if
        
        self.set_axes(axes) 
        self.set_method(method)
        self.set_where(where)
        self.set_within(within)
        self.set_over(over)
        self.set_intervals(intervals)
        self.set_comment(comment)
    #--- End: def

    def __deepcopy__(self, memo):
        '''

Used if copy.deepcopy is called on the variable.

'''
        return self.copy()
    #--- End: def

    def __repr__(self):
        '''Called by the :py:obj:`repr` built-in function.

x.__repr__() <==> repr(x)

        '''
        return '<{0}: {1}>'.format(self.__class__.__name__, str(self))
    #--- End: def

    def __str__(self):
        '''

x.__str__() <==> str(x)

Return a CF-netCDF-like string of the cell method.

Note that if the intention use this string in a CF-netCDF cell_methods
attribute then the cell method's `!name` attribute may need to be
modified, where appropriate, to reflect netCDF variable names.

'''      
        string = ['{0}:'.format(axis) for axis in self.axes]

        method = self.method
        if method is None:
            method = ''

        string.append(method)

        for portion in ('within', 'where', 'over'):
            p = getattr(self, portion, None)
            if p is not None:
                string.extend((portion, p))
        #--- End: for

        intervals = self.interval
        if intervals:
            x = ['(']

            y = ['interval: {0}'.format(data) for data in intervals]
            x.append(' '.join(y))

            if self.comment is not None:
                x.append(' comment: {0}'.format(self.comment))

            x.append(')')

            string.append(''.join(x))

        elif self.comment is not None:
            string.append('({0})'.format(self.comment))

        return ' '.join(string)
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
    def get_interval(self, *default):
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
        interval = self._interval
        if interval is None:
            if default:
                return default[0]

            raise AttributeError("interval aascas 34r34 5iln ")

        return interval
    #--- End: def
    
    def set_interval(self, interval, copy=True):
        '''
        '''
        if not isinstance(value, (tuple, list)):
            raise ValueError(
"interval attribute must be a tuple or list, not {0!r}".format(
    value.__class__.__name__))
        
        # Parse the intervals
        values = []
        for interval in value:
#            if isinstance(interval, basestring):
#                i = interval.split()
#
#                try:
#                    x = ast_literal_eval(i.pop(0))
#                except:
#                    raise ValueError(
#                        "Unparseable interval: {0!r}".format(interval))
#
#                if interval:
#                    units = ' '.join(i)
#                else:
#                    units = None
#                    
#                try:
#                    d = self._Data(x, units)
#                except:
#                    raise ValueError(
#                        "Unparseable interval: {0!r}".format(interval))
#            else:
            try:
                d = self._Data.asdata(interval, copy=True)
            except:
                raise ValueError(
                    "Unparseable interval: {0!r}".format(interval))
#            #--- End: if
            
            if d.size != 1:
                raise ValueError(
                    "Unparseable interval: {0!r}".format(interval))
                
            if d.ndim > 1:
                d.squeeze(copy=False)

            values.append(d)
        #--- End: for

        self._interval = tuple(values)
    #--- End: def

    def del_interval(self):
        '''
        '''
        interval = self._interval
        self._interval = None
        return interval
    #--- End: def
    
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
    #--- End: def
    @interval.deleter
    def interval(self):


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

``d.copy()`` is equivalent to ``copy.deepcopy(d)``.

:Returns:

    out: 
        The deep copy.

:Examples:

>>> e = d.copy()

        '''
        new = type(self)(source=self, copy=True)
    #--- End: def

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
