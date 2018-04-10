from abstract import Implementation


class CFDMImplementation(Implementation):
    '''
    '''
    def __init__(self, NetCDF=None, AuxiliaryCoordinate=None,
                 CellMeasure=None, CellMethod=None,
                 CoordinateAncillary=None ,CoordinateReference=None,
                 DimensionCoordinate=None, DomainAncillary=None,
                 DomainAxis=None, Field=None, FieldAncillary=None,
                 Bounds=None, Data=None, GatheredArray=None):
#                 Conventions=None):
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

        '''
        super(CFDMImplementation, self).__init__(
            NetCDF=NetCDF,
            AuxiliaryCoordinate=AuxiliaryCoordinate,
            CellMeasure=CellMeasure,
            CellMethod=CellMethod,
            CoordinateAncillary=CoordinateAncillary,
            CoordinateReference=CoordinateReference,
            DimensionCoordinate=DimensionCoordinate,
            DomainAncillary=DomainAncillary,
            DomainAxis=DomainAxis,
            Field=Field,
            FieldAncillary=FieldAncillary,
            Bounds=Bounds,
            Data=Data,
            GatheredArray=GatheredArray)
#            Conventions=Conventions)
    #--- End: def
