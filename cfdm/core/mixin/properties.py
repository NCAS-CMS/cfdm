import abc

# ====================================================================
#

#
# ====================================================================

class Properties(object):
    '''

Base class for storing a data array with metadata.

A variable contains a data array and metadata comprising properties to
describe the physical nature of the data.

All components of a variable are optional.

'''
    __metaclass__ = abc.ABCMeta

    
    
    def del_ncvar(self):
        '''
        '''        
        return self._del_attribute('ncvar')
    #--- End: def

    def get_ncvar(self, *default):
        '''
        '''        
        return self._get_attribute('ncvar', *default)
    #--- End: def

#    @abc.abstractmethod
#    def name(self, default=None, ncvar=True):
#        '''Return a name for the construct.
#        '''
 #       pass
 #   #--- End: def

    def set_ncvar(self, value):
        '''
        '''        
        return self._set_attribute('ncvar', value)
    #--- End: def

#--- End: class
