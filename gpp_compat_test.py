########################################################################
#
# File:   gpp_compat_test.py
# Author: Mark Mitchell
# Date:   05/02/2003
#
# Contents:
#   GPPCompatTest
#
# Copyright (c) 2003 by CodeSourcery, LLC.  All rights reserved. 
#
########################################################################

########################################################################
# Imports
########################################################################

from   compat_test import CompatTest
from   gpp_test_base import GPPTestBase

########################################################################
# Classes
########################################################################

class GPPCompatTest(CompatTest, GPPTestBase):
    """A 'GPPCompatTest' emulates a G++ 'compat.exp' test."""

    def _GetTargetEnvironment(self, context):

        return GPPTestBase._GetTargetEnvironment(self, context)
            
    
