import abc

_MUST_IMPLEMENT = 'This method must be implemented'


class ConstructAccess(object):
    '''Mixin class for manipulating a `Constructs` object.

    '''
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def _get_constructs(self, *default):
        '''Return the `Constructs` object

:Examples 1:

>>> c = f._get_constructs()

:Parameters:

    default: optional
        If set then return *default* if there is no `Constructs` object.
:Returns:

    out:
        The `Constructs` object. If unset then return *default* if provided.

:Examples 2:

>>> c = f._get_constructs(None)

        '''
        raise NotImplementedError(_MUST_IMPLEMENT)
    #--- End: def
    
    def array_constructs(self, copy=False):
        return self._get_constructs().array_constructs(copy=copy)
    
    def auxiliary_coordinates(self, copy=False):
        return self._get_constructs().constructs(construct_type='auxiliary_coordinate',
                                                 copy=copy)
    
    def cell_measures(self, copy=False):
        return self._get_constructs().constructs(construct_type='cell_measure',
                                                 copy=copy)
    
    def construct_axes(self, key=None):
        return self._get_constructs().construct_axes(key=key)
    
    def construct_type(self, key):
        return self._get_constructs().construct_type(key)
       
    def constructs(self, copy=False):
        '''
        '''
        return self._get_constructs().constructs(copy=copy)
    #--- End: def
    
    def coordinate_references(self, copy=False):
        return self._get_constructs().constructs(construct_type='coordinate_reference',
                                                 copy=copy)
    
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
        return self._get_constructs().constructs(construct_type='dimension_coordinate',
                                                 copy=copy)
    
    def domain_ancillaries(self, copy=False):
        return self._get_constructs().constructs(construct_type='domain_ancillary',
                                                 copy=copy)
    
    def domain_axes(self, copy=False):
        return self._get_constructs().constructs(construct_type='domain_axis',
                                                 copy=copy)
    
    def domain_axis_name(self, axis):
        '''
        '''
        return self._get_constructs().domain_axis_name(axis)
    #--- End: for
    
    @abc.abstractmethod
    def del_construct(self, key):
        '''
        '''
        pass
    #--- End: def

    def set_auxiliary_coordinate(self, item, key=None, axes=None,
                                 copy=True, replace=True):
        '''Insert an auxiliary coordinate construct.
        '''
        if not replace and key in self.auxiliary_coordinates():
            raise ValueError(
"Can't insert auxiliary coordinate construct: Identifier {!r} already exists".format(key))

        return self.set_construct('auxiliary_coordinate', item,
                                  key=key, axes=axes, copy=copy)
    #--- End: def

    def set_domain_axis(self, domain_axis, key=None, replace=True, copy=True):
        '''Insert a domain axis construct.
        '''
        axes = self.domain_axes()
        if not replace and key in axes and axes[key].size != domain_axis.size:
            raise ValueError(
"Can't insert domain axis: Existing domain axis {!r} has different size (got {}, expected {})".format(
    key, domain_axis.size, axes[key].size))

        return self.set_construct('domain_axis',
                                  domain_axis, key=key, copy=copy)
    #--- End: def

    def set_domain_ancillary(self, item, key=None, axes=None,
                             extra_axes=0, copy=True, replace=True):
        '''Insert a domain ancillary construct.
        '''       
        if not replace and key in self.domain_ancillaries():
            raise ValueError(
"Can't insert domain ancillary construct: Identifier {0!r} already exists".format(key))

        return self.set_construct('domain_ancillary', item, key=key,
                                  axes=axes, extra_axes=extra_axes,
                                  copy=copy)
    #--- End: def

    def set_construct(self, construct_type, construct, key=None,
                      axes=None, extra_axes=0, replace=True,
                      copy=True):
        '''Insert a construct.
        '''
        return self._get_constructs().set_construct(construct_type,
                                                    construct,
                                                    key=key,
                                                    axes=axes,
                                                    extra_axes=extra_axes,
                                                    replace=replace,
                                                    copy=copy)
    #--- End: def

    def set_construct_axes(self, key, axes):
        '''
        '''
        return self._get_constructs().set_construct_axes(key, axes)
    #--- End: def

    def set_cell_measure(self, item, key=None, axes=None, copy=True, replace=True):
        '''
        '''
        if not replace and key in self.cell_measures():
            raise ValueError(
"Can't insert cell measure construct: Identifier {0!r} already exists".format(key))

        return self.set_construct('cell_measure', item, key=key,
                                  axes=axes, copy=copy)
    #--- End: def

    def set_coordinate_reference(self, item, key=None, axes=None,
                                    copy=True, replace=True):
        '''
        '''
        return self.set_construct('coordinate_reference',
                                  item, key=key, copy=copy)
    #--- End: def

    def set_dimension_coordinate(self, item, key=None, axes=None, copy=True, replace=True):
        '''
        '''
        if not replace and key in self.dimension_coordinates():
            raise ValueError(
"Can't insert dimension coordinate construct: Identifier {!r} already exists".format(key))

        return self.set_construct('dimension_coordinate',
                                  item, key=key, axes=axes, copy=copy)
    #--- End: def

#--- End: class
