import abc

import mixin
import structure


class CoordinateConversion(mixin.Terms, structure.CoordinateConversion):
    '''
'''
    __metaclass__ = abc.ABCMeta
    
    # Ancillary-valued terms are stored as references to external
    # objects
    _internal_ancillaries = False

#--- End: class
