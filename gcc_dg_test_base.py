########################################################################
#
# File:   gcc_dg_test_base.py
# Author: Mark Mitchell
# Date:   05/15/2003
#
# Contents:
#   GCCDGTestBase
#
# Copyright (c) 2003 by CodeSourcery, LLC.  All rights reserved. 
#
########################################################################

from   compiler import Compiler
from   dg_test import DGTest
from   gcc_test_base import GCCTestBase
import os
from   qm.executable import Filter
import re

########################################################################
# Classes
########################################################################

class GCCDGTestBase(DGTest):
    """A 'GCCDGTestBase' is a base for all GCC DG tests..

    This test class emulates the 'gcc-dg.exp' source file in the GCC
    testsuite."""

    __extension_map = {
        DGTest.KIND_PREPROCESS : ".i",
        DGTest.KIND_COMPILE : ".s",
        DGTest.KIND_ASSEMBLE : ".o",
        DGTest.KIND_LINK: ".exe",
        DGTest.KIND_RUN : ".exe",
        GCCTestBase.KIND_PRECOMPILE : ".gch",
        }
    """A map from dg-do keywords to extensions.

    The extension indicates what filename extension should be used for
    the output file."""

    __prune_regexp \
         = re.compile("(?m)("
                      "(^.*: In ((static member )?function|member|method"
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

    _default_options = None
    """The default set of compiler options to use when running tests."""
    
    def Run(self, context, result):

        self._SetUp(context)
        self._RunDGTest("", self._default_options, context, result)
                        

    def _ExecuteFinalCommand(self, command, args, context, result):

        if command in ("scan-assembler", "scan-assembler-not",
                       "scan-assembler-dem", "scan-assembler-dem-not"):
            self.__ScanFile(result,
                            context,
                            command,
                            self.__GetOutputFile(context,
                                                 self.KIND_COMPILE,
                                                 self.GetId()),
                            args)
        elif command in ("scan-file", "scan-file-not"):
            self.__ScanFile(result,
                            context,
                            command,
                            os.path.join(context.GetTemporaryDirectory(),
                                         args[0]),
                            args[1:])
        else:
            return DGTest._ExecuteFinalCommand(self, command, args,
                                               context, result)


    def _DGadditional_files(self, line_num, args, context):
        """Emulate the 'dg-additional-file' command.

        'line_num' -- The number at which the command was found.

        'args' -- The arguments to the command, as a list of
        strings.

        'context' -- The 'Context' in which the test is running."""

        # This function is only used to handle exotic situations where
        # files have to be downloaded to a target systems.  Our
        # DejaGNU emulation does not presently support this
        # functionality.
        return


    def _DGadditional_sources(self, line_num, args, context):
        """Emulate the 'dg-additional-sources' command.

        'line_num' -- The number at which the command was found.

        'args' -- The arguments to the command, as a list of
        strings.

        'context' -- The 'Context' in which the test is running."""

        self.__additional_source_files = args[0].split()


    def _PruneOutput(self, output):

        # This function emulates prune_gcc_output.
        return self.__prune_regexp.sub("", output)
        
        
    def _RunTool(self, path, kind, options, context, result):

        # This method emulates g++-dg-test.

        source_files = [path]
        if self.__additional_source_files:
            dirname = os.path.dirname(path)
            source_files += map(lambda f: os.path.join(dirname, f),
                                self.__additional_source_files)
        options = self._ParseTclWords(options)
        if "-frepo" in options:
            is_repo_test = 1
            kind = DGTest.KIND_ASSEMBLE
        else:
            is_repo_test = 0
        file = self.__GetOutputFile(context, kind, path)
        kind = self._test_kind_map[kind]
        output = self._Compile(context, result, source_files, file,
                               kind, options)
        if is_repo_test:
            kind = DGTest.KIND_LINK
            object_file = file
            file = self.__GetOutputFile(context, kind, path)
            kind = self._test_kind_map[kind]
            output += self._Compile(context, result, [object_file], file,
                                    kind, options)

        return (output, file)

        
    def __GetOutputFile(self, context, kind, path = None):
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

        return os.path.join(context.GetTemporaryDirectory(), file)


    def __ScanFile(self, result, context, command, output_file, args):
        """Look for a pattern in the 'output_file'.

        'result' -- The QMTest 'Result' for this test.

        'context' -- The QMTest 'Context' in which this test is
        executing.
        
        'command' -- The name of the 'dg-final' command being run.

        'output_file' -- The name of the file in which to look for the
        pattern.

        'args' -- The arguments to the 'command'.

        This method emulates 'dg-scan' in the GCC testsuite."""

        # See if there is a target selector applied to this test.
        expectation = self.PASS
        if len(args) > 1:
            code = self._ParseTargetSelector(args[1], context)
            if code == "N":
                return
            if code == "F":
                expectation = self.FAIL

        # See if the pattern appears in the output.
        pattern = args[0]
        output = open(output_file).read()
        # Run the output through the demangler, if necessary.
        if command in ("scan-assembler-dem", "scan-assembler-dem-not"):
            executable = Filter(output)
            executable.Run(["c++filt"])
            output = executable.stdout
        m = re.search(pattern, output)

        # Command names that end with "not" indicate negative tests.
        positive = not command.endswith("not")
        # Record the result of the test.
        if ((positive and m)
            or (not positive and not m)):
            outcome = self.PASS
        else:
            outcome = self.FAIL
        message = self._name + " " + command + " " + pattern
        self._RecordDejaGNUOutcome(result, outcome, message, expectation)
        

    def _SetUp(self, context):

        self.__additional_source_files = None
        super(GCCDGTestBase, self)._SetUp(context)
