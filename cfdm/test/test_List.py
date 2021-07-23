import datetime
import faulthandler
import unittest

faulthandler.enable()  # to debug seg faults and timeouts

import cfdm


class ListTest(unittest.TestCase):
    """Unit test for the List class."""

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

        self.gathered = "gathered.nc"

    def test_List__repr__str__dump(self):
        """Test all means of List inspection."""
        f = cfdm.read(self.gathered)[0]

        list_ = f.data.get_list()

        _ = repr(list_)
        _ = str(list_)
        self.assertIsInstance(list_.dump(display=False), str)


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print()
    unittest.main(verbosity=2)
