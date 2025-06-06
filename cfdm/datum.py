from . import core, mixin


class Datum(mixin.Parameters, mixin.NetCDFVariable, mixin.Files, core.Datum):
    """A datum component of a CF data model coordinate reference.

    A datum is a complete or partial definition of the zeroes of the
    dimension and auxiliary coordinate constructs which define a
    coordinate system.

    The datum may contain the definition of a geophysical surface
    which corresponds to the zero of a vertical coordinate construct,
    and this may be required for both horizontal and vertical
    coordinate systems.

    Elements of the datum not specified may be implied by the
    properties of the dimension and auxiliary coordinate constructs
    referenced by the `CoordinateReference` instance that contains the
    datum.

    **NetCDF interface**

    {{netCDF variable}}

    .. versionadded:: (cfdm) 1.7.0

    """
