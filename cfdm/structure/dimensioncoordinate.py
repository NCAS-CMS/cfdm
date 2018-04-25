import abc

import abstract
import mixin

from .cellextent import CellExtent


class DimensionCoordinate(mixin.CellAccess, abstract.Coordinate):
    '''A dimension coordinate construct of the CF data model.

Coordinate constructs provide information which locate the cells of
the domain and which depend on a subset of the domain axis
constructs. As previously discussed, there are two distinct types of
coordinate construct: a dimension coordinate construct provides
monotonic numeric coordinates for a single domain axis, and an
auxiliary coordinate construct provides any type of coordinate
information for one or more of the domain axes.

In both cases, the coordinate construct consists of a data array of
the coordinate values which spans a subset of the domain axis
constructs, an optional array of cell bounds recording the extents of
each cell, and properties to describe the coordinates (in the same
sense as for the field construct). An array of cell bounds spans the
same domain axes as its coordinate array, with the addition of an
extra dimension whose size is that of the number of vertices of each
cell. This extra dimension does not correspond to a domain axis
construct since it does not relate to an independent axis of the
domain. Note that, for climatological time axes, the bounds are
interpreted in a special way indicated by the cell method constructs.

The dimension coordinate construct is able to unambiguously describe
cell locations because a domain axis can be associated with at most
one dimension coordinate construct, whose data array values must all
be non-missing and strictly monotonically increasing or
decreasing. They must also all be of the same numeric data type. If
cell bounds are provided, then each cell must have exactly two
vertices. CF-netCDF coordinate variables and numeric scalar coordinate
variables correspond to dimension coordinate constructs.

    '''
    __metaclass__ = abc.ABCMeta

    def __new__(cls, *args, **kwargs):
        obj = object.__new__(cls, *args, **kwargs)
        
        obj._CellExtent = CellExtent

        return obj
    #--- End: def
#--- End: class
