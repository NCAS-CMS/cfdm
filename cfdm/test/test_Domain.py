import datetime
import os
import unittest

import faulthandler

faulthandler.enable()  # to debug seg faults and timeouts

import cfdm


class DomainTest(unittest.TestCase):
    """TODO DOCS."""

    def setUp(self):
        """TODO DOCS."""
        # Disable log messages to silence expected warnings
        cfdm.LOG_LEVEL("DISABLE")
        # Note: to enable all messages for given methods, lines or
        # calls (those without a 'verbose' option to do the same)
        # e.g. to debug them, wrap them (for methods, start-to-end
        # internally) as follows:
        #
        # cfdm.LOG_LEVEL('DEBUG')
        # < ... test code ... >
        # cfdm.log_level('DISABLE')

        self.filename = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "test_file.nc"
        )
        f = cfdm.read(self.filename)
        self.assertEqual(len(f), 1, "f={!r}".format(f))
        self.f = f[0]

    def test_Domain__repr__str__dump(self):
        """TODO DOCS."""
        d = self.f.domain

        _ = repr(d)
        _ = str(d)
        self.assertIsInstance(d.dump(display=False), str)

    def test_Domain_equals(self):
        """TODO DOCS."""
        f = self.f

        d = f.domain
        e = d.copy()

        self.assertTrue(d.equals(d, verbose=3))
        self.assertTrue(d.equals(e, verbose=3))
        self.assertTrue(e.equals(d, verbose=3))


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print("")
    unittest.main(verbosity=2)
