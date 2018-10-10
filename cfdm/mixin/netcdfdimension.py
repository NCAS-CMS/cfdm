from builtins import object


class NetCDFDimension(object):
    '''Mixin

    '''

    def _intialise_ncdim_from(self, source):
        '''
        '''
        try:
            ncdim = source.nc_get_dimension(None)
        except AttributeError:
            ncdim = None

        if ncdim is not None:
            self.nc_set_dimension(ncdim)
    #--- End: def

    def nc_del_dimension(self):
        '''
        '''        
        return self._del_component('nc_dimension')
    #--- End: def

    def nc_get_dimension(self, *default):
        '''ttttttttt
        '''        
        return self._get_component('nc_dimension', *default)
    #--- End: def

    def nc_has_dimension(self):
        '''
        '''        
        return self._has_component('nc_dimension')
    #--- End: def

    def nc_set_dimension(self, value):
        '''
        '''
        return self._set_component('nc_dimension', value, copy=False)
    #--- End: def

#--- End: class
