import abc

import abstract


class CoordinateConversion(abstract.Terms):
    '''A coordinate conversion of a coordinate reference construct of the
CF data model.

A coordinate conversion defines a formula for converting coordinate
values taken from the dimension or auxiliary coordinate constructs to
a different coordinate system. A term of the conversion formula can be
a scalar or vector parameter which does not depend on any domain axis
constructs, may have units (such as a reference pressure value), or
may be a descriptive string (such as the projection name "mercator"),
or it can be a domain ancillary construct (such as one containing
spatially varying orography data). A coordinate reference construct
relates the field's coordinate values to locations in a planetary
reference frame.

    '''
    __metaclass__ = abc.ABCMeta

#--- End: class
