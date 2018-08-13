import abc


class ConstructAccess(object):
    '''Mixin class for manipulating constructs stored in a `Constructs`
object.

    '''
    __metaclass__ = abc.ABCMeta

    def construct(self, construct_type=None, name=None, axes=None,
                  copy=False):
        '''
        '''
        return self._get_constructs().construct(
            construct_type=construct_type,
            name=name,
            axes=axes,
            copy=copy)
    #--- End: def

    def constructs(self, construct_type=None, name=None, axes=None,
                   copy=False):
        '''
        '''
        return self._get_constructs().constructs(
            construct_type=construct_type,
            name=name,
            axes=axes,
            copy=copy)
    #--- End: def

    def domain_axis_name(self, axis):
        '''
        '''
        return self._get_constructs().domain_axis_name(axis)
    #--- End: def
    
#--- End: class
