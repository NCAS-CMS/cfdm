import abc


# ====================================================================
#
# 
#
# ====================================================================

class ConstructAccess(object):
    '''
    '''
    __metaclass__ = abc.ABCMeta

    def domain_axis_name(self, axis):
        '''
        '''
        return self._get_constructs().domain_axis_name(axis)
    #--- End: for
    
#--- End: class
