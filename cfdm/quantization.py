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
    describe quantization via the BitRound algorithm, retaining 6
    significant bits, and implemented by libnetcdf::

       >>> q.parameters()
       {'algorithm': 'bitround',
        'quantization_nsb': 6,
        'implementation': 'libnetcdf version 4.9.4'}

    See CF section 8.4. "Lossy Compression via Quantization".

    **NetCDF interface**

    {{netCDF variable}}

    {{netCDF group attributes}}

    .. versionadded:: (cfdm) NEXTVERSION

    """

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
