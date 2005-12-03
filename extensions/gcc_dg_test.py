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

    _default_options = ["-ansi", "-pedantic-errors"]

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


    def _DGrequire_dll(self, line_num, args, context):
        """Emulate the 'dg-require-dll' command.

        'line_num' -- The number at which the command was found.

        'args' -- The arguments to the command, as a list of
        strings.

        'context' -- The 'Context' in which the test is running."""

        if not context[GCCInit.SUPPORTS_DLL_CONTEXT_PROPERTY]:
            self._DGdo(line_num, ["run", "target none-none-none"],
                       context)
        


class GCCDGNoncompileTest(GCCDGTest):
    """A 'GCCDGNoncompileTest' is a GCC test using the 'dg' test driver.

    This test class emulates the 'noncompile.exp' source file in the
    GCC testsuite."""

    _default_options = []
    


class GCCDGCPPTest(GCCDGTestBase, GCCTestBase):
    """A 'GCCDGCPPTradTest' is a GCC test using the 'cpp' test driver.

    This test class emulates the 'cpp.exp' source file in the GCC
    testsuite."""

    _default_options = ["-ansi", "-pedantic-errors"]



class GCCDGCPPTradTest(GCCDGTestBase, GCCTestBase):
    """A 'GCCDGCPPTradTest' is a GCC test using the 'trad' test driver.

    This test class emulates the 'trad.exp' source file in the GCC
    testsuite."""

    _default_options = ["-traditional-cpp"]



class GCCDGTortureTest(GCCDGTest):
    """A 'GCCDGTortureTest' emulates 'gcc.dg/torture/dg-torture.exp'."""

    _default_options = []

    _torture_with_loops = [
        ["-O0"],
        ["-O1"],
        ["-O2"],
        ["-O3", "-fomit-frame-pointer"],
        ["-O3", "-fomit-frame-pointer", "-funroll-loops"],
        ["-O3", "-fomit-frame-pointer",
         "-funroll-all-loops", "-finline-functions"],
        ["-O3", "-g"],
        ["-Os"],
        ]
    """A list of command-line options to use for "torture" tests.

    This variable emulates 'torture_with_loops' in 'gcc-dg.exp'."""

    _torture_without_loops = [item for item in _torture_with_loops
                              if [arg for arg in item
                                  if arg.find("loop") == -1]]
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
            if (fnmatch.fnmatch(l, "*for*(*")
                or fnmatch.fnmatch(l, "*while*(*")):
                options = self._torture_with_loops
                break
        for o in options:
            # See if there is any reason to expect this test to fail.
            # See check_conditional_xfail in DejaGNU for the code
            # being emulated here.
            target = self._GetTarget(context)
            for tgts, r_opt, f_opt in self._xfail_if:
                # Check the target.
                tgt_match = 0
                for t in tgts:
                    if fnmatch.fnmatch(target, t):
                        tgt_match = 1
                        break
                if not tgt_match:
                    continue

                raise NotImplementedError
            # Run the test.
            self._RunDGTest(o, self._default_options, context, result)


    def _DGxfail_if(self, line_num, args, context):
        """Emulate the 'dg-xfail-if' command.

        'line_num' -- The number at which the command was found.

        'args' -- The arguments to the command, as a list of
        strings.

        'context' -- The 'Context' in which the test is running."""

        targets = self._ParseTclWords(args[1])
        required_options = self._ParseTclWords(args[2])
        forbidden_options = self._ParseTclWords(args[3])
        self._xfail_if.append((targets, required_options, forbidden_options))


    def _SetUp(self, context):

        self._xfail_if = []
        super(GCCDGTortureTest, self)._SetUp(context)
        


class GCCDGFormatTest(GCCDGTortureTest):
    """A 'GCCDGFormatTest' emulates 'gcc.dg/format/format.exp'."""

    _default_options = []
    
    _torture_with_loops = [ "", "-DWIDE" ]

    _torture_without_loops = _torture_with_loops



class GCCCTortureCompileTest(GCCDGTortureTest):
    """A 'GCCCTortureCompileTest' emulates 'compile.exp'."""

    _default_kind = GCCDGTortureTest.KIND_ASSEMBLE
    
    _default_options = ["-w"]
