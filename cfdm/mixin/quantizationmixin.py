class QuantizationWriteMixin:
    """TODOQ.

    .. versionadded:: (cfdm) NEXTVERSION

    """

    def del_quantize_on_write(self, default=ValueError()):
        """TODOQ.

        .. versionadded:: (cfdm) NEXTVERSION

        :Returns:

            `Quantization`
                TODOQ

        """
        self._del_component("quantize_on_write", default)

    def get_quantize_on_write(self, default=ValueError()):
        """TODOQ.

        .. versionadded:: (cfdm) NEXTVERSION

        :Returns:

            `Quantization`
                TODOQ

        """
        return self._get_component("quantize_on_write", default)

    def set_quantize_on_write(
        self, quantization, quantization_nsd=None, quantization_nsb=None
    ):
        """TODOQ.

        .. versionadded:: (cfdm) NEXTVERSION

        :Parameters:

            quantization: `Quantization`

            quantization_nsd: `int` or `None`, optional

            quantization_nsb: `int` or `None`, optional

        :Returns:

            `None`

        """
        if self.get_quantization(None) is not None:
            raise ValueError("TODOQ can't set on write when already quantized")

        q = quantization.copy()

        quantization_parameters = q.quantization_parameters()
        algorithm = q.get_parameter("algorithm", None)
        parameter = quantization_parameters.get(algorithm)

        if parameter is None:
            raise ValueError("TODOQ bad algorithm")

        if quantization_nsd is not None:
            if quantization_nsd is not None:
                raise ValueError(
                    "Must provide either 'quantization_nsd' or "
                    "'quantization_nsb', but not both."
                )

            if parameter != "quantization_nsd":
                raise ValueError("TODOQ!")

            ns = quantization_nsd
        elif quantization_nsb is not None:
            if parameter != "quantization_nsb":
                raise ValueError("TODOQ!")

            ns = quantization_nsb
        else:
            raise ValueError(
                "Must provide either 'quantization_nsd' or "
                "'quantization_nsb', but not both."
            )

        q.set_parameter(parameter, ns, copy=False)
        self._set_component("quantize_on_write", q, copy=False)
