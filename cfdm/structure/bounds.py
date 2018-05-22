import abc

import abstract

class Bounds(abstract.PropertiesData):
    '''A cell bounds array with properties.

An array of cell bounds spans the same domain axes as its coordinate
array, with the addition of an extra dimension whose size is that of
the number of vertices of each cell. This extra dimension does not
correspond to a domain axis construct since it does not relate to an
independent axis of the domain. Note that, for climatological time
axes, the bounds are interpreted in a special way indicated by the
cell method constructs.

    '''
    __metaclass__ = abc.ABCMeta

#--- End: class
