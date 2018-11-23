from __future__ import print_function
import datetime
import os
import unittest

import cfdm

# Build the test suite from the tests found in the test files.
testsuite_setup = unittest.TestSuite()
testsuite_setup.addTests(unittest.TestLoader().discover('.', pattern='setup_create_field*.py'))

testsuite = unittest.TestSuite()
testsuite.addTests(unittest.TestLoader().discover('.', pattern='test_*.py'))
 
# Run the test suite.
def run_test_suite_setup(verbosity=2):
    runner = unittest.TextTestRunner(verbosity=verbosity)
    runner.run(testsuite_setup)

# Run the test suite.
def run_test_suite(verbosity=2):
    runner = unittest.TextTestRunner(verbosity=verbosity)
    runner.run(testsuite)

if __name__ == '__main__':
    print('---------------')
    print('CFDM TEST SUITE')
    print('---------------')
    print('Run date:', datetime.datetime.now())
    cfdm.environment()
    print('')
    print('Running tests from', os.path.abspath(os.curdir))
    print('')
    
    run_test_suite_setup()
    run_test_suite()
