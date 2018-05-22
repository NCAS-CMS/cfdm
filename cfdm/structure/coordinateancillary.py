import abc

import abstract


class CoordinateAncillary(abstract.PropertiesData):
    '''A coordinate ancillary array with properties.

An ancillary array records whether each part is to be included or
excluded from the cell. The ancillary array spans the same domain axes
as its coordinate array, with the addition of an extra ragged
dimension whose size for each cell is the number of cell parts. A
CF-netCDF interior ring variable corresponds to an ancillary array
indicating which parts, if any, are to be excluded from the cells.

    '''
    __metaclass__ = abc.ABCMeta

#--- End: class
