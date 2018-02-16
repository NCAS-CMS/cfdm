import abc

import abstract

# ====================================================================
#
# Cell method object
#
# ====================================================================

class CellMethod(abstract.Properties):
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
    
    def __init__(self, axes=None, method=None, properties={},
                 source=None, copy=True):
        '''
        '''
        super(CellMethod, self).__init__(properties=properties,
                                         source=source, copy=copy)

        if source:
            if not isinstance(source, CellMethod):
                raise ValueError(
"ERROR: source must be a subclass of 'CellMethod'. Got {!r}".format(
    source.__class__.__name__))

            if axes is None:
                axes = source.get_axes(None)

            if method is None:
                method = source.get_method(None)
        #--- End: if

        if axes is not None:
            axes = self.set_axes(axes)

        if method is not None:
            method = self.set_method(method)
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
        string = ['{0}:'.format(axis) for axis in self.get_axes(())]
        string.append(self.get_method(''))
        return ' '.join(string)
    #--- End: def

    def del_axes(self):
        '''
'''
        return self._del_component('axes', None)
    #--- End: def
    
    def del_method(self):
        '''
'''
        return self._del_component('method', None)
    #--- End: def
    
    def get_axes(self, *default):
        '''
'''
        return self._get_component('axes', None, *default)
    #--- End: def

    def get_method(self, *default):
        '''
        '''
        return self._get_component('method', None, *default)
    #--- End: def
    
    def has_axes(self):
        '''
'''
        return self._has_component('axes', None)
    #--- End: def

    def has_method(self):
        '''
'''
        return self._has_component('method', None)
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

    def set_method(self, value):
        '''
'''
        return self._set_component('method', None, value)
    #--- End: def

#--- End: class
