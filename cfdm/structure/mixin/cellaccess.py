import abc

class CellAccess(object):
    '''

    '''
    __metaclass__ = abc.ABCMeta

    @property
    def bounds(self):
        '''
        '''
        return self.get_bounds()
    #--- End: def

    @property
    def cell_extent(self):
        '''
        '''
        cell_extent = self.get_cell_extent(None)
        if cell_extent is None:
            cell_extent = self._CellExtent(domain_ancillaries={},
                                           parameters={})
            self.set_cell_extent(cell_extent, copy=False)
            
        return cell_extent
    #--- End: def

#--- End: class
