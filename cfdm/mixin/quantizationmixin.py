class QuantizationWriteMixin:
    """Mixin class for constructs that allow quantize-on-write.

    .. versionadded:: (cfdm) NEXTVERSION

    """

    def del_quantize_on_write(self, default=ValueError()):
        """TODOQ.

        .. versionadded:: (cfdm) NEXTVERSION

        :Parameters:

            default: optional
                Return the value of the *default* parameter if there
                is no quantize-on-write instruction.

                {{default Exception}}

        :Returns:

            `Quantization`
                The deleted quantize-on-write instruction in a
                quantization variable.

        """
        return self._del_component("quantize_on_write", default)

    def get_quantize_on_write(self, default=ValueError()):
        """TODOQ.

        .. versionadded:: (cfdm) NEXTVERSION

        :Parameters:

            default: optional
                Return the value of the *default* parameter if there
                is no quantize-on-write instruction.

                {{default Exception}}

        :Returns:

            `Quantization`
                The quantize-on-write instruction in a quantization
                variable.

        """
        return self._get_component("quantize_on_write", default)

    def set_quantize_on_write(
        self,
        quantization,
        quantization_nsd=None,
        quantization_nsb=None,
        copy=True,
    ):
        """Set a quantize-on-write instruction.

        A quantize-on-write instruction 

        .. versionadded:: (cfdm) NEXTVERSION

        .. seealso:: `get_quantization`, `get_quantize_on_write`,
                     `del_quantize_on_write`

        :Parameters:

            quantization: `Quantization`
                The quantize-on-write instruction in a quantization
                variable.

            quantization_nsd: `int` or `None`, optional
                If set to an integer, then set the "quantization_nsd"
                parameter of *quantization* to that value. Note that
                setting this parameter will automatically force *copy*
                to be True, regardless of its actual setting.

            quantization_nsb: `int` or `None`, optional
                If set to an integer, then set the "quantization_nsb"
                parameter of *quantization* to that value. Note that
                setting this parameter will automatically force *copy*
                to be True, regardless of its actual setting.

            copy: `bool`, optional
                If True (the default) then copy *quantization* prior
                to storing it in the `{{class}}` instance.

        :Returns:

            `None`

        """
        if self.get_quantization(None) is not None:
            raise ValueError(
                "Can't set a quantize-on-write instruction on a "
                f"{self.__class__.__name__} that is already quantised"
            )

        if copy:
            quantization = quantization.copy()

        algorithm = quantization.get_parameter("algorithm", None)
        parameter = quantization.algorithm_parameters().get(algorithm)

        if parameter is None:
            raise ValueError("TODOQ bad algorithm")

        if quantization_nsd is not None:
            if quantization_nsb is not None:
                raise ValueError(
                    "Can not set both keywords 'quantization_nsd' and "
                    "'quantization_nsb' at the same time"
                )

            if parameter != "quantization_nsd":
                raise ValueError(
                    f"Can only provide keyword {parameter!r} for "
                    f"quantization algorithm {algorithm!r}"
                )

            if not copy:
                # Copy anyway, because we're about to change it.
                q = quantization.copy()

            quantization.set_parameter(parameter, quantization_nsd, copy=False)
        elif quantization_nsb is not None:
            if parameter != "quantization_nsb":
                raise ValueError(
                    f"Can only provide keyword {parameter!r} for "
                    f"quantization algorithm {algorithm!r}"
                )

            if not copy:
                # Copy anyway, because we're about to change it.
                quantization = quantization.copy()

            quantization.set_parameter(parameter, quantization_nsb, copy=False)

        self._set_component("quantize_on_write", q, copy=False)
