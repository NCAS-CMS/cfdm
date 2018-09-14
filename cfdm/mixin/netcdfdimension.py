from builtins import object


class NetCDFDimension(object):
    '''Mixin

    '''

    def _intialise_ncdim_from(self, source):
        '''
        '''
        try:
            ncdim = source.get_ncdim(None)
        except AttributeError:
            ncdim = None

        if ncdim is not None:
            self.set_ncdim(ncdim)
    #--- End: def

    def del_ncdim(self):
        '''
        '''        
        return self._del_component('ncdim')
    #--- End: def

    def get_ncdim(self, *default):
        '''ttttttttt
        '''        
        return self._get_component('ncdim', None, *default)
    #--- End: def

    def has_ncdim(self):
        '''
        '''        
        return self._has_component('ncdim')
    #--- End: def

    def set_ncdim(self, value):
        '''
        '''
        return self._set_component('ncdim', None, value)
    #--- End: def

#--- End: class
