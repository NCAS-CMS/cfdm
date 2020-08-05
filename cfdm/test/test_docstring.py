import datetime
import unittest

import cfdm


class DocstringTest(unittest.TestCase):
    def setUp(self):
        self.package = 'cfdm'
        self.repr = ''
        self.subclasses_of_Container = (
            cfdm.Field,
            cfdm.AuxiliaryCoordinate,
            cfdm.DimensionCoordinate,
            cfdm.DomainAncillary,
            cfdm.FieldAncillary,
            cfdm.CellMeasure,
            cfdm.DomainAxis,
            cfdm.CoordinateReference,
            cfdm.CellMethod,

            cfdm.NodeCountProperties,
            cfdm.PartNodeCountProperties,
            cfdm.Bounds,
            cfdm.InteriorRing,
            cfdm.List,
            cfdm.Index,
            cfdm.Count,

            cfdm.Data,
            cfdm.NetCDFArray,
            cfdm.NumpyArray,
            cfdm.GatheredArray,
            cfdm.RaggedContiguousArray,
            cfdm.RaggedIndexedArray,
            cfdm.RaggedIndexedContiguousArray,

            cfdm.core.mixin.Properties,
            cfdm.core.mixin.PropertiesData,
            cfdm.core.mixin.PropertiesDataBounds,
            cfdm.core.mixin.Coordinate,
            
        )
        self.subclasses_of_Properties = (
            cfdm.Field,
            cfdm.AuxiliaryCoordinate,
            cfdm.DimensionCoordinate,
            cfdm.DomainAncillary,
            cfdm.FieldAncillary,
            cfdm.CellMeasure,
            cfdm.NodeCountProperties,
            cfdm.PartNodeCountProperties,
            cfdm.Bounds,
            cfdm.InteriorRing,
            cfdm.List,
            cfdm.Index,
            cfdm.Count,
        )
        self.subclasses_of_PropertiesData = (
            cfdm.Field,
            cfdm.AuxiliaryCoordinate,
            cfdm.DimensionCoordinate,
            cfdm.DomainAncillary,
            cfdm.FieldAncillary,
            cfdm.CellMeasure,
            cfdm.Bounds,
            cfdm.InteriorRing,
            cfdm.List,
            cfdm.Index,
            cfdm.Count,
        )
        self.subclasses_of_PropertiesDataBounds = (
            cfdm.AuxiliaryCoordinate,
            cfdm.DimensionCoordinate,
            cfdm.DomainAncillary,
        )

    def test_docstring(self):
        # Test that all {{ occurences have been substituted
        for klass in self.subclasses_of_Container:
            for x in (klass, klass()):
                for name in dir(x):
                    if name.startswith('__'):
                        continue
                    
                    f = getattr(klass, name, None)
                    if f is None or not hasattr(f, '__doc__'):
                        continue
                    
                    self.assertIsNotNone(f.__doc__,
                                         '\nCLASS: {}\nMETHOD NAME: {}\nMETHOD: {}\n__doc__: {}'.format(
                                             klass, name, f, f.__doc__))
                    
                    self.assertNotIn('{{', f.__doc__,
                                     '\nCLASS: {}\nMETHOD NAME: {}\nMETHOD: {}'.format(klass, name, f))

    def test_docstring_package(self):
        string = '>>> f = {}.'.format(self.package)
        for klass in self.subclasses_of_Container:
            for x in (klass, klass()):
                self.assertIn(string, x._has_component.__doc__, klass)

        string = '>>> f = {}.'.format(self.package)
        for klass in self.subclasses_of_Properties:
            for x in (klass, klass()):
                self.assertIn(string, x.clear_properties.__doc__, klass)

    def test_docstring_class(self):
        for klass in self.subclasses_of_Properties:
            string = '>>> f = {}.{}'.format(self.package, klass.__name__)
            for x in (klass, klass()):
                self.assertIn(string, x.clear_properties.__doc__, klass)

        for klass in self.subclasses_of_Container:
            string = klass.__name__
            for x in (klass, klass()):
                self.assertIn(string, x.copy.__doc__, klass)

    def test_docstring_plus_class(self):
        string = '>>> d = {}.{}'.format(self.package, 'Data')
        for klass in self.subclasses_of_PropertiesData:
            for x in (klass, klass()):
                self.assertIn(string, x.has_data.__doc__, klass)

    def test_docstring_repr(self):
        string = '<{}Data'.format(self.repr)
        for klass in self.subclasses_of_PropertiesData:
            for x in (klass, klass()):
                self.assertIn(string, x.has_data.__doc__, klass)

    def test_docstring_default(self):
        string = 'Return the value of the *default* parameter'
        for klass in self.subclasses_of_Properties:
            for x in (klass, klass()):
                self.assertIn(string, x.del_property.__doc__, klass)

# --- End: class


if __name__ == '__main__':
    print('Run date:', datetime.datetime.now())
    cfdm.environment()
    print('')
    unittest.main(verbosity=2)
