########################################################################
#
# File:   gpp_gcov_test.py
# Author: Mark Mitchell
# Date:   04/23/2003
#
# Contents:
#   GPPGCOVTest
#
# Copyright (c) 2003 by CodeSourcery, LLC.  All rights reserved. 
#
########################################################################

########################################################################
# Imports
########################################################################

from   gpp_dg_test import GPPDGTest
from   gcov_test import GCOVTest

########################################################################
# Classes
########################################################################

class GPPGCOVTest(GPPDGTest, GCOVTest):
    """A 'GPPGCOVTest' is a G++ coverage test."""

    def _ExecuteFinalCommand(self, command, args, context, result):

        if command == "run-gcov":
            return self._RunGCOVTest(args, context, result)

        return super(GPPGCOVTest, self)._ExecuteFinalCommand(self,
                                                             command,
                                                             args,
                                                             context,
                                                             result)
