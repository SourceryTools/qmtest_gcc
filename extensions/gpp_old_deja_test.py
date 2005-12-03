########################################################################
#
# File:   gpp_old_deja_test.py
# Author: Mark Mitchell
# Date:   05/02/2003
#
# Contents:
#   GPPOldDejaTest
#
# Copyright (c) 2003 by CodeSourcery, LLC.  All rights reserved. 
#
########################################################################

########################################################################
# Imports
########################################################################

from   gpp_dg_test import GPPDGTest
import re

########################################################################
# Classes
########################################################################

class GPPOldDejaTest(GPPDGTest):
    """A 'GPPOldDejaTest' is a test using the 'old-deja' test driver."""

    __prune_regexp \
         = re.compile("(?m)("
                      "(^.*: In (.*function|method|.*structor).*)"
                      "|(^.*: In instantiation of .*)"
                      "|(^.*:   instantiated from .*)"
                      "|(^.*file path prefix .* never used)"
                      "|(^.*linker input file unused since linking not done)"
                      "|(^collect: re(compiling|linking).*)"
                      ")")
    """A regular expression matching irrelevant output from GCC."""
    
    def _PruneOutput(self, output):

        output = self.__prune_regexp.sub("", output)
        return super(GPPOldDejaTest, self)._PruneOutput(output)
