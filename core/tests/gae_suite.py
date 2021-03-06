# Copyright 2014 The Oppia Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Oppia test suite.

Invoke this test script from the command line by running

    python core/tests/gae_suite.py

from the root folder.


=====================
CUSTOMIZATION OPTIONS
=====================

You can customize this script as follows:

(1) Append a test target to make the script run all tests in a given module
or class, or run a particular test. For example,

    python core/tests/gae_suite.py --test_target='foo.bar.Baz'

runs all tests in test class Baz in the foo/bar.py module, and

    python core/tests/gae_suite.py --test_target='foo.bar.Baz.quux'

runs the test method quux in the test class Baz in the foo/bar.py module.


(2) Append a test path to make the script run all tests in a given
subdirectory. For example,

    python core/tests/gae_suite.py --test_path='core/controllers'

runs all tests in the core/controllers/ directory.


Only one of test_path and test_target should be specified.

In addition, you can add the --omit_slow_tests flag to exclude tests that are
tagged with test_utils.TestBase.SLOW_TEST.
"""

__author__ = 'Sean Lip'

import argparse
import os
import sys
import unittest

root_dir = os.path.realpath(os.path.join(os.getcwd()))
sys.path.append(root_dir)

import feconf

EXPECTED_TEST_COUNT = 235


_PARSER = argparse.ArgumentParser()
_PARSER.add_argument(
    '--test_target',
    help='optional dotted module name of the test(s) to run',
    type=str)
_PARSER.add_argument(
    '--test_path',
    help='optional subdirectory path containing the test(s) to run',
    type=str)
_PARSER.add_argument(
    '--omit_slow_tests',
    help='whether to omit tests that are flagged as slow',
    action='store_true')

OPPIA_TOOLS_DIR = os.path.join(os.getcwd(), '..', 'oppia_tools')


def create_test_suites(parsed_args):
    """Creates test suites. If test_dir is None, runs all tests."""
    loader = unittest.TestLoader()
    root_dir = os.path.realpath(os.path.join(os.getcwd()))

    if parsed_args.test_target and parsed_args.test_path:
        raise Exception('At most one of test_path and test_target '
                        'should be specified.')
    if parsed_args.test_target and '/' in parsed_args.test_target:
        raise Exception('The delimiter in test_target should be a dot (.)')
    if parsed_args.test_path and '.' in parsed_args.test_path:
        raise Exception('The delimiter in test_path should be a slash (/)')

    if parsed_args.test_target:
        return [loader.loadTestsFromName(parsed_args.test_target)]

    if parsed_args.test_path:
        root_dir = os.path.join(root_dir, parsed_args.test_path)

    suite = loader.discover(
        root_dir, pattern='*_test.py', top_level_dir=root_dir)
    return [suite]


def _require_dir_exists(f):
    d = os.path.dirname(f)
    if not os.path.exists(d):
        raise Exception('Directory %s does not exist.' % d)


def main():
    """Runs the tests."""

    def _iterate(test_suite_or_case):
        """Iterate through all the test cases in `test_suite_or_case`."""
        try:
            suite = iter(test_suite_or_case)
        except TypeError:
            yield test_suite_or_case
        else:
            for test in suite:
                for subtest in _iterate(test):
                    yield subtest

    feconf.PLATFORM = 'gae'

    GAE_DIR = os.path.join(
        OPPIA_TOOLS_DIR, 'google_appengine_1.8.8', 'google_appengine')
    CURR_DIR = os.path.abspath(os.getcwd())
    WEBTEST_DIR = os.path.abspath(
        os.path.join(OPPIA_TOOLS_DIR, 'webtest-1.4.2'))
    WEBOB_DIR = os.path.abspath(os.path.join(
        OPPIA_TOOLS_DIR, 'google_appengine_1.8.8', 'google_appengine', 'lib',
        'webob_0_9'))
    BLEACH_DIR = os.path.abspath(os.path.join(
        os.getcwd(), 'third_party', 'bleach-1.2.2'))
    HTML5LIB_DIR = os.path.abspath(os.path.join(
        os.getcwd(), 'third_party', 'html5lib-python-0.95'))

    _require_dir_exists(GAE_DIR)
    _require_dir_exists(CURR_DIR)
    _require_dir_exists(WEBTEST_DIR)
    _require_dir_exists(WEBOB_DIR)
    _require_dir_exists(BLEACH_DIR)
    _require_dir_exists(HTML5LIB_DIR)

    sys.path.insert(0, GAE_DIR)
    sys.path.insert(0, CURR_DIR)
    sys.path.append(WEBTEST_DIR)
    sys.path.append(WEBOB_DIR)
    sys.path.append(BLEACH_DIR)
    sys.path.append(HTML5LIB_DIR)

    import dev_appserver
    dev_appserver.fix_sys_path()

    parsed_args = _PARSER.parse_args()
    suites = create_test_suites(parsed_args)

    import test_utils

    if parsed_args.omit_slow_tests:
        new_suites = []
        for suite in suites:
            new_suite = unittest.TestSuite()
            for test in _iterate(suite):
                if (not hasattr(test, 'TAGS') or
                        not test_utils.TestTags.SLOW_TEST in test.TAGS):
                    new_suite.addTest(test)
            new_suites.append(new_suite)

        suites = new_suites

    results = [unittest.TextTestRunner(verbosity=2).run(suite)
               for suite in suites]

    tests_run = 0
    for result in results:
        tests_run += result.testsRun
        if result.errors or result.failures:
            raise Exception(
                'Functional test suite failed: %s errors, %s failures of '
                '%s tests run.' % (
                    len(result.errors), len(result.failures), result.testsRun))

    if tests_run == 0:
        raise Exception('No tests were run.')

    if (parsed_args.test_path is None and parsed_args.test_target is None
            and not parsed_args.omit_slow_tests
            and tests_run != EXPECTED_TEST_COUNT):
        raise Exception('Expected %s tests to be run, not %s.' %
                        (EXPECTED_TEST_COUNT, tests_run))


if __name__ == '__main__':
    main()
