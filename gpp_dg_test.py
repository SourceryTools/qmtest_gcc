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

from   compiler import Compiler
from   dg_test import DGTest
import gpp
import os
from   qm.executable import Filter
import re

########################################################################
# Classes
########################################################################

class GPPDGTest(DGTest):
    """A 'GPPDGTest' is a G++ test using the 'dg' test driver.

    This test class emulates the 'g++-dg.exp' source file in the GCC
    testsuite."""

    KIND_PRECOMPILE = "precompile"
    
    __extension_map = {
        DGTest.KIND_PREPROCESS : ".i",
        DGTest.KIND_COMPILE : ".s",
        DGTest.KIND_ASSEMBLE : ".o",
        DGTest.KIND_LINK: ".exe",
        DGTest.KIND_RUN : ".exe",
        KIND_PRECOMPILE : ".gch",
        }
    """A map from dg-do keywords to extensions.

    The extension indicates what filename extension should be used for
    the output file."""

    __test_kind_map = {
        DGTest.KIND_PREPROCESS : gpp.KIND_PREPROCESS,
        DGTest.KIND_COMPILE : gpp.KIND_COMPILE,
        DGTest.KIND_ASSEMBLE : gpp.KIND_ASSEMBLE,
        DGTest.KIND_LINK : gpp.KIND_EXECUTABLE,
        DGTest.KIND_RUN : gpp.KIND_EXECUTABLE,
        KIND_PRECOMPILE : gpp.KIND_PRECOMPILE
        }
    """A map from dg-do keywords to 'gpp' compilation kinds."""

    __default_options = "-ansi -pedantic-errors -Wno-long-long"
    """The default set of compiler options to use when running tests."""

    __prune_regexp \
         = re.compile("(?m)("
                      "(^.*: In ((static member)?function|member|method"
                       "|(copy )?constructor|instantiation|program|subroutine"
                       "|block-data) .*)"
                      "|(^.*: At (top level|global scope):.*)"
                      "|(^collect2: ld returned .*)"
                      "|(^Please submit.*instructions.*)"
                      "|(^.*: warning: -f(pic|PIC) ignored for target.*)"
                      "|(^.*: warning: -f(pic|PIC)( and -fpic are|"
                       "is)? not supported.*)"
                      ")")
    """A regular expression matching irrelevant output from GCC.

    This regular expression emulates code in 'prune_gcc_output'."""
                      
    def Run(self, context, result):

        self._SetUp(context)
        self._RunDGTest(self.__default_options, context, result)
                        

    def _ExecuteFinalCommand(self, command, args, context, result):

        if command in ("scan-assembler", "scan-assembler-not",
                       "scan-assembler-dem", "scan-assembler-dem-not"):
            # See if there is a target selector applied to this test.
            expectation = self.PASS
            if len(args) > 1:
                code = self._ParseTargetSelector(args[1])
                if code == "N":
                    return
                if code == "F":
                    expectation = self.FAIL

            # See if the pattern appears in the output.
            pattern = args[0]
            output = self.__GetOutputFile(self.KIND_COMPILE, self.GetId())
            output = open(output).read()
            # Run the output through the demangler, if necessary.
            if command in ("scan-assembler-dem", "scan-assembler-dem-not"):
                executable = Filter(output)
                executable.Run(["c++filt"])
                output = executable.stdout
            m = re.search(pattern, output)

            # Record the result of the test.
            if ((command in ("scan-assembler",
                             "scan-assembler-dem") and not m)
                or (command in ("scan-assembler-not",
                                "scan-assembler-dem-not") and m)):
                outcome = self.FAIL
            else:
                outcome = self.PASS
            message = self._name + " command " + pattern
            self._RecordDejaGNUOutcome(result, outcome, message, expectation)
        else:
            return DGTest._ExecuteFinalCommand(self, command, args,
                                               context, result)

        
    def _GetTargetEnvironment(self, context):

        return gpp.get_target_environment(context)
            

    def _PruneOutput(self, output):

        # This function emulates prune_gcc_output.
        return re.sub(self.__prune_regexp, "", output)
        
        
    def _RunTool(self, path, kind, options, context, result):

        # This method emulates g++-dg-test.

        file = self.__GetOutputFile(kind, path)
        kind = self.__test_kind_map[kind]
        output = gpp.compile(context, result,
                             [path],
                             file,
                             kind,
                             options.split(),
                             self)
            
        return (output, file)

        
    def __GetOutputFile(self, kind, path = None):
        """Return the compilation mode and output file name for the test.

        'kind' -- The kind of test being performed; one of
        'DGTest.__test_kinds'.

        'path' -- The path to the file being compiled.  If 'None', the
        primary source path is used.
        
        returns -- A pair '(mode, file)' where 'mode' is one of the
        'Compiler.modes' and 'file' is the name of the output file
        generated."""
        
        ext = self.__extension_map[kind]
        file = os.path.basename(path)
        if kind != self.KIND_PRECOMPILE:
            file = os.path.splitext(file)[0]
        file += ext
        if kind == self.KIND_RUN:
            file = os.path.join(".", file)

        return file
        
