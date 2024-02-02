import logging

import netCDF4
import numpy as np

_safecast = netCDF4.utils._safecast
default_fillvals = netCDF4.default_fillvals

logger = logging.getLogger(__name__)


class VariableIndexer:
    """An indexer of netCDF variables that applies masking and scaling.

    During indexing, masking and scaling is applied according to the
    CF conventions, either of which may be disabled via initialisation
    options.

    String and character variables are converted to unicode arrays,
    the latter with the last dimension concatenated.

    .. versionadded:: (cfdm) HDFVER

    **Examples**

    >>> nc = netCDF4.Dataset('file.nc', 'r')
    >>> x = cfdm.VariableIndexer(nc.variables['x'])
    >>> x.shape
    (12, 64, 128)
    >>> print(x[0, 0:4, 0:3])
    [[236.5, 236.2, 236.0],
     [240.9, --   , 239.6],
     [243.4, 242.4, 241.3],
     [243.1, 241.7, 240.4]]

    >>> h5 = h5netcdf.File('file.nc', 'r')
    >>> x = cfdm.VariableIndexer(h5.variables['x'])
    >>> x.shape
    (12, 64, 128)
    >>> print(x[0, 0:4, 0:3])
    [[236.5, 236.2, 236.0],
     [240.9, --   , 239.6],
     [243.4, 242.4, 241.3],
     [243.1, 241.7, 240.4]]

    """

    def __init__(self, variable, mask=True, scale=True, always_masked=False):
        """**Initialisation**

        :Parameters:

            variable: `netCDF4.Variable` or `h5netcdf.Variable`
                The variable to be indexed. Any masking and scaling
                that may be applied by the *variable* itself is
                disabled, i.e. Any masking and scaling is always
                applied by the `VariableIndexer` instance.

            mask: `bool`
                If True, the default, then an array returned by
                indexing is automatically converted to a masked array
                when missing values or fill values are present.

            scale: `bool`
                If True, the default, then the ``scale_factor`` and
                ``add_offset`` are applied to an array returned by
                indexing, and signed integer data is automatically
                converted to unsigned integer data if the
                ``_Unsigned`` attribute is set to "true" or "True".

            always_masked: `bool`
                If False, the default, then an array returned by
                indexing which has no missing values is created as a
                regular numpy array. If True then an array returned by
                indexing is always a masked array, even if there are
                no missing values.

        """
        self.variable = variable
        self.mask = mask
        self.scale = scale
        self.always_masked = always_masked

        self.shape = variable.shape

    def __getitem__(self, index):
        """Return a subspace of the variable as a `numpy` array.

        v.__getitem__(index) <==> v[index]

        Indexing follows rules defined by the variable.

        .. versionadded:: (cfdm) HDFVER

        """
        variable = self.variable
        scale = self.scale

        attrs = self._attrs(variable)
        dtype = variable.dtype

        netCDF4_scale = False
        netCDF4_mask = False
        try:
            netCDF4_scale = variable.scale
            netCDF4_mask = variable.mask
        except AttributeError:
            pass
        else:
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

        if scale:
            dtype_unsigned_int = None
            is_unsigned_int = attrs.get("_Unsigned", False) in ("true", "True")
            if is_unsigned_int:
                data_dtype = data.dtype
                dtype_unsigned_int = (
                    f"{data_dtype.byteorder}u{data_dtype.itemsize}"
                )
                data = data.view(dtype_unsigned_int)

        if self.mask:
            attrs = self._FillValue(variable, attrs)
            data = self._mask(
                data,
                dtype,
                attrs,
                scale=scale,
                always_masked=self.always_masked,
                dtype_unsigned_int=dtype_unsigned_int,
            )

        if scale:
            data = self._scale(data, attrs)

        if data.dtype.kind == "S":
            # Assume that object arrays contain strings
            data = data.astype("U", copy=False)

        if netCDF4_scale:
            variable.set_auto_scale(True)

        if netCDF4_mask:
            variable.set_auto_mask(True)

        return data

    def _attrs(self, variable):
        """Return the variable attributes.

        .. versionadded:: (cfdm) HDFVER

        :Parameter:

            variable: `netCDF4.Variable` or `h5netcdf.Variable`
                The variable to be indexed.

        :Returns:

            `dict`
                The attributes.

        """
        try:
            # h5netcdf
            return dict(variable.attrs)
        except AttributeError:
            # netCDF4
            return {
                attr: variable.getncattr(attr) for attr in variable.ncattrs()
            }

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
                f"WARNING: {attname} not used since it cannot "
                "be safely cast to variable data type {dtype!r}"
            )  # pragma: no cover

        return is_safe, attvalue

    def _FillValue(self, variable, attrs):
        """Set the variable _FillValue.

        .. versionadded:: (cfdm) HDFVER

        :Parameter:

            variable: `netCDF4.Variable` or `h5netcdf.Variable`
                The variable to be indexed.

            attrs: `dict`
                The variable attributes. May get updated in-place.

        :Returns:

            `dict`
                The variable attributes, updated in-place with
                ``_FillValue`` if present and not previously set..

        """
        if "_FillValue" not in attrs:
            try:
                fillvalue = getattr(variable._h5ds, "fillvalue", None)
            except AttributeError:
                # netCDf4
                pass
            else:
                # h5netcdf
                if fillvalue is not None:
                    attrs["_FillValue"] = fillvalue
                elif variable.dtype.kind == "O":
                    attrs["_FillValue"] = default_fillvals["S1"]

        return attrs

    def _mask(
        self,
        data,
        dtype,
        attrs,
        scale=True,
        always_masked=False,
        dtype_unsigned_int=None,
    ):
        """Mask the data.

        .. versionadded:: (cfdm) HDFVER

        :Parameter:

            data: `numpy.ndarray`
                The unmasked and unscaled data indexed from the
                variable.

            dtype: `numpy.dtype`
                The data type of the variable (which may be different
                to that of *data*).

            attrs: `dict`
                The variable attributes.

            scale: `bool`
                Whether the data is to be scaled.

            always_masked: `bool`
                Whether or not return a regular numpy array when there
                are no missing values.

            dtype_unsigned_int: `dtype` or `None`
                The data type to which unsigned integer data has been
                cast.

        :Returns:

            `nump.ndarray`
                The masked (but not scaled) data.

        """
        totalmask = np.zeros(data.shape, np.bool_)
        fill_value = None

        safe_missval, missing_value = self._check_safecast(
            "missing_value", dtype, attrs
        )
        if safe_missval:
            mval = np.array(missing_value, dtype)
            if scale and dtype_unsigned_int is not None:
                mval = mval.view(dtype_unsigned_int)

            # create mask from missing values.
            mvalmask = np.zeros(data.shape, np.bool_)
            if not mval.ndim:  # mval a scalar.
                mval = (mval,)  # make into iterable.

            for m in mval:
                # is scalar missing value a NaN?
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
                # 1st element if missing_value is a vector).
                fill_value = mval[0]
                totalmask += mvalmask

        # set mask=True for data == fill value
        safe_fillval, _FillValue = self._check_safecast(
            "_FillValue", dtype, attrs
        )
        if safe_fillval:
            fval = np.array(_FillValue, dtype)
            if scale and dtype_unsigned_int is not None:
                fval = fval.view(dtype_unsigned_int)

            # is _FillValue a NaN?
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
        else:
            # Don't return masked array if variable filling is disabled.
            no_fill = 0
            #                with nogil:
            #                    ierr = nc_inq_var_fill(self._grpid,self._varid,&no_fill,NULL)
            #                _ensure_nc_success(ierr)

            # if no_fill is not 1, and not a byte variable, then use
            # default fill value.  from
            # http://www.unidata.ucar.edu/software/netcdf/docs/netcdf-c/Fill-Values.html#Fill-Values
            # "If you need a fill value for a byte variable, it is
            # recommended that you explicitly define an appropriate
            # _FillValue attribute, as generic utilities such as
            # ncdump will not assume a default fill value for byte
            # variables."  Explained here too:
            # http://www.unidata.ucar.edu/software/netcdf/docs/known_problems.html#ncdump_ubyte_fill
            # "There should be no default fill values when reading any
            # byte type, signed or unsigned, because the byte ranges
            # are too small to assume one of the values should appear
            # as a missing value unless a _FillValue attribute is set
            # explicitly."  (do this only for non-vlens, since vlens
            # don't have a default _FillValue)
            if no_fill != 1 or dtype.str[1:] not in ("u1", "i1"):
                if dtype.kind == "S":
                    default_fillval = default_fillvals["S1"]
                else:
                    default_fillval = default_fillvals[dtype.str[1:]]

                fillval = np.array(default_fillval, dtype)
                has_fillval = data == fillval
                # if data is an array scalar, has_fillval will be a
                # boolean.  in that case convert to an array.
                #                if type(has_fillval) == bool:
                if isinstance(has_fillval, bool):
                    has_fillval = np.asarray(has_fillval)

                if has_fillval.any():
                    if fill_value is None:
                        fill_value = fillval

                    mask = data == fillval
                    totalmask += mask

        # Set mask=True for data outside [valid_min, valid_max]
        validmin = None
        validmax = None
        # If valid_range exists use that, otherwise look for
        # valid_min, valid_max. No special treatment of byte data as
        # described at
        # http://www.unidata.ucar.edu/software/netcdf/docs/attribute_conventions.html).
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

        if scale:
            if validmin is not None and dtype_unsigned_int is not None:
                validmin = validmin.view(dtype_unsigned_int)

            if validmax is not None and dtype_unsigned_int is not None:
                validmax = validmax.view(dtype_unsigned_int)

        # http://www.unidata.ucar.edu/software/netcdf/docs/attribute_conventions.html).
        # "If the data type is byte and _FillValue is not explicitly
        # defined, then the valid range should include all possible
        # values.  Otherwise, the valid range should exclude the
        # _FillValue (whether defined explicitly or by default) as
        # follows. If the _FillValue is positive then it defines a
        # valid maximum, otherwise it defines a valid minimum."
        if safe_fillval:
            fval = np.array(_FillValue, dtype)
        else:
            k = dtype.str[1:]
            if k in ("u1", "i1"):
                fval = None
            else:
                if dtype.kind == "S":
                    default_fillval = default_fillvals["S1"]
                else:
                    default_fillval = default_fillvals[k]

                fval = np.array(default_fillval, dtype)

        if dtype.kind != "S":
            # Don't set validmin/validmax mask for character data

            # Setting valid_min/valid_max to the _FillVaue is too
            # surprising for many users (despite the netcdf docs
            # attribute best practices suggesting clients should do
            # this).
            if validmin is not None:
                totalmask += data < validmin

            if validmax is not None:
                totalmask += data > validmax

        if fill_value is None and fval is not None:
            fill_value = fval

        # If all else fails, use default _FillValue as fill_value for
        # masked array.
        if fill_value is None:
            if dtype.kind == "S":
                fill_value = default_fillvals["S1"]
            else:
                fill_value = default_fillvals[dtype.str[1:]]

        # Create masked array with computed mask
        masked_values = totalmask.any()
        if masked_values:
            data = np.ma.masked_array(
                data, mask=totalmask, fill_value=fill_value
            )
        else:
            # Always return masked array, if no values masked.
            data = np.ma.masked_array(data)

        # Scalar array with mask=True should be converted to
        # np.ma.MaskedConstant to be consistent with slicing
        # behavior of masked arrays.
        if data.shape == () and data.mask.all():
            # Return a scalar numpy masked constant not a 0-d masked
            # array, so that data == np.ma.masked.
            data = data[()]

        elif not always_masked and not masked_values:
            # Return a regular numpy array if requested and there are
            # no missing values
            data = np.array(data, copy=False)

        return data

    def _scale(self, data, attrs):
        """Scale the data..

        .. versionadded:: (cfdm) HDFVER

        :Parameter:

            data: `numpy.ndarray`
                The unmasked and unscaled data indexed from the
                variable.

            attrs: `dict`
                The variable attributes.

        :Returns:

            `nump.ndarray`
                The scaled data.

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
                "invalid scale_factor or add_offset attribute, "
                "no unpacking done..."
            )
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
