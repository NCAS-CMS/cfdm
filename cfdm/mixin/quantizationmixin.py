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
        return self._del_component("quantize_on_write", default)

    def get_quantize_on_write(self, default=ValueError()):
        """TODOQ.

        .. versionadded:: (cfdm) NEXTVERSION

        :Returns:

            `Quantization`
                TODOQ

        """
        return self._get_component("quantize_on_write", default)

    def set_quantize_on_write(
        self,
        quantization,
        quantization_nsd=None,
        quantization_nsb=None,
        copy=True,
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

        if copy:
            q = quantization.copy()

        quantization_parameters = q.quantization_parameters()
        algorithm = q.get_parameter("algorithm", None)
        parameter = quantization_parameters.get(algorithm)

        if parameter is None:
            raise ValueError("TODOQ bad algorithm")

        if quantization_nsd is not None:
            if quantization_nsb is not None:
                raise ValueError(
                    "Can not set both 'quantization_nsd' and "
                    "'quantization_nsb' at the same time"
                )

            if parameter != "quantization_nsd":
                raise ValueError("TODOQ!")

            if not copy:
                # Copy anyway, because we're about to change it.
                q = quantization.copy()

            q.set_parameter(parameter, quantization_nsd, copy=False)
        elif quantization_nsb is not None:
            if parameter != "quantization_nsb":
                raise ValueError("TODOQ!")

            if not copy:
                # Copy anyway, because we're about to change it.
                q = quantization.copy()

            q.set_parameter(parameter, quantization_nsb, copy=False)

        self._set_component("quantize_on_write", q, copy=False)
