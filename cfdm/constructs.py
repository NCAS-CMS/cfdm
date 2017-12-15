from collections import OrderedDict

class Constructs(dict):
    '''
Keys are item identifiers, values are item objects.
    '''
    def __init__(self, Axes=None):
        '''
'''
        self._auxiliary_coordinates = {}
        self._field_ancillaries     = {}
        self._domain_ancillaries    = {}
        self._dimension_coordinates = {}
        self._cell_measures         = {}
        self._domain_axes           = {}
        self._coordinate_references = {}

        self._cell_methods = OrderedDict()

        # The axes identifiers for each item. For example,
        # self._copnstruct_axes['aux2'] = ['dim1, 'dim0']
        self._item_axes = {}

        self._construct_type = {}
    #--- End: def

    def __deepcopy__(self, memo):
        '''

Called by the :py:obj:`copy.deepcopy` standard library function.

.. versionadded:: 1.6

'''
        return self.copy(shallow=False)
    #--- End: def


    def _xxx(out, axes=None, copy=False):
        '''
        '''
        if axes is not None:
            axes = set(axes)
            item_axes = self.item_axes()
            for key, item in out.items():
                if set(item_axes[key]) == axes:
                    out[key] = item.copy()
        #--- End: if
                
        if copy:
            for key, item in out.items():
                out[key] = item.copy()
        #--- End: if
                        
        return out
    #--- End: def

    def coordinate_references(self, copy=False):
        '''
        '''
        return self._xxx(self._coordinate_references.copy(), axes=None, copy=copy)
    #--- End: def
        
    def auxiliary_coordinates(self, axes=None, copy=False):
        '''Auxiliary coordinate objects and their identifiers
        
:Returns:
        
    out: `dict`
          A dictionary of auxiliary coordinate objects keyed by their
          identifiers.

:Examples:

>>> i.auxs()
{'aux0': <CF AuxiliaryCorodinate: >}

        '''
        return self._xxx(self._auxiliary_coordinates.copy(), axes, copy)
    #--- End: def

    def auxiliary_coordinate(self, key=None, axes=None, default=None, copy=False):
        '''Auxiliary coordinate objects and their identifiers
        
:Returns:
        
    out: `dict`
          A dictionary of auxiliary coordinate objects keyed by their
          identifiers.

:Examples:

>>> i.auxs()
{'aux0': <CF AuxiliaryCorodinate: >}

        '''
        x = self.auxiliary_coordinates(axes=axes, copy=copy)
        key, item = x.popitem()

        if x:
            return default

        return item
    #--- End: def

    def variables():
        out = self._dimension_coordinates.copy()
        out.update(self._auxiliary_coordinates)
        out.update(self._cell_methods)
        out.update(self._field_ancillaries)
        out.update(self._domain_ancillaries)
        return out
    
    def variable(key, default=None):
        return self.variables.get(key, default)
    
    def dimension_coordinates(self):
        '''Return dimension coordinate objects and their identifiers
        
:Returns:
        
    out: `dict`
          A dictionary of dimension coordinate objects keyed by their
          identifiers.

:Examples:

>>> i.dims()
{'dim0': <CF DimensionCoordinate: >}

        '''
        return _xxx(self._dimension_coordinates.copy(), axes, copy)
    #--- End: def

    def domain_axes(self, copy=False):
        '''
        '''
        return self._xxx(self._domain_axes.copy(), axes=None, copy=copy)
    #--- End: def
    
    def item_axes(self, key=None, new_axes=None, default=None):
        '''
:Examples 1:

>>> x = c.item_axes()

:Parameters:

    key: `str`, optional

    axes: sequence of `str`, optional

    default: optional

:Returns:

    out: `dict` or `tuple` or *default*

:Examples 2:

>>> c.item_axes()
{'aux0': ('dim1', 'dim0'),
 'aux1': ('dim0',),
 'aux2': ('dim0',),
 'aux3': ('dim0',),
 'aux4': ('dim0',),
 'aux5': ('dim0',)}
>>> c.item_axes(key='aux0')
('dim1', 'dim0')
>>> print c.item_axes(key='aux0', new_axes=['dim0', 'dim1'])
None
>>> c.item_axes(key='aux0')
('dim0', 'dim1')

'''
        if key is None:
            # Return all of the items' axes
            return self._item_axes.copy()

        if new_axes is None:
            # Return a particular item's axes
            return self._item_axes.get(key, default)
 
        # Still here? The set new item axes.
        self._item_axes[key] = tuple(new_axes)
    #--- End: def
    
    def axes_to_items(self):
        '''
:Examples:

>>> i.axes_to_items()
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
        item_axes = self.item_axes()
        out = {}

        for axes in item_axes.values():
            out[axes] = {}
                
        for role in ('_dimension_coordinates',
                     '_auxiliary_coordinates',
                     '_cell_measures',
                     '_domain_ancillaries',
                     '_field_ancillaries'):     
            for item_axes, items in out.iteritems():
                items_role = {}
                for key in getattr(self, role):
                    if axes[key] == item_axes:
                        items_role[key] = self[key]
                #--- End: for
                items[role] = items_role
        #--- End: for
        
        return out
    #--- End: def

    def axis_name(self, axis, default=None):
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
        domain_axes =  self.domain_axes()
        
        if axis not in domain_axes:
            return default

        item_axes = self.item_axes()
        
        for key, dim in self.dimension_coordinates().iteritems():
            if item_axes[key] == (axis,):
                # Get the name from a dimension coordinate
                return dim.name(default=default)

        found = False
        for key, aux in self.auxiliary_coordinates().iteritems():
            if item_axes()[key] == (axis,):
                if found:
                    found = False
                    break
                
                # Get the name from an auxiliary coordinate
                name = aux.name(default=default)
                found = True
        #--- End: for
        if found:
            return name

        axis = domain_axes[axis]
        ncdim = getattr(axis, 'ncdim', None)
        if ncdim is not None:
            # Get the name from netCDF dimension name            
            return 'ncdim%{0}'.format(ncdim)
        
        return default
    #--- End: def

    def copy(self, shallow=False):
        '''

Return a deep or shallow copy.

``i.copy()`` is equivalent to ``copy.deepcopy(i)``.

``i.copy(shallow=True)`` is equivalent to ``copy.copy(i)``.

:Parameters:

    shallow: `bool`, optional

:Returns:

    out: `Items`
        The copy.

:Examples:

>>> i = j.copy()

'''
        X = type(self)
        new = X.__new__(X)

        for role in ('_dimension_coordinates', 
                     '_auxiliary_coordinates', 
                     '_cell_measures',         
                     '_domain_ancillaries',    
                     '_field_ancillaries',
                     '_cell_methods',
                     '_coordinate_references',
                     '_domain_axes'):
            setattr(new, role, setattr(self, role).copy())
            d = getattr(new, role)
            if shallow:
                for key, value in self.iteritems():
                    d[key] = value
            else:
                for key, value in self.iteritems():
                    d[key] = value.copy()
        #--- End: for
        
        # Copy item axes (this is OK because it is a dictionary of
        # tuples).
        new._item_axes = self._item_axes.copy()

        return new
    #--- End: def
    
    def equals(self, other, rtol=None, atol=None,
               ignore_data_type=False, ignore_fill_value=False,
               traceback=False, _equivalent=False, ignore=()):
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
        self_sizes  = [d.size for d in self._domain_axes.values()]
        other_sizes = [d.size for d in other._domain_axes.values()]
        
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

        axes_to_items0 = self.axes_to_items()
        axes_to_items1 = other.axes_to_items()
        
        for axes0, items0 in axes_to_items0.iteritems():
            matched_all_items_with_these_axes = False

            len_axes0 = len(axes0) 
            for axes1, items1 in axes_to_items1.items():
                matched_roles = False

                if len_axes0 != len(axes1):
                    # axes1 and axes0 contain differents number of
                    # axes.
                    continue
            
                for role in ('_dimension_coordinates', 
                             '_auxiliary_coordinates', 
                             '_cell_measures',         
                             '_domain_ancillaries',    
                             '_field_ancillaries'):    
                    matched_role = False

                    role_items0 = items0[role]
                    role_items1 = items1[role]

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
                                            atol=atol,
                                            ignore_data_type=ignore_data_type,
                                            ignore_fill_value=ignore_fill_value,
                                            ignore=ignore,
                                            traceback=False):
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

                    del items1[role]
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
                    names = [self.axis_name(axis0) for axis0 in axes0]
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
"Field: Ambiguous axis mapping ({} -> {} and {})".format(
    self.axis_name(axes0), other.axis_name(axis1),
    other.axis_name(axis0_to_axis1[axis0])))
                    return False
                elif axis1 in axis1_to_axis0 and axis0 != axis1_to_axis0[axis1]:
                    if traceback:
                        print(
"Field: Ambiguous axis mapping ({} -> {} and {})".format(
    self.axis_name(axis0), self.axis_name(axis1_to_axis0[axis0]),
    other.axis_name(axes1)))
                    return False

                axis0_to_axis1[axis0] = axis1
                axis1_to_axis0[axis1] = axis0
        #--- End: for     

        #-------------------------------------------------------------
        # Cell methods
        #-------------------------------------------------------------
        if len(self.cell_methods) != len(other.cell_methods):
            if traceback:
                print("Field: Different cell methods: {0!r}, {1!r}".format(
                    self.cell_methods, other.cell_methods))
            return False

        for cm0, cm1 in zip(self.cell_methods.values(),
                            other.cell_methods.values()):
            # Check that there are the same number of axes
            axes0 = cm0.axes
            axes1 = list(cm1.axes)
            if len(cm0.axes) != len(axes1):
                if traceback:
                    print (
"Field: Different cell methods (mismatched axes): {0!r}, {1!r}".format(
    self.cell_methods, other.cell_methods))
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
    self.cell_methods, other.cell_methods))

                        return False
                    elif axis0 == axis1:
                        # Assume that the axes are standard names
                        axes1.remove(axis1)
                        argsort.append(cm1.axes.index(axis1))
                    elif axis1 is None:
                        if traceback:
                            print (
"Field: Different cell methods (undefined axis): {0!r}, {1!r}".format(
    self.cell_methods, other.cell_methods))
                        return False
            #--- End: for

            if len(cm1.axes) != len(argsort):
                if traceback:
                    print ("Field: Different cell methods: {0!r}, {1!r}".format(
                        self.cell_methods, other.cell_methods))
                return False

            cm1 = cm1.copy()
            cm1.sort(argsort=argsort)
            cm1.axes = axes0

            if not cm0.equals(cm1, atol=atol, rtol=rtol,
                              ignore_data_type=ignore_data_type,
                              ignore_fill_value=ignore_fill_value,
                              traceback=traceback):
                if traceback:
                    print ("Field: Different cell methods: {0!r}, {1!r}".format(
                        self.cell_methods, other.cell_methods))
                return False                
        #--- End: for

        # ------------------------------------------------------------
        # Coordinate references
        # ------------------------------------------------------------
        refs1 = other.refs()
        for ref0 in self.refs().values():
            found_match = False
            for key1, ref1 in refs1.items():
                if not ref0.equals(ref1, rtol=rtol, atol=atol,
                                   ignore_data_type=ignore_data_type,
                                   ignore_fill_value=ignore_fill_value, traceback=False):
                    continue

                # Coordinates
                coordinates0 = ref0.coordinates
                coordinates1 = set()
                for value in ref1.coordinates:
                    coordinates1.add(key1_to_key0.get(value, value))
                    
#                coordinates1 = set(
#                    [key1_to_key0.get(other.key(value, role='da'), value)
#                     for value in ref1.coordinates])
                if coordinates0 != coordinates1:
                    continue

                # Domain ancillary terms
                terms0 = ref0.ancillaries
                terms1 = {}
                for key, value in ref1.ancillaries.items():
                    terms1[key] = key1_to_key0.get(value, value))
#                terms0 = dict(
#                    [(term,
#                      self.key(value, role='c', default=value))
#                     for term, value in ref0.ancillaries.iteritems()])
#                terms1 = dict(
#                    [(term,
#                      key1_to_key0.get(other.key(value, role='c'), value))
#                     for term, value in ref1.ancillaries.iteritems()])
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

        # ------------------------------------------------------------
        # Still here? Then the two Constructs are equal
        # ------------------------------------------------------------
        return True
    #--- End: def

    def get(self, key, default=None):
        d = getattr(self, self._construct_type.get(key), None)
        if d is None:
            return default

        return d.get(key, default)
    #--- End: def
    
    def insert_field_ancillary(self, item, key, axes, copy=True):
        if copy:
            item = item.copy()
        self._itemaxes[key] = tuple(axes)
        self._field_ancillaries[key] = item
        self._construct_type[key] = '_field_ancillary'
        
    def insert_auxilary_coordinate(self, item, key, axes, copy=True):
        '''
        '''
        if copy:
            item = item.copy()
        self._item_axes[key] = tuple(axes)
        self._auxiliary_coordinate[key] = item
        self._construct_type[key] = '_auxiliary_coordinate'

    def insert_domain_ancillary(self, item, key, axes, copy=True):
        '''
        '''
        if copy:
            item = item.copy()
        self._item_axes[key] = tuple(axes)
        self._domain_acnillaries[key] = item
        self._construct_type[key] = '_domain_ancillary'
        
    def insert_dimension_coordinate(self, item, key, axes, copy=True):
        '''
        '''
        if copy:
            item = item.copy()
        self._item_axes[key] = tuple(axes)
        self._dimension_cordinates[key] = item
        self._construct_type[key] = '_dimension_coordinate'
        
    def insert_cell_measure(self, item, key, axes, copy=True):
        '''
        '''
        if copy:
            item = item.copy()
        self._item_axes[key] = tuple(axes)
        self._cell_measure[key] = item
        self._construct_type[key] = '_cell_measure'
        
    def insert_coordinate_reference(self, item, key, copy=True):
        if copy:
            item = item.copy()
        self._coordinate_references[key] = item
        self._construct_type[key] = '_coordinate_reference'
        
    def insert_cell_method(self, item, key, copy=True):
        if copy:
            item = item.copy()
        self._cell_methods[key] = item
        self._construct_type[key] = '_cell_method'

    def replace(self, key,  item, axes=None):
        getattr(self, self._construct_type[key])[key] = item
        if axes is not None:
            self._item_axes[key] = tuple(axes)
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
        keys = [x for x in self._construct_type.values()
                if x.startswith(construct_type)]
                    
        n = len(keys)
        key = '{0}{1}'.format(construct_type, n)

        while key in keys:
            n += 1
            key = '{0}{1}'.format(construct_type, n)

        return key
    #--- End: def

    def remove_item(self, key):
        '''
'''
        self._item_axes.pop(key, None)
        return getattr(self, self._construct_type.pop(key)).pop(key, None)
    #--- End: def

#--- End: class
