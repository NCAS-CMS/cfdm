from . import core, mixin


class Quantization(
    mixin.NetCDFVariable,
    mixin.NetCDFGroupAttributes,
    mixin.Files,
    mixin.Parameters,
    core.abstract.Parameters,
):
    """A quantization variable.

    Quantization eliminates false precision, usually by rounding the
    least significant bits of floating-point mantissas to zeros, so
    that a subsequent compression on disk is more efficient.

    A quantization variable describes a quantization algorithm via a
    collection of parameters.

    The ``algorithm`` parameter names a specific quantization
    algorithm via one of the keys in the `algorithm_parameters`
    dictionary.

    The ``implementation`` parameter contains unstandardised text that
    concisely conveys the algorithm provenance including the name of
    the library or client that performed the quantization, the
    software version, and any other information required to
    disambiguate the source of the algorithm employed. The text must
    take the form ``software-name version version-string
    [(optional-information)]``.

    The retained precision of the algorithm is defined with either the
    ``quantization_nsb`` or ``quantization_nsd`` parameter.

    For instance, the following parameters describe quantization via
    the BitRound algorithm, retaining 6 significant bits, and
    implemented by libnetcdf::

       >>> q = {{package}}.{{class}}(
       ...         parameters={'algorithm': 'bitround',
       ...                     'quantization_nsb': 6,
       ...                     'implementation': 'libnetcdf version 4.9.4'}
       ... )
       >>> q.parameters()
       {'algorithm': 'bitround',
        'quantization_nsb': 6,
        'implementation': 'libnetcdf version 4.9.4'}

    See CF section 8.4. "Lossy Compression via Quantization".

    **NetCDF interface**

    {{netCDF variable}}

    {{netCDF group attributes}}

    .. versionadded:: (cfdm) 1.12.2.0

    """

    @classmethod
    def algorithm_parameters(cls):
        """Map CF quantization algorithms to CF algorithm parameters.

        .. versionadded:: (cfdm) 1.12.2.0

        :Returns:

            `dict`
                A dictionary for which a key is a CF quantization
                algorithm name, with a value of the name of the
                corresponding CF per-variable configuration attribute.

        **Examples**

        >>> {{package}}.{{class}}.algorithm_parameters()
        {'bitgroom': 'quantization_nsd',
         'bitround': 'quantization_nsb',
         'digitround': 'quantization_nsd',
         'granular_bitround': 'quantization_nsd'}

        """
        return {
            "bitgroom": "quantization_nsd",
            "bitround": "quantization_nsb",
            "digitround": "quantization_nsd",
            "granular_bitround": "quantization_nsd",
        }
