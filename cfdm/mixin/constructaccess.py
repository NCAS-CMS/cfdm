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
        '''TODO 
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
    
#--- End: class
