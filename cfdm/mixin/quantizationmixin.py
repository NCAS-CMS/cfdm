class QuantizationMixin:
    """Mixin class for accessing quantization metadata.

    .. versionadded:: (cfdm) 1.12.2.0

    """

    def __initialise_from_source(self, source, copy=True):
        """Initialise quantization information from a source.

        This method is called by
        `_Container__parent_initialise_from_source`, which in turn is
        called by `cfdm.core.Container.__init__`.

        .. versionadded:: (cfdm) 1.12.2.0

        :Parameters:

            source:
                The object from which to extract the initialisation
                information. Typically, but not necessarily, a
                `{{class}}` object.

            copy: `bool`, optional
                If True (the default) then deep copy the
                initialisation information.

        :Returns:

            `None`

        """
        try:
            q = source.get_quantization(None)
        except (AttributeError, ValueError, TypeError):
            pass
        else:
            if q is not None:
                # No need to copy, because `get_quantization` already
                # returns a copy.
                self._set_component("quantization", q, copy=False)

        try:
            q = source.get_quantize_on_write(None)
        except (AttributeError, ValueError, TypeError):
            pass
        else:
            if q is not None:
                # No need to copy, because `get_quantize_on_write` already
                # returns a copy.
                self._set_component("quantize_on_write", q, copy=False)

    def _del_quantization(self, default=ValueError()):
        """Remove quantization metadata.

        Quantization eliminates false precision, usually by rounding
        the least significant bits of floating-point mantissas to
        zeros, so that a subsequent compression on disk is more
        efficient.

        Quantization metadata describes any existing quantization that
        has already been applied to the data. Removing the
        quantization metadata does not change the data in any way. If
        the data has in fact already been quantized, then it is up to
        the user to set new quantization metadata to describe this,
        with `_set_quantization`.

        .. versionadded:: (cfdm) 1.12.2.0

        .. seealso:: `get_quantization`, `_set_quantization`,
                     `del_quantize_on_write`

        :Parameters:

            default: optional
                Return the value of the *default* keyword if there is
                no quantization metadata.

                {{default Exception}}

        :Returns:

            `Quantization`
                The deleted quantization metadata.

        **Examples**

        >>> f.get_quantization()
        <{{repr}}Quantization: algorithm=bitgroom, quantization_nsd=4>
        >>> q = f._del_quantization()
        >>> print(f.get_quantization(None))
        None
        >>> f._set_quantization(q)
        >>> f.get_quantization(None)
        <{{repr}}Quantization: algorithm=bitgroom, quantization_nsd=4>

        """
        return self._del_component("quantization", default)

    def _set_quantization(self, quantization, copy=True):
        """Set quantization metadata.

        Quantization eliminates false precision, usually by rounding
        the least significant bits of floating-point mantissas to
        zeros, so that a subsequent compression on disk is more
        efficient.

        Quantization metadata describes any existing quantization that
        has already been applied to the data. Any existing
        quantization metadata are automatically removed prior to the
        new setting. Setting quantization metadata does not change the
        data in any way, and will not cause the data to be quantized
        when written to a netCDF dataset. It is up to the user to
        ensure that the new quantization metadata is consistent with
        the data, i.e. that the data has in fact been quantized in the
        manner described by the new quantization metadata.

        .. versionadded:: (cfdm) 1.12.2.0

        .. seealso:: `get_quantization`, `_del_quantization`,
                     `set_quantize_on_write`

        :Parameters:

            quantization: `Quantization`
                The new quantization metadata.

            copy: `bool`, optional
                If True (the default) then copy *quantization* prior
                to insertion.

        :Returns:

            `None`

        **Examples**

        >>> f.get_quantization()
        <{{repr}}Quantization: algorithm=bitgroom, quantization_nsd=4>
        >>> q = f._del_quantization()
        >>> print(f.get_quantization(None))
        None
        >>> f._set_quantization(q)
        >>> f.get_quantization()
        <{{repr}}Quantization: algorithm=bitgroom, quantization_nsd=4>

        """
        q_on_w = self.get_quantize_on_write(None)
        if q_on_w is not None:
            raise ValueError(
                "Can't set quantization metadata on a "
                f"{self.__class__.__name__} that has a quantize-on-write "
                f"instruction: {q_on_w!r}"
            )

        if copy:
            quantization = quantization.copy()

        return self._set_component("quantization", quantization, copy=False)

    def del_quantize_on_write(self, default=ValueError()):
        """Remove a quantize-on-write instruction.

        Quantization eliminates false precision, usually by rounding
        the least significant bits of floating-point mantissas to
        zeros, so that a subsequent compression on disk is more
        efficient.

        The existence of a quantize-on-write instruction does not mean
        that the data in memory has been quantized, rather it means
        that if the data is written to a netCDF dataset with
        `{{package}}.write`, then quantization will be applied to the
        data in the netCDF dataset on disk, leaving the data in memory
        unchanged. Removing a quantize-on-write instruction means that
        the data will not be quantized when written to disk.

        Removing a quantize-on-write instruction means that the data
        will not be quantized when written to disk.

        .. versionadded:: (cfdm) 1.12.2.0

        .. seealso:: `get_quantize_on_write`, `set_quantize_on_write`,
                     `_del_quantization`

        :Parameters:

            default: optional
                Return the value of the *default* keyword if there is
                no quantize-on-write instruction.

                {{default Exception}}

        :Returns:

            `Quantization`
                The deleted quantize-on-write instruction.

        **Examples**

        >>> f.set_quantize_on_write(algorithm='bitgroom', quantization_nsd=6)
        >>> f.get_quantize_on_write()
        <{{repr}}Quantization: algorithm=bitgroom, quantization_nsd=6>
        >>> q = f.del_quantize_on_write()
        >>> print(f.get_quantize_on_write(None))
        None

        """
        return self._del_component("quantize_on_write", default)

    def get_quantization(self, default=ValueError()):
        """Get quantization metadata.

        Quantization eliminates false precision, usually by rounding
        the least significant bits of floating-point mantissas to
        zeros, so that a subsequent compression on disk is more
        efficient.

        Quantization metadata describes any existing quantization that
        has already been applied to the data.

        .. versionadded:: (cfdm) 1.12.2.0

        .. seealso:: `_del_quantization`, `_set_quantization`,
                     `get_quantize_on_write`

        :Parameters:

            default: optional
                Return the value of the *default* keyword if there is
                no quantization metadata.

                {{default Exception}}

        :Returns:

            `Quantization`
                A copy of quantization metadata.

        **Examples**

        >>> f.get_quantization()
        <{{repr}}Quantization: algorithm=bitgroom, quantization_nsd=4>
        >>> q = f._del_quantization()
        >>> print(f.get_quantization(None))
        None
        >>> f._set_quantization(q)
        >>> f.get_quantization()
        <{{repr}}Quantization: algorithm=bitgroom, quantization_nsd=4>

        """
        q = self._get_component("quantization", None)
        if q is None:
            if default is None:
                return

            return self._default(
                default,
                message=(
                    f"{self.__class__.__name__} has no "
                    "quantization metadata"
                ),
            )

        return q.copy()

    def get_quantize_on_write(self, default=ValueError()):
        """Get a quantize-on-write instruction.

        Quantization eliminates false precision, usually by rounding
        the least significant bits of floating-point mantissas to
        zeros, so that a subsequent compression on disk is more
        efficient.

        The existence of a quantize-on-write instruction does not mean
        that the data in memory has been quantized, rather it means
        that if the data is written to a netCDF dataset with
        `{{package}}.write`, then quantization will be applied to the
        data in the netCDF dataset on disk, leaving the data in memory
        unchanged.

        .. versionadded:: (cfdm) 1.12.2.0

        .. seealso:: `set_quantize_on_write`, `del_quantize_on_write`,
                     `get_quantization`

        :Parameters:

            default: optional
                Return the value of the *default* keyword if there is
                no quantize-on-write instruction.

                {{default Exception}}

        :Returns:

            `Quantization`
                A copy of the quantize-on-write instruction.

        **Examples**

        >>> f.set_quantize_on_write(algorithm='bitgroom', quantization_nsd=6)
        >>> f.get_quantize_on_write()
        <{{repr}}Quantization: algorithm=bitgroom, quantization_nsd=6>
        >>> q = f.del_quantize_on_write()
        >>> print(f.get_quantize_on_write(None))
        None

        """
        q = self._get_component("quantize_on_write", None)
        if q is None:
            if default is None:
                return

            return self._default(
                default,
                message=(
                    f"{self.__class__.__name__} has no "
                    "quantize-on-write instruction"
                ),
            )

        return q.copy()

    def set_quantize_on_write(
        self,
        quantization=None,
        algorithm=None,
        quantization_nsd=None,
        quantization_nsb=None,
    ):
        """Set a quantize-on-write instruction.

        Quantization eliminates false precision, usually by rounding
        the least significant bits of floating-point mantissas to
        zeros, so that a subsequent compression on disk is more
        efficient.

        The existence of a quantize-on-write instruction does not mean
        that the data in memory has been quantized, rather it means
        that if the data is written to a netCDF dataset with
        `{{package}}.write`, then quantization will be applied to the
        data in the netCDF dataset on disk, leaving the data in memory
        unchanged.

        An existing quantization-on-write instruction is removed prior
        to the new setting.

        .. versionadded:: (cfdm) 1.12.2.0

        .. seealso:: `get_quantize_on_write`, `del_quantize_on_write`,
                     `_set_quantization`

        :Parameters:

            quantization: `Quantization` or `None`, optional
                The quantize-on-write instructions. By default, or if
                `None`, a `Quantization` objects with no parameters is
                used.

                Its parameters may be overridden by the *algorithm*,
                *quantization_nsd* or *quantization_nsb* keywords. If
                the "implementation" parameter is defined then it is
                removed (because it will get reset during a subsequent
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

        Use the quantization metadata from another construct,
        overriding its per-variable quantization parameter:

        >>> q = g.get_quantization()
        >>> f.set_quantize_on_write(q, quantization_nsd=13)

        """
        qm = self.get_quantization(None)
        if qm is not None:
            raise ValueError(
                "Can't set a quantize-on-write instruction on a "
                f"{self.__class__.__name__} that has quantization metadata: "
                f"{qm!r}"
            )

        if quantization is None:
            q = self._Quantization()
        else:
            q = quantization.copy()
            q.del_parameter("implementation", None)

        if algorithm is not None:
            # Override the algorithm parameter
            q.set_parameter("algorithm", algorithm, copy=False)
        else:
            algorithm = q.get_parameter("algorithm", None)

        # Get the parameter name associated with this algorithm
        parameter = q.algorithm_parameters().get(algorithm)
        if parameter is None:
            raise ValueError(
                "Invalid quantization algorithm: {algorithm!r}. "
                f"Must be one of {tuple(q.algorithm_parameters())}"
            )

        if quantization_nsd is not None:
            # Override the quantization_nsd parameter
            if quantization_nsb is not None:
                raise ValueError(
                    "Can't set keywords 'quantization_nsd' and "
                    "'quantization_nsb' at the same time"
                )

            if parameter != "quantization_nsd":
                raise ValueError(
                    f"Can set keyword {parameter!r} for "
                    f"quantization algorithm {algorithm!r}"
                )

            q.set_parameter(parameter, quantization_nsd)
        elif quantization_nsb is not None:
            # Override the quantization_nsb parameter
            if parameter != "quantization_nsb":
                raise ValueError(
                    f"Can't set keyword {parameter!r} for "
                    f"quantization algorithm {algorithm!r}"
                )

            q.set_parameter(parameter, quantization_nsb)

        self._set_component("quantize_on_write", q, copy=False)
