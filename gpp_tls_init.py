########################################################################
#
# File:   gpp_tls_init.py
# Author: Mark Mitchell
# Date:   04/21/2003
#
# Contents:
#   GPPTLSInit
#
# Copyright (c) 2003 by CodeSourcery, LLC.  All rights reserved. 
#
########################################################################

########################################################################
# Imports
########################################################################

from   compiler import Compiler
from   dejagnu_base import DejaGNUBase
from   gpp_test_base import GPPTestBase
from   qm.test.resource import Resource
import os

########################################################################
# Classes
########################################################################

class GPPTLSInit(Resource, DejaGNUBase, GPPTestBase):
    """A 'GPPTLSInit' stores information for thread-local-storage tests.

    Every G++ thread-local-storage test depends on a 'GPPTLSInit'
    resource."""

    SUPPORTED_TAG = "GPPTLSInit.supported"
    """The context property that indicates compiler support for TLS.

    If this context property is true, the compiler supports TLS;
    otherwise, it does not."""
    
    def SetUp(self, context, result):

        super(GPPTLSInit, self)._SetUp(context)
        
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
