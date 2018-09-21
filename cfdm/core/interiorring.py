from . import abstract


class InteriorRing(abstract.PropertiesData):
    '''An interior ring array with properties.

For polygon geometries, an individual part may define an "interior
ring", i.e. a hole that is to be omitted from the cell extent (as
would occur, for example, for a cell describing the land area of a
region containing a lake). In this case an interior ring array is
required that records whether each polygon is to be included or
excluded from the cell, supplied by an interior ring variable in
CF-netCDF. The interior ring array spans the same domain axes as its
coordinate array, with the addition of an extra ragged dimension that
indexes the geometries for each cell.

    '''

#--- End: class
