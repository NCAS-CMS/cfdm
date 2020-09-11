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

    .. versionadded:: (cfdm) 1.7.0

    '''
    def __init__(self, properties=None, data=None, source=None,
                 copy=True, _use_data=True):
        '''**Initialization**

    :Parameters:

        {{init properties: `dict`, optional}}

            *Parameter example:*
               ``properties={'standard_name': 'longitude'}``

        {{init data: data_like, optional}}

        source: optional
            Override the *properties* and *data* parameters with
            ``source.properties()`` and ``source.get_data(None)``
            respectively.

            If *source* does not have one of these methods, then the
            corresponding parameter is not set.

        {{init copy: `bool`, optional}}

        '''
        super().__init__(properties=properties, data=data,
                         source=source, copy=copy)

# --- End: class
