import h5netcdf
import netCDF4
import numpy as np

from . import abstract
from .mixin import FileArrayMixin
from .numpyarray import NumpyArray

_safecast = netCDF4.utils._safecast

class HDFArray(FileArrayMixin, abstract.Array):
    """An underlying array stored in an HDF file.

    .. versionadded:: (cfdm) TODOHDF

    """

    def __init__(
        self,
        filename=None,
        address=None,
        dtype=None,
        shape=None,
        mask=True,
        units=False,
        calendar=False,
        missing_values=None,
        source=None,
        copy=True,
    ):
        """**Initialisation**

        :Parameters:

            filename: (sequence of) `str`, optional
                The name of the file(s) containing the array.

            address: (sequence of) `str` or `int`, optional
                The identity of the variable in each file defined by
                *filename*. Either a netCDF variable name or an
                integer HDF variable ID.

            dtype: `numpy.dtype`
                The data type of the array in the file. May be `None`
                if the numpy data-type is not known (which can be the
                case for string types, for example).

            shape: `tuple`
                The array dimension sizes in the file.

            size: `int`
                Number of elements in the array in the file.

            ndim: `int`
                The number of array dimensions in the file.

            mask: `bool`
                If True (the default) then mask by convention when
                reading data from disk.

                A netCDF array is masked depending on the values of any of
                the netCDF variable attributes ``valid_min``,
                ``valid_max``, ``valid_range``, ``_FillValue`` and
                ``missing_value``.

            units: `str` or `None`, optional
                The units of the variable. Set to `None` to indicate
                that there are no units. If unset then the units will
                be set during the first `__getitem__` call.

            calendar: `str` or `None`, optional
                The calendar of the variable. By default, or if set to
                `None`, then the CF default calendar is assumed, if
                applicable. If unset then the calendar will be set
                during the first `__getitem__` call.

            missing_values: `dict`, optional
                The missing value indicators defined by the variable
                attributes. See `get_missing_values` for details.

            {{init source: optional}}

            {{init copy: `bool`, optional}}

        """
        super().__init__(source=source, copy=copy)

        if source is not None:
            try:
                shape = source._get_component("shape", None)
            except AttributeError:
                shape = None

            try:
                filename = source._get_component("filename", None)
            except AttributeError:
                filename = None

            try:
                address = source._get_component("address", None)
            except AttributeError:
                address = None

            try:
                dtype = source._get_component("dtype", None)
            except AttributeError:
                dtype = None

            try:
                mask = source._get_component("mask", True)
            except AttributeError:
                mask = True

            try:
                units = source._get_component("units", False)
            except AttributeError:
                units = False

            try:
                calendar = source._get_component("calendar", False)
            except AttributeError:
                calendar = False

            try:
                missing_values = source._get_component("missing_values", None)
            except AttributeError:
                missing_values = None

        if shape is not None:
            self._set_component("shape", shape, copy=False)

        if filename is not None:
            if isinstance(filename, str):
                filename = (filename,)
            else:
                filename = tuple(filename)

            self._set_component("filename", filename, copy=False)

        if address is not None:
            if isinstance(address, (str, int)):
                address = (address,)
            else:
                address = tuple(address)

            self._set_component("address", address, copy=False)

        if missing_values is not None:
            self._set_component(
                "missing_values", missing_values.copy(), copy=False
            )

        self._set_component("dtype", dtype, copy=False)
        self._set_component("mask", mask, copy=False)
        self._set_component("units", units, copy=False)
        self._set_component("calendar", calendar, copy=False)

        # By default, close the file after data array access
        self._set_component("close", True, copy=False)

    def __getitem__(self, indices):
        """Returns a subspace of the array as a numpy array.

        x.__getitem__(indices) <==> x[indices]

        The indices that define the subspace must be either `Ellipsis` or
        a sequence that contains an index for each dimension. In the
        latter case, each dimension's index must either be a `slice`
        object or a sequence of two or more integers.

        Indexing is similar to numpy indexing. The only difference to
        numpy indexing (given the restrictions on the type of indices
        allowed) is:

          * When two or more dimension's indices are sequences of integers
            then these indices work independently along each dimension
            (similar to the way vector subscripts work in Fortran).

        .. versionadded:: (cfdm) 1.7.0

        """
        dataset, address = self.open()
        dataset0 = dataset

        mask = self.get_mask()
        groups, address = self.get_groups(address)

        if groups:
            # Traverse the group structure, if there is one (CF>=1.8).
            for g in groups[:-1]:
                dataset = dataset.groups[g] # h5netcdf

            dataset = dataset.groups[groups[-1]]# h5netcdf

        if isinstance(address, str):
            # Get the variable by netCDF name
            variable = dataset.variables[address]
            self.variable = variable
#            variable.set_auto_mask(mask) # h5netcdf           
            array = variable[indices]
#            array = self.mask_unpack(variable, array)
        else:
            # Get the variable by netCDF integer ID
            for variable in dataset.variables.values():
                if variable._varid == address:
                    variable.set_auto_mask(mask)
                    array = variable[indices]
                    break

        # Set the units, if they haven't been set already.
        self._set_units(variable)

        del self.variable
        self.close(dataset0)
        del dataset, dataset0

        string_type = isinstance(array, str)
        if string_type:
            # --------------------------------------------------------
            # A netCDF string type scalar variable comes out as Python
            # str object, so convert it to a numpy array.
            # --------------------------------------------------------
            array = np.array(array, dtype=f"U{len(array)}")

        if not self.ndim:
            # Hmm netCDF4 has a thing for making scalar size 1, 1d
            array = array.squeeze()

        kind = array.dtype.kind
        if not string_type and kind in "SU":
            #     == 'S' and array.ndim > (self.ndim -
            #     getattr(self, 'gathered', 0) -
            #     getattr(self, 'ragged', 0)):
            # --------------------------------------------------------
            # Collapse (by concatenation) the outermost (fastest
            # varying) dimension of char array into
            # memory. E.g. [['a','b','c']] becomes ['abc']
            # --------------------------------------------------------
            if kind == "U":
                array = array.astype("S", copy=False)

            array = netCDF4.chartostring(array)
            shape = array.shape
            array = np.array([x.rstrip() for x in array.flat], dtype="U")
            array = np.reshape(array, shape)
            array = np.ma.masked_where(array == "", array)
        elif not string_type and kind == "O":
            # --------------------------------------------------------
            # A netCDF string type N-d (N>=1) variable comes out as a
            # numpy object array, so convert it to numpy string array.
            # --------------------------------------------------------
            array = array.astype("U", copy=False)

            # --------------------------------------------------------
            # netCDF4 does not auto-mask VLEN variable, so do it here.
            # --------------------------------------------------------
            array = np.ma.where(array == "", np.ma.masked, array)

        return array

    def __repr__(self):
        """Called by the `repr` built-in function.

        x.__repr__() <==> repr(x)

        """
        return f"<{self.__class__.__name__}{self.shape}: {self}>"

    def __str__(self):
        """Called by the `str` built-in function.

        x.__str__() <==> str(x)

        """
        return f"{self.get_filename(None)}, {self.get_address()}"

    def _set_units(self, var):
        """The units and calendar properties.

        These are set from the netCDF variable attributes, but only if
        they have already not been defined, either during {{class}}
        instantiation or by a previous call to `_set_units`.

        .. versionadded:: (cfdm) 1.10.0.1

        :Parameters:

            var: `netCDF4.Variable`
                The variable containing the units and calendar
                definitions.

        :Returns:

            `tuple`
                The units and calendar values, either of which may be
                `None`.

        """
        # Note: Can't use None as the default since it is a valid
        #       `units` or 'calendar' value that indicates that the
        #       attribute has not been set in the dataset.
        units = self._get_component("units", False)
        if units is False:
            try:
                units = var.getncattr("units")
            except AttributeError:
                units = None

            self._set_component("units", units, copy=False)

        calendar = self._get_component("calendar", False)
        if calendar is False:
            try:
                calendar = var.getncattr("calendar")
            except AttributeError:
                calendar = None

            self._set_component("calendar", calendar, copy=False)

        return units, calendar

    @property
    def array(self):
        """Return an independent numpy array containing the data.

        .. versionadded:: (cfdm) 1.7.0

        :Returns:

            `numpy.ndarray`
                An independent numpy array of the data.

        **Examples**

        >>> n = numpy.asanyarray(a)
        >>> isinstance(n, numpy.ndarray)
        True

        """
        return self[...]

    def get_format(self):
        """The format of the files.

        .. versionadded:: (cfdm) 1.10.1.0

        .. seealso:: `get_address`, `get_filename`, `get_formats`

        :Returns:

            `str`
                The file format. Always ``'nc'``, signifying netCDF.

        **Examples**

        >>> a.get_format()
        'nc'

        """
        return "nc"

    def get_groups(self, address):
        """The netCDF4 group structure of a netCDF variable.

        .. versionadded:: (cfdm) 1.8.6.0

        :Parameters:

            address: `str` or `int`
                The netCDF variable name, or integer varid, from which
                to get the groups.

                .. versionadded:: (cfdm) 1.10.1.0

        :Returns:

            (`list`, `str`) or (`list`, `int`)
                The group structure and the name within the group. If
                *address* is a varid then an empty list and the varid
                are returned.

        **Examples**

        >>> n.get_groups('tas')
        ([], 'tas')

        >>> n.get_groups('/tas')
        ([], 'tas')

        >>> n.get_groups('/data/model/tas')
        (['data', 'model'], 'tas')

        >>> n.get_groups(9)
        ([], 9)

        """
        try:
            if "/" not in address:
                return [], address
        except TypeError:
            return [], address

        out = address.split("/")[1:]
        return out[:-1], out[-1]

    def get_mask(self):
        """Whether or not to automatically mask the data.

        .. versionadded:: (cfdm) 1.8.2

        **Examples**

        >>> b = a.get_mask()

        """
        return self._get_component("mask")

    def get_missing_values(self):
        """The missing value indicators from the netCDF variable.

        .. versionadded:: (cfdm) 1.10.0.3

        :Returns:

            `dict` or `None`
                The missing value indicators from the netCDF variable,
                keyed by their netCDF attribute names. An empty
                dictionary signifies that no missing values are given
                in the file. `None` signifies that the missing values
                have not been set.

        **Examples**

        >>> a.get_missing_values()
        None

        >>> b.get_missing_values()
        {}

        >>> c.get_missing_values()
        {'missing_value': 1e20, 'valid_range': (-10, 20)}

        >>> d.get_missing_values()
        {'valid_min': -999}

        """
        out = self._get_component("missing_values", None)
        if out is None:
            return

        return out.copy()

    def close(self, dataset):
        """Close the dataset containing the data.

        .. versionadded:: (cfdm) 1.7.0

        :Parameters:

            dataset: `netCDF4.Dataset`
                The netCDF dataset to be be closed.

        :Returns:

            `None`

        """
        if self._get_component("close"):
            dataset.close()

    def open(self, **kwargs):
        """Return an open file object containing the data array.

        When multiple files have been provided an attempt is made to
        open each one, in the order stored, and an open file object is
        returned from the first file that exists.

        :Returns:

            (`netCDF4.Dataset`, `str`)
                The open file object, and the address of the data
                within the file.

        """
        return super().open(h5netcdf.File, mode="r", **kwargs)

    def _check_safecast(self, attname):
        # check to see that variable attribute exists
        # can can be safely cast to variable data type.
        msg="""WARNING: %s not used since it cannot be safely cast to variable data type""" % attname
        attrs = variable.attrs
        if attname in attrs:
            attvalue = self.variable.attrs[attname]
            att = np.array(attvalue)
            setattr(self, attname, attvalue)
        else:
            return False
        try:
            atta = np.array(att, self.dtype)
        except ValueError:
            is_safe = False
            warnings.warn(msg)
            return is_safe
        is_safe = _safecast(att,atta)
        if not is_safe:
            warnings.warn(msg)
        return is_safe

#    def mask_and_scale(self, data):
#        """TODOHDF"""
#        self.scale = True # h5netcdf
#        attrs = self.variable.attrs
#        self._Unsigned = attrs.get('_Unsigned', 'false')
#        
#        # if attribute _Unsigned is "true", and variable has signed integer
#        # dtype, return view with corresponding unsigned dtype (issues #656,
#        # #794)
#        # _Unsigned attribute must be "true" or "True" (string). Issue #1232.
#        is_unsigned = getattr(self, '_Unsigned', False) in ["True","true"]
#        is_unsigned_int = is_unsigned and data.dtype.kind == 'i'
#        if self.scale and is_unsigned_int:  # only do this if autoscale option is on.
#            dtype_unsigned_int='%su%s' % (data.dtype.byteorder,data.dtype.itemsize)
#            data = data.view(dtype_unsigned_int)
#            
#        # private function for creating a masked array, masking missing_values
#        # and/or _FillValues.
#        totalmask = np.zeros(data.shape, np.bool_)
#        fill_value = None
#        safe_missval = self._check_safecast('missing_value')
#        if safe_missval:
#            mval = numpy.array(self.missing_value, self.dtype)
#            if self.scale and is_unsigned_int:
#                mval = mval.view(dtype_unsigned_int)
#                
#            # create mask from missing values.
#            mvalmask = np.zeros(data.shape, numpy.bool_)
#            if mval.shape == (): # mval a scalar.
#                mval = [mval] # make into iterable.
#                
#            for m in mval:
#                # is scalar missing value a NaN?
#                try:
#                    mvalisnan = numpy.isnan(m)
#                except TypeError: # isnan fails on some dtypes (issue 206)
#                    mvalisnan = False
#                    
#                if mvalisnan:
#                    mvalmask += numpy.isnan(data)
#                else:
#                    mvalmask += data==m
#                    
#            if mvalmask.any():
#                # set fill_value for masked array
#                # to missing_value (or 1st element
#                # if missing_value is a vector).
#                fill_value = mval[0]
#                totalmask += mvalmask
#                
#        # set mask=True for data == fill value
#        safe_fillval = self._check_safecast('_FillValue')
#        if safe_fillval:
#            fval = np.array(self._FillValue, self.dtype)
#            if self.scale and is_unsigned_int:
#                fval = fval.view(dtype_unsigned_int)
#                
#            # is _FillValue a NaN?
#            try:
#                fvalisnan = np.isnan(fval)
#            except: # isnan fails on some dtypes (issue 202)
#                fvalisnan = False
#                
#            if fvalisnan:
#                mask = np.isnan(data)
#            elif (data == fval).any():
#                mask = data==fval
#            else:
#                mask = None
#
#            if mask is not None:
#                if fill_value is None:
#                    fill_value = fval
#                    
#                totalmask += mask
#        # issue 209: don't return masked array if variable filling
#        # is disabled.
#        else:
#            if __netcdf4libversion__ < '4.5.1' and\
#                self._grp.file_format.startswith('NETCDF3'):
#                # issue #908: no_fill not correct for NETCDF3 files before 4.5.1
#                # before 4.5.1 there was no way to turn off filling on a
#                # per-variable basis for classic files.
#                no_fill=0
#            else:
#                with nogil:
#                    ierr = nc_inq_var_fill(self._grpid,self._varid,&no_fill,NULL)
#                _ensure_nc_success(ierr)
#            # if no_fill is not 1, and not a byte variable, then use default fill value.
#            # from http://www.unidata.ucar.edu/software/netcdf/docs/netcdf-c/Fill-Values.html#Fill-Values
#            # "If you need a fill value for a byte variable, it is recommended
#            # that you explicitly define an appropriate _FillValue attribute, as
#            # generic utilities such as ncdump will not assume a default fill
#            # value for byte variables."
#            # Explained here too:
#            # http://www.unidata.ucar.edu/software/netcdf/docs/known_problems.html#ncdump_ubyte_fill
#            # "There should be no default fill values when reading any byte
#            # type, signed or unsigned, because the byte ranges are too
#            # small to assume one of the values should appear as a missing
#            # value unless a _FillValue attribute is set explicitly."
#            # (do this only for non-vlens, since vlens don't have a default _FillValue)
#            if not self._isvlen and (no_fill != 1 or self.dtype.str[1:] not in ['u1','i1']):
#                fillval = np.array(default_fillvals[self.dtype.str[1:]],self.dtype)
#                has_fillval = data == fillval
#                # if data is an array scalar, has_fillval will be a boolean.
#                # in that case convert to an array.
#                if type(has_fillval) == bool:
#                    has_fillval = np.asarray(has_fillval)
#                
#                if has_fillval.any():
#                    if fill_value is None:
#                        fill_value = fillval
#                        
#                    mask = data == fillval
#                    totalmask += mask
#        # set mask=True for data outside valid_min,valid_max.
#        # (issue #576)
#        validmin = None;
#        validmax = None
#        # if valid_range exists use that, otherwise
#        # look for valid_min, valid_max.  No special
#        # treatment of byte data as described at
#        # http://www.unidata.ucar.edu/software/netcdf/docs/attribute_conventions.html).
#        safe_validrange = self._check_safecast('valid_range')
#        safe_validmin = self._check_safecast('valid_min')
#        safe_validmax = self._check_safecast('valid_max')
#        if safe_validrange and self.valid_range.size == 2:
#            validmin = np.array(self.valid_range[0], self.dtype)
#            validmax = np.array(self.valid_range[1], self.dtype)
#        else:
#            if safe_validmin:
#                validmin = np.array(self.valid_min, self.dtype)
#
#            if safe_validmax:
#                validmax = numpy.array(self.valid_max, self.dtype)
#        if validmin is not None and self.scale and is_unsigned_int:
#            validmin = validmin.view(dtype_unsigned_int)
#
#        if validmax is not None and self.scale and is_unsigned_int:
#            validmax = validmax.view(dtype_unsigned_int)
#        # http://www.unidata.ucar.edu/software/netcdf/docs/attribute_conventions.html).
#        # "If the data type is byte and _FillValue
#        # is not explicitly defined,
#        # then the valid range should include all possible values.
#        # Otherwise, the valid range should exclude the _FillValue
#        # (whether defined explicitly or by default) as follows.
#        # If the _FillValue is positive then it defines a valid maximum,
#        #  otherwise it defines a valid minimum."
#        byte_type = self.dtype.str[1:] in ['u1','i1']
#        if safe_fillval:
#            fval = np.array(self._FillValue, self.dtype)
#        else:
#            fval = np.array(default_fillvals[self.dtype.str[1:]],self.dtype)
#            if byte_type:
#                fval = None
#                
#        if self.dtype.kind != 'S': # don't set mask for character data
#            # issues #761 and #748:  setting valid_min/valid_max to the
#            # _FillVaue is too surprising for many users (despite the
#            # netcdf docs attribute best practices suggesting clients
#            # should do this).
#            #if validmin is None and (fval is not None and fval <= 0):
#            #    validmin = fval
#            #if validmax is None and (fval is not None and fval > 0):
#            #    validmax = fval
#            if validmin is not None:
#                totalmask += data < validmin
#            if validmax is not None:
#                totalmask += data > validmax
#
#        if fill_value is None and fval is not None:
#            fill_value = fval
#        # if all else fails, use default _FillValue as fill_value
#        # for masked array.
#        
#        if fill_value is None:
#            fill_value = default_fillvals[self.dtype.str[1:]]
#            
#        # create masked array with computed mask
#        masked_values = bool(totalmask.any())
#        if masked_values:
#            data = np.ma.masked_array(data, mask=totalmask,fill_value=fill_value)
#        else:
#            # issue #785: always return masked array, if no values masked
#            data = np.ma.masked_array(data)
#            
#        # issue 515 scalar array with mask=True should be converted
#        # to numpy.ma.MaskedConstant to be consistent with slicing
#        # behavior of masked arrays.
#        if data.shape == () and data.mask.all():
#            # return a scalar numpy masked constant not a 0-d masked array,
#            # so that data == numpy.ma.masked.
#            data = data[()] # changed from [...] (issue #662)
#            
#        elif not self.always_mask and not masked_values:
#            # issue #809: return a regular numpy array if requested
#            # and there are no missing values
#            data = np.array(data, copy=False)
#
#        # ---------------------------
#        # Now scale
#        # ---------------------------
#        if self.scale and\
#           (self._isprimitive or (self._isvlen and self.dtype != str)) and\
#           valid_scaleoffset:
#            # if variable has scale_factor and add_offset attributes, apply
#            # them.
#            if hasattr(self, 'scale_factor') and hasattr(self, 'add_offset'):
#                if self.add_offset != 0.0 or self.scale_factor != 1.0:
#                    data = data*self.scale_factor + self.add_offset
#                else:
#                    data = data.astype(self.scale_factor.dtype) # issue 913
#            # else if variable has only scale_factor attribute, rescale.
#            elif hasattr(self, 'scale_factor') and self.scale_factor != 1.0:
#                data = data*self.scale_factor
#            # else if variable has only add_offset attribute, add offset.
#            elif hasattr(self, 'add_offset') and self.add_offset != 0.0:
#                data = data
#                
#        return data
    
    def mask_unpack(self, variable, array):
        """TODOHDF"""
        mu =  _Mask_Unpack(variable)
        array = mu.mask(array)
        array = mu.unpack(array)
        return data

    def to_memory(self):
        """Bring data on disk into memory.

        .. versionadded:: (cfdm) 1.7.0

        :Returns:

            `NumpyArray`
                The new with all of its data in memory.

        """
        return NumpyArray(self[...])


default_fillvals = netCDF4.default_fillvals 
_private_atts = []

class _Mask_Unpack(netCDF4.Variable):
    """TODOHDF"""
    def __init__(self, variable): 
        self.__dict__['_isprimitive'] = True # h5netcdf
        self.__dict__['_isvlen'] = False # h5netcdf
        self.__dict__['_isenum'] = False # h5netcdf
        self.__dict__['dtype'] = variable.dtype

        attrs = variable.attrs
        print (attrs)
        self.__dict__['attrs'] = attrs
        self.__dict__['_Unsigned'] = 'false'
        for attr in ('_FillValue', 'add_offset', 'scale', '_Unsigned', 'valid_max', 'valid_min', 'valid_range', ):
            if attr in attrs:
                self.__dict__[attr] = attrs[attr]
                
    def getncattr(self, name, encoding='utf-8'):
        """Retrieve a netCDF4 attribute."""
        return self.attrs[name]

    def mask(self, data):
        """TODOHDF"""
        return self._toma(data)
           
    def unpack(self, data):
        """Unpack non-masked values using scale_factor and add_offset.

        """
        if not scale:
            return data
        
        try: # check to see if scale_factor and add_offset is valid (issue 176).
            if hasattr(self,'scale_factor'): float(self.scale_factor)
            if hasattr(self,'add_offset'): float(self.add_offset)
            valid_scaleoffset = True
        except:
            valid_scaleoffset = False
            if self.scale:
                msg = 'invalid scale_factor or add_offset attribute, no unpacking done...'
                # warnings.warn(msg) # h5netcdf

        if self.scale and\
           (self._isprimitive or (self._isvlen and self.dtype != str)) and\
           valid_scaleoffset:
            # if variable has scale_factor and add_offset attributes, apply
            # them.
            if hasattr(self, 'scale_factor') and hasattr(self, 'add_offset'):
                if self.add_offset != 0.0 or self.scale_factor != 1.0:
                    data = data*self.scale_factor + self.add_offset
                else:
                    data = data.astype(self.scale_factor.dtype) # issue 913
            # else if variable has only scale_factor attribute, rescale.
            elif hasattr(self, 'scale_factor') and self.scale_factor != 1.0:
                data = data*self.scale_factor
            # else if variable has only add_offset attribute, add offset.
            elif hasattr(self, 'add_offset') and self.add_offset != 0.0:
                data = data + self.add_offset
