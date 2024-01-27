import logging

import netCDF4
import numpy as np

_safecast = netCDF4.utils._safecast
default_fillvals = netCDF4.default_fillvals

logger = logging.getLogger(__name__)


class Mask:

#        variable = dataset.variables[address]
#        self.variable = variable
#        array = variable[indices]
#        print(11)
#        if mask:
#            print(22)
#            self.scale = True
#            self.always_mask = False
#            self._isvlen = variable.dtype == np.dtype("O")
#            isvlen = variable.dtype == np.dtype("O")
#            if not self._isvlen:
#                array = self._mask2(
#                    array,
#                    variable.dtype,
#                    variable.attrs,
#                    isvlen,
#                    self.scale,
#                    self.always_mask,
#                )
#                #                array = self._mask(array)
#                array = self._scale(array)
#
#        string_type = isinstance(array, str)
#        if string_type:
#            # --------------------------------------------------------
#            # A netCDF string type scalar variable comes out as Python
#            # str object, so convert it to a numpy array.
#            # --------------------------------------------------------
#            array = np.array(array, dtype=f"U{len(array)}")
#
#        if not self.ndim:
#            # Hmm netCDF4 has a thing for making scalar size 1, 1d
#            array = array.squeeze()
#
#        array = self._process_string_and_char(array)
#        return array

    @classmethod
    def _check_safecast(cls, attname, var_dtype, attrs):
        """TODOHDF.

        Check to see that variable attribute exists can can be safely
        cast to variable data type.

        """
        #        attrs = self.variable.attrs
        if attname in attrs:
            attvalue = attrs[attname]
            att = np.array(attvalue)
        else:
            return False, None

        is_safe = True
        try:
            atta = np.array(att, var_dtype)
        except ValueError:
            is_safe = False
        else:
            is_safe = _safecast(att, atta)

        if not is_safe:
            logger.warn(
                f"WARNING: {attname} not used since it cannot "
                "be safely cast to variable data type"
            )  # pragma: no cover

        return is_safe, attvalue

#    def _mask(self, data):
#        """TODOHDF."""
#        print("MASK", data.shape)
#        # Private function for creating a masked array, masking
#        # missing_values and/or _FillValues.
#
#        attrs = self.variable.attrs
#        is_unsigned = attrs.get("_Unsigned", False) in ("true", "True")
#        is_unsigned_int = is_unsigned and data.dtype.kind == "i"
#
#        dtype = data.dtype
#        if self.scale and is_unsigned_int:
#            # Only do this if autoscale option is on.
#            dtype_unsigned_int = f"{dtype.byteorder}u{dtype.itemsize}"
#            data = data.view(dtype_unsigned_int)
#
#        totalmask = np.zeros(data.shape, np.bool_)
#        fill_value = None
#        safe_missval = self._check_safecast("missing_value")
#        if safe_missval:
#            mval = np.array(self.missing_value, self.dtype)
#            if self.scale and is_unsigned_int:
#                mval = mval.view(dtype_unsigned_int)
#
#            # create mask from missing values.
#            mvalmask = np.zeros(data.shape, np.bool_)
#            if mval.shape == ():  # mval a scalar.
#                mval = (mval,)  # make into iterable.
#
#            for m in mval:
#                # is scalar missing value a NaN?
#                try:
#                    mvalisnan = np.isnan(m)
#                except TypeError:
#                    # isnan fails on some dtypes
#                    mvalisnan = False
#
#                if mvalisnan:
#                    mvalmask += np.isnan(data)
#                else:
#                    mvalmask += data == m
#
#            if mvalmask.any():
#                # Set fill_value for masked array to missing_value (or
#                # 1st element if missing_value is a vector).
#                fill_value = mval[0]
#                totalmask += mvalmask
#
#        # set mask=True for data == fill value
#        safe_fillval = self._check_safecast("_FillValue")
#        if safe_fillval:
#            fval = np.array(self._FillValue, self.dtype)
#            if self.scale and is_unsigned_int:
#                fval = fval.view(dtype_unsigned_int)
#
#            # is _FillValue a NaN?
#            try:
#                fvalisnan = np.isnan(fval)
#            except Exception:
#                # isnan fails on some dtypes
#                fvalisnan = False
#
#            if fvalisnan:
#                mask = np.isnan(data)
#            elif (data == fval).any():
#                mask = data == fval
#            else:
#                mask = None
#
#            if mask is not None:
#                if fill_value is None:
#                    fill_value = fval
#
#                totalmask += mask
#        else:
#            # Don't return masked array if variable filling is disabled.
#            no_fill = 0
#            #                with nogil:
#            #                    ierr = nc_inq_var_fill(self._grpid,self._varid,&no_fill,NULL)
#            #                _ensure_nc_success(ierr)
#
#            # if no_fill is not 1, and not a byte variable, then use
#            # default fill value.  from
#            # http://www.unidata.ucar.edu/software/netcdf/docs/netcdf-c/Fill-Values.html#Fill-Values
#            # "If you need a fill value for a byte variable, it is
#            # recommended that you explicitly define an appropriate
#            # _FillValue attribute, as generic utilities such as
#            # ncdump will not assume a default fill value for byte
#            # variables."  Explained here too:
#            # http://www.unidata.ucar.edu/software/netcdf/docs/known_problems.html#ncdump_ubyte_fill
#            # "There should be no default fill values when reading any
#            # byte type, signed or unsigned, because the byte ranges
#            # are too small to assume one of the values should appear
#            # as a missing value unless a _FillValue attribute is set
#            # explicitly."  (do this only for non-vlens, since vlens
#            # don't have a default _FillValue)
#            if not self._isvlen and (
#                no_fill != 1 or dtype.str[1:] not in ("u1", "i1")
#            ):
#                fillval = np.array(default_fillvals[dtype.str[1:]], dtype)
#                has_fillval = data == fillval
#                # if data is an array scalar, has_fillval will be a
#                # boolean.  in that case convert to an array.
#                #                if type(has_fillval) == bool:
#                if isinstance(has_fillval, bool):
#                    has_fillval = np.asarray(has_fillval)
#
#                if has_fillval.any():
#                    if fill_value is None:
#                        fill_value = fillval
#
#                    mask = data == fillval
#                    totalmask += mask
#
#        # Set mask=True for data outside valid_min, valid_max.
#        validmin = None
#        validmax = None
#        # If valid_range exists use that, otherwise look for
#        # valid_min, valid_max. No special treatment of byte data as
#        # described at
#        # http://www.unidata.ucar.edu/software/netcdf/docs/attribute_conventions.html).
#        safe_validrange = self._check_safecast("valid_range")
#        safe_validmin = self._check_safecast("valid_min")
#        safe_validmax = self._check_safecast("valid_max")
#        if safe_validrange and self.valid_range.size == 2:
#            validmin = np.array(self.valid_range[0], self.dtype)
#            validmax = np.array(self.valid_range[1], self.dtype)
#        else:
#            if safe_validmin:
#                validmin = np.array(self.valid_min, self.dtype)
#
#            if safe_validmax:
#                validmax = np.array(self.valid_max, self.dtype)
#
#        if validmin is not None and self.scale and is_unsigned_int:
#            validmin = validmin.view(dtype_unsigned_int)
#
#        if validmax is not None and self.scale and is_unsigned_int:
#            validmax = validmax.view(dtype_unsigned_int)
#
#        # http://www.unidata.ucar.edu/software/netcdf/docs/attribute_conventions.html).
#        # "If the data type is byte and _FillValue is not explicitly
#        # defined, then the valid range should include all possible
#        # values.  Otherwise, the valid range should exclude the
#        # _FillValue (whether defined explicitly or by default) as
#        # follows. If the _FillValue is positive then it defines a
#        # valid maximum, otherwise it defines a valid minimum."
#        if safe_fillval:
#            fval = np.array(self._FillValue, dtype)
#        else:
#            k = dtype.str[1:]
#            if k in ("u1", "i1"):
#                fval = None
#            else:
#                fval = np.array(default_fillvals[k], dtype)
#
#        if self.dtype.kind != "S":
#            # Don't set mask for character data
#
#            # Setting valid_min/valid_max to the _FillVaue is too
#            # surprising for many users (despite the netcdf docs
#            # attribute best practices suggesting clients should do
#            # this).
#            if validmin is not None:
#                totalmask += data < validmin
#
#            if validmax is not None:
#                totalmask += data > validmax
#
#        if fill_value is None and fval is not None:
#            fill_value = fval
#
#        # If all else fails, use default _FillValue as fill_value for
#        # masked array.
#        if fill_value is None:
#            fill_value = default_fillvals[dtype.str[1:]]
#
#        # Create masked array with computed mask
#        masked_values = bool(totalmask.any())
#        if masked_values:
#            data = np.ma.masked_array(
#                data, mask=totalmask, fill_value=fill_value
#            )
#        else:
#            # Always return masked array, if no values masked.
#            data = np.ma.masked_array(data)
#
#        # Scalar array with mask=True should be converted to
#        # np.ma.MaskedConstant to be consistent with slicing
#        # behavior of masked arrays.
#        if data.shape == () and data.mask.all():
#            # Return a scalar numpy masked constant not a 0-d masked
#            # array, so that data == np.ma.masked.
#            data = data[()]
#
#        elif not self.always_mask and not masked_values:
#            # Return a regular numpy array if requested and there are
#            # no missing values
#            data = np.array(data, copy=False)
#
#           
#        return data

    @classmethod
    def _process_string_and_char(cls, array):
        """TODOHDF."""
        string_type = isinstance(array, str)
        kind = array.dtype.kind
        if not string_type and kind in "SU":
            # Collapse by concatenation the outermost (fastest
            # varying) dimension of char array into
            # memory. E.g. [['a','b','c']] becomes ['abc']
            if kind == "U":
                array = array.astype("S", copy=False)

            array = netCDF4.chartostring(array)
            shape = array.shape
            array = np.array([x.rstrip() for x in array.flat], dtype="U")
            array = np.reshape(array, shape)
            array = np.ma.masked_where(array == "", array)
        elif not string_type and kind == "O":
            # An N-d (N>=1) string variable comes out as a numpy
            # object array, so convert it to numpy string array.
            array = array.astype("U", copy=False)

            # Mask the VLEN variable
            array = np.ma.where(array == "", np.ma.masked, array)
                
        return array

    @classmethod
    def _process_char_array(cls, array, mask=True):
        """TODOHDF."""
        # Collapse by concatenation the outermost (fastest
        # varying) dimension of char array into
        # memory. E.g. [['a','b','c']] becomes ['abc']
        if kind == "U":
            array = array.astype("S", copy=False)

        array = netCDF4.chartostring(array)
        shape = array.shape
        array = np.array([x.rstrip() for x in array.flat], dtype="U")
        array = np.reshape(array, shape)
        if mask:
            array = np.ma.masked_where(array == "", array)
            if not np.ma.is_masked(data):
                array = np.array(array, copy=False)
            
        return array

    @classmethod
    def _process_string(cls, data, mask=True):
        """TODOHDF."""
        if mask and data == "":
            data = np.ma.masked_all((), dtype=f"U{len(data)}")
        else:
            data = np.array(data, dtype="U")
            
        return data
    
    @classmethod
    def _process_object_array(cls, array, mask=True):
        """TODOHDF."""
        array = array.astype("U", copy=False)
        if mask:
            array = np.ma.where(array == "", np.ma.masked, array)
            if not np.ma.is_masked(data):
                array = np.array(array, copy=False)
            
        return array

    def _is_char(cls, data):
        return data.dtype.kind in "SU" # isinstance(data.item(0), (str, bytes))
    
    def _is_string(cls, data):
        return data.dtype.kind in "O"

    @classmethod
    def mask_and_scale(cls, mask=True, scale=True):
        """
        """
        if isinstance(data, str):
            return cls._process_string(data, mask=mask)

        if _is_string(data):
            return cls._process_object_array(data, mask=mask)            

        if _is_char(data):
            return cls._process_char_array(data, mask=mask)

        if mask or scale:
            is_unsigned_int = attrs.get("_Unsigned", False) in ("true", "True")
            if is_unsigned_int:                
                dtype = data.dtype
                dtype_unsigned_int = f"{dtype.byteorder}u{dtype.itemsize}"
                data = data.view(dtype_unsigned_int)

        if mask:
            data = cls._mask(data.scale=scale, always_mask=False)

        if scale:
            data = cls._scale(data, attrs)

        return data
    
    @classmethod
    def _mask(
        cls, data, var_dtype, attrs, scale=True, always_mask=False
    ):
        """TODOHDF."""
        print("MASK", data.shape)

        if isinstance(data, str):
            return cls._process_string(data)

        if  _is_string(data):
            return cls._process_object_array(data)

        if  _is_char(data):
            return cls._process_char_array(data)

        dtype = data.dtype
#        is_unsigned = attrs.get("_Unsigned", False) in ("true", "True")
#        is_unsigned_int = is_unsigned and data.dtype.kind == "i"
#
#        dtype = data.dtype
#        if scale and is_unsigned_int:
#            # Only do this if autoscale option is on.
#            dtype_unsigned_int = f"{dtype.byteorder}u{dtype.itemsize}"
#            data = data.view(dtype_unsigned_int)

        totalmask = np.zeros(data.shape, np.bool_)
        fill_value = None
        safe_missval, missing_value = cls._check_safecast(
            "missing_value", var_dtype, attrs
        )
        if safe_missval:
            mval = np.array(missing_value, var_dtype)
            if scale and is_unsigned_int:
                mval = mval.view(dtype_unsigned_int)

            # create mask from missing values.
            mvalmask = np.zeros(data.shape, np.bool_)
            if mval.shape == ():  # mval a scalar.
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
        safe_fillval, _FillValue = cls._check_safecast(
            "_FillValue", dtype, attrs
        )
        if safe_fillval:
            fval = np.array(_FillValue, var_dtype)
            if scale and is_unsigned_int:
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
            if (
                no_fill != 1 or dtype.str[1:] not in ("u1", "i1")
            ):
                fillval = np.array(default_fillvals[dtype.str[1:]], dtype)
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

        # Set mask=True for data outside valid_min, valid_max.
        validmin = None
        validmax = None
        # If valid_range exists use that, otherwise look for
        # valid_min, valid_max. No special treatment of byte data as
        # described at
        # http://www.unidata.ucar.edu/software/netcdf/docs/attribute_conventions.html).
        safe_validrange, valid_range = cls._check_safecast(
            "valid_range", var_dtype, attrs
        )
        safe_validmin, valid_min = cls._check_safecast(
            "valid_min", var_dtype, attrs
        )
        safe_validmax, valid_max = cls._check_safecast(
            "valid_max", var_dtype, attrs
        )
        if safe_validrange and valid_range.size == 2:
            validmin = np.array(valid_range[0], var_dtype)
            validmax = np.array(valid_range[1], var_dtype)
        else:
            if safe_validmin:
                validmin = np.array(valid_min, var_dtype)

            if safe_validmax:
                validmax = np.array(valid_max, var_dtype)

        if validmin is not None and scale and is_unsigned_int:
            validmin = validmin.view(dtype_unsigned_int)

        if validmax is not None and scale and is_unsigned_int:
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
                fval = np.array(default_fillvals[k], dtype)

        if var_dtype.kind != "S":
            # Don't set mask for character data

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
            fill_value = default_fillvals[dtype.str[1:]]

        # Create masked array with computed mask
        masked_values = bool(totalmask.any())
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

        elif not always_mask and not masked_values:
            # Return a regular numpy array if requested and there are
            # no missing values
            data = np.array(data, copy=False)

        return data

    @classmethod
    def _scale(cls, data, attrs):
        """TODOHDF."""
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
