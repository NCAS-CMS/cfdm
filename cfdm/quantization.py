from . import core, mixin


class Quantization(mixin.Parameters, mixin.NetCDFVariable, mixin.Files, core.abstract.Parameters):
    """TODOQ

    **NetCDF interface**

    {{netCDF variable}}

    .. versionadded:: (cfdm) NEXTVERSION

    """

    def __init__(self, parameters=None, source=None, copy=True):
        """**Initialisation**

        :Parameters:

            parameters: `dict`, optional
               Set parameters. The dictionary keys are parameter
               names, with corresponding values.

               Parameters may also be set after initialisation with
               the `set_parameters` and `set_parameter` methods.

               *Parameter example:*
                 ``parameters=TODOQ``

            {{init source: optional}}

            {{init copy: `bool`, optional}}

        """
        super().__init__(parameters=parameters, source=source, copy=copy)

        self._initialise_netcdf(source)
        self._initialise_original_filenames(source)
