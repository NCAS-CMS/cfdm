from builtins import object


class NetCDF(object):
    '''Mixin

    '''

    def _intialise_netcdf(self, source=None):
        '''
        '''
        if source is None:
             netcdf = None
        else:        
            try:
                netcdf = source._get_component('netcdf', None)
            except AttributeError:
                netcdf = None
        #--- End: if
        
        if netcdf is None:        
            self._set_component('netcdf', {}, copy=False)
        else:
            self._set_component('netcdf', netcdf.copy(), copy=False)
    #--- End: def

#--- End: class
