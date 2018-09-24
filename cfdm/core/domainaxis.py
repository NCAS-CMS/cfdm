from builtins import (str, super)

from . import abstract


class DomainAxis(abstract.Container):
    '''A domain axis construct of the CF data model. 

A domain axis construct specifies the number of points along an
independent axis of the domain. It comprises a positive integer
representing the size of the axis. In CF-netCDF it is usually defined
either by a netCDF dimension or by a scalar coordinate variable, which
implies a domain axis of size one. The field construct's data array
spans the domain axis constructs of the domain, with the optional
exception of size one axes, because their presence makes no difference
to the order of the elements.

    '''
    def __init__(self, size=None, source=None, copy=True):
        '''**Initialization**

:Parameters:

    size: `int`, optional
        The size of the domain axis.

    source:

    copy: `bool`, optional
        If True then . In any 

        '''
        super().__init__()
        
        if source is not None:
            try:
                size = source.get_size(None)
            except AttributeError:
                size = None
        #--- End: if
        
        if size is not None:
            self.set_size(size)        
    #--- End: def

    def __str__(self):
        '''x.__str__() <==> str(x)

        '''
        return str(self.get_size(''))
    #--- End: def

    def copy(self):
        '''
        '''
        return type(self)(source=self)
    #--- End: def

    def del_size(self):
        '''
        '''
        return self._del_component('size')
    #--- End: def

    def has_size(self):
        '''
        '''
        return self._has_component('size')
    #--- End: def

    def get_size(self, *default):
        '''
        '''
        return self._get_component('size', *default)
    #--- End: def

    def set_size(self, size, copy=True):
        '''
        '''
        self._set_component('size', size, copy=copy)
    #--- End: def

#--- End: class
