import abc

import abstract

class Datum(abstract.Terms):
    '''A datum of a coordinate reference construct of the CF data model.

A datum is a complete or partial definition of the zeroes of the
dimension and auxiliary coordinate constructs which define a
coordinate system.

The datum may contain the definition of a geophysical surface which
corresponds to the zero of a vertical coordinate construct, and this
may be required for both horizontal and vertical coordinate systems.

Elements of the datum not specified may be implied by the properties
of the dimension and auxiliary coordinate constructs referenced by the
`CoordinateReference` object that contains the datum.

    '''
    __metaclass__ = abc.ABCMeta

#--- End: class
