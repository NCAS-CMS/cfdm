#from __future__ import absolute_import
#from future.utils import with_metaclass
#
#import abc

from . import abstract


class Bounds(abstract.PropertiesData):
#    class Bounds(with_metaclass(abc.ABCMeta, abstract.PropertiesData)):
    '''A cell bounds array with properties.

An array of cell bounds spans the same domain axes as its coordinate
array, with the addition of an extra dimension whose size is that of
the number of vertices of each cell. This extra dimension does not
correspond to a domain axis construct since it does not relate to an
independent axis of the domain. Note that, for climatological time
axes, the bounds are interpreted in a special way indicated by the
cell method constructs.

In the CF data model, cell bounds do not have their own properties
because they can not logically be different to those of the coordinate
construct itself. However, it is sometimes desired to store properties
on a CF-netCDF bounds variable, so the `Bounds` object supports this
capability.

    '''

#--- End: class
