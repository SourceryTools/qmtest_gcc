########################################################################
#
# File:   gpp_debug_init.py
# Author: Mark Mitchell
# Date:   04/21/2003
#
# Contents:
#   GPPDebugInit
#
# Copyright (c) 2003 by CodeSourcery, LLC.  All rights reserved. 
#
########################################################################

########################################################################
# Imports
########################################################################

from   compiler import Compiler
from   qm.test.resource import Resource
import os
import gpp

########################################################################
# Classes
########################################################################

class GPPDebugInit(Resource):
    """A 'GPPDebugInit' stores information for debugging tests.

    Every G++ debugging test depends on a 'GPPDebugInit' resource."""

    OPTIONS_TAG = "GPPDebugInit.options"
    """This context property indicates what debugging options are available.

    The value associated with this context property is a list of
    lists.  Each (inner) list contains strings giving compiler
    options.  Every debugging test should be run with all of the
    options indicated."""

    __debug_options = ["-gdwarf-2", "-gstabs", "-gstabs+", "-gxcoff",
                       "-gxcoff+", "-gcoff"]
    """The list of debugging options that might be valid."""
    
    def SetUp(self, context, result):

        # This method emulates g++.dg/debug.exp.
        options = []
        trivial_source_file = os.path.join(self.GetDatabase().GetRoot(),
                                           os.path.dirname(self.GetId()),
                                           "trivial.C")
        for o in self.__debug_options:
            output = gpp.compile(context, result,
                                 [trivial_source_file], "trivial.S",
                                 gpp.KIND_COMPILE,
                                 [o])
            if output.find(": unknown or unsupported -g option") != -1:
                continue
            for l in ("1", "", "3"):
                options.append([o + l])
                for opt in ("-O2", "-O3"):
                    options.append([o + l, opt])

        context[self.OPTIONS_TAG] = options
