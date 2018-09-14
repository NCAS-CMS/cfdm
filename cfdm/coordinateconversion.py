from . import mixin
from . import structure


class CoordinateConversion(mixin.ParametersDomainAncillaries,
                           structure.CoordinateConversion):
        #with_metaclass(
        #abc.ABCMeta,
        #type('NewBase', (mixin.ParametersDomainAncillaries, structure.CoordinateConversion), {}))):
    '''
'''
    
    # Ancillary-valued terms are stored as references to external
    # objects
    _internal_ancillaries = False

#--- End: class
