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

============  ========================================================
Attribute     Description
============  ========================================================
`!names`      
`!intervals`  
`!method`     
`!over`       
`!where`      
`!within`     
`!comment`    
`!axes`       
============  ========================================================

    '''
    _Data = Data
#    def __new__(cls, **kwargs):
#        cls = object.__new__(cls)
#        cls._Data = Data
#        return cls

    def __init__(self, *cell_method):
        '''
'''
        if cell_method:
            cell_method = CellMethods(*cell_method)
            if len(cell_method) > 1:
                raise ValueError(" e5y 6sdf ")

            cell_method = cell_method[0]
            self.__dict__ = cell_method[0].__dict__.copy()
        else:
            self._axes      = ()
            self._intervals = ()
            self._method    = None
            self._comment   = None
            self._where     = None
            self._within    = None
            self._over      = None
    #--- End: def

    def __deepcopy__(self, memo):
        '''

Used if copy.deepcopy is called on the variable.

'''
        return self.copy()
    #--- End: def

    def __getitem__(self, index):
        '''Called to implement evaluation of c[index].

c.__getitem__(index) <==> c[index]

The cell method is treated as if it were a single element cell methods
list containing itself, i.e. ``c[index]`` is equivalent to
``cf.CellMethods(c)[index]``.

:Examples 1:

>>> d = c[0]
>>> d = c[:1]
>>> d = c[1:]

:Returns:

    out : cf.CellMethod or cf.CellMethods
        If *index* is the integer 0 or -1 then the cell method itself
        is returned. If *index* is a slice then a cell methods list is
        returned which is either empty or else contains a single
        element of the cell method itself.
          
.. seealso:: `cf.CellMethods.__getitem__`

:Examples 2:

>>> c[0] is c[-1] is c
True
>>> c[0:1].equals(cf.FieldList(f))   
True
>>> c[0:1][0] is c
True
>>> c[1:].equals(cf.CellMethods())
True
>>> c[1:]       
[]
>>> c[-1::3][0] is c
True

        '''
        return CellMethods((self,))[index]
    #--- End: def

    def __hash__(self):
        '''

x.__hash__() <==> hash(x)

'''
        return hash(str(self))
    #--- End: def

    def __len__(self):
        '''Called by the :py:obj:`len` built-in function.

x.__len__() <==> len(x)

Always returns 1.

:Examples:

>>> len(c)
1

        '''
        return 1
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
        return self.dump(display=False, prefix='')
        string = ['{0}:'.format(axis) for axis in self._axes]

        method = self.method
        if method is None:
            method = ''

        string.append(method)

        for portion in ('within', 'where', 'over'):
            p = getattr(self, portion, None)
            if p is not None:
                string.extend((portion, p))
        #--- End: for

        intervals = self.intervals
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

    def __eq__(self, y):
        '''

x.__eq__(y) <==> x==y

'''
        return self.equals(y)
    #--- End: def

    def __ne__(self, other):
        '''

x.__ne__(y) <==> x!=y

'''
        return not self.__eq__(other)
    #--- End: def

    @classmethod
    def parse(cls, string=None, field=None):
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
            cm = cls() #CellMethod()

            axes  = []
            while cell_methods:
                if not cell_methods[0].endswith(':'):
                    break

                # Check that "name" ebds with colon? How? ('lat: mean (area-weighted) or lat: mean (interval: 1 degree_north comment: area-weighted)')

#                names.append(cell_methods.pop(0)[:-1])            
#                axes.append(None)

                axis = cell_methods.pop(0)[:-1]
                if field is not None:
                    axis = field.axis(axis, key=True)

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
                            intervals.append(self._Data(parsed_interval, units))
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

            cm.intervals = tuple(intervals)

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
    def intervals(self):
        '''

Each cell method's interval keyword(s).

:Examples:

>>> c
<CF CellMethod: time: minimum>
>>> c.intervals
()
>>> c.intervals = ['1 hr']
>>> c
<CF CellMethod: time: minimum (interval: 1 hr)>
>>> c.intervals
(<CF Data: 1 hr>,)
>>> c.intervals = [cf.Data(7.5 'minutes')]
>>> c
<CF CellMethod: time: minimum (interval: 7.5 minutes)>
>>> c.intervals
(<CF Data: 7.5 minutes>,)
>>> del c.intervals        
>>> c
<CF CellMethods: time: minimum>

>>> c
<CF CellMethod: lat: lon: mean>
>>> c.intervals = ['0.2 degree_N', cf.Data(0.1 'degree_E')]
>>> c
<CF CellMethod: lat: lon: mean (interval: 0.1 degree_N interval: 0.2 degree_E)>

        '''
        return self._intervals

    @intervals.setter
    def intervals(self, value):
        if not isinstance(value, (tuple, list)):
            raise ValueError(
"intervals attribute must be a tuple or list, not {0!r}".format(
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

        self._intervals = tuple(values)
    #--- End: def
    @intervals.deleter
    def intervals(self):
        self._intervals = ()

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

    def dump(self, display=True, prefix=None, field=None, _level=0):
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

    field: `cf.Field`, optional

:Returns:

    out: `str` or `None`
        A string containing the description.

:Examples:
         
        '''
        if prefix is None:
            prefix = 'Cell Method: '

        if not field:
            names = self.axes
        else:
            names = [field.axis_name(axis, default=axis) for axis in self.axes]

        string = ['{0}{1}:'.format(prefix, axis) for axis in names]

        method = self.method
        if method is None:
            method = ''

        string.append(method)

        for portion in ('within', 'where', 'over'):
            p = getattr(self, portion, None)
            if p is not None:
                string.extend((portion, p))
        #--- End: for

        intervals = self.intervals
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

        string = ' '.join(string)

        if display:
            print string
        else:
            return string
    #--- End: def

    def expand_intervals(self, copy=True):
        if copy:
            c = self.copy()
        else:
            c = self

        n_axes = len(c._axes)
        intervals = c._intervals
        if n_axes > 1 and len(intervals) == 1:
            c._intervals *= n_axes

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

        intervals = self._intervals
        if len(intervals) <= 1:
            return

        intervals2 = []
        for i in argsort:
            intervals2.append(intervals[i])
        self._intervals = tuple(intervals2)
    #--- End: def

    def remove_axes(self, axes):
        '''

:Parameters:

    axes: sequence of `str`

:Returns:

    None

        '''
        if len(self._intervals) <= 1:
            self._axes = tuple([axis for axis in self._axes if axis not in axes])
            if not len(self._axes):
                self._intervals = ()
            return
        
        # Still here?
        _axes = []
        _intervals = []

        for axis, interval in zip(self._axes, self._intervals):
            if axis not in axes:
                _axes.append(axis)
                _intervals.append(interval)

        self._axes      = tuple(_axes)
        self._intervals = tuple(_intervals)
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

        intervals = self.intervals
        if intervals:
            new.intervals = tuple([i.copy() for i in intervals])
        else:
            new.intervals = ()

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

        if 'intervals' in ignore:
            return True

        intervals0 = self.intervals
        intervals1 = other.intervals
        if intervals0:
            if not intervals1:
                if traceback:
                    print("{}: Different intervals: {!r} != {!r}".format(
                        self.__class__.__name__, self.intervals, other.intervals))
                return False

            if len(intervals0) != len(intervals1):
                if traceback:
                    print("{}: Different intervals: {!r} != {!r}".format(
                        self.__class__.__name__, self.intervals, other.intervals))
                return False

            for data0, data1 in zip(intervals0, intervals1):
                if not data0.equals(data1, rtol=rtol, atol=atol,
                                    ignore_data_type=ignore_data_type,
                                    ignore_fill_value=ignore_fill_value,
                                    traceback=traceback):
                    if traceback:
                        print("{}: Different intervals: {!r} != {!r}".format(
                            self.__class__.__name__, self.intervals, other.intervals))
                    return False
     
        elif intervals1:
            if traceback:
                print("{}: Different intervals: {!r} != {!r}".format(
                    self.__class__.__name__, self.intervals, other.intervals))
            return False
        #--- End: if

        return True
    #--- End: def

    def equivalent(self, other, rtol=None, atol=None, traceback=False):
        '''True if two cell methods are equivalent, False otherwise.

The `axes` and `intervals` attributes are ignored in the comparison.

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

        axes0 = self.axes
        axes1 = other.axes
            
        if len(axes0) != len(axes1) or set(axes0) != set(axes1):
            if traceback:
                print("{}: Nonequivalent axes: {!r}, {!r}".format(
                    self.__class__.__name__, axes0, axes1))
            return False
            
        other1 = other.copy()
        argsort = [axes1.index(axis0) for axis0 in axes0]
        other1.sort(argsort=argsort)
        self1 = self

        if not self1.equals(other1, rtol=rtol, atol=atol, ignore=('intervals',)):
            if traceback:
                print("{0}: Nonequivalent: {1!r}, {2!r}".format(
                    self.__class__.__name__, self, other))
            return False

        if len(self1.intervals) != len(other1.intervals):
            self1 = self1.expand_intervals(copy=False)
            other1.expand_intervals(copy=False)
            if len(self1.intervals) != len(other1.intervals):
                if traceback:
                    print("{0}: Different numbers of intervals: {1!r} != {2!r}".format(
                        self.__class__.__name__, self1.intervals, other1.intervals))
                return False

        intervals0 = self1.intervals
        if intervals0:
            for data0, data1 in zip(intervals0, other1.intervals):
                if not data0.allclose(data1, rtol=rtol, atol=atol):
                    if traceback:
                        print("{0}: Different interval data: {1!r} != {2!r}".format(
                            self.__class__.__name__, self.intervals, other.intervals))
                    return False
        #--- End: if

        # Still here? Then they are equivalent
        return True
    #--- End: def

    def write(self, axis_map={}):
        '''

Return a string of the cell method.


'''
        string = ['{0}:'.format(axis_map.get(axis, axis))
                  for axis in self._axes]

        method = self._method
        if method is None:
            return ''

        string.append(method)

        for portion in ('within', 'where', 'over'):
            p = getattr(self, portion, None)
            if p is not None:
                string.extend((portion, p))
        #--- End: for

        intervals = self.intervals
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

#--- End: class

## ====================================================================
##
## CellMethods object
##
## ====================================================================
#
#class CellMethods(list):
#    '''
#
#A CF cell methods object to describe the characteristic of a field
#that is represented by cell values.
#
#'''
#
#    def __init__(self, *cell_methods):
#        '''
#
#**Initialization**
#
#:Parameters:
#
#    string : str or cf.CellMethod or cf.CellMethods, optional
#        Initialize new instance from a CF-netCDF-like cell methods
#        string. See the `parse` method for details. By default an
#        empty cell methods is created.
#
#:Examples:
#
#>>> c = cf.CellMethods()
#>>> c = cf.CellMethods('time: max: height: mean')
#        '''
#        if cell_methods and len(cell_methods) == 1:
#            cell_methods = cell_methods[0]
#            if isinstance(cell_methods, basestring):
#                cell_methods = self._parse(cell_methods)
#
#        super(CellMethods, self).__init__(cell_methods)
#    #--- End: def
#
#    # ================================================================
#    # Overloaded list methods
#    # ================================================================
#    def __getslice__(self, i, j):
#        '''
#
#Called to implement evaluation of f[i:j]
#
#f.__getslice__(i, j) <==> f[i:j]
#
#:Examples 1:
#
#>>> g = f[0:1]
#>>> g = f[1:-4]
#>>> g = f[:1]
#>>> g = f[1:]
#
#:Returns:
#
#    out : cf.CellMethods
#
#'''
#        return type(self)(list.__getslice__(self, i, j))
#    #--- End: def
#
#    def __getitem__(self, index):
#        '''Called to implement evaluation of f[index]
#
#f.__getitem_(index) <==> f[index]
#
#:Examples 1:
#
#>>> g = f[0]
#>>> g = f[-1:-4:-1]
#>>> g = f[2:2:2]
#
#:Returns:
#
#    out : cf.CellMethod or cf.CellMethods
#        If *index* is an integer then a cell method is returned. If
#        *index* is a slice then a sequence of cell methods are
#        returned, which may be empty.
#
#        '''
#        out = list.__getitem__(self, index)
#        if isinstance(out, list):
#            return type(self)(out)
#        return out
#    #--- End: def
#
#    def __deepcopy__(self, memo):
#        '''
#Used if copy.deepcopy is called on the variable.
#
#'''
#        return self.copy()
#    #--- End: def
#
#    def __hash__(self):
#        '''
#
#x.__hash__() <==> hash(x)
#
#'''
#        return hash(str(self))
#    #--- End: def
#
#    def __repr__(self):
#        '''
#x.__repr__() <==> repr(x)
#
#'''
#        return '<CF %s: %s>' % (self.__class__.__name__, str(self))
#    #--- End: def
#
#    def __str__(self):
#        '''
#
#x.__str__() <==> str(x)
#
#'''        
#        return ' '.join([str(cm) for cm in self])
#    #--- End: def
#
#    def __eq__(self, other):
#        '''
#
#x.__eq__(y) <==> x==y
#
#'''
#        return self.equals(other)
#    #--- End: def
#
#    def __ne__(self, other):
#        '''
#
#x.__ne__(y) <==> x!=y
#
#'''
#        return not self.__eq__(other)
#    #--- End: def
#
#    def _parse(self, string=None, field=None):
#        '''Parse a CF cell_methods string into this `cf.CellMethods` instance in
#place.
#
#:Parameters:
#
#    string: `str`, optional
#        The CF cell_methods string to be parsed into the
#        `cf.CellMethods` object. By default the cell methods will be
#        empty.
#
#:Returns:
#
#    out: `list`
#
#:Examples:
#
#>>> c = cf.CellMethods()
#>>> c = c._parse('time: minimum within years time: mean over years (ENSO years)')    
#>>> print c
#Cell methods    : time: minimum within years
#                  time: mean over years (ENSO years)
#
#        '''
#        if not string:
#            return []
#
#        out = []
#
#        # Split the cell_methods string into a list of strings ready
#        # for parsing into the result list. E.g.
#        #   'lat: mean (interval: 1 hour)'
#        # maps to 
#        #   ['lat:', 'mean', '(', 'interval:', '1', 'hour', ')']
#        cell_methods = re_sub('\((?=[^\s])' , '( ', string)
#        cell_methods = re_sub('(?<=[^\s])\)', ' )', cell_methods).split()
#
#        while cell_methods:
#            cm = CellMethod()
#
#            axes  = []
#            while cell_methods:
#                if not cell_methods[0].endswith(':'):
#                    break
#
#                # Check that "name" ebds with colon? How? ('lat: mean (area-weighted) or lat: mean (interval: 1 degree_north comment: area-weighted)')
#
##                names.append(cell_methods.pop(0)[:-1])            
##                axes.append(None)
#
#                axis = cell_methods.pop(0)[:-1]
#                if field is not None:
#                    axis = field.axis(axis, key=True)
#
#                axes.append(axis)
#            #--- End: while
#            cm.axes  = axes
#
#            if not cell_methods:
#                out.append(cm)
#                break
#
#            # Method
#            cm.method = cell_methods.pop(0)
#
#            if not cell_methods:
#                out.append(cm)
#                break
#
#            # Climatological statistics and statistics which apply to
#            # portions of cells
#            while cell_methods[0] in ('within', 'where', 'over'):
#                attr = cell_methods.pop(0)
#                setattr(cm, attr, cell_methods.pop(0))
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
##                            parsed_interval = float(ast_literal_eval(interval))
#                            parsed_interval = ast_literal_eval(interval)
#                        except:
#                            raise ValueError(
#"Unparseable cell methods interval: {!r}".format(
#    interval+' '+units if units is not None else interval))
#                            
#                        try:
#                            intervals.append(self._Data(parsed_interval, units))
#                        except:
#                            raise ValueError(
#"Unparseable cell methods interval: {!r}".format(
#    interval+' '+units if units is not None else interval))
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
#                        cm.comment = ' '.join(comment)
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
#                raise ValueError("0798798  ")
#
#            cm.intervals = tuple(intervals)
#
#            out.append(cm)
#        #--- End: while
#
#        return out
#    #--- End: def
#
#    @property
#    def axes(self):
#        return tuple([cm.axes for cm in self])
# 
#    @axes.setter
#    def axes(self, value):
#        if len(self) > 1:
#            raise ValueError(
#"Must select a cell method to update. Consider c[i].intervals=value")
#        if not self:
#            raise ValueError("Can't update empty cell methods list")
#
#        if not isinstance(value, (tuple, list)):
#            raise ValueError("%s axes attribute must be a tuple or list" %
#                             self.__class__.__name__)
#        
#        self[0].axes = value
#    #--- End: def
#
#    @axes.deleter
#    def axes(self):
#        if len(self) > 1:
#            raise ValueError(
#"Must select a cell method to update. Consider c[i].intervals=value")
#
#        if self:
#            self[0].axes = ()
#    #--- End: def
#
#    @property
#    def comment(self):
#        '''
#         
#Each cell method's comment keyword.
#
#'''
#        return tuple([cm.comment for cm in self])
#
#    @comment.deleter
#    def comment(self):
#        if len(self) > 1:
#            raise ValueError(
#"Must select a cell method to update. Consider c[i].intervals=value")
#        
#        if self:
#            self[0].comment = None
#    #--- End: def
# 
#    @property
#    def method(self):
#        '''
#
#Each cell method's method keyword.
#
#These describe how the cell values of field have been determined or
#derived.
#
#:Examples:
#
#>>> c = cf.CellMethods('time: minimum area: mean')       
#>>> c
#<CF CellMethods: time: minimum area: mean>
#>>> c.method
#['minimum', 'mean']
#>>> c[1].method = 'variance'
#>>> c.method
#['minimum', 'variance']
#>>> c
#<CF CellMethods: time: minimum area: variance>
#>>> d = c[1]
#>>> d
#<CF CellMethods: area: variance>
#>>> d.method
#['variance']
#>>> d.method = 'maximum'
#>>> d.method
#['maximum']
#>>> c
#<CF CellMethods: time: minimum area: maximum>
#
#'''
#        return tuple([cm.method for cm in self])
#    #--- End: def
#
#    @method.setter
#    def method(self, value):
#        if len(self) > 1:
#            raise ValueError(
#"Must select a cell method to update. Consider c[i].intervals=value")
#        if not self:
#            raise ValueError("Can't update empty cell methods list")
#        
#        self[0].method = value
#    #--- End: def
# 
#    @method.deleter
#    def method(self):
#        if len(self) > 1:
#            raise ValueError(
#"Must select a cell method to update. Consider c[i].intervals=value")
#
#        if self:
#            self[0].method = None
#    #--- End: def
# 
#    @property
#    def intervals(self):
#        '''
#
#Each cell method's interval keyword(s).
#
#'''
#        return tuple([cm.intervals for cm in self])
#
#    @intervals.setter
#    def intervals(self, value):
#        if len(self) > 1:
#            raise ValueError(
#"Must select a cell method to update. Consider c[i].intervals=value")
#        if not self:
#            raise ValueError("Can't update empty cell methods list")
#            
#        if not isinstance(value, (tuple, list)):
#            raise ValueError(
#"{0} intervals attribute must be a tuple or list, not a {1}".format(
#    self.__class__.__name__, value.__class__.__name__))
#        
#        # Parse the intervals
#        values = []
#        for interval in value:
#            if isinstance(interval, basestring):
#                i = interval.split()
#
#                try:
#                    x = ast_literal_eval(i.pop(0))
#                except:
#                    raise ValueError(
#"Unparseable cell methods interval: {0!r}".format(interval))
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
#"Unparseable cell method interval: {0!r}".format(interval))
#            else:
#                try:
#                    d = self._Data.asdata(interval, copy=True)
#                except:
#                    raise ValueError(
#"Unparseable cell method interval: {0!r}".format(interval))
#            #--- End: if
#            
#            if d.size != 1:
#                raise ValueError(
#"Unparseable cell method interval: {0!r}".format(interval))
#                
#            if d.ndim > 1:
#                d.squeeze(copy=False)
#
#            values.append(d)
#        #--- End: for
#
#        self[0].intervals = tuple(values)
#    #--- End: def
# 
#    @intervals.deleter
#    def intervals(self):
#        if len(self) > 1:
#            raise ValueError(
#"Must select a cell method to update. Consider del c[i].intervals")
#        
#        if self:
#            self[0].intervals = ()
#    #--- End: def
# 
#    @property
#    def over(self):
#        '''
#         
#Each cell method's over keyword.
#
#These describe how climatological statistics have been derived.
#
#.. seealso:: `within`
#
#:Examples:
#
#>>> c = cf.CellMethods('time: minimum area: mean')       
#>>> c
#<CF CellMethods: time: minimum time: mean>
#>>> c.over
#[None, None]
#>>> c[0].within = 'years'
#>>> c[1].over = 'years'
#>>> c.over
#>>> [None, 'years']
#>>> c
#<CF CellMethods: time: minimum within years time: mean over years>
#>>> d = c[1]
#>>> d
#<CF CellMethods: time: mean over years>
#>>> del d.over
#>>> d.over
#[None]
#>>> d
#<CF CellMethods: time: mean>
#>>> del c[0].within
#>>> c.within
#()        
#>>> c
#<CF CellMethods: time: minimum time: mean>
#
#'''
#        return tuple([cm.over for cm in self])
#    #--- End: def
#
#    @over.setter
#    def over(self, value):
#        if len(self) > 1:
#            raise ValueError(
#"Must select a cell method to update. Consider c[i].over=value")
#        if not self:
#            raise ValueError("Can't update empty cell methods list")
#
#        self[0].over = value
#    #--- End: def
# 
#    @over.deleter
#    def over(self):
#        if len(self) > 1:
#            raise ValueError(
#"Must select a cell method to update. Consider c[i].over=value")
#        
#        if self:
#            self[0].over = None
#    #--- End: def
# 
#    @property
#    def where(self):
#        '''
#         
#Each cell method's where keyword.
#
#'''
#        return tuple([cm.where for cm in self])
#    #--- End: def
# 
#    @where.setter
#    def where(self, value):
#        if len(self) > 1:
#            raise ValueError(
#"Must select a cell method to update. Consider c[i].intervals=value")
#        if not self:
#            raise ValueError("Can't update empty cell methods list")
#
#        self[0].where = value
#    #--- End: def
# 
#    @where.deleter
#    def where(self):
#        if len(self) > 1:
#            raise ValueError(
#"Must select a cell method to update. Consider c[i].intervals=value")
#        
#        if self:
#            self[0].where = None
#    #--- End: def
# 
#    @property
#    def within(self):
#        '''
#         
#Each cell method's within keyword.
#
#These describe how climatological statistics have been derived.
#
#.. seealso:: `over`
#
#:Examples:
#
#>>> c = cf.CellMethods('time: minimum area: mean')       
#>>> c
#<CF CellMethods: time: minimum time: mean>
#>>> c.within
#(None, None)
#>>> c[0].within = 'years'
#>>> c[1].over = 'years'
#>>> c
#<CF CellMethods: time: minimum within years area: mean over years>
#>>> c.within
#>>> ('years', None)
#>>> del c[0].within
#>>> c
#<CF CellMethods: time: minimum time: mean over years>
#>>> c.within
#>>> (None, None)
#'''
#        return tuple([cm.within for cm in self])
#    #--- End: def
# 
#    def copy(self):
#        '''
#
#Return a deep copy.
#
#``c.copy()`` is equivalent to ``copy.deepcopy(c)``.
#
#:Returns:
#
#    out : 
#        The deep copy.
#
#:Examples:
#
#>>> d = c.copy()
#
#'''   
#        return type(self)([cm.copy() for cm in self])
#    #--- End: def
#
#    def change_axes(self, axis_map, copy=False):
#        '''
#    '''
#        if copy:
#            cms = self.copy()
#        else:
#            cms = self
#
#        for cm in cms:
#            cm.change_axes(axis_map, copy=False)
#
#        return cms
#    #--- End: def
#
#    def dump(self, display=True, prefix=None, field=None, _level=0):
#        '''
#        
#Return a string containing a full description of the instance.
#
#If a cell methods 'name' is followed by a '*' then that cell method is
#relevant to the data in a way which may not be precisely defined its
#corresponding dimension or dimensions.
#
#:Parameters:
#
#    display: `bool`, optional
#        If False then return the description as a string. By default
#        the description is printed, i.e. ``c.dump()`` is equivalent to
#        ``print c.dump(display=False)``.
#
#    prefix: `str`, optional
#       Set the common prefix of component names. By default the
#       instance's class name is used.
#
#    field: `cf.Field`, optional
#
#:Returns:
#
#    out: `str` or `None`
#        A string containing the description.
#
#:Examples:
#
#        '''
#        indent1 = '    ' * _level        
#        
#        if prefix is None:
#            prefix = ''
#        else:
#            prefix = '{0}: '.format(prefix)
#
#        string = ['{0}{1}'.format(prefix, 
#                                  cm.dump(display=False, field=field, _level=_level))
#                  for cm in self]
#        string = '\n'.join(string)
#        
#        if display:
#            print string
#        else:
#            return string
#    #--- End: def
#
#    def equals(self, other, rtol=None, atol=None,
#               ignore_fill_value=False, traceback=False):
#        '''
#
#True if two cell methods are equal, False otherwise.
#
#The `axes` attribute is ignored in the comparison.
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
#    ignore_fill_value : bool, optional
#        If True then data arrays with different fill values are
#        considered equal. By default they are considered unequal.
#
#    traceback : bool, optional
#        If True then print a traceback highlighting where the two
#        instances differ.
#
#:Returns: 
#
#    out : bool
#        Whether or not the two instances are equal.
#
#:Examples:
#
#'''
#        if self is other:
#            return True
#
#        # Check that each instance is the same type
#        if self.__class__ != other.__class__:
#            if traceback:
#                print("{0}: Different types: {0} != {1}".format(
#                    self.__class__.__name__,
#                    other.__class__.__name__))
#            return False
#
#        if len(self) != len(other):
#            if traceback:
#                print(
#                    "{0}: Different numbers of cell methods: {1} != {2}".format(
#                        self.__class__.__name__, len(self), len(other)))
#            return False
#    
#        for cm0, cm1 in zip(self, other):
#            if not cm0.equals(cm1, rtol=rtol, atol=atol,
#                              ignore_fill_value=ignore_fill_value,
#                              traceback=traceback):
#                return False 
#        #--- End: for
#
#        return True
#    #--- End: def
#
#    def equivalent(self, other, rtol=None, atol=None, traceback=False):
#        '''
#
#True if two cell methods are equivalent, False otherwise.
#
#The `axes` attributes are ignored in the comparison.
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
#:Examples:
#
#'''
#        if self is other:
#            return True
#
#        # Check that each instance is the same type
#        if self.__class__ != other.__class__:
#            if traceback:
#                print("{0}: Different types: {0} != {1}".format(
#                    self.__class__.__name__, other.__class__.__name__))
#            return False
#
#        if len(self) != len(other):
#            if traceback:
#                print(
#"{0}: Different numbers of methods: {1} != {2}".format(
#    self.__class__.__name__, len(self), len(other)))
#            return False
#    
#        for cm0, cm1 in zip(self, other):
#            if not cm0.equivalent(cm1, rtol=rtol, atol=atol, 
#                                  traceback=traceback):
#                if traceback:
#                    print("{0}: Different cell method".format(self.__class__.__name__))
#                return False 
#        #--- End: for
#
#        return True
#    #--- End: def
#
##    def has_cellmethod(self, other):
##        '''
##
##Return True if and only if this cell methods is a super set of another.
##
##:Parameters:
##
##    other : cf.CellMethods
##        The other cell methods for comparison.
##
##:Returns:
##    out : bool
##        Whether or not this cell methods is a super set of the other.
##
##:Examples:
##
##'''
##        if len(other) != 1:
##            return False
##
##        found_match = False
##
##        cm1 = other[0]
##        for cm in self:
##            if cm.equivalent(cm1):
##                found_match = True
##                break
##        #--- End: for
##
##        return found_match
##    #--- End: def
#
#    def inspect(self):
#        '''
#
#Inspect the attributes.
#
#.. seealso:: `cf.inspect`
#
#:Returns: 
#
#    None
#
#'''
#        print cf_inspect(self)
#    #--- End: def
#
#    def remove_axes(self, axes):
#        '''
#        '''
#        for cm in self:
#            cm.remove_axes(axes)
#    #--- End: def
#
#    def translate_from_netcdf(self, field):
#        '''
#
#Translate netCDF variable names stored in the `!names` attribute into 
#`axes` and `names` attributes.
#
#:Parameters:
#
#    field : cf.Field
#        The field which provides the translation.
#
#:Returns:
#
#    out : cf.CellMethods
#        A new cell methods instance with translated names.
#
#:Examples:
#
#>>> c = cf.CellMethods('t: mean lon: mean')
#>>> c.names = (('t',), ('lon',))
#>>> c.axes = ((None,), (None,))
#>>> d = c.translate_from_net(f)
#>>> d.names = (('time',), ('longitude',))
#>>> d.axes = (('dim0',), ('dim2',))
#>>> d
#<CF CellMethods: 'time: mean longitude: mean')
#
#        '''
#        cell_methods = self.copy()
#
#        # Change each names value to a standard_name (or coordinate
#        # identifier) and create the axes attribute.
#            
#        # CF conventions (version 1.7): In the specification of this
#        # attribute, name can be a dimension of the variable, a scalar
#        # coordinate variable, a valid standard name, or the word
#        # 'area'.
#        for cm in cell_methods:
#            names = cm.names
#
#            if names == ('area',):
#                cm.axes = (None,)
#                continue
#
#            names = list(names)
#            axes  = []
#
#            dim_coords = field.dims()
#
#            # Still here?
#            for i, name in enumerate(names):
#                axis = None
#                for axis, ncdim in field.ncdimensions.iteritems():
#                    if name == ncdim:
#                        break
#                    
#                    axis = None
#                #--- End: for                    
#
#                if axis is not None:
#                    # name is a netCDF dimension name (including
#                    # scalar coordinates).
#                    axes.append(axis)
#                    if axis in dim_coords:
#                        names[i] = dim_coords[axis].name(default=axis)
#                    else:
#                        names[i] = None
#                else:                    
#                    # name must (ought to) be a standard name
#                    axes.append(field.axis({'standard_name': name},
#                                           role='d', exact=True, key=True))
#            #--- End: for
#
#            cm.names = tuple(names)
#            cm.axes  = tuple(axes)
#        #--- End: for
#    
#        return cell_methods
#    #--- End: def
#
#    def translate_to_netcdf(self, axis_to_ncdim, axis_to_ncscalar):
#        '''
#
#Translate `names` to CF-netCDF names.
#
#:Parameters:
#
#    axis_to_ncdim: dict
#        The first dictionary which provides the translation.
#
#    axis_to_ncscalar: dict
#        The alternative dictionary which provides the translation.
#
#:Returns:
#
#    out : cf.CellMethods
#        A new cell methods instance with translated names.
#
#:Examples:
#
#>>> c = cf.CellMethods('t: mean lon: mean')
#>>> c.names = (('t',), ('lon',))
#>>> c.axes = ((None,), (None,))
#>>> d = c.translate_to_netcdf(f)
#>>> d.names = (('time',), ('longitude',))
#>>> d.axes = (('dim0',), ('dim2',))
#>>> d
#<CF CellMethods: 'time: mean longitude: mean')
#
#        '''
#        new = self.copy()
#
#        for cm in new:
#            names = cm.names
#            if names == ('area',):
#                continue
#
#            cm.names = tuple([axis_to_ncdim.get(a, axis_to_ncscalar.get(a, n))
#                              for a, n in zip(cm.axes, names)])
#        #--- End: for
#
#        return new
#    #--- End: def
#
#    def write(self, axis_map={}):
#        '''
#'''
#        return ' '.join([c.write(axis_map) for c in self])
#    #--- End: def
#
##--- End: class
