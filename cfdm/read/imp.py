

class xxxF(object):
    '''
    '''
    def __init__(self, NetCDF=None, AuxiliaryCoordinate=None,
                 CellMeasure=None, CellMethod=None,
                 CoordinateAncillary=None ,CoordinateReference=None,
                 DimensionCoordinate=None, DomainAncillary=None,
                 DomainAxis=None, Field=None, FieldAncillary=None,
                 Bounds=None, Data=None, GatheredArray=None):
        '''
        '''
        self.Bounds              = Bounds
        self.CoordinateAncillary = CoordinateAncillary
        self.Data                = Data
        self.NetCDF              = NetCDF
        self.GatheredArray       = GatheredArray

        # CF data model constructs
        self.AuxiliaryCoordinate = AuxiliaryCoordinate
        self.CellMeasure         = CellMeasure
        self.CellMethod          = CellMethod
        self.CoordinateReference = CoordinateReference
        self.DimensionCoordinate = DimensionCoordinate
        self.DomainAncillary     = DomainAncillary
        self.DomainAxis          = DomainAxis
        self.Field               = Field         
        self.FieldAncillary      = FieldAncillary
 
