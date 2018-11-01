from builtins import object

import re


class ConstructAccess(object):
    '''Mixin class for manipulating constructs stored in a `Constructs`
object.

    '''

    def _unique_construct_names(self):
        '''TODO 

        '''    
        key_to_name = {}
        name_to_keys = {}


        for d in self._get_constructs()._constructs.values():
            name_to_keys = {}
        
            for key, construct in d.items():
                name = construct.name(default='cfdm%'+key)
                name_to_keys.setdefault(name, []).append(key)
                key_to_name[key] = name
    
            for name, keys in name_to_keys.items():
                if len(keys) <= 1:
                    continue
                
                for key in keys:
                    key_to_name[key] = '{0}{{{1}}}'.format(
                        name,
                        re.findall('\d+$', key)[0])
        #--- End: for
        
        return key_to_name
    #--- End: def
    
    def _unique_domain_axis_names(self):
        '''TODO 
        '''
        key_to_name = {}
        name_to_keys = {}

        for key, value in self.domain_axes().items():
            name_size = (self.domain_axis_name(key), value.get_size(''))
            name_to_keys.setdefault(name_size, []).append(key)
            key_to_name[key] = name_size

        for (name, size), keys in name_to_keys.items():
            if len(keys) == 1:
                key_to_name[keys[0]] = '{0}({1})'.format(name, size)
            else:
                for key in keys:                    
                    key_to_name[key] = '{0}{{{1}}}({2})'.format(name,
                                                                re.findall('\d+$', key)[0],
                                                                size)
        #--- End: for
        
        return key_to_name
    #--- End: def
    
    def coordinate_references(self, copy=False):
        '''Return coordinate reference constructs.

.. versionadded:: 1.7

.. seealso:: `constructs`, `get_construct`

:Parameters:

    copy: `bool`, optional
        If `True` then deep copies of the constructs are returned.


:Returns:

    out: `dict`
        TODO

**Examples**

TODO
>>> f.coordinate_references()
{}
        '''
        return self._get_constructs().constructs(
            construct_type='coordinate_reference', copy=copy)
    #--- End: def

    def coordinates(self, axes=None, copy=False):
        '''Return dimension and auxiliary coordinate constructs.

.. versionadded:: 1.7

.. seealso:: `constructs`, `get_construct`

:Parameters:

    axes: sequence of `str`, optional
        TODO

    copy: `bool`, optional
        If `True` then deep copies of the constructs are returned.

:Returns:

    out: `dict`
        TODO

**Examples**

TODO
>>> f.coordinates()
{}
        '''
        out = self.dimension_coordinates(axes=axes, copy=copy)
        out.update(self.auxiliary_coordinates(axes=axes, copy=copy))
        return out
    #--- End: def

    def domain_ancillaries(self, axes=None, copy=False):
        '''Return domain ancillary constructs.

.. versionadded:: 1.7

.. seealso:: `constructs`, `get_construct`

:Parameters:

    axes: sequence of `str`, optional
        TODO

    copy: `bool`, optional
        If `True` then deep copies of the constructs are returned.

:Returns:

    out: `dict`
        TODO

**Examples**

TODO
>>> f.domain_ancillaries()
{}
        '''
        return self._get_constructs().constructs(
            construct_type='domain_ancillary', axes=axes, copy=copy)
    #--- End: def
    
    def cell_measures(self, axes=None, copy=False):
        '''Return cell measure constructs.

.. versionadded:: 1.7

.. seealso:: `constructs`, `get_construct`

:Parameters:

    axes: sequence of `str`, optional
        TODO

    copy: `bool`, optional
        If `True` then deep copies of the constructs are returned.

:Returns:

    out: `dict`
        TODO

**Examples**

TODO
>>> f.cell_measure()
{}
        '''
        return self._get_constructs().constructs(
            construct_type='cell_measure', axes=axes, copy=copy)
    #--- End: def
    
    def get_construct(self, description=None, id=None, axes=None,
                      construct_type=None, copy=False):
        '''TODO 
        '''
        return self._get_constructs().get_construct(
            description=description, id=id,
            construct_type=construct_type,
            axes=axes,
            copy=copy)
    #--- End: def

    def constructs(self, description=None, id=None, axes=None,
                   construct_type=None, copy=False):
        '''Return the metadata constructs

Constructs are returned as values of a dictionary, keyed by unique
internal identifiers.

By default all constructs are returned, but a subset may be selected
via the optional parameters. If multiple parameters are specified,
then the constructs that satisfy all of the criteria are returned.

.. versionadded:: 1.7

.. seealso:: `del_construct`, `get_construct`, `set_construct`

:Parameters:

    description: `str`, optional
        Return only the constructs which have the given property, or
        other attribute, value.

        The description may be one of:

        * The value of the standard name property on its own. 

            *Example:*
              ``description='air_pressure'`` will return constructs
              that that have a "standard_name" property with the value
              "air_pressure".

        * The value of any property prefixed by the property name and
          a colon. 

            *Example:*
              ``description='positive:up'`` will return constructs
              that that have a "positive" property with the value
              "up".

            *Example:*
              ``description='foo:bar'`` will return constructs
              that that have a "foo" property with the value
              "bar".

            *Example:*
              ``description='standard_name:air_pressure'`` will return
              constructs that that have a "standard_name" property
              with the value "air_pressure".

        * The measure of a cell measure constructs, prefixed by
          "measure%"

            *Example:*
              ``description='measure%area'`` will return area cell
              measure constructs.

        * The netCDF variable name, prefixed by "ncvar%"

            *Example:*
              ``description='ncvar%lat'`` will return constructs with
              netCDF variable name "lat".

        * The netCDF dimension name, prefixed by "ncdim%"

            *Example:*
              ``description='ncdim%time'`` will return domain axis
              constructs with netCDF dimension name "time".

    id: `str`, optional
        Return only the construct with the given internal identifier.

        *Example:*
          ``id='fieldancillary0'``

    construct_type: `str`, optional
        Return only constructs of the given type. Valid types are:

          ==========================  ================================
          *construct_type*            Constructs
          ==========================  ================================
          ``'field_ancillary'``       Field ancillary constructs
          ``'domain_ancillary'``      Domain ancillary constructs
          ``'dimension_coordinate'``  Dimension coordinate constructs
          ``'domain_axis'``           Domain axis constructs
          ``'auxiliary_coordinate'``  Auxiliary coordinate constructs
          ``'cell_measure'``          Cell measure constructs
          ``'cell_method'``           Cell method constructs
          ``'coordinate_reference'``  Coordinate reference constructs
          ==========================  ================================

        *Example:*
          ``construct_type='dimension_coordinate'``

    axes: sequence of `str`, optional
        Only return constructs which have data that spans any one or
        more of the given domain axes, in any order. Domain axes are
        specified by their unique internal identifiers.

        *Example:*
          ``axes=['domainaxis2']``

        *Example:*
          ``axes=['domainaxis0', 'domainaxis1']``

    copy: `bool`, optional
        If True then return copies of the constructs, rather than the
        actual construct objects contained in the field.

:Returns:

    out: `dict`

**Examples:**

>>> f.constructs()
TODO

        '''
        return self._get_constructs().constructs(
            description=description, id=id,
            construct_type=construct_type, axes=axes, copy=copy)
    #--- End: def

    def domain_axes(self, copy=False):
        '''Return domain axis constructs.

.. versionadded:: 1.7

.. seealso:: `constructs`, `get_construct`

:Parameters:

    copy: `bool`, optional
        If `True` then deep copies of the constructs are returned.

:Returns:

    out: `dict`
        TODO

**Examples**

TODO
>>> f.domain_axes()
{}
        '''
        return self._get_constructs().constructs(
            construct_type='domain_axis', copy=copy)
    #--- End: def
        
#    def coordinates(self, axes=None, copy=False):
#        '''
#        '''
#        out = self.dimension_coordinates(axes=axes, copy=copy)
 #       out.update(self.auxiliary_coordinates(axes=axes, copy=copy))
 #       return out
 #   #--- End: def

    def auxiliary_coordinates(self, axes=None, copy=False):
        '''Return auxiliary coordinate constructs.

.. versionadded:: 1.7

.. seealso:: `constructs`, `get_construct`

:Parameters:

    axes: sequence of `str`, optional
        TODO

    copy: `bool`, optional
        If `True` then deep copies of the constructs are returned.

:Returns:

    out: `dict`
        TODO

**Examples**

TODO
>>> f.auxiliary_constructs()
{}

        '''
        return self._get_constructs().constructs(
            construct_type='auxiliary_coordinate', axes=axes, copy=copy)
    #--- End: def
 
    def dimension_coordinates(self, axes=None, copy=False):
        '''Return dimension coordinate constructs.

.. versionadded:: 1.7

.. seealso:: `constructs`, `get_construct`

:Parameters:

    axes: sequence of `str`, optional
        TODO

    copy: `bool`, optional
        If `True` then deep copies of the constructs are returned.

:Returns:

    out: `dict`
        TODO

**Examples**

TODO
>>> f.dimension_coordinates()
{}
        '''
        return self._get_constructs().constructs(
            construct_type='dimension_coordinate', axes=axes, copy=copy)
    #--- End: def
    
    def domain_axis_name(self, axis):
        '''TODO 
        '''
        return self._get_constructs().domain_axis_name(axis)
    #--- End: def
    
    def set_cell_measure(self, item, axes=None, id=None, copy=True):
        '''Set a cell measure construct.

.. versionadded:: 1.7

.. seealso:: `constructs`, `del_construct`, `get_construct`,
             `set_construct_axes`

:Parameters:

    item: `CellMeasure`
        TODO

    axes: sequence of `str`, optional
        The identifiers of the domain axes spanned by the data array.

        The axes may also be set afterwards with the
        `set_construct_axes` method.

        *Example:*
          ``axes=['domainaxis1']``
        
    id: `str`, optional
        The identifier of the construct. If not set then a new, unique
        identifier is created. If the identifier already exisits then
        the exisiting construct will be replaced.

        *Example:*
          ``id='cellmeasure0'``
        
    copy: `bool`, optional
        If False then do not copy the construct prior to insertion. By
        default it is copied.
        
:Returns:

     out: `str`
        The identifier of the construct.
    
**Examples**

TODO
        '''
        return self.set_construct('cell_measure', item, id=id,
                                  axes=axes, copy=copy)
    #--- End: def

    def set_coordinate_reference(self, item, id=None, copy=True):
        '''Set a coordinate reference construct.

.. versionadded:: 1.7

.. seealso:: `constructs`, `del_construct`, `get_construct`,
             `set_construct_axes`

:Parameters:

    item: `CoordinateReference`
        TODO

    id: `str`, optional
        The identifier of the construct. If not set then a new, unique
        identifier is created. If the identifier already exisits then
        the exisiting construct will be replaced.

        *Example:*
          ``id='coordinatereference0'``
        
    copy: `bool`, optional
        If False then do not copy the construct prior to insertion. By
        default it is copied.
        
:Returns:

     out: `str`
        The identifier of the construct.
    
**Examples**

TODO

        '''
        return self.set_construct('coordinate_reference',
                                  item, id=id, copy=copy)
    #--- End: def

    def set_dimension_coordinate(self, item, axes=None, id=None,
                                 copy=True):
        '''Set a dimension coordinate construct.

.. versionadded:: 1.7

.. seealso:: `constructs`, `del_construct`, `get_construct`,
             `set_construct_axes`

:Parameters:

    item: `DimensionCoordinate`
        TODO

    axes: sequence of `str`, optional
        The identifiers of the domain axes spanned by the data array.

        The axes may also be set afterwards with the
        `set_construct_axes` method.

        *Example:*
          ``axes=['domainaxis1']``
        
    id: `str`, optional
        The identifier of the construct. If not set then a new, unique
        identifier is created. If the identifier already exisits then
        the exisiting construct will be replaced.

        *Example:*
          ``id='dimensioncoordinate1'``
        
    copy: `bool`, optional
        If False then do not copy the construct prior to insertion. By
        default it is copied.
        
:Returns:

     out: `str`
        The identifier of the construct.
    
**Examples**

TODO

        '''
        return self.set_construct('dimension_coordinate', item, id=id,
                                  axes=axes, copy=copy)
    #--- End: def
    
    def set_auxiliary_coordinate(self, item, axes=None, id=None,
                                 copy=True):
        '''Set an auxiliary coordinate construct.

.. versionadded:: 1.7

.. seealso:: `constructs`, `del_construct`, `get_construct`,
             `set_construct_axes`

:Parameters:

    item: `AuxiliaryCoordinate`
        TODO

    axes: sequence of `str`, optional
        The identifiers of the domain axes spanned by the data array.

        The axes may also be set afterwards with the
        `set_construct_axes` method.

        *Example:*
          ``axes=['domainaxis1']``
        
    id: `str`, optional
        The identifier of the construct. If not set then a new, unique
        identifier is created. If the identifier already exisits then
        the exisiting construct will be replaced.

        *Example:*
          ``id='auxiliarycoordinate0'``
        
    copy: `bool`, optional
        If False then do not copy the construct prior to insertion. By
        default it is copied.
        
:Returns:

     out: `str`
        The identifier of the construct.
    
**Examples**

TODO

    '''
        return self.set_construct('auxiliary_coordinate', item,
                                  id=id, axes=axes, copy=copy)
    #--- End: def

    def set_domain_axis(self, domain_axis, id=None, copy=True):
        '''Set a domain axis construct.

.. versionadded:: 1.7

.. seealso:: `constructs`, `del_construct`, `get_construct`

:Parameters:

    item: `DomainAxis`
        TODO
        
    id: `str`, optional
        The identifier of the construct. If not set then a new, unique
        identifier is created. If the identifier already exisits then
        the exisiting construct will be replaced.

        *Example:*
          ``id='domainaxis2'``
        
    copy: `bool`, optional
        If False then do not copy the construct prior to insertion. By
        default it is copied.
        
:Returns:

     out: `str`
        The identifier of the construct.
    
**Examples**

TODO

        '''
        return self.set_construct('domain_axis', domain_axis, id=id,
                                  copy=copy)
    #--- End: def

    def set_domain_ancillary(self, item, axes=None, id=None, copy=True):
#                             extra_axes=0, copy=True):
        '''Set a domain ancillary construct.

.. versionadded:: 1.7

.. seealso:: `constructs`, `del_construct`, `get_construct`,
             `set_construct_axes`

:Parameters:

    item: `DomainAncillary`
        TODO

    axes: sequence of `str`, optional
        The identifiers of the domain axes spanned by the data array.

        The axes may also be set afterwards with the
        `set_construct_axes` method.

        *Example:*
          ``axes=['domainaxis1', 'domainaxis0']``
        
    id: `str`, optional
        The identifier of the construct. If not set then a new, unique
        identifier is created. If the identifier already exisits then
        the exisiting construct will be replaced.

        *Example:*
          ``id='domainancillary0'``
        
    copy: `bool`, optional
        If False then do not copy the construct prior to insertion. By
        default it is copied.
        
:Returns:

     out: `str`
        The identifier of the construct.
    
**Examples**

TODO

        ''' 
        return self.set_construct('domain_ancillary', item, id=id,
                                  axes=axes, #extra_axes=extra_axes,
                                  copy=copy)
    #--- End: def

#--- End: class
