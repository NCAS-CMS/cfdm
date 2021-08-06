import datetime
import faulthandler
import unittest

faulthandler.enable()  # to debug seg faults and timeouts

import cfdm


class CountTest(unittest.TestCase):
    """Unit test for the Count class."""

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

        self.contiguous = "DSG_timeSeries_contiguous.nc"

    def test_Count__repr__str__dump(self):
        """Test all means of Count inspection."""
        f = cfdm.read(self.contiguous)[0]

        count = f.data.get_count()

        _ = repr(count)
        _ = str(count)
        self.assertIsInstance(count.dump(display=False), str)


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print()
    unittest.main(verbosity=2)
