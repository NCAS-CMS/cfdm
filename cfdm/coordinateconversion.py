from . import mixin
from . import core


class CoordinateConversion(mixin.ParametersDomainAncillaries,
                           core.CoordinateConversion):
        #with_metaclass(
        #abc.ABCMeta,
        #type('NewBase', (mixin.ParametersDomainAncillaries, structure.CoordinateConversion), {}))):
    '''
'''
    
    # Ancillary-valued terms are stored as references to external
    # objects
    _internal_ancillaries = False

#--- End: class
