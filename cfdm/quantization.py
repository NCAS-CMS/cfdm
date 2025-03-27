from . import core, mixin


class Quantization(
    mixin.NetCDFVariable,
    mixin.NetCDFGroupAttributes,
    mixin.Files,
    mixin.Parameters,
    core.abstract.Parameters,
):
    """A quantization variable.

    The parameters of a quantization variable describe a configured
    quantization algorithm. For instance, the following parameters
    describe quantization via the BitRound algorithm retaining 6
    significant bits, and implemented by libnetcdf::

       >>> q.parameters()
       {'algorithm': 'bitround',
        'quantization_nsb': 6,
        'implementation': 'libnetcdf version 4.9.2'}

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

               *Example:*
                 ``parameters={'algorithm': 'bitround',
                 'implementation': 'libnetcdf version 4.9.2'}``

            {{init source: optional}}

            {{init copy: `bool`, optional}}

        """
        super().__init__(parameters=parameters, source=source, copy=copy)

        self._initialise_netcdf(source)
        self._initialise_original_filenames(source)

    @classmethod
    def algorithm_parameters(cls):
        """Map CF quantization algorithms to CF algorithm parameters.

        .. versionadded:: (cfdm) NEXTVERSION

        :Returns:

            `dict`
                A dictionary for which a key is a CF quantization
                algorithm name, with corresponding value of the name
                of the CF attribute that configures it.

        """
        return {
            "bitgroom": "quantization_nsd",
            "bitround": "quantization_nsb",
            "digitround": "quantization_nsd",
            "granular_bitround": "quantization_nsd",
        }
