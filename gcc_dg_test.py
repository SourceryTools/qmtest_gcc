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

import fnmatch
from   gcc_dg_test_base import GCCDGTestBase
from   gcc_init import GCCInit
from   gpp_test_base import GCCTestBase

########################################################################
# Classes
########################################################################

class GCCDGTest(GCCDGTestBase, GCCTestBase):
    """A 'GCCDGTest' is a GCC test using the 'dg' test driver.

    This test class emulates the 'gcc-dg.exp' source file in the GCC
    testsuite."""

    _default_options = "-ansi -pedantic-errors"

    def _DGrequire_weak(self, line_num, args, context):
        """Emulate the 'dg-require-weak' command.

        'line_num' -- The number at which the command was found.

        'args' -- The arguments to the command, as a list of
        strings.

        'context' -- The 'Context' in which the test is running."""

        if not context[GCCInit.SUPPORTS_WEAK_CONTEXT_PROPERTY]:
            self._DGdo(line_num, ["run", "target none-none-none"],
                       context)


    def _DGrequire_alias(self, line_num, args, context):
        """Emulate the 'dg-require-alias' command.

        'line_num' -- The number at which the command was found.

        'args' -- The arguments to the command, as a list of
        strings.

        'context' -- The 'Context' in which the test is running."""

        if not context[GCCInit.SUPPORTS_ALIAS_CONTEXT_PROPERTY]:
            self._DGdo(line_num, ["run", "target none-none-none"],
                       context)
        

    def _DGrequire_gc_sections(self, line_num, args, context):
        """Emulate the 'dg-require-gc-sections' command.

        'line_num' -- The number at which the command was found.

        'args' -- The arguments to the command, as a list of
        strings.

        'context' -- The 'Context' in which the test is running."""

        if not context[GCCInit.SUPPORTS_GCSEC_CONTEXT_PROPERTY]:
            self._DGdo(line_num, ["run", "target none-none-none"],
                       context)



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



class GCCDGTortureTest(GCCDGTest):
    """A 'GCCDGTortureTest' emulates 'gcc.dg/torture/dg-torture.exp'."""

    _default_options = ""

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
    
    def Run(self, context, result):

        # This method emulates gcc-dg-runtest.
        self._SetUp(context)
        # Assume there are no loops in the input source.
        options = self._torture_without_loops
        # But if there are use the "with loops" options.
        source = open(self._GetSourcePath())
        for l in source.xreadlines():
            if (fnmatch.fnmatch(l, "for*(")
                or fnmatch.fnmatch(l, "while*(")):
                options = self._torture_with_loops
                break
        for o in options:
            self._RunDGTest(o, self._default_options, context, result)



class GCCDGFormatTest(GCCDGTortureTest):
    """A 'GCCDGFormatTest' emulates 'gcc.dg/format/format.exp'."""

    _default_options = ""
    
    _torture_with_loops = [ "", "-DWIDE" ]

    _torture_without_loops = _torture_with_loops



