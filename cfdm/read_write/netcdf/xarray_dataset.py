
class XarrayDataset:
    """An adapter that mimics netCDF4.Dataset for xarray."""
    def __init__(self):
        import xarray as xr

        # xarray dataset
        self.ds = xr.Dataset()        
        self.attrs =  self.ds.attrs
        self.coords =  {}
        self.data_vars = {}
        
        # xarray variable class
        self.DataArray = xr.DataArray
        
    def createDimension(self, **kwargs):
        # xarray handles dimensions implicitly, but we can 
        # initialize it by adding a dummy coordinate if needed.
        pass

    def createVariable(self, varname, dtype, dimensions, coordinate=False):
        import xarray as xr
       
        # Instantiate placeholder data (often lazy/dask in cfdm)
        # Note: cfdm often passes data later, so we start with an empty array
#        data = np.ma.masked_all([0] * len(dimensions), dtype=dtype) 
        var = XarrayVariable(dims=dimensions, name=varname,dtype=dtype)
       

        if coordinate:
            self.coords[varname] = var
        else:            
            self.data_vars[varname] = var
        
        return var

    def setncatts(self, attributes):
        self.ds.attrs.update(attributes)

    def finalise(self):
        for name, var in  self.coords.items():
            self.ds.coords[name] = var.finalise()

        for name, var in  self.data_vars.items():
            self.ds[name] = var.finalise()
        print (1111, self.ds)
        return self.ds


class XarrayVariable:
    def __init__(self, dims, name, dtype):
        self.dims = dims
        self.name = name
        self.attrs = {}
        self.dtype = dtype
        
    def setncatts(self, attributes):
        self.attrs.update(attributes)

    def finalise(self):
        import xarray as xr

        if not hasattr(self, 'data') and not self.dims:
            import numpy as np
            self.data = np.ma.masked_all((), dtype=self.dtype) 
             
        
        return xr.DataArray(data=self.data, dims=self.dims, name=self.name, attrs=self.attrs)
