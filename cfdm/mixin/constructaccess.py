from builtins import object


class ConstructAccess(object):
    '''Mixin class for manipulating constructs stored in a `Constructs`
object.

    '''

    def auxiliary_coordinates(self, axes=None, copy=False):
        '''Return the auxiliary coordinates 
        '''    
        return self._get_constructs().constructs(
            construct_type='auxiliary_coordinate',
            axes=axes, copy=copy)
    #--- End: def

    def cell_measures(self, axes=None, copy=False):
        '''Return the 
        '''    
        return self._get_constructs().constructs(
            construct_type='cell_measure',
            axes=axes, copy=copy)
    #--- End: def

    def construct(self, description=None, axes=None,
                  construct_type=None, copy=False):
        '''
        '''
        return self._get_constructs().construct(
            description=description,
            construct_type=construct_type,
            axes=axes,
            copy=copy)
    #--- End: def

    def constructs(self, description=None, axes=None,
                   construct_type=None, copy=False):
        '''
        '''
        return self._get_constructs().constructs(
            description=description,
            construct_type=construct_type,
            axes=axes,
            copy=copy)
    #--- End: def

    def coordinates(self, axes=None, copy=False):
        '''
        '''
        out = self.dimension_coordinates(axes=axes, copy=copy)
        out.update(self.auxiliary_coordinates(axes=axes, copy=copy))
        return out
    #--- End: def

    def dimension_coordinates(self, axes=None, copy=False):
        '''Return the 
        '''    
        return self._get_constructs().constructs(
            construct_type='dimension_coordinate',
            axes=axes, copy=copy)
    #--- End: def

    def domain_ancillaries(self, axes=None, copy=False):
        '''
        '''    
        return self._get_constructs().constructs(
            construct_type='domain_ancillary',
            axes=axes, copy=copy)
    #--- End: def

    def domain_axis_name(self, axis):
        '''
        '''
        return self._get_constructs().domain_axis_name(axis)
    #--- End: def
    
#--- End: class
