########################################################################
#
# File:   gcc_dg_test.py
# Author: Mark Mitchell
# Date:   05/16/2003
#
# Contents:
#   GCCDGTest
#
# Copyright (c) 2003 by CodeSourcery, LLC.  All rights reserved. 
#
########################################################################

########################################################################
# Imports
########################################################################

from   gcc_dg_test_base import GCCDGTestBase
from   gpp_test_base import GCCTestBase

########################################################################
# Classes
########################################################################

class GCCDGTest(GCCDGTestBase, GCCTestBase):
    """A 'GCCDGTest' is a GCC test using the 'dg' test driver.

    This test class emulates the 'gcc-dg.exp' source file in the GCC
    testsuite."""

    _torture_with_loops = [
        "-O0",
        "-O1",
        "-O2",
        "-O3 -fomit-frame-pointer",
        "-O3 -fomit-frame-pointer -funroll-loops",
        "-O3 -fomit-frame-pointer -funroll-all-loops -finline-functions",
        "-O3 -g",
        "-Os"
        ]
    """A list of command-line options to use for "torture" tests.

    This variable emulates 'torture_with_loops' in 'gcc-dg.exp'."""

    _torture_without_loops \
        = filter(lambda s: s.find("loop") == -1,
                 _torture_with_loops)
    """A subset of 'torture_with_loops' that does not do loop optimizations.

    This variable emulates 'torture_without_loops' in 'gcc-dg.exp'."""
    
    _default_options = "-ansi -pedantic-errors"
    
    def Run(self, context, result):

        self._SetUp(context)
        for o in self._torture_with_loops:
            self._RunDGTest(o, self._default_options, context, result)



class GCCDGNoncompileTest(GCCDGTest):
    """A 'GCCDGNoncompileTest' is a GCC test using the 'dg' test driver.

    This test class emulates the 'noncompile.exp' source file in the
    GCC testsuite."""

    _default_options = ""
    


class GCCDGCPPTest(GCCDGTestBase, GCCTestBase):
    """A 'GCCDGCPPTradTest' is a GCC test using the 'cpp' test driver.

    This test class emulates the 'cpp.exp' source file in the GCC
    testsuite."""

    _default_options = "-ansi -pedantic-errors"



class GCCDGCPPTradTest(GCCDGTestBase, GCCTestBase):
    """A 'GCCDGCPPTradTest' is a GCC test using the 'trad' test driver.

    This test class emulates the 'trad.exp' source file in the GCC
    testsuite."""

    _default_options = "-traditional-cpp"


class GCCDGFormatTest(GCCDGTest):
    """A 'GCCDGFormatTest' emulates 'gcc.dg/format/format.exp'."""

    _default_options = ""
    
    _torture_with_loops = [ "", "-DWIDE" ]

    _torture_without_loops = _torture_with_loops

