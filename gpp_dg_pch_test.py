########################################################################
#
# File:   gpp_dg_pch_test.py
# Author: Mark Mitchell
# Date:   04/21/2003
#
# Contents:
#   GPPDGPCHTest
#
# Copyright (c) 2003 by CodeSourcery, LLC.  All rights reserved. 
#
########################################################################

########################################################################
# Imports
########################################################################

import filecmp
from   gpp_dg_test import GPPDGTest
import os
import shutil

########################################################################
# Classes
########################################################################c

class GPPDGPCHTest(GPPDGTest):
    """A 'GPPDGPCHTest' is a G++ test using the 'pch.exp' driver."""

    def Run(self, context, result):

        # This function emulates g++.dg/pch.exp.

        # Initialize.
        self._SetUp(context)
        # Remove stuff left from the last time the test was run.
        source = self._GetSourcePath()
        basename = os.path.splitext(os.path.basename(source))[0]
        for f in (basename + ".H.gch",
                  basename + ".s",
                  basename + ".s-gch"):
            try:
                os.remove(f)
            except:
                pass

        for o in ("-g", "-O2 -g", "-O2"):
            # Create the precompiled header file.
            try:
                os.remove(basename + ".H")
            except:
                pass
            shutil.copyfile(os.path.splitext(source)[0] + ".Hs",
                            basename + ".H")
            self._RunDGTest(o, context, result,
                            basename + ".H",
                            self.KIND_PRECOMPILE,
                            keep_output = 1)

            assembly_outcome = self.UNTESTED
            if os.path.exists(basename + ".H.gch"):
                os.remove(basename + ".H")
                self._RunDGTest(o + " -I.", context, result, keep_output = 1)
                os.remove(basename + ".H.gch")
                if os.path.exists(basename + ".s"):
                    os.rename(basename + ".s", basename + ".s-gch")
                    shutil.copyfile(os.path.splitext(source)[0] + ".Hs",
                                    basename + ".H")
                    self._RunDGTest(o + " -I.", context, result,
                                    keep_output = 1)
                    if filecmp.cmp(basename + ".s", basename + ".s-gch"):
                        assembly_outcome = self.PASS
                    else:
                        assembly_outcome = self.FAIL
                    os.remove(basename + ".H")
                    os.remove(basename + ".s")
                    os.remove(basename + ".s-gch")
            else:
                self._RecordDejaGNUOutcome(result,
                                           self.UNTESTED,
                                           self._name + " " + o)
            message = self._name + " " + o + " assembly comparision"
            self._RecordDejaGNUOutcome(result, assembly_outcome, message)
