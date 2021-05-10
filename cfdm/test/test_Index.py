import datetime
import unittest

import faulthandler

faulthandler.enable()  # to debug seg faults and timeouts

import cfdm


class IndexTest(unittest.TestCase):
    """TODO DOCS."""

    def setUp(self):
        """TODO DOCS."""
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

        self.indexed = "DSG_timeSeries_indexed.nc"

    def test_Index__repr__str__dump(self):
        """TODO DOCS."""
        f = cfdm.read(self.indexed)[0]

        index = f.data.get_index()

        _ = repr(index)
        _ = str(index)
        self.assertIsInstance(index.dump(display=False), str)


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print()
    unittest.main(verbosity=2)
