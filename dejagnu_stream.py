########################################################################
#
# File:   dejagnu_stream.py
# Author: Mark Mitchell
# Date:   04/30/2003
#
# Contents:
#   DejaGNUStream
#
# Copyright (c) 2003 by CodeSourcery, LLC.  All rights reserved. 
#
########################################################################

########################################################################
# Imports
########################################################################

from dejagnu_test import DejaGNUTest
from qm.test.file_result_stream import FileResultStream

########################################################################
# Classes
########################################################################

class DejaGNUStream(FileResultStream):
    """A 'DejaGNUStream' formats its output like DejaGNU."""

    __outcome_descs = {
        DejaGNUTest.PASS: "expected passes",
        DejaGNUTest.FAIL: "unexpected failures",
        DejaGNUTest.XFAIL: "expected failures",
        DejaGNUTest.XPASS: "unexpected successes",
        DejaGNUTest.WARNING: "warnings",
        DejaGNUTest.ERROR: "errors",
        DejaGNUTest.UNSUPPORTED: "unsupported tests",
        DejaGNUTest.UNRESOLVED: "unresolved testcases",
        DejaGNUTest.UNTESTED: "untested testcases"
        }
    
    def __init__(self, arguments):

        super(DejaGNUStream, self).__init__(arguments)
        self.__outcomes = {}
        for o in DejaGNUTest.dejagnu_outcomes:
            self.__outcomes[o] = 0
            
            
    def WriteResult(self, result):

        # Get the DejaGNU annotations in sorted order.
        keys = filter(lambda k: k.startswith(DejaGNUTest.RESULT_PREFIX),
                      result.keys())
        keys.sort(lambda k1, k2: cmp(int(k1[len(DejaGNUTest.RESULT_PREFIX):]),
                                     int(k2[len(DejaGNUTest.RESULT_PREFIX):])))
        for k in keys:
            r = result[k]
            self.file.write(r + "\n")
            # Keep track of the outcomes.
            outcome = r[:r.find(":")]
            self.__outcomes[outcome] += 1


    def Summarize(self):

        self.file.write("\n\t\t=== Summary ===\n")
        # This function emulates log_summary from the DejaGNU
        # distribution.
        for o in DejaGNUTest.dejagnu_outcomes:
            if self.__outcomes[o]:
                desc = "# of %s" % self.__outcome_descs[o]
                self.file.write(desc)
                if len(desc) < 24:
                    self.file.write("\t")
                self.file.write("\t%d\n" % self.__outcomes[o])
