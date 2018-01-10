from collections import OrderedDict

class Constructs(object):
    '''
Keys are item identifiers, values are item objects.
    '''
    def __init__(self, array_constructs=(), non_array_constructs=(),
                 ordered_constructs=()):
        '''
'''
        self._array_constructs     = set(array_constructs)
        self._non_array_constructs = set(non_array_constructs)
        self._ordered_constructs   = set(ordered_constructs)
        self._construct_axes = {}
        self._construct_type = {}
        self._constructs     = {}

        for x in array_constructs:
            self._constructs[x] = {}
        
        for x in non_array_constructs:
            self._constructs[x] = {}
        
        for x in ordered_constructs:
            self._constructs[x] = OrderedDict()
    #--- End: def

    def __call__(self):
        '''
        '''
        return self.constructs()
    #--- End: def
    
    def __deepcopy__(self, memo):
        '''

Called by the :py:obj:`copy.deepcopy` standard library function.

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

#    def construct(self, key, new_construct=None, copy=False):
#        '''
#        '''
#        construct_type  = self._construct_type.get(key)
#        if construct_type is None:
#            return None
#
#
#        
#        if key is None:
#            # Return all of the constructs' axes
#            return self._construct_axes.copy()
#
#        if new_construct is None:
#            # Return a particular construct
#            construct = self._construct[construct_type][key]
#            if copy:
#                construct = construct.copy()
#
#            return construct
# 
#        # Still here? The set new construct
#        self._construct[construct_type][key] = new_construct
#    #--- End: def
    
    def constructs(self, construct_type=None, axes=None, copy=False):
        '''
        '''
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

        if axes:
            spans_axes = set(axes)
            construct_axes = self.construct_axes()
            for key, construct in out.items():
                x = construct_axes.get(key)
                if x is None:
                    del out[key]
                elif not spans_axes.intersection(x):
                    del out[key]
        #--- End: def

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

    def copy(self):
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
                new_v[key] = construct.copy()
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
        '_dimension_coordinates': {'dim1': <DimensionCoordinate>},
        '_auxiliary_coordinates': {},
        '_cell_measures'        : {},
        '_domain_ancillaries'   : {},
        '_field_ancillaries'    : {},
        }
 ('dim1', 'dim2',): {
        '_dimension_coordinates': {},
        '_auxiliary_coordinates': {'aux0': <AuxiliaryCoordinate:>,
                                   'aux1': <AuxiliaryCoordinate:>},
        '_cell_measures'        : {},
        '_domain_ancillaries'   : {},
        '_field_ancillaries'    : {},
        }
}
'''
        out = {}

        for axes in self.construct_axes().values():
            d = {}
            for construct_type in self._array_constructs:
                d[construct_type] = {}

            out[axes] = d
        #--- End: for

        for key, construct in self.array_constructs().iteritems():
            axes = self.construct_axes(key)
            construct_type = self._construct_type[key]
            out[axes][construct_type][key] = construct
        
        return out
    #--- End: def

    def domain_axis_name(self, axis): #, default=None):
        '''Return the canonical name for an axis.

:Parameters:

    axis: `str`
        The identifier of the axis.

          *Example:*
            ``axis='axis2'``

    default: optional

:Returns:

    out: `str`
        The canonical name for the axis.

:Examples:

        '''
        domain_axes = self.domain_axes()
        
        if axis not in domain_axes:
            return default

        construct_axes = self.construct_axes()

        name = None
        
        for key, dim in self.dimension_coordinates().iteritems():
            if construct_axes[key] == (axis,):
                # Get the name from a dimension coordinate
                name = dim.name(ncvar=False, id=False, default=None)
                break
        #--- End: for
        if name is not None:
            return name

        found = False
        for key, aux in self.auxiliary_coordinates().iteritems():
            if construct_axes[key] == (axis,):
                if found:
                    name = None
                    break
                
                # Get the name from an auxiliary coordinate
                name = aux.name(ncvar=False, id=False, default=None)
                found = True
        #--- End: for
        if name is not None:
            return name

        ncdim = domain_axes[axis].ncdim()
        if ncdim is not None:
            # Get the name from netCDF dimension name            
            return 'ncdim%{0}'.format(ncdim)
        
        return 'id%{0}'.format(axis)
    #--- End: def

    def equals(self, other, rtol=None, atol=None, traceback=False,
               **kwargs):
        '''
        
        '''
        if self is other:
            return True
        
        # Check that each instance is the same type
        if type(self) != type(other):
            if traceback:
                print("{0}: Different object types: {0}, {1}".format(
                    self.__class__.__name__, other.__class__.__name__))
            return False
        #--- End: if

        # ------------------------------------------------------------
        # Domain axes
        # ------------------------------------------------------------
        self_sizes  = [d.size for d in self.domain_axes().values()]
        other_sizes = [d.size for d in other.domain_axes().values()]
        
        if sorted(self_sizes) != sorted(other_sizes):
            # There is not a 1-1 correspondence between axis sizes
            if traceback:
                print("{0}: Different domain axes: {1} != {2}".format(
                    self.__class__.__name__,
                    sorted(self.values()),
                    sorted(other.values())))
            return False
        #--- End: if
        
        if rtol is None:
            rtol = RTOL()
        if atol is None:
            atol = ATOL()

        # ------------------------------------------------------------
        # 
        # ------------------------------------------------------------
        axes0_to_axes1 = {}

        key1_to_key0 = {}

        axes_to_items0 = self.axes_to_constructs()
        axes_to_items1 = other.axes_to_constructs()
        
        for axes0, items0 in axes_to_items0.iteritems():
            matched_all_items_with_these_axes = False

            len_axes0 = len(axes0) 
            for axes1, items1 in axes_to_items1.items():
                matched_roles = False

                if len_axes0 != len(axes1):
                    # axes1 and axes0 contain differents number of
                    # axes.
                    continue
            
                for construct_type in self._array_constructs:
                    matched_role = False

                    role_items0 = items0[construct_type]
                    role_items1 = items1[construct_type]

                    if len(role_items0) != len(role_items1):
                        # There are the different numbers of items
                        # with this role
                        matched_all_items_with_these_axes = False
                        break

                    # Check that there are matching pairs of equal
                    # items
                    for key0, item0 in role_items0.iteritems():
                        matched_item = False
                        for key1, item1 in role_items1.items():
                            if item0.equals(item1, rtol=rtol,
                                            atol=atol, traceback=False, **kwargs):
                                del role_items1[key1]
                                key1_to_key0[key1] = key0
                                matched_item = True
                                break
                        #--- End: for

                        if not matched_item:
                            break
                    #--- End: for

                    if role_items1:
                        break

                    del items1[construct_type]
                #--- End: for

                matched_all_items_with_these_axes = not items1

                if matched_all_items_with_these_axes:
                    del axes_to_items1[axes1]
                    break
            #--- End: for

            # Map item axes in the two instances
            axes0_to_axes1[axes0] = axes1

            if not matched_all_items_with_these_axes:
                if traceback:
                    names = [self.domain_axis_name(axis0) for axis0 in axes0]
                    print("Can't match items spanning axes {0}".format(names))
                return False
        #--- End: for

        axis0_to_axis1 = {}
        axis1_to_axis0 = {}
        for axes0, axes1 in axes0_to_axes1.iteritems():
            for axis0, axis1 in zip(axes0, axes1):
                if axis0 in axis0_to_axis1 and axis1 != axis0_to_axis1[axis0]:
                    if traceback:
                        print(
"Field: Ambiguous axis mapping ({} -> both {} and {})".format(
    self.domain_axis_name(axes0), other.domain_axis_name(axis1),
    other.domain_axis_name(axis0_to_axis1[axis0])))
                    return False
                elif axis1 in axis1_to_axis0 and axis0 != axis1_to_axis0[axis1]:
                    if traceback:
                        print(
"Field: Ambiguous axis mapping ({} -> both {} and {})".format(
    self.domain_axis_name(axis0), self.domain_axis_name(axis1_to_axis0[axis0]),
    other.domain_axis_name(axes1)))
                    return False

                axis0_to_axis1[axis0] = axis1
                axis1_to_axis0[axis1] = axis0
        #--- End: for     

        #-------------------------------------------------------------
        # Cell methods
        #-------------------------------------------------------------
        cell_methods0 = self.cell_methods()
        cell_methods1 = other.cell_methods()

        if len(cell_methods0) != len(cell_methods1):
            if traceback:
                print("Field: Different cell methods: {0!r}, {1!r}".format(
                    cell_methods0, cell_methods1))
            return False

        if cell_methods0:
            for cm0, cm1 in zip(cell_methods0.values(),
                                cell_methods1.values()):
                # Check that there are the same number of axes
                axes0 = cm0.axes
                axes1 = list(cm1.axes)
                if len(cm0.axes) != len(axes1):
                    if traceback:
                        print (
"Field: Different cell methods (mismatched axes): {0!r}, {1!r}".format(
    cell_methods0, cell_methods1))
                    return False
    
                argsort = []
                for axis0 in axes0:
                    if axis0 is None:
                        return False
                    for axis1 in axes1:
                        if axis0 in axis0_to_axis1 and axis1 in axis1_to_axis0:
                            if axis1 == axis0_to_axis1[axis0]:
                                axes1.remove(axis1)
                                argsort.append(cm1.axes.index(axis1))
                                break
                        elif axis0 in axis0_to_axis1 or axis1 in axis1_to_axis0:
                            if traceback:
                                print (
"Field: Different cell methods (mismatched axes): {0!r}, {1!r}".format(
    cell_methods0, cell_methods1))
    
                            return False
                        elif axis0 == axis1:
                            # Assume that the axes are standard names
                            axes1.remove(axis1)
                            argsort.append(cm1.axes.index(axis1))
                        elif axis1 is None:
                            if traceback:
                                print (
"Field: Different cell methods (undefined axis): {0!r}, {1!r}".format(
    cell_methods0, cell_methods1))
                            return False
                #--- End: for
    
                if len(cm1.axes) != len(argsort):
                    if traceback:
                        print ("Field: Different cell methods: {0!r}, {1!r}".format(
                            cell_methods0, cell_methods1))
                    return False
    
                cm1 = cm1.copy()
                cm1.sort(argsort=argsort)
                cm1.axes = axes0
    
                if not cm0.equals(cm1, atol=atol, rtol=rtol,
                                  traceback=traceback, **kwargs):
                    if traceback:
                        print ("Field: Different cell methods: {0!r}, {1!r}".format(
                            cell_methods0, cell_methods1))
                    return False                
            #--- End: for
        #--- End: if

        # ------------------------------------------------------------
        # Coordinate references
        # ------------------------------------------------------------
        refs0 = self.coordinate_references()
        refs1 = other.coordinate_references()

        if len(refs0) != len(refs1):
            if traceback:
                print("Field: Different coordinate references: {0!r}, {1!r}".format(
                    refs0, refs1))
            return False

        if refs0:
            for ref0 in refs0.values():
                found_match = False
                for key1, ref1 in refs1.items():
                    if not ref0.equals(ref1, rtol=rtol, atol=atol,
                                       traceback=True, **kwargs): ####
                        continue
    
                    # Coordinates
                    coordinates0 = ref0.coordinates
                    coordinates1 = set()
                    for value in ref1.coordinates:
                        coordinates1.add(key1_to_key0.get(value, value))
                        
                    if coordinates0 != coordinates1:
                        continue
    
                    # Domain ancillary terms
                    terms0 = ref0.domain_ancillaries
                    terms1 = {}
                    for term, key in ref1.domain_ancillaries.items():
                        terms1[term] = key1_to_key0.get(key, key)
    
                    if terms0 != terms1:
                        continue
    
                    found_match = True
                    del refs1[key1]                                       
                    break
                #--- End: for
    
                if not found_match:
                    if traceback:
                        print("Field: No match for {0!r})".format(ref0))
                    return False
            #--- End: for
        #--- End: if

        # ------------------------------------------------------------
        # Still here? Then the two Constructs are equal
        # ------------------------------------------------------------
        return True
    #--- End: def
    
    def auxiliary_coordinates(self, copy=False):
        return self.constructs('auxiliarycoordinate', copy=copy)
    #--- End: def
   
    def cell_methods(self, copy=False):
        return self.constructs('cellmethod', copy=copy)
    #--- End: def
    
    def coordinate_references(self, copy=False):
        return self.constructs('coordinatereference', copy=copy)
    #--- End: def

    def dimension_coordinates(self, copy=False):
        return self.constructs('dimensioncoordinate', copy=copy)
    #--- End: def

    def domain_axes(self, copy=False):
        return self.constructs('domainaxis', copy=copy)
    #--- End: def
    
    def get(self, key, default=None):
        d = self._constructs.get(self._construct_type.get(key))
        if d is None:
            return default

        return d.get(key, default)
    #--- End: def
    
    def insert(self, construct_type, construct, key=None,
               axes=None, copy=True):
        '''
        '''
        if key is None:
            key = self.new_identifier(construct_type)
        elif key in self._consructs[construct_type]:
            raise ValueError("Key exists. Use replace")
        
        if construct_type in self._array_constructs:
            if axes is None:
                raise ValueError("sdf lsbe lhbkhjb iuhj-98qohu n")
            if len(axes) != construct.ndim:
                raise ValueError(
"Can't insert {}: Mismatched axis sizes (got {}, expected {})".format(
    construct_type, len(axes), construct.ndim))

            domain_axes = self.domain_axes()
            for axis, size in zip(axes, construct.shape):
                if size != domain_axes[axis].size:
                    raise ValueError(
"Can't insert {}: Mismatched axis size (got {}, expected {})".format(
    construct_type, size, domain_axes[axis].size))
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

Return a new, unique auxiliary coordinate identifier for the domain.

.. seealso:: `new_measure_identifier`, `new_dimemsion_identifier`,
             `new_ref_identifier`

The domain is not updated.

:Parameters:

    item_type: `str`

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

        n = len(keys)
        key = '{0}{1}'.format(construct_type, n)

        while key in keys:
            n += 1
            key = '{0}{1}'.format(construct_type, n)

        return key
    #--- End: def

    def remove(self, key, default=None):
        '''
'''
        self._construct_axes.pop(key, None)

        construct_type = self._construct_type.pop(key, None)
        if construct_type is None:
            return default

        return self._constructs[construct_type].pop(key, default)
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
