from builtins import object


class NetCDF(object):
    '''Mixin

    '''

    def _initialise_netcdf(self, source=None):
        '''
        '''
        if source is None:
             netcdf = {}
        else:        
            try:
                netcdf = source._get_component('netcdf', None).copy()
            except AttributeError:
                netcdf = {}
        #--- End: if
        
        self._set_component('netcdf', netcdf, copy=False)
    #--- End: def

#--- End: class


class NetCDFDimension(NetCDF):
    '''Mixin

    '''

#    def _initialise_ncdim_from(self, source):
#        '''
#        '''
#        try:
#            ncdim = source.nc_get_dimension(None)
#        except AttributeError:
#            ncdim = None##
#
#        if ncdim is not None:
#            self.nc_set_dimension(ncdim)
#    #--- End: def

    def nc_del_dimension(self, *default):
        '''
        '''
        try:
            return self._get_component('netcdf').pop('dimension', *default)
        except keyError:
            raise AttributeError("{!r} object has no netCDF dimension name".format(self.__class__.__name__))
    #--- End: def

    def nc_get_dimension(self, *default):
        '''ttttttttt
        '''
        try:
            return self._get_component('netcdf')['dimension']
        except KeyError:
            if default:
                return default[0]

            raise AttributeError("{!r} has no netCDF dimension name".format(
                self.__class__.__name__))
    #--- End: def

    def nc_has_dimension(self):
        '''
        '''
        return 'dimension' in self._get_component('netcdf')
    #--- End: def

    def nc_set_dimension(self, value):
        '''
        '''
        self._get_component('netcdf')['dimension'] = value
    #--- End: def

#--- End: class


class NetCDFVariable(NetCDF):
    '''Mixin

    '''

#    def _initialise_ncvar_from(self, source):
#        '''
#        '''
#        try:
#            ncvar = source.nc_get_variable(None)
#        except AttributeError:
#            ncvar = None
#
#        if ncvar is not None:
#            self.nc_set_variable(ncvar)
#    #--- End: def

    def nc_del_variable(self, *default):
        '''
        '''        
        try:
            return self._get_component('netcdf').pop('variable', *default)
        except keyError:
            raise AttributeError("{!r} object has no netCDF variable name".format(self.__class__.__name__))
    #--- End: def
        
    def nc_get_variable(self, *default):
        '''ttttttttt
        '''
        try:
            return self._get_component('netcdf')['variable']
        except KeyError:
            if default:
                return default[0]

            raise AttributeError("{!r} has no netCDF variable name".format(
                self.__class__.__name__))
    #--- End: def

    def nc_has_variable(self):
        '''
        '''
        return 'variable' in self._get_component('netcdf')
    #--- End: def

    def nc_set_variable(self, value):
        '''
        '''
        self._get_component('netcdf')['variable'] = value
    #--- End: def

#--- End: class


class NetCDFSampleDimension(NetCDF):
    '''Mixin

    '''
    def nc_del_sample_dimension(self, *default):
        '''
        '''        
        try:
            return self._get_component('netcdf').pop('sample_dimension', *default)
        except keyError:
            raise AttributeError("{!r} object has no netCDF sample dimension name".format(self.__class__.__name__))
    #--- End: def

    def nc_get_sample_dimension(self, *default):
        '''ttttttttt
        '''
        try:
            return self._get_component('netcdf')['sample_dimension']
        except KeyError:
            if default:
                return default[0]

            raise AttributeError("{!r} has no netCDF sample dimension name".format(
                self.__class__.__name__))
    #--- End: def

    def nc_has_sample_dimension(self):
        '''
        '''
        return 'sample_dimension' in self._get_component('netcdf')
    #--- End: def

    def nc_set_sample_dimension(self, value):
        '''
        '''
        self._get_component('netcdf')['sample_dimension'] = value
    #--- End: def

#--- End: class

class NetCDFInstanceDimension(NetCDF):
    '''Mixin

    '''
    def nc_del_instance_dimension(self,*default):
        '''
        '''        
        try:
            return self._get_component('netcdf').pop('instance_dimension', *default)
        except keyError:
            raise AttributeError("{!r} object has no netCDF instance dimension name".format(self.__class__.__name__))
    #--- End: def

    def nc_get_instance_dimension(self, *default):
        '''ttttttttt
        '''
        try:
            return self._get_component('netcdf')['instance_dimension']
        except KeyError:
            if default:
                return default[0]

            raise AttributeError("{!r} has no netCDF instance dimension name".format(
                self.__class__.__name__))
    #--- End: def

    def nc_has_instance_dimension(self):
        '''
        '''
        return 'instance_dimension' in self._get_component('netcdf')
    #--- End: def

    def nc_set_instance_dimension(self, value):
        '''
        '''
        self._get_component('netcdf')['instance_dimension'] = value
    #--- End: def

#--- End: class

