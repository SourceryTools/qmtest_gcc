########################################################################
#
# File:   debug_init.py
# Author: Mark Mitchell
# Date:   05/16/2003
#
# Contents:
#   DebugInit, GCCDebugInit, GPPDebugInit
#
# Copyright (c) 2003 by CodeSourcery, LLC.  All rights reserved. 
#
########################################################################

########################################################################
# Imports
########################################################################

from   compiler import Compiler
from   dejagnu_base import DejaGNUBase
from   gcc_dg_test import GCCDGTest
from   gpp_dg_test import GPPDGTest
from   gcc_test_base import GCCTestBase
from   gpp_test_base import GPPTestBase
from   qm.test.resource import Resource
import os

########################################################################
# Classes
########################################################################

class DebugInit(Resource, DejaGNUBase, GCCTestBase):
    """A 'DebugInit' stores information for debugging tests."""

    OPTIONS_TAG = None
    """This context property indicates what debugging options are available.

    The value associated with this context property is a list of
    lists.  Each (inner) list contains strings giving compiler
    options.  Every debugging test should be run with all of the
    options indicated."""

    _trivial_source_file = None
    """The path to a trivial source file.

    This file is compiled several times to determine what debugging
    options are available."""
    
    __debug_options = ["-gdwarf-2", "-gstabs", "-gstabs+", "-gxcoff",
                       "-gxcoff+", "-gcoff"]
    """The list of debugging options that might be valid."""
    
    def SetUp(self, context, result):

        super(DebugInit, self)._SetUp(context)

        # This method emulates g++.dg/debug.exp.
        options = []
        trivial_source_file = os.path.join(self.GetDatabase().GetRoot(),
                                           os.path.dirname(self.GetId()),
                                           self._trivial_source_file)
        for o in self.__debug_options:
            output = self._Compile(context, result,
                                   [trivial_source_file], "trivial.S",
                                   self.KIND_COMPILE,
                                   [o])
            if output.find(": unknown or unsupported -g option") != -1:
                continue
            for l in ("1", "", "3"):
                options.append([o + l])
                for opt in ("-O2", "-O3"):
                    options.append([o + l, opt])

        context[self.OPTIONS_TAG] = options



class GCCDebugInit(DebugInit, GCCTestBase):
    """A 'GPPDebugInit' stores information for debugging tests.

    Every G++ debugging test depends on a 'GPPDebugInit' resource."""

    OPTIONS_TAG = "GCCDebugInit.options"

    _trivial_source_file = "trivial.c"



class GPPDebugInit(DebugInit, GPPTestBase):
    """A 'GPPDebugInit' stores information for debugging tests.

    Every G++ debugging test depends on a 'GPPDebugInit' resource."""

    OPTIONS_TAG = "GPPDebugInit.options"

    _trivial_source_file = "trivial.C"



class GCCDGDebugTest(GCCDGTest):
    """A 'GCCDGDebugTest' is a GCC test using the 'debug.exp' driver."""

    def Run(self, context, result):

        basename = os.path.basename(self._GetSourcePath())
            
        def isanywhere(string, list):
            for s in list:
                if s.find(string) != -1:
                    return True
            return False

        self._SetUp(context)
        for opts in context[GCCDebugInit.OPTIONS_TAG]:
            if (basename in ["debug-1.c", "debug-2.c", "debug-6.c"]
                and opts[0].endswith("1")):
                continue
            elif (basename in ["debug-1.c", "debug-2.c"]
                  and isanywhere("03", opts) != -1
                  and (isanywhere("coff", opts) != -1
                       or isanywhere("stabs", opts) != -1)):
                continue
            self._RunDGTest(opts, [], context, result)



class GPPDGDebugTest(GPPDGTest):
    """A 'GPPDGDebugTest' is a G++ test using the 'debug.exp' driver."""

    def Run(self, context, result):

        self._SetUp(context)
        for opts in context[GPPDebugInit.OPTIONS_TAG]:
            self._RunDGTest(" ".join(opts), "", context, result)
