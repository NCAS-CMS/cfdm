from __future__ import print_function
from __future__ import absolute_import
from builtins import zip
import abc

from . import structure
from future.utils import with_metaclass


class Constructs(with_metaclass(abc.ABCMeta, structure.Constructs)):
    '''
    '''    
    
    def auxiliary_coordinates(self, axes=None, copy=False):
        '''
        '''
        return self.constructs(construct_type='auxiliary_coordinate', axes=axes, copy=copy)
    #--- End: def

    def construct(self, construct_type=None, name=None, axes=None,
                  copy=False):
        '''
        '''
        out = self.constructs(construct_type=construct_type,
                              name=name, axes=axes, copy=copy)

        if not out:
            raise ValueError("No such construct")
        
        key, construct = out.popitem()
        if out:
            raise ValueError("More than one construct meets criteria")
            
        return construct
    #--- End: def

    def constructs(self, name=None, axes=None, construct_type=None,
                   copy=False):
        '''
        '''
        out = super(Constructs, self).constructs(construct_type=construct_type,
                                                 copy=copy)

        if axes is not None:
            spans_axes = set(axes)
            construct_axes = self.construct_axes()
            for key, construct in list(out.items()):
                x = construct_axes.get(key)
                if x is None or not spans_axes.intersection(x):
                    del out[key]
        #--- End: if

        if name is not None:
            (prefix, _, key) = name.partition('%')
            if prefix == 'cfdm':
                construct = out.get(key)
                if construct is not None:
                    out = {key: construct}
                else:
                    out = {}
            else:
                (prefix, _, value) = name.partition(':')
                custom = (prefix,) if value else None
                
                for key, construct in list(out.items()):
                    if name not in construct.name(custom=custom, all_names=True):
                        del out[key]
        #--- End: if
            
        return out
    #--- End: def

    def cell_methods(self, copy=False):
        return self.constructs(construct_type='cell_method', copy=copy)
    #--- End: def
    
    def coordinate_references(self, copy=False):
        return self.constructs(construct_type='coordinate_reference', copy=copy)
    #--- End: def

    def dimension_coordinates(self, axes=None, copy=False):
        return self.constructs(construct_type='dimension_coordinate', axes=axes, copy=copy)
    #--- End: def

    def domain_axis_name(self, axis):
        '''Return the canonical name for an axis.

:Examples 1:

>>> f.domain_axis_name('domainaxis1')
'longitude'

:Parameters:

    axis: `str`
        The identifier of the axis.

          *Example:*
            ``axis='domainaxis2'``

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
        
        for key, dim in self.dimension_coordinates().items():
            if construct_axes[key] == (axis,):
                # Get the name from a dimension coordinate
                name = dim.name(ncvar=False, default=None)
                break
        #--- End: for
        if name is not None:
            return name

        found = False
        for key, aux in self.auxiliary_coordinates().items():
            if construct_axes[key] == (axis,):
                if found:
                    name = None
                    break
                
                # Get the name from an auxiliary coordinate
                name = aux.name(ncvar=False, default=None)
                found = True
        #--- End: for
        if name is not None:
            return name

        ncdim = domain_axes[axis].get_ncdim(None)
        if ncdim is not None:
            # Get the name from a netCDF dimension
            return 'ncdim%{0}'.format(ncdim)

        # Get the name from the identifier
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
        
        axes0_to_axes1 = {}
        axis0_to_axis1 = {}
        axis1_to_axis0 = {}
        key1_to_key0   = {}
        
        # ------------------------------------------------------------
        # Domain axes
        # ------------------------------------------------------------
        if not self._equals_domain_axis(other, rtol=rtol, atol=atol,
                                        traceback=traceback,
                                        axis1_to_axis0=axis1_to_axis0,
                                        key1_to_key0=key1_to_key0,
                                        **kwargs):
            return False
        
        # ------------------------------------------------------------
        # Check the array constructs
        # ------------------------------------------------------------
        axes_to_constructs0 = self.axes_to_constructs()
        axes_to_constructs1 = other.axes_to_constructs()
#        print 'axes_to_constructs0 =', axes_to_constructs0
#        print '\naxes_to_constructs1 =', axes_to_constructs1
        for axes0, constructs0 in axes_to_constructs0.items():
#            print '\n\naxes0 = ', axes0
#            print 'constructs0 = ', constructs0
            matched_all_constructs_with_these_axes = False

            log = []
            
            len_axes0 = len(axes0) 
            for axes1, constructs1 in list(axes_to_constructs1.items()):
                log = []
                constructs1 = constructs1.copy()
#                print '\n    axes1 = ', axes1
#                print '    constructs1 = ', constructs1
                matched_roles = False

                if len_axes0 != len(axes1):
                    # axes1 and axes0 contain differents number of
                    # domain axes.
                    continue

                for construct_type in self._array_constructs:
#                    print '        construct_type =', construct_type
                    matched_role = False
                    role_constructs0 = constructs0[construct_type]
                    role_constructs1 = constructs1[construct_type].copy()

                    if len(role_constructs0) != len(role_constructs1):
                        # There are the different numbers of
                        # constructs of this type
                        matched_all_constructs_with_these_axes = False
                        log.append('Different numbers of '+construct_type)
                        break

                    # Check that there are matching pairs of equal
                    # constructs
                    for key0, item0 in role_constructs0.items():
                        matched_construct = False
                        for key1, item1 in list(role_constructs1.items()):
                            if item0.equals(item1, rtol=rtol,
                                            atol=atol,
                                            traceback=False, **kwargs):
                                del role_constructs1[key1]
                                key1_to_key0[key1] = key0
                                matched_construct = True
                                break
                        #--- End: for

                        if not matched_construct:
                            log.append("Can't match "+construct_type+" "+repr(item0))
                            break
                    #--- End: for

                    if role_constructs1:
                        # At least one construct in other is not equal
                        # to a construct in self
                        break

                    # Still here? Then all constructs of this type
                    # that spanning these axes match
                    del constructs1[construct_type]
                #--- End: for

                matched_all_constructs_with_these_axes = not constructs1

                if matched_all_constructs_with_these_axes:
                    del axes_to_constructs1[axes1]
                    break
            #--- End: for

            if not matched_all_constructs_with_these_axes:
                if traceback:
                    names = [self.domain_axis_name(axis0) for axis0 in axes0]
                    print("Can't match constructs spanning axes {0}".format(names))
                    print('\n'.join(log))
                    print()
                    print(axes_to_constructs0)
                    print()
                    print(axes_to_constructs1)
                return False

            # Map item axes in the two instances
            axes0_to_axes1[axes0] = axes1
        #--- End: for

        for axes0, axes1 in axes0_to_axes1.items():
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

#        # ------------------------------------------------------------
#        #
#        # ------------------------------------------------------------
#        for construct_type in ('dimension_coordinate',
#                               'auxiliary_coordinate',
#                               'domain_ancillary'):
#            found_match = False
#            for key1, y in other.constructs(construct_type).iteritems():
#                x = self.get_construct(key1_to_key0[key1])                
#
##                terms0 = x.cell_extent.domain_ancillaries()
#                terms0 = x.ancillaries()
#                terms1 = {}
##                for term, key in y.cell_extent.domain_ancillaries().items():
#                for term, key in y.ancillaries().items():
#                    terms1[term] = key1_to_key0.get(key, key)
#                    
#                if terms0 != terms1:                    
#                    if traceback:
#                        print(
#"Traceback: No match for {0!r})".format('????'))
#                    return False
#        #--- End: for
        
        # ------------------------------------------------------------
        # Check non-array constructs
        # ------------------------------------------------------------
        for construct_type in self._non_array_constructs:
            if not getattr(self, '_equals_'+construct_type)(
                    other,
                    rtol=rtol, atol=atol,
                    traceback=traceback,
                    axis1_to_axis0=axis1_to_axis0,
                    key1_to_key0=key1_to_key0, **kwargs):
                return False

        # ------------------------------------------------------------
        # Still here? Then the two objects are equal
        # ------------------------------------------------------------     
        return True
    #--- End: def
    
    def _equals_coordinate_reference(self, other, rtol=None, atol=None,
                                     traceback=False,
                                     axis1_to_axis0=None,
                                     key1_to_key0=None, **kwargs):
        '''
        '''
        refs0 = self.coordinate_references()
        refs1 = other.coordinate_references()

        if len(refs0) != len(refs1):
            if traceback:
                print(
"Traceback: Different coordinate references: {0!r}, {1!r}".format(
    list(refs0.values()), list(refs1.values())))
            return False

        if refs0:
            for ref0 in list(refs0.values()):
                found_match = False
                for key1, ref1 in list(refs1.items()):
                    if not ref0.equals(ref1, rtol=rtol, atol=atol,
                                       traceback=False, **kwargs): ####
                        continue

                    # Coordinates
                    coordinates0 = ref0.coordinates()
                    coordinates1 = set()
                    for value in ref1.coordinates():
                        coordinates1.add(key1_to_key0.get(value, value))
                        
                    if coordinates0 != coordinates1:
                        continue
    
                    # Domain ancillary-valued coordinate conversion terms
                    terms0 = ref0.coordinate_conversion.domain_ancillaries()
                    terms1 = {}
                    for term, key in list(ref1.coordinate_conversion.domain_ancillaries().items()):
                        terms1[term] = key1_to_key0.get(key, key)
    
                    if terms0 != terms1:
                        continue
    
#                    # Domain ancillary-valued datum terms
#                    terms0 = ref0.datum.domain_ancillaries()
#                    terms1 = {}
#                    for term, key in ref1.datum.domain_ancillaries().items():
#                        terms1[term] = key1_to_key0.get(key, key)
#    
#                    if terms0 != terms1:
#                        continue
    
                    found_match = True
                    del refs1[key1]                                       
                    break
                #--- End: for
    
                if not found_match:
                    if traceback:
                        print(
"Traceback: No match for {0!r})".format(ref0))
                    return False
            #--- End: for
        #--- End: if

        return True
    #--- End: def

    def _equals_cell_method(self, other, rtol=None, atol=None,
                            traceback=False, axis1_to_axis0=None,
                            key1_to_key0=None, **kwargs):
        '''
        
        '''
        cell_methods0 = self.cell_methods()
        cell_methods1 = other.cell_methods()

        if len(cell_methods0) != len(cell_methods1):
            if traceback:
                print(
"Traceback: Different numbers of cell methods: {0!r}, {1!r}".format(
    cell_methods0, cell_methods1))
            return False
        
        axis0_to_axis1 = {}
        for axis0, axis1 in axis1_to_axis0.items():
            axis0_to_axis1[axis0] = axis1
            
        for cm0, cm1 in zip(list(cell_methods0.values()),
                            list(cell_methods1.values())):
            # Check that there are the same number of axes
            axes0 = cm0.get_axes(())
            axes1 = list(cm1.get_axes(()))
            if len(axes0) != len(axes1):
                if traceback:
                    print (
"{0}: Different cell methods (mismatched axes): {1!r}, {2!r}".format(
    cm0.__class__.__name__, cell_methods0, cell_methods1))
                return False
    
            indices = []
            for axis0 in axes0:
                if axis0 is None:
                    return False
                for axis1 in axes1:
                    if axis0 in axis0_to_axis1 and axis1 in axis1_to_axis0:
                        if axis1 == axis0_to_axis1[axis0]:
                            axes1.remove(axis1)
                            indices.append(cm1.get_axes(()).index(axis1))
                            break
                    elif axis0 in axis0_to_axis1 or axis1 in axis1_to_axis0:
                        if traceback:
                            print (
"Traceback: Different cell methods (mismatched axes): {0!r}, {1!r}".format(
    cell_methods0, cell_methods1))
                        return False
                    elif axis0 == axis1:
                        # Assume that the axes are standard names
                        axes1.remove(axis1)
                        indices.append(cm1.get_axes(()).index(axis1))
                    elif axis1 is None:
                        if traceback:
                            print (
"Traceback: Different cell methods (undefined axis): {0!r}, {1!r}".format(
    cell_methods0, cell_methods1))
                        return False
            #--- End: for

            if len(cm1.get_axes(())) != len(indices):
                if traceback:
                    print ("Field: Different cell methods: {0!r}, {1!r}".format(
                        cell_methods0, cell_methods1))
                return False

            cm1 = cm1.sorted(indices=indices)
            cm1.set_axes(axes0)

            if not cm0.equals(cm1, atol=atol, rtol=rtol,
                              traceback=traceback, **kwargs):
                if traceback:
                    print (
"Traceback: Different cell methods: {0!r}, {1!r}".format(
    cell_methods0, cell_methods1))
                return False                
        #--- End: for

        return True
    #--- End: def

    def _equals_domain_axis(self, other, rtol=None, atol=None,
                            traceback=False, axis1_to_axis0=None,
                            key1_to_key0=None, **kwargs):
        '''
        '''
        # ------------------------------------------------------------
        # Domain axes
        # ------------------------------------------------------------
        self_sizes  = [d.get_size() for d in list(self.domain_axes().values())]
        other_sizes = [d.get_size() for d in list(other.domain_axes().values())]
        
        if sorted(self_sizes) != sorted(other_sizes):
            # There is not a 1-1 correspondence between axis sizes
            if traceback:
                print("{0}: Different domain axes: {1} != {2}".format(
                    self.__class__.__name__,
                    sorted(self.values()),
                    sorted(other.values())))
            return False

        return True
    #--- End: def
    
#--- End: class
