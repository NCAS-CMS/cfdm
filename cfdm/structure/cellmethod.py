import abc

import abstract

from data import Data

# ====================================================================
#
# Cell method object
#
# ====================================================================

#class CellMethod(abstract.Properties):
class CellMethod(abstract.Container):
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
        obj = object.__new__(cls, *args, **kwargs)
        obj._Data = Data
        return obj
    #--- End: def

    def __init__(self, axes=None, method=None, comment=None,
                 intervals=None, over=None, where=None, within=None,
                 source=None, copy=True):
        '''
        '''
        super(CellMethod, self).__init__(source=source)

        if source:
            try:
                intervals = source.get_intervals(None)
            except AttributeErrror:
                intervals = None

            if intervals is not None and copy:
                self.set_intervals([i.copy() for i in intervals])
            
            return
        #--- End: if

        if axes is not None:
            axes = self.set_axes(axes)

        if comment is not None:
            axes = self.set_comment(comment)

        if intervals is not None:
            axes = self.set_intervals(intervals)

        if method is not None:
            method = self.set_method(method)

        if over is not None:
            axes = self.set_over(over)

        if where is not None:
            axes = self.set_where(where)

        if within is not None:
            axes = self.set_within(within)
    #--- End: def

    def __repr__(self):
        '''x.__repr__() <==> repr(x)

        '''
        return '<{0}: {1}>'.format(self.__class__.__name__, str(self))
    #--- End: def

    def __str__(self):
        '''x.__str__() <==> str(x)

Return a CF-netCDF-like string of the cell method.

Note that if the intention use this string in a CF-netCDF cell_methods
attribute then the cell method's `!name` attribute may need to be
modified, where appropriate, to reflect netCDF variable names.

        '''     
        string = ['{0}:'.format(axis) for axis in self.get_axes(())]
        string.append(self.get_method(''))
        return ' '.join(string)
    #--- End: def

    def copy(self):
        '''Return a deep copy.

``f.copy()`` is equivalent to ``copy.deepcopy(f)``.

.. versionadded:: 1.6

:Examples 1:

>>> g = f.copy()

:Returns:

    out:
        The deep copy.

        '''
        return type(self)(source=self, copy=True)
    #--- End: def

    def del_axes(self):
        '''
'''
        return self._del_component('axes')
    #--- End: def
    
    def del_intervals(self):
        '''
'''
        return self._del_component('intervals')
    #--- End: def
    
    def del_method(self):
        '''
'''
        return self._del_component('method')
    #--- End: def
    
    def get_axes(self, *default):
        '''
'''
        return self._get_component('axes', None, *default)
    #--- End: def

    def get_comment(self, *default):
        '''
'''
        return self._get_component('comment', None, *default)
    #--- End: def

    def get_intervals(self, *default):
        '''
'''
        return self._get_component('intervals', None, *default)
    #--- End: def

    def get_method(self, *default):
        '''
        '''
        return self._get_component('method', None, *default)
    #--- End: def

    def get_over(self, *default):
        '''
'''
        return self._get_component('over', None, *default)
    #--- End: def

    def get_where(self, *default):
        '''
'''
        return self._get_component('where', None, *default)
    #--- End: def

    def get_within(self, *default):
        '''
'''
        return self._get_component('within', None, *default)
    #--- End: def

    def get_(self, *default):
        '''
'''
        return self._get_component('', None, *default)
    #--- End: def

    def has_axes(self):
        '''
'''
        return self._has_component('axes')
    #--- End: def

    def has_method(self):
        '''
'''
        return self._has_component('method')
    #--- End: def

    def set_axes(self, value):
        '''
        '''
        if isinstance(value, basestring):
            value = (value,)
        else:
            value = tuple(value)
            
        return self._set_component('axes', None, value)
    #--- End: def

    def set_comment(self, value):
        '''
'''
        return self._set_component('comment', None, value)
    #--- End: def

    def set_intervals(self, value):
        '''
'''
        return self._set_component('intervals', None, value)
    #--- End: def

    def set_method(self, value):
        '''
'''
        return self._set_component('method', None, value)
    #--- End: def

    def set_over(self, value):
        '''
'''
        return self._set_component('over', None, value)
    #--- End: def

    def set_where(self, value):
        '''
'''
        return self._set_component('where', None, value)
    #--- End: def

    def set_within(self, value):
        '''
'''
        return self._set_component('within', None, value)
    #--- End: def

#--- End: class
