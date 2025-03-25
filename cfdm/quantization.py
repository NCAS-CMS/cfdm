from . import core, mixin


class Quantization(
    mixin.NetCDFVariable,
    mixin.NetCDFGroupAttributes,
    mixin.Files,
    mixin.Parameters,
    core.abstract.Parameters,
):
    """TODOQ.

    See CF section 8.4. "Lossy Compression via Quantization".

    **NetCDF interface**

    {{netCDF variable}}

    {{netCDF group attributes}}

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

    @classmethod
    def quantization_parameters(cls):
        """TODOQ.

        Maps the CF quantization "algorithm" to the corresponding CF
        property that defines the algorithm's parameter for the number
        of significant bits or digits.

        .. versionadded:: (cfdm) NEXTVERSION

        :Returns:

            `dict`
                A dictionary for which a key is a CF algorithm name,
                with corresponding value of the parameter name that
                configures the algorithm.

        """
        return {
            "bitgroom": "quantization_nsd",
            "bitround": "quantization_nsb",
            "digitround": "quantization_nsd",
            "granular_bitround": "quantization_nsd",
        }
