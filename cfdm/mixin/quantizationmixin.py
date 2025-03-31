class QuantizationMixin:
    """Mixin class for access to quantization metdata.

    .. versionadded:: (cfdm) NEXTVERSION

    """

    def __initialise(self, source, copy=True):
        """Initialise quantization information from a source.

        Intended to be called by `_parent_initialise_from_source`.

        .. versionadded:: (cfdm) NEXTVERSION

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

        .. warning:: Removing quantization metadata does not change
                     the actual quantization (if any) of the data.

        .. versionadded:: (cfdm) NEXTVERSION

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

        """
        return self._del_component("quantization", default)

    def _set_quantization(self, quantization, copy=True):
        """Set quantization metadata.

        Any existing quantization metadata removed prior to the new
        setting.

        .. warning:: Setting quantization metadata does not change the
                     actual quantization (if any) of the data, and
                     will not cause the data to be quantized when
                     written to a netCDF dataset.

        .. versionadded:: (cfdm) NEXTVERSION

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

        See `set_quantize_on_write` for details.

        .. versionadded:: (cfdm) NEXTVERSION

        .. seealso:: `get_quantize_on_write`, `set_quantize_on_write`,
                     `_del_quantization`

        :Parameters:

            default: optional
                Return the value of the *default* keyword if there is
                no quantize-on-write instruction.

                {{default Exception}}

        :Returns:

            `Quantization`
                The deleted quantize-on-write instruction in a
                quantization variable.

        """
        return self._del_component("quantize_on_write", default)

    def get_quantization(self, default=ValueError()):
        """Get quantization metadata.

        .. versionadded:: (cfdm) NEXTVERSION

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

        See `set_quantize_on_write` for details.

        .. versionadded:: (cfdm) NEXTVERSION

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

        .. note:: Setting a quantize-on-write instruction does not
                  immediately change the data, but if the `{{class}}`
                  is written to a netCDF dataset with
                  `{{package}}.write`, then the quantization will be
                  applied at that time to the data on disk, leaving
                  the construct's data in memory unchanged.

        .. versionadded:: (cfdm) NEXTVERSION

        .. seealso:: `get_quantize_on_write`, `del_quantize_on_write`,
                     `_set_quantization`

        :Parameters:

            quantization: `Quantization` or `None`, optional
                The quantize-on-write instruction in a quantization
                variable. By default, or if `None`, a `Quantization`
                with no parameters is used.

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

        Use the quantization metadata from another construct,
        overriding its per-variable quantization parameter:

        >>> q = g.get_quantization()
        >>> f.set_quantize_on_write(q, quantization_nsd=13))

        """
        qm = self.get_quantization(None)
        if qm is not None:
            raise ValueError(
                "Can't set a quantize-on-write instruction on a "
                f"{self.__class__.__name__} that has quantization metadata: "
                f"{qm!r}"
            )

        if quantization is None:
            # Note: A parent class must define the `_Quantization`
            #       attribute as its quantization class.
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
