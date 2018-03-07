import collections

from copy import deepcopy

# ====================================================================
#

#
# ====================================================================

class Collection(dict):
    '''

Base class for storing a data array with metadata.

A variable contains a data array and metadata comprising properties to
describe the physical nature of the data.

All components of a variable are optional.

'''    
    def copy(self):
        '''Return a deep copy.

``x.copy()`` is equivalent to ``copy.deepcopy(x)``.

.. versionadded:: 1.6

:Examples 1:

>>> d = c.copy()

:Parameters:

    data: `bool`, optional
        This parameter has no effect and is ignored.

:Returns:

    out:
        The deep copy.

        '''        
        return deepcopy(self)
    #--- End: def

#--- End: class
