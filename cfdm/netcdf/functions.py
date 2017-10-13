from os.path import isfile

from netCDF4 import Dataset as netCDF4_Dataset

def _open_netcdf_file(filename, mode, fmt='NETCDF4'):
    '''

Open a netCDF file and read it into a netCDF4.Dataset object.

If the file is already open then the existing netCDF4.Dataset object
will be returned.

:Parameters:

    filename : str
        The netCDF file to be opened.

:Returns:

    out : netCDF4.Dataset
         A netCDF4.Dataset instance for the netCDF file.

:Examples:

>>> nc1 = _open_netcdf_file('file.nc')
>>> nc1
<netCDF4.Dataset at 0x1a7dad0>
>>> nc2 = _open_netcdf_file('file.nc')
>>> nc2 is nc1
True

'''
    if mode in ('a', 'r+'):
        if not isfile(filename):
            nc = netCDF4_Dataset(filename, 'w', format=fmt) 
            nc.close()

    try:        
        nc = netCDF4_Dataset(filename, mode, format=fmt)
    except RuntimeError as runtime_error:
        raise RuntimeError("{}: {}".format(runtime_error, filename))

    return nc
#--- End: def
