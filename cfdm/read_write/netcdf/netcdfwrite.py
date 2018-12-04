from __future__ import print_function
from builtins import (str, zip)
from past.builtins import basestring

import copy
import os

import numpy
import netCDF4

#from ....functions import abspath, flat

### numpy.count_nonzero(numpy.ma.count(coordinates, axis=-1))

from .. import IOWrite

from . import constants

zzz = False

class NetCDFWrite(IOWrite):
    '''
    '''

    def _create_netcdf_variable_name(self, parent, default):
#                                     force_use_existing=False):
        '''
        
:Parameter:
        
    parent:
           
    default: `str`
    
:Returns:

    out: `str`
        The netCDF variable name.

        '''
        ncvar = self.implementation.get_ncvar(parent, None)

#        if force_use_existing:
#            if ncvar is None:
#                raise ValueError("asdasdads TODO")
#
#            return ncvar
            
        if ncvar is None:
            try:
                ncvar = self.implementation.get_property(parent,
                                                         'standard_name', default)
            except AttributeError:
                ncvar = default
        #--- End: if
                
        return self._netcdf_name(ncvar)
    #--- End: def
    
    def _netcdf_name(self, base, dimsize=None):
        '''Return a new netCDF variable or dimension name.
    
:Parameters:

    base: `str`

    dimsize: `int`, optional

:Returns:

    out: `str`
        NetCDF dimension name or netCDF variable name.

        '''
        g = self.write_vars

        ncvar_names = g['ncvar_names']
        ncdim_names = g['ncdim_to_size']

        existing_names = g['ncvar_names'].union(ncdim_names )
        
        if dimsize is not None:
            if base in ncdim_names and dimsize == g['ncdim_to_size'][base]:
                # Return the name of an existing netCDF dimension with
                # this name and this size
                return base
        #--- End: if
    
        if base in existing_names:
            counter = g.setdefault('count_'+base, 1)
        
            ncvar = '{0}_{1}'.format(base, counter)
            while ncvar in existing_names:
                counter += 1
                ncvar = '{0}_{1}'.format(base, counter)
        else:
            ncvar = base


        ncvar = ncvar.replace(' ', '_')
            
        ncvar_names.add(ncvar)
    
        return ncvar
    #--- End: def
    
    def _write_attributes(self, parent, ncvar, extra={}, omit=()):
        '''
:Examples 1:

>>> w._write_attributes(x, 'lat')
    
:Parameters:

    parent:

    ncvar: `str`

    extra: `dict`, optional
    
    omit: sequence of `str`, optional

:Returns:

    `None`

:Examples 2:
    
        '''
        netcdf_attrs = self.implementation.get_properties(parent)
        
        netcdf_attrs.update(extra)
#        netcdf_attrs.pop('_FillValue', None)
    
        for attr in omit:
            netcdf_attrs.pop(attr, None) 
    
        if not netcdf_attrs:
            return
        
        self.write_vars['nc'][ncvar].setncatts(netcdf_attrs)

        if zzz:
            self.write_vars['zzz'].write('\n{}.setncatts({})\n'.format(ncvar, netcdf_attrs))            
    #--- End: def
    
    def _character_array(self, array):
        '''Convert a numpy string array to a numpy character array wih an
extra trailing dimension.
    
:Parameters:

    array: `numpy.ndarray`

:Returns:

    out: `numpy.ndarray`

:Examples:

>>> print a, a.shape, a.dtype.itemsize
['fu' 'bar'] (2,) 3
>>> b = _character_array(a)
>>> print b, b.shape, b.dtype.itemsize
[['f' 'u' ' ']
 ['b' 'a' 'r']] (2, 3) 1

>>> print a, a.shape, a.dtype.itemsize
[-- 'bar'] (2,) 3
>>> b = _character_array(a)
>>> print b, b.shape, b.dtype.itemsize
[[-- -- --]
 ['b' 'a' 'r']] (2, 3) 1

        '''
#        strlen = array.dtype.itemsize
        original_shape = array.shape
        original_size  = array.size

        masked = numpy.ma.isMA(array)
        if masked:
            fill_value = array.fill_value
            mask = array.mask
            array = numpy.ma.filled(array, fill_value='')

        if array.dtype.kind == 'U':
            array = array.astype('S')
#        print ('A', repr(array))
        array = numpy.array(tuple(array.tostring().decode('ascii')), dtype='S1')
#        print ('B', repr(array))
#        else:
#            # dtype is 'U'
#            x = []
#            for s in array.flatten():
#                x.extend(tuple(s.ljust(N, '\x00')))
#
#            array = numpy.array(k, dtype='S1')               

        array.resize(original_shape + (array.size//original_size,))
#        if masked:        
#            array = numpy.ma.array(array, mask=mask, fill_value=fill_value)
        
#        if array.dtype.kind == 'U':
#            # Convert unicode to string
#            array = array.astype('S')
#            
#        new = netCDF4.stringtochar(array, encoding='none')
#        print('new=', repr(new))
##        print('AAAAAAAAAAAAAAAAAA new.shape=', new.shape, repr(new))
        
        if masked:
            array = numpy.ma.masked_where(array=='', array)
            array.set_fill_value(fill_value)

        if array.dtype.kind != 'S':
            raise ValueError("AAAAAAAAARRRRRRRRRRRRRRRGGGGGGGGGGHHHHHHHH")
        
#            new = numpy.ma.array(new, mask=mask, fill_value=fill_value)

#        new = numpy.ma.masked_all(shape + (strlen,), dtype='S1')
#        
#        for index in numpy.ndindex(shape):
#            value = array[index]
#            if value is numpy.ma.masked:
#                new[index] = numpy.ma.masked
#            else:
#                new[index] = tuple(value.ljust(strlen, ' ')) 
#        #--- End: for

#        print('new=', repr(new))
        return array
    #--- End: def
    
    def _datatype(self, variable):
        '''Return the netCDF4.createVariable datatype corresponding to the
datatype of the array of the input variable
    
For example, if variable.dtype is 'float32', then 'f4' will be
returned.
    
Numpy string data types will return 'S1' regardless of the numpy
string length. This means that the required conversion of
multi-character datatype numpy arrays into single-character datatype
numpy arrays (with an extra trailing dimension) is expected to be done
elsewhere (currently in the _write_netcdf_variable method).
    
If the input variable has no `!dtype` attribute (or it is None) then
'S1' is returned.
    
 :Parameters:
 
     variable: 
         Any object with a `!dtype` attribute whose value is a
         `numpy.dtype` object or `None`.
 
 :Returns:
 
     out: `str`
        The `netCDF4.createVariable` data type corresponding to the
        datatype of the array of the input variable.

        '''
        g = self.write_vars

        data = self.implementation.get_data(variable, None)
        if data is None:
            return 'S1'

        dtype = getattr(data, 'dtype', None)
#        print('dtype=', dtype)
#        if not hasattr(variable, 'dtype'):
#            dtype = numpy.asanyarray(variable).dtype
        if dtype is None or dtype.char == 'S':
            return 'S1'            
    
#        dtype = variable.dtype
    
#        convert_dtype = g['datatype']
    
        new_dtype = g['datatype'].get(dtype, None)
        if new_dtype is not None:
            dtype = new_dtype
            
        return '{0}{1}'.format(dtype.kind, dtype.itemsize)
    #--- End: def
    
    def _string_length_dimension(self, size):
        '''Create, if necessary, a netCDF dimension for string variables.
    
:Parameters:

    size: `int`

:Returns:

    out: `str`
        The netCDF dimension name.

        '''
        g = self.write_vars

        # ----------------------------------------------------------------
        # Create a new dimension for the maximum string length
        # ----------------------------------------------------------------
        ncdim = self._netcdf_name('strlen{0}'.format(size), dimsize=size)
        
        if ncdim not in g['ncdim_to_size']:
            # This string length dimension needs creating
            g['ncdim_to_size'][ncdim] = size
            g['netcdf'].createDimension(ncdim, size)
            if zzz:
                g['zzz'].write('\nnc.createDimension({ncdim!r}, {size!r})\n'.format(
                    ncdim=ncdim, size=size))
        return ncdim
    #--- End: def
    
    def _netcdf_dimensions(self, field, key, construct):
        '''Return a tuple of the netCDF dimension names for the axes of a
metadata construct.
    
If the construct has no data, then return `None`

:Parameters:

    field: `Field`

    key: `str`

:Returns:

    out: `tuple` or `None`
        The netCDF dimension names, or `None` if there are no data.

        '''
        g = self.write_vars

        domain_axes = self.implementation.get_construct_axes(field, key)

        if not domain_axes:
            # No data
            return

        domain_axes = tuple(domain_axes)
        
        ncdims = [g['axis_to_ncdim'][axis] for axis in domain_axes]

        compression_type = self.implementation.get_compression_type(construct)
        if compression_type:
            sample_dimension_position = self.implementation.get_sample_dimension_position(construct)
            compressed_axes = tuple(self.implementation.get_compressed_axes(field, key, construct))
            compressed_ncdims = tuple([g['axis_to_ncdim'][axis] for axis in compressed_axes])

            sample_ncdim = g['sample_ncdim'].get(compressed_ncdims)
            
            if compression_type == 'gathered':
                # ----------------------------------------------------
                # Compression by gathering
                # ----------------------------------------------------
                if sample_ncdim is None:
                    # The list variable has not yet been written to
                    # the file, so write it and also get the netCDF
                    # name of the sample dimension.
                    list_variable = self.implementation.get_list_variable(construct)
                    sample_ncdim = self._write_list_variable(
                        field,
                        list_variable,
                        compress=' '.join(compressed_ncdims))
                    g['sample_ncdim'][compressed_ncdims] = sample_ncdim

            elif compression_type == 'ragged contiguous':
                # ----------------------------------------------------
                # Compression by contiguous ragged array
                # ----------------------------------------------------
                # No need to do anything because i) the count variable
                # has already been written to the file, ii) we already
                # have the position of the sample dimension in the
                # compressed array, and iii) we already have the
                # netCDF name of the sample dimension.
                pass

            elif compression_type == 'ragged indexed':
                # ----------------------------------------------------
                # Compression by indexed ragged array
                # ----------------------------------------------------
                # No need to do anything because i) the index variable
                # has already been written to the file, ii) we already
                # have the position of the sample dimension in the
                # compressed array, and iii) we already have the
                # netCDF name of the sample dimension.
                pass
            elif compression_type == 'ragged indexed contiguous':
                pass
            else:
                raise ValueError(
"Can't write {!r}: Unknown compression type: {!r}".format(construct, compression_type))

            n = len(compressed_ncdims)
            ncdims[sample_dimension_position:sample_dimension_position+n] = [sample_ncdim]
        #--- End: if

        return tuple(ncdims)
    #--- End: def
        
    def _write_dimension(self, ncdim, f, axis=None, unlimited=False,
                         size=None):
        '''Write a netCDF dimension to the file.
    
:Parameters:
    
    ncdim: `str`
        The netCDF dimension name.

    f: `Field`
   
    axis: `str` or `None`
        The field's domain axis identifier.

    unlimited: `bool`, optional
        If True then create an unlimited dimension. By default
        dimensions are not unlimited.

    size: `int`, optional
        Must be set if *axis* is `None`.

:Returns:

    `None`
        
        '''
        g = self.write_vars
        verbose = g['verbose']
        
        if axis is not None:        
            if verbose:
                domain_axis = self.implementation.get_domain_axes(f)[axis]
                print('    Writing', repr(domain_axis), 'to netCDF dimension:', ncdim)

            size = self.implementation.get_domain_axis_size(f, axis)
        
#            g['ncdim_to_size'][ncdim] = size
            g['axis_to_ncdim'][axis] = ncdim
        #--- End: if
        
        g['ncdim_to_size'][ncdim] = size
        
        if unlimited:
            # Create an unlimited dimension
            size = None
            try:
                g['netcdf'].createDimension(ncdim, size)
            except RuntimeError as error:
                message = "Can't create unlimited dimension in {} file ({}).".format(
                    g['netcdf'].file_format, error)
    
                error = str(error)
                if error == 'NetCDF: NC_UNLIMITED size already in use':
                    raise RuntimeError(
message+" In a {} file only one unlimited dimension is allowed. Consider using a netCDF4 format.".format(g['netcdf'].file_format))
                    
                raise RuntimeError(message)
        else:
            try:
                g['netcdf'].createDimension(ncdim, size)
            except RuntimeError as error:
                raise RuntimeError(
                    "Can't create dimension of size {} in {} file ({})".format(
                        size, g['netcdf'].file_format, error))
        #--- End: if
        
        if zzz:
            g['zzz'].write('\nnc.createDimension({ncdim!r}, {size!r})\n'.format(
                ncdim=ncdim, size=size))

    #--- End: def
    
#    def _change_reference_datetime(self, coord):
#        '''
#    
#    :Parameters:
#    
#        coord : `Coordinate`
#    
#    :Returns:
#    
#        out : `Coordinate`
#    
#    '''
#        g = self.write_vars
#
#        if not coord.Units.isreftime:
#            return coord
#    
#        reference_datetime = g['reference_datetime']
#        if not reference_datetime:
#            return coord
#    
#        coord2 = coord.copy()
#        try:
#            coord2.reference_datetime = reference_datetime
#        except ValueError:
#            raise ValueError(
#    "Can't override coordinate reference date-time {!r} with {!r}".format(
#        coord.reference_datetime, reference_datetime))
#    
#        return coord2
#    #--- End: def
    
    def _write_dimension_coordinate(self, f, key, coord):
        '''Write a coordinate variable and its bound variable to the file.
    
This also writes a new netCDF dimension to the file and, if required,
a new netCDF dimension for the bounds.

:Parameters:

    f: `Field`
   
    key: `str`

    coord: `DimensionCoordinate`

:Returns:

    out: `str`
        The netCDF name of the dimension coordinate.

        '''
        g = self.write_vars

        seen = g['seen']
    
#        coord = self._change_reference_datetime(coord)

        axis = self.implementation.get_construct_axes(f, key)[0]

        create = False
        if not self._already_in_file(coord):
            create = True
        elif seen[id(coord)]['ncdims'] != ():
            if seen[id(coord)]['ncvar'] != seen[id(coord)]['ncdims'][0]:
                # Already seen this coordinate but it was an auxiliary
                # coordinate, so it needs to be created as a dimension
                # coordinate.
                create = True
        #--- End: if
    
        if create:
            ncvar = self._create_netcdf_variable_name(coord,
                                                      default='coordinate')
            
            # Create a new dimension,  ##if it is not a scalar coordinate
#            if self.implementation.get_data_ndim(coord) > 0:
            unlimited = self._unlimited(f, axis)
            self._write_dimension(ncvar, f, axis, unlimited=unlimited)
    
            ncdimensions = self._netcdf_dimensions(f, key, coord)
            
            # If this dimension coordinate has bounds then write the
            # bounds to the netCDF file and add the 'bounds' or
            # 'climatology' attribute to a dictionary of extra
            # attributes
            extra = self._write_bounds(coord, ncdimensions, ncvar)
    
            # Create a new dimension coordinate variable
            self._write_netcdf_variable(ncvar, ncdimensions, coord, extra=extra)
        else:
            ncvar = seen[id(coord)]['ncvar']

        g['key_to_ncvar'][key] = ncvar
    
        g['axis_to_ncdim'][axis] = ncvar

        return ncvar
    #--- End: def

    def _write_count_variable(self, f, count_variable, ncdim=None,
                              create_ncdim=True):
        '''

        '''
        g = self.write_vars
    
        if not self._already_in_file(count_variable):
            ncvar = self._create_netcdf_variable_name(count_variable,
                                                      default='count')

            if create_ncdim:
                ncdim = self._netcdf_name(ncdim)
                self._write_dimension(
                    ncdim, f, None,
                    size=self.implementation.get_data_size(count_variable))

            # --------------------------------------------------------
            # Create the sample dimension
            # --------------------------------------------------------
            _ = self.implementation.nc_get_sample_dimension(count_variable, 'element')
            sample_ncdim = self._netcdf_name(_)
            self._write_dimension(
                sample_ncdim, f, None,
                size=int(self.implementation.get_data_sum(count_variable)))
            
            # Assume that the instance axis is the first in the data
            # array
#            instance_axis = self.implementation.get_field_data_axes(f)[0]
#            ncdim = g['axis_to_ncdim'][instance_axis]
            
            extra = {'sample_dimension': sample_ncdim}

            # Create a new list variable
            self._write_netcdf_variable(ncvar, (ncdim,),
                                        count_variable, extra=extra)

            g['count_variable_sample_dimension'][ncvar] = sample_ncdim
        else:
            ncvar = g['seen'][id(count_variable)]['ncvar']
            sample_ncdim = g['count_variable_sample_dimension'][ncvar]
    
        return sample_ncdim
    #--- End: def
    
    def _write_index_variable(self, f, index_variable, ncdim=None,
                              create_ncdim=True,
                              instance_dimension=None,
                              sample_dimension=None):
        '''

        '''
        g = self.write_vars
    
        if not self._already_in_file(index_variable):
            ncvar = self._create_netcdf_variable_name(index_variable,
                                                      default='index')

            if create_ncdim:
                ncdim = self._netcdf_name(ncdim)
                self._write_dimension(
                    ncdim, f, None,
                    size=self.implementation.get_data_size(index_variable))
                
#            if sample_dimension is None:
#                sample_dimension = ncdim
#                _ = self.implementation.nc_get_sample_dimension(index_variable, 'element')
#                sample_ncdim = self._netcdf_name(_)
#                self._write_dimension(
#                    sample_ncdim, f, None,
#                    size=self.implementation.get_data_size(index_variable))

#            instance_axis = self.implementation.get_field_data_axes(f)[0]
#            instance_dimension = g['axis_to_ncdim'][instance_axis]
 
#            instance_ncdim =  self.implementation.nc_get_instance_dimension(
#                index_variable, 'instance')
            
            extra = {'instance_dimension': instance_dimension}

            # Create a new list variable
            self._write_netcdf_variable(ncvar, (ncdim,),
                                        index_variable, extra=extra)

            g['index_variable_sample_dimension'][ncvar] = sample_dimension
        else:
            ncvar = g['seen'][id(index_variable)]['ncvar']
            sample_ncdim = g['index_variable_sample_dimension'][ncvar]
    
        return sample_dimension
    #--- End: def
    
    def _write_list_variable(self, f, list_variable, compress):
        '''

        '''        
        g = self.write_vars

        create = not self._already_in_file(list_variable)
    
        if create:
            ncvar = self._create_netcdf_variable_name(list_variable,
                                                      default='list')
            
            # Create a new dimension
            self._write_dimension(
                ncvar, f,
                size=self.implementation.get_data_size(list_variable))
            
            extra = {'compress': compress}
    
            # Create a new list variable
            self._write_netcdf_variable(ncvar, (ncvar,),
                                        list_variable, extra=extra)


            self.implementation.nc_set_variable(list_variable, ncvar) # Why?
        else:
            ncvar = g['seen'][id(list_variable)]['ncvar']

        return ncvar
    #--- End: def
    
    def _write_scalar_data(self, value, ncvar):
        '''Write a dimension coordinate and bounds to the netCDF file.
    
This also writes a new netCDF dimension to the file and, if required,
a new netCDF bounds dimension.

.. note:: This function updates ``g['seen']``.

:Parameters:

    data: `Data`
   
    ncvar: `str`

:Returns:

    out: `str`
        The netCDF name of the scalar data variable

        '''
        g = self.write_vars

        seen = g['seen']
    
        create = not self._already_in_file(value, ncdims=())
    
        if create:
            ncvar = self._netcdf_name(ncvar) # DCH ?
            
            # Create a new dimension coordinate variable
            self._write_netcdf_variable(ncvar, (), value)
        else:
            ncvar = seen[id(value)]['ncvar']
    
        return ncvar
    #--- End: def
    
    def _already_in_file(self, variable, ncdims=None, ignore_type=False):
        '''Return True if a variable is logically equal any variable in the
g['seen'] dictionary.
    
If this is the case then the variable has already been written to the
output netCDF file and so we don't need to do it again.
    
If 'ncdims' is set then a extra condition for equality is applied,
namely that of 'ncdims' being equal to the netCDF dimensions (names
and order) to that of a variable in the g['seen'] dictionary.
    
When True is returned, the input variable is added to the g['seen']
dictionary.
    
:Parameters:
    
    variable : 

    ncdims : tuple, optional

:Returns:

    out: `bool`
        True if the variable has already been written to the file,
        False otherwise.

        '''
        g = self.write_vars

        seen = g['seen']
    
        for value in seen.values():
            if ncdims is not None and ncdims != value['ncdims']:
                # The netCDF dimensions (names and order) of the input
                # variable are different to those of this variable in
                # the 'seen' dictionary
                continue
    
            # Still here?
            if self.implementation.equal_constructs(variable, value['variable'],
                                                    ignore_type=ignore_type):
                seen[id(variable)] = {'variable': variable,
                                      'ncvar'   : value['ncvar'],
                                      'ncdims'  : value['ncdims']}
                return True
        #--- End: for
        
        return False
    #--- End: def
    
    def _write_bounds(self, coord, coord_ncdimensions, coord_ncvar):
        '''Create a bounds netCDF variable, creating a new bounds netCDF
dimension if required. Return the bounds variable's netCDF variable
name.
    
.. note:: This function updates ``g['netcdf']``.
    
:Parameters:

    coord: `BoundedVariable`

    coord_ncdimensions: `tuple`
        The ordered netCDF dimension names of the coordinate's
        dimensions (which do not include the bounds dimension).

    coord_ncvar: `str`
        The netCDF variable name of the parent variable

:Returns:

    out: `dict`

:Examples:

>>> extra = _write_bounds(c, ('dim2',))

    '''
        g = self.write_vars

        bounds = self.implementation.get_bounds(coord, None)
        if bounds is None:
            return {}

        data = self.implementation.get_data(bounds, None) 
        if data is None:
            return {}

        # Still here? Then this coordinate has a bounds attribute
        # which contains data.
        extra = {}
        
        size = data.shape[-1]
    
        ncdim = self._netcdf_name('bounds{0}'.format(size), dimsize=size)
    
        # Check if this bounds variable has not been previously
        # created.
        ncdimensions = coord_ncdimensions +(ncdim,)        
        if self._already_in_file(bounds, ncdimensions):
            # This bounds variable has been previously created, so no
            # need to do so again.
            ncvar = g['seen'][id(bounds)]['ncvar']
    
        else:
    
            # This bounds variable has not been previously created, so
            # create it now.
            ncdim_to_size = g['ncdim_to_size']
            if ncdim not in ncdim_to_size:
                if g['verbose']:
                    print('    Writing size', size, 'netCDF dimension for bounds:', ncdim)
                    
                ncdim_to_size[ncdim] = size
                g['netcdf'].createDimension(ncdim, size)
                if zzz:
                    g['zzz'].write('\nnc.createDimension({ncdim!r}, {size!r})\n'.format(
                        ncdim=ncdim, size=size))

            ncvar = self.implementation.get_ncvar(bounds, coord_ncvar+'_bounds')                
            ncvar = self._netcdf_name(ncvar)
            
            # Note that, in a field, bounds always have equal units to
            # their parent coordinate
    
            # Select properties to omit
            omit = []
            for prop in g['omit_bounds_properties']:
                if self.implementation.has_property(coord, prop):
                    omit.append(prop)
            #--- End: for
    
            # Create the bounds netCDF variable
            self._write_netcdf_variable(ncvar, ncdimensions, bounds,
                                        omit=omit)
        #--- End: if
    
        if self.implementation.is_climatology(coord):
            extra['climatology'] = ncvar
        else:
            extra['bounds'] = ncvar
    
        g['bounds'][coord_ncvar] = ncvar
            
        return extra
    #--- End: def
            
    def _write_scalar_coordinate(self, f, key, coord_1d, axis, coordinates,
                                 extra={}):
        '''Write a scalar coordinate and its bounds to the netCDF file.
    
It is assumed that the input coordinate is has size 1, but this is not
checked.
    
If an equal scalar coordinate has already been written to the file
then the input coordinate is not written.
    
:Parameters:

    f: `Field`
   
    axis : str
        The field's axis identifier for the scalar coordinate.

    coordinates: `list`

:Returns:

    coordinates: `list`
        The updated list of netCDF auxiliary coordinate names.

        '''
        g = self.write_vars

#        coord = self._change_reference_datetime(coord)
            
        scalar_coord = self.implementation.squeeze(coord_1d, axes=0)
    
        if not self._already_in_file(scalar_coord, ()):
            ncvar = self._create_netcdf_variable_name(scalar_coord,
                                                      default='scalar')                        

            # If this scalar coordinate has bounds then create the
            # bounds netCDF variable and add the bounds or climatology
            # attribute to the dictionary of extra attributes
            bounds_extra = self._write_bounds(scalar_coord, (), ncvar)
    
            # Create a new scalar coordinate variable
            self._write_netcdf_variable(ncvar, (), scalar_coord,
                                        extra=bounds_extra)
    
        else:
            # This scalar coordinate has already been written to the
            # file
            ncvar = g['seen'][id(scalar_coord)]['ncvar']
    
        g['axis_to_ncscalar'][axis] = ncvar
    
        g['key_to_ncvar'][key] = ncvar
    
        coordinates.append(ncvar)
    
        return coordinates
    #--- End: def

    def _write_auxiliary_coordinate(self, f, key, coord, coordinates):
        '''Write auxiliary coordinates and bounds to the netCDF file.
    
If an equal auxiliary coordinate has already been written to the file
then the input coordinate is not written.
    
:Parameters:

    f: `Field`
   
    key: `str`

    coord: `Coordinate`

    coordinates: `list`

:Returns:

    coordinates: `list`
        The list of netCDF auxiliary coordinate names updated in
        place.

:Examples:

>>> coordinates = _write_auxiliary_coordinate(f, 'aux2', coordinates)

        '''
        g = self.write_vars

#        coord = self._change_reference_datetime(coord)
        ncdimensions = self._netcdf_dimensions(f, key, coord)

        if self._already_in_file(coord, ncdimensions):
            ncvar = g['seen'][id(coord)]['ncvar']
        else:
            ncvar = self._create_netcdf_variable_name(coord,
                                                      default='auxiliary')

            

            # TODO: move setting of bounds ncvar to here
            
            # If this auxiliary coordinate has bounds then create the
            # bounds netCDF variable and add the bounds or climatology
            # attribute to the dictionary of extra attributes
            extra = self._write_bounds(coord, ncdimensions, ncvar)

            # Create a new auxiliary coordinate variable
            self._write_netcdf_variable(ncvar, ncdimensions, coord,
                                        extra=extra)
        
            g['key_to_ncvar'][key] = ncvar
        
        coordinates.append(ncvar)        

        return coordinates
    #--- End: def

    def _write_domain_ancillary(self, f, key, anc):
        '''Write a domain ancillary and its bounds to the netCDF file.
    
If an equal domain ancillary has already been written to the file athen
it is not re-written.

:Examples 1:

>>> ncvar = w._write_domain_ancillary(f, 'domainancillary2', d)
    
:Parameters:

    f: `Field`
   
    key: `str`
        The internal identifier of the domain ancillary object.

    anc: `DomainAncillary`
    
:Returns:

    out: `str`
        The netCDF variable name of the domain ancillary variable.

:Examples 2:

        '''
        g = self.write_vars

#        ncdimensions = tuple([g['axis_to_ncdim'][axis]
#                              for axis in self.implementation.get_construct_axes(f, key)])

        ncdimensions = self._netcdf_dimensions(f, key, anc)
        
        create = not self._already_in_file(anc, ncdimensions, ignore_type=True)
    
        if not create:
            ncvar = g['seen'][id(anc)]['ncvar']
        
        else:
            # See if we can set the default netCDF variable name to
            # its formula_terms term
            default = None
            for ref in self.implementation.get_coordinate_references(f).values():
                for term, da_key in ref.coordinate_conversion.domain_ancillaries().items(): # DCH ALERT
                    if da_key == key:
                        default = term
                        break
                #--- End: for
                if default is not None:
                    break
            #--- End: for
            if default is None:
                default='domain_ancillary'
                
            ncvar = self._create_netcdf_variable_name(anc,
                                                      default=default)
    
            # If this domain ancillary has bounds then create the bounds
            # netCDF variable
            self._write_bounds(anc, ncdimensions, ncvar)
    
            # Create a new domain ancillary variable
            self._write_netcdf_variable(ncvar, ncdimensions, anc)
        #--- End: if
    
        g['key_to_ncvar'][key] = ncvar
    
        return ncvar
    #--- End: def
      
    def _write_field_ancillary(self, f, key, anc):
        '''Write a field ancillary to the netCDF file.
    
If an equal field ancillary has already been written to the file then
it is not re-written.
    
:Parameters:

    f : `Field`
   
    key : str

    anc : `FieldAncillary`

:Returns:

    out: `str`
        The netCDF variable name of the field ancillary object.

:Examples:

>>> ncvar = _write_field_ancillary(f, 'fieldancillary2', anc)

    '''
        g = self.write_vars

#        ncdimensions = tuple([g['axis_to_ncdim'][axis]
#                              for axis in self.implementation.get_construct_axes(f, key)])
    
        ncdimensions = self._netcdf_dimensions(f, key, anc)
        
        create = not self._already_in_file(anc, ncdimensions)
    
        if not create:
            ncvar = g['seen'][id(anc)]['ncvar']    
        else:
            ncvar = self._create_netcdf_variable_name(anc, default='ancillary_data')

            # Create a new field ancillary variable
            self._write_netcdf_variable(ncvar, ncdimensions, anc)
    
        g['key_to_ncvar'][key] = ncvar
    
        return ncvar
    #--- End: def
      
    def _write_cell_measure(self, field, key, cell_measure):
        '''Write a cell measure construct to the netCDF file.

If an identical construct has already in the file then the cell
measure will not be written.

:Parameters:

    field: `Field`
        The field containing the cell measure.

    key: `str`
        The identifier of the cell measure (e.g. 'cellmeasure0').

    cell_measure: `CellMeasure`

:Returns:

    out: `str`
        The 'measure: ncvar'.

:Examples:

        '''
        g = self.write_vars

        measure = self.implementation.get_measure(cell_measure)
        if measure is None:
            raise ValueError(
"Can't create a netCDF cell measure variable without a 'measure' property")

        ncdimensions = self._netcdf_dimensions(field, key, cell_measure)

        if self._already_in_file(cell_measure, ncdimensions):
            # Use existing cell measure variable
            ncvar = g['seen'][id(cell_measure)]['ncvar']
        elif self.implementation.nc_get_external(cell_measure):
            # The cell measure is external
            ncvar = self._create_netcdf_variable_name(cell_measure, default='cell_measure')

            # Add ncvar to the global external_variables attribute
            self._set_external_variables(ncvar)

            # Create a new field to write out to the external file
            if g['external_file'] is not None:                
                self._create_external(field=field, construct_id=key,
                                      ncvar=ncvar, ncdimensions=ncdimensions)
        else:
            ncvar = self._create_netcdf_variable_name(cell_measure, default='cell_measure')

            # Create a new cell measure variable
            self._write_netcdf_variable(ncvar, ncdimensions, cell_measure)
                
        g['key_to_ncvar'][key] = ncvar
    
        # Update the field's cell_measures list
        return '{0}: {1}'.format(measure, ncvar)
    #--- End: def


    def _set_external_variables(self, ncvar):
        '''Add ncvar to the global external_variables attribute

        '''
        g = self.write_vars
        
        external_variables = g['external_variables']

        if external_variables:
            external_variables = '{} {}'.format(external_variables, ncvar)
        else:
            external_variables = ncvar
            g['global_attributes'].add('external_variables')

        g['netcdf'].setncattr('external_variables', external_variables)

        g['external_variables'] = external_variables
    #--- End: def
    
    def _create_external(self, field=None, construct_id=None,
                         ncvar=None, ncdimensions=None):
        '''TODO
        '''
        g = self.write_vars
        
        if ncdimensions is None:
            return

        # Still here?
        external = self.implementation.create_field(
            field=field,
            construct_id=construct_id)
        
        # Set the correct netCDF variable and dimension names
        self.implementation.nc_set_variable(external, ncvar)
        
        external_domain_axes = self.implementation.get_domain_axes(external)
        for ncdim, axis in zip(ncdimensions,
                               self.implementation.get_field_data_axes(external)):
            external_domain_axis = external_domain_axes[axis]
            self.implementation.nc_set_dimension(external_domain_axis, ncdim)
            
        g['external_fields'].append(external)

        return external
    #--- End: def
    
    def _createVariable(self, **kwargs):
        '''
        '''
        g = self.write_vars

        ncvar = kwargs['varname']
        
        g['nc'][ncvar] = g['netcdf'].createVariable(**kwargs)
        
        if zzz:
            g['zzz'].write('\n{} = nc.createVariable(\n    {})\n'.format(
                ncvar,
                ',\n    '.join("{}={!r}".format(k, v) for k, v in kwargs.items())))
    #--- End: def
    
    def _write_grid_mapping(self, f, ref, multiple_grid_mappings):
        '''Write a grid mapping georeference to the netCDF file.
    
.. note:: This function updates ``grid_mapping``, ``g['seen']``.

:Parameters:

    f: `Field`

    ref: `CoordinateReference`
        The grid mapping coordinate reference to write to the file.

    multiple_grid_mappings: `bool`

:Returns:

    out: `str`

:Examples:

        '''
        g = self.write_vars

        verbose = g['verbose']
        
        if self._already_in_file(ref):
            # Use existing grid_mapping variable
            ncvar = g['seen'][id(ref)]['ncvar']
    
        else:
            # Create a new grid mapping variable
            cc_parameters = self.implementation.get_coordinate_conversion_parameters(ref)
            default = cc_parameters.get('grid_mapping_name', 'grid_mapping')
            ncvar = self._create_netcdf_variable_name(ref, default=default)

            if verbose:
                print('    Writing', repr(ref), 'to netCDF variable:', ncvar)

#            args = [ncvar, 'S1', ()]
            kwargs = {'varname': ncvar,
                      'datatype': 'S1',
                      'dimensions': (),
                      'endian': g['endian']}
            kwargs.update(g['netcdf_compression'])

            self._createVariable(**kwargs)
            
#            g['nc'][ncvar] = g['netcdf'].createVariable(**kwargs) #ncvar, 'S1', (),
#                                                        endian=g['endian'],
#                                                        **g['netcdf_compression'])
#            if zzz:
#                g['zzz'].write('\n{} = nc.createVariable(\n    {})\n'.format(
#                    ncvar,
#                    ',\n    '.join("{}={!r}".format(k, v) for k, v in kwargs.items())))

                          
#            cref = ref.copy()
#            cref = ref.canonical(f) # NOTE: NOT converting units
    
            # Add named parameters
            parameters = self.implementation.get_datum_parameters(ref)
            parameters.update(cc_parameters)
            
            for term, value in list(parameters.items()):
                if value is None:
                    del parameters[term]
                    continue
                
                if numpy.size(value) == 1:
                    value = numpy.array(value, copy=False).item()
                else:
                    value = numpy.array(value, copy=False).tolist()

                parameters[term] = value

            # Add the grid mapping name property
#            grid_mapping_name = cc_parameters.get('grid_mapping_name', None)
#            if grid_mapping_name is not None:
#                parameters['grid_mapping_name'] = grid_mapping_name
                
            g['nc'][ncvar].setncatts(parameters)
            if zzz:
                g['zzz'].write('{}.setncatts({})\n'.format(ncvar, parameters))
                
            # Update the 'seen' dictionary
            g['seen'][id(ref)] = {'variable': ref, 
                                  'ncvar'   : ncvar,
                                  'ncdims'  : (), # Grid mappings have no netCDF dimensions
                              }
        #--- End: if

        if multiple_grid_mappings:
            return '{0}: {1}'.format(
                ncvar,
                ' '.join(
                    sorted([g['key_to_ncvar'][key]
                            for key in self.implementation.get_coordinate_reference_coordinates(ref)])))
        else:
            return ncvar
    #--- End: def
    
    def _write_netcdf_variable(self, ncvar, ncdimensions, cfvar,
                               omit=(), extra={}, fill=False,
                               data_variable=False):
        '''Create a netCDF variable from *cfvar* with name *ncvar* and
dimensions *ncdimensions*. The new netCDF variable's properties are
given by cfvar.properties(), less any given by the *omit* argument. If
a new string-length netCDF dimension is required then it will also be
created. The ``seen`` dictionary is updated for *cfvar*.
    
:Parameters:

    ncvar: `str`
        The netCDF name of the variable.

    dimensions: `tuple`
        The netCDF dimension names of the variable

    cfvar: `Variable`
        The coordinate, cell measure or field object to write to the
        file.

    omit: sequence of `str`, optional

    extra: `dict`, optional

:Returns:

    `None`

        '''
        g = self.write_vars
                
        verbose = g['verbose']
        
        if verbose:
            print('    Writing {!r}'.format(cfvar), end='')
     
        # ------------------------------------------------------------
        # Set the netCDF4.createVariable datatype
        # ------------------------------------------------------------
        datatype = self._datatype(cfvar)
        data = self.implementation.get_data(cfvar, None)

        original_ncdimensions = ncdimensions 
        
        if data is not None and datatype == 'S1':
            # --------------------------------------------------------
            # Convert a string data type numpy array into a
            # character data type ('S1') numpy array with an extra
            # trailing dimension.
            # --------------------------------------------------------
            strlen = data.dtype.itemsize
#            if strlen > 1:
            data = self._convert_to_char(data)
            ncdim = self._string_length_dimension(strlen)            
            ncdimensions = original_ncdimensions + (ncdim,)
        #--- End: if
        
        if verbose:
            print(' to netCDF variable: {}({})'.format(ncvar, ', '.join(ncdimensions)))

        # ------------------------------------------------------------
        # Find the fill value - the value that the variable's data get
        # filled before any data is written. if the fill value is
        # False then the variable is not pre-filled.
        # ------------------------------------------------------------
        if fill:
            fill_value = self.implementation.get_property(cfvar, '_FillValue', None)
        else:
            fill_value = False
    
        if data_variable:
            lsd = g['least_significant_digit']
        else:
            lsd = None
    
        # Set HDF chunk sizes
        chunksizes = None
    #    chunksizes = [size for i, size in sorted(cfvar.HDF_chunks().items())]
    #    if chunksizes == [None] * cfvar.get_data().ndim:
    #        chunksizes = None
    #
    #    if verbose:
    #        print '  chunksizes:', chunksizes

        # ------------------------------------------------------------
        # Create a new netCDF variable
        # ------------------------------------------------------------
        kwargs = {'varname'   : ncvar,
                  'datatype'  : datatype,
                  'dimensions': ncdimensions,
                  'endian'    : g['endian'],
                  'chunksizes': chunksizes}
        kwargs.update(g['netcdf_compression'])

        try:
            self._createVariable(**kwargs)
#            args = (ncvar, datatype, ncdimensions)
#            g['nc'][ncvar] = g['netcdf'].createVariable(**kwargs)
#                *args,
#                fill_value=fill_value,
#                least_significant_digit=lsd,
#                endian=g['endian'],
#                chunksizes=chunksizes,
#                **g['netcdf_compression'])
        except RuntimeError as error:
            error = str(error)
            if error == 'NetCDF: Not a valid data type or _FillValue type mismatch':
                raise ValueError(
"Can't write {} data from {!r} to a {} file. Consider using a netCDF4 format, or use the 'datatype' parameter, or change the datatype before writing.".format(
    cfvar.data.dtype.name, cfvar, g['netcdf'].file_format))
                
            message = "Can't create variable in {} file from {} ({})".format(
                g['netcdf'].file_format, cfvar, error)

            if error == 'NetCDF: NC_UNLIMITED in the wrong index':            
                raise RuntimeError(
                    message+". In a {} file the unlimited dimension must be the first (leftmost) dimension of the variable. Consider using a netCDF4 format.".format(g['netcdf'].file_format))
                    
            raise RuntimeError(message)
#        else:
#            if zzz:
#                g['zzz'].write('\n{} = nc.createVariable(\n    {})\n'.format(
#                    ncvar,
#                    ',\n    '.join("{}={!r}".format(k, v) for k, v in kwargs.items())))
        #--- End: try

        #-------------------------------------------------------------
        # Write attributes to the netCDF variable
        #-------------------------------------------------------------
        self._write_attributes(cfvar, ncvar, extra=extra, omit=omit)
    
        #-------------------------------------------------------------
        # Write data to the netCDF variable
        #
        # Note that we don't need to worry about scale_factor and
        # add_offset, since if a data array is *not* a numpy array,
        # then it will have its own scale_factor and add_offset
        # parameters which will be applied when the array is realised,
        # and the python netCDF4 package will deal with the case when
        # scale_factor or add_offset are set as properties on the
        # variable.
        # ------------------------------------------------------------
        if data is not None:  
            # Find the missing data values, if any.
            _FillValue    = self.implementation.get_property(cfvar, '_FillValue', None) 
            missing_value = self.implementation.get_property(cfvar, 'missing_value', None)
            unset_values = [value for value in (_FillValue, missing_value)
                            if value is not None]
            self._write_data(data, ncvar, ncdimensions, unset_values)
    
        # Update the 'seen' dictionary
        g['seen'][id(cfvar)] = {'variable': cfvar,
                                'ncvar'   : ncvar,
                                'ncdims'  : original_ncdimensions}
    #--- End: def
    
    def _write_data(self, data, ncvar, ncdimensions, unset_values=()):
        '''

:Parameters:

    data: `Data`

    ncvar: `str`

    ncdimensions: `tuple` of `str`

    unset_values: sequence of numbers

        '''
        g = self.write_vars

#        convert_dtype = g['datatype']


        if set(ncdimensions).intersection(g['sample_ncdim'].values()):
            # Get the data as a compressed numpy array
            array = self.implementation.get_compressed_array(data)
        else:
            # Get the data as an uncompressed numpy array
            array = self.implementation.get_array(data)

        # Convert data type
        new_dtype = g['datatype'].get(array.dtype)
        if new_dtype is not None:
            array = array.astype(new_dtype)  

        # Check that the array doesn't contain any elements
        # which are equal to any of the missing data values
        if unset_values:
            if numpy.ma.is_masked(array):
                temp_array = array.compressed()
            else:
                temp_array = array
                
            if numpy.intersect1d(unset_values, temp_array):
                raise ValueError(
"ERROR: Can't write data that has _FillValue or missing_value at unmasked point: {!r}".format(cfvar))
        #--- End: if
    
        # Copy the array into the netCDF variable
        g['nc'][ncvar][...] = array

        self._aaa(ncvar, array)
    #--- End: def

    def _aaa(self, ncvar, array):
        '''
        '''
        g = self.write_vars
        
        if zzz:
            masked = numpy.ma.isMA(array)
            if masked:
                array = array.toflex()

#            fd, filename = mkstemp(prefix=ncvar+'_array', suffix='.npy')
#            close(fd)
            filename = ncvar+'_array.npy'
            
            numpy.save(filename, array)

            g['zzz'].write('\n_ = numpy.load({filename!r})\n'.format(filename=filename))
            if masked:
                g['zzz'].write('_ = numpy.ma.array(_["_data"], mask=_["_mask"], copy=False)\n')
                
            g['zzz'].write('{ncvar}[...] = _\n'.format(ncvar=ncvar))
    #--- End: def
    
    def _convert_to_char(self, data):
        '''Convert string data into character data

The return `Data` object will have data type 'S1' and will have an
extra trailing dimension.
    
:Parameters:
    
    data: `Data`

:Returns:

    out: `Data`

        '''
        strlen = data.dtype.itemsize
#        print ('1 strlen =', strlen)
#        if strlen > 1:
        data = self.implementation.initialise_Data(
                array=self._character_array(self.implementation.get_array(data)),
                units=self.implementation.get_data_units(data, None),
                calendar=self.implementation.get_data_calendar(data, None),
                copy=False)
    
        return data
    #--- End: def
    
    def _write_field(self, f, add_to_seen=False,
                     allow_data_expand_dims=True):
        '''
    
:Parameters:

    f : `Field`

    add_to_seen : bool, optional

    allow_data_expand_dims: `bool`, optional

:Returns:

    `None`

        '''
        g = self.write_vars
        
        verbose = g['verbose']
        if verbose:
            print('  Writing', repr(f)+':')

        xxx = []
            
        seen = g['seen']
          
        org_f = f
        if add_to_seen:
            id_f = id(f)
            
        # Copy the field, as we are almost certainly about to do
        # terrible things to it.
        f = self.implementation.copy_construct(org_f)
    
        data_axes = self.implementation.get_field_data_axes(f)
    
        # Mapping of domain axis identifiers to netCDF dimension
        # names. This gets reset for each new field that is written to
        # the file.
        #
        # For example: {'domainaxis1': 'lon'}
        g['axis_to_ncdim'] = {}
    
        # Mapping of domain axis identifiers to netCDF scalar
        # coordinate variable names. This gets reset for each new
        # field that is written to the file.
        #
        # For example: {'domainaxis0': 'time'}
        g['axis_to_ncscalar'] = {}
        
        # Mapping of construct internal identifiers to netCDF variable
        # names. This gets reset for each new field that is written to
        # the file.
        #
        # For example: {'dimensioncoordinate1': 'longitude'}
        g['key_to_ncvar'] = {}

        # Type of compression applied to the field
        compression_type = self.implementation.get_compression_type(f)
        g['compression_type'] = compression_type
        if verbose:
            print('    Compression = {!r}'.format(g['compression_type']))
        # 
        g['sample_ncdim']     = {}
    
        # Initialize the list of the field's auxiliary/scalar coordinates
        coordinates = []

        g['formula_terms_refs'] = [
            ref for ref in list(self.implementation.get_coordinate_references(f).values())
            if self.implementation.get_coordinate_conversion_parameters(ref).get('standard_name', False)] 

        g['grid_mapping_refs'] = [
            ref for ref in list(self.implementation.get_coordinate_references(f).values())
            if self.implementation.get_coordinate_conversion_parameters(ref).get('grid_mapping_name', False)]

        field_coordinates = self.implementation.get_coordinates(f)
                        
        owning_coordinates = []
        standard_names = []
        computed_standard_names = []
        for ref in g['formula_terms_refs']:
            coord_key = None

            standard_name = self.implementation.get_coordinate_conversion_parameters(ref).get(
                'standard_name')
            computed_standard_name = self.implementation.get_coordinate_conversion_parameters(ref).get(
                'computed_standard_name')
            
            if standard_name is not None and computed_standard_name is not None:
                for key in self.implementation.get_coordinate_reference_coordinates(ref):
                    coord = field_coordinates[key]

                    if not (self.implementation.get_data_ndim(coord) == 1 and
                            self.implementation.get_property(coord, 'standard_name', None) == standard_name):
                        continue
                    
                    if coord_key is not None:
                        coord_key = None
                        break

                    coord_key = key
            #--- End: if
                
            owning_coordinates.append(coord_key)
            standard_names.append(standard_name)
            computed_standard_names.append(computed_standard_name)
        #--- End: for

        for key, csn in zip(owning_coordinates, computed_standard_names):
            if key is None:
                continue
            
            x = self.implementation.get_property(coord, 'computed_standard_name', None)
            if x is None:
                self.implementation.set_property(field_coordinates[key], 'computed_standard_name', csn)
            elif x != csn:
                raise ValueError(";sdm p8whw=0[")
        #--- End: for
                   
        dimension_coordinates = self.implementation.get_dimension_coordinates(f)
        
        # For each of the field's domain axes ...
        domain_axes = self.implementation.get_domain_axes(f)
       
        for axis in sorted(domain_axes):
            found_dimension_coordinate = False
            for key, dim_coord in dimension_coordinates.items():
                if self.implementation.get_construct_axes(f, key) != (axis,):
                    continue

                # --------------------------------------------------------
                # Still here? Then a dimension coordinate exists for
                # this domain axis.
                # --------------------------------------------------------
                if axis in data_axes:
                    # The data array spans this domain axis, so write
                    # the dimension coordinate to the file as a
                    # coordinate variable.
                    ncvar = self._write_dimension_coordinate(f, key, dim_coord)
                else:
                    # The data array does not span this axis (and
                    # therefore the dimension coordinate must have
                    # size 1).
                    if (not g['scalar'] or
                        len(self.implementation.get_constructs(f, axes=[axis])) >= 2):
                        # Either A) it has been requested to not write
                        # scalar coordinate variables; or B) there ARE
                        # auxiliary coordinates, cell measures, domain
                        # ancillaries or field ancillaries which span
                        # this domain axis. Therefore write the
                        # dimension coordinate to the file as a
                        # coordinate variable.
                        ncvar = self._write_dimension_coordinate(f, key, dim_coord)
    
                        # Expand the field's data array to include
                        # this domain axis
                        f = self.implementation.field_expand_dims(f,
                                                                  position=0, axis=axis) 
                    else:
                        # Scalar coordinate variables are being
                        # allowed; and there are NO auxiliary
                        # coordinates, cell measures, domain
                        # ancillaries or field ancillaries which span
                        # this domain axis. Therefore write the
                        # dimension coordinate to the file as a scalar
                        # coordinate variable.
                        coordinates = self._write_scalar_coordinate(
                            f, key, dim_coord, axis, coordinates)
                #-- End: if

                found_dimension_coordinate = True
                break
            #--- End: for

            if not found_dimension_coordinate:
                # --------------------------------------------------------
                # There is no dimension coordinate for this axis
                # --------------------------------------------------------

                spanning_constructs = self.implementation.get_constructs(f, axes=[axis])
                
                if axis not in data_axes and spanning_constructs:
                    # The data array doesn't span the domain axis but
                    # an auxiliary coordinate, cell measure, domain
                    # ancillary or field ancillary does, so expand the
                    # data array to include it.
                    f = self.implementation.field_expand_dims(f,
                                                              position=0, axis=axis)
                    data_axes.append(axis)
    
                # If the data array (now) spans this domain axis then create a
                # netCDF dimension for it
                if axis in data_axes:
                    axis_size0 = self.implementation.get_domain_axis_size(f, axis)
                
                    use_existing_dimension = False

                    if spanning_constructs:
                        for key, construct in list(spanning_constructs.items()):
                            axes = self.implementation.get_construct_axes(f, key)
                            spanning_constructs[key] = (construct, axes.index(axis))
                        
                        for b1 in g['xxx']:
                            (ncdim1,  axis_size1),  constructs1 = list(b1.items())[0]

                            if axis_size0 != axis_size1:
                                continue
    
#                            if not constructs1:
#                                continue

                            constructs1 = constructs1.copy()
                            
                            for key0, (construct0, index0) in spanning_constructs.items():
                                matched_construct = False
                                for key1, (construct1, index1) in constructs1.items():
                                    if (index0 == index1 and
                                        self.implementation.equal_constructs(construct0, construct1)):
                                        del constructs1[key1]
                                        matched_construct = True
                                        break
                                #--- End: for        
        
                                if not matched_construct:
                                    break
                            #--- End: for
                            
                            if not constructs1:
                                use_existing_dimension = True
                                break
                        #--- End: for
                    #--- End: if
    
                    if use_existing_dimension:
                        g['axis_to_ncdim'][axis] = ncdim1
                    elif (g['compression_type'] == 'ragged contiguous' and 
                          len(data_axes) == 2 and axis == data_axes[1]):
                        # Do not create the a netCDF dimension for the
                        # element dimension
                        g['axis_to_ncdim'][axis] = 'dsg%{}'.format('contiuous_element')
                    elif (g['compression_type'] == 'ragged indexed' and 
                          len(data_axes) == 2 and axis == data_axes[1]):
                        # Do not create the a netCDF dimension for the
                        # element dimension
                        g['axis_to_ncdim'][axis] = 'dsg%{}'.format('indexed_element')
                    elif (g['compression_type'] == 'ragged indexed contiguous' and 
                          len(data_axes) == 3 and axis == data_axes[1]):
                        # Do not create the a netCDF dimension for the
                        # element dimension
                        g['axis_to_ncdim'][axis] = 'dsg%{}'.format('indexed_contiguous_element1')
                    elif (g['compression_type'] == 'ragged indexed contiguous' and 
                          len(data_axes) == 3 and axis == data_axes[2]):
                        # Do not create the a netCDF dimension for the
                        # element dimension
                        g['axis_to_ncdim'][axis] = 'dsg%{}'.format('indexed_contiguous_element2')
                    else:
                        domain_axis = self.implementation.get_domain_axes(f)[axis] 
                        ncdim = self.implementation.nc_get_dimension(domain_axis, 'dim')
                        ncdim = self._netcdf_name(ncdim)
                        unlimited = self._unlimited(f, axis)
                        self._write_dimension(ncdim, f, axis, unlimited=unlimited)
                        
                        xxx.append({(ncdim, axis_size0): spanning_constructs})
            #--- End: if    
        #--- End: for

        field_data_axes = tuple(self.implementation.get_field_data_axes(f))
        data_ncdimensions = [g['axis_to_ncdim'][axis] for axis in field_data_axes]
   
        # ------------------------------------------------------------
        # Now that we've dealt with all of the axes, deal with
        # compression
        # ------------------------------------------------------------
        if compression_type:
            compressed_axes = tuple(self.implementation.get_compressed_axes(f))
            g['compressed_axes'] = compressed_axes
            compressed_ncdims = tuple([g['axis_to_ncdim'][axis]
                                       for axis in compressed_axes])
            
            if compression_type == 'gathered':
                # ----------------------------------------------------
                # Compression by gathering
                #
                # Write the list variable to the file, making a note
                # of the netCDF sample dimension.
                # ----------------------------------------------------
                list_variable = self.implementation.get_list_variable(f)
                compress = ' '.join(compressed_ncdims)
                sample_ncdim = self._write_list_variable(f, list_variable,
                                                         compress=compress)
            
            elif compression_type == 'ragged contiguous':
                # ----------------------------------------------------
                # Compression by contiguous ragged array
                #
                # Write the count variable to the file, making a note
                # of the netCDF sample dimension.
                # ----------------------------------------------------
                count = self.implementation.get_count_variable(f)
                sample_ncdim = self._write_count_variable(
                    f, count,
                    ncdim=data_ncdimensions[0], create_ncdim=False)

            elif compression_type == 'ragged indexed':
                # ----------------------------------------------------
                # Compression by indexed ragged array
                #
                # Write the index variable to the file, making a note
                # of the netCDF sample dimension.
                # ----------------------------------------------------
                index = self.implementation.get_index_variable(f)
                index_ncdim = self.implementation.nc_get_dimension(index)
                sample_ncdim = self._write_index_variable(
                    f, index,
                    ncdim=index_ncdim, create_ncdim=True,
                    instance_dimension=data_ncdimensions[0],
                    sample_dimension=index_ncdim)

            elif compression_type == 'ragged indexed contiguous':
                # ----------------------------------------------------
                # Compression by indexed contigous ragged array
                #
                # Write the index variable to the file, making a note
                # of the netCDF sample dimension.
                # ----------------------------------------------------
                count = self.implementation.get_count_variable(f)
                count_ncdim = self.implementation.nc_get_dimension(count)
                sample_ncdim = self._write_count_variable(
                    f, count,
                    ncdim=count_ncdim, create_ncdim=True)

                index_ncdim = count_ncdim
                index = self.implementation.get_index_variable(f)
                self._write_index_variable(
                    f, index,
                    ncdim=index_ncdim, create_ncdim=False,
                    instance_dimension=data_ncdimensions[0],
                    sample_dimension=sample_ncdim)

                g['sample_ncdim'][compressed_ncdims[0:2]] = index_ncdim

            else:
                raise ValueError(
"Can't write {!r}: Unknown compression type: {!r}".format(org_f, compression_type))
                
            g['sample_ncdim'][compressed_ncdims] = sample_ncdim
            
            n = len(compressed_ncdims)
            sample_dimension = self.implementation.get_sample_dimension_position(f)
#            sample_dimension = [i for i in range(len(field_data_axes)-n+1)
#                                if field_data_axes[i:i+n] == compressed_axes]
#            sample_dimension = sample_dimension[0]

            data_ncdimensions[sample_dimension:sample_dimension+n] = [sample_ncdim]
        #--- End: if
        
        data_ncdimensions = tuple(data_ncdimensions)

        # ----------------------------------------------------------------
        # Create auxiliary coordinate variables, except those which might
        # be completely specified elsewhere by a transformation.
        # ----------------------------------------------------------------
        # Initialize the list of 'coordinates' attribute variable values
        # (each of the form 'name')
        for key, aux_coord in sorted(self.implementation.get_auxiliary_coordinates(f).items()):
#            if self.implementation.is_geometry(aux_coord):
#                coordinates = self._write_geometry_coordinate(f, key, aux_coord,
#                                                              coordinates)

            coordinates = self._write_auxiliary_coordinate(f, key, aux_coord,
                                                           coordinates)
    
        # ------------------------------------------------------------
        # Create netCDF variables from domain ancillaries
        # ------------------------------------------------------------
        for key, anc in sorted(self.implementation.get_domain_ancillaries(f).items()):
            self._write_domain_ancillary(f, key, anc)
    
        # ------------------------------------------------------------
        # Create netCDF variables from cell measures 
        # ------------------------------------------------------------
        # Set the list of 'cell_measures' attribute values (each of
        # the form 'measure: name')
        cell_measures = [self._write_cell_measure(f, key, msr)
                         for key, msr in sorted(self.implementation.get_cell_measures(f).items())]
        
        # ------------------------------------------------------------
        # Create netCDF formula_terms attributes from vertical
        # coordinate references
        # ------------------------------------------------------------
        for ref in g['formula_terms_refs']:
            formula_terms = []
            bounds_formula_terms = []
            owning_coord_key = None

            standard_name = self.implementation.get_coordinate_conversion_parameters(ref).get(
                'standard_name')
            if standard_name is not None:
                c = []
                for key in self.implementation.get_coordinate_reference_coordinates(ref):
                    coord = self.implementation.get_coordinates(f)[key]
                    if self.implementation.get_property(coord, 'standard_name', None) == standard_name:
                        c.append((key, coord))

                if len(c) == 1:
#                    owning_coord_key, owning_coord = c[0]
                    owning_coord_key, _ = c[0]
            #--- End: if
    
            z_axis = self.implementation.get_construct_axes(f, owning_coord_key)[0]
                
            if owning_coord_key is not None:
                # This formula_terms coordinate reference matches up
                # with an existing coordinate
    
                for term, value in self.implementation.get_coordinate_conversion_parameters(ref).items():
                    if value is None:
                        continue
    
                    if term in ('standard_name', 'computed_standard_name'):
                        continue
    
                    ncvar = self._write_scalar_data(value, ncvar=term)
    
                    formula_terms.append('{0}: {1}'.format(term, ncvar))
                    bounds_formula_terms.append('{0}: {1}'.format(term, ncvar))
            
                for term, key in ref.coordinate_conversion.domain_ancillaries().items(): # DCH ALERT
                    if key is None:
                        continue
    
                    domain_anc = self.implementation.get_domain_ancillaries(f)[key]
                    if domain_anc is None:
                        continue
    
                    if id(domain_anc) not in seen:
                        continue
    
                    # Get the netCDF variable name for the domain
                    # ancillary and add it to the formula_terms attribute
                    ncvar = seen[id(domain_anc)]['ncvar']                
                    formula_terms.append('{0}: {1}'.format(term, ncvar))
    
                    bounds = g['bounds'].get(ncvar, None)
                    if bounds is not None:
                        if z_axis not in self.implementation.get_construct_axes(f, key):
                            bounds = None
    
                    if bounds is None:        
                        bounds_formula_terms.append('{0}: {1}'.format(term, ncvar))
                    else:
                        bounds_formula_terms.append('{0}: {1}'.format(term, bounds))
            #--- End: if

            # Add the formula_terms attribute to the parent coordinate
            # variable
            if formula_terms:
                ncvar = g['key_to_ncvar'][owning_coord_key]
                formula_terms = ' '.join(formula_terms)
                g['nc'][ncvar].setncattr('formula_terms', formula_terms)
                if zzz:
                    g['zzz'].write('{ncvar}.setncattr("formula_terms", {formula_terms!r})\n'.format(
                        ncvar=ncvar, formula_terms=formula_terms))
            
                if g['verbose']:
                    print('    Writing formula_terms attribute to netCDF variable', ncvar+':', repr(formula_terms))
    
                # Add the formula_terms attribute to the parent
                # coordinate bounds variable
                bounds_ncvar = g['bounds'].get(ncvar)
                if bounds_ncvar is not None:
                    bounds_formula_terms = ' '.join(bounds_formula_terms)
                    g['nc'][bounds_ncvar].setncattr('formula_terms', bounds_formula_terms)
                    if zzz:
                        g['zzz'].write('{ncvar}.setncattr("formula_terms", {formula_terms!r})\n'.format(
                            ncvar=bounds_ncvar, formula_terms=bounds_formula_terms))

                    if g['verbose']:
                        print('    Writing formula_terms to netCDF bounds variable', bounds_ncvar+':', repr(bounds_formula_terms))
            #--- End: if
                        
            # Deal with a vertical datum
            if owning_coord_key is not None:
                self._create_vertical_datum(ref, owning_coord_key)
        #--- End: for
    
        # ------------------------------------------------------------
        # Create netCDF variables grid mappings
        # ------------------------------------------------------------
        multiple_grid_mappings = (len(g['grid_mapping_refs']) > 1)
        
        grid_mapping = [self._write_grid_mapping(f, ref, multiple_grid_mappings)
                        for ref in g['grid_mapping_refs']]
        
        # ----------------------------------------------------------------
        # Field ancillary variables
        #
        # Create the 'ancillary_variables' CF-netCDF attribute and
        # create the referenced CF-netCDF ancillary variables
        # ----------------------------------------------------------------
        ancillary_variables = [
            self._write_field_ancillary(f, key, anc)
            for key, anc in self.implementation.get_field_ancillaries(f).items()]
    
        # ----------------------------------------------------------------
        # Create the CF-netCDF data variable
        # ----------------------------------------------------------------
        ncvar = self._create_netcdf_variable_name(f, default='data')
    
        ncdimensions = data_ncdimensions
#                                      ncdimensions = tuple([g['axis_to_ncdim'][axis]
#                              for axis in self.implementation.get_field_data_axes(f)])
    
        extra = {}

        # Cell measures
        if cell_measures:
            cell_measures = ' '.join(cell_measures)
            if verbose:
                print('    Writing cell_measures attribute to netCDF variable {}: {!r}'.format(
                    ncvar, cell_measures))
                
            extra['cell_measures'] = cell_measures
            
        # Auxiliary/scalar coordinates
        if coordinates:
            coordinates = ' '.join(coordinates)
            if verbose:
                print('    Writing coordinates attribute to netCDF variable {}: {!r}'.format(
                    ncvar, coordinates))
                
            extra['coordinates'] = coordinates
    
        # Grid mapping
        if grid_mapping:
            grid_mapping = ' '.join(grid_mapping)
            if verbose:
                print('    Writing grid_mapping attribute to netCDF variable {}: {!r}'.format(
                    ncvar, grid_mapping))
                
            extra['grid_mapping'] = grid_mapping
    
        # Ancillary variables
        if ancillary_variables:
            ancillary_variables = ' '.join(ancillary_variables)
            if verbose:
                print('    Writing ancillary_variables attribute to netCDF variable {}: {!r}'.format(
                ncvar, ancillary_variables))

            extra['ancillary_variables'] = ancillary_variables
            
#        # Flag values
#        if hasattr(f, 'flag_values'):
#            extra['flag_values'] = f.flag_values
#    
#        # Flag masks
#        if hasattr(f, 'flag_masks'):
#            extra['flag_masks'] = f.flag_masks
#    
#        # Flag meanings
#        if hasattr(f, 'flag_meanings'):
#            extra['flag_meanings'] = f.flag_meanings
    
        # name can be a dimension of the variable, a scalar coordinate
        # variable, a valid standard name, or the word 'area'
        cell_methods = self.implementation.get_cell_methods(f)
        if cell_methods:
            axis_map = g['axis_to_ncdim'].copy()
            axis_map.update(g['axis_to_ncscalar'])

            cell_methods_strings = []
            for cm in list(cell_methods.values()):
                axes = [axis_map.get(axis, axis)
                        for axis in self.implementation.get_cell_method_axes(cm, ())]
                self.implementation.set_cell_method_axes(cm, axes)
                cell_methods_strings.append(self.implementation.get_cell_method_string(cm))

            cell_methods = ' '.join(cell_methods_strings)
            if verbose:
                print('    Writing cell_methods attribute to netCDF variable', ncvar+':', cell_methods)

            extra['cell_methods'] = cell_methods
            
        # Create a new data variable
        self._write_netcdf_variable(ncvar, ncdimensions, f,
                                    omit=g['global_attributes'],
                                    extra=extra, data_variable=True)
        
        # Update the 'seen' dictionary, if required
        if add_to_seen:
            seen[id_f] = {'variable': org_f,
                          'ncvar'   : ncvar,
                          'ncdims'  : ncdimensions}

        if xxx:
            g['xxx'].extend(xxx)
    #--- End: def

    def _create_vertical_datum(self, ref, coord_key):
        '''Deal with a vertical datum
        '''
        g = self.write_vars

        if not self.implementation.has_datum(ref):
            return

        if g['verbose']:
            print('    Datum =', self.implementation.get_datum(ref))
            
#        domain_ancillaries = API.get_datum_ancillaries(ref)

        count = [0, None]
        for grid_mapping in g['grid_mapping_refs']:
#            datum1 = API.get_datum(grid_mapping)
#            if not datum1:
#            if API.empty_coordinate_reference_datum(grid_mapping):
#                continue

#            domain_ancillaries1 = API.get_datum_ancillaries(
#                grid_mapping)
                 
            if self.implementation.equal_datums(ref, grid_mapping):
                count = [count[0] + 1, grid_mapping]
                if count[0] > 1:
                    break
                
#            if (datum.equals(datum1) and
#                domain_ancillaries == domain_ancillaries1):
#                count = [count[0] + 1, grid_mapping]
#                if count[0] > 1:
#                    break
        #--- End: for

        if count[0] == 1:
            # Add the vertical coordinate to an existing
            # horizontal coordinate reference
            if g['verbose']:
                print('    Adding', coord_key, 'to', grid_mapping)


                
            grid_mapping = count[1]
            self.implementation.set_coordinate_reference_coordinate(grid_mapping,
                                                                    coord_key)
        else:
            # Create a new horizontal coordinate reference for
            # the vertical datum
            if g['verbose']:
                print('WHAT??')
            new_grid_mapping = self.implementation.initialise_CoordinateReference(
                coordinates=[coord_key],
                datum=self.implementation.get_datum(ref))
            
            g['grid_mapping_refs'].append(new_grid_mapping)
    #--- End: def
                            
    def _unlimited(self, field, axis):
        '''TODO

:Parameters:
  
    field: `Field`

    axis: `str`
   
:Returns:

    out: `bool`

        '''
        return axis in self.implementation.nc_get_unlimited_axes(field)
    #--- End: def
    
    def _write_global_attributes(self, fields):
        '''Find the netCDF global properties from all of the input fields and
write them to the netCDF4.Dataset.
    
:Parameters:
  
    fields : `list`
  
:Returns:
    
    `None`
        
        '''
        g = self.write_vars

        # ------------------------------------------------------------
        # Initialize the global attributes with those requested to be
        # such
        # ------------------------------------------------------------
        global_attributes = g['global_attributes']

        # ------------------------------------------------------------
        # Add in the standard "description of file contents"
        # attributes
        # ------------------------------------------------------------
        global_attributes.update(constants.description_of_file_contents_attributes)

        # ------------------------------------------------------------
        # Add properties that have been marked as global on each field
        # ------------------------------------------------------------
        for f in fields:
            f_global = self.implementation.nc_get_global_attributes(f)
            global_attributes.update(f_global)

        # ------------------------------------------------------------
        # Remove attributes that have been specifically requested not
        # to be global attributes
        # ------------------------------------------------------------
        global_attributes.difference(g['variable_attributes'])
            
        # ------------------------------------------------------------
        # Remove global attributes that have different values for
        # different fields
        # ------------------------------------------------------------
        f0 = fields[0]
        for prop in tuple(global_attributes):
            if not self.implementation.has_property(f0, prop):
                global_attributes.remove(prop)
                continue
                
            prop0 = self.implementation.get_property(f0, prop, None)

            if len(fields) > 1:
                for f in fields[1:]:
                    prop1 = self.implementation.get_property(f, prop, None)
                    if not self.implementation.equal_properties(prop0, prop1):
                        global_attributes.remove(prop)
                        break
        #--- End: for

        # ------------------------------------------------------------
        # Write the global attributes to the file
        # ------------------------------------------------------------
        g['netcdf'].setncattr('Conventions', 'CF-'+self.implementation.get_cf_version())
        
        for attr in global_attributes - set(('Conventions',)):
            g['netcdf'].setncattr(attr, self.implementation.get_property(f0, attr)) 
            
        g['global_attributes'] = global_attributes
    #--- End: def

    def file_close(self, filename):
        '''Close the netCDF file that has been written.

:Returns:

    `None`

        '''
        self.write_vars['netcdf'].close()

        if zzz:
            self.write_vars['zzz'].close()
    #--- End: def

    def file_open(self, filename, mode, fmt):
        '''Open the netCDF file for writing.
        
:Returns:
        
    out: `netCDF.Dataset`
        
        '''
        try:        
            nc = netCDF4.Dataset(filename, mode, format=fmt)
        except RuntimeError as error:
            raise RuntimeError("{}: {}".format(error, filename))        

        if zzz:
            creator = open('netcdf4_creator.py', 'w')
            self.write_vars['zzz'] = creator
            
            creator.writelines(['import netCDF4\n',
                                'import numpy\n',
                                '\n',
                                'nc = netCDF4.Dataset({!r}, {!r}, {format!r})\n'.format(
                                    filename, mode, format=fmt),
            ])
            
        return nc
    #--- End: def

#    @classmethod
#    def file_type(cls, filename):
#        '''Find the format of a file.
#    
#:Parameters:
#    
#    filename: `str`
#        The file name.
#    
#:Returns:
# 
#    out: `str`
#        The format type of the file.
#    
#:Examples:
#
#>>> filetype = n.file_type(filename)
#    
#    '''
#        # ----------------------------------------------------------------
#        # Assume that URLs are in netCDF format
#        # ----------------------------------------------------------------
#        if filename.startswith('http://'):
#           return 'netCDF'
#    
#        # ----------------------------------------------------------------
#        # netCDF
#        # ----------------------------------------------------------------
#        if netcdf.is_netcdf_file(filename):
#            return 'netCDF'
#    #--- End: def

    def write(self, fields, filename, fmt='NETCDF4', overwrite=True,
              global_attributes=None, variable_attributes=None,
              external_file=None, datatype=None,
              least_significant_digit=None, endian='native',
              compress=0, fletcher32=False, shuffle=True, scalar=True,
              HDF_chunks=None, extra_write_vars=None, verbose=False):
        '''Write fields to a netCDF file.
        
NetCDF dimension and variable names will be taken from variables'
`!ncvar` attributes and the field attribute `!ncdimensions` if
present, otherwise they are inferred from standard names or set to
defaults. NetCDF names may be automatically given a numerical suffix
to avoid duplication.
    
Output netCDF file global properties are those which occur in the set
of CF global properties and non-standard data variable properties and
which have equal values across all input fields.
    
Logically identical field components are only written to the file
once, apart from when they need to fulfil both dimension coordinate
and auxiliary coordinate roles for different data variables.
    
:Parameters:

    fields : (arbitrarily nested sequence of) `cf.Field`
        The field or fields to write to the file.

    filename : str
        The output CF-netCDF file. Various type of expansion are
        applied to the file names:
        
          ====================  ======================================
          Expansion             Description
          ====================  ======================================
          Tilde                 An initial component of ``~`` or
                                ``~user`` is replaced by that *user*'s
                                home directory.
           
          Environment variable  Substrings of the form ``$name`` or
                                ``${name}`` are replaced by the value
                                of environment variable *name*.
          ====================  ======================================
    
        Where more than one type of expansion is used in the same
        string, they are applied in the order given in the above
        table.

          Example: If the environment variable *MYSELF* has been set
          to the "david", then ``'~$MYSELF/out.nc'`` is equivalent to
          ``'~david/out.nc'``.
  
    fmt : str, optional
        The format of the output file. One of:

           =====================  ================================================
           fmt                    Description
           =====================  ================================================
           ``'NETCDF3_CLASSIC'``  Output to a CF-netCDF3 classic format file
           ``'NETCDF3_64BIT'``    Output to a CF-netCDF3 64-bit offset format file
           ``'NETCDF4_CLASSIC'``  Output to a CF-netCDF4 classic format file
           ``'NETCDF4'``          Output to a CF-netCDF4 format file
           =====================  ================================================

        By default the *fmt* is ``'NETCDF3_CLASSIC'``. Note that the
        netCDF3 formats may be slower than any of the other options.

    overwrite: bool, optional
        If False then raise an exception if the output file
        pre-exists. By default a pre-existing output file is over
        written.

    verbose : bool, optional
        If True then print one-line summaries of each field written.
    
    datatype : dict, optional
        Specify data type conversions to be applied prior to writing
        data to disk. Arrays with data types which are not specified
        remain unchanged. By default, array data types are preserved
        with the exception of booleans (``numpy.dtype(bool)``, which
        are converted to 32 bit integers.

          **Example:**
            To convert 64 bit floats and integers to their 32 bit
            counterparts: ``dtype={numpy.dtype(float):
            numpy.dtype('float32'), numpy.dtype(int):
            numpy.dtype('int32')}``.

:Returns:

    `None`

:Examples 2:

>>> f
[<CF Field: air_pressure(30, 24)>,
 <CF Field: u_compnt_of_wind(19, 29, 24)>,
 <CF Field: v_compnt_of_wind(19, 29, 24)>,
 <CF Field: potential_temperature(19, 30, 24)>]
>>> write(f, 'file')

>>> type(f)
<class 'cf.field.FieldList'>
>>> cf.write([f, g], 'file.nc', verbose=True)
[<CF Field: air_pressure(30, 24)>,
 <CF Field: u_compnt_of_wind(19, 29, 24)>,
 <CF Field: v_compnt_of_wind(19, 29, 24)>,
 <CF Field: potential_temperature(19, 30, 24)>]
        '''    
        if verbose:
            print('Writing to', fmt)

        # ------------------------------------------------------------
        # Initialise netCDF write parameters
        # ------------------------------------------------------------
        self.write_vars = {
            # CF conventions for output file
#            'Conventions': Conventions,
            # Format of output file
            'fmt': None,
            # netCDF4.Dataset instance
            'netcdf'           : None,    
            # Map netCDF variable names to netCDF4.Variable instances
            'nc': {},      
            # Map netCDF dimension names to netCDF dimension sizes
            'ncdim_to_size': {},
            # Dictionary of netCDF variable names and netCDF
            # dimensions keyed by items of the field (such as a
            # coordinate or a coordinate reference)
            'seen': {},
            # Set of all netCDF dimension and netCDF variable names.
            'ncvar_names': set(()),
            # Set of global or non-standard CF properties which have
            # identical values across all input fields.
            'variable_attributes': set(()),
            'global_attributes': set(()),
            'bounds': {},
            # NetCDF compression/endian
            'netcdf_compression': {},
            'endian': 'native',
            'least_significant_digit': None,
            # CF properties which need not be set on bounds if they're set
            # on the parent coordinate
            'omit_bounds_properties': ('units', 'standard_name', 'axis',
                                       'positive', 'calendar', 'month_lengths',
                                       'leap_year', 'leap_month'),
            # Data type conversions to be applied prior to writing
            'datatype': {},
            # Print statements
            'verbose': False,

            'xxx': [],

            'count_variable_sample_dimension': {},
            'index_variable_sample_dimension': {},

            'external_variables': '',
            'external_fields'   : [],
        }
        g = self.write_vars
        
        if extra_write_vars:
            g.update(copy.deepcopy(extra_write_vars))

        compress = int(compress)
        zlib = bool(compress) 
    
        if fmt not in ('NETCDF3_CLASSIC', 'NETCDF3_64BIT',
                       'NETCDF4', 'NETCDF4_CLASSIC'):
            raise ValueError("Unknown output file format: {}".format(fmt))
    
        if compress and fmt in ('NETCDF3_CLASSIC', 'NETCDF3_64BIT'):
            raise ValueError("Can't compress {} format file".format(fmt))
        
        # ------------------------------------------------------------
        # Set up non-global attributes
        # ------------------------------------------------------------
        if variable_attributes:
            if isinstance(variable_attributes, basestring):
                variable_attributes = set((variable_attributes,))
            else:
                variable_attributes = set(variable_attributes)

            g['variable_attributes'] = variable_attributes
    
        if global_attributes:
            if isinstance(global_attributes, basestring):
                global_attributes = set((global_attributes,))
            else:
                global_attributes = set(global_attributes)

            g['global_attributes'] = global_attributes
    
        # ------------------------------------------------------------
        # Set up data type conversions. By default, booleans are
        # converted to 32-bit integers and python objects are
        # converted to 64-bit floats.
        # ------------------------------------------------------------
        dtype_conversions = {numpy.dtype(bool)  : numpy.dtype('int32'),
                             numpy.dtype(object): numpy.dtype(float)}
        if datatype:
            dtype_conversions.update(datatype)

        g['datatype'].update(dtype_conversions)

        # -------------------------------------------------------
        # Compression/endian
        # -------------------------------------------------------
        g['netcdf_compression'].update(
            {'zlib'       : zlib,
             'complevel'  : compress,
             'fletcher32' : bool(fletcher32),
             'shuffle'    : bool(shuffle),
            })
        g['endian'] = endian
        g['least_significant_digit'] = least_significant_digit
        
        g['verbose'] = verbose
        
        g['fmt'] = fmt

        if isinstance(fields, self.implementation.get_class('Field')):
            fields = (fields,)
        else:
            try:
                fields = tuple(fields)
            except TypeError:
                raise TypeError("'fields' parameter must be a (sequence of) Field")
            
        # -------------------------------------------------------
        # Scalar coordinate variables
        # -------------------------------------------------------
        g['scalar'] = scalar
            
        # ---------------------------------------------------------------
        # Still here? Open the output netCDF file.
        # ---------------------------------------------------------------
        filename = os.path.expanduser(os.path.expandvars(filename))
        
        if external_file is not None:
            external_file = os.path.expanduser(os.path.expandvars(external_file))
            if os.path.realpath(external_file) == os.path.realpath(filename):
                raise ValueError("Can't set filename and external_file to the same path")
        #--- End: if
        g['external_file'] = external_file

        if os.path.isfile(filename):
            if not overwrite:
                raise IOError(
                    "Can't write to an existing file unless overwrite=True: {}".format(
                        os.path.abspath(filename)))
                    
            if not os.access(filename, os.W_OK):
                raise IOError(
                    "Can't overwrite an existing file without permission: {}".format(
                        os.path.abspath(filename)))
                
            os.remove(filename)

        # ------------------------------------------------------------
        # Open the netCDF file to be written
        # ------------------------------------------------------------
        mode = 'w'
        g['filename'] = filename
        g['netcdf'] = self.file_open(filename, mode, fmt)
    
        # ---------------------------------------------------------------
        # Set the fill mode for a Dataset open for writing to off. This
        # will prevent the data from being pre-filled with fill values,
        # which may result in some performance improvements.
        # ---------------------------------------------------------------
        g['netcdf'].set_fill_off()
    
        # ---------------------------------------------------------------
        # Write global properties to the file first. This is important
        # as doing it later could slow things down enormously. This
        # function also creates the g['global_attributes'] set, which
        # is used in the _write_field function.
        # ---------------------------------------------------------------
        self._write_global_attributes(fields)
    
        # ---------------------------------------------------------------
        #
        # ---------------------------------------------------------------
        for f in fields:
    
    #        # Set HDF chunking
    #        chunks = f.HDF_chunks()
    #        if chunks
    #        
    #        org_chunks = f.HDF_chunks(HDF_chunks)
    #        default_chunks = f.HDF_chunks()
    #        chunks = org_chunks.copy()
    #        shape = f.shape
    #        for i, size in org_chunks.iteritems():
    #            if size is None:
    #                size = default_chunks[i]
    #            dim_size = shape[i]
    #            if size is None or size > dim_size:
    #                size = dim_size
    #            chunks[i] = size
    #
    #        f.HDF_chunks(chunks)
    
            if g['verbose']:            
                print('  HDF chunks :', 'PASS FOR NOW') #f.HDF_chunks()
            
            # Write the field
            self._write_field(f)
    
    #        # Reset HDF chunking
    #        f.HDF_chunks(org_chunks)
        #-- End: for

        # ---------------------------------------------------------------
        # Write all of the buffered data to disk
        # ---------------------------------------------------------------
        self.file_close(filename)

        # ------------------------------------------------------------
        # Write external fields to the external file
        # ------------------------------------------------------------
        if g['external_fields'] and g['external_file'] is not None:
            self.write(fields=g['external_fields'],
                       filename=g['external_file'],
                       fmt=fmt,
                       overwrite=overwrite,
                       datatype=datatype,
                       endian='native',
                       compress=compress,
                       fletcher32=fletcher32,
                       shuffle=shuffle,
                       HDF_chunks=HDF_chunks,
                       verbose=verbose)            
    #--- End: def
   
#--- End: class
