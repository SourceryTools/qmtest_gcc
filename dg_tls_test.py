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

from   compiler import Compiler
from   dejagnu_base import DejaGNUBase
from   gcc_test_base import GCCTestBase
from   gcc_dg_test import GCCDGTest
from   gpp_dg_test import GPPDGTest
from   gpp_test_base import GPPTestBase
from   qm.test.result import Result
from   qm.test.resource import Resource
import os

########################################################################
# Classes
########################################################################

class TLSInitBase(Resource, DejaGNUBase):
    """A 'TLSInitBase' determines whether or not TLS is supported.

    Every thread-local-storage test depends on a 'GPPTLSInit'
    resource."""

    SUPPORTED_TAG = "TLSInit.supported"
    """The context property that indicates compiler support for TLS.

    If this context property is true, the compiler supports TLS;
    otherwise, it does not."""
    
    def SetUp(self, context, result):

        super(TLSInitBase, self)._SetUp(context)
        
        # This method emulates g++.dg/tls.exp.
        trivial_source_file = os.path.join(self.GetDatabase().GetRoot(),
                                           os.path.dirname(self.GetId()),
                                           "trivial.C")
        output = self._Compile(context, result,
                               [trivial_source_file], "trivial.S",
                               self.KIND_COMPILE)
        if output.find("not supported") != -1:
            context[self.SUPPORTED_TAG] = 0
        else:
            context[self.SUPPORTED_TAG] = 1



class GCCTLSInit(TLSInitBase, GCCTestBase):
    """A 'GCCTLSInit' resource checks to see if TLS is available in GCC."""



class GPPTLSInit(TLSInitBase, GPPTestBase):
    """A 'GPPTLSInit' resource checks to see if TLS is available in G++."""


    
class GCCDGTLSTest(GCCDGTest):
    """A 'GPPDGTLSTest' is a G++ test using the 'tls.exp' driver."""

    def Run(self, context, result):

        if not context[GCCTLSInit.SUPPORTED_TAG]:
            result.SetOutcome(Result.UNTESTED,
                              "Thread-local storage is not supported.")
            return

        super(GCCDGTLSTest, self).Run(context, result)



class GPPDGTLSTest(GPPDGTest):
    """A 'GPPDGTLSTest' is a G++ test using the 'tls.exp' driver."""

    def Run(self, context, result):

        if not context[GPPTLSInit.SUPPORTED_TAG]:
            result.SetOutcome(Result.UNTESTED,
                              "Thread-local storage is not supported.")
            return
        
        super(GPPDGTLSTest, self).Run(context, result)



