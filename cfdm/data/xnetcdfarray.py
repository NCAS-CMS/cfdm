import logging

from . import abstract
from .locks import netcdf_lock, no_lock
from .mixin import IndexMixin
from .netcdfindexer import netcdf_indexer

logger = logging.getLogger(__name__)


class XnetcdfArray(IndexMixin, abstract.FileArray):
    """A netCDF array accessed with `xnetcdf`.

    .. versionadded:: (cfdm) 1.13.3.0

    """

    @property
    def _lock(self):
        """Return a lock for dataset array access.

        .. versionadded:: (cfdm) 1.13.3.0

        :Returns:

            `threading.Lock` or `contextlib.nullcontext`
                For those backends which require it (i.e. 'netCDF4'
                and 'h5py'), returns a `threading.Lock` object that
                prevents concurrent reads of the dataset.

                For all other backends, the returned lock is a
                `contextlib.nullcontext` object which does no locking.

        """
        # Get the backend, if possible.
        variable = self.get_variable(None)
        if variable is not None:
            backend = variable.backend_api
        else:
            backend = self.get_backend()
            if not isinstance(backend, str):
                backend = None

        # Choose the lock based on the backend
        match backend:
            case "netCDF4" | "h5py" | "xarray" | None:
                return netcdf_lock
            case _:
                return no_lock

    def _attributes(self, var):
        """Get the variable attributes.

        If the attributes have not been set, then they are retrieved
        from the *var* and cached for fast future access.

        .. versionadded:: (cfdm) 1.12.0.0

        .. seealso:: `get_attributes`

        :Parameters:

            var: `xnetcdf.Variable`
                The variable.

        :Returns:

            `dict`
                The attributes. The returned attributes are not a copy
                of the cached dictionary.

        """
        attributes = self._get_component("attributes", None)
        if attributes is None:
            attributes = var.attrs.copy()
            self._set_component("attributes", attributes, copy=False)

        return attributes

    def _get_array(self, index=None):
        """Returns a subspace of the dataset variable.

        The subspace is defined by the `index` attributes, and is
        applied with `cfdm.netcdf_indexer`.

        .. versionadded:: (cfdm) 1.13.3.0

        .. seealso:: `__array__`, `index`

        :Parameters:

            {{index: `tuple` or `None`, optional}}

        :Returns:

            `numpy.ndarray`
                The subspace.

        """
        if index is None:
            index = self.index()

        with self._lock:
            dataset = None
            variable = self.get_variable(None)
            if variable is None:
                dataset, path = self.open()
                variable = dataset[path]

            # Get the data, applying masking and scaling as required.
            array = netcdf_indexer(
                variable,
                mask=self.get_mask(),
                unpack=self.get_unpack(),
                always_masked_array=False,
                orthogonal_indexing=True,
                attributes=self._attributes(variable),
                copy=False,
            )
            array = array[index]

            # Close the dataset if it is local
            if variable.is_local:
                self.close(variable.root)

        return array

    def close(self, dataset):
        """Close the dataset containing the data.

        .. versionadded:: (cfdm) 1.13.3.0

        :Parameters:

            dataset: `xnetcdf.Dataset`
                The netCDF dataset to be closed.

        :Returns:

            `None`

        """
        if self._get_component("close"):
            dataset.close()

    def open(self, **kwargs):
        """Return a dataset object and address.

        .. versionadded:: (cfdm) 1.13.3.0

        :Parameters:

            kwargs: optional
                Extra keyword arguments to `xnetcdf.Dataset`.

        :Returns:

            (`xnetcdf.Dataset`, `str`)
                The open file object, and the address of the data
                within the file.

        """
        import xnetcdf

        backend = self.get_backend()
        options = {"backend": backend} | self.get_backend_options() | kwargs

        out = None
        try:
            out = super().open(xnetcdf.Dataset, options=options)
        except Exception as e:
            error = [str(e)]

            # As a last resort, try opening an http dataset with
            # OPeNDAP via netCDF4. (Currently, the only backend that
            # can use OPeNDAP is 'netCDF4'.)
            try_opendap = self.get_filesystem() is None
            if backend is None or backend == "netCDF4" or "netCDF4" in backend:
                filename = self.get_filename()
                if isinstance(filename, str):
                    from urllib.parse import urlparse

                    try_opendap = urlparse(filename).scheme in (
                        "http",
                        "https",
                    )

            if try_opendap:
                options["backend"] = "netCDF4"
                try:
                    out = super().open(
                        xnetcdf.Dataset,
                        options=options,
                        create_filesystem=False,
                    )
                except Exception as e:
                    error.append(str(e))

            if out is None:
                raise type(e)("\n\n".join(error))

        return out
