import atexit
import datetime
import faulthandler
import os
import tempfile
import unittest

import numpy as np
import umfive

faulthandler.enable()  # to debug seg faults and timeouts

import cfdm

n_tmpfiles = 1
tmpfiles = [
    tempfile.mkstemp("_test_pp.nc", dir=os.getcwd())[1]
    for i in range(n_tmpfiles)
]
[tmpfile] = tmpfiles


def _remove_tmpfiles():
    """Try to remove defined temporary files by deleting their paths."""
    for f in tmpfiles:
        try:
            os.remove(f)
        except OSError:
            pass


atexit.register(_remove_tmpfiles)


class ppTest(unittest.TestCase):  # noqa: D101
    ppfile = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "wgdos_packed.pp"
    )

    ppextradata = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "extra_data.pp"
    )

    new_table = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "new_STASH_to_CF.txt"
    )
    text_file = open(new_table, "w")
    text_file.write(
        "1!30201!long name                           !Pa!!!NEW_NAME!!"
    )
    text_file.close()

    def test_PP_read_um(self):  # noqa: D102
        f = cfdm.read(self.ppextradata)[0]

        g = cfdm.read(self.ppextradata)[0]
        self.assertTrue(f.equals(g))

        g = cfdm.read(self.ppextradata, um={"um_version": "4.5"})[0]
        self.assertTrue(f.equals(g))

        p = cfdm.read("wgdos_packed.pp")[0]
        p0 = cfdm.read(
            "wgdos_packed.pp",
            um={"um_version": "4.5", "height_at_top_of_model": 23423.65},
        )[0]

        self.assertTrue(p.equals(p0))

    def test_load_stash2standard_name(self):  # noqa: D102
        f = cfdm.read(self.ppfile)[0]
        self.assertEqual(f.identity(), "eastward_wind")
        self.assertEqual(f.data.Units, cfdm.Units("m s-1"))

        for merge in (True, False):
            umfive.load_stash_table(self.new_table, merge=merge)
            f = cfdm.read(self.ppfile)[0]
            self.assertEqual(f.identity(), "NEW_NAME")
            self.assertEqual(f.data.Units, cfdm.Units("Pa"))
            umfive.stash_table(reset=True)
            f = cfdm.read(self.ppfile)[0]
            self.assertEqual(f.identity(), "eastward_wind")
            self.assertEqual(f.data.Units, cfdm.Units("m s-1"))

        umfive.stash_table(reset=True)

    def test_PP_read_select(self):  # noqa: D102
        f = cfdm.read(self.ppfile, select="lbproc=0")
        self.assertEqual(len(f), 1)

    def test_PP_WGDOS_UNPACKING(self):  # noqa: D102
        f = cfdm.read(self.ppfile)[0]

        self.assertEqual(f.array.mean(), 3.8080420658506196)

        array = f.array

        f = cfdm.read(self.ppfile)[0]

        for cfa in (None, "auto"):
            cfdm.write(f, tmpfile, cfa=cfa)
            g = cfdm.read(tmpfile)[0]

            self.assertTrue((f.array == array).all())
            self.assertTrue(f.equals(g))

    def test_PP_extra_data(self):  # noqa: D102
        f = cfdm.read(self.ppextradata)[0]

        self.assertEqual(len(f.dimension_coordinates()), 3)
        self.assertEqual(len(f.auxiliary_coordinates()), 3)

        sites = f.dimension_coordinate("long_name=site")
        self.assertTrue(np.allclose(sites, [1, 2, 3]))

        regions = f.auxiliary_coordinate("region")
        self.assertEqual(
            regions.array.tolist(),
            ["Northern Hemisphere", "Southern Hemisphere", "Global"],
        )

        self.assertTrue(f.dimension_coordinate("height", default=False))
        self.assertTrue(f.dimension_coordinate("time", default=False))
        self.assertTrue(f.auxiliary_coordinate("longitude", default=False))

    def test_PP_um_version(self):  # noqa: D102
        f = cfdm.read(self.ppfile)[0]
        self.assertEqual(f.get_property("um_version"), "11.0")

        f = cfdm.read(self.ppfile, um={"um_version": "6.6.3"})[0]
        self.assertEqual(f.get_property("um_version"), "6.6.3")

    def test_PP_file_object(self):  # noqa: D102
        # Can't yet read PP/UM from file-like objects
        with open(self.ppfile, "rb") as fh:
            cfdm.read(fh)

            # Check that the file has been rewound
            self.assertEqual(fh.tell(), 0)


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print()
    unittest.main(verbosity=2)
