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

########################################################################
# Classes
########################################################################

class GPPDGTest(DGTest):
    """A 'GPPDGTest' is a G++ test using the 'dg' test driver.

    This test class emulates the 'g++-dg.exp' source file in the GCC
    testsuite."""

    __compilation_mode_map = {
        "preprocess" : (Compiler.MODE_PREPROCESS, ".i"),
        "compiler" : (Compiler.MODE_COMPILE, ".s"),
        "assemble" : (Compiler.MODE_ASSEMBLE, ".o"),
        "link" : (Compiler.MODE_LINK, ".exe"),
        "run" : (Compiler.MODE_LINK, ".exe")
        }
    """A map from dg-do keywords to compilation modes and extensions.

    The compilation mode indicates how the file should be compiled.
    The extension indicates what filename extension should be used for
    the output file."""
    
    def _RunTool(self, kind, context, result):
        """Run the tool being tested.

        'kind' -- The kind of test to perform.

        'context' -- The 'Context' for the test execution.

        'result' -- The QMTest 'Result' for the test.

        returns -- A pair '(output, file)' where 'output' consists of
        any messages produced by the compiler, and 'file' is the name
        of the file produced by the compilation, if any."""

        # This method emulates g++-dg-test.

        # Map the dg-do keyword to a corresponding compilation mode.
        mode, ext = self.__compilation_mode_map[kind]
        file = os.path.basename(self._GetSourcePath())
        file = os.path.splitext(file)[0] + ext
        if kind == "run":
            file = os.path.join(".", file)

        output = self._Compile(context, result,
                               [self._GetSourcePath()],
                               file,
                               mode,
                               [])
            
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
        # Add the source files.
        if mode != Compiler.MODE_ASSEMBLE:
            command += source_files
        # Indicate the compilation mode.
        command += compiler._GetModeSwitches(mode)
        # Indicate where the output should go.
        command += ["-o", output_file]
        # Add the source files if they have not already been added.
        if mode == Compiler.MODE_ASSEMBLE:
            command += source_files

        # Run the compiler.
        self._RecordCommand(result, command)
        status, output = compiler.ExecuteCommand(None, command)

        # If there was no output, DejaGNU uses the exit status.
        if not output and status != 0:
            output = "exit statis is %d" % status

        return output

        
