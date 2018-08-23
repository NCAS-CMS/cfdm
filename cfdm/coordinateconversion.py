from __future__ import absolute_import
import abc

from . import mixin
from . import structure
from future.utils import with_metaclass

class CoordinateConversion(with_metaclass(
        abc.ABCMeta,
        type('NewBase', (mixin.ParametersDomainAncillaries, structure.CoordinateConversion), {}))):
    '''
'''
    
    # Ancillary-valued terms are stored as references to external
    # objects
    _internal_ancillaries = False

#--- End: class
