from builtins import super

from .abstract import Implementation


class CFDMImplementation(Implementation):
    '''
    '''
    def __init__(self, version=None,
                 AuxiliaryCoordinate=None,
                 CellMeasure=None,
                 CellMethod=None,
                 CoordinateAncillary=None,
                 CoordinateReference=None,
                 DimensionCoordinate=None,
                 DomainAncillary=None,
                 DomainAxis=None,
                 Field=None,
                 FieldAncillary=None,
                 Bounds=None,
                 Data=None,
                 CompressedArray=None,
                 GatheredArray=None,
                 NetCDFArray=None,
                 RaggedContiguousArray=None,
                 RaggedIndexedArray=None,
                 RaggedIndexedContiguousArray=None,
    ):
        '''**Initialisation**

:Parameters:

    AuxiliaryCoordinate:
        An auxiliary coordinate construct class.

    CellMeasure:
        A cell measure construct class.

    CellMethod:
        A cell method construct class.

    CoordinateReference:
        A coordinate reference construct class.

    DimensionCoordinate:
        A dimension coordinate construct class.

    DomainAncillary:
        A domain ancillary construct class.

    DomainAxis:
        A domain axis construct class.

    Field:
        A field construct class.

    FieldAncillary:
        A field ancillary construct class.

    Bounds:              = Bounds
    CoordinateAncillary = CoordinateAncillary
    Data                = Data
    NetCDF              = NetCDF
    CompressedArray     = CompressedArray

        '''
        super().__init__(
            version=version,
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
            CompressedArray=CompressedArray,
            GatheredArray=GatheredArray,
            NetCDFArray=NetCDFArray,
            RaggedContiguousArray=RaggedContiguousArray,
            RaggedIndexedArray=RaggedIndexedArray,
            RaggedIndexedContiguousArray=RaggedIndexedContiguousArray,
        )
    #--- End: def

#--- End: class

