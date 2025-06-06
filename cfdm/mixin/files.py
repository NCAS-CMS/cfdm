from ..functions import abspath


class Files:
    """Mixin class for storing simple netCDF elements.

    .. versionadded:: (cfdm) 1.10.0.1

    """

    def __initialise_from_source(self, source=None, copy=True):
        """Initialise original file names from a source.

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
            f = source._get_component("original_filenames", None)
        except AttributeError:
            pass
        else:
            if f is not None:
                # No need to copy, because 'f' will be a `tuple` of
                # `str`.
                self._set_component("original_filenames", f, copy=False)

    def _original_filenames(self, define=None, update=None, clear=False):
        """The names of files containing the original data and metadata.

        {{original filenames}}

        .. versionadded:: (cfdm) 1.10.0.1

        .. seealso:: `get_original_filenames`

        :Parameters:

            {{define: (sequence of) `str`, optional}}

            {{update: (sequence of) `str`, optional}}

            {{clear: `bool` optional}}

        :Returns:

            `set` or `None`
                {{Returns original filenames}}

                If the *define* or *update* parameter is set then
                `None` is returned.

        **Examples**

        >>> d = {{package}}.{{class}}(9)
        >>> d._original_filenames()
        ()
        >>> d._original_filenames(define="file1.nc")
        >>> d._original_filenames()
        ('/data/user/file1.nc',)
        >>> d._original_filenames(update=["file1.nc"])
        >>> d._original_filenames()
        ('/data/user/file1.nc',)
        >>> d._original_filenames(update="file2.nc")
        >>> d._original_filenames()
        ('/data/user/file1.nc', '/data/user/file2.nc')
        >>> d._original_filenames(define="file3.nc")
        >>> d._original_filenames()
        ('/data/user/file3.nc',)
        >>> d._original_filenames(clear=True)
        >>> d._original_filenames()
        ()

        """
        filenames = None

        if define:
            # Replace the existing collection of original file names
            if isinstance(define, str):
                define = (define,)

            filenames = tuple([abspath(name) for name in define])

        if update:
            # Add new original file names to the existing collection
            if define is not None:
                raise ValueError(
                    "Can't set the 'define' and 'update' parameters "
                    "at the same time"
                )

            filenames = self._get_component("original_filenames", ())
            if isinstance(update, str):
                update = (update,)

            filenames += tuple([abspath(name) for name in update])

        if filenames:
            if len(filenames) > 1:
                filenames = tuple(set(filenames))

            self._set_component("original_filenames", filenames, copy=False)

        if define is not None or update is not None:
            if clear:
                raise ValueError(
                    "Can't set the 'clear' parameter with either of the "
                    "'define' and 'update' parameters"
                )

            # Return None, having potentially changed the file names
            return

        # Still here? Then return the existing original file names
        if clear:
            return set(self._del_component("original_filenames", ()))

        return set(self._get_component("original_filenames", ()))

    def get_original_filenames(self):
        """The names of files containing the original data and metadata.

        {{original filenames}}

        .. versionadded:: (cfdm) 1.10.0.1

        :Returns:

            `set`
                {{Returns original filenames}}

        """
        return self._original_filenames()
