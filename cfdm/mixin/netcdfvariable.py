from builtins import object


class NetCDFVariable(object):
    '''Mixin

    '''

    def _intialise_ncvar_from(self, source):
        '''
        '''
        try:
            ncvar = source.nc_get_variable(None)
        except AttributeError:
            ncvar = None

        if ncvar is not None:
            self.nc_set_variable(ncvar)
    #--- End: def

#    def del_ncvar(self):
#        '''
#        '''        
#        return self._del_component('ncvar')
#    #--- End: def
#        
#    def has_ncvar(self):
#        '''
#        '''        
#        return self._has_component('ncvar')
#    #--- End: def
#
#    def set_ncvar(self, value):
#        '''
#        '''
#        return self._set_component('ncvar', value, copy=False)
#    #--- End: def

    def nc_del_variable(self):
        '''
        '''        
        return self._del_component('nc_variable')
    #--- End: def
        
    def nc_get_variable(self, *default):
        '''ttttttttt
        '''        
        return self._get_component('nc_variable', *default)
    #--- End: def

    def nc_has_variable(self):
        '''
        '''        
        return self._has_component('nc_variable')
    #--- End: def

    def nc_set_variable(self, value):
        '''
        '''
        return self._set_component('nc_variable', value, copy=False)
    #--- End: def

#    def get_ncvar(self, *default):
#        '''ttttttttt
#        '''        
#        return self._get_component('ncvar', *default)
#    #--- End: def
#
#    def del_ncvar(self):
#        '''ttttttttt
#        '''        
#        return self.nc_del_variable()
#    #--- End: def
#
#    def get_ncvar(self, *default):
#        '''ttttttttt
#        '''        
#        return self.nc_get_variable(*default)
#    #--- End: def
#
#    def has_ncvar(self):
#        '''ttttttttt
#        '''        
#        return self.nc_has_variable()
#    #--- End: def
#
#    def set_ncvar(self, value):
#        '''ttttttttt
#        '''        
#        return self.nc_set_variable(value)
#    #--- End: def

#--- End: class
