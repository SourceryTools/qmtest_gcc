########################################################################
#
# File:   gcc_init.py
# Author: Mark Mitchell
# Date:   06/05/2003
#
# Contents:
#   GCCInit
#
# Copyright (c) 2003 by CodeSourcery, LLC.  All rights reserved. 
#
########################################################################

########################################################################
# Imports
########################################################################

from   qm.test.resource import Resource
from   dejagnu_base import DejaGNUBase
from   gcc_test_base import GCCTestBase
import os
import re

########################################################################
# Classes
########################################################################

class GCCInit(Resource, GCCTestBase, DejaGNUBase):
    """A 'GPPInit' resource stores information for G++ tests.

    Every C test depends on a 'GCCInit' resource."""

    SUPPORTS_WEAK_CONTEXT_PROPERTY = "GCCInit.supports_weak"
    """A context property that is true if weak symbols are supported.

    This context property is made available to all tests that depend
    on this resource."""
    
    def SetUp(self, context, result):

        super(GCCInit, self)._SetUp(context)

        # Figure out whether or not weak symbols are supported.
        basename = os.path.join(context.GetTemporaryDirectory(),
                                self.GetId())
        source_file = basename + ".c"
        asm_file = basename + ".s"
        f = open(source_file, "w")
        f.write("void f() __attribute__((weak));")
        output = self._Compile(context, result, [source_file], asm_file,
                               GCCTestBase.KIND_COMPILE)
        context[self.SUPPORTS_WEAK_CONTEXT_PROPERTY] = not output
