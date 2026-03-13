import datetime
import faulthandler
import unittest

faulthandler.enable()  # to debug seg faults and timeouts

import cfdm


class xarrayTest(unittest.TestCase):
    """Unit test for converting to xarray."""

    def setUp(self):
        """Preparations called immediately before each test method."""
        # Disable log messages to silence expected warnings
        cfdm.log_level("DISABLE")
        # Note: to enable all messages for given methods, lines or
        # calls (those without a 'verbose' option to do the same)
        # e.g. to debug them, wrap them (for methods, start-to-end
        # internally) as follows:
        #
        # cfdm.LOG_LEVEL('DEBUG')
        # < ... test code ... >
        # cfdm.log_level('DISABLE')

    def test_Field_to_xarray(self):
        """Test Field.to_xarray."""
        examples = cfdm.example_fields()

        for i, f in enumerate(examples):
            if i == 6:
                # Can't yet convert cell geometries
                with self.assertRaises(NotImplementedError):
                    f.to_xarray()
            else:
                ds = f.to_xarray()
                str(ds)
                self.assertIn("Conventions", ds.attrs)


    def test_Domain_to_xarray(self):
        """Test Domain.to_xarray."""
        examples = cfdm.example_fields()

        for i, f in enumerate(examples):
            f = f.domain            
            if i == 6:
                # Can't yet convert cell geometries
                with self.assertRaises(NotImplementedError):
                    f.to_xarray()
            else:
                ds = f.to_xarray()
                str(ds)


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print("")
    unittest.main(verbosity=2)
