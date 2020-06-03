from __future__ import print_function
from builtins import (str, zip)
from past.builtins import basestring

import copy
import logging
import os
import re

from distutils.version import LooseVersion

import numpy
import netCDF4

from .. import IOWrite

from . import constants

from ...decorators import _manage_log_level_via_verbosity


logger = logging.getLogger(__name__)


class NetCDFWrite(IOWrite):
    '''
    '''
    def cf_description_of_file_contents_attributes(self):
        '''Description of file contents properties

        '''
        return ('comment',
                'Conventions',
                'featureType',
                'history',
                'institution',
                'references',
                'source',
                'title',
        )

    def cf_geometry_types(self):
        '''Geometry types

    .. versionadded:: 1.8.0

        '''
        return set(('point',
                    'line',
                    'polygon',
        ))

    def cf_cell_method_qualifiers(self):
        '''Cell method qualifiers

        '''
        return set((
            'within',
            'where',
            'over',
            'interval',
            'comment',
        ))

    def _create_netcdf_variable_name(self, parent, default):
#                                     force_use_existing=False):
        '''TODO

    .. versionadded:: 1.7.0

    :Parameters:

        parent:

        default: `str`

    :Returns:

        `str`
            The netCDF variable name.

        '''
        ncvar = self.implementation.nc_get_variable(parent, None)

#        if force_use_existing:
#            if ncvar is None:
#                raise ValueError("asdasdads TODO")
#
#            return ncvar

        if ncvar is None:
            try:
                ncvar = self.implementation.get_property(parent,
                                                         'standard_name',
                                                         default)
            except AttributeError:
                ncvar = default
        # --- End: if

        return self._netcdf_name(ncvar)

    def _netcdf_name(self, base, dimsize=None, role=None):
        '''Return a new netCDF variable or dimension name.

    .. versionadded:: 1.7.0

    :Parameters:

        base: `str`

        dimsize: `int`, optional

        role: `str`, optional

    :Returns:

        `str`
            NetCDF dimension name or netCDF variable name.

        '''
        g = self.write_vars

        ncvar_names = g['ncvar_names']
        ncdim_names = g['ncdim_to_size']

        existing_names = g['ncvar_names'].union(ncdim_names)

        if dimsize is not None:
            if not role:
                raise ValueError("Must supply role when providing dimsize")

            if base in g['dimensions_with_role'].get(role, ()):
                if base in ncdim_names and dimsize == g['ncdim_to_size'][base]:
                    # Return the name of an existing netCDF dimension
                    # with this name, this size, and matching the
                    # given role.
                    return base
        # --- End: if

        if base in existing_names:
            counter = g.setdefault('count_' + base, 1)

            ncvar = '{0}_{1}'.format(base, counter)
            while ncvar in existing_names:
                counter += 1
                ncvar = '{0}_{1}'.format(base, counter)
        else:
            ncvar = base

        ncvar = ncvar.replace(' ', '_')

        ncvar_names.add(ncvar)

        if role and dimsize is not None:
            g['dimensions_with_role'].setdefault(role, []).append(ncvar)

        return ncvar

    def _numpy_compressed(self, array):
        '''Return all the non-masked data as a 1-d array.

    .. versionadded:: 1.8.0

    :Parameters:

        array: `numpy.ndarray`
           A numpy array, that may or may not be masked.

    :Returns:

        `numpy.ndarray`
            The compressed numpy array.

    **Examples:**

    >>> x = numpy.ma.array(np.arange(5), mask=[0]*2 + [1]*3)
    >>> c = n._numpy_compressed(x)
    >>> c
    array([0, 1])
    >>> type(c)
    <type 'numpy.ndarray'>

        '''
        if numpy.ma.isMA(array):
            return array.compressed()

        return array.flatten()

    def _write_attributes(self, parent, ncvar, extra={}, omit=()):
        '''TODO

    :Parameters:

        parent:

        ncvar: `str`

        extra: `dict`, optional

        omit: sequence of `str`, optional

    :Returns:

        `dict`

        '''
        g = self.write_vars

        if parent is None:
            netcdf_attrs = {}
        else:
            netcdf_attrs = self.implementation.get_properties(parent)

        netcdf_attrs.update(extra)

        for attr in omit:
            netcdf_attrs.pop(attr, None)

        if not netcdf_attrs:
            return {}

        # Make sure that _FillValue and missing data have the same
        # data type as the data
        for attr in ('_FillValue', 'missing_value'):
            if attr not in netcdf_attrs:
                continue

            data = self.implementation.get_data(parent, None)
            if data is not None:
                dtype = g['datatype'].get(data.dtype, data.dtype)
                netcdf_attrs[attr] = numpy.array(netcdf_attrs[attr],
                                                 dtype=dtype)
        # --- End: for

        self.write_vars['nc'][ncvar].setncatts(netcdf_attrs)

        return netcdf_attrs

    def _character_array(self, array):
        '''Convert a numpy string array to a numpy character array wih an
    extra trailing dimension.

    :Parameters:

        array: `numpy.ndarray`

    :Returns:

        `numpy.ndarray`

    **Examples:**

    >>> print(a, a.shape, a.dtype.itemsize)
    ['fu' 'bar'] (2,) 3
    >>> b = _character_array(a)
    >>> print(b, b.shape, b.dtype.itemsize)
    [['f' 'u' ' ']
     ['b' 'a' 'r']] (2, 3) 1

    >>> print(a, a.shape, a.dtype.itemsize)
    [-- 'bar'] (2,) 3
    >>> b = _character_array(a)
    >>> print(b, b.shape, b.dtype.itemsize)
    [[-- -- --]
     ['b' 'a' 'r']] (2, 3) 1

        '''
#        strlen = array.dtype.itemsize
        original_shape = array.shape
        original_size = array.size

        masked = numpy.ma.isMA(array)
        if masked:
            fill_value = array.fill_value
            mask = array.mask
            array = numpy.ma.filled(array, fill_value='')

        if array.dtype.kind == 'U':
            array = array.astype('S')

        array = numpy.array(tuple(array.tostring().decode('ascii')),
                            dtype='S1')

#        else:
#            # dtype is 'U'
#            x = []
#            for s in array.flatten():
#                x.extend(tuple(s.ljust(N, '\x00')))
#
#            array = numpy.array(k, dtype='S1')

        array.resize(original_shape + (array.size // original_size,))
#        if masked:
#            array = numpy.ma.array(array, mask=mask, fill_value=fill_value)

#        if array.dtype.kind == 'U':
#            # Convert unicode to string
#            array = array.astype('S')
#
#        new = netCDF4.stringtochar(array, encoding='none')

        if masked:
            array = numpy.ma.masked_where(array == '', array)
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
#        # --- End: for

        return array

    def _datatype(self, variable):
        '''Return the netCDF4.createVariable datatype corresponding to the
    datatype of the array of the input variable

    For example, if variable.dtype is 'float32', then 'f4' will be
    returned.

    For a NETCDF4 or CFA4 format file, numpy string data types will
    either return `str` regardless of the numpy string length (and a
    netCDF4 string type variable will be created) or, if
    `self.write_vars['string']`` is `False`, ``'S1'`` (see below).

    For all other output netCDF formats (such NETCDF4_CLASSIC,
    NETCDF3_64BIT, etc.) numpy string data types will return 'S1'
    regardless of the numpy string length. This means that the
    required conversion of multi-character datatype numpy arrays into
    single-character datatype numpy arrays (with an extra trailing
    dimension) is expected to be done elsewhere (currently in the
    _write_netcdf_variable method).

    If the input variable has no `!dtype` attribute (or it is None)
    then 'S1' is returned, or `str` for NETCDF files.

    :Parameters:

        variable:
            A numpy array or an object with a `get_data` method.

    :Returns:

       `str` or str
           The `netCDF4.createVariable` data type corresponding to the
           datatype of the array of the input variable.

        '''
        g = self.write_vars

        if not isinstance(variable, numpy.ndarray):
            data = self.implementation.get_data(variable, None)
            if data is None:
                return 'S1'
        else:
            data = variable

        dtype = getattr(data, 'dtype', None)
        if dtype is None or dtype.kind in 'SU':
            if g['fmt'] == 'NETCDF4' and g['string']:
                return str

            return 'S1'

        new_dtype = g['datatype'].get(dtype, None)
        if new_dtype is not None:
            dtype = new_dtype

        return '{0}{1}'.format(dtype.kind, dtype.itemsize)

    def _string_length_dimension(self, size):
        '''Create, if necessary, a netCDF dimension for string variables.

    :Parameters:

        size: `int`

    :Returns:

        `str`
            The netCDF dimension name.

        '''
        g = self.write_vars

        # ------------------------------------------------------------
        # Create a new dimension for the maximum string length
        # ------------------------------------------------------------
        ncdim = self._netcdf_name('strlen{0}'.format(size),
                                  dimsize=size, role='string_length')

        if ncdim not in g['ncdim_to_size']:
            # This string length dimension needs creating
            g['ncdim_to_size'][ncdim] = size
            g['netcdf'].createDimension(ncdim, size)

        return ncdim

    def _netcdf_dimensions(self, field, key, construct):
        '''Return a tuple of the netCDF dimension names for the axes of a
    metadata construct.

    If the construct has no data, then return `None`

    :Parameters:

        field: Field construct

        key: `str`

    :Returns:

        `tuple` or `None`
            The netCDF dimension names, or `None` if there are no
            data.

        '''
        g = self.write_vars

        domain_axes = self.implementation.get_construct_data_axes(field, key)

        if not domain_axes:
            # No data
            return

        domain_axes = tuple(domain_axes)

        ncdims = [g['axis_to_ncdim'][axis] for axis in domain_axes]

        compression_type = self.implementation.get_compression_type(construct)
        if compression_type:
            sample_dimension_position = (
                self.implementation.get_sample_dimension_position(construct))
            compressed_axes = (
                tuple(self.implementation.get_compressed_axes(
                    field, key, construct)))
            compressed_ncdims = tuple([g['axis_to_ncdim'][axis]
                                       for axis in compressed_axes])

            sample_ncdim = g['sample_ncdim'].get(compressed_ncdims)

            if compression_type == 'gathered':
                # ----------------------------------------------------
                # Compression by gathering
                # ----------------------------------------------------
                if sample_ncdim is None:
                    # The list variable has not yet been written to
                    # the file, so write it and also get the netCDF
                    # name of the sample dimension.
                    list_variable = self.implementation.get_list(construct)
                    sample_ncdim = self._write_list_variable(
                        field,
                        list_variable,
                        compress=' '.join(compressed_ncdims))
                    g['sample_ncdim'][compressed_ncdims] = sample_ncdim

            elif compression_type == 'ragged contiguous':
                # ----------------------------------------------------
                # Compression by contiguous ragged array
                #
                # No need to do anything because i) the count variable
                # has already been written to the file, ii) we already
                # have the position of the sample dimension in the
                # compressed array, and iii) we already have the
                # netCDF name of the sample dimension.
                # ----------------------------------------------------
                pass

            elif compression_type == 'ragged indexed':
                # ----------------------------------------------------
                # Compression by indexed ragged array
                #
                # No need to do anything because i) the index variable
                # has already been written to the file, ii) we already
                # have the position of the sample dimension in the
                # compressed array, and iii) we already have the
                # netCDF name of the sample dimension.
                # ----------------------------------------------------
                pass
            elif compression_type == 'ragged indexed contiguous':
                pass
            else:
                raise ValueError(
                    "Can't write {!r}: Unknown compression type: {!r}".format(
                        construct, compression_type))

            n = len(compressed_ncdims)
            ncdims[sample_dimension_position:sample_dimension_position + n] = (
                [sample_ncdim])
        # --- End: if

        return tuple(ncdims)

    def _write_dimension(self, ncdim, f, axis=None, unlimited=False,
                         size=None):
        '''Write a netCDF dimension to the file.

    :Parameters:

        ncdim: `str`
            The netCDF dimension name.

        f: Field construct

        axis: `str` or `None`
            The field's domain axis identifier.

        unlimited: `bool`, optional
            If `True` then create an unlimited dimension. By default
            dimensions are not unlimited.

        size: `int`, optional
            Must be set if *axis* is `None`.

    :Returns:

        `None`

        '''
        g = self.write_vars

        if axis is not None:
            domain_axis = self.implementation.get_domain_axes(f)[axis]
            logger.info(
                '    Writing {!r} to netCDF dimension:{}'.format(
                    domain_axis, ncdim)
            )  # pragma: no cover

            size = self.implementation.get_domain_axis_size(f, axis)
            g['axis_to_ncdim'][axis] = ncdim

        g['ncdim_to_size'][ncdim] = size

        if unlimited:
            # Create an unlimited dimension
            size = None
            try:
                g['netcdf'].createDimension(ncdim, size)
            except RuntimeError as error:
                message = ("Can't create unlimited dimension "
                           "in {} file ({}).".format(
                               g['netcdf'].file_format, error))

                error = str(error)
                if error == 'NetCDF: NC_UNLIMITED size already in use':
                    raise RuntimeError(
                        message + " In a {} file only one unlimited dimension "
                        "is allowed. Consider using a netCDF4 format.".format(
                            g['netcdf'].file_format))

                raise RuntimeError(message)
        else:
            try:
                g['netcdf'].createDimension(ncdim, size)
            except RuntimeError as error:
                raise RuntimeError(
                    "Can't create dimension of size {} in {} file ({})".format(
                        size, g['netcdf'].file_format, error))
        # --- End: if

    def _write_dimension_coordinate(self, f, key, coord):
        '''Write a coordinate variable and its bound variable to the file.

    This also writes a new netCDF dimension to the file and, if
    required, a new netCDF dimension for the bounds.

    :Parameters:

        f: Field construct

        key: `str`

        coord: Dimension coordinate construct

    :Returns:

        `str`
            The netCDF name of the dimension coordinate.

        '''
        g = self.write_vars

        seen = g['seen']

        data_axes = self.implementation.get_construct_data_axes(f, key)
        axis = data_axes[0]

        create = False
        if not self._already_in_file(coord):
            create = True
        elif seen[id(coord)]['ncdims'] != ():
            if seen[id(coord)]['ncvar'] != seen[id(coord)]['ncdims'][0]:
                # Already seen this coordinate but it was an auxiliary
                # coordinate, so it needs to be created as a dimension
                # coordinate.
                create = True
        # --- End: if

        if create:
            ncvar = self._create_netcdf_variable_name(coord,
                                                      default='coordinate')

            # Create a new dimension
#            unlimited = self._unlimited(f, axis)
            unlimited = self.implementation.nc_is_unlimited_axis(f, axis)
            self._write_dimension(ncvar, f, axis, unlimited=unlimited)

            ncdimensions = self._netcdf_dimensions(f, key, coord)

            # If this dimension coordinate has bounds then write the
            # bounds to the netCDF file and add the 'bounds' or
            # 'climatology' attribute (as appropriate) to a dictionary
            # of extra attributes
            extra = self._write_bounds(f, coord, key, ncdimensions, ncvar)

            # Create a new dimension coordinate variable
            self._write_netcdf_variable(ncvar, ncdimensions, coord,
                                        extra=extra)
        else:
            ncvar = seen[id(coord)]['ncvar']
            ncdimensions = seen[id(coord)]['ncdims']

        g['key_to_ncvar'][key] = ncvar
        g['key_to_ncdims'][key] = ncdimensions

        g['axis_to_ncdim'][axis] = ncvar

        return ncvar

    def _write_count_variable(self, f, count_variable, ncdim=None,
                              create_ncdim=True):
        '''TODO

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
            _ = self.implementation.nc_get_sample_dimension(count_variable,
                                                            'element')
            sample_ncdim = self._netcdf_name(_)
            self._write_dimension(
                sample_ncdim, f, None,
                size=int(self.implementation.get_data_sum(count_variable)))

            extra = {'sample_dimension': sample_ncdim}

            # Create a new list variable
            self._write_netcdf_variable(ncvar, (ncdim,),
                                        count_variable, extra=extra)

            g['count_variable_sample_dimension'][ncvar] = sample_ncdim
        else:
            ncvar = g['seen'][id(count_variable)]['ncvar']
            sample_ncdim = g['count_variable_sample_dimension'][ncvar]

        return sample_ncdim

    def _write_index_variable(self, f, index_variable,
                              sample_dimension, ncdim=None,
                              create_ncdim=True,
                              instance_dimension=None):
        '''Write an index variable to the netCDF file.

    :Parameters:

        f: Field construct

        index_variable: Index variable

        sample_dimension: `str`
            The name of the netCDF sample dimension.

        ncdim: `str`, optional

        create_ncdim: bool, optional

        instance_dimension: `str`, optional
            The name of the netCDF instance dimension.

    :Returns:

        `str`
            The name of the netCDF sample dimension.

        '''
        g = self.write_vars

        if not self._already_in_file(index_variable):
            ncvar = self._create_netcdf_variable_name(index_variable,
                                                      default='index')

            if create_ncdim:
                ncdiml = self._netcdf_name(ncdim)
                self._write_dimension(
                    ncdim, f, None,
                    size=self.implementation.get_data_size(index_variable))
            # --- End: if

            # Create a new list variable
            extra = {'instance_dimension': instance_dimension}
            self._write_netcdf_variable(ncvar, (ncdim,),
                                        index_variable, extra=extra)

            g['index_variable_sample_dimension'][ncvar] = sample_dimension
        else:
            ncvar = g['seen'][id(index_variable)]['ncvar']
            sample_ncdim = g['index_variable_sample_dimension'][ncvar]

        return sample_dimension

    def _write_list_variable(self, f, list_variable, compress):
        '''TODO

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

    def _write_scalar_data(self, value, ncvar):
        '''Write a dimension coordinate and bounds to the netCDF file.

    This also writes a new netCDF dimension to the file and, if
    required, a new netCDF bounds dimension.

    .. note:: This function updates ``g['seen']``.

    :Parameters:

        data: Data instance

        ncvar: `str`

    :Returns:

        `str`
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

    def _create_geometry_container(self, field):
        '''TODO

    .. versionadded:: 1.8.0

    :Parameters:

        field: Field construct

    :Returns:

        `dict`
            A representation off the CF-netCDF geometry container
            variable for field constuct. If there is no geometry
            container then the dictionary is empty.

        '''
        g = self.write_vars

        gc = {}
        for key, coord in self.implementation.get_auxiliary_coordinates(
                field).items():
            geometry_type = self.implementation.get_geometry(coord, None)
            if geometry_type not in self.cf_geometry_types():
                # No geometry bounds for this auxiliary coordinate
                continue

            nodes = self.implementation.get_bounds(coord)
            if nodes is None:
                # No geometry nodes for this auxiliary coordinate
                continue

            # assuming 1-d coord ...
            geometry_dimension = g['key_to_ncdims'][key][0]

            geometry_id = (geometry_dimension, geometry_type)
            gc.setdefault(geometry_id,
                          {'geometry_type'     : geometry_type,
                           'geometry_dimension': geometry_dimension})

            # Nodes
            nodes_ncvar = g['seen'][id(nodes)]['ncvar']
            gc[geometry_id].setdefault('node_coordinates', []).append(
                nodes_ncvar)

            # Coordinates
            try:
                coord_ncvar = g['seen'][id(coord)]['ncvar']
            except KeyError:
                # There is no netCDF auxiliary coordinate variable
                pass
            else:
                gc[geometry_id].setdefault('coordinates', []).append(
                    coord_ncvar)

            # Grid mapping
            grid_mappings = [
                g['seen'][id(cr)]['ncvar']
                for cr in field.coordinate_references.values()
                if (cr.coordinate_conversion.get_parameter(
                        'grid_mapping_name', None) is not None
                    and key in cr.coordinates())]
            gc[geometry_id].setdefault('grid_mapping', []).extend(
                grid_mappings)

            # Node count
            try:
                ncvar = g['geometry_encoding'][nodes_ncvar]['node_count']
            except KeyError:
                # There is no node count variable
                pass
            else:
                gc[geometry_id].setdefault('node_count', []).append(ncvar)

            # Part node count
            try:
                ncvar = g['geometry_encoding'][nodes_ncvar]['part_node_count']
            except KeyError:
                # There is no part node count variable
                pass
            else:
                gc[geometry_id].setdefault('part_node_count', []).append(ncvar)

            # Interior ring
            try:
                ncvar = g['geometry_encoding'][nodes_ncvar]['interior_ring']
            except KeyError:
                # There is no interior ring variable
                pass
            else:
                gc[geometry_id].setdefault('interior_ring', []).append(ncvar)
        # --- End: for

        if not gc:
            # This field has no geometries
            return {}

        for x in gc.values():
            # Node coordinates
            if 'node_coordinates' in x:
                x['node_coordinates'] = ' '.join(sorted(x['node_coordinates']))

            # Coordinates
            if 'coordinates' in x:
                x['coordinates'] = ' '.join(sorted(x['coordinates']))

            # Grid mapping
            grid_mappings = set(x.get('grid_mapping', ()))
            if len(grid_mappings) == 1:
                x['grid_mapping'] = grid_mappings.pop()
            elif len(grid_mappings) > 1:
                raise ValueError(
                    "Can't write {!r}: Geometry container has multiple "
                    "grid mapping variables: {!r}".format(
                        field, x['grid_mapping']))

            # Node count
            nc = set(x.get('node_count', ()))
            if len(nc) == 1:
                x['node_count'] = nc.pop()
            elif len(nc) > 1:
                raise ValueError(
                    "Can't write {!r}: Geometry container has multiple "
                    "node count variables: {!r}".format(
                        field, x['node_count']))

            # Part node count
            pnc = set(x.get('part_node_count', ()))
            if len(pnc) == 1:
                x['part_node_count'] = pnc.pop()
            elif len(pnc) > 1:
                raise ValueError(
                    "Can't write {!r}: Geometry container has multiple "
                    "part node count variables: {!r}".format(
                        field, x['part_node_count']))

            # Interior ring
            ir = set(x.get('interior_ring', ()))
            if len(ir) == 1:
                x['interior_ring'] = ir.pop()
            elif len(ir) > 1:
                raise ValueError(
                    "Can't write {!r}: Geometry container has multiple "
                    "interior ring variables: {!r}".format(
                        field, x['interior_ring']))
        # --- End: for

        if len(gc) > 1:
            raise ValueError(
                "Can't write {!r}: Multiple geometry containers: {!r}".format(
                    field, list(gc.values())))

        _, geometry_container = gc.popitem()

        return geometry_container

    def _already_in_file(self, variable, ncdims=None, ignore_type=False):
        '''Return True if a variable is logically equal any variable in the
    g['seen'] dictionary.

    If this is the case then the variable has already been written to
    the output netCDF file and so we don't need to do it again.

    If 'ncdims' is set then a extra condition for equality is applied,
    namely that of 'ncdims' being equal to the netCDF dimensions
    (names and order) to that of a variable in the g['seen']
    dictionary.

    When `True` is returned, the input variable is added to the
    g['seen'] dictionary.

    :Parameters:

        variable :

        ncdims : `tuple`, optional

    :Returns:

        `bool`
            `True` if the variable has already been written to the
            file, `False` otherwise.

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
            if self.implementation.equal_constructs(variable,
                                                    value['variable'],
                                                    ignore_type=ignore_type):
                seen[id(variable)] = {'variable': variable,
                                      'ncvar'   : value['ncvar'],
                                      'ncdims'  : value['ncdims']}
                return True
        # --- End: for

        return False

    def _write_geometry_container(self, field, geometry_container):
        '''Write a netCDF geometry container variable.

    .. versionadded:: 1.8.0

    :Returns:

        `str`
            The netCDF variable name for the geometry container.

        '''
        g = self.write_vars

        for ncvar, gc in g['geometry_containers'].items():
            if geometry_container == gc:
                # Use this existing geometry container
                return ncvar
        # --- End: for

        # Still here? Then write the geometry container to the file
        ncvar = self.implementation.nc_get_geometry_variable(
            field,
            default='geometry_container')
        ncvar = self._netcdf_name(ncvar)

        logger.info(
            '    Writing geometry container variable: {}'.format(ncvar)
        )  # pragma: no cover
        logger.info(
            '        {}'.format(geometry_container))  # pragma: no cover

        kwargs = {'varname': ncvar,
                  'datatype': 'S1',
                  'dimensions': (),
                  'endian': g['endian']}
        kwargs.update(g['netcdf_compression'])

        self._createVariable(**kwargs)

        g['nc'][ncvar].setncatts(geometry_container)

        # Update the 'geometry_containers' dictionary
        g['geometry_containers'][ncvar] = geometry_container

        return ncvar

    def _write_bounds(self, f, coord, coord_key, coord_ncdimensions,
                      coord_ncvar=None):
        '''Create a bounds netCDF variable, creating a new bounds netCDF
    dimension if required. Return the bounds variable's netCDF
    variable name.

    .. versionadded:: 1.7.0

    :Parameters:

        f: Field construct

        coord:

        coord_key: `str`
            The coordinate construct key.

        coord_ncdimensions: `tuple` of `str`
            The ordered netCDF dimension names of the coordinate's
            dimensions (which do not include the bounds dimension).

        coord_ncvar: `str`
            The netCDF variable name of the parent variable

    :Returns:

        `dict`

    **Examples:**

    >>> _write_bounds(c, ('dim2',))
    {'bounds': 'lat_bounds'}

    >>> _write_bounds(c, ('dim2',))
    {'nodes': 'x'}

    >>> _write_bounds(c, ('dim2',))
    {'climatology': 'time_bnds'}

        '''
        g = self.write_vars

        bounds = self.implementation.get_bounds(coord, None)
        if bounds is None:
            return {}

        data = self.implementation.get_data(bounds, None)
        if data is None:
            return {}

        if (g['output_version'] >= g['CF-1.8'] and
            self.implementation.is_geometry(coord)):
            
            # --------------------------------------------------------
            # CF>=1.8 and we have geometry bounds, which are dealt
            # with separately
            # --------------------------------------------------------
            extra = self._write_node_coordinates(coord, coord_ncvar,
                                                 coord_ncdimensions)
            return extra

        # Still here? Then this coordinate has non-geometry bounds
        # with data
        extra = {}

        size = data.shape[-1]

#        ncdim = self._netcdf_name('bounds{0}'.format(size),
#                                  dimsize=size, role='bounds')

        ncdim = self._netcdf_name(
            self.implementation.nc_get_dimension(bounds,
                                                 'bounds{0}'.format(size)),
            dimsize=size, role='bounds')

        # Check if this bounds variable has not been previously
        # created.
        ncdimensions = coord_ncdimensions + (ncdim,)
        if self._already_in_file(bounds, ncdimensions):
            # This bounds variable has been previously created, so no
            # need to do so again.
            ncvar = g['seen'][id(bounds)]['ncvar']
        else:
            # This bounds variable has not been previously created, so
            # create it now.
            ncdim_to_size = g['ncdim_to_size']
            if ncdim not in ncdim_to_size:
                logger.info(
                    '    Writing size {} netCDF dimension for '
                    'bounds: {}'.format(size, ncdim)
                )  # pragma: no cover

                ncdim_to_size[ncdim] = size
                g['netcdf'].createDimension(ncdim, size)

                # Set the netCDF bounds variable name
                default = coord_ncvar + '_bounds'
            else:
                default = 'bounds'

            ncvar = self.implementation.nc_get_variable(bounds,
                                                        default=default)
            ncvar = self._netcdf_name(ncvar)

            # Note that, in a field, bounds always have equal units to
            # their parent coordinate

            # Select properties to omit
            omit = []
            for prop in g['omit_bounds_properties']:
                if self.implementation.has_property(coord, prop):
                    omit.append(prop)
            # --- End: for

            # Create the bounds netCDF variable
            self._write_netcdf_variable(ncvar, ncdimensions, bounds,
                                        omit=omit)
        # --- End: if

        extra['bounds'] = ncvar
#        if self.implementation.is_climatology(coord):
        axes = self.implementation.get_construct_data_axes(f, coord_key)
        for clim_axis in f.climatological_time_axes():
            if clim_axis == axes:
                logger.info(
                    '    Setting climatological bounds'
                )  # pragma: no cover

                extra['climatology'] = extra.pop('bounds')
                break
        # --- End: for
#        else:

        g['bounds'][coord_ncvar] = ncvar

        return extra

    def _write_node_coordinates(self, coord, coord_ncvar,
                                coord_ncdimensions):
        '''Create a netCDF node coordinates variable.

    This will create:

    * A netCDF node dimension, if required.
    * A netCDF node count variable, if required.
    * A netCDF part node count variable, if required.
    * A netCDF interior ring variable, if required.

    .. versionadded:: 1.8.0

    :Parameters:

        coord:

        coord_ncvar: `str`

        coord_ncdimensions: `list`

    :Returns:

        `dict`

        '''
        out = {}

        g = self.write_vars

        bounds = self.implementation.get_bounds(coord, None)
        if bounds is None:
            return {}

        data = self.implementation.get_data(bounds, None)
        if data is None:
            return {}

        # Still here? Then this coordinate has a nodes attribute
        # which contains data.

        # Create the node coordinates flattened data
        array = self.implementation.get_array(data)
        array = self._numpy_compressed(array)
        data = self.implementation.initialise_Data(array=array, copy=False)

        # ------------------------------------------------------------
        # Create a bounds variable to hold the node coordinates
        # variable. This is what will be written to disk.
        # ------------------------------------------------------------
        nodes = self.implementation.initialise_Bounds()
        self.implementation.set_data(nodes, data, copy=False)
        properties = self.implementation.get_properties(bounds)
        self.implementation.set_properties(nodes, properties)

        # Find the base of the netCDF part dimension name
        size = self.implementation.get_data_size(nodes)
        ncdim = self._get_node_ncdimension(nodes, default='node')
        ncdim = self._netcdf_name(ncdim, dimsize=size, role='node')

        if self._already_in_file(nodes, (ncdim,)):
            # This node coordinates variable has been previously
            # created, so no need to do so again.
            ncvar = g['seen'][id(nodes)]['ncvar']

            # We need to log the original Bounds variable as being in
            # the file, too. This is so that the geometry container
            # variable can be created later on.
            g['seen'][id(bounds)] = {'ncvar': ncvar,
                                     'variable': bounds,
                                     'ncdims': None}
        else:
            # This node coordinates variable has not been previously
            # created, so create it now.
            ncdim_to_size = g['ncdim_to_size']
            if ncdim not in ncdim_to_size:
                size = self.implementation.get_data_size(nodes)
                logger.info(
                    '    Writing size {} netCDF node dimension: '
                    '{}'.format(size, ncdim)
                )  # pragma: no cover

                ncdim_to_size[ncdim] = size
                g['netcdf'].createDimension(ncdim, size)

            # Set an appropriate default netCDF node coordinates
            # variable name
            axis = self.implementation.get_property(bounds, 'axis')
            if axis is not None:
                default = str(axis).lower()
            else:
                default = 'node_coordinate'

            ncvar = self.implementation.nc_get_variable(bounds,
                                                        default=default)
            ncvar = self._netcdf_name(ncvar)

            # Create the netCDF node coordinates variable
            self._write_netcdf_variable(ncvar, (ncdim,), nodes)

            encodings = {}

            _ = self._write_node_count(coord, bounds,
                                       coord_ncdimensions, encodings)
            encodings.update(_)

            _ = self._write_part_node_count(coord, bounds, encodings)
            encodings.update(_)

            _ = self._write_interior_ring(coord, bounds, encodings)
            encodings.update(_)

            g['geometry_encoding'][ncvar] = encodings

            # We need to log the original Bounds variable as being in
            # the file, too. This is so that the geometry container
            # variable can be created later on.
            g['seen'][id(bounds)] = {'ncvar'   : ncvar,
                                     'variable': bounds,
                                     'ncdims'  : None}
        # --- End: if

        if coord_ncvar is not None:
            g['bounds'][coord_ncvar] = ncvar

        return {'nodes': ncvar}

    def _write_node_count(self, coord, bounds, coord_ncdimensions,
                          encodings):
        '''Create a netCDF node count variable.

    .. versionadded:: 1.8.0

    :Parameters:

        coord:

        bounds:

        coord_ncdimensions: sequence of `str`

        encodings: `dict`
            Ignored.

    :Returns:

        `dict`

        '''
        g = self.write_vars

        # Create the node count flattened data
        array = self.implementation.get_array(self.implementation.get_data(
            bounds))
        if self.implementation.get_data_ndim(bounds) == 2:    # DCH
            array = numpy.ma.count(array, axis=1)             # DCH
        else:                                                 # DCH
            array = numpy.ma.count(array, axis=2).sum(axis=1) # DCH

        data = self.implementation.initialise_Data(array=array, copy=False)

        # ------------------------------------------------------------
        # Create a count variable to hold the node count data and
        # properties. This is what will be written to disk.
        # ------------------------------------------------------------
        count = self.implementation.initialise_Count()
        self.implementation.set_data(count, data, copy=False)

        # Find the base of the netCDF node count variable name
        nc = self.implementation.get_node_count(coord)
        if nc is not None:
            ncvar = self.implementation.nc_get_variable(nc,
                                                        default='node_count')
            # Copy node count variable properties to the new count
            # variable
            properties = self.implementation.get_properties(nc)
            self.implementation.set_properties(count, properties)
        else:
            ncvar = 'node_count'

        geometry_dimension = coord_ncdimensions[0]

        if self._already_in_file(count, (geometry_dimension,)):
            # This node count variable has been previously created, so
            # no need to do so again.
            ncvar = g['seen'][id(count)]['ncvar']
        else:
            # This node count variable has not been previously
            # created, so create it now.
            if geometry_dimension not in g['ncdim_to_size']:
                raise ValueError(
                    "The netCDF geometry dimension should already exist ...")

            ncvar = self._netcdf_name(ncvar)

            # Create the netCDF node cuont variable
            self._write_netcdf_variable(ncvar, (geometry_dimension,), count)
        # --- End: if

        # Return encodings
        return {'geometry_dimension': geometry_dimension,
                'node_count'        : ncvar}

    def _get_part_ncdimension(self, coord, default=None):
        '''Get the base of the netCDF dimension for part node count and
    interior ring variables.

    .. versionadded:: 1.8.0

    :Returns:

        TODO

        '''
        ncdim = None

        pnc = self.implementation.get_part_node_count(coord)
        if pnc is not None:
            # Try to get the netCDF dimension from a part node count
            # variable
            ncdim = self.implementation.nc_get_dimension(pnc, default=None)

        if ncdim is None:
            # Try to get the netCDF dimension from an interior ring
            # variable
            interior_ring = self.implementation.get_interior_ring(coord)
            if interior_ring is not None:
                ncdim = self.implementation.nc_get_dimension(interior_ring,
                                                             default=None)
        # --- End: if

        if ncdim is not None:
            # Found a netCDF dimension
            return ncdim

        # Return the default
        return default

    def _get_node_ncdimension(self, bounds, default=None):
        '''TODO

    .. versionadded:: 1.8.0

    :Returns:

        TODO

        '''
        ncdim = self.implementation.nc_get_dimension(bounds, default=None)
        if ncdim is not None:
            # Found a netCDF dimension
            return ncdim

        # Retrun the default
        return default

    def _write_part_node_count(self, coord, bounds, encodings):
        '''Create a bounds netCDF variable, creating a new bounds netCDF
    dimension if required. Return the bounds variable's netCDF
    variable name.

    .. versionadded:: 1.8.0

    :Parameters:

        coord:

        coord_ncvar: `str`
            The netCDF variable name of the parent variable

    :Returns:

        `dict`

    **Examples:**

    >>> _write_part_node_count(c, b)
    {'part_node_count': 'pnc'}

    >>> _write_part_node_count(c, b)
    {}

        '''
#        if self.implementation.get_data_ndim(bounds) < 3: # DCH
#            # No need for a part node count variable required
#            return {}
        if self.implementation.get_data_shape(bounds)[1] == 1:
            # No part node count variable required
            return {}

        g = self.write_vars

        # Create the part node count flattened data
        array = self.implementation.get_array(self.implementation.get_data(
            bounds))
        array = numpy.trim_zeros(numpy.ma.count(array, axis=2).flatten())
        data = self.implementation.initialise_Data(array=array, copy=False)

        # ------------------------------------------------------------
        # Create a count variable to hold the part node count data and
        # properties. This is what will be written to disk.
        # ------------------------------------------------------------
        count = self.implementation.initialise_Count()
        self.implementation.set_data(count, data, copy=False)

        # Find the base of the netCDF part_node_count variable name
        pnc = self.implementation.get_part_node_count(coord)
        if pnc is not None:
            ncvar = self.implementation.nc_get_variable(
                pnc,
                default='part_node_count')
            # Copy part node count variable properties to the new
            # count variable
            properties = self.implementation.get_properties(pnc)
            self.implementation.set_properties(count, properties)
        else:
            ncvar = 'part_node_count'

        # Find the base of the netCDF part dimension name
        size = self.implementation.get_data_size(count)
        if g['part_ncdim'] is not None:
            ncdim = g['part_ncdim']
        elif 'part_ncdim' in encodings:
            ncdim = encodings['part_ncdim']
        else:
            ncdim = self._get_part_ncdimension(coord, default='part')
            ncdim = self._netcdf_name(ncdim, dimsize=size, role='part')

        if self._already_in_file(count, (ncdim,)):
            # This part node count variable has been previously
            # created, so no need to do so again.
            ncvar = g['seen'][id(count)]['ncvar']
        else:
            ncdim_to_size = g['ncdim_to_size']
            if ncdim not in ncdim_to_size:
                logger.info(
                    '    Writing size {} netCDF part '
                    'dimension{}'.format(size, ncdim)
                )  # pragma: no cover

                ncdim_to_size[ncdim] = size
                g['netcdf'].createDimension(ncdim, size)

            ncvar = self._netcdf_name(ncvar)

            # Create the netCDF part_node_count variable
            self._write_netcdf_variable(ncvar, (ncdim,), count)
        # --- End: if

        g['part_ncdim'] = ncdim

        return {'part_node_count': ncvar,
                'part_ncdim'     : ncdim}

    def _write_interior_ring(self, coord, bounds, encodings):
        '''TODO

    .. versionadded:: 1.8.0

    :Parameters:

        coord:

        coord_ncvar: `str`
            The netCDF variable name of the parent variable

    :Returns:

        `dict`

        '''
        interior_ring = self.implementation.get_interior_ring(coord)
        if interior_ring is None:
            return {}

        g = self.write_vars

#        array = self.implementation.get_data(interior_ring).array.compressed()
        data = self.implementation.get_data(interior_ring)
        array = self.implementation.get_array(data)
        array = self._numpy_compressed(array)

        # Replace the data with its compressed, flattened version
        interior_ring = self.implementation.copy_construct(interior_ring)
        data = self.implementation.initialise_Data(array=array, copy=False)
        self.implementation.set_data(interior_ring, data, copy=False)

        ncvar = self.implementation.nc_get_variable(interior_ring,
                                                    default='interior_ring')

        size = self.implementation.get_data_size(interior_ring)
        if g['part_ncdim'] is not None:
            ncdim = g['part_ncdim']
        elif 'part_ncdim' in encodings:
            ncdim = encodings['part_ncdim']
        else:
            ncdim = self._get_part_ncdimension(coord, default='part')
            ncdim = self._netcdf_name(ncdim, dimsize=size, role='part')

        if self._already_in_file(interior_ring, (ncdim,)):
            # This interior ring variable has been previously created,
            # so no need to do so again.
            ncvar = g['seen'][id(interior_ring)]['ncvar']
        else:
            ncdim_to_size = g['ncdim_to_size']
            if ncdim not in ncdim_to_size:
                logger.info(
                    '    Writing size {} netCDF part '
                    'dimension{}'.format(size, ncdim)
                )  # pragma: no cover
                ncdim_to_size[ncdim] = size
                g['netcdf'].createDimension(ncdim, size)

            ncvar = self._netcdf_name(ncvar)

            # Create the netCDF interior ring variable
            self._write_netcdf_variable(ncvar, (ncdim,), interior_ring)
        # --- End: if

        g['part_ncdim'] = ncdim

        return {'interior_ring': ncvar,
                'part_ncdim'   : ncdim}

    def _write_scalar_coordinate(self, f, key, coord_1d, axis, coordinates,
                                 extra={}):
        '''Write a scalar coordinate and its bounds to the netCDF file.

    It is assumed that the input coordinate is has size 1, but this is not
    checked.

    If an equal scalar coordinate has already been written to the file
    then the input coordinate is not written.

    :Parameters:

        f: Field construct

        key: `str`
            The coordinate construct key

        coordinate
        axis : str
            The field's axis identifier for the scalar coordinate.

        coordinates: `list`

    :Returns:

        coordinates: `list`
            The updated list of netCDF auxiliary coordinate names.

        '''
        g = self.write_vars

        scalar_coord = self.implementation.squeeze(coord_1d, axes=0)

        if not self._already_in_file(scalar_coord, ()):
            ncvar = self._create_netcdf_variable_name(scalar_coord,
                                                      default='scalar')

            # If this scalar coordinate has bounds then create the
            # bounds netCDF variable and add the 'bounds' or
            # 'climatology' (as appropriate) attribute to the
            # dictionary of extra attributes
            bounds_extra = self._write_bounds(f, scalar_coord, key, (), ncvar)

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

    def _write_auxiliary_coordinate(self, f, key, coord, coordinates):
        '''Write auxiliary coordinates and bounds to the netCDF file.

    If an equal auxiliary coordinate has already been written to the file
    then the input coordinate is not written.

    :Parameters:

        f: Field construct

        key: `str`

        coord: `Coordinate`

        coordinates: `list`

    :Returns:

        coordinates: `list`
            The list of netCDF auxiliary coordinate names updated in
            place.

    **Examples:**

    >>> coordinates = _write_auxiliary_coordinate(f, 'aux2', coordinates)

        '''
        g = self.write_vars

        ncvar = None

        # The netCDF dimensions for the auxiliary coordinate variable
        ncdimensions = self._netcdf_dimensions(f, key, coord)

        if self._already_in_file(coord, ncdimensions):
            ncvar = g['seen'][id(coord)]['ncvar']

            # Register that bounds as being the file, too. This is so
            # that a geometry container variable can be created later
            # on, if required.
            bounds_ncvar = g['bounds'].get(ncvar)
            if bounds_ncvar is not None:
                bounds = self.implementation.get_bounds(coord, None)
                if bounds is not None:
                    g['seen'][id(bounds)] = {'ncvar'   : bounds_ncvar,
                                             'variable': bounds,
                                             'ncdims'  : None}
        else:
            if (not self.implementation.get_properties(coord) and
                self.implementation.get_data(coord, default=None) is None):
                # No coordinates, but possibly bounds
                self._write_bounds(f, coord, key, ncdimensions,
                                   coord_ncvar=None)
            else:
                ncvar = self._create_netcdf_variable_name(coord,
                                                          default='auxiliary')

                # TODO: move setting of bounds ncvar to here - why?

                # If this auxiliary coordinate has bounds then create
                # the bounds netCDF variable and add the 'bounds',
                # 'climatology' or 'nodes' attribute (as appropriate)
                # to the dictionary of extra attributes.
                extra = self._write_bounds(f, coord, key, ncdimensions, ncvar)

                # Create a new auxiliary coordinate variable, if it has data
                if self.implementation.get_data(coord, None) is not None:
                    self._write_netcdf_variable(ncvar, ncdimensions, coord,
                                                extra=extra)

#                g['key_to_ncvar'][key] = ncvar
#                g['key_to_ncdims'][key] = ncdimensions
        # --- End: if

        g['key_to_ncvar'][key] = ncvar
        g['key_to_ncdims'][key] = ncdimensions

        if ncvar is not None:
            coordinates.append(ncvar)

        return coordinates

    def _write_domain_ancillary(self, f, key, anc):
        '''Write a domain ancillary and its bounds to the netCDF file.

    If an equal domain ancillary has already been written to the file
    athen it is not re-written.

    .. versionadded:: 1.7.0

    :Parameters:

        f: Field construct

        key: `str`
            The internal identifier of the domain ancillary object.

        anc: Domain ancillary construct

    :Returns:

        `str`
            The netCDF variable name of the domain ancillary variable.

        '''
        g = self.write_vars

        ncdimensions = self._netcdf_dimensions(f, key, anc)

        create = not self._already_in_file(anc, ncdimensions, ignore_type=True)

        if not create:
            ncvar = g['seen'][id(anc)]['ncvar']
        else:
            # See if we can set the default netCDF variable name to
            # its formula_terms term
            default = None
            for ref in self.implementation.get_coordinate_references(
                    f).values():
                for term, da_key in ref.coordinate_conversion.domain_ancillaries().items(): # DCH ALERT
                    if da_key == key:
                        default = term
                        break
                # --- End: for
                if default is not None:
                    break
            # --- End: for

            if default is None:
                default = 'domain_ancillary'

            ncvar = self._create_netcdf_variable_name(anc,
                                                      default=default)

            # If this domain ancillary has bounds then create the bounds
            # netCDF variable
            self._write_bounds(f, anc, key, ncdimensions, ncvar)

            # Create a new domain ancillary variable
            self._write_netcdf_variable(ncvar, ncdimensions, anc)

        g['key_to_ncvar'][key] = ncvar
        g['key_to_ncdims'][key] = ncdimensions

        return ncvar

    def _write_field_ancillary(self, f, key, anc):
        '''Write a field ancillary to the netCDF file.

    If an equal field ancillary has already been written to the file
    then it is not re-written.

    :Parameters:

        f : Field construct

        key : str

        anc : Field ancillary construct

    :Returns:

        `str`
            The netCDF variable name of the field ancillary object.

    **Examples:**

    >>> ncvar = _write_field_ancillary(f, 'fieldancillary2', anc)

        '''
        g = self.write_vars

        ncdimensions = self._netcdf_dimensions(f, key, anc)

        create = not self._already_in_file(anc, ncdimensions)

        if not create:
            ncvar = g['seen'][id(anc)]['ncvar']
        else:
            ncvar = self._create_netcdf_variable_name(anc,
                                                      default='ancillary_data')

            # Create a new field ancillary variable
            self._write_netcdf_variable(ncvar, ncdimensions, anc)

        g['key_to_ncvar'][key] = ncvar
        g['key_to_ncdims'][key] = ncdimensions

        return ncvar

    def _write_cell_measure(self, field, key, cell_measure):
        '''Write a cell measure construct to the netCDF file.

    If an identical construct has already in the file then the cell
    measure will not be written.

    :Parameters:

        field: Field construct
            The field containing the cell measure.

        key: `str`
            The identifier of the cell measure (e.g. 'cellmeasure0').

        cell_measure: Cell measure construct

    :Returns:

        `str`
            The 'measure: ncvar'.

        '''
        g = self.write_vars

        measure = self.implementation.get_measure(cell_measure)
        if measure is None:
            raise ValueError(
                "Can't create a netCDF cell measure variable "
                "without a 'measure' property")

        ncdimensions = self._netcdf_dimensions(field, key, cell_measure)

        if self._already_in_file(cell_measure, ncdimensions):
            # Use existing cell measure variable
            ncvar = g['seen'][id(cell_measure)]['ncvar']
        elif self.implementation.nc_get_external(cell_measure):
            # The cell measure is external
            ncvar = self._create_netcdf_variable_name(cell_measure,
                                                      default='cell_measure')

            # Add ncvar to the global external_variables attribute
            self._set_external_variables(ncvar)

            # Create a new field to write out to the external file
            if g['external_file'] is not None:
                self._create_external(field=field, construct_id=key,
                                      ncvar=ncvar, ncdimensions=ncdimensions)
        else:
            ncvar = self._create_netcdf_variable_name(cell_measure,
                                                      default='cell_measure')

            # Create a new cell measure variable
            self._write_netcdf_variable(ncvar, ncdimensions, cell_measure)

        g['key_to_ncvar'][key] = ncvar
        g['key_to_ncdims'][key] = ncdimensions

        # Update the field's cell_measures list
        return '{0}: {1}'.format(measure, ncvar)

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

    def _create_external(self, field=None, construct_id=None,
                         ncvar=None, ncdimensions=None):
        '''Create a new field to flag it for being written the external file.

    .. versionadded:: 1.7.0

        '''
        g = self.write_vars

        if ncdimensions is None:
            return

        # Still here?
        external = self.implementation.convert(
            field=field,
            construct_id=construct_id)

        # Set the correct netCDF variable and dimension names
        self.implementation.nc_set_variable(external, ncvar)

        external_domain_axes = self.implementation.get_domain_axes(external)
        for ncdim, axis in zip(ncdimensions,
                               self.implementation.get_field_data_axes(
                                   external)):
            external_domain_axis = external_domain_axes[axis]
            self.implementation.nc_set_dimension(external_domain_axis, ncdim)

        g['external_fields'].append(external)

        return external

    def _createVariable(self, **kwargs):
        '''TODO

    .. versionadded:: 1.7.0

        '''
        g = self.write_vars

        ncvar = kwargs['varname']

        g['nc'][ncvar] = g['netcdf'].createVariable(**kwargs)

    def _write_grid_mapping(self, f, ref, multiple_grid_mappings):
        '''Write a grid mapping georeference to the netCDF file.

    .. versionadded:: 1.7.0

    :Parameters:

        f: Field construct

        ref: Coordinate reference construct
            The grid mapping coordinate reference to write to the file.

        multiple_grid_mappings: `bool`

    :Returns:

        `str`

        '''
        g = self.write_vars

        if self._already_in_file(ref):
            # Use existing grid_mapping variable
            ncvar = g['seen'][id(ref)]['ncvar']

        else:
            # Create a new grid mapping variable
            cc_parameters = (
                self.implementation.get_coordinate_conversion_parameters(ref))
            default = cc_parameters.get('grid_mapping_name', 'grid_mapping')
            ncvar = self._create_netcdf_variable_name(ref, default=default)

            logger.info(
                '    Writing {!r} to netCDF variable:'.format(ref, ncvar)
            )# pragma: no cover

            kwargs = {'varname': ncvar,
                      'datatype': 'S1',
                      'dimensions': (),
                      'endian': g['endian']}
            kwargs.update(g['netcdf_compression'])

            self._createVariable(**kwargs)

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

            g['nc'][ncvar].setncatts(parameters)

            # Update the 'seen' dictionary
            g['seen'][id(ref)] = {'variable': ref,
                                  'ncvar'   : ncvar,
                                  # Grid mappings have no netCDF dimensions
                                  'ncdims'  : (),
            }
        # --- End: if

        if multiple_grid_mappings:
            return '{0}: {1}'.format(
                ncvar,
                ' '.join(
                    sorted([g['key_to_ncvar'][key]
                            for key in self.implementation.get_coordinate_reference_coordinates(ref)])))
        else:
            return ncvar

    def _write_netcdf_variable(self, ncvar, ncdimensions, cfvar,
                               omit=(), extra={}, fill=False,
                               data_variable=False):
        '''Create a netCDF variable from *cfvar* with name *ncvar* and
    dimensions *ncdimensions*. The new netCDF variable's properties
    are given by cfvar.properties(), less any given by the *omit*
    argument. If a new string-length netCDF dimension is required then
    it will also be created. The ``seen`` dictionary is updated for
    *cfvar*.

    :Parameters:

        ncvar: `str`
            The netCDF name of the variable.

        dimensions: `tuple`
            The netCDF dimension names of the variable

        cfvar: `Variable`
            The construct to write to the netCDF file.

        omit: sequence of `str`, optional

        extra: `dict`, optional

    :Returns:

        `None`

        '''
        g = self.write_vars

        logger.info('    Writing {!r}'.format(cfvar))  # pragma: no cover

        # ------------------------------------------------------------
        # Set the netCDF4.createVariable datatype
        # ------------------------------------------------------------
        datatype = self._datatype(cfvar)
        data = self.implementation.get_data(cfvar, None)

        original_ncdimensions = ncdimensions

        data, ncdimensions = self._transform_strings(cfvar, data,
                                                     ncdimensions)

        # ------------------------------------------------------------
        # Find the fill value - the value that the variable's data get
        # filled before any data is written. if the fill value is
        # False then the variable is not pre-filled.
        # ------------------------------------------------------------
        # if fill:
        #    fill_value = self.implementation.get_property(cfvar, '_FillValue', None)
        # else:
#        fill_value = None #False

#        fill_value = None
#        if g['fmt'] == 'NETCDF4' and datatype == str:
#            fill_value = '\x00'

        if data_variable:
            lsd = g['least_significant_digit']
        else:
            lsd = None

        # Set HDF chunk sizes
        chunksizes = None
        if data is not None:
            chunksizes = self.implementation.nc_get_hdf5_chunksizes(data)

        if chunksizes is not None:
            logger.detail(
                '      HDF5 chunksizes: {}'.format(chunksizes)
            )  # pragma: no cover

        # ------------------------------------------------------------
        # Create a new netCDF variable
        # ------------------------------------------------------------
        kwargs = {'varname'   : ncvar,
                  'datatype'  : datatype,
                  'dimensions': ncdimensions,
                  'endian'    : g['endian'],
                  'chunksizes': chunksizes,
#                  'fill_value': fill_value,
#                  'least_significant_digit': lsd,
        }

        kwargs.update(g['netcdf_compression'])

        # TODO
        kwargs = self._customize_createVariable(cfvar, kwargs)

        logger.info(
            ' to netCDF variable: {}({})'.format(
                ncvar, ', '.join(ncdimensions))
        )  # pragma: no cover

        try:
            self._createVariable(**kwargs)
        except RuntimeError as error:
            error = str(error)
            if error == ("NetCDF: Not a valid data type or _FillValue "
                         "type mismatch"):
                raise ValueError(
                    "Can't write {} data from {!r} to a {} file. "
                    "Consider using a netCDF4 format, or use the 'datatype' "
                    "parameter, or change the datatype before writing.".format(
                        cfvar.data.dtype.name, cfvar, g['netcdf'].file_format))

            message = "Can't create variable in {} file from {} ({})".format(
                g['netcdf'].file_format, cfvar, error)

            if error == 'NetCDF: NC_UNLIMITED in the wrong index':
                raise RuntimeError(
                    message + ". In a {} file the unlimited dimension must "
                    "be the first (leftmost) dimension of the variable. "
                    "Consider using a netCDF4 format.".format(
                        g['netcdf'].file_format))

            raise RuntimeError(message)

        # ------------------------------------------------------------
        # Write attributes to the netCDF variable
        # ------------------------------------------------------------
        attributes = self._write_attributes(cfvar, ncvar, extra=extra,
                                            omit=omit)

        # ------------------------------------------------------------
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
            _FillValue = self.implementation.get_property(cfvar,
                                                          '_FillValue',
                                                          None)
            missing_value = self.implementation.get_property(cfvar,
                                                             'missing_value',
                                                             None)
            unset_values = [value for value in (_FillValue, missing_value)
                            if value is not None]

            compressed = bool(
                set(ncdimensions).intersection(g['sample_ncdim'].values()))

            self._write_data(data, cfvar, ncvar, ncdimensions,
                             unset_values=unset_values,
                             compressed=compressed,
                             attributes=attributes)

        # Update the 'seen' dictionary
        g['seen'][id(cfvar)] = {'variable': cfvar,
                                'ncvar'   : ncvar,
                                'ncdims'  : original_ncdimensions}

    def _customize_createVariable(self, cfvar, kwargs):
        '''TODO

    .. versionadded:: 1.7.6

    :Parameters:

        cfvar: CFDM instance that contains data

        kwargs: `dict`

        '''
        return kwargs

    def _transform_strings(self, construct, data, ncdimensions):
        '''TODO

    .. versionadded:: 1.7.3

    :Parameters:

        construct:

        data: Data instance or `None`

        ncdimensions: `tuple`

    :Returns:

        `Data`, `tuple`

        '''
        datatype = self._datatype(construct)

        if data is not None and datatype == 'S1':
            # --------------------------------------------------------
            # Convert a string data type numpy array into a character
            # data type ('S1') numpy array with an extra trailing
            # dimension. Note that for NETCDF4 output files, datatype
            # is str, so this conversion does not happen.
            # --------------------------------------------------------
            array = self.implementation.get_array(data)
#            if numpy.ma.is_masked(array):
#                array = array.compressed()
#            else:
#                array = array.flatten()
            array = self._numpy_compressed(array)

            strlen = len(max(array, key=len))

            data = self._convert_to_char(data)
            ncdim = self._string_length_dimension(strlen)

            ncdimensions = ncdimensions + (ncdim,)

        return data, ncdimensions

    def _write_data(self, data, cfvar, ncvar, ncdimensions,
                    unset_values=(), compressed=False, attributes={}):
        '''TODO

    :Parameters:

        data: Data instance

        cfvar: cfdm instance

        ncvar: `str`

        ncdimensions: `tuple` of `str`

        unset_values: sequence of numbers

        attributes: `dict`, optional
            The netCDF attributes for the constructs that have been
            written to the file.

        '''
        g = self.write_vars

        if compressed:
#        if set(ncdimensions).intersection(g['sample_ncdim'].values()):
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
#            if numpy.ma.is_masked(array):
#                temp_array = array.compressed()
#            else:
#                temp_array = array
            if numpy.intersect1d(unset_values,
                                 self._numpy_compressed(array)).size:
                raise ValueError(
                    "ERROR: Can't write data that has _FillValue or "
                    "missing_value at unmasked point: {!r}".format(ncvar))
        # --- End: if

        if (g['fmt'] == 'NETCDF4' and array.dtype.kind in 'SU' and
            numpy.ma.isMA(array)):
            # VLEN variables can not be assigned to by masked arrays
            # https://github.com/Unidata/netcdf4-python/pull/465
            array = array.filled('')

        if g['warn_valid']:
            # Check for out-of-range values
            warned = self._check_valid(cfvar, array, attributes)

        # Copy the array into the netCDF variable
        g['nc'][ncvar][...] = array

        self._aaa(ncvar, array)

    def _check_valid(self, cfvar, array, attributes):
        '''Check array for out-of-range values, as defined by the
    valid_[min|max|range] attributes.

    .. versionadded:: 1.8.3

    :Parameters:

        cfvar: Construct

        array: `numpy.ndarray`

        attributes: `dict`

    :Returns:

        `bool`
            Whether or not a warning was issued.

        '''
        out = 0

        valid_range = None
        valid_min = None
        valid_max = None

        if 'valid_range' in attributes:
            prop = 'valid_range'
            valid_range = True
            valid_min, valid_max = attributes[prop]

        message = ("WARNING: {!r} has data values written to {} "
                   "that are strictly {} than the valid {} "
                   "defined by the {} property: {}. "
                   "Set warn_valid=False to remove warning.")

        if 'valid_min' in attributes:
            prop = 'valid_min'
            if valid_range:
                raise ValueError("Can't write {!r} with both {} and "
                                 "valid_range properties".format(cvfar, prop))

            valid_min = attributes[prop]

        if valid_min is not None and array.min() < valid_min:
            print(message.format(
                cfvar, self.write_vars['filename'],
                'less', 'minimum', prop, valid_min))
            out += 1

        if 'valid_max' in attributes:
            prop = 'valid_max'
            if valid_range:
                raise ValueError("Can't write {!r} with both {} and "
                                 "valid_range properties".format(cvfar, prop))

            valid_max = attributes[prop]

        if valid_max is not None and array.max() > valid_max:
            print(message.format(
                cfvar, self.write_vars['filename'],
                'greater', 'maximum', prop, valid_max))
            out += 1

        return bool(out)

    def _aaa(self, ncvar, array):
        '''TODO

        '''
        g = self.write_vars

    def _convert_to_char(self, data):
        '''Convert string data into character data

    The return Data instance object will have data type 'S1' and will
    have an extra trailing dimension.

    .. versionadded:: 1.7.0

    :Parameters:

        data: Data instance

    :Returns:

        Data instance

        '''
        strlen = data.dtype.itemsize
#        print ('1 strlen =', strlen)
#        if strlen > 1:
        data = self.implementation.initialise_Data(
                array=self._character_array(
                    self.implementation.get_array(data)),
                units=self.implementation.get_data_units(data, None),
                calendar=self.implementation.get_data_calendar(data, None),
                copy=False)

        return data

    def _write_field(self, f, add_to_seen=False,
                     allow_data_insert_dimension=True):
        '''TODO

    .. versionadded:: 1.7.0

    :Parameters:

        f : Field construct

        add_to_seen : bool, optional

        allow_data_insert_dimension: `bool`, optional

    :Returns:

        `None`

        '''
        g = self.write_vars

        logger.info('  Writing {!r}:'.format(f))  # pragma: no cover

        xxx = []

        seen = g['seen']

        org_f = f
        if add_to_seen:
            id_f = id(f)

        # Copy the field, as we are almost certainly about to do
        # terrible things to it (or are we? should review this)
        f = self.implementation.copy_construct(org_f)

        data_axes = list(self.implementation.get_field_data_axes(f))

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

        # Mapping of construct internal identifiers to their netCDF
        # dimensions. This gets reset for each new field that is
        # written to the file.
        #
        # For example: {'dimensioncoordinate1': ['longitude']}
        g['key_to_ncdims'] = {}

        # Type of compression applied to the field
        compression_type = self.implementation.get_compression_type(f)
        g['compression_type'] = compression_type
        logger.info(
            "    Compression = {!r}".format(g['compression_type'])
        )  # pragma: no cover

        #
        g['sample_ncdim'] = {}

        #
        g['part_ncdim'] = None

        # Initialize the list of the field's auxiliary/scalar
        # coordinates
        coordinates = []

        if g['output_version'] >= g['CF-1.8']:
            if not self.implementation.conform_geometry_variables(f):
                raise ValueError(
                    "Can't write {!r}: node count, part node count, "
                    "or interior ring variables have "
                    "inconistent properties".format(f))
        # --- End: if

        g['formula_terms_refs'] = [
            ref
            for ref in list(self.implementation.get_coordinate_references(
                    f).values())
            if self.implementation.get_coordinate_conversion_parameters(
                    ref).get('standard_name', False)
        ]

        g['grid_mapping_refs'] = [
            ref
            for ref in list(
                    self.implementation.get_coordinate_references(f).values())
            if self.implementation.get_coordinate_conversion_parameters(
                    ref).get('grid_mapping_name', False)
        ]

        field_coordinates = self.implementation.get_coordinates(f)

        owning_coordinates = []
        standard_names = []
        computed_standard_names = []
        for ref in g['formula_terms_refs']:
            coord_key = None

            standard_name = (
                self.implementation.get_coordinate_conversion_parameters(
                    ref).get('standard_name')
            )
            computed_standard_name = (
                self.implementation.get_coordinate_conversion_parameters(
                    ref).get('computed_standard_name')
            )

            if (standard_name is not None
                and computed_standard_name is not None):
                for key in self.implementation.get_coordinate_reference_coordinates(ref):
                    coord = field_coordinates[key]

                    if not (self.implementation.get_data_ndim(coord) == 1 and
                            self.implementation.get_property(coord, 'standard_name', None) == standard_name):
                        continue

                    if coord_key is not None:
                        coord_key = None
                        break

                    coord_key = key
            # --- End: if

            owning_coordinates.append(coord_key)
            standard_names.append(standard_name)
            computed_standard_names.append(computed_standard_name)
        # --- End: for

        for key, csn in zip(owning_coordinates, computed_standard_names):
            if key is None:
                continue

            x = self.implementation.get_property(
                coord, 'computed_standard_name', None)
            if x is None:
                self.implementation.set_property(
                    field_coordinates[key], 'computed_standard_name', csn)
            elif x != csn:
                raise ValueError(";sdm p8whw=0[")
        # --- End: for

        dimension_coordinates = (
            self.implementation.get_dimension_coordinates(f)
        )

        # For each of the field's domain axes ...
        domain_axes = self.implementation.get_domain_axes(f)

        for axis in sorted(domain_axes):
            found_dimension_coordinate = False
            for key, dim_coord in dimension_coordinates.items():
                if self.implementation.get_construct_data_axes(f, key) != (axis,):
                    continue

                # ----------------------------------------------------
                # Still here? Then a dimension coordinate exists for
                # this domain axis.
                # ----------------------------------------------------
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
                        len(self.implementation.get_constructs(
                            f, axes=[axis])) >= 2):
                        # Either A) it has been requested to not write
                        # scalar coordinate variables; or B) there ARE
                        # auxiliary coordinates, cell measures, domain
                        # ancillaries or field ancillaries which span
                        # this domain axis. Therefore write the
                        # dimension coordinate to the file as a
                        # coordinate variable.
                        ncvar = self._write_dimension_coordinate(
                            f, key, dim_coord)

                        # Expand the field's data array to include
                        # this domain axis
                        f = self.implementation.field_insert_dimension(
                                f, position=0, axis=axis)
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
                # --- End: if

                found_dimension_coordinate = True
                break
            # --- End: for

            if not found_dimension_coordinate:
                # ----------------------------------------------------
                # There is NO dimension coordinate for this axis
                # ----------------------------------------------------
                spanning_constructs = (
                    self.implementation.get_constructs(f, axes=[axis])
                )

                spanning_auxiliary_coordinates = (
                    self.implementation.get_auxiliary_coordinates(
                        f, axes=[axis], exact=True)
                )

                if (axis not in data_axes
                    and spanning_constructs
                    and spanning_constructs != spanning_auxiliary_coordinates):
                    # The data array doesn't span the domain axis but
                    # a cell measure, domain ancillary or field
                    # ancillary does, or an N-d (N>1) auxiliary
                    # coordinate does, so expand the data array to
                    # include it.
                    f = self.implementation.field_insert_dimension(
                            f, position=0, axis=axis)
                    data_axes.append(axis)

#                spanning_constructs = self.implementation.get_constructs(f, axes=[axis])
#
#                if axis not in data_axes and spanning_constructs:
#                    # The data array doesn't span the domain axis but
#                    # an auxiliary coordinate, cell measure, domain
#                    # ancillary or field ancillary does, so expand the
#                    # data array to include it.
#                    f = self.implementation.field_insert_dimension(
#                            f, position=0, axis=axis)
#                    data_axes.append(axis)

                # If the data array (now) spans this domain axis then create a
                # netCDF dimension for it
                if axis in data_axes:
                    axis_size0 = (
                        self.implementation.get_domain_axis_size(f, axis)
                    )

                    use_existing_dimension = False

                    if spanning_constructs:
                        for key, construct in list(
                                spanning_constructs.items()):
                            axes = (
                                self.implementation.get_construct_data_axes(
                                    f, key)
                            )
                            spanning_constructs[key] = (construct,
                                                        axes.index(axis))

                        for b1 in g['xxx']:
                            (ncdim1,  axis_size1),  constructs1 = (
                                list(b1.items())[0]
                            )

                            if axis_size0 != axis_size1:
                                continue

                            constructs1 = constructs1.copy()

                            matched_construct = False

                            for key0, (construct0, index0) in spanning_constructs.items():
#                                matched_construct = False
                                for key1, (construct1, index1) in constructs1.items():
                                    if (index0 == index1 and
                                        self.implementation.equal_constructs(
                                            construct0, construct1)):
                                        del constructs1[key1]
                                        matched_construct = True
                                        break
                                # --- End: for

                                if  matched_construct:
                                    break
                            # --- End: for

#                            if not constructs1:
                            if matched_construct:
                                use_existing_dimension = True
                                break
                        # --- End: for
                    # --- End: if

                    if use_existing_dimension:
                        g['axis_to_ncdim'][axis] = ncdim1
                    elif (g['compression_type'] == 'ragged contiguous'
                          and len(data_axes) == 2
                          and axis == data_axes[1]):
                        # Do not create a netCDF dimension for the
                        # element dimension
                        g['axis_to_ncdim'][axis] = 'ragged_{}'.format(
                            'contiguous_element')
                    elif (g['compression_type'] == 'ragged indexed'
                          and len(data_axes) == 2
                          and axis == data_axes[1]):
                        # Do not create a netCDF dimension for the
                        # element dimension
                        g['axis_to_ncdim'][axis] = 'ragged_{}'.format(
                            'indexed_element')
                    elif (g['compression_type'] == 'ragged indexed contiguous'
                          and len(data_axes) == 3
                          and axis == data_axes[1]):
                        # Do not create a netCDF dimension for the
                        # element dimension
                        g['axis_to_ncdim'][axis] = 'ragged_{}'.format(
                            'indexed_contiguous_element1')
                    elif (g['compression_type'] == 'ragged indexed contiguous'
                          and len(data_axes) == 3
                          and axis == data_axes[2]):
                        # Do not create a netCDF dimension for the
                        # element dimension
                        g['axis_to_ncdim'][axis] = 'ragged_{}'.format(
                            'indexed_contiguous_element2')
                    else:
                        domain_axis = (
                            self.implementation.get_domain_axes(f)[axis]
                        )
                        ncdim = self.implementation.nc_get_dimension(
                            domain_axis, 'dim')
                        ncdim = self._netcdf_name(ncdim)
                        unlimited = self.implementation.nc_is_unlimited_axis(
                            f, axis)
                        self._write_dimension(
                            ncdim, f, axis, unlimited=unlimited)

                        xxx.append({(ncdim, axis_size0): spanning_constructs})
                # --- End: if
            # --- End: if
        # --- End: for

        field_data_axes = tuple(self.implementation.get_field_data_axes(f))
        data_ncdimensions = [g['axis_to_ncdim'][axis]
                             for axis in field_data_axes]

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
                list_variable = self.implementation.get_list(f)
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
                count = self.implementation.get_count(f)
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
                index = self.implementation.get_index(f)
                index_ncdim = self.implementation.nc_get_dimension(
                    index, default='sample')
                sample_ncdim = self._write_index_variable(
                    f, index,
                    sample_dimension=index_ncdim,
                    ncdim=index_ncdim, create_ncdim=True,
                    instance_dimension=data_ncdimensions[0])

            elif compression_type == 'ragged indexed contiguous':
                # ----------------------------------------------------
                # Compression by indexed contigous ragged array
                #
                # Write the index variable to the file, making a note
                # of the netCDF sample dimension.
                # ----------------------------------------------------
                count = self.implementation.get_count(f)
                count_ncdim = self.implementation.nc_get_dimension(
                    count, default='feature')
                sample_ncdim = self._write_count_variable(
                    f, count,
                    ncdim=count_ncdim, create_ncdim=True)

                index_ncdim = count_ncdim
                index = self.implementation.get_index(f)
                self._write_index_variable(
                    f, index,
                    sample_dimension=sample_ncdim,
                    ncdim=index_ncdim, create_ncdim=False,
                    instance_dimension=data_ncdimensions[0])

                g['sample_ncdim'][compressed_ncdims[0:2]] = index_ncdim

            else:
                raise ValueError(
                    "Can't write {!r}: Unknown compression type: {!r}".format(
                        org_f, compression_type))

            g['sample_ncdim'][compressed_ncdims] = sample_ncdim

            n = len(compressed_ncdims)
            sample_dimension = (
                self.implementation.get_sample_dimension_position(f)
            )
#            sample_dimension = [i for i in range(len(field_data_axes)-n+1)
#                                if field_data_axes[i:i+n] == compressed_axes]
#            sample_dimension = sample_dimension[0]

            data_ncdimensions[sample_dimension:sample_dimension + n] = (
                [sample_ncdim]
            )
        # --- End: if

        data_ncdimensions = tuple(data_ncdimensions)

        # ------------------------------------------------------------
        # Create auxiliary coordinate variables, except those which
        # might be completely specified elsewhere by a transformation.
        # ------------------------------------------------------------

        # Initialize the list of 'coordinates' attribute variable
        # values (each of the form 'name')
        for key, aux_coord in sorted(
                self.implementation.get_auxiliary_coordinates(f).items()):
            axes = self.implementation.get_construct_data_axes(f, key)
            if len(axes) > 1 or axes[0] in data_axes:
                # This auxiliary coordinate construct spans at least
                # one of the dimensions of the field constuct's data
                # array.
                coordinates = self._write_auxiliary_coordinate(f, key,
                                                               aux_coord,
                                                               coordinates)
            else:
                # This auxiliary coordinate needs to be written as a
                # scalar coordiante variable
                coordinates = self._write_scalar_coordinate(f, key,
                                                            aux_coord,
                                                            axis,
                                                            coordinates)
        # --- End: for

        # ------------------------------------------------------------
        # Create netCDF variables from domain ancillaries
        # ------------------------------------------------------------
        for key, anc in sorted(
                self.implementation.get_domain_ancillaries(f).items()):
            self._write_domain_ancillary(f, key, anc)

        # ------------------------------------------------------------
        # Create netCDF variables from cell measures
        # ------------------------------------------------------------
        # Set the list of 'cell_measures' attribute values (each of
        # the form 'measure: name')
        cell_measures = [
            self._write_cell_measure(f, key, msr)
            for key, msr in sorted(
                    self.implementation.get_cell_measures(f).items())
        ]

        # ------------------------------------------------------------
        # Create netCDF formula_terms attributes from vertical
        # coordinate references
        # ------------------------------------------------------------
        for ref in g['formula_terms_refs']:
            formula_terms = []
            bounds_formula_terms = []
            owning_coord_key = None

            standard_name = (
                self.implementation.get_coordinate_conversion_parameters(
                    ref).get('standard_name')
            )
            if standard_name is not None:
                c = []
                for key in self.implementation.get_coordinate_reference_coordinates(ref):
                    coord = self.implementation.get_coordinates(f)[key]
                    if self.implementation.get_property(coord, 'standard_name', None) == standard_name:
                        c.append((key, coord))

                if len(c) == 1:
                    owning_coord_key, _ = c[0]
            # --- End: if

            z_axis = self.implementation.get_construct_data_axes(
                f, owning_coord_key)[0]

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

                for term, key in ref.coordinate_conversion.domain_ancillaries().items():  # DCH ALERT
                    if key is None:
                        continue

                    domain_anc = (
                        self.implementation.get_domain_ancillaries(f)[key]
                    )
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
                        if z_axis not in self.implementation.get_construct_data_axes(f, key):
                            bounds = None

                    if bounds is None:
                        bounds_formula_terms.append('{0}: {1}'.format(
                            term, ncvar))
                    else:
                        bounds_formula_terms.append('{0}: {1}'.format(
                            term, bounds))
            # --- End: if

            # Add the formula_terms attribute to the parent coordinate
            # variable
            if formula_terms:
                ncvar = g['key_to_ncvar'][owning_coord_key]
                formula_terms = ' '.join(formula_terms)
                g['nc'][ncvar].setncattr('formula_terms', formula_terms)

                logger.info(
                    "    Writing formula_terms attribute to "
                    "netCDF variable {}: {!r}".format(ncvar, formula_terms)
                )  # pragma: no cover

                # Add the formula_terms attribute to the parent
                # coordinate bounds variable
                bounds_ncvar = g['bounds'].get(ncvar)
                if bounds_ncvar is not None:
                    bounds_formula_terms = ' '.join(bounds_formula_terms)
                    g['nc'][bounds_ncvar].setncattr(
                        'formula_terms', bounds_formula_terms)

                    logger.info(
                        "    Writing formula_terms to netCDF "
                        "bounds variable {}: {!r}".format(
                             bounds_ncvar, bounds_formula_terms)
                    )  # pragma: no cover
            # --- End: if

            # Deal with a vertical datum
            if owning_coord_key is not None:
                self._create_vertical_datum(ref, owning_coord_key)
        # --- End: for

        # ------------------------------------------------------------
        # Create netCDF variables grid mappings
        # ------------------------------------------------------------
        multiple_grid_mappings = (len(g['grid_mapping_refs']) > 1)

        grid_mapping = [self._write_grid_mapping(f, ref,
                                                 multiple_grid_mappings)
                        for ref in g['grid_mapping_refs']]

        # ------------------------------------------------------------
        # Field ancillary variables
        #
        # Create the 'ancillary_variables' CF-netCDF attribute and
        # create the referenced CF-netCDF ancillary variables
        # ------------------------------------------------------------
        ancillary_variables = [
            self._write_field_ancillary(f, key, anc)
            for key, anc in self.implementation.get_field_ancillaries(
                    f).items()
        ]

        # ------------------------------------------------------------
        # Create the CF-netCDF data variable
        # ------------------------------------------------------------
        ncvar = self._create_netcdf_variable_name(f, default='data')

        ncdimensions = data_ncdimensions

        extra = {}

        # Cell measures
        if cell_measures:
            cell_measures = ' '.join(cell_measures)
            logger.info(
                "    Writing cell_measures attribute to "
                "netCDF variable {}: {!r}".format(ncvar, cell_measures)
            )  # pragma: no cover

            extra['cell_measures'] = cell_measures

        # Auxiliary/scalar coordinates
        if coordinates:
            coordinates = ' '.join(coordinates)
            logger.info(
                "    Writing coordinates attribute to "
                "netCDF variable {}: {!r}".format(ncvar, coordinates)
            )  # pragma: no cover

            extra['coordinates'] = coordinates

        # Grid mapping
        if grid_mapping:
            grid_mapping = ' '.join(grid_mapping)
            logger.info(
                "    Writing grid_mapping attribute to "
                "netCDF variable {}: {!r}".format(ncvar, grid_mapping)
            )  # pragma: no cover

            extra['grid_mapping'] = grid_mapping

        # Ancillary variables
        if ancillary_variables:
            ancillary_variables = ' '.join(ancillary_variables)
            logger.info(
                "    Writing ancillary_variables attribute to "
                "netCDF variable {}: {!r}".format(
                    ncvar, ancillary_variables)
            )  # pragma: no cover

            extra['ancillary_variables'] = ancillary_variables

        # name can be a dimension of the variable, a scalar coordinate
        # variable, a valid standard name, or the word 'area'
        cell_methods = self.implementation.get_cell_methods(f)
        if cell_methods:
            axis_map = g['axis_to_ncdim'].copy()
            axis_map.update(g['axis_to_ncscalar'])

            cell_methods_strings = []
            for cm in list(cell_methods.values()):
                if not self.cf_cell_method_qualifiers().issuperset(
                        self.implementation.get_cell_method_qualifiers(cm)):
                    raise ValueError(
                        "Can't write {!r}: Unknown cell method "
                        "property: {!r}".format(
                            org_f, cm.properties()))

                axes = [axis_map.get(axis, axis)
                        for axis in self.implementation.get_cell_method_axes(
                                cm, ())]
                self.implementation.set_cell_method_axes(cm, axes)
                cell_methods_strings.append(
                    self.implementation.get_cell_method_string(cm))

            cell_methods = ' '.join(cell_methods_strings)
            logger.info(
                "    Writing cell_methods attribute to "
                "netCDF variable {}: {}".format(ncvar, cell_methods)
            )  # pragma: no cover

            extra['cell_methods'] = cell_methods

        # ------------------------------------------------------------
        # Geometry container (CF>=1.8)
        # ------------------------------------------------------------
        if g['output_version'] >= g['CF-1.8']:
            geometry_container = self._create_geometry_container(f)
            if geometry_container:
                gc_ncvar = self._write_geometry_container(f,
                                                          geometry_container)
                extra['geometry'] = gc_ncvar
        # --- End: if

        # Create a new CF-netCDF data variable
        self._write_netcdf_variable(ncvar, ncdimensions, f,
                                    omit=g['global_attributes'],
                                    extra=extra, data_variable=True)

        # Update the 'seen' dictionary, if required
        if add_to_seen:
            seen[id_f] = {'variable': org_f,
                          'ncvar': ncvar,
                          'ncdims': ncdimensions}

        if xxx:
            g['xxx'].extend(xxx)

    def _create_vertical_datum(self, ref, coord_key):
        '''Deal with a vertical datum

    .. versionaddedd:: 1.7.0

        '''
        g = self.write_vars

        if not self.implementation.has_datum(ref):
            return

        count = [0, None]
        for grid_mapping in g['grid_mapping_refs']:
            if self.implementation.equal_datums(ref, grid_mapping):
                count = [count[0] + 1, grid_mapping]
                if count[0] > 1:
                    break
        # --- End: for

        if count[0] == 1:
            # Add the vertical coordinate to an existing
            # horizontal coordinate reference
            logger.info(
                '      Adding {!r} to {!r}'.format(coord_key, grid_mapping)
            )  # pragma: no cover

            grid_mapping = count[1]
            self.implementation.set_coordinate_reference_coordinate(
                grid_mapping, coord_key)
        else:
            # Create a new horizontal coordinate reference for the
            # vertical datum
            logger.info(
                "    Creating a new horizontal coordinate reference "
                "for the vertical datum"
            )  # pragma: no cover

            new_grid_mapping = (
                self.implementation.initialise_CoordinateReference()
            )

            self.implementation.set_coordinate_reference_coordinates(
                coordinate_reference=new_grid_mapping,
                coordinates=[coord_key])

            coordinate_conversion = (
                self.implementation.initialise_CoordinateConversion(
                    parameters={'grid_mapping_name': 'latitude_longitude'})
            )
            self.implementation.set_coordinate_conversion(
                coordinate_reference=new_grid_mapping,
                coordinate_conversion=coordinate_conversion)

            datum = self.implementation.get_datum(ref)
            self.implementation.set_datum(
                coordinate_reference=new_grid_mapping,
                datum=datum)

            ncvar = self.implementation.nc_get_variable(datum)
            if ncvar is not None:
                self.implementation.nc_set_variable(new_grid_mapping, ncvar)

            g['grid_mapping_refs'].append(new_grid_mapping)

    def _unlimited(self, field, axis):
        '''Whether an axis is unlimited.

    .. versionadded:: 1.7.0

    :Parameters:

        field: Field construct

        axis: `str`

    :Returns:

        `bool`

        '''
        return self.implementation.nc_is_unlimited_axis(field, axis)

    def _write_global_attributes(self, fields):
        '''Find the netCDF global properties from all of the input fields and
    write them to the netCDF4.Dataset.

    :Parameters:

        fields : `list` of field constructs

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
        global_attributes.update(
            self.cf_description_of_file_contents_attributes())

        # ------------------------------------------------------------
        # Add properties that have been marked as global on each field
        # ------------------------------------------------------------
        force_global = {}
        for f in fields:
            for attr, v in self.implementation.nc_get_global_attributes(
                    f).items():
                if v is None:
                    global_attributes.add(attr)
                else:
                    force_global.setdefault(attr, []).append(v)
        # --- End: for

        if 'Conventions' not in force_global:
            for f in fields:
                v = self.implementation.nc_get_global_attributes(f).get(
                    'Conventions')
                if v is not None:
                    force_global.setdefault('Conventions', []).append(v)
        # --- End: if

        force_global = {attr: v[0] for attr, v in force_global.items()
                        if len(v) == len(fields) and len(set(v)) == 1}

        # File descriptors supercede "forced" global attributes
        for attr in g['file_descriptors']:
            force_global.pop(attr, None)

        # ------------------------------------------------------------
        # Remove attributes that have been specifically requested to
        # not be global attributes.
        # ------------------------------------------------------------
        global_attributes.difference_update(g['variable_attributes'])

        # ------------------------------------------------------------
        # Remove properties listed as file descriptors.
        # ------------------------------------------------------------
        global_attributes.difference_update(g['file_descriptors'])

        # ------------------------------------------------------------
        # Remove attributes that are "forced" global attributes. These
        # are dealt with separately, because they may appear as global
        # and variable attributes.
        # ------------------------------------------------------------
        global_attributes.difference_update(force_global)

        # ------------------------------------------------------------
        # Remove global attributes that have different values for
        # different fields
        # ------------------------------------------------------------
        f0 = fields[0]
        for prop in tuple(global_attributes):
            prop0 = self.implementation.get_property(f0, prop, None)

            if prop0 is None:
                global_attributes.remove(prop)
                continue

            if len(fields) > 1:
                for f in fields[1:]:
                    prop1 = self.implementation.get_property(f, prop, None)
                    if not self.implementation.equal_properties(prop0, prop1):
                        global_attributes.remove(prop)
                        break
        # --- End: for

        # -----------------------------------------------------------
        # Write the Conventions global attribute to the file
        # ------------------------------------------------------------
        delimiter = ' '
        set_Conventions = force_global.pop('Conventions', None)
        if g['Conventions']:
            if isinstance(g['Conventions'], basestring):
                g['Conventions'] = [g['Conventions']]
            else:
                g['Conventions'] = list(g['Conventions'])
        else:
            if set_Conventions is None:
                g['Conventions'] = []
            else:
                if ',' in set_Conventions:
                    g['Conventions'] = split.set_Conventions.split(',')
                else:
                    g['Conventions'] = split.set_Conventions.split()
        # --- End: if

        for i, c in enumerate(g['Conventions'][:]):
            x = re.search('CF-(\d.*)', c)
            if x:
                g['Conventions'].pop(i)
        # --- End: for

        if [x for x in g['Conventions'] if ',' in x]:
            raise ValueError(
                "Conventions names can not contain commas: {0}".format(
                    g['Conventions']))

        g['output_version'] = g['latest_version']
        g['Conventions'] = (
            ['CF-' + str(g['output_version'])] + list(g['Conventions'])
        )

        if [x for x in g['Conventions'] if ' ' in x]:
            # At least one of the conventions contains blanks
            # space, so join them with commas.
            delimiter = ','

        g['netcdf'].setncattr('Conventions', delimiter.join(g['Conventions']))

        # ------------------------------------------------------------
        # Write the file descriptors to the file
        # ------------------------------------------------------------
        for attr, value in g['file_descriptors'].items():
            g['netcdf'].setncattr(attr, value)

        # ------------------------------------------------------------
        # Write other global attributes to the file
        # ------------------------------------------------------------
        for attr in global_attributes - set(('Conventions',)):
            g['netcdf'].setncattr(attr, self.implementation.get_property(
                f0, attr))

        # ------------------------------------------------------------
        # Write "forced" global attributes to the file
        # ------------------------------------------------------------
        for attr, v in force_global.items():
            g['netcdf'].setncattr(attr, v)

        g['global_attributes'] = global_attributes

    def file_close(self, filename):
        '''Close the netCDF file that has been written.

    :Returns:

        `None`

        '''
        self.write_vars['netcdf'].close()

    def file_open(self, filename, mode, fmt, fields):
        '''Open the netCDF file for writing.

    :Parameters:

        filename: `str`
            As for the *filename* parameter for initialising a
            `netCDF.Dataset` instance.

        mode: `str`
            As for the *mode* parameter for initialising a
            `netCDF.Dataset` instance.

        fmt: `str`
            As for the *format* parameter for initialising a
            `netCDF.Dataset` instance.

        fields: sequence of `Field`
            The field constructs to be written.

    :Returns:

        `netCDF.Dataset`
            A `netCDF4.Dataset` object for the file.

        '''
        if fields:
            filename = os.path.abspath(filename)
            for f in fields:
                if filename in self.implementation.get_filenames(f):
                    raise ValueError(
                        "Can't write to a file that contains data "
                        "that needs to be read: {}".format(filename))
        # --- End: if

        if self.write_vars['overwrite']:
            os.remove(filename)

        try:
            nc = netCDF4.Dataset(filename, mode, format=fmt)
        except RuntimeError as error:
            raise RuntimeError("{}: {}".format(error, filename))

        return nc

    @_manage_log_level_via_verbosity
    def write(self, fields, filename, fmt='NETCDF4', overwrite=True,
              global_attributes=None, variable_attributes=None,
              file_descriptors=None, external=None, Conventions=None,
              datatype=None, least_significant_digit=None,
              endian='native', compress=0, fletcher32=False,
              shuffle=True, scalar=True, string=True,
              extra_write_vars=None, verbose=None,
              warn_valid=True):
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

    .. versionadded:: 1.7.0

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

            ==========================  =================================================
            *fmt*                       Description
            ==========================  =================================================
            ``'NETCDF4'``               Output to a CF-netCDF4 format file
            ``'NETCDF4_CLASSIC'``       Output to a CF-netCDF4 classic format file
            ``'NETCDF3_CLASSIC'``       Output to a CF-netCDF3 classic format file
            ``'NETCDF3_64BIT'``         Output to a CF-netCDF3 64-bit offset format file
            ``'NETCDF3_64BIT_OFFSET'``  NetCDF3 64-bit offset format file
            ``'NETCDF3_64BIT'``         An alias for ``'NETCDF3_64BIT_OFFSET'``
            ``'NETCDF3_64BIT_DATA'``    NetCDF3 64-bit offset format file with extensions
            ==========================  =================================================

            By default the *fmt* is ``'NETCDF4'``. Note that the
            netCDF3 formats may be slower than netCDF4 options.

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
            with the exception of Booleans (``numpy.dtype(bool)``, which
            are converted to 32 bit integers.

            *Parameter example:*
              To convert 64 bit floats and integers to their 32 bit
              counterparts: ``dtype={numpy.dtype(float):
              numpy.dtype('float32'), numpy.dtype(int):
              numpy.dtype('int32')}``.

        Conventions: (sequence of) `str`, optional
             Specify conventions to be recorded by the netCDF global
             "Conventions" attribute. These conventions are in addition to
             version of CF being used e.g. ``'CF-1.7'``, which must not be
             specified. If the "Conventions" property is set on a field
             construct then it is ignored. Note that a convention name is
             not allowed to contain any commas.

             *Parameter example:*
               ``Conventions='UGRID-1.0'``

             *Parameter example:*
               ``Conventions=['UGRID-1.0']``

             *Parameter example:*
               ``Conventions=['CMIP-6.2', 'UGRID-1.0']``

             *Parameter example:*
               ``Conventions='CF-1.7'``

             *Parameter example:*
               ``Conventions=['CF-1.7', 'CMIP-6.2']``

        string: `bool`, optional
           By default string-valued construct data are written as
           netCDF arrays of type string if the output file format is
           ``'NETCDF4'``, or of type char with an extra dimension
           denoting the maximum string length for any other output
           file format (see the *fmt* parameter). If *string* is False
           then string-valued construct data are written as netCDF
           arrays of type char with an extra dimension denoting the
           maximum string length, regardless of the selected output
           file format.

        warn_valid: `bool`, optional
            If False then do not warn for when writing "out of range"
            data, as defined by the presence of ``valid_min``,
            ``valid_max`` or ``valid_range`` properties on field or
            metadata constructs that have data. By default a warning
            is printed if any such construct has any of these
            properties.

            *Parameter example:*
              If a field construct has ``valid_max`` property with
              value ``100`` and data with maximum value ``999``, then
              a warning will be printed if ``warn_valid=True``.

            .. versionadded:: 1.8.3

    :Returns:

        `None`

    **Examples:**

    >>> f
    [<CF Field: air_pressure(30, 24)>,
     <CF Field: u_compnt_of_wind(19, 29, 24)>,
     <CF Field: v_compnt_of_wind(19, 29, 24)>,
     <CF Field: potential_temperature(19, 30, 24)>]
    >>> write(f, 'file')

    >>> type(f)
    <class 'cf.field.FieldList'>
    >>> cf.write([f, g], 'file.nc', verbose=3)
    [<CF Field: air_pressure(30, 24)>,
     <CF Field: u_compnt_of_wind(19, 29, 24)>,
     <CF Field: v_compnt_of_wind(19, 29, 24)>,
     <CF Field: potential_temperature(19, 30, 24)>]

        '''
        logger.info('Writing to {}'.format(fmt))  # pragma: no cover

        # ------------------------------------------------------------
        # Initialise netCDF write parameters
        # ------------------------------------------------------------
        self.write_vars = {
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
            'variable_attributes': set(),
            'global_attributes'  : set(),
            'file_descriptors'   : {},

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

            # Whether or not to write string data-types to netCDF4
            # files (as opposed to car data-types).
            'string': string,

            # Print statements
            'verbose': False,

            # Conventions
            'Conventions': Conventions,

            'xxx': [],

            'count_variable_sample_dimension': {},
            'index_variable_sample_dimension': {},

            'external_variables': '',
            'external_fields'   : [],

            'geometry_containers': {},
            'geometry_encoding'  : {},

            'dimensions_with_role': {},

            'latest_version': LooseVersion(
                self.implementation.get_cf_version()),
            'version': {},

            # Warn for the presence of out-of-range data with of
            # valid_[min|max|range] attributes?
            'warn_valid': bool(warn_valid),
            'valid_properties': set(('valid_min', 'valid_max', 'valid_range')),
        }
        g = self.write_vars

        # ------------------------------------------------------------
        # Set possible versions
        # ------------------------------------------------------------
        for version in ('1.6', '1.7', '1.8', '1.9'):
            g['CF-' + version] = LooseVersion(version)

        if extra_write_vars:
            g.update(copy.deepcopy(extra_write_vars))

        compress = int(compress)
        zlib = bool(compress)

        if fmt not in ('NETCDF3_CLASSIC', 'NETCDF3_64BIT',
                       'NETCDF4', 'NETCDF4_CLASSIC',
                       'NETCDF3_64BIT_OFFSET', 'NETCDF3_64BIT_DATA'):
            raise ValueError("Unknown output file format: {}".format(fmt))

        if compress and fmt in ('NETCDF3_CLASSIC', 'NETCDF3_64BIT',
                                'NETCDF3_64BIT_OFFSET', 'NETCDF3_64BIT_DATA'):
            raise ValueError("Can't compress {} format file".format(fmt))

        # ------------------------------------------------------------
        # Set up global/non-global attributes
        # ------------------------------------------------------------
        if variable_attributes:
            if isinstance(variable_attributes, basestring):
                variable_attributes = set((variable_attributes,))
            else:
                variable_attributes = set(variable_attributes)

            g['variable_attributes'] = variable_attributes

            if 'Conventions' in variable_attributes:
                raise ValueError(
                    "Can't prevent the 'Conventions' property from being "
                    "a netCDF global variable: {0}".format(
                        variable_attributes))

        if global_attributes:
            if isinstance(global_attributes, basestring):
                global_attributes = set((global_attributes,))
            else:
                global_attributes = set(global_attributes)

            g['global_attributes'] = global_attributes

        if file_descriptors:
            if 'Conventions' in file_descriptors:
                raise ValueError(
                    "Use the Conventions parameter to specify conventions, "
                    "rather than a file descriptor.")

            g['file_descriptors'] = file_descriptors

        # ------------------------------------------------------------
        # Set up data type conversions. By default, Booleans are
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

        g['fmt'] = fmt

        if isinstance(fields, self.implementation.get_class('Field')):
            fields = (fields,)
        else:
            try:
                fields = tuple(fields)
            except TypeError:
                raise TypeError("'fields' parameter must be a (sequence of) "
                                "Field instances")

        # ------------------------------------------------------------
        # Scalar coordinate variables
        # ------------------------------------------------------------
        g['scalar'] = scalar

        g['overwrite'] = overwrite

        # ------------------------------------------------------------
        # Still here? Open the output netCDF file.
        # ------------------------------------------------------------
        filename = os.path.expanduser(os.path.expandvars(filename))
        if os.path.isfile(filename):
            if not overwrite:
                raise IOError(
                    "Can't write to an existing file unless "
                    "overwrite=True: {}".format(
                        os.path.abspath(filename)))

            if not os.access(filename, os.W_OK):
                raise IOError(
                    "Can't overwrite an existing file without "
                    "permission: {}".format(
                        os.path.abspath(filename)))
        else:
            g['overwrite'] = False

        # ------------------------------------------------------------
        # Open the netCDF file to be written
        # ------------------------------------------------------------
        mode = 'w'
        g['filename'] = filename
        g['netcdf'] = self.file_open(filename, mode, fmt, fields)

#        # -----------------------------------------------------------
#        # Set the fill mode for a Dataset open for writing to
#        off. This # will prevent the data from being pre-filled with
#        fill values, # which may result in some performance
#        improvements.  #
#        -------------------------------------------------------------
#        g['netcdf'].set_fill_off()

        # ------------------------------------------------------------
        # Write global properties to the file first. This is important
        # as doing it later could slow things down enormously. This
        # function also creates the g['global_attributes'] set, which
        # is used in the _write_field function.
        # ------------------------------------------------------------
        self._write_global_attributes(fields)

        if external is not None:
            if g['output_version'] < g['CF-1.7']:
                raise ValueError(
                    "Can't create external variables at CF-{} "
                    "(version too old)".format(
                        g['output_version']))

            external = os.path.expanduser(os.path.expandvars(external))
            if os.path.realpath(external) == os.path.realpath(filename):
                raise ValueError("Can't set filename and external to the "
                                 "same path")
        # --- End: if
        g['external_file'] = external

        # ------------------------------------------------------------
        # Write each field construct
        # ------------------------------------------------------------
        for f in fields:
            self._write_field(f)

        # ------------------------------------------------------------
        # Write all of the buffered data to disk
        # ------------------------------------------------------------
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
                       endian=endian,
                       compress=compress,
                       fletcher32=fletcher32,
                       shuffle=shuffle,
                       verbose=verbose,
                       extra_write_vars=extra_write_vars)

# --- End: class
