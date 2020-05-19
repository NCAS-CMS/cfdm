from . import abstract


class InteriorRing(abstract.PropertiesData):
    '''An interior ring array with properties.

    If a cell is composed of multiple polygon parts, an individual
    polygon may define an "interior ring", i.e. a region that is to be
    omitted from, as opposed to included in, the cell extent. In this
    case an interior ring array is required that records whether each
    polygon is to be included or excluded from the cell, and is
    supplied by an interior ring variable in CF-netCDF. The interior
    ring array spans the same domain axis constructs as its coordinate
    array, with the addition of an extra dimension that indexes the
    parts for each cell. For example, a cell describing the land area
    surrounding a lake would require two polygon parts: one defines
    the outer boundary of the land area; the other, recorded as an
    interior ring, is the lake boundary, defining the inner boundary
    of the land area.

    .. versionadded:: 1.8.0

    '''
# --- End: class
