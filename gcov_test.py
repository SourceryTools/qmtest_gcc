########################################################################
#
# File:   gcov_test.py
# Author: Mark Mitchell
# Date:   04/23/2003
#
# Contents:
#   GCOVTest
#
# Copyright (c) 2003 by CodeSourcery, LLC.  All rights reserved. 
#
########################################################################

########################################################################
# Imports
########################################################################

import os
import re

########################################################################
# Classes
########################################################################

class GCOVTest:
    """A 'GCOVTest' is a test using the 'gcov.exp' driver.

    This test class emulates the 'gcov.exp' source file in the GCC
    testsuite.

    This class is a mix-in."""

    __gcov_regexp = re.compile(r"^[^:]+: *([0-9]+):")
    """A regular expression matching a line of 'gcov' output."""
    
    __line_regexp = re.compile(r"^ *([^:]*): *([0-9]+):.*count\(([0-9]+)\)")
    """A regular expression matching gcov lines that indicate line counts.

    If a line in the source file is matched by this regular
    expression, then the first group gives the line count determined
    by gcov, the second the line number, and the third the expected
    line count."""

    __branch_count_regexp = re.compile(r"branch\(([0-9 ]+)\)")
    """A regular expression matching gcov lines that indicate branch counts."""

    __taken_regexp = re.compile(r"branch +[0-9]+ taken ([0-9]+)%")
    """A regular expression matching lines that show branch taken results."""

    __end_regexp = re.compile(r"branch(end)")
    """A regular expression matching lines showing last branch result."""


    def _RunGCOVTest(self, args, context, result):

        verify_calls = 0
        verify_branches = 0

        for a in args:
            if a == "calls":
                verify_calls = 1
            elif a == "branches":
                verify_branches = 1

        # Get the name of the executable.
        gcov_args = self._ParseTclWords(args[-1])
        testcase = gcov_args[-1]
        
        # Run "gcov" to collect coverage information.
        status, output = self._RunBuildExecutable(context, result,
                                                  context["GCOVTest.gcov"],
                                                  gcov_args)
        if status != 0:
            self._RecordDejaGNUOutcome(result,
                                       self.FAIL,
                                       (self.GetId() + " gcov failed: "
                                        + output))
            self._CleanUp(testcase)
            return

        gcov_file = testcase + ".gcov"
        if not os.path.exists(gcov_file):
            self._RecordDejaGNUOutcome(result,
                                       self.FAIL,
                                       self.GetId() + " gcov failed: "
                                       + gcov_file + " does not exist")
            self.__CleanUp(testcase)
            return

        lfailed = self.__VerifyLines(result, testcase, gcov_file)
        
        if verify_branches:
            bfailed = self.__VerifyBranches(result, testcase, gcov_file)
        else:
            bfailed = 0
            
        if verify_calls:
            raise NotImplementedError
        else:
            cfailed = 0

        if lfailed or bfailed or cfailed:
            self._RecordDejaGNUOutcome(result,
                                       self.FAIL,
                                       ("%s gcov: %d failures in line counts, "
                                        "%d in branch percentages, "
                                        "%d in return percentages"
                                        % (self.GetId(), lfailed, bfailed,
                                           cfailed)))
        else:
            self._RecordDejaGNUOutcome(result, self.PASS,
                                       self.GetId() + " gcov")
            self.__CleanUp(testcase)


    def __VerifyBranches(self, result, testcase, gcov_file):
        """Verify that the branch information in 'gcov_file' is correct.
        
        'testcase' -- The patch to the source file being compiled.

        'gcov_file' -- The path to the '.gcov' file."""

        failures = 0
        expected = []
        line_num = 0
        for l in open(gcov_file).xreadlines():
            m = self.__gcov_regexp.match(l)
            if m:
                line_num = m.group(1)
            if l.find("branch") == -1:
                continue
            m = self.__branch_count_regexp.match(l)
            if m:
                if expected:
                    message = ("%d: expected branch percentages not found: %s"
                               % (line_num, str(expected)))
                    self._RecordDejaGNUOutcome(result, self.FAIL, message)
                    failures += 1
                expected = self._ParseTclWords(m.group(1))
                expected = map(lambda e: (e > 50 and 100 - e) or e,
                               expected)
                continue
            m = self.__taken_regexp.match(l)
            if m:
                p = int(m.group(1))
                if p < 0:
                    message = ("%d: negative percentage: %d"
                               % (line_num, p))
                    self._RecordDejaGNUOutcome(result, self.FAIL, message)
                    failures += 1
                elif p > 100:
                    message = ("%d: percentage greater than 100: %d"
                               % (line_num, p))
                else:
                    if p > 50:
                        p = 100 - 50
                    if p in expected:
                        expected.remove(p)
                continue
            m = self.__end_regexp.match(l)
            if m:
                if expected:
                    message = ("%d: expected branch percentages not found: %s"
                               % (line_num, str(expected)))
                    failures += 1
                expected = []

        if expected:
            message = ("%d: expected branch percentages not found: %s"
                       % (line_num, str(expected)))
            self._RecordDejaGNUOutcome(result, self.FAIL, message)
            failures += 1

        return failures

        
    def __VerifyLines(self, result, testcase, gcov_file):
        """Verify that the line counts in 'gcov_file' are correct.
        
        'testcase' -- The patch to the source file being compiled.

        'gcov_file' -- The path to the '.gcov' file."""

        failures = 0
        for l in open(gcov_file).xreadlines():
            m = self.__line_regexp.match(l)
            if m:
                actual = m.group(1)
                line_num = m.group(2)
                expected = m.group(3)
                if actual == "":
                    message = "%d:no data available for this line" % line_num
                    self._RecordDejaGNUOutcome(result, self.FAIL, message)
                    failures += 1
                elif actual != expected:
                    message = "%d:is %d:should be %d" % (line_num,
                                                         actual,
                                                         expected)
                    self._RecordDejaGNUOutcome(result, self.FAIL, message)
                    failures += 1

        return failures
    
    
    def __CleanUp(self, testcase):
        """Remove files generated by 'gcov'.

        'testcase' -- The name of the source file being tested."""

        basename = os.path.basename(testcase)
        base = os.path.splitext(basename)[0]
        try:
            os.path.remove(base + ".bb",
                           base + ".bbg",
                           base + ".da",
                           base + ".gcov")
        except:
            pass
