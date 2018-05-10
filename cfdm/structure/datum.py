import abc

import abstract


class Datum(abstract.Terms):
    '''A datum of a coordinate reference construct of the CF data model.

A datum is a complete or partial definition of the zeroes of the
dimension and auxiliary coordinate constructs which define a
coordinate system. The datum may be indicated via properties or domain
ancilary constructs. Elements of the datum not specified may be
implied by the metadata of the dimension and auxiliary coordinate
constructs of the coordinate system.

Note that the datum may contain the definition of a geophysical
surface which corresponds to the zero of a vertical coordinate
construct, and this may be required for both horizontal and vertical
coordinate systems.

    '''
    __metaclass__ = abc.ABCMeta

#--- End: class
