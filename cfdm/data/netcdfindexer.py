import logging

import netCDF4
import numpy as np

_safecast = netCDF4.utils._safecast
_default_fillvals = netCDF4.default_fillvals

logger = logging.getLogger(__name__)


class NetCDFIndexer:
    """A data indexer that applies netCDF masking and unpacking.

    During indexing, masking and unpacking is applied according to the
    netCDF conventions, either or both of which may be disabled via
    initialisation options.

    The netCDF conventions assign special meaning to the following
    variable attributes: ``_FillValue``, ``missing_value``,
    ``_Unsigned``, ``valid_max``, ``valid_min``, and ``valid_range``
    (for masking); and ``add_offset`` and ``scale_factor`` (for
    unpacking).

    In addition, string and character variables are converted to
    unicode arrays, the latter with the last dimension concatenated.

    Adapted from `netCDF4`.

    .. versionadded:: (cfdm) HDFVER

    **Examples**

    >>> import netCDF4
    >>> nc = netCDF4.Dataset('file.nc', 'r')
    >>> x = cfdm.{{class}}(nc.variables['x'])
    >>> x.shape
    (12, 64, 128)
    >>> print(x[0, 0:4, 0:3])
    [[236.5, 236.2, 236.0],
     [240.9, --   , 239.6],
     [243.4, 242.4, 241.3],
     [243.1, 241.7, 240.4]]

    >>> import h5netcdf
    >>> h5 = h5netcdf.File('file.nc', 'r')
    >>> x = cfdm.{{class}}(h5.variables['x'])
    >>> x.shape
    (12, 64, 128)
    >>> print(x[0, 0:4, 0:3])
    [[236.5, 236.2, 236.0],
     [240.9, --   , 239.6],
     [243.4, 242.4, 241.3],
     [243.1, 241.7, 240.4]]

    >>> import numpy as np
    >>> n = np.arange(9)
    >>> x = cfdm.{{class}}(n)
    >>> x.shape
    (9,)
    >>> print(x[...])
    [1 2 3 4 5 6 7 8]
    >>> x = cfdm.{{class}}(n, attrs={'_FillValue': 4})
    >>> print(x[...])
    [1 2 3 -- 5 6 7 8]

    """

    def __init__(
        self, variable, mask=True, unpack=True, always_mask=False, attrs=None
    ):
        """**Initialisation**

        :Parameters:

            variable:
                The variable to be indexed, one of `netCDF4.Variable`,
                `h5netcdf.Variable`, or `numpy.ndarray`. Any masking
                and unpacking that could be implemented by applied by
                the *variable* itself is disabled, i.e. Any masking
                and unpacking is always applied by the
                `NetCDFIndexer` instance.

            mask: `bool`
                If True, the default, then an array returned by
                indexing is automatically converted to a masked array
                when missing values or fill values are present.

            unpack: `bool`
                If True, the default, then the ``scale_factor`` and
                ``add_offset`` are applied to an array returned by
                indexing, and signed integer data is automatically
                converted to unsigned integer data if the
                ``_Unsigned`` attribute is set to "true" or "True".

            always_mask: `bool`
                If False, the default, then an array returned by
                indexing which has no missing values is created as a
                regular numpy array. If True then an array returned by
                indexing is always a masked array, even if there are
                no missing values.

            attrs: `dict`, optional
                Provide the netCDF attributes of the *variable* as
                dictionary key/value pairs. If *attrs* is set then any
                netCDF attributes stored by *variable* itself are
                ignored.

        """
        self.variable = variable
        self.mask = mask
        self.unpack = unpack
        self.always_mask = always_mask
        self._attrs = attrs
        self.shape = variable.shape

    def __getitem__(self, index):
        """Return a subspace of the variable as a `numpy` array.

        v.__getitem__(index) <==> v[index]

        Indexing follows the rules defined by the variable.

        .. versionadded:: (cfdm) HDFVER

        """
        variable = self.variable
        unpack = self.unpack
        attrs = self.attrs()
        dtype = variable.dtype

        netCDF4_scale = False
        netCDF4_mask = False
        try:
            netCDF4_scale = variable.scale
        except AttributeError:
            pass
        else:
            netCDF4_mask = variable.mask
            # Prevent netCDF4 from doing any masking and scaling
            variable.set_auto_maskandscale(False)

        # Index the variable
        data = variable[index]

        if isinstance(data, str):
            data = np.array(data, dtype="S")
        elif data.dtype.kind in "OSU":
            kind = data.dtype.kind
            if kind == "S":
                data = netCDF4.chartostring(data)

            # Assume that object arrays are arrays of strings
            data = data.astype("S", copy=False)
            if kind == "O":
                dtype = data.dtype

        if dtype is str:
            dtype = data.dtype

        dtype_unsigned_int = None
        if unpack:
            is_unsigned_int = attrs.get("_Unsigned", False) in ("true", "True")
            if is_unsigned_int:
                data_dtype = data.dtype
                dtype_unsigned_int = (
                    f"{data_dtype.byteorder}u{data_dtype.itemsize}"
                )
                data = data.view(dtype_unsigned_int)

        if self.mask:
            attrs = self._set_FillValue(variable, attrs)
            data = self._mask(
                data,
                dtype,
                attrs,
                unpack=unpack,
                dtype_unsigned_int=dtype_unsigned_int,
            )

        if unpack:
            data = self._unpack(data, attrs)

        if data.dtype.kind == "S":
            data = data.astype("U", copy=False)

        # Reset a netCDF4 variables's scale and mask behaviour
        if netCDF4_scale:
            variable.set_auto_scale(True)

        if netCDF4_mask:
            variable.set_auto_mask(True)

        return data

    def _check_safecast(self, attname, dtype, attrs):
        """Check an attribute's data type.

        Checks to see that variable attribute exists and can be safely
        cast to variable data type.

        .. versionadded:: (cfdm) HDFVER

        :Parameter:

            attname: `str`
                The attribute name.

            dtype: `numpy.dtype`
                The variable data type.

            attrs: `dict`
                The variable attributes.

        :Returns:

            `bool`, value
                Whether or not the attribute data type is consistent
                with the variable data type, and the attribute value.

        """
        if attname in attrs:
            attvalue = attrs[attname]
            att = np.array(attvalue)
        else:
            return False, None

        is_safe = True
        try:
            atta = np.array(att, dtype)
        except ValueError:
            is_safe = False
        else:
            is_safe = _safecast(att, atta)

        if not is_safe:
            logger.warn(
                f"WARNING: Attribute {attname} not used since it can't "
                f"be safely cast to variable data type {dtype!r}"
            )  # pragma: no cover

        return is_safe, attvalue

    def _set_FillValue(self, variable, attrs):
        """Set the ``_FillValue`` from a `h5netcdf.Variable`.

        If the attributes already contain a ``_FillValue`` then
        nothing is done.

        .. versionadded:: (cfdm) HDFVER

        .. seealso:: `_default_FillValue`

        :Parameter:

            variable: `h5netcdf.Variable`
                The variable.

            attrs: `dict`
                The variable attributes. Will get updated in-place if
                a ``_FillValue`` is found.

        :Returns:

            `dict`
                The variable attributes, updated with ``_FillValue``
                if present and not previously set.

        """
        if "_FillValue" not in attrs:
            try:
                # h5netcdf
                _FillValue = getattr(variable._h5ds, "fillvalue", None)
            except AttributeError:
                # netCDf4
                pass
            else:
                if _FillValue is not None:
                    attrs["_FillValue"] = _FillValue

        return attrs

    def _default_FillValue(self, dtype):
        """Return the default ``_FillValue`` for the given data type.

        .. versionadded:: (cfdm) HDFVER

        .. seealso:: `_set_FillValue`, `netCDF4.default_fillvals`

        :Parameter:

            dtype: `numpy.dtype`
                The variable's data type

        :Returns:

                The default ``_FillValue``.

        """
        if dtype.kind in "OS":
            return _default_fillvals["S1"]
        else:
            return _default_fillvals[dtype.str[1:]]

    def _mask(
        self,
        data,
        dtype,
        attrs,
        unpack=True,
        dtype_unsigned_int=None,
    ):
        """Mask the data.

        .. versionadded:: (cfdm) HDFVER

        :Parameter:

            data: `numpy.ndarray`
                The unmasked and unpacked data indexed from the
                variable.

            dtype: `numpy.dtype`
                The data type of the variable (which may be different
                to that of *data*).

            attrs: `dict`
                The variable attributes.

            unpack: `bool`
                Whether the data is to be unpacked.

            dtype_unsigned_int: `dtype` or `None`
                The data type to which unsigned integer data has been
                cast. Should be `None` for data that are not unsigned
                integers.

        :Returns:

            `nump.ndarray`
                The masked (but not unpacked) data.

        """
        totalmask = np.zeros(data.shape, np.bool_)
        fill_value = None

        safe_missval, missing_value = self._check_safecast(
            "missing_value", dtype, attrs
        )
        if safe_missval:
            mval = np.array(missing_value, dtype)
            if unpack and dtype_unsigned_int is not None:
                mval = mval.view(dtype_unsigned_int)

            # Create mask from missing values.
            mvalmask = np.zeros(data.shape, np.bool_)
            if not mval.ndim:  # mval a scalar.
                mval = (mval,)  # Make into iterable.

            for m in mval:
                try:
                    mvalisnan = np.isnan(m)
                except TypeError:
                    # isnan fails on some dtypes
                    mvalisnan = False

                if mvalisnan:
                    mvalmask += np.isnan(data)
                else:
                    mvalmask += data == m

            if mvalmask.any():
                # Set fill_value for masked array to missing_value (or
                # first element if missing_value is a vector).
                fill_value = mval[0]
                totalmask += mvalmask

        # Set mask=True for data == fill value
        safe_fillval, _FillValue = self._check_safecast(
            "_FillValue", dtype, attrs
        )
        if not safe_fillval:
            _FillValue = self._default_FillValue(dtype)
            safe_fillval = True

        if safe_fillval:
            fval = np.array(_FillValue, dtype)
            if unpack and dtype_unsigned_int is not None:
                fval = fval.view(dtype_unsigned_int)

            try:
                fvalisnan = np.isnan(fval)
            except Exception:
                # isnan fails on some dtypes
                fvalisnan = False

            if fvalisnan:
                mask = np.isnan(data)
            elif (data == fval).any():
                mask = data == fval
            else:
                mask = None

            if mask is not None:
                if fill_value is None:
                    fill_value = fval

                totalmask += mask

        # Set mask=True for data outside [valid_min, valid_max]
        #
        # If valid_range exists use that, otherwise look for
        # valid_min, valid_max. No special treatment of byte data as
        # described in the netCDF documentation.
        validmin = None
        validmax = None
        safe_validrange, valid_range = self._check_safecast(
            "valid_range", dtype, attrs
        )
        safe_validmin, valid_min = self._check_safecast(
            "valid_min", dtype, attrs
        )
        safe_validmax, valid_max = self._check_safecast(
            "valid_max", dtype, attrs
        )
        if safe_validrange and valid_range.size == 2:
            validmin = np.array(valid_range[0], dtype)
            validmax = np.array(valid_range[1], dtype)
        else:
            if safe_validmin:
                validmin = np.array(valid_min, dtype)

            if safe_validmax:
                validmax = np.array(valid_max, dtype)

        if unpack:
            if validmin is not None and dtype_unsigned_int is not None:
                validmin = validmin.view(dtype_unsigned_int)

            if validmax is not None and dtype_unsigned_int is not None:
                validmax = validmax.view(dtype_unsigned_int)

        if dtype.kind != "S":
            # Don't set validmin/validmax mask for character data
            #
            # Setting valid_min/valid_max to the _FillVaue is too
            # surprising for many users (despite the netcdf docs
            # attribute best practices suggesting clients should do
            # this).
            if validmin is not None:
                totalmask += data < validmin

            if validmax is not None:
                totalmask += data > validmax

        # Mask the data
        if totalmask.any():
            data = np.ma.masked_array(data, mask=totalmask, fill_value=fval)
            if not data.ndim:
                # Return a scalar numpy masked constant not a 0-d
                # masked array, so that data == np.ma.masked.
                data = data[()]
        elif self.always_mask:
            data = np.ma.masked_array(data)

        return data

    def _unpack(self, data, attrs):
        """Unpack the data..

        .. versionadded:: (cfdm) HDFVER

        :Parameter:

            data: `numpy.ndarray`
                The unmasked and unpacked data indexed from the
                variable.

            attrs: `dict`
                The variable attributes.

        :Returns:

            `nump.ndarray`
                The unpacked data.

        """
        # If variable has scale_factor and add_offset attributes,
        # apply them.
        scale_factor = attrs.get("scale_factor")
        add_offset = attrs.get("add_offset")
        try:
            if scale_factor is not None:
                float(scale_factor)

            if add_offset is not None:
                float(add_offset)
        except ValueError:
            logging.warn(
                "Invalid scale_factor or add_offset attribute, "
                "no unpacking done."
            )  # pragma: no cover
            return data

        if scale_factor is not None and add_offset is not None:
            if add_offset != 0.0 or scale_factor != 1.0:
                data = data * scale_factor + add_offset
            else:
                data = data.astype(scale_factor.dtype)
        elif scale_factor is not None and scale_factor != 1.0:
            # If variable has only scale_factor attribute, rescale.
            data = data * scale_factor
        elif add_offset is not None and add_offset != 0.0:
            # If variable has only add_offset attribute, add offset.
            data = data + add_offset

        return data

    def attrs(self):
        """Return the netCDF attributes of the variable.

        .. versionadded:: (cfdm) HDFVER

        :Returns:

            `dict`
                The attributes.

        **Examples**

        >>> v.attrs()
        {'standard_name': 'air_temperature',
         'missing_value': -999.0}

        """
        if self._attrs is not None:
            return self._attrs.copy()

        variable = self.variable
        try:
            # h5netcdf
            return dict(variable.attrs)
        except AttributeError:
            try:
                # netCDF4
                return {
                    attr: variable.getncattr(attr)
                    for attr in variable.ncattrs()
                }
            except AttributeError:
                # numpy
                return {}
