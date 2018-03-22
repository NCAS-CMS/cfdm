import abc


# ====================================================================
#
# 
#
# ====================================================================

class DomainConstructMethods(object):
    '''
    '''
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def _get_constructs(self, *default):
        '''
.. versionadded:: 1.6
        
        '''
        pass #        return self._get_component(3, 'constructs', None, *default)
    #--- End: def
    
    def array_constructs(self, copy=False, ignore=()):
        return self._get_constructs().array_constructs(copy=copy, ignore=ignore)
    
    def auxiliary_coordinates(self, copy=False):
        return self._get_constructs().constructs('auxiliary_coordinate', copy=copy)
    
    def cell_measures(self, copy=False):
        return self._get_constructs().constructs('cell_measure', copy=copy)
    
#    def cell_methods(self, copy=False):
#        return self._get_constructs().constructs('cell_method', copy=copy)
    
    def construct_axes(self, key=None):
        return self._get_constructs().construct_axes(key=key)
    
    def construct_type(self, key):
        return self._get_constructs().construct_type(key)
       
    def constructs(self, copy=False):
        '''Return all of the data model constructs of the field.

.. versionadded:: 1.6

.. seealso:: `dump`

:Examples 1:

>>> f.{+name}()

:Returns:

    out: `list`
        The objects correposnding CF data model constructs.

:Examples 2:

>>> f.constructs()
[<DomainAxis: 96>,
 <DomainAxis: 1>,
 <DomainAxis: 15>,
 <DomainAxis: 72>,
 <CellMethod: dim3: mean>,
 <DimensionCoordinate: longitude(96) degrees_east>,
 <DimensionCoordinate: time(1) 360_day>,
 <DimensionCoordinate: air_pressure(15) hPa>,
 <DimensionCoordinate: latitude(72) degrees_north>]

        '''
        return self._get_constructs().constructs(copy=copy)
    #--- End: def
    
    def coordinate_references(self, copy=False):
        return self._get_constructs().constructs('coordinate_reference', copy=copy)
    
    def coordinates(self, copy=False):
        '''
        '''
        out = self.dimension_coordinates(copy=copy)
        out.update(self.auxiliary_coordinates(copy=copy))
        return out
    #--- End: def

    def get_construct(self, key, *default):
        '''
        '''
        return self._get_constructs().get_construct(key, *default)
    #--- End: def

    def dimension_coordinates(self, copy=False):
        return self._get_constructs().constructs('dimension_coordinate', copy=copy)
    
    def domain_ancillaries(self, copy=False):
        return self._get_constructs().constructs('domain_ancillary', copy=copy)
    
    def domain_axes(self, copy=False):
        return self._get_constructs().domain_axes(copy=copy)
    
    def domain_axis_name(self, axis):
        '''
        '''
        return self._get_constructs().domain_axis_name(axis)
    #--- End: for
    
#    def field_ancillaries(self, copy=False):
#        return self._get_constructs().constructs('field_ancillary', copy=copy)

    @abc.abstractmethod
    def del_construct(self, key):
        '''
        '''
        constructs = self._get_constructs()
        
#        if key in constructs.domain_axes():
#            # Remove a domain axis
#            domain_axis = True
#            
#            for k, value in self.construct_axes().iteritems():
#                if key in value:
#                    raise ValueError(
#"Can't remove domain axis that is spanned by {}: {!r}".format(
#    k, self.get_construct(k)))##
#
#        else:
#            domain_axis = False
#
#        if domain_axis:

#        # Remove reference to removed domain axis construct in
#        # cell method constructs
#        for cm_key, cm in self.cell_methods().iteritems():
#            axes = cm.get_axes()
#            if key not in axes:
#                continue
#            
#            axes = list(axes)
#            axes.remove(key)
#                cm.set_axes(axes)
#        else:

        # Remove reference to removed construct in coordinate
        # reference constructs
        for ref in self.coordinate_references().itervalues():
            for term, value in ref.domain_ancillaries().iteritems():
                if key == value:
                    ref.set_domain_ancillary(term, None)
                    
            for coord_key in ref.coordinates():
                if key == coord_key:
                    ref.del_coordinate(coord_key)
                    break
        #--- End: for
        
        return constructs.del_construct(key)
    #--- End: def

    def set_auxiliary_coordinate(self, item, key=None, axes=None,
                                 copy=True, replace=True):
        '''Insert an auxiliary coordinate object into the {+variable}.

.. seealso:: `set_domain_axis`, `set_measure`, `set_data`,
             `set_dim`, `set_ref`

:Parameters:

    item: `AuxiliaryCoordinate`
        The new auxiliary coordinate object. If it is not already a
        auxiliary coordinate object then it will be converted to one.

    key: `str`, optional
        The identifier for the *item*. By default a new, unique
        identifier will be generated.

    axes: sequence of `str`, optional
        The ordered list of axes for the *item*. Each axis is given by
        its identifier. By default the axes are assumed to be
        ``'dim0'`` up to ``'dimM-1'``, where ``M-1`` is the number of
        axes spanned by the *item*.

    {+copy_item_in}
      
    replace: `bool`, optional
        If False then do not replace an existing auxiliary coordinate
        object of domain which has the same identifier. By default an
        existing auxiliary coordinate object with the same identifier
        is replaced with *item*.
    
:Returns:

    out: `str`
        The identifier for the inserted *item*.

:Examples:

>>>

        '''
        if not replace and key in self.auxiliary_coordinates():
            raise ValueError(
"Can't insert auxiliary coordinate object: Identifier {!r} already exists".format(key))

        return self.set_construct('auxiliary_coordinate', item,
                                  key=key, axes=axes, copy=copy)
    #--- End: def

#    def set_cell_method(self, cell_method, key=None, copy=True):
#        '''Insert cell method objects into the {+variable}.
#
#.. seealso:: `set_aux`, `set_measure`, `set_ref`,
#             `set_data`, `set_dim`
#
#:Parameters:
#
#    cell_method: `CellMethod`
#
#:Returns:
#
#    `None`
#
#:Examples:
#
#        '''
#        self.set_construct('cell_method', cell_method, key=key,
#                           copy=copy)
#    #--- End: def

    def set_domain_axis(self, domain_axis, key=None, replace=True, copy=True):
        '''Insert a domain axis into the {+variable}.

.. seealso:: `set_aux`, `set_measure`, `set_ref`,
             `set_data`, `set_dim`

:Parameters:

    axis: `DomainAxis`
        The new domain axis.

    key: `str`, optional
        The identifier for the new axis. By default a new,
        unique identifier is generated.
  
    replace: `bool`, optional
        If False then do not replace an existing axis with the same
        identifier but a different size. By default an existing axis
        with the same identifier is changed to have the new size.

:Returns:

    out: `str`
        The identifier of the new domain axis.


:Examples:

>>> f.set_domain_axis(DomainAxis(1))
>>> f.set_domain_axis(DomainAxis(90), key='dim4')
>>> f.set_domain_axis(DomainAxis(23), key='dim0', replace=False)

        '''
        axes = self.domain_axes()
        if not replace and key in axes and axes[key].size != domain_axis.size:
            raise ValueError(
"Can't insert domain axis: Existing domain axis {!r} has different size (got {}, expected {})".format(
    key, domain_axis.size, axes[key].size))

        return self.set_construct('domain_axis',
                                  domain_axis, key=key, copy=copy)
    #--- End: def

#    def set_field_ancillary(self, construct, key=None, axes=None,
#                            copy=True, replace=False):
#        '''Insert a field ancillary object into the {+variable}.
#        
#    {+copy_item_in}
#      
#        '''
#        if replace:
#            if key is None:
#                raise ValueError("Must specify which construct to replace")
#
#            return self._get_constructs().replace(construct, key, axes=axes,
#                                                 copy=copy)
#        #--- End: if
#        
#        return self.set_construct('field_ancillary', construct,
#                                  key=key, axes=axes,
#                                  copy=copy)
#    #--- End: def

    def set_domain_ancillary(self, item, key=None, axes=None,
                                copy=True, replace=True):
        '''Insert a domain ancillary object into the {+variable}.
      
    {+copy_item_in}
        '''       
        if not replace and key in self.domain_ancillaries():
            raise ValueError(
"Can't insert domain ancillary object: Identifier {0!r} already exists".format(key))

        return self.set_construct('domain_ancillary', item, key=key,
                                  axes=axes,
                                  copy=copy)
    #--- End: def

    def set_construct(self, construct_type, construct, key=None, axes=None,
                      copy=True):
        '''
        '''
        return self._get_constructs().set_construct(construct_type,
                                                    construct,
                                                    key=key,
                                                    axes=axes,
                                                    copy=copy)
    #--- End: def

    def set_construct_axes(self, key, axes):
        '''
        '''
        return self._get_constructs().set_construct_axes(key, axes)
    #--- End: def

    def set_cell_measure(self, item, key=None, axes=None, copy=True, replace=True):
        '''Insert a cell measure object into the {+variable}.

.. seealso:: `set_domain_axis`, `set_aux`, `set_data`,
             `set_dim`, `set_ref`

:Parameters:

    item: `CellMeasure`
        The new cell measure object.

    key: `str`, optional
        The identifier for the *item*. By default a new, unique
        identifier will be generated.

    axes: sequence of `str`, optional
        The ordered list of axes for the *item*. Each axis is given by
        its identifier. By default the axes are assumed to be
        ``'dim0'`` up to ``'dimM-1'``, where ``M-1`` is the number of
        axes spanned by the *item*.

    {+copy_item_in}
      
    replace: `bool`, optional
        If False then do not replace an existing cell measure object
        of domain which has the same identifier. By default an
        existing cell measure object with the same identifier is
        replaced with *item*.
    
:Returns:

    out: 
        The identifier for the *item*.

:Examples:

>>>

        '''
        if not replace and key in self.cell_measures():
            raise ValueError(
"Can't insert cell measure object: Identifier {0!r} already exists".format(key))

        return self.set_construct('cell_measure', item, key=key,
                                  axes=axes, copy=copy)
    #--- End: def

    def set_coordinate_reference(self, item, key=None, axes=None,
                                    copy=True, replace=True):
        '''Insert a coordinate reference object into the {+variable}.

.. seealso:: `set_domain_axis`, `set_aux`, `set_measure`,
             `set_data`, `set_dim`
             
:Parameters:

    item: `CoordinateReference`
        The new coordinate reference object.

    key: `str`, optional
        The identifier for the *item*. By default a new, unique
        identifier will be generated.

    axes: *optional*
        *Ignored*

    {+copy_item_in}

    replace: `bool`, optional
        If False then do not replace an existing coordinate reference object of
        domain which has the same identifier. By default an existing
        coordinate reference object with the same identifier is replaced with
        *item*.
    
:Returns:

    out: 
        The identifier for the *item*.


:Examples:

>>>

        '''
        return self.set_construct('coordinate_reference',
                                  item, key=key, copy=copy)
    #--- End: def

    def set_dimension_coordinate(self, item, key=None, axes=None, copy=True, replace=True):
        '''Insert a dimension coordinate object into the {+variable}.

.. seealso:: `set_aux`, `set_domain_axis`, `set_item`,
             `set_measure`, `set_data`, `set_ref`,
             `remove_item`

:Parameters:

    item: `DimensionCoordinate` or `cf.Coordinate` or `cf.AuxiliaryCoordinate`
        The new dimension coordinate object. If it is not already a
        dimension coordinate object then it will be converted to one.

    axes: sequence of `str`, optional
        The axis for the *item*. The axis is given by its domain
        identifier. By default the axis will be the same as the given
        by the *key* parameter.

    key: `str`, optional
        The identifier for the *item*. By default a new, unique
        identifier will be generated.

    {+copy_item_in}

    replace: `bool`, optional
        If False then do not replace an existing dimension coordinate
        object of domain which has the same identifier. By default an
        existing dimension coordinate object with the same identifier
        is replaced with *item*.
    
:Returns:

    out: 
        The identifier for the inserted *item*.

:Examples:

>>>

        '''
        if not replace and key in self.dimension_coordinates():
            raise ValueError(
"Can't insert dimension coordinate object: Identifier {!r} already exists".format(key))

        return self.set_construct('dimension_coordinate',
                                  item, key=key, axes=axes, copy=copy)
    #--- End: def

#--- End: class


class ConstructAccess(object):
    '''
    '''
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def _get_constructs(self, *default):
        '''
.. versionadded:: 1.6
        
        '''
        pass #        return self._get_component(3, 'constructs', None, *default)
    #--- End: def
    
    def array_constructs(self, copy=False, ignore=())
        return self._get_constructs().array_constructs(copy=copy, ignore=ignore)
    
    def construct_axes(self, key=None):
        return self._get_constructs().construct_axes(key=key)
    
    def construct_type(self, key):
        return self._get_constructs().construct_type(key)
       
    def constructs(self, copy=False):
        '''Return all of the data model constructs of the field.

.. versionadded:: 1.6

.. seealso:: `dump`

:Examples 1:

>>> f.{+name}()

:Returns:

    out: `list`
        The objects correposnding CF data model constructs.

:Examples 2:

>>> f.constructs()
[<DomainAxis: 96>,
 <DomainAxis: 1>,

<DomainAxis: 15>,
 <DomainAxis: 72>,
 <CellMethod: dim3: mean>,
 <DimensionCoordinate: longitude(96) degrees_east>,
 <DimensionCoordinate: time(1) 360_day>,
 <DimensionCoordinate: air_pressure(15) hPa>,
 <DimensionCoordinate: latitude(72) degrees_north>]

        '''
        return self._get_constructs().constructs(copy=copy)
    #--- End: def

    def get_construct(self, key, *default):
        '''
        '''
        return self._get_constructs().get_construct(key, *default)
    #--- End: def

    @abc.abstractmethod
    def del_construct(self, key):
        '''
        '''
        constructs = self._get_constructs()
        
#        if key in constructs.domain_axes():
#            # Remove a domain axis
#            domain_axis = True
#            
#            for k, value in self.construct_axes().iteritems():
#                if key in value:
#                    raise ValueError(
#"Can't remove domain axis that is spanned by {}: {!r}".format(
#    k, self.get_construct(k)))##
#
#        else:
#            domain_axis = False
#
#        if domain_axis:

#        # Remove reference to removed domain axis construct in
#        # cell method constructs
#        for cm_key, cm in self.cell_methods().iteritems():
#            axes = cm.get_axes()
#            if key not in axes:
#                continue
#            
#            axes = list(axes)
#            axes.remove(key)
#                cm.set_axes(axes)
#        else:

        # Remove reference to removed construct in coordinate
        # reference constructs
        for ref in self.coordinate_references().itervalues():
            for term, value in ref.domain_ancillaries().iteritems():
                if key == value:
                    ref.set_domain_ancillary(term, None)
                    
            for coord_key in ref.coordinates():
                if key == coord_key:
                    ref.del_coordinate(coord_key)
                    break
        #--- End: for
        
        return constructs.del_construct(key)
    #--- End: def

    def set_construct(self, construct_type, construct, key=None, axes=None,
                      copy=True):
        '''
        '''
        return self._get_constructs().set_construct(construct_type,
                                                    construct,
                                                    key=key,
                                                    axes=axes,
                                                    copy=copy)
    #--- End: def

    def set_construct_axes(self, key, axes):
        '''
        '''
        return self._get_constructs().set_construct_axes(key, axes)
    #--- End: def
#--- End: class
