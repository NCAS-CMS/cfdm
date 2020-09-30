from . import mixin
from . import core


class Datum(mixin.Parameters,
            mixin.NetCDFVariable,
            core.Datum):
    '''A datum component of a coordinate reference construct of the CF
    data model.

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

    The netCDF variable name of the construct may be accessed with the
    `nc_set_variable`, `nc_get_variable`, `nc_del_variable` and
    `nc_has_variable` methods.

    The netCDF variable group structure may be accessed with the
    `nc_set_variable`, `nc_get_variable`, `nc_variable_groups`,
    `nc_clear_variable_groups` and `nc_set_variable_groups` methods.

    .. versionadded:: (cfdm) 1.7.0

    '''
    def __init__(self, parameters=None, source=None, copy=True):
        '''**Initialization**

    :Parameters:

        parameters: `dict`, optional
           Set parameters. The dictionary keys are parameter names,
           with corresponding values. Ignored if the *source*
           parameter is set.

           Parameters may also be set after initialisation with the
           `set_parameters` and `set_parameter` methods.

           *Parameter example:*
             ``parameters={'earth_radius': 6371007.}``

        source: optional
            Initialize the parameters from those of *source*.

            {{init source}}

        {{init copy: `bool`, optional}}

        '''
        super().__init__(parameters=parameters,
                         source=source,
                         copy=copy)

        self._initialise_netcdf(source)

# --- End: class
