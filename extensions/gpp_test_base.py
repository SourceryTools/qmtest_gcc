########################################################################
#
# File:   gpp_test_base.py
# Author: Mark Mitchell
# Date:   05/15/2003
#
# Contents:
#   GPPTestBase
#
# Copyright (c) 2003 by CodeSourcery, LLC.  All rights reserved. 
#
########################################################################

########################################################################
# Imports
########################################################################

from   gcc_test_base import GCCTestBase
import os

########################################################################
# Classes
########################################################################

class GPPTestBase(GCCTestBase):
    """A 'GPPTestBase' is a base for all G++ tests.

    This class emulates functionality in 'g++.exp' in the GCC
    testsuite."""

    _language = "cplusplus"

    _options_context_property = "GPPInit.options"

    _libdir_context_property = "GPPInit.library_directories"
    
    def _GetTargetEnvironment(self, context):

        env = {}
	if context[self._libdir_context_property]:
            dirs = ":".join(context[self._libdir_context_property])
            for v in ("LD_LIBRARY_PATH",
                      "SHLIB_PATH",
                      "LD_LIBRARY_N32_PATH",
                      "LD_LIBRARY64_PATH"):
                val = os.environ.get(v, "")
                if val:
                    env[v] = val + ":" + dirs
                else:
                    env[v] = dirs

        return env
