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

    __compilation_mode_map = {
        DGTest.KIND_PREPROCESS : (Compiler.MODE_PREPROCESS, ".i"),
        DGTest.KIND_COMPILE : (Compiler.MODE_COMPILE, ".s"),
        DGTest.KIND_ASSEMBLE : (Compiler.MODE_ASSEMBLE, ".o"),
        DGTest.KIND_LINK: (Compiler.MODE_LINK, ".exe"),
        DGTest.KIND_RUN : (Compiler.MODE_LINK, ".exe")
        }
    """A map from dg-do keywords to compilation modes and extensions.

    The compilation mode indicates how the file should be compiled.
    The extension indicates what filename extension should be used for
    the output file."""

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
            mode, output \
                = self.__GetCompilationModeAndOutputFile(self.KIND_COMPILE)
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
            message = self.GetId() + " command " + pattern
            self._RecordDejaGNUOutcome(result, outcome, message, expectation)
        else:
            return DGTest._ExecuteFinalCommand(self, command, args,
                                               context, result)

        
    def _GetTargetEnvironment(self, context):

        env = {}
        dirs = ":".join(context["GPPInit.library_directories"])
        for v in ("LD_LIBRARY_PATH",
                  "SHLIB_PATH",
                  "LD_LIBRARY_N32_PATH",
                  "LD_LIBRARY64_PATH"):
            val = os.environ.get(v, "")
            if val:
                env[v] = val + ":" + dirs
            else:
                env[v] = dirs

        return env
            

    def _PruneOutput(self, output):

        # This function emulates prune_gcc_output.
        return re.sub(self.__prune_regexp, "", output)
        
        
    def _RunTool(self, kind, options, context, result):

        # This method emulates g++-dg-test.

        mode, file = self.__GetCompilationModeAndOutputFile(kind)
        output = self._Compile(context, result,
                               [self._GetSourcePath()],
                               file,
                               mode,
                               options.split())
            
        return (output, file)


    def _Compile(self, context, result, source_files, output_file,
                 mode, options):
        """Compile 'source_file'.

        'result' -- The QMTest 'Result' for the test.
        
        'context' -- The 'Context' in which the test is running.
        
        'source_file' -- A list of paths giving the source files to be
        compiled.

        'output_file' -- The name of the output file to be created.

        'mode' -- One of the 'Compiler.modes'.

        'options' -- A list of additional command-line options to be
        provided to the compiler.

        returns -- The output produced by the compiler."""

        # This method emulates g++_target_compile (in the GCC
        # testsuite), and target_compile (in the DejaGNU distribution).

        # There are a lot of complexities in default_target_compile
        # which we do not presently attempt to emulate.
        # Form the command-line.  Using Compiler.GetCompilationCommand
        # isn't guaranteed to create exactly the same command used by
        # DejaGNU, so we form the command manually.
        compiler = context["CompilerTable.compiler_table"]["cplusplus"]
        command = [compiler.GetPath()]
        # Add the global options (as originally specified in the
        # context file).  These are added before the options for this
        # test so that the latter can override the former.
        command += context["GPPInit.options"]
        command += options
        # Add the source files.
        if mode != Compiler.MODE_ASSEMBLE:
            command += source_files
        # Indicate the compilation mode.
        command += compiler._GetModeSwitches(mode)
        # For an executable test, provide necessary -L options.
        if mode == Compiler.MODE_LINK:
            command += map(lambda d: "-L" + d,
                           context["GPPInit.library_directories"])
        # Indicate where the output should go.
        command += ["-o", output_file]
        # Add the source files if they have not already been added.
        if mode == Compiler.MODE_ASSEMBLE:
            command += source_files

        # Run the compiler.
        index = self._RecordCommand(result, command)
        status, output = compiler.ExecuteCommand(None, command)
        self._RecordCommandOutput(result, index, status, output)
                    
        # If there was no output, DejaGNU uses the exit status.
        if not output and status != 0:
            output = "exit statis is %d" % status

        return output

        
    def __GetCompilationModeAndOutputFile(self, kind):
        """Return the compilation mode and output file name for the test.

        'kind' -- The kind of test being performed; one of
        'DGTest.__test_kinds'.
        
        returns -- A pair '(mode, file)' where 'mode' is one of the
        'Compiler.modes' and 'file' is the name of the output file
        generated."""
        
        mode, ext = self.__compilation_mode_map[kind]
        file = os.path.basename(self._GetSourcePath())
        file = os.path.splitext(file)[0] + ext
        if kind == self.KIND_RUN:
            file = os.path.join(".", file)

        return mode, file
        
