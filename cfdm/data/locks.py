from dask.utils import SerializableLock

# Global lock for netCDFfile access
netcdf_lock = SerializableLock()
