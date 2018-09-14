from builtins import object


class NetCDFVariable(object):
    '''Mixin

    '''

    def _intialise_ncvar_from(self, source):
        '''
        '''
        try:
            ncvar = source.get_ncvar(None)
        except AttributeError:
            ncvar = None

        if ncvar is not None:
            self.set_ncvar(ncvar)
            
    def del_ncvar(self):
        '''
        '''        
        return self._del_component('ncvar')
    #--- End: def
        
    def get_ncvar(self, *default):
        '''ttttttttt
        '''        
        return self._get_component('ncvar', None, *default)
    #--- End: def

    def has_ncvar(self):
        '''
        '''        
        return self._has_component('ncvar')
    #--- End: def

    def set_ncvar(self, value):
        '''
        '''
        return self._set_component('ncvar', None, value)
    #--- End: def

#--- End: class
