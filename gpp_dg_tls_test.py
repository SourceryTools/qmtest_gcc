########################################################################
#
# File:   gpp_dg_tls_test.py
# Author: Mark Mitchell
# Date:   04/21/2003
#
# Contents:
#   GPPDGTLSTest
#
# Copyright (c) 2003 by CodeSourcery, LLC.  All rights reserved. 
#
########################################################################

########################################################################
# Imports
########################################################################

from gpp_dg_test import GPPDGTest
from gpp_tls_init import GPPTLSInit
from qm.test.result import Result

########################################################################
# Classes
########################################################################

class GPPDGTLSTest(GPPDGTest):
    """A 'GPPDGTLSTest' is a G++ test using the 'tls.exp' driver."""

    def Run(self, context, result):

        if not context[GPPTLSInit.SUPPORTED_TAG]:
            result.SetOutcome(Result.UNTESTED,
                              "Thread-local storage is not supported.")
            return
        
        GPPDGTest.Run(self, context, result)
