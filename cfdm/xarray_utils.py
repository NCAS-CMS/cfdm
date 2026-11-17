def from_xarray(ds, domain=False):
    """Convert an `xarray` dataset to CF field or domain constructs.

    `cfdm.from_xarray` is an entirely in-memory operation which does
    two things: it maps the `xarray` dataset variables and attributes
    onto CF constructs; and it copies pointers to the arrays
    describing the actual data, from the `xarray` dataset to the
    fields or domains. No actual data is copied.

    .. note:: **For best results, the xarray dataset will have been
              created with none of xarray's own CF decoding applied to
              it**, because xarray's partial CF decoding may interfere
              adversely with the complete CF-compliant decoding that
              is always applied by `cfdm.from_xarray`.

              If an xarray dataset is created with a call to
              `xarray.open_dataset` or `xarray.open_datatree` that
              uses the ``decode_cf=False, mask_and_scale=False``
              parameter settings, then `cfdm.from_xarray` will always
              work as intended.

    .. versionadded:: NEXTVERSION

    .. seealso:: `cfdm.to_xarray`

    :Parameters:

        ds: `xarray.Dataset` or `xarray.DataTree`
            The `xarray` dataset to be converted.

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
    from . import read

    return read(ds, domain=domain)


def to_xarray(f, group=True):
    """Convert CF field or domain constructs to an `xarray` dataset.

    `cfdm.to_xarray` is an entirely in-memory operation which does two
    things: it maps the CF constructs onto `xarray` dataset variables
    and attributes; and it copies pointers to the arrays describing
    the actual data, from the fields or domains to the `xarray`
    dataset. No actual data is copied.

    If the `cf_xarray` package (https://cf-xarray.readthedocs.io) is
    installed then the `cf_xarray` accessors that allow some
    interpretation of CF attributes will be present on the returned
    `xarray` objects.

    .. versionadded:: NEXTVERSION

    .. seealso:: `cfdm.from_xarray`

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
    from . import write

    return write(f, fmt="XARRAY", group=group)
