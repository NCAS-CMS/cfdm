import abc

import abstract


class InteriorRing(abstract.PropertiesData):
    '''An interior ring array with properties.

An interior ring array records whether each part is to be included or
excluded from the cell. The array spans the same domain axes as its
coordinate array, with the addition of an extra ragged dimension whose
size for each cell is the number of cell parts.

    '''
    __metaclass__ = abc.ABCMeta

#--- End: class
