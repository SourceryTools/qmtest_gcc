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
from   gcc_dg_test import GCCDGTortureTest
from   gpp_dg_test import GPPDGTest
import os
import shutil

########################################################################
# Classes
########################################################################c

class DGPCHTest:
    """A 'DGPCHTest' emulates the 'dg-pch.exp' driver."""

    _suffix = None
    """The header-file suffix."""

    _pch_options = None
    """A list of command-line options.

    Each element of the list is a string giving one or more
    command-line options.  Each test is run multiple times using all
    of the command-line options in the list."""
    
    def Run(self, context, result):

        # This function emulates dg-pch.exp.
        suffix = self._suffix
        # Initialize.
        self._SetUp(context)
        # Remove stuff left from the last time the test was run.
        source = self._GetSourcePath()
        basename = os.path.splitext(os.path.basename(source))[0]
        basename = os.path.join(context.GetTemporaryDirectory(),
                                basename)
        for f in (basename + suffix + ".gch",
                  basename + ".s",
                  basename + ".s-gch"):
            try:
                os.remove(f)
            except:
                pass

        for o in self._pch_options:
            # Create the precompiled header file.
            try:
                os.remove(basename + suffix)
            except:
                pass
            shutil.copyfile(os.path.splitext(source)[0] + suffix + "s",
                            basename + suffix)
            self._RunDGTest(o, "", context, result,
                            basename + suffix,
                            self.KIND_PRECOMPILE,
                            keep_output = 1)

            assembly_outcome = self.UNTESTED
            if os.path.exists(basename + suffix + ".gch"):
                os.remove(basename + suffix)
                options = o + " -I" + context.GetTemporaryDirectory()
                self._RunDGTest(options, "", context, result, keep_output = 1)
                os.remove(basename + suffix + ".gch")
                if os.path.exists(basename + ".s"):
                    os.rename(basename + ".s", basename + ".s-gch")
                    shutil.copyfile((os.path.splitext(source)[0]
                                     + suffix + "s"),
                                    basename + suffix)
                    self._RunDGTest(options, "", context, result,
                                    keep_output = 1)
                    if filecmp.cmp(basename + ".s", basename + ".s-gch"):
                        assembly_outcome = self.PASS
                    else:
                        assembly_outcome = self.FAIL
                    os.remove(basename + suffix)
                    os.remove(basename + ".s")
                    os.remove(basename + ".s-gch")
            else:
                self._RecordDejaGNUOutcome(result,
                                           self.UNTESTED,
                                           self._name + " " + o)
            message = self._name + " " + o + " assembly comparision"
            self._RecordDejaGNUOutcome(result, assembly_outcome, message)



class GCCDGPCHTest(DGPCHTest, GCCDGTortureTest):
    """A 'GCCDGPCHTest' is a GCC test using the 'pch.exp' driver."""

    _suffix = ".h"

    _pch_options = ["-O0 -g"] + GCCDGTortureTest._torture_without_loops



class GPPDGPCHTest(DGPCHTest, GPPDGTest):
    """A 'GPPDGPCHTest' is a G++ test using the 'pch.exp' driver."""

    _suffix = ".H"

    _pch_options = ("-g", "-O2 -g", "-O2")
    
