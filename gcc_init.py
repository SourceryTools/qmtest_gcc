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
    """A context property that is true if weak symbols are supported."""
    
    SUPPORTS_ALIAS_CONTEXT_PROPERTY = "GCCInit.supports_alias"
    """A context property that is true if weak symbols are supported."""

    SUPPORTS_GCSEC_CONTEXT_PROPERTY = "GCCInit.supports_gcsec"
    """A context property that is true if --gc-sections is supported."""
    
    def SetUp(self, context, result):

        super(GCCInit, self)._SetUp(context)

        # Run small test programs to figure out what features are
        # supported.
        for test, mode, options, property in \
            (("void f() __attribute__((weak));\n",
              GCCTestBase.KIND_COMPILE,
              [],
              self.SUPPORTS_WEAK_CONTEXT_PROPERTY),
             ('void f() __attribute__((alias("g")));\n',
              GCCTestBase.KIND_COMPILE,
              [],
              self.SUPPORTS_ALIAS_CONTEXT_PROPERTY),
             ("int main() {}\n",
              GCCTestBase.KIND_EXECUTABLE,
              ["-Wl,--gc-sections"],
              self.SUPPORTS_GCSEC_CONTEXT_PROPERTY)):
            basename = os.path.join(context.GetTemporaryDirectory(),
                                    self.GetId())
            source_file = basename + ".c"
            asm_file = basename + ".s"
            f = open(source_file, "w")
            f.write(test)
            f.close()
            output = self._Compile(context, result, [source_file], asm_file,
                                   mode, options)
            context[property] = not output
