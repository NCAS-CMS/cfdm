from builtins import super

from . import abstract


class Bounds(abstract.PropertiesData):
    '''A cell bounds component of a coordinate or domain ancillary
    construct of the CF data model.

    An array of cell bounds spans the same domain axes as its
    coordinate array, with the addition of an extra dimension whose
    size is that of the number of vertices of each cell. This extra
    dimension does not correspond to a domain axis construct since it
    does not relate to an independent axis of the domain. Note that,
    for climatological time axes, the bounds are interpreted in a
    special way indicated by the cell method constructs.

    .. versionadded:: 1.7.0

    '''
    def __init__(self, properties=None, data=None, source=None,
                 copy=True, _use_data=True):
        '''**Initialization**

    :Parameters:

        properties: `dict`, optional
            Set descriptive properties. The dictionary keys are
            property names, with corresponding values. Ignored if the
            *source* parameter is set.

            Properties may also be set after initialisation with the
            `set_properties` and `set_property` methods.

            *Parameter example:*
               ``properties={'standard_name': 'altitude'}``

        data: `Data`, optional
            Set the data. Ignored if the *source* parameter is set.

            The data also may be set after initialisation with the
            `set_data` method.

        source: optional
            Override the *properties* and *data* parameters with
            ``source.properties()`` and ``source.get_data(None)``
            respectively.

            If *source* does not have one of these methods, then the
            corresponding parameter is not set.

        copy: `bool`, optional
            If False then do not deep copy input parameters prior to
            initialization. By default arguments are deep copied.

        '''
        super().__init__(properties=properties, data=data,
                         source=source, copy=copy)

# --- End: class
