class QuantizationWriteMixin:
    """Mixin class for constructs that allow quantize-on-write.

    .. versionadded:: (cfdm) NEXTVERSION

    """

    def del_quantize_on_write(self, default=ValueError()):
        """Remove a quantize-on-write instruction.

        See `set_quantize_on_write` for details.

        .. versionadded:: (cfdm) NEXTVERSION

        .. seealso:: `get_quantization`, `get_quantize_on_write`,
                     `set_quantize_on_write`

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
        """Get a quantize-on-write instruction.

        See `set_quantize_on_write` for details.

        .. versionadded:: (cfdm) NEXTVERSION

        .. seealso:: `get_quantization`, `set_quantize_on_write`,
                     `del_quantize_on_write`

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
        quantization=None,
        algorithm=None,
        quantization_nsd=None,
        quantization_nsb=None,
    ):
        """Set a quantize-on-write instruction.

        Calling `set_quantize_on_write` does not immediataely change
        the data, but if the {{class}} is written to a netCDF dataset
        with `{{package}}.write` then the quantization will be applied
        to its data on disk, leaving the construct's data in memory
        unchanged.

        .. versionadded:: (cfdm) NEXTVERSION

        .. seealso:: `get_quantization`, `get_quantize_on_write`,
                     `del_quantize_on_write`

        :Parameters:

            quantization: `Quantization` or `None`, optional
                The quantize-on-write instruction in a quantization
                variable. By default, or if `None`, an empty
                `Quantization` component is used.

                Its parameters may be overridden by the *algorithm*,
                *quantization_nsd* or *quantization_nsb* keywords. If
                the "implementation" parameter is defined then it is
                removed (because it will get reset during a future
                call to `{{package}}.write`).

            algorithm: `str` or `None`, optional
                Set the "algorithm" parameter of *quantization*.

            quantization_nsd: `int` or `None`, optional
                Set the "quantization_nsd" parameter of
                *quantization*.

            quantization_nsb: `int` or `None`, optional
                Set the "quantization_nsb" parameter of
                *quantization*.

        :Returns:

            `None`

        **Examples**

        >>> f.set_quantize_on_write(algorithm='bitgroom', quantization_nsd=6)

        >>> q = {{package}}.Quantization({'algorithm': 'bitgroom',
        ...                               'quantization_nsd': 6})
        >>> f.set_quantize_on_write(q)

        Use the quantization component from another construct,
        overriding its per-variable quantization parameter:

        >>> q = g.get_quantization()
        >>> f.set_quantize_on_write(q, 'quantization_nsd': 6}))

        """
        if self.get_quantization(None) is not None:
            raise ValueError(
                "Can't set a quantize-on-write instruction on a "
                f"{self.__class__.__name__} that is already quantized"
            )

        q = quantization.copy()

        q.del_parameter("implementation", None)

        algorithm = q.get_parameter("algorithm", None)
        parameter = q.algorithm_parameters().get(algorithm)

        if parameter is None:
            raise ValueError(
                "Must provide a quantization algorthm with the "
                "'quantization' or 'algorithm' keywords "
            )

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

            q.set_parameter(parameter, quantization_nsd, copy=False)
        elif quantization_nsb is not None:
            if parameter != "quantization_nsb":
                raise ValueError(
                    f"Can only provide keyword {parameter!r} for "
                    f"quantization algorithm {algorithm!r}"
                )

            q.set_parameter(parameter, quantization_nsb, copy=False)

        self._set_component("quantize_on_write", q, copy=False)
