########################################################################
#
# File:   gpp_dg_test.py
# Author: Mark Mitchell
# Date:   04/16/2003
#
# Contents:
#   GPPDGTest
#
# Copyright (c) 2003 by CodeSourcery, LLC.  All rights reserved. 
#
########################################################################

########################################################################
# Imports
########################################################################

from   gcc_dg_test_base import GCCDGTestBase
from   gpp_test_base import GPPTestBase
import re

########################################################################
# Classes
########################################################################

class GPPDGTest(GCCDGTestBase, GPPTestBase):
    """A 'GPPDGTest' is a G++ test using the 'dg' test driver.

    This test class emulates the 'g++-dg.exp' source file in the GCC
    testsuite."""

    _default_options = ["-ansi", "-pedantic-errors", "-Wno-long-long"]

    def _GetTargetEnvironment(self, context):

        return GPPTestBase._GetTargetEnvironment(self, context)

    
