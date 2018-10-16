from builtins import object

import re


class ConstructAccess(object):
    '''Mixin class for manipulating constructs stored in a `Constructs`
object.

    '''

    def _unique_construct_names(self):
        '''

        '''    
        key_to_name = {}
        name_to_keys = {}


        for d in self._get_constructs()._constructs.values():
            name_to_keys = {}
        
#        for key, construct in self.constructs().items():
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
        '''
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
    
    def auxiliary_coordinates(self, axes=None, copy=False):
        '''Return the auxiliary coordinates 
        '''    
        return self._get_constructs().constructs(
            construct_type='auxiliary_coordinate',
            axes=axes, copy=copy)
    #--- End: def

    def cell_measures(self, axes=None, copy=False):
        '''Return the 
        '''    
        return self._get_constructs().constructs(
            construct_type='cell_measure',
            axes=axes, copy=copy)
    #--- End: def

    def construct(self, description=None, axes=None,
                  construct_type=None, copy=False):
        '''
        '''
        return self._get_constructs().construct(
            description=description,
            construct_type=construct_type,
            axes=axes,
            copy=copy)
    #--- End: def

    def constructs(self, description=None, axes=None,
                   construct_type=None, copy=False):
        '''
        '''
        return self._get_constructs().constructs(
            description=description,
            construct_type=construct_type,
            axes=axes,
            copy=copy)
    #--- End: def

    def coordinates(self, axes=None, copy=False):
        '''
        '''
        out = self.dimension_coordinates(axes=axes, copy=copy)
        out.update(self.auxiliary_coordinates(axes=axes, copy=copy))
        return out
    #--- End: def

    def dimension_coordinates(self, axes=None, copy=False):
        '''Return the 
        '''    
        return self._get_constructs().constructs(
            construct_type='dimension_coordinate',
            axes=axes, copy=copy)
    #--- End: def

    def domain_ancillaries(self, axes=None, copy=False):
        '''
        '''    
        return self._get_constructs().constructs(
            construct_type='domain_ancillary',
            axes=axes, copy=copy)
    #--- End: def

    def domain_axis_name(self, axis):
        '''
        '''
        return self._get_constructs().domain_axis_name(axis)
    #--- End: def
    
#--- End: class
