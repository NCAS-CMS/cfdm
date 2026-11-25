"""Utilities for conversion to and from xarray."""


def from_xarray(ds, domain=False):
    """Convert an `xarray` dataset to CF field or domain constructs.

    In general (see the note below) `cfdm.from_xarray` is an in-memory
    operation which does two things: it maps the `xarray` dataset
    variables and attributes onto CF constructs; and it copies
    pointers to the arrays describing the actual data, from the
    `xarray` dataset to the fields or domains. No actual data is
    copied.

    `cfdm.from_xarray` treats the `xarray` dataset as if it were an
    in-memory view of a netCDF dataset (even if it wasn't created as
    such), and creates the same CF field or domain constructs that
    `cfdm.read` would if it were to read that netCDF dataset.

    .. warning:: For optimal performance and minimal memory usage,
                 open `xarray` datasets from disk with
                 ``decode_cf=False``. This is **not** the default for
                 `xarray.open_dataset` or `xarray.open_datatree`.

                 If the dataset is opened with the default
                 ``decode_cf=True``, the automatic reversal of
                 xarray's CF decoding for selected variables will
                 eagerly load their data arrays into memory.  This
                 applies to variables with explicit ``_FillValue`` or
                 ``missing_value`` attributes, and to variables
                 decoded into non-numeric time or timedelta objects.

                 This is never an issue for datasets created with
                 `cfdm.to_xarray`:
                 ``cfdm.from_xarray(cfdm.to_xarray(f))`` will never
                 load those data arrays into memory.

    .. versionadded:: NEXTVERSION

    .. seealso:: `cfdm.to_xarray`, `cfdm.read`

    :Parameters:

        ds: `xarray.Dataset` or `xarray.DataTree`
            The `xarray` dataset to be converted. The group structure
            of an `xarray.DataTree` instance is preserved in the
            returned field or domains.

        domain: `bool`, optional
            If False (the default) then return only field constructs
            that are defined by CF data variables in the `xarray`
            dataset, ignoring all CF domain variables. If True then
            only the domain constructs that are explicitly defined by
            CF domain variables in the `xarray` dataset are returned.

    :Returns:

        sequence of `Field` or `Domain`
            The equivalent fields or domains.

    :Examples:

    Create some field constructs, convert them to an `xarray` dataset,
    convert the `xarray` dataset back to field constructs, and show
    that (in this case) no information has been lost.

    >>> f = cfdm.example_fields(0, 7)
    >>> f
    [<Field: specific_humidity(latitude(5), longitude(8)) 1>,
     <Field: eastward_wind(time(3), air_pressure(1), grid_latitude(4), grid_longitude(5)) m s-1>]
    >>> ds = cfdm.to_xarray(f)
    >>> ds
    <xarray.Dataset> Size: 3kB
    Dimensions:                     (lat: 5, lon: 8, time_1: 3, air_pressure: 1,
                                     grid_latitude: 4, grid_longitude: 5,
                                     bounds2: 2, bounds4: 4)
    Coordinates:
      * lat                         (lat) float64 40B -75.0 -45.0 0.0 45.0 75.0
      * lon                         (lon) float64 64B 22.5 67.5 ... 292.5 337.5
      * time_1                      (time_1) float64 24B 120.5 121.5 122.5
      * air_pressure                (air_pressure) float64 8B 850.0
      * grid_latitude               (grid_latitude) float64 32B 0.44 0.0 -0.44 -0.88
      * grid_longitude              (grid_longitude) float64 40B -1.18 ... 0.58
        latitude                    (grid_latitude, grid_longitude) float64 160B dask.array<chunksize=(4, 5), meta=np.ndarray>
        longitude                   (grid_latitude, grid_longitude) float64 160B dask.array<chunksize=(4, 5), meta=np.ndarray>
        time                        float64 8B dask.array<chunksize=(), meta=np.ndarray>
    Dimensions without coordinates: bounds2, bounds4
    Data variables:
        lat_bnds                    (lat, bounds2) float64 80B dask.array<chunksize=(5, 2), meta=np.ndarray>
        lon_bnds                    (lon, bounds2) float64 128B dask.array<chunksize=(8, 2), meta=np.ndarray>
        q                           (lat, lon) float64 320B dask.array<chunksize=(5, 8), meta=np.ndarray>
        bounds                      (time_1, bounds2) float64 48B dask.array<chunksize=(3, 2), meta=np.ndarray>
        bounds_1                    (grid_latitude, bounds2) float64 64B dask.array<chunksize=(4, 2), meta=np.ndarray>
        bounds_2                    (grid_longitude, bounds2) float64 80B dask.array<chunksize=(5, 2), meta=np.ndarray>
        latitude_bounds             (grid_latitude, grid_longitude, bounds4) float64 640B dask.array<chunksize=(4, 5, 4), meta=np.ndarray>
        bounds_3                    (grid_latitude, grid_longitude, bounds4) float64 640B dask.array<chunksize=(4, 5, 4), meta=np.ndarray>
        rotated_latitude_longitude  object 8B nan
        ua                          (time_1, air_pressure, grid_latitude, grid_longitude) float32 240B dask.array<chunksize=(3, 1, 4, 5), meta=np.ndarray>
    Attributes:
        Conventions:  CF-1.13
    >>> g = cfdm.from_xarray(ds)
    >>> g
    [<Field: specific_humidity(latitude(5), longitude(8)) 1>,
     <Field: eastward_wind(time(3), air_pressure(1), grid_latitude(4), grid_longitude(5)) m s-1>]
    >>> [field1.equals(field0) for field0, field1 in zip(f, g)]
    [True, True]

    """
    try:
        import xarray  # noqa: F401
    except ImportError as e:
        raise ImportError(
            f"{e}. Must install xarray "
            "to allow the conversion to and from an xarray dataset"
        )

    from . import read

    return read(ds, domain=domain)


def to_xarray(f, group=True):
    """Convert CF field or domain constructs to an `xarray` dataset.

    `cfdm.to_xarray` is an in-memory operation which does two things:
    it maps the CF constructs onto `xarray` dataset variables and
    attributes; and it copies pointers to the arrays describing the
    actual data, from the fields or domains to the `xarray`
    dataset. No actual data is copied.

    In general, `cfdm.to_xarray` creates an `xarray` dataset that is
    an in-memory view of the netCDF dataset that would have been
    created by writing the CF field or domain constructs to disk with
    `cfdm.write`.

    .. tip:: **A very convenient way to access uncompressed CF data in
             an xarray dataset**

             When `cfdm.read` reads fields and domains from datasets
             with CF compression-by-convention features (discrete
             sampling geometries, cell geometries, coordinate
             subsampling, gathering, etc.), these are represented as
             uncompressed views of the data stored in lazy Dask
             arrays. Because these Dask arrays are passed on unchanged
             to an xarray dataset, `cfdm.read` and `cfdm.to_xarray`
             together provide a means to directly access uncompressed CF
             data in xarray::

             >>> f = cfdm.read(<datasets>)
             >>> ds = cfdm.to_xarray(f)

    .. tip:: **Integration with cf_xarray**

             If the `cf_xarray` package
             (https://cf-xarray.readthedocs.io) is installed then the
             `cf_xarray` accessors that allow some interpretation of
             CF attributes will be present on the xarray dataset.

    .. versionadded:: NEXTVERSION

    .. seealso:: `cfdm.from_xarray`, `cfdm.write`

    :Parameters:

        f: (sequence of) `Field` or `Domain`
            The fields or domains to be converted.

        group: `bool`, optional
            If False then create a "flat" `xarray` dataset, i.e. one
            with only the root group, regardless of any group
            structure specified by the netCDF interfaces of the
            fields, domains, or their components. If True (the
            default) then any sub-groups will be created and
            populated.

    :Returns:

        `xarray.Dataset` or `xarray.DataTree`
            The equivalent `xarray` dataset.

            If there are no sub-groups of the root group, or if
            *group* is False, then an `xarray.Dataset` is returned.

            If there are sub-groups of the root group and *group* is
            True, then an `xarray.DataTree` is returned.

    :Examples:

    Create some field constructs, convert them to an `xarray` dataset,
    convert the `xarray` dataset back to field constructs, and show
    that (in this case) no information has been lost.

    >>> f = cfdm.example_fields(0, 7)
    >>> f
    [<Field: specific_humidity(latitude(5), longitude(8)) 1>,
     <Field: eastward_wind(time(3), air_pressure(1), grid_latitude(4), grid_longitude(5)) m s-1>]
    >>> ds = cfdm.to_xarray(f)
    >>> ds
    <xarray.Dataset> Size: 3kB
    Dimensions:                     (lat: 5, lon: 8, time_1: 3, air_pressure: 1,
                                     grid_latitude: 4, grid_longitude: 5,
                                     bounds2: 2, bounds4: 4)
    Coordinates:
      * lat                         (lat) float64 40B -75.0 -45.0 0.0 45.0 75.0
      * lon                         (lon) float64 64B 22.5 67.5 ... 292.5 337.5
      * time_1                      (time_1) float64 24B 120.5 121.5 122.5
      * air_pressure                (air_pressure) float64 8B 850.0
      * grid_latitude               (grid_latitude) float64 32B 0.44 0.0 -0.44 -0.88
      * grid_longitude              (grid_longitude) float64 40B -1.18 ... 0.58
        latitude                    (grid_latitude, grid_longitude) float64 160B dask.array<chunksize=(4, 5), meta=np.ndarray>
        longitude                   (grid_latitude, grid_longitude) float64 160B dask.array<chunksize=(4, 5), meta=np.ndarray>
        time                        float64 8B dask.array<chunksize=(), meta=np.ndarray>
    Dimensions without coordinates: bounds2, bounds4
    Data variables:
        lat_bnds                    (lat, bounds2) float64 80B dask.array<chunksize=(5, 2), meta=np.ndarray>
        lon_bnds                    (lon, bounds2) float64 128B dask.array<chunksize=(8, 2), meta=np.ndarray>
        q                           (lat, lon) float64 320B dask.array<chunksize=(5, 8), meta=np.ndarray>
        bounds                      (time_1, bounds2) float64 48B dask.array<chunksize=(3, 2), meta=np.ndarray>
        bounds_1                    (grid_latitude, bounds2) float64 64B dask.array<chunksize=(4, 2), meta=np.ndarray>
        bounds_2                    (grid_longitude, bounds2) float64 80B dask.array<chunksize=(5, 2), meta=np.ndarray>
        latitude_bounds             (grid_latitude, grid_longitude, bounds4) float64 640B dask.array<chunksize=(4, 5, 4), meta=np.ndarray>
        bounds_3                    (grid_latitude, grid_longitude, bounds4) float64 640B dask.array<chunksize=(4, 5, 4), meta=np.ndarray>
        rotated_latitude_longitude  object 8B nan
        ua                          (time_1, air_pressure, grid_latitude, grid_longitude) float32 240B dask.array<chunksize=(3, 1, 4, 5), meta=np.ndarray>
    Attributes:
        Conventions:  CF-1.13
    >>> g = cfdm.from_xarray(ds)
    >>> g
    [<Field: specific_humidity(latitude(5), longitude(8)) 1>,
     <Field: eastward_wind(time(3), air_pressure(1), grid_latitude(4), grid_longitude(5)) m s-1>]
    >>> [field1.equals(field0) for field0, field1 in zip(f, g)]
    [True, True]

    """
    try:
        import xarray  # noqa: F401
    except ImportError as e:
        raise ImportError(
            f"{e}. Must install xarray "
            "to allow the conversion to and from an xarray dataset"
        )

    from . import write

    return write(f, fmt="XARRAY", group=group)
