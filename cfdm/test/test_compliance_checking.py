import atexit
import datetime
import faulthandler
import os
from pprint import pprint
import tempfile
import unittest

from netCDF4 import Dataset
from urllib import request

faulthandler.enable()  # to debug seg faults and timeouts

import cfdm


n_tmpfiles = 1
tmpfiles = [
    tempfile.mkstemp("_test_compliance_check.nc", dir=os.getcwd())[1]
    for i in range(n_tmpfiles)
]
(
    tmpfile0,
) = tmpfiles


def _remove_tmpfiles():
    """Remove temporary files created during tests."""
    for f in tmpfiles:
        try:
            os.remove(f)
        except OSError:
            pass


atexit.register(_remove_tmpfiles)


def _create_noncompliant_names_field(compliant_field, temp_file):
    """Create a copy of a field with bad standard names on all variables."""
    cfdm.write(compliant_field, temp_file)

    with Dataset(temp_file, "r+") as nc:
        field_all_varnames = list(nc.variables.keys())
        # Store a bad name which is the variable name prepended with 'badname_'
        # - this makes it a certain invalid name and one we can identify as
        # being tied to the original variable, for testing purposes.
        bad_name_mapping = {
            varname: "badname_" + varname for varname in field_all_varnames
        }

        for var_name, bad_std_name in bad_name_mapping.items():
            var = nc.variables[var_name]
            var.standard_name = bad_std_name

    return cfdm.read(temp_file)[0]


class ComplianceCheckingTest(unittest.TestCase):
    """Test CF Conventions compliance checking functionality."""

    # 1. Create a file with field with invalid standard names generally
    # using our 'kitchen sink' field as a basis
    good_snames_general_field = cfdm.example_field(1)
    # TODO set bad names and then write to tempfile and read back in
    bad_snames_general_field = _create_noncompliant_names_field(
        good_snames_general_field, tmpfile0)

    # 1. Create a file with a UGRID field with invalid standard names
    # on UGRID components, using our core 'UGRID 1' field as a basis
    ugrid_file_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "ugrid_1.nc"
    )
    good_ugrid_sn_f = cfdm.read(ugrid_file_path)[0]
    # Note we can't write UGRID files using cf at the moment, so needed
    # another way to create UGRID dataset with bad names to test on
    # and the simplest is to write extra 'bad names' file alongside
    # 'ugrid_1.nc' in create_test_files module.
    bad_names_ugrid_file_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "ugrid_1_bad_names.nc"
    )
    bad_ugrid_sn_fields = cfdm.read(bad_names_ugrid_file_path)

    bad_sn_expected_reason = (
        "standard_name attribute has a value that is not a "
        "valid name contained in the current standard name table"
    )
    bad_sn_expected_code = 400022

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

    def test_extract_names_from_xml(self):
        """Test the `conformance._extract_names_from_xml` function."""
        # Check with a small 'dummy' XML table which is the current table
        # but with only the first two names included, w/ or w/o a few aliases
        # (note the aliases don't match up to the two included names but
        # this is irrelevant to the testing so OK)
        two_name_table_start = """<?xml version="1.0"?>
            <standard_name_table xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="https://cfconventions.org/Data/schema-files/cf-standard-name-table-2.0.xsd">
            <version_number>92</version_number>
            <conventions>CF-StandardNameTable-92</conventions>
            <first_published>2025-07-24T14:20:46Z</first_published>
            <last_modified>2025-07-24T14:20:46Z</last_modified>
            <institution>Centre for Environmental Data Analysis</institution>
            <contact>support@ceda.ac.uk</contact>


            <entry id="acoustic_area_backscattering_strength_in_sea_water">
               <canonical_units>1</canonical_units>
               <description>Acoustic area backscattering strength is 10 times the log10 of the ratio of the area backscattering coefficient to the reference value, 1 (m2 m-2). Area backscattering coefficient is the integral of the volume backscattering coefficient over a defined distance. Volume backscattering coefficient is the linear form of acoustic_volume_backscattering_strength_in_sea_water. For further details see MacLennan et. al (2002) doi:10.1006/jmsc.2001.1158.</description>
            </entry>

            <entry id="acoustic_centre_of_mass_in_sea_water">
               <canonical_units>m</canonical_units>
               <description>Acoustic centre of mass is the average of all sampled depths weighted by their volume backscattering coefficient. Volume backscattering coefficient is the linear form of acoustic_volume_backscattering_strength_in_sea_water. For further details see Urmy et. al (2012) doi:10.1093/icesjms/fsr205.</description>
            </entry>
        """
        include_two_aliases = """<alias id="chlorophyll_concentration_in_sea_water">
              <entry_id>mass_concentration_of_chlorophyll_in_sea_water</entry_id>

            </alias>

            <alias id="concentration_of_chlorophyll_in_sea_water">
              <entry_id>mass_concentration_of_chlorophyll_in_sea_water</entry_id>

            </alias>
        """
        table_end = "</standard_name_table>"

        two_name_output = cfdm.conformance._extract_names_from_xml(
            two_name_table_start + table_end, include_aliases=False)
        self.assertIsInstance(two_name_output, list)
        self.assertEqual(len(two_name_output), 2)
        self.assertIn(
            "acoustic_area_backscattering_strength_in_sea_water",
            two_name_output
        )
        self.assertIn(
            "acoustic_centre_of_mass_in_sea_water", two_name_output)

        # No aliases in this table therefore expect same output as before
        # when setting 'include_aliases=True'
        self.assertEqual(
            cfdm.conformance._extract_names_from_xml(
                two_name_table_start + table_end, include_aliases=True),
            two_name_output
        )

        aliases_inc_output = cfdm.conformance._extract_names_from_xml(
            two_name_table_start + include_two_aliases + table_end,
            include_aliases=True
        )
        self.assertIsInstance(aliases_inc_output, list)
        self.assertEqual(len(aliases_inc_output), 4)
        # Check all non-aliases are there, as per above output
        self.assertTrue(set(two_name_output).issubset(aliases_inc_output))
        # Also should have the aliases this time
        self.assertIn(
            "chlorophyll_concentration_in_sea_water",
            aliases_inc_output
        )
        self.assertIn(
            "concentration_of_chlorophyll_in_sea_water",
            aliases_inc_output
        )

        # When setting 'include_aliases=True' should ignore the two aliases
        # in table so expect same as two_name_output
        self.assertEqual(
            cfdm.conformance._extract_names_from_xml(
                two_name_table_start + include_two_aliases + table_end,
                include_aliases=False
            ),
            two_name_output
        )

    def test_get_all_current_standard_names(self):
        """Test the `conformance.get_all_current_standard_names` function."""
        # First check the URL used is actually available in case of issues
        # arising in case GitHub endpoints go down
        sn_xml_url = cfdm.conformance._STD_NAME_CURRENT_XML_URL
        with request.urlopen(sn_xml_url) as response:
            self.assertEqual(
                response.status, 200,
                "Standard name XML inaccesible: unexpected status code "
                f"{response.status} for reference URL of: {sn_xml_url}"
            )  # 200 == OK
        # SLB-DH discuss TODO: what behaviour do we want for the (v. rare)
        # case that the URL isn't accessible? Ideally we can skip standard
        # name validation with a warning, in these cases.

        output = cfdm.conformance.get_all_current_standard_names()
        self.assertIsInstance(output, list)

        # The function gets the current table so we can't know exactly how
        # many names there will be there going forward, but given there are
        # over 4500 names (~4900 at time of writing, Aug 2025) and there is
        # a general upward trend with names rarely removed, we can safely
        # assume the list is at least 4500 names long and test on this in
        # lieu of changing exact size.
        self.assertTrue(len(output) > 4500)

        # Check some known names which won't ever be removed are in there
        self.assertIn("longitude", output)
        self.assertIn("latitude", output)
        self.assertIn("time", output)

        # Check a long name with plenty of underscores is in there too
        self.assertIn(
            "integral_wrt_time_of_radioactivity_concentration_of_113Cd_in_air",
            output
        )

        # Check a standard name with known alias
        self.assertIn("atmosphere_moles_of_cfc113", output)
        # Since the default behaviour is to not include aliases, this alias
        # of the above should not be in the list
        self.assertNotIn("moles_of_cfc113_in_atmosphere", output)

        aliases_inc_output = cfdm.conformance.get_all_current_standard_names(
            include_aliases=True
        )
        self.assertIsInstance(aliases_inc_output, list)

        # As with above length check, can't be sure of eact amount as it
        # changes but we can safely put a lower limit on it. At time of
        # writing, Aug 2025) there are over 5500 names including aliases
        # (where there are ~500 aliases as opposed to non-alias names) so
        # set 5000 as a good limit (> 4500 check w/ include_aliases=False)
        self.assertTrue(len(aliases_inc_output) > 5000)

        # Check all non-aliases are there, as above
        self.assertTrue(set(output).issubset(aliases_inc_output))

        # This time the alias should be included
        self.assertIn("moles_of_cfc113_in_atmosphere", aliases_inc_output)

    def test_standard_names_validation_compliant_field(self):
        """Test compliance checking on a compliant non-UGRID field."""
        f = self.good_snames_general_field
        dc_output = f.dataset_compliance()
        self.assertEqual(dc_output, dict())

    def test_standard_names_validation_noncompliant_field(self):
        """Test compliance checking on a non-compliant non-UGRID field."""
        f = self.bad_snames_general_field
        cfdm.write(f, "kitchen-sink-field.-bad-names.nc")
        dc_output = f.dataset_compliance()

        print("----------------- TEST 1 NON UGRID ---------------------")
        pprint(dc_output)

        # TODO

    def test_standard_names_validation_compliant_ugrid_field(self):
        """Test compliance checking on a compliant UGRID field."""
        f = self.good_ugrid_sn_f
        dc_output = f.dataset_compliance()
        self.assertEqual(dc_output, dict())

    def test_standard_names_validation_noncompliant_ugrid_fields(self):
        """Test compliance checking on non-compliant UGRID fields."""
        # SLB DEV
        # TODO add error to run to say need to run 'create_test_files'

        # Fields for testing on: those in ugrid_1 with bad names pre-set
        f1, f2, f3 = self.bad_ugrid_sn_fields  # unpack to shorter names
        dc_output_1 = f1.dataset_compliance()
        dc_output_2 = f2.dataset_compliance()
        dc_output_3 = f3.dataset_compliance()

        print("----------------- TEST 2 UGRID ---------------------")
        pprint(dc_output_1)

        # TODO see from below that not all bad names get set - but want
        # that, so should update create_test_files method to set on all
        # for bad case.
        with Dataset("ugrid_1_bad_names.nc", "r+") as nc:
            for varname, var in nc.variables.items():
                print(varname, getattr(var, "standard_name", "No standard_name"))

        # =======================================================
        # Field 1/3: top-level dict (1/4)
        # =======================================================
        self.assertIsInstance(dc_output_1, dict)
        self.assertCountEqual(dc_output_1.keys(), ["pa"])

        pa = dc_output_1["pa"]
        self.assertIsInstance(pa, dict)
        self.assertCountEqual(pa.keys(), ["attributes", "dimensions"])

        # pa.dimensions
        pa_dimensions = pa["dimensions"]
        self.assertIsInstance(pa_dimensions, dict)
        self.assertCountEqual(pa_dimensions.keys(), ["nMesh2_node", "time"])
        self.assertEqual(pa_dimensions["nMesh2_node"], {"size": 7})
        self.assertEqual(pa_dimensions["time"], {"size": 2})

        # pa.attributes
        pa_attributes = pa["attributes"]
        self.assertIsInstance(pa_attributes, dict)
        self.assertCountEqual(pa_attributes.keys(), ["mesh", "standard_name"])

        # pa.attributes.standard_name (1/4)
        pa_standard_name = pa_attributes["standard_name"]
        self.assertIsInstance(pa_standard_name, list)
        self.assertEqual(len(pa_standard_name), 1)

        self.assertEqual(
            pa_standard_name[0],
            {
                "code": self.bad_sn_expected_code,
                "reason": self.bad_sn_expected_reason,
                "value": "badname_Mesh2",
            },
        )

        # pa.attributes.mesh
        mesh = pa_attributes["mesh"]
        self.assertIsInstance(mesh, dict)
        self.assertCountEqual(mesh.keys(), ["dimensions", "variables"])

        # mesh.dimensions
        mesh_dimensions = mesh["dimensions"]
        self.assertIsInstance(mesh_dimensions, dict)
        self.assertCountEqual(mesh_dimensions.keys(), ["nMesh2_node", "time"])
        self.assertEqual(mesh_dimensions["nMesh2_node"], {"size": 7})
        self.assertEqual(mesh_dimensions["time"], {"size": 2})

        # mesh.variables
        mesh_variables = mesh["variables"]
        self.assertIsInstance(mesh_variables, dict)
        self.assertCountEqual(mesh_variables.keys(), ["Mesh2"])

        mesh2 = mesh_variables["Mesh2"]
        self.assertIsInstance(mesh2, dict)
        self.assertCountEqual(mesh2.keys(), ["attributes", "dimensions"])

        # Mesh2.dimensions
        self.assertEqual(mesh2["dimensions"], {})

        # Mesh2.attributes
        mesh2_attributes = mesh2["attributes"]
        self.assertIsInstance(mesh2_attributes, dict)
        self.assertCountEqual(
            mesh2_attributes.keys(),
            [
                "edge_node_connectivity",
                "face_face_connectivity",
                "face_node_connectivity",
            ],
        )

        # =======================================================
        # Field 1/3: edge_node_connectivity (2/4)
        # =======================================================
        edge_node = mesh2_attributes["edge_node_connectivity"]
        self.assertIsInstance(edge_node, dict)
        self.assertCountEqual(edge_node.keys(), ["dimensions", "variables"])
        self.assertEqual(edge_node["dimensions"], {})

        edge_node_vars = edge_node["variables"]
        self.assertIsInstance(edge_node_vars, dict)
        self.assertCountEqual(edge_node_vars.keys(), ["Mesh2_edge_nodes"])

        edge_nodes = edge_node_vars["Mesh2_edge_nodes"]
        self.assertIsInstance(edge_nodes, dict)
        self.assertCountEqual(edge_nodes.keys(), ["attributes", "dimensions"])
        self.assertEqual(
            edge_nodes["dimensions"],
            {
                "Two": {"size": 2},
                "nMesh2_edge": {"size": 9},
            },
        )

        edge_nodes_attrs = edge_nodes["attributes"]
        self.assertIsInstance(edge_nodes_attrs, dict)
        self.assertCountEqual(edge_nodes_attrs.keys(), ["standard_name"])

        edge_sn = edge_nodes_attrs["standard_name"]
        self.assertIsInstance(edge_sn, list)
        self.assertEqual(len(edge_sn), 1)
        self.assertEqual(
            edge_sn[0],
            {
                "code": self.bad_sn_expected_code,
                "reason": self.bad_sn_expected_reason,
                "value": "badname_Mesh2_edge_nodes",
            },
        )

        # =======================================================
        # Field 1/3: face_face_connectivity (3/4)
        # =======================================================
        face_face = mesh2_attributes["face_face_connectivity"]
        self.assertIsInstance(face_face, dict)
        self.assertCountEqual(face_face.keys(), ["dimensions", "variables"])
        self.assertEqual(face_face["dimensions"], {})

        face_face_vars = face_face["variables"]
        self.assertIsInstance(face_face_vars, dict)
        self.assertCountEqual(face_face_vars.keys(), ["Mesh2_face_links"])

        face_links = face_face_vars["Mesh2_face_links"]
        self.assertIsInstance(face_links, dict)
        self.assertCountEqual(face_links.keys(), ["attributes", "dimensions"])
        self.assertEqual(
            face_links["dimensions"],
            {
                "Four": {"size": 4},
                "nMesh2_face": {"size": 3},
            },
        )

        face_links_attrs = face_links["attributes"]
        self.assertIsInstance(face_links_attrs, dict)
        self.assertCountEqual(face_links_attrs.keys(), ["standard_name"])

        face_links_sn = face_links_attrs["standard_name"]
        self.assertIsInstance(face_links_sn, list)
        self.assertEqual(len(face_links_sn), 1)
        self.assertEqual(
            face_links_sn[0],
            {
                "code": self.bad_sn_expected_code,
                "reason": self.bad_sn_expected_reason,
                "value": "badname_Mesh2_face_links",
            },
        )

        # =======================================================
        # Field 1/3: face_node_connectivity (4/4)
        # =======================================================
        face_node = mesh2_attributes["face_node_connectivity"]
        self.assertIsInstance(face_node, dict)
        self.assertCountEqual(face_node.keys(), ["dimensions", "variables"])
        self.assertEqual(face_node["dimensions"], {})

        face_node_vars = face_node["variables"]
        self.assertIsInstance(face_node_vars, dict)
        self.assertCountEqual(face_node_vars.keys(), ["Mesh2_face_nodes"])

        face_nodes = face_node_vars["Mesh2_face_nodes"]
        self.assertIsInstance(face_nodes, dict)
        self.assertCountEqual(face_nodes.keys(), ["attributes", "dimensions"])
        self.assertEqual(
            face_nodes["dimensions"],
            {
                "Four": {"size": 4},
                "nMesh2_face": {"size": 3},
            },
        )

        face_nodes_attrs = face_nodes["attributes"]
        self.assertIsInstance(face_nodes_attrs, dict)
        self.assertCountEqual(face_nodes_attrs.keys(), ["standard_name"])

        face_nodes_sn = face_nodes_attrs["standard_name"]
        self.assertIsInstance(face_nodes_sn, list)
        self.assertEqual(len(face_nodes_sn), 1)
        self.assertEqual(
            face_nodes_sn[0],
            {
                "code": self.bad_sn_expected_code,
                "reason": self.bad_sn_expected_reason,
                "value": "badname_Mesh2_face_nodes",
            },
        )

        # =======================================================
        # Field 2/3: top-level dict (1/4)
        # =======================================================
        # Same structure to field 1 but has some differences, notably:
        # * pa -> ta
        # * nMesh2_node -> nMesh2_face
        # * {'nMesh2_node': {'size': 7} -> {'nMesh2_face': {'size': 3}.
        # So similar testing but some different values.
        # TODO when we use pytest we can parameterise these assertions
        # to prevent duplicating the lines.
        self.assertIsInstance(dc_output_2, dict)
        self.assertCountEqual(dc_output_2.keys(), ["ta"])

        ta = dc_output_2["ta"]
        self.assertIsInstance(ta, dict)
        self.assertCountEqual(ta.keys(), ["attributes", "dimensions"])

        # pa.dimensions
        ta_dimensions = ta["dimensions"]
        self.assertIsInstance(ta_dimensions, dict)
        self.assertCountEqual(ta_dimensions.keys(), ["nMesh2_face", "time"])
        self.assertEqual(ta_dimensions["nMesh2_face"], {"size": 3})
        self.assertEqual(ta_dimensions["time"], {"size": 2})

        # ta.attributes
        ta_attributes = ta["attributes"]
        self.assertIsInstance(ta_attributes, dict)
        self.assertCountEqual(ta_attributes.keys(), ["mesh", "standard_name"])

        # ta.attributes.standard_name (1/4)
        ta_standard_name = ta_attributes["standard_name"]
        self.assertIsInstance(ta_standard_name, list)
        self.assertEqual(len(ta_standard_name), 1)

        self.assertEqual(
            ta_standard_name[0],
            {
                "code": self.bad_sn_expected_code,
                "reason": self.bad_sn_expected_reason,
                "value": "badname_Mesh2",
            },
        )

        # ta.attributes.mesh
        mesh = ta_attributes["mesh"]
        self.assertIsInstance(mesh, dict)
        self.assertCountEqual(mesh.keys(), ["dimensions", "variables"])

        # mesh.dimensions
        mesh_dimensions = mesh["dimensions"]
        self.assertIsInstance(mesh_dimensions, dict)
        self.assertCountEqual(mesh_dimensions.keys(), ["nMesh2_face", "time"])
        self.assertEqual(mesh_dimensions["nMesh2_face"], {"size": 3})
        self.assertEqual(mesh_dimensions["time"], {"size": 2})

        # mesh.variables
        mesh_variables = mesh["variables"]
        self.assertIsInstance(mesh_variables, dict)
        self.assertCountEqual(mesh_variables.keys(), ["Mesh2"])

        mesh2 = mesh_variables["Mesh2"]
        self.assertIsInstance(mesh2, dict)
        self.assertCountEqual(mesh2.keys(), ["attributes", "dimensions"])

        # Mesh2.dimensions
        self.assertEqual(mesh2["dimensions"], {})

        # Mesh2.attributes
        mesh2_attributes = mesh2["attributes"]
        self.assertIsInstance(mesh2_attributes, dict)
        self.assertCountEqual(
            mesh2_attributes.keys(),
            [
                "edge_node_connectivity",
                "face_face_connectivity",
                "face_node_connectivity",
            ],
        )

        # =======================================================
        # Field 2/3: edge_node_connectivity (2/4)
        # =======================================================
        edge_node = mesh2_attributes["edge_node_connectivity"]
        self.assertIsInstance(edge_node, dict)
        self.assertCountEqual(edge_node.keys(), ["dimensions", "variables"])
        self.assertEqual(edge_node["dimensions"], {})

        edge_node_vars = edge_node["variables"]
        self.assertIsInstance(edge_node_vars, dict)
        self.assertCountEqual(edge_node_vars.keys(), ["Mesh2_edge_nodes"])

        edge_nodes = edge_node_vars["Mesh2_edge_nodes"]
        self.assertIsInstance(edge_nodes, dict)
        self.assertCountEqual(edge_nodes.keys(), ["attributes", "dimensions"])
        self.assertEqual(
            edge_nodes["dimensions"],
            {
                "Two": {"size": 2},
                "nMesh2_edge": {"size": 9},
            },
        )

        edge_nodes_attrs = edge_nodes["attributes"]
        self.assertIsInstance(edge_nodes_attrs, dict)
        self.assertCountEqual(edge_nodes_attrs.keys(), ["standard_name"])

        edge_sn = edge_nodes_attrs["standard_name"]
        self.assertIsInstance(edge_sn, list)
        self.assertEqual(len(edge_sn), 1)
        self.assertEqual(
            edge_sn[0],
            {
                "code": self.bad_sn_expected_code,
                "reason": self.bad_sn_expected_reason,
                "value": "badname_Mesh2_edge_nodes",
            },
        )

        # =======================================================
        # Field 2/3: face_face_connectivity (3/4)
        # =======================================================
        face_face = mesh2_attributes["face_face_connectivity"]
        self.assertIsInstance(face_face, dict)
        self.assertCountEqual(face_face.keys(), ["dimensions", "variables"])
        self.assertEqual(face_face["dimensions"], {})

        face_face_vars = face_face["variables"]
        self.assertIsInstance(face_face_vars, dict)
        self.assertCountEqual(face_face_vars.keys(), ["Mesh2_face_links"])

        face_links = face_face_vars["Mesh2_face_links"]
        self.assertIsInstance(face_links, dict)
        self.assertCountEqual(face_links.keys(), ["attributes", "dimensions"])
        self.assertEqual(
            face_links["dimensions"],
            {
                "Four": {"size": 4},
                "nMesh2_face": {"size": 3},
            },
        )

        face_links_attrs = face_links["attributes"]
        self.assertIsInstance(face_links_attrs, dict)
        self.assertCountEqual(face_links_attrs.keys(), ["standard_name"])

        face_links_sn = face_links_attrs["standard_name"]
        self.assertIsInstance(face_links_sn, list)
        self.assertEqual(len(face_links_sn), 1)
        self.assertEqual(
            face_links_sn[0],
            {
                "code": self.bad_sn_expected_code,
                "reason": self.bad_sn_expected_reason,
                "value": "badname_Mesh2_face_links",
            },
        )

        # =======================================================
        # Field 2/3: face_node_connectivity (4/4)
        # =======================================================
        face_node = mesh2_attributes["face_node_connectivity"]
        self.assertIsInstance(face_node, dict)
        self.assertCountEqual(face_node.keys(), ["dimensions", "variables"])
        self.assertEqual(face_node["dimensions"], {})

        face_node_vars = face_node["variables"]
        self.assertIsInstance(face_node_vars, dict)
        self.assertCountEqual(face_node_vars.keys(), ["Mesh2_face_nodes"])

        face_nodes = face_node_vars["Mesh2_face_nodes"]
        self.assertIsInstance(face_nodes, dict)
        self.assertCountEqual(face_nodes.keys(), ["attributes", "dimensions"])
        self.assertEqual(
            face_nodes["dimensions"],
            {
                "Four": {"size": 4},
                "nMesh2_face": {"size": 3},
            },
        )

        face_nodes_attrs = face_nodes["attributes"]
        self.assertIsInstance(face_nodes_attrs, dict)
        self.assertCountEqual(face_nodes_attrs.keys(), ["standard_name"])

        face_nodes_sn = face_nodes_attrs["standard_name"]
        self.assertIsInstance(face_nodes_sn, list)
        self.assertEqual(len(face_nodes_sn), 1)
        self.assertEqual(
            face_nodes_sn[0],
            {
                "code": self.bad_sn_expected_code,
                "reason": self.bad_sn_expected_reason,
                "value": "badname_Mesh2_face_nodes",
            },
        )

        # =======================================================
        # Field 3/3: top-level dict (1/4)
        # =======================================================
        # Same structure to field 1 (and therefore 2) but has some
        # differences, notably:
        # * pa/ta -> v
        # * nMesh2_node/nMesh2_face -> nMesh2_edge
        # * {'nMesh2_node': {'size': 7} (etc.) -> {'nMesh2_edge': {'size': 9}.
        # So similar testing but some different values.
        # TODO when we use pytest we can parameterise these assertions
        # to prevent duplicating the lines.
        self.assertIsInstance(dc_output_3, dict)
        self.assertCountEqual(dc_output_3.keys(), ["v"])

        v = dc_output_3["v"]
        self.assertIsInstance(v, dict)
        self.assertCountEqual(v.keys(), ["attributes", "dimensions"])

        # pa.dimensions
        v_dimensions = v["dimensions"]
        self.assertIsInstance(v_dimensions, dict)
        self.assertCountEqual(v_dimensions.keys(), ["nMesh2_edge", "time"])
        self.assertEqual(v_dimensions["nMesh2_edge"], {"size": 9})
        self.assertEqual(v_dimensions["time"], {"size": 2})

        # v.attributes
        v_attributes = v["attributes"]
        self.assertIsInstance(v_attributes, dict)
        self.assertCountEqual(v_attributes.keys(), ["mesh", "standard_name"])

        # v.attributes.standard_name (1/4)
        v_standard_name = v_attributes["standard_name"]
        self.assertIsInstance(v_standard_name, list)
        self.assertEqual(len(v_standard_name), 1)

        self.assertEqual(
            v_standard_name[0],
            {
                "code": self.bad_sn_expected_code,
                "reason": self.bad_sn_expected_reason,
                "value": "badname_Mesh2",
            },
        )

        # v.attributes.mesh
        mesh = v_attributes["mesh"]
        self.assertIsInstance(mesh, dict)
        self.assertCountEqual(mesh.keys(), ["dimensions", "variables"])

        # mesh.dimensions
        mesh_dimensions = mesh["dimensions"]
        self.assertIsInstance(mesh_dimensions, dict)
        self.assertCountEqual(mesh_dimensions.keys(), ["nMesh2_edge", "time"])
        self.assertEqual(mesh_dimensions["nMesh2_edge"], {"size": 9})
        self.assertEqual(mesh_dimensions["time"], {"size": 2})

        # mesh.variables
        mesh_variables = mesh["variables"]
        self.assertIsInstance(mesh_variables, dict)
        self.assertCountEqual(mesh_variables.keys(), ["Mesh2"])

        mesh2 = mesh_variables["Mesh2"]
        self.assertIsInstance(mesh2, dict)
        self.assertCountEqual(mesh2.keys(), ["attributes", "dimensions"])

        # Mesh2.dimensions
        self.assertEqual(mesh2["dimensions"], {})

        # Mesh2.attributes
        mesh2_attributes = mesh2["attributes"]
        self.assertIsInstance(mesh2_attributes, dict)
        self.assertCountEqual(
            mesh2_attributes.keys(),
            [
                "edge_node_connectivity",
                "face_face_connectivity",
                "face_node_connectivity",
            ],
        )

        # =======================================================
        # Field 3/3: edge_node_connectivity (2/4)
        # =======================================================
        edge_node = mesh2_attributes["edge_node_connectivity"]
        self.assertIsInstance(edge_node, dict)
        self.assertCountEqual(edge_node.keys(), ["dimensions", "variables"])
        self.assertEqual(edge_node["dimensions"], {})

        edge_node_vars = edge_node["variables"]
        self.assertIsInstance(edge_node_vars, dict)
        self.assertCountEqual(edge_node_vars.keys(), ["Mesh2_edge_nodes"])

        edge_nodes = edge_node_vars["Mesh2_edge_nodes"]
        self.assertIsInstance(edge_nodes, dict)
        self.assertCountEqual(edge_nodes.keys(), ["attributes", "dimensions"])
        self.assertEqual(
            edge_nodes["dimensions"],
            {
                "Two": {"size": 2},
                "nMesh2_edge": {"size": 9},
            },
        )

        edge_nodes_attrs = edge_nodes["attributes"]
        self.assertIsInstance(edge_nodes_attrs, dict)
        self.assertCountEqual(edge_nodes_attrs.keys(), ["standard_name"])

        edge_sn = edge_nodes_attrs["standard_name"]
        self.assertIsInstance(edge_sn, list)
        self.assertEqual(len(edge_sn), 1)
        self.assertEqual(
            edge_sn[0],
            {
                "code": self.bad_sn_expected_code,
                "reason": self.bad_sn_expected_reason,
                "value": "badname_Mesh2_edge_nodes",
            },
        )

        # =======================================================
        # Field 3/3: face_face_connectivity (3/4)
        # =======================================================
        face_face = mesh2_attributes["face_face_connectivity"]
        self.assertIsInstance(face_face, dict)
        self.assertCountEqual(face_face.keys(), ["dimensions", "variables"])
        self.assertEqual(face_face["dimensions"], {})

        face_face_vars = face_face["variables"]
        self.assertIsInstance(face_face_vars, dict)
        self.assertCountEqual(face_face_vars.keys(), ["Mesh2_face_links"])

        face_links = face_face_vars["Mesh2_face_links"]
        self.assertIsInstance(face_links, dict)
        self.assertCountEqual(face_links.keys(), ["attributes", "dimensions"])
        self.assertEqual(
            face_links["dimensions"],
            {
                "Four": {"size": 4},
                "nMesh2_face": {"size": 3},
            },
        )

        face_links_attrs = face_links["attributes"]
        self.assertIsInstance(face_links_attrs, dict)
        self.assertCountEqual(face_links_attrs.keys(), ["standard_name"])

        face_links_sn = face_links_attrs["standard_name"]
        self.assertIsInstance(face_links_sn, list)
        self.assertEqual(len(face_links_sn), 1)
        self.assertEqual(
            face_links_sn[0],
            {
                "code": self.bad_sn_expected_code,
                "reason": self.bad_sn_expected_reason,
                "value": "badname_Mesh2_face_links",
            },
        )

        # =======================================================
        # Field 3/3: face_node_connectivity (4/4)
        # =======================================================
        face_node = mesh2_attributes["face_node_connectivity"]
        self.assertIsInstance(face_node, dict)
        self.assertCountEqual(face_node.keys(), ["dimensions", "variables"])
        self.assertEqual(face_node["dimensions"], {})

        face_node_vars = face_node["variables"]
        self.assertIsInstance(face_node_vars, dict)
        self.assertCountEqual(face_node_vars.keys(), ["Mesh2_face_nodes"])

        face_nodes = face_node_vars["Mesh2_face_nodes"]
        self.assertIsInstance(face_nodes, dict)
        self.assertCountEqual(face_nodes.keys(), ["attributes", "dimensions"])
        self.assertEqual(
            face_nodes["dimensions"],
            {
                "Four": {"size": 4},
                "nMesh2_face": {"size": 3},
            },
        )

        face_nodes_attrs = face_nodes["attributes"]
        self.assertIsInstance(face_nodes_attrs, dict)
        self.assertCountEqual(face_nodes_attrs.keys(), ["standard_name"])

        face_nodes_sn = face_nodes_attrs["standard_name"]
        self.assertIsInstance(face_nodes_sn, list)
        self.assertEqual(len(face_nodes_sn), 1)
        self.assertEqual(
            face_nodes_sn[0],
            {
                "code": self.bad_sn_expected_code,
                "reason": self.bad_sn_expected_reason,
                "value": "badname_Mesh2_face_nodes",
            },
        )


if __name__ == "__main__":
    print("Run date:", datetime.datetime.now())
    cfdm.environment()
    print("")
    unittest.main(verbosity=2)
