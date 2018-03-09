import abc

from collections import OrderedDict


class Constructs(object):
    '''
Keys are item identifiers, values are item objects.
    '''

    __metaclass__ = abc.ABCMeta
    
    def __init__(self, 
                 auxiliary_coordinate=None,                
                 dimension_coordinate=None,         
                 domain_ancillary=None,         
                 field_ancillary=None,         
                 cell_measure=None,
                 coordinate_reference=None,
                 domain_axis=None,
                 cell_method=None):
        '''
        '''
        self._zzz = {}

        self._array_constructs     = set()
        self._non_array_constructs = set()
        self._ordered_constructs   = set()

        self._construct_axes = {}
        # The construct type for each key. For example
        # {'domainaxis1':'domain_axis', 'aux3':'auxiliary_coordinate'}
        self._construct_type = {}
        
        self._constructs     = {}
        
        if auxiliary_coordinate:
            self._zzz['auxiliary_coordinate'] = auxiliary_coordinate
            self._array_constructs.add(auxiliary_coordinate)
            
        if dimension_coordinate:
            self._zzz['dimension_coordinate'] = dimension_coordinate
            self._array_constructs.add(dimension_coordinate)
            
        if domain_ancillary:
            self._zzz['domain_ancillary'] = domain_ancillary
            self._array_constructs.add(domain_ancillary)
            
        if field_ancillary:
            self._zzz['field_ancillary'] = field_ancillary
            self._array_constructs.add(field_ancillary)

        if cell_measure:
            self._zzz['cell_measure'] = cell_measure
            self._array_constructs.add(cell_measure)

        if domain_axis:
            self._zzz['domain_axis'] = domain_axis
            self._non_array_constructs.add(domain_axis)

        if coordinate_reference:
            self._zzz['coordinate_reference'] = coordinate_reference
            self._non_array_constructs.add(coordinate_reference)

        if cell_method:
            self._zzz['cell_method'] = cell_method
            self._non_array_constructs.add(cell_method)
            self._ordered_constructs.add(cell_method)

        for x in self._array_constructs:
            self._constructs[x] = {}
        
        for x in self._non_array_constructs:
            self._constructs[x] = {}
        
        for x in self._ordered_constructs:
            self._constructs[x] = OrderedDict()
    #--- End: def

    def __call__(self):
        '''
        '''
        return self.constructs()
    #--- End: def
    
    def __deepcopy__(self, memo):
        '''Called by the :py:obj:`copy.deepcopy` standard library function.

.. versionadded:: 1.6

        '''
        return self.copy()
    #--- End: def

    def __repr__(self):
        '''x.__repr__() <==> repr(x)

        '''
        return '<{0}: {1}>'.format(self.__class__.__name__, str(self))
    #--- End: def

    def __str__(self):
        '''x.__str__() <==> str(x)

        '''
        return ' '
    #--- End: def

    def construct_type(self, key):
        '''
        '''
        return self._construct_type.get(key)
    #--- End: def

    def construct_types(self):
        '''
        '''
        return self._construct_type.copy()
    #--- End: def

    def array_constructs(self, axes=None, copy=False):
        '''
        '''
        out = {}
        for construct_type in self._array_constructs:
            out.update(self._constructs[construct_type])

        if axes:
            spans_axes = set(axes)
            construct_axes = self.construct_axes()
            for key, construct in out.items():
                x = construct_axes[key]
                if not spans_axes.intersection(x):
                    del out[key]
        #--- End: def

        return out
    #--- End: def
    
    def non_array_constructs(self):
        '''
        '''
        out = {}
        for construct_type in self._non_array_constructs:
            out.update(self._constructs[construct_type])

        return out
    #--- End: def

    def clear(self):
        '''
        '''
        self._construct_axes.clear()

        for x in array_constructs:
            self._constructs[x].clear()
        
        for x in non_array_constructs:
            self._constructs[x].clear()
        
        for x in ordered_constructs:
            self._constructs[x].clear()
    #--- End: def

    def _xxx(self, construct_type):
        if construct_type is None:
            return None
        
        x = self._zzz.get(construct_type)
        if x is None:
            raise ValueError("Invalid construct type: {!r}".format(construct_type))
        return x
        
    def constructs(self, construct_type=None, copy=False):
        '''
        '''
        construct_type = self._xxx(construct_type)
        if construct_type is not None:
            out = self._constructs[construct_type].copy()
        else:
            out = {}
            for v in self._constructs.values():
                out.update(v)
        #--- End: if

        if copy:
            for key, construct in out.items():
                out[key] = construct.copy()

        return out
    #--- End: def
    
    def construct_axes(self, key=None, new_axes=None, default=None):
        '''
:Examples 1:

>>> x = c.construct_axes()

:Parameters:

    key: `str`, optional

    axes: sequence of `str`, optional

    default: optional

:Returns:

    out: `dict` or `tuple` or *default*

:Examples 2:

>>> c.variable_axes()
{'aux0': ('dim1', 'dim0'),
 'aux1': ('dim0',),
 'aux2': ('dim0',),
 'aux3': ('dim0',),
 'aux4': ('dim0',),
 'aux5': ('dim0',)}
>>> c._axes(key='aux0')
('dim1', 'dim0')
>>> print c.item_axes(key='aux0', new_axes=['dim0', 'dim1'])
None
>>> c._axes(key='aux0')
('dim0', 'dim1')

'''
        if key is None:
            # Return all of the constructs' axes
            return self._construct_axes.copy()

        if new_axes is None:
            # Return a particular construct's axes
            return self._construct_axes.get(key, default)
 
        # Still here? The set new item axes.
        self._construct_axes[key] = tuple(new_axes)
    #--- End: def

    def set_construct_axes(self, key, axes):
        '''
        '''        
        self._construct_axes[key] = tuple(new_axes)
    #--- End: def

    def copy(self, data=True):
        '''
Return a deep or shallow copy.

``c.copy()`` is equivalent to ``copy.deepcopy(c)``.

:Returns:

    out: `Constructs`
        The copy.

:Examples:

>>> d = c.copy()

'''
        X = type(self)
        new = X.__new__(X)

        new._zzz                  = self._zzz.copy()
        new._array_constructs     = self._array_constructs.copy()
        new._non_array_constructs = self._non_array_constructs.copy()
        new._ordered_constructs   = self._ordered_constructs.copy()
        new._construct_axes       = self._construct_axes.copy()
        
        new._construct_type = {}
        d = {}
        for construct_type in (tuple(new._array_constructs) +
                               tuple(new._non_array_constructs)):
            v = self._constructs[construct_type]
            new_v = {}
            for key, construct in v.iteritems():
                new_v[key] = construct.copy(data=data)
                new._construct_type[key] = construct_type
                
            d[construct_type] = new_v
        #--- End: for
        new._constructs = d

        return new
    #--- End: def

    def subset(self, array_constructs=(), non_array_constructs=(), copy=True):
        '''
        '''

        ordered_constructs = self._ordered_constructs.copy()

        for x in ordered_constructs.copy():
            if x not in array_constructs and x not in non_array_constructs:
                ordered_constructs.remove(x)
        #--- End: for
        
        new = type(self)(array_constructs=array_constructs,
                         non_array_constructs=non_array_constructs,
                         ordered_constructs=ordered_constructs)
        
        for construct_type in (tuple(array_constructs) +
                               tuple(non_array_constructs)):
            d = {}
            for key, construct in self._constructs[construct_type].iteritems():
                d[key] = construct.copy()
                new._construct_type[key] = construct_type
                if construct_type in array_constructs:                    
                    new._construct_axes[key] = self._construct_axes[key]
                    
                if copy:
                    construct = construct.copy()

                new._constructs[construct_type][key] = construct
                #--- End: for
            new._constructs[construct_type] = d
        #--- End: for

        return new
    #--- End: def
        
    def axes_to_constructs(self):
        '''(
:Examples:

>>> i.axes_to_constructs()
{
 ('dim1',): {
        'dimension_coordinates': {'dim1': <DimensionCoordinate>},
        'auxiliary_coordinates': {},
        'cell_measures'        : {},
        'domain_ancillaries'   : {},
        'field_ancillaries'    : {},
        }
 ('dim1', 'dim2',): {
        'dimension_coordinates': {},
        'auxiliary_coordinates': {'aux0': <AuxiliaryCoordinate:>,
                                  'aux1': <AuxiliaryCoordinate:>},
        'cell_measures'        : {},
        'domain_ancillaries'   : {},
        'field_ancillaries'    : {},
        }
}
'''
        out = {}

        for axes in self.construct_axes().values():
            d = {}
            for construct_type in self._array_constructs:
                d[construct_type] = {}  ARRAY CONSTRUCTS SHOULD CONTAIN GENERIC NAME, NOT KEY BASE .....

            out[axes] = d
        #--- End: for

        for key, construct in self.array_constructs().iteritems():
            axes = self.construct_axes(key)
            construct_type = self._construct_type[key]
            out[axes][construct_type][key] = construct

        return out
    #--- End: def

    def domain_axes(self, copy=False):
        return self.constructs('domain_axis', copy=copy)
    #--- End: def
    
    def get_construct(self, key, *default):
        '''
        '''
        d = self._constructs.get(self._construct_type.get(key))
        if d is None:
            d = {}
            
        try:            
            return d[key]
        except KeyError:
            if default:
                return default[0]

            raise ValueError("Can't get construct!!!!!!")
    #--- End: def
    
    def set_construct(self, construct_type, construct, key=None,
                      axes=None, copy=True):
        '''
        '''
        construct_type = self._xxx(construct_type)
        if key is None:
            key = self.new_identifier(construct_type)
        elif key in self._constructs[construct_type]:
            raise ValueError("Key exists. Use replace")
        
        if construct_type in self._array_constructs:
            if axes is None:
                raise ValueError("sdf lsbe lhbkhjb iuhj-98qohu n")
            if len(axes) != construct.get_data().ndim:
                raise ValueError(
"Can't insert {}: Mismatched axis sizes (got {}, expected {})".format(
    construct_type, len(axes), construct.get_data().ndim))

            domain_axes = self.domain_axes()
            for axis, size in zip(axes, construct.get_data().shape):
                if size != domain_axes[axis].get_size():
                    raise ValueError(
"Can't insert {}: Mismatched axis size (got {}, expected {})".format(
    construct_type, size, domain_axes[axis].get_size()))
            #--- End: for

            self._construct_axes[key] = tuple(axes)
        #--- End: if
        
        self._construct_type[key] = construct_type

        if copy:
            construct = construct.copy()

        self._constructs[construct_type][key] = construct
        
        return key
    #--- End: def

    def new_identifier(self, construct_type):
        '''

Return a new, unique identifier for the construct.

:Parameters:

    construct_type: `str`

:Returns:

    out: `str`
        The new identifier.

:Examples:

>>> d.items().keys()
['aux2', 'aux0', 'dim1', 'ref2']
>>> d.new_identifier('aux')
'aux3'
>>> d.new_identifier('ref')
'ref1'

>>> d.items().keys()
[]
>>> d.new_identifier('dim')
'dim0'


>>> d.axes()
{'dim0', 'dim4'}
>>> d.new_identifier('axis')
'dim2'

>>> d.axes()
{}
>>> d.new_identifier('axis')
'dim0'

        '''
        keys = self._constructs[construct_type]

        key = '{0}{1}'.format(construct_type, len(keys))
        while key in keys:
            n += 1
            key = '{0}{1}'.format(construct_type, n)

        return key
    #--- End: def

    def del_construct(self, key):        
        '''Remove a construct.

:Examples 1:

>>> x = c.del_construct('auxiliarycoordinate2')

:Parameters:

    key: `str`

:Returns:

    out:
        The removed construct, or `None` if the given key did not
        exist.

:Examples 2:

        '''
        self._construct_axes.pop(key, None)

        construct_type = self._construct_type.pop(key, None)
        if construct_type is None:
            return

        return self._constructs[construct_type].pop(key, None)
    #--- End: def

    def replace(self, key, construct=None, axes=None, copy=True):
        '''
'''
        construct_type = self.construct_types().get(key)
        if construct_type is None:
            raise ValueError("Can't replace non-existent construct {!r}".format(key))

        if axes is not None and construct_type in self._array_constructs:        
            self._construct_axes[key] = tuple(axes)

        if construct is not None:
            if copy:
                construct = construct.copy()
            
            self._constructs[construct_type][key] = construct
    #--- End: def
    
#--- End: class
