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

    _default_options = "-ansi -pedantic-errors"
    


class GCCDGNoncompileTest(GCCDGTest):
    """A 'GCCDGTest' is a GCC test using the 'dg' test driver.

    This test class emulates the 'noncompile.exp' source file in the
    GCC testsuite."""

    _default_options = ""
    
